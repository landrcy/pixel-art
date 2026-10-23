#!/usr/bin/env python3
"""
pixel_tools.py - small reusable helpers for hand-made-looking pixel art (Pillow + numpy).

Features
  * palette loading (.hex / .gpl / .png strip / built-in names / list of hex)
  * hue-shifted ramp generator (Slynyrd-style HSB ramps)
  * threshold-map dithering: bayer2/4/8, checker, diamond, dashes, hlines, hlines_dots,
    cross (star/plus), cross_sparse, noise (tiled, stable), plus hard bands with a bridge row
  * multi-colour dithered gradients (vertical/horizontal), with band-width progression
  * nearest-palette quantize (optionally ordered-dithered)
  * nearest-neighbour upscale, sprite sheets, palette-cycling frames
  * linting for "AI tells": colour count, off-palette pixels, semi-transparent pixels, orphans

Run `python3 pixel_tools.py` to execute the self-test and write demo PNGs to ./pixel_tools_demo/
Library use:  from pixel_tools import *
"""
from __future__ import annotations
import colorsys, math, os, re, sys
from typing import Iterable, Sequence
import numpy as np
from PIL import Image

RGB = tuple  # (r,g,b)

# ----------------------------------------------------------------------------
# Built-in palettes (hex, from Lospec palette-list .hex files; sunset_study = the
# 4-colour navy/mauve/dusty-pink/cream dithering study palette)
# ----------------------------------------------------------------------------
PALETTES = {
    "endesga32": "be4a2f d77643 ead4aa e4a672 b86f50 733e39 3e2731 a22633 e43b44 f77622 feae34 fee761 63c74d 3e8948 265c42 193c3e 124e89 0099db 2ce8f5 ffffff c0cbdc 8b9bb4 5a6988 3a4466 262b44 181425 ff0044 68386c b55088 f6757a e8b796 c28569",
    "endesga64": "ff0040 131313 1b1b1b 272727 3d3d3d 5d5d5d 858585 b4b4b4 ffffff c7cfdd 92a1b9 657392 424c6e 2a2f4e 1a1932 0e071b 1c121c 391f21 5d2c28 8a4836 bf6f4a e69c69 f6ca9f f9e6cf edab50 e07438 c64524 8e251d ff5000 ed7614 ffa214 ffc825 ffeb57 d3fc7e 99e65f 5ac54f 33984b 1e6f50 134c4c 0c2e44 00396d 0069aa 0098dc 00cdf9 0cf1ff 94fdff fdd2ed f389f5 db3ffd 7a09fa 3003d9 0c0293 03193f 3b1443 622461 93388f ca52c9 c85086 f68187 f5555d ea323c c42430 891e2b 571c27",
    "resurrect64": "2e222f 3e3546 625565 966c6c ab947a 694f62 7f708a 9babb2 c7dcd0 ffffff 6e2727 b33831 ea4f36 f57d4a ae2334 e83b3b fb6b1d f79617 f9c22b 7a3045 9e4539 cd683d e6904e fbb954 4c3e24 676633 a2a947 d5e04b fbff86 165a4c 239063 1ebc73 91db69 cddf6c 313638 374e4a 547e64 92a984 b2ba90 0b5e65 0b8a8f 0eaf9b 30e1b9 8ff8e2 323353 484a77 4d65b4 4d9be6 8fd3ff 45293f 6b3e75 905ea9 a884f3 eaaded 753c54 a24b6f cf657f ed8099 831c5d c32454 f04f78 f68181 fca790 fdcbb0",
    "apollo": "172038 253a5e 3c5e8b 4f8fba 73bed3 a4dddb 19332d 25562e 468232 75a743 a8ca58 d0da91 4d2b32 7a4841 ad7757 c09473 d7b594 e7d5b3 341c27 602c2c 884b2b be772b de9e41 e8c170 241527 411d31 752438 a53030 cf573c da863e 1e1d39 402751 7a367b a23e8c c65197 df84a5 090a14 10141f 151d28 202e37 394a50 577277 819796 a8b5b2 c7cfcc ebede9",
    "sweetie16": "1a1c2c 5d275d b13e53 ef7d57 ffcd75 a7f070 38b764 257179 29366f 3b5dc9 41a6f6 73eff7 f4f4f4 94b0c2 566c86 333c57",
    "aap64": "060608 141013 3b1725 73172d b4202a df3e23 fa6a0a f9a31b ffd541 fffc40 d6f264 9cdb43 59c135 14a02e 1a7a3e 24523b 122020 143464 285cc4 249fde 20d6c7 a6fcdb ffffff fef3c0 fad6b8 f5a097 e86a73 bc4a9b 793a80 403353 242234 221c1a 322b28 71413b bb7547 dba463 f4d29c dae0ea b3b9d1 8b93af 6d758d 4a5462 333941 422433 5b3138 8e5252 ba756a e9b5a3 e3e6ff b9bffb 849be4 588dbe 477d85 23674e 328464 5daf8d 92dcba cdf7e2 e4d2aa c7b08b a08662 796755 5a4e44 423934",
    "pico8": "000000 1d2b53 7e2553 008751 ab5236 5f574f c2c3c7 fff1e8 ff004d ffa300 ffec27 00e436 29adff 83769c ff77a8 ffccaa",
    "sunset_study": "272744 8b6d9c c69fa5 f2d3ab",
}

