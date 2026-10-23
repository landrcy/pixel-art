#!/usr/bin/env python3
"""Illuminated-manuscript border kit (pixel art, purple + antique gold) - re-runnable.
   python3 generate.py          -> writes every PNG / json / css next to this file
Draws geometry as boolean masks, then an automatic bevel shader (light from top-left, selective
dark-bronze / indigo outlines) paints them into the 14-colour palette. Only pixel mirrors/tiling are used."""
import json, math, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pxl import *

OUT = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ helpers
def to_img(idx):
    rgba = np.zeros(idx.shape + (4,), np.uint8)
    for k, h in PAL.items():
        if h: rgba[idx == k] = (*rgb(h), 255)
    return Image.fromarray(rgba, "RGBA")

def gem_at(M, shape_fn):
    g = np.zeros_like(M["gem"]); shape_fn(g)
    ring = g.copy()
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ring |= np.roll(np.roll(g, dy, 0), dx, 1)
    M["gem"] = M["gem"] | g; M["carve"] = M["carve"] | ring
    return g

def lattice(M, g, period=5, phase=0):
    h, w = g.shape
    ys, xs = np.mgrid[0:h, 0:w]
    yy, xx = np.nonzero(g)
    xs = xs - xx.min(); ys = ys - yy.min()          # phase relative to the gem, so every repeat is identical
    sel = (((xs + ys + phase) % period == 0) | ((xs - ys + phase) % period == 0)) & g
    M["gemdark"] = M["gemdark"] | sel

def specs_of(gems):
    ex = []
    for g in gems:
        ys, xs = np.nonzero(g)
        if len(xs) == 0: continue
        i = np.argmin(xs + ys * 1.0001)
        ex.append(((int(xs[i]), int(ys[i])), 8))
    return ex

def volute(m, tx, ty, R, direction, th=430, widths=((0, 2), (0.55, 1)), end_r=1.5, bead=1.3, bead_mask=None):
    """one spiral scroll that leaves point (tx,ty) heading +x. direction=+1 curls DOWN (clockwise on
    screen), -1 curls UP. end_r = radius of the last turn; bead drawn in the eye."""
    if direction > 0:
        pts = spiral(tx, ty + R, -90, -90 + th, R, end_r)
        c = (tx, ty + R)
    else:
        pts = spiral(tx, ty - R, 90, 90 - th, R, end_r)
        c = (tx, ty - R)
    stroke(m, pts, widths)
    if bead_mask is not None and bead:
        disc(bead_mask, c[0], c[1] + 0.5, bead)

def mirror_h(img): return img.transpose(Image.FLIP_LEFT_RIGHT)
def mirror_v(img): return img.transpose(Image.FLIP_TOP_BOTTOM)

# ------------------------------------------------------------------ vine-free vertical strip (48 x 128)
def strip_motif(M, oy, variant, gems):
    AX = 23.5
    rect(M["gold"], 23, oy - 6, 24, oy + 64 + 6)
    for ny in (0.5, 32.5, 64.5):                       # nodes (diamond + 2x2 amethyst)
        gems.append(gem_at(M, lambda m: rect(m, 23, int(oy + ny), 24, int(oy + ny) + 1)))
        diamond(M["gold"], AX, oy + ny + 0.5, 4.5, 4.5)
    mcy = oy + 16.5                                   # round medallion
    disc(M["gold"], AX, mcy, 8.4)
    g1 = gem_at(M, lambda m: disc(m, AX, mcy, 4.0)); gems.append(g1)
    lcy = oy + 48.5                                   # lozenge
    diamond(M["gold"], AX, lcy, 7.8, 10.5)
    g2 = gem_at(M, lambda m: diamond(m, AX, lcy, 4.6, 7.2)); gems.append(g2)
    lattice(M, g2 if variant == 0 else g1, 5)
    A = np.zeros_like(M["gold"]); T = np.zeros_like(M["gold"])
    for cy_, tx in ((mcy, 36.0), (lcy, 35.5)):         # twin volutes on a T-arm, mirrored to the left
        volute(T, tx, cy_ + 0.0, 5.0, +1, 400, ((0, 2), (0.55, 1)), 1.2)
        volute(T, tx, cy_ + 1.0, 5.0, -1, 400, ((0, 2), (0.55, 1)), 1.2)
        rect(A, 30, int(cy_), int(tx), int(cy_) + 1)
        disc(A, tx, cy_ - 5.0 + 1.5, 1.3); disc(A, tx, cy_ + 5.0 + 0.5, 1.3)
    M["wire"] = M["wire"] | T | T[:, ::-1]
    M["gold"] = M["gold"] | A | A[:, ::-1]

def build_strip(full=False):
    H = 128; SH = 4                                   # SH: tile row 0 = apex of a node
    M = Masks(48, H * 3); gems = []
    for rep in range(3):
        for u in range(2):
            strip_motif(M, rep * H + u * 64 + SH, u, gems)
        rect(M["gold"], 2, rep * H - 3, 4, rep * H + H + 3)                       # outer rail
        for yy in (0.5, 32.5, 64.5, 96.5, 128.5):                                  # rail knots on the nodes
            diamond(M["gold"], 3.0, rep * H + yy + SH + 0.5, 3.6, 3.6)
        for y in range(0, H, 4):                                                   # inner pearl line
            rect(M["gold"], 45, rep * H + y + 1, 46, rep * H + y + 2)
    idx = render(M, specs_of(gems))
    return idx if full else idx[H:2 * H]

# ------------------------------------------------------------------ corner 64 x 64
def build_corner():
    S = 64
    M = Masks(S, S); gems = []
    TG = np.zeros((S, S), bool); TW = np.zeros((S, S), bool)
    C = 14.5
    rect(TG, 0, 2, S + 6, 4)
    stroke(TG, line(C + 8, C + 8, 40.5, 40.5), ((0, 2),))
    diamond(TG, 31.0, 31.0, 4.0, 4.0)
    rect(TG, 22, 14, 58, 15)
    for (tx, R, th, W, m) in ((38.5, 8.5, 480, ((0, 3), (0.3, 2), (0.82, 1)), TG),
                              (53.5, 5.5, 470, ((0, 2), (0.65, 1)), TW)):
        volute(m, tx, 14.5, R, +1, th, W, 2.2, bead_mask=TG, bead=1.9 if R > 7 else 1.3)
    disc(TG, 59.5, 14.5, 2.1)
    for x in range(45, 62, 4):
        rect(TG, x, 7, x + 1, 8)
    G = TG | TG.T; Wr = TW | TW.T
    disc(G, C, C, 11.2)
    gems.append(gem_at(M, lambda m: disc(m, C, C, 6.0)))
    diamond(G, 44.0, 44.0, 7.5, 7.5)
    gems.append(gem_at(M, lambda m: diamond(m, 44.0, 44.0, 4.0, 4.0)))
    gems.append(gem_at(M, lambda m: rect(m, 30, 30, 31, 31)))
    M["gold"] = G; M["wire"] = Wr
    return render(M, specs_of(gems))

# ------------------------------------------------------------------ dividers
def build_divider():
    W, H = 160, 24
    M = Masks(W, H); gems = []
    cx = 79.5
    rect(M["gold"], 0, 2, W - 1, 4)
    T = np.zeros((H, W), bool)
    for x in range(133, 160, 4):                       # beaded line, phase 1,2 (mod 4) -> mirror-safe
        rect(T, x, 7, x + 1, 8)
    for x in range(1, 28, 4):
        rect(T, x, 7, x + 1, 8)
    # volutes hanging from the rail (right half), gold layer so thick parts get the bronze outline
    volute(T, 99.5, 4.0, 7.0, +1, 440, ((0, 3), (0.3, 2), (0.8, 1)), 2.2, bead_mask=T, bead=1.9)
    volute(T, 118.5, 4.0, 5.5, +1, 430, ((0, 2), (0.6, 1)), 1.8, bead_mask=T, bead=1.3)
    rect(T, 86, 11, 98, 12)                             # arm into the lozenge
    for nx in (99.0, 118.0):                            # nodes where the volutes leave the rail
        diamond(T, nx + 0.5, 4.0, 3.5, 3.5)
        disc(T, nx + 0.5 + 0.0, 4.0, 2.0)
    M["gold"] = M["gold"] | T | T[:, ::-1]
    diamond(M["gold"], cx, 12.0, 9.5, 11.5)
    gems.append(gem_at(M, lambda m: diamond(m, cx, 12.0, 5.0, 7.0)))
    return render(M, specs_of(gems))