# ----------------------------------------------------------------------------
# Colour helpers
# ----------------------------------------------------------------------------
def hex_to_rgb(h: str) -> RGB:
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def rgb_to_hex(c: Sequence[int]) -> str:
    return "#%02x%02x%02x" % tuple(int(round(v)) for v in c[:3])

def load_palette(src) -> list[RGB]:
    """src: built-in name ('endesga32', 'sunset_study'...), path to .hex/.gpl/.png/.txt,
    a whitespace/comma separated hex string, or a list of hex/RGB items."""
    if isinstance(src, (list, tuple)):
        return [hex_to_rgb(c) if isinstance(c, str) else tuple(c[:3]) for c in src]
    if src in PALETTES:
        return [hex_to_rgb(c) for c in PALETTES[src].split()]
    if os.path.isfile(src):
        low = src.lower()
        if low.endswith((".png", ".gif", ".bmp")):  # palette strip image: unique colours, row-major
            im = Image.open(src).convert("RGB")
            seen, out = set(), []
            for p in im.getdata():
                if p not in seen:
                    seen.add(p); out.append(p)
            return out
        text = open(src, encoding="utf-8", errors="ignore").read()
        if low.endswith(".gpl"):
            out = []
            for line in text.splitlines():
                m = re.match(r"\s*(\d+)\s+(\d+)\s+(\d+)", line)
                if m:
                    out.append(tuple(int(v) for v in m.groups()))
            return out
        return [hex_to_rgb(t) for t in re.findall(r"#?[0-9a-fA-F]{6}\b", text)]
    toks = re.findall(r"#?[0-9a-fA-F]{6}\b", str(src))
    if toks:
        return [hex_to_rgb(t) for t in toks]
    raise ValueError(f"cannot load palette from {src!r}")

def luminance(c: RGB) -> float:
    r, g, b = c
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def sort_by_luminance(pal: Sequence[RGB]) -> list[RGB]:
    return sorted(pal, key=luminance)

# ----------------------------------------------------------------------------
# Hue-shifted ramp generator
# ----------------------------------------------------------------------------
def _hue_toward(h: float, target: float, amount: float) -> float:
    """move hue h (deg) toward target (deg) along the shorter arc by <=amount degrees"""
    d = (target - h + 180) % 360 - 180
    step = max(-amount, min(amount, d))
    return (h + step) % 360