def build_line_tile():
    W, H = 16, 24
    M = Masks(W * 3, H)
    rect(M["gold"], 0, 2, W * 3 - 1, 4)
    for x in range(1, W * 3, 4): rect(M["gold"], x, 7, x + 1, 8)
    idx = render(M, wrap="x")
    return idx[:, W:2 * W]

# ------------------------------------------------------------------ ornaments
def build_diamond():
    M = Masks(16, 24); gems = []
    diamond(M["gold"], 7.5, 11.5, 7.9, 11.9)
    gems.append(gem_at(M, lambda m: diamond(m, 7.5, 11.5, 4.2, 7.6)))
    return render(M, specs_of(gems))

def build_medallion():
    M = Masks(24, 24); gems = []
    c = 11.5
    disc(M["gold"], c, c, 11.4)
    def band(m):
        disc(m, c, c, 8.6); disc(m, c, c, 5.6, v=False)
    gems.append(gem_at(M, band))
    gems.append(gem_at(M, lambda m: disc(m, c, c, 2.0)))
    return render(M, specs_of(gems))

def build_finial():
    W = H = 24
    M = Masks(W, H); gems = []
    T = np.zeros((H, W), bool); TW = np.zeros((H, W), bool)
    pts = spiral(17.5, 11.5, 180, 180 + 460, 6.0, 2.6)
    stroke(TW, pts, ((0, 3), (0.35, 2), (0.75, 1)))
    disc(T, 17.5, 12.0, 1.6)
    M["wire"] = TW | TW[:, ::-1]; M["gold"] = T | T[:, ::-1]
    rect(M["gold"], 11, 5, 12, 20)
    disc(M["gold"], 11.5, 3.5, 2.2)
    diamond(M["gold"], 11.5, 20.5, 4.5, 3.5)
    gems.append(gem_at(M, lambda m: rect(m, 11, 19, 12, 20)))
    return render(M, specs_of(gems))

def build_glints():
    N, S = 6, 13
    sheet = np.zeros((S, S * N), np.uint8)
    arms = {   # frame -> list of (distance, colour) per arm; diag list
        0: ([(0, 14)], []),
        1: ([(0, 14), (1, 13)], []),
        2: ([(0, 14), (1, 13), (2, 12), (3, 11)], [(1, 13)]),
        3: ([(0, 14), (1, 13), (2, 13), (3, 12), (4, 12), (5, 11), (6, 10)], [(1, 13), (2, 12)]),
        4: ([(0, 14), (1, 13), (2, 12), (3, 11)], [(1, 12)]),
        5: ([(0, 13), (1, 11)], []),
    }
    for f, (ar, dg) in arms.items():
        ox, c = f * S, 6
        for d, col in ar:
            if d == 0: sheet[c, ox + c] = col; continue
            for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d)): sheet[c + dy, ox + c + dx] = col
        for d, col in dg:
            for dx, dy in ((d, d), (-d, d), (d, -d), (-d, -d)): sheet[c + dy, ox + c + dx] = col
    return sheet

# ------------------------------------------------------------------ palette / manifest / preview
PURPLE = [(1, "r0"), (2, "r1"), (3, "r2"), (4, "r3"), (5, "r4"), (6, "r5"), (7, "r6"), (8, "spec")]
GOLD = [(9, "g0", "dark bronze-brown (outline / shade)"), (10, "g1", "bronze (shadow side)"), (11, "g2", "antique gold (body)"),
        (12, "g3", "warm gold (lit edge)"), (13, "g4", "pale gold (highlight)"), (14, "glint", "specular glint")]

def write_palette():
    colors = [{"name": n, "hex": PAL[i], "group": "purple"} for i, n in PURPLE] + \
             [{"name": n, "hex": PAL[i], "group": "gold", "role": r} for i, n, r in GOLD]
    pj = {"name": "llc-manuscript-purple-gold", "colors": colors,
          "purple_ramp": [PAL[i] for i, _ in PURPLE[:7]], "purple_specular": PAL[8],
          "gold_ramp": [PAL[i] for i, _, _ in GOLD[:5]], "gold_specular": PAL[14],
          "notes": "purple ramp identical to ../palette.json (llc-violet-dusk); gold ramp hue-shifts bronze-brown (~10deg) -> pale yellow-gold (~47deg). Light from top-left."}
    json.dump(pj, open(os.path.join(OUT, "palette.json"), "w"), indent=2)
    css = ["/* illuminated-manuscript kit palette (purple ramp shared with ../palette.css) */", ":root {"]
    for i, n in PURPLE: css.append(f"  --ms-{n}: {PAL[i]};")
    for i, n, r in GOLD: css.append(f"  --ms-{n}: {PAL[i]}; /* {r} */")
    css.append("}")
    open(os.path.join(OUT, "palette.css"), "w").write("\n".join(css) + "\n")

def write_manifest():
    def sz(f): return list(Image.open(os.path.join(OUT, f)).size)
    E = lambda f, **k: dict(file=f, size=sz(f), **k)
    items = [
        E("vine-strip-left.png", tile="vertical (repeat-y), seamless top/bottom", usage="left hero edge: background:url() repeat-y left top; start under the TL corner (y=64) and stop above the BL corner. Row 0 is a node apex so it butts cleanly against a corner."),
        E("vine-strip-right.png", tile="vertical (repeat-y)", usage="exact horizontal mirror of the left strip; right hero edge, background-position: right top"),
        E("corner-tl.png", tile="no", usage="top-left corner flourish; rails (3px, x/y 2-4) run off the right/bottom edge to join strips and divider line tiles"),
        E("corner-tr.png", tile="no", usage="exact horizontal mirror of corner-tl"),
        E("corner-bl.png", tile="no", usage="exact vertical mirror of corner-tl"),
        E("corner-br.png", tile="no", usage="exact 180deg rotation (h+v mirror) of corner-tl"),
        E("divider-top.png", tile="centre piece; extend left/right with divider-line-tile (160 is a multiple of 16)", usage="centre under the top rail between the two top corners; hangs from a 3px rail"),
        E("divider-bottom.png", tile="centre piece", usage="exact vertical mirror of divider-top, for the bottom edge"),
        E("divider-line-tile.png", tile="horizontal (repeat-x), seamless", usage="rail + pearl line; repeat-x either side of the divider ornament (use the same tile both sides, it is mirror-symmetric); flip vertically for the bottom edge"),
        E("ornament-diamond.png", tile="no", usage="lozenge gem; bullet/section marker, chain between dividers"),
        E("ornament-medallion.png", tile="no", usage="round jewelled medallion; centre-piece above/below the logo"),
        E("ornament-finial.png", tile="no", usage="twin-volute scroll finial; top-centre cap or section ending"),
        E("gold-glint-sheet.png", tile="6 frames, 13x13 each, side by side", usage="CSS steps(6) animation; position over gold (gems, rails)"),
        E("preview.png", tile="no", usage="320x180 composed scene (not for production)"),
        E("preview@4x.png", tile="no", usage="nearest-neighbour 4x of preview.png"),
    ]
    kit = {"name": "llc-illuminated-manuscript-border-kit", "pixel_grid": 1, "scale": "native 1x; scale by integer factors only with image-rendering: pixelated",
           "light": "top-left", "alpha": "0/255 only", "colors": len(PAL) - 1, "palette": "palette.json",
           "no_motifs": "no vines, no leaves; scrollwork, volutes, lozenges, pearls, medallions only",
           "css": {
               "strip_left": ".hero::before{content:'';position:absolute;left:0;top:64px;bottom:64px;width:48px;background:url(vine-strip-left.png) repeat-y 0 0;image-rendering:pixelated}",
               "strip_right": "same with right:0 and vine-strip-right.png (exact mirror)",
               "divider_row": "[line-tile repeat-x] + divider-top.png (centred, 160px) + [line-tile repeat-x]; the tile is mirror-symmetric so the same file serves both sides",
               "glint": ".glint{width:13px;height:13px;background:url(gold-glint-sheet.png) 0 0/78px 13px;image-rendering:pixelated;animation:glint .9s steps(6) infinite}@keyframes glint{to{background-position:-78px 0}}"},
           "files": items, "generator": "generate.py", "qa": "python3 lint.py (alpha, palette, isolated pixels, mirrors, tile seams, joins; writes checks/*.png)"}
    json.dump(kit, open(os.path.join(OUT, "kit.json"), "w"), indent=2)