def make_ramp(base: str | RGB, steps: int = 5, hue_shift: float = 14.0,
              b_range: tuple[float, float] = (0.25, 0.93),
              s_curve: tuple[float, float, float] = (0.85, 1.0, 0.55),
              warm_target: float = 55.0, cool_target: float = 265.0,
              base_index: int | None = None) -> list[str]:
    """Return `steps` hex colours dark -> light.
    Highlights drift toward warm_target hue (yellow), shadows toward cool_target (violet/blue),
    by <= hue_shift degrees per step. Brightness rises linearly b_range[0]->b_range[1].
    Saturation follows s_curve = (dark, mid, light) multipliers of the base saturation
    (peaks in the middle, drops in highlights, slightly lower in deep shadows).
    base_index = which step equals the base hue/sat (default: middle)."""
    r, g, b = hex_to_rgb(base) if isinstance(base, str) else base
    h0, s0, _v0 = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h0 *= 360
    if base_index is None:
        base_index = steps // 2
    out = []
    for i in range(steps):
        t = i / max(1, steps - 1)
        v = b_range[0] + (b_range[1] - b_range[0]) * t
        # piecewise-linear saturation: dark -> mid -> light
        sm = (s_curve[0] + (s_curve[1] - s_curve[0]) * (t / 0.5)) if t < 0.5 else \
             (s_curve[1] + (s_curve[2] - s_curve[1]) * ((t - 0.5) / 0.5))
        s = min(0.95, s0 * sm)
        k = i - base_index
        h = h0
        for _ in range(abs(k)):
            h = _hue_toward(h, warm_target if k > 0 else cool_target, hue_shift)
        rr, gg, bb = colorsys.hsv_to_rgb(h / 360, max(0.0, s), min(1.0, v))
        out.append(rgb_to_hex((rr * 255, gg * 255, bb * 255)))
    return out

# ----------------------------------------------------------------------------
# Threshold maps (value 0..1 per tile cell; pixel takes the LIGHTER colour if thr < level)
# ----------------------------------------------------------------------------
def bayer_matrix(n: int) -> np.ndarray:
    """n must be 2,4,8,16. Returns normalised thresholds in (0,1)."""
    assert n in (2, 4, 8, 16, 32)
    m = np.array([[0, 2], [3, 1]], dtype=np.float64)
    while m.shape[0] < n:
        s = m.shape[0]
        m = np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])
    return (m + 0.5) / (n * n)

def _rank_to_thr(rank: np.ndarray) -> np.ndarray:
    """convert any integer-ish ordering matrix into evenly spaced thresholds in (0,1)"""
    flat = rank.flatten().astype(float)
    order = flat.argsort(kind="stable").argsort(kind="stable")
    return ((order + 0.5) / flat.size).reshape(rank.shape)

def _cross_tile(n: int, centres: list[tuple[int, int]]) -> np.ndarray:
    """plus/star stamps: centres first, then the 4 arms, then everything else by Bayer order"""
    rank = np.full((n, n), 3.0)
    base = bayer_matrix(n)
    rank += base  # fill order for the leftover pixels (all > arms)
    for cx, cy in centres:
        rank[cy % n, cx % n] = 0 + base[cy % n, cx % n] * 0.01
    for cx, cy in centres:
        for k, (dx, dy) in enumerate(((0, -1), (0, 1), (-1, 0), (1, 0))):  # grow top, bottom, left, right
            y, x = (cy + dy) % n, (cx + dx) % n
            if rank[y, x] >= 3:
                rank[y, x] = 1 + 0.5 * k + 0.001 * base[y, x]  # identical growth in every stamp
    return _rank_to_thr(rank)

def threshold_map(name: str = "bayer4", seed: int = 7) -> np.ndarray:
    """Named dither patterns (match the 10 styles of the dithering study sheet)
      bayer2 / bayer4 / bayer8 : classic ordered dither
      checker      : 50% checkerboard core; 25/75 steps either side (= bayer2)
      diamond      : clustered-dot diamonds / zig-zag rows (the 'diamond' ordered style)
      dashes       : 2x1 horizontal dashes in a brick offset (bayer4 stretched 2x wide)
      hlines       : whole horizontal lines, 25/50/75% = 1,2,3 rows of every 4
      hlines_dots  : horizontal lines with half-density dotted rows between the steps
      cross        : plus/star motif, period 4 (dense)
      cross_sparse : plus/star motif, period 8 (airy, good for starry dusk skies)
      noise        : stable random (16x16 tiled permutation); organic but can clump - use sparingly
    """
    n = name.lower()
    if n in ("bayer2", "checker"):
        return bayer_matrix(2)
    if n == "bayer4":
        return bayer_matrix(4)
    if n == "bayer8":
        return bayer_matrix(8)
    if n == "diamond":
        return _rank_to_thr(np.array([[12, 5, 6, 13], [4, 0, 1, 7], [11, 3, 2, 8], [15, 10, 9, 14]]))
    if n == "dashes":
        b = bayer_matrix(4)
        return np.repeat(b, 2, axis=1)  # 4 rows x 8 cols
    if n == "hlines":
        rows = np.array([0, 2, 1, 3], dtype=float)  # which row lights first
        return ((rows + 0.5) / 4)[:, None] * np.ones((4, 2))
    if n == "hlines_dots":
        rows = np.array([0, 2, 1, 3], dtype=float)
        t = np.zeros((4, 2))
        for y in range(4):
            for x in range(2):
                t[y, x] = (rows[y] + (0.15 if (x + y) % 2 == 0 else 0.6)) / 4
        return t
    if n == "cross":
        return _cross_tile(4, [(1, 1), (3, 3)])
    if n == "cross_sparse":
        return _cross_tile(8, [(2, 2), (6, 6)])
    if n == "noise":
        rng = np.random.default_rng(seed)
        return _rank_to_thr(rng.permutation(256).reshape(16, 16))
    raise ValueError(f"unknown dither pattern {name!r}")

DITHER_STYLES = ["bayer2", "bayer4", "bayer8", "diamond", "dashes", "hlines",
                 "hlines_dots", "cross", "cross_sparse", "noise"]

def tile_to(thr: np.ndarray, w: int, h: int, ox: int = 0, oy: int = 0) -> np.ndarray:
    th, tw = thr.shape
    ys = (np.arange(h) + oy) % th
    xs = (np.arange(w) + ox) % tw
    return thr[np.ix_(ys, xs)]

# ----------------------------------------------------------------------------
# Gradients
# ----------------------------------------------------------------------------
def gradient_positions(n_rows: int, n_colors: int, progression: Sequence[float] | None = None) -> np.ndarray:
    """level (0..n_colors-1, float) per row. progression = relative band heights for the
    n_colors-1 transitions (e.g. [1,1.5,2.5] -> thin first band, thick last band)."""
    if progression is None:
        progression = [1.0] * (n_colors - 1)
    assert len(progression) == n_colors - 1
    prog = np.array(progression, dtype=float)
    edges = np.concatenate([[0], np.cumsum(prog / prog.sum())]) * n_rows
    y = np.arange(n_rows) + 0.5
    lvl = np.zeros(n_rows)
    for i in range(n_colors - 1):
        m = (y >= edges[i]) & (y < edges[i + 1] + (1e-9 if i == n_colors - 2 else 0))
        lvl[m] = i + (y[m] - edges[i]) / (edges[i + 1] - edges[i])
    lvl[y >= edges[-1]] = n_colors - 1
    return lvl