def save(img, name):
    img.save(os.path.join(OUT, name)); return img

def load(f): return Image.open(os.path.join(OUT, f)).convert("RGBA")

def build_preview():
    W, H = 320, 180
    bg = Image.new("RGBA", (W, H), rgb("#4d2a96") + (255,))
    for (y0, y1, col) in ((30, 150, "#7439b5"), (52, 128, "#a257c9")):   # hard bands, like the hub sky layers
        bg.paste(Image.new("RGBA", (W, y1 - y0), rgb(col) + (255,)), (0, y0))
    P = lambda im, x, y: bg.alpha_composite(im, (x, y))
    strip, strip_r = load("vine-strip-left.png"), load("vine-strip-right.png")
    P(strip.crop((0, 0, 48, 52)), 0, 64); P(strip_r.crop((0, 0, 48, 52)), 272, 64)
    P(load("corner-tl.png"), 0, 0); P(load("corner-tr.png"), 256, 0)
    P(load("corner-bl.png"), 0, 116); P(load("corner-br.png"), 256, 116)
    tile = load("divider-line-tile.png")
    for x in (64, 240):
        P(tile, x, 0); P(mirror_v(tile), x, 156)
    P(load("divider-top.png"), 80, 0); P(load("divider-bottom.png"), 80, 156)
    L = Image.open("/workspace/hub/logo/L.png").convert("RGBA"); C = Image.open("/workspace/hub/logo/C.png").convert("RGBA")
    lx = (W - (L.width + C.width)) // 2; ly = (H - L.height) // 2
    P(L, lx, ly); P(C, lx + L.width, ly)
    P(load("ornament-medallion.png"), 140, 25)
    P(load("ornament-finial.png"), 240, 100)
    P(load("ornament-diamond.png"), 49, 98); P(mirror_h(load("ornament-diamond.png")), 255, 73)
    sheet = load("gold-glint-sheet.png")
    fr = lambda i: sheet.crop((i * 13, 0, i * 13 + 13, 13))
    for (cx, cy, f) in ((11, 11, 3), (148, 38, 2), (245, 85, 4), (108, 11, 1), (212, 11, 5), (302, 168, 3), (80, 150, 2)):
        P(fr(f), cx - 6, cy - 6)
    return bg

def main():
    strip = to_img(build_strip()); save(strip, "vine-strip-left.png"); save(mirror_h(strip), "vine-strip-right.png")
    c = to_img(build_corner()); save(c, "corner-tl.png"); save(mirror_h(c), "corner-tr.png")
    save(mirror_v(c), "corner-bl.png"); save(mirror_h(mirror_v(c)), "corner-br.png")
    dv = to_img(build_divider()); save(dv, "divider-top.png"); save(mirror_v(dv), "divider-bottom.png")
    save(to_img(build_line_tile()), "divider-line-tile.png")
    save(to_img(build_diamond()), "ornament-diamond.png")
    save(to_img(build_medallion()), "ornament-medallion.png")
    save(to_img(build_finial()), "ornament-finial.png")
    save(to_img(build_glints()), "gold-glint-sheet.png")
    write_palette()
    pv = build_preview(); save(pv, "preview.png")
    save(pv.resize((pv.width * 4, pv.height * 4), Image.NEAREST), "preview@4x.png")
    write_manifest()

if __name__ == "__main__":
    main()