def dither_gradient(w: int, h: int, colors: Sequence, pattern: str = "bayer4",
                    direction: str = "v", progression: Sequence[float] | None = None,
                    transition: float = 0.5, seed: int = 7) -> Image.Image:
    """Multi-colour gradient. colors: hex strings/RGB, first->last along the direction.
    pattern: any threshold_map name, or 'band' (hard bands, no dither), or 'band_bridge'
    (hard bands + one alternating-pixel row at each boundary, the cheapest hand-made look).
    transition: 1.0 = dither across the whole segment, 0.3 = dither only the middle 30% of each segment
      (so most of the segment is flat colour: this is what makes it look hand-made, not 'filtered').
    """
    cols = [hex_to_rgb(c) if isinstance(c, str) else tuple(c[:3]) for c in colors]
    n = len(cols)
    length = h if direction == "v" else w
    lvl = gradient_positions(length, n, progression)            # (length,)
    seg = np.minimum(lvl.astype(int), n - 2) if n > 1 else np.zeros(length, int)
    frac = lvl - seg
    # squeeze: only the middle `transition` fraction of the segment is dithered
    lo, hi = 0.5 - transition / 2, 0.5 + transition / 2
    frac = np.clip((frac - lo) / max(1e-9, (hi - lo)), 0, 1)
    if direction == "v":
        segm, fracm = np.repeat(seg[:, None], w, 1), np.repeat(frac[:, None], w, 1)
    else:
        segm, fracm = np.repeat(seg[None, :], h, 0), np.repeat(frac[None, :], h, 0)
    if pattern == "band":
        up = fracm >= 0.5
    elif pattern == "band_bridge":
        up = fracm >= 0.5
        # bridge: on the row/col just before and just after the edge, every other pixel flips
        yy, xx = np.mgrid[0:h, 0:w]
        axis = yy if direction == "v" else xx
        other = xx if direction == "v" else yy
        flip_a = np.zeros_like(up)
        flip_b = np.zeros_like(up)
        # row after edge (first of upper colour) -> every other pixel stays lower colour; row before -> inverse
        edge_after = up & ~np.roll(up, 1, axis=0 if direction == "v" else 1)
        edge_before = ~up & np.roll(up, -1, axis=0 if direction == "v" else 1)
        up = up.copy()
        up[edge_after & (other % 2 == 0)] = False
        up[edge_before & (other % 2 == 1)] = True
    else:
        thr = tile_to(threshold_map(pattern, seed), w, h)
        up = fracm > thr
    idx = np.where(up, segm + 1, segm)
    arr = np.array(cols, dtype=np.uint8)[idx]
    return Image.fromarray(arr, "RGB")

def bayer_gradient(w: int, h: int, c0, c1, n: int = 4, direction: str = "v") -> Image.Image:
    """Two-colour ordered-dither gradient (c0 at top/left -> c1 at bottom/right)."""
    return dither_gradient(w, h, [c0, c1], pattern=f"bayer{n}", direction=direction, transition=1.0)

# ----------------------------------------------------------------------------
# Quantize / scale / sheets
# ----------------------------------------------------------------------------
def nearest_palette_index(arr: np.ndarray, palette: Sequence[RGB], weights=(0.30, 0.59, 0.11)) -> np.ndarray:
    """arr: HxWx3 (float or uint8). Perceptual-ish weighted RGB distance. Returns HxW indices."""
    pal = np.array(palette, dtype=np.float64)
    w = np.array(weights) ** 0.5
    a = arr.astype(np.float64)[..., None, :] * w
    p = pal[None, None, :, :] * w
    return ((a - p) ** 2).sum(-1).argmin(-1)

def quantize(img: Image.Image, palette, dither: str | None = None, strength: float = 48.0) -> Image.Image:
    """Snap every pixel to the nearest palette colour (no blending, no new colours).
    dither: None or a threshold_map name -> ordered dither (adds +/-strength/2 before snapping).
    Alpha is thresholded at 128 (pixel art has no semi-transparency)."""
    pal = load_palette(palette)
    rgba = img.convert("RGBA")
    a = np.array(rgba)
    rgb, alpha = a[..., :3].astype(np.float64), a[..., 3]
    if dither:
        thr = tile_to(threshold_map(dither), rgb.shape[1], rgb.shape[0])
        rgb = np.clip(rgb + (thr[..., None] - 0.5) * strength, 0, 255)
    idx = nearest_palette_index(rgb, pal)
    out = np.array(pal, dtype=np.uint8)[idx]
    res = np.dstack([out, np.where(alpha >= 128, 255, 0).astype(np.uint8)])
    return Image.fromarray(res, "RGBA")

def upscale(img: Image.Image, k: int) -> Image.Image:
    """Integer nearest-neighbour upscale (never use bilinear/bicubic/lanczos for pixel art)."""
    assert isinstance(k, int) and k >= 1, "scale must be an integer"
    return img.resize((img.width * k, img.height * k), Image.NEAREST)

def downscale_blocks(img: Image.Image, k: int) -> Image.Image:
    """Inverse of upscale for clean k x k blocks (nearest sampling at block centres)."""
    return img.resize((img.width // k, img.height // k), Image.NEAREST)

def sprite_sheet(frames: Sequence[Image.Image], cols: int | None = None, pad: int = 0) -> Image.Image:
    """Horizontal strip by default (cols=None) - ideal for CSS steps() animation."""
    fw, fh = frames[0].size
    cols = cols or len(frames)
    rows = math.ceil(len(frames) / cols)
    sheet = Image.new("RGBA", (cols * (fw + pad) - pad, rows * (fh + pad) - pad), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(f.convert("RGBA"), ((i % cols) * (fw + pad), (i // cols) * (fh + pad)))
    return sheet

def save_gif(frames: Sequence[Image.Image], path: str, ms: int | Sequence[int] = 100, scale: int = 1):
    fr = [upscale(f.convert("RGB"), scale) if scale > 1 else f.convert("RGB") for f in frames]
    fr[0].save(path, save_all=True, append_images=fr[1:], duration=ms, loop=0, disposal=2)

def palette_cycle_frames(indexed: np.ndarray, palette: Sequence[RGB], cycle_ranges: Sequence[tuple[int, int]],
                         n_frames: int) -> list[Image.Image]:
    """Mark Ferrari-style colour cycling. indexed = HxW palette indices, palette = list of RGB,
    cycle_ranges = [(first_idx,last_idx),...] inclusive; each range rotates 1 slot per frame
    (n_frames should divide the range lengths for a perfect loop). Returns RGB frames."""
    frames = []
    for f in range(n_frames):
        pal = [tuple(c) for c in palette]
        for lo, hi in cycle_ranges:
            seg = pal[lo:hi + 1]
            k = f % len(seg)
            pal[lo:hi + 1] = seg[-k:] + seg[:-k] if k else seg
        frames.append(Image.fromarray(np.array(pal, dtype=np.uint8)[indexed], "RGB"))
    return frames

def scroll_wrap(img: Image.Image, dx: int, dy: int = 0) -> Image.Image:
    """whole-pixel wrap scroll (for seamless parallax/wave loops)"""
    a = np.array(img)
    return Image.fromarray(np.roll(np.roll(a, dx, axis=1), dy, axis=0), img.mode)

# ----------------------------------------------------------------------------
# Lint: detect "AI tells"
# ----------------------------------------------------------------------------
def lint(img: Image.Image, palette=None, max_colors: int = 32, assumed_scale: int = 1) -> dict:
    """Returns a report dict. Pass the NATIVE-resolution image (or set assumed_scale to
    check an upscaled export is made of clean k x k blocks)."""
    rgba = np.array(img.convert("RGBA"))
    report: dict = {"size": img.size}
    alpha = rgba[..., 3]
    report["semi_transparent_pixels"] = int(((alpha > 0) & (alpha < 255)).sum())
    opaque = alpha == 255
    rgb = rgba[..., :3]
    cols, counts = np.unique(rgb[opaque].reshape(-1, 3), axis=0, return_counts=True)
    report["colors"] = len(cols)
    report["too_many_colors"] = len(cols) > max_colors
    if palette is not None:
        pal = set(map(tuple, load_palette(palette)))
        report["off_palette_pixels"] = int(sum(c for col, c in zip(map(tuple, cols), counts) if col not in pal))
    # orphans: opaque pixel with no 4-neighbour of identical colour
    h, w = alpha.shape
    pad = np.pad(rgb, ((1, 1), (1, 1), (0, 0)), constant_values=-1).astype(int)
    same = np.zeros((h, w), dtype=int)
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        nb = pad[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
        same += (nb == rgb).all(-1)
    orphans = opaque & (same == 0)
    report["orphan_pixels"] = int(orphans.sum())
    report["orphan_ratio"] = round(float(orphans.sum()) / max(1, int(opaque.sum())), 4)
    if assumed_scale > 1:
        k = assumed_scale
        hh, ww = (h // k) * k, (w // k) * k
        blocks = rgba[:hh, :ww].reshape(hh // k, k, ww // k, k, 4)
        uniform = (blocks == blocks[:, :1, :, :1, :]).all(axis=(1, 3, 4))
        report["clean_block_ratio"] = round(float(uniform.mean()), 4)  # 1.0 = every block uniform
    issues = []
    if report["semi_transparent_pixels"]: issues.append("semi-transparent pixels (blur/AA glow)")
    if report["too_many_colors"]: issues.append(f"{len(cols)} colours > {max_colors}")
    if report.get("off_palette_pixels"): issues.append("pixels outside the palette")
    if report["orphan_ratio"] > 0.01: issues.append("many orphan pixels (>1%) - noise")
    if "clean_block_ratio" in report and report["clean_block_ratio"] < 0.995: issues.append("mixed pixel sizes / sub-pixel edges")
    report["issues"] = issues
    return report

# ----------------------------------------------------------------------------
# Demo + self-test
# ----------------------------------------------------------------------------
def dither_study(path: str, palette="sunset_study", w=24, h=64, scale=4):
    """Re-creates the 3-row x 10-style study sheet (2/3/4 colours x 10 dither styles)."""
    pal = load_palette(palette)
    styles = ["bayer2", "bayer4", "bayer8", "dashes", "hlines", "hlines_dots", "diamond", "band_bridge", "noise", "cross_sparse"]
    rows = [[pal[0], pal[2]], [pal[0], pal[1], pal[2]], [pal[0], pal[1], pal[2], pal[3]]]
    sheet = Image.new("RGB", (len(styles) * (w + 4), len(rows) * (h + 4)), (255, 255, 255))
    for r, cols in enumerate(rows):
        for c, s in enumerate(styles):
            g = dither_gradient(w, h, cols, pattern=s, transition=0.8)
            sheet.paste(g, (c * (w + 4) + 2, r * (h + 4) + 2))
    upscale(sheet, scale).save(path)

def _selftest(outdir: str = "pixel_tools_demo"):
    os.makedirs(outdir, exist_ok=True)
    # palettes
    for name in PALETTES:
        p = load_palette(name)
        assert len(p) >= 4, name
    assert len(load_palette("endesga32")) == 32 and len(load_palette("pico8")) == 16
    assert load_palette("#ff0000 00ff00") == [(255, 0, 0), (0, 255, 0)]
    # ramp: 5 steps, brightness monotonic, hue warms toward highlights, cools toward shadows
    ramp = make_ramp("#3b82c4", 5)
    lum = [luminance(hex_to_rgb(c)) for c in ramp]
    assert lum == sorted(lum) and len(set(ramp)) == 5, ramp
    hs = [colorsys.rgb_to_hsv(*[v / 255 for v in hex_to_rgb(c)])[0] * 360 for c in ramp]
    assert hs[0] > hs[2] and hs[4] < hs[2], hs   # shadows rotate toward violet (up), highlights toward cyan/green (down)
    # bayer
    b4 = bayer_matrix(4)
    assert sorted(np.round(b4.flatten() * 16 - 0.5).astype(int)) == list(range(16))
    # every threshold map: coverage rises monotonically with level, and ~= level
    for name in DITHER_STYLES:
        t = threshold_map(name)
        cov = [(t < lv).mean() for lv in (0.0, 0.25, 0.5, 0.75, 1.0)]
        assert cov == sorted(cov) and cov[0] == 0 and cov[-1] == 1, (name, cov)
        assert abs(cov[2] - 0.5) < 0.1, (name, cov)
    # 50% checker is a true checkerboard
    t2 = (bayer_matrix(2) < 0.5)
    assert t2.sum() == 2 and t2[0, 0] != t2[0, 1]
    # gradient: only palette colours, top is c0, bottom is c1
    c0, c1 = "#272744", "#c69fa5"
    for pat in DITHER_STYLES + ["band", "band_bridge"]:
        g = dither_gradient(32, 48, [c0, c1], pattern=pat)
        cols = {tuple(c) for c in np.array(g).reshape(-1, 3)}
        assert cols <= {hex_to_rgb(c0), hex_to_rgb(c1)}, pat
        assert tuple(np.array(g)[0, 0]) == hex_to_rgb(c0) and tuple(np.array(g)[-1, 0]) == hex_to_rgb(c1), pat
    # quantize
    photo = Image.effect_mandelbrot((64, 64), (-2, -1.5, 1, 1.5), 40).convert("RGB")
    q = quantize(photo, "sweetie16", dither="bayer4")
    rep = lint(q, "sweetie16")
    assert rep["colors"] <= 16 and rep["off_palette_pixels"] == 0 and rep["semi_transparent_pixels"] == 0, rep
    # upscale: integer + crisp
    u = upscale(q, 4)
    assert u.size == (256, 256)
    assert lint(u, "sweetie16", assumed_scale=4)["clean_block_ratio"] == 1.0
    blurry = u.resize((255, 255), Image.BILINEAR)
    assert lint(blurry, "sweetie16", assumed_scale=4)["issues"], "lint should flag blurry/off-grid image"
    # sheet + cycling
    pal = load_palette("sunset_study")
    idx = np.tile(np.arange(4), (4, 4))[:, :16] % 4
    fr = palette_cycle_frames(idx, pal, [(0, 3)], 4)
    assert len(fr) == 4 and np.array(fr[0]).tobytes() != np.array(fr[1]).tobytes()
    assert np.array(fr[0]).tobytes() == np.array(palette_cycle_frames(idx, pal, [(0, 3)], 8)[4]).tobytes()
    sh = sprite_sheet(fr)
    assert sh.size == (16 * 4, 4)
    # outputs
    dither_study(os.path.join(outdir, "dither_study_sunset.png"))
    sky = dither_gradient(160, 90, ["#272744", "#8b6d9c", "#c69fa5", "#f2d3ab"], "bayer4",
                          progression=[1, 1.6, 2.4], transition=0.35)
    upscale(sky, 4).save(os.path.join(outdir, "sky_bayer4.png"))
    r = make_ramp("#2e9bb0", 6)
    strip = Image.new("RGB", (6 * 8, 8))
    for i, c in enumerate(r):
        strip.paste(hex_to_rgb(c), (i * 8, 0, i * 8 + 8, 8))
    upscale(strip, 8).save(os.path.join(outdir, "ramp_teal.png"))
    save_gif(fr, os.path.join(outdir, "cycle.gif"), 150, 8)
    print("pixel_tools self-test OK ->", os.path.abspath(outdir))
    print("teal ramp:", r)

if __name__ == "__main__":
    _selftest(sys.argv[1] if len(sys.argv) > 1 else "pixel_tools_demo")
