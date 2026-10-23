#!/usr/bin/env python3
"""LLC hub intro — scene 1 ("violet dusk garden").  Re-runnable generator:

    python3 generate.py            # writes logo/v2/*.png and intro-art/*.png|json|css

Everything is drawn on one 320x180 pixel grid, nearest-neighbour only, binary alpha, tiny palette.
"""
import json, math, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pixlib import *
import logo_v2 as LV

W, H = 320, 180
rng = np.random.default_rng(1303)

# ---------------------------------------------------------------- palette
# index: name, hex.  r0..r6 is the logo's 7-step hue-shifted ramp; void/n1 extend it down for the night sky.
SC = [('void', '#0d0a1a'), ('n1', '#150f33'),
      ('r0', '#1a1245'), ('r1', '#2f1c6b'), ('r2', '#4d2a96'), ('r3', '#7439b5'),
      ('r4', '#a257c9'), ('r5', '#d083da'), ('r6', '#f5c4ec'), ('spec', '#fff1fb')]
PALH = [h for _, h in SC]
R = lambda i: i + 2          # logo-ramp index -> scene palette index
SPEC = 9

def to_img(idx):
    a = np.zeros(idx.shape + (4,), np.uint8)
    for i, h in enumerate(PALH): a[idx == i] = (*hexrgb(h), 255)
    return Image.fromarray(a, 'RGBA')

def new(w=W, h=H): return -np.ones((h, w), int)

def tile3(fn, w=W, h=H):
    """draw on a 3x wide canvas then keep the middle => seamless horizontal tiling"""
    big = fn(w * 3, h)
    return big[:, w:2 * w]

# ---------------------------------------------------------------- sky
def make_sky():
    X, Y = np.meshgrid(np.arange(W), np.arange(H))
    t = Y / (H - 1)
    glow = np.exp(-((Y - 150) / 22.0) ** 2) * (.55 + .45 * np.cos(2 * np.pi * (X - 160) / W))
    v = 6.3 * t ** 1.9 + 1.5 * glow
    idx = quantize(v, bayer=BAYER4, K=2.0, lo=0, hi=7)
    return idx

# ---------------------------------------------------------------- stars
def make_stars(sky):
    idx = new()
    anchors = []
    occupied = np.zeros((H, W), bool)
    def free(x, y, r=3):
        return not occupied[max(y - r, 0):y + r + 1, max(x - r, 0):x + r + 1].any()
    def put(x, y, c, r=3):
        idx[y, x % W] = c; occupied[y, x % W] = True
    # anchors for the twinkling sprite (hand-picked so they frame the logo area)
    for (x, y) in ((34, 30), (92, 18), (132, 60), (190, 24), (290, 70), (62, 84), (210, 96)):
        anchors.append((x, y))
        put(x, y, SPEC)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)): put(x + dx, y + dy, R(5))
    n = 0; tries = 0
    while n < 90 and tries < 4000:
        tries += 1
        y = int(rng.random() ** 1.5 * 112); x = int(rng.integers(0, W))
        if not free(x, y, 3) or sky[y, x] > 4: continue
        k = rng.random()
        if k < .62: put(x, y, R(5) if rng.random() < .55 else R(4))
        elif k < .86: put(x, y, R(6))
        elif k < .95:                       # 2px dim pair, reads as a soft star
            put(x, y, R(4)); put(x + 1, y, R(3))
        else:                               # tiny plus
            put(x, y, R(6))
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)): put(x + dx, y + dy, R(4))
        n += 1
    return idx, anchors

# ---------------------------------------------------------------- moon
def make_moon():
    idx = new()
    cx, cy, r = 258, 40, 16
    X, Y = np.meshgrid(np.arange(W) + .5, np.arange(H) + .5)
    d = np.hypot(X - cx, Y - cy)
    th = np.tile(BAYER4, (H // 4 + 1, W // 4 + 1))[:H, :W]
    halo = np.clip(1 - (d - r) / 22.0, 0, 1)
    for lo, c in ((.50, R(2)), (.22, R(1))):
        m = (d > r) & (halo > lo + (th - .5) * .26)
        idx[m & (idx < 0)] = c
    disc = d <= r
    cut = np.hypot(X - (cx + 8), Y - (cy - 1.5)) <= r * .93      # shadow disc shifted right: lit limb on the left
    lit = disc & ~cut
    # earth-lit dark limb: nearly sky colour, dithered edge so it melts into the halo
    dark = disc & cut
    idx[dark] = R(1)
    idx[dark & (th < .3)] = R(2)
    din = np.maximum(edt_in(lit) - .5, 0)
    gx = (X - (cx - r)) / (2 * r); gy = (Y - (cy - r)) / (2 * r)
    v = 6.35 + 1.1 * np.clip(1 - din / 4.5, 0, 1) * 0 - .9 * np.clip(din / 6, 0, 1) + .8 * (.5 - (gx + gy) / 2)
    q = quantize(v, K=2.0, lo=5, hi=8)
    idx[lit] = q[lit] + 2 - 2 + 0 if False else np.clip(q[lit], 5, 8) 
    for (px, py) in ((251, 33), (249, 46)):
        idx[py, px] = R(4); idx[py, px + 1] = R(4)
    return idx

# ---------------------------------------------------------------- vines / foliage helpers
def to_scene(gidx, shift, lo=0):
    """logo-glyph index (0..6, 7=spec) -> scene palette index, shifted darker by `shift` ramp steps"""
    out = np.where(gidx < 0, -1, np.clip(gidx + shift + 2, lo, 9))
    return out

def vine_path(base, ang, length, sway, lam, phase=0, step=9):
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); vx, vy = -uy, ux
    pts = []
    for s_ in np.arange(0, length + step, step):
        off = sway * math.sin(2 * math.pi * s_ / lam + phase) * min(1, s_ / 16)
        pts.append((base[0] + ux * s_ + vx * off, base[1] + uy * s_ + vy * off))
    return catmull(pts, 10)

def add_vine(g, base, ang, length, sway, lam, phase, w0, w1, curl_side, curl_r, leaves, leaf_len=12, leaf_half=4, rng=rng, offs=0):
    path = vine_path(base, ang, length, sway, lam, phase)
    widths = [w0, (w0 + w1) / 2, w1, max(w1 - .6, 1.4)]
    pts = g.flourish(path, widths, curl=(curl_side, curl_r, curl_r * .32, 330))
    # leaves along the stem (alternate sides)
    P = np.array(path); seg = np.hypot(*np.diff(P, axis=0).T); L = np.concatenate([[0], np.cumsum(seg)])
    for k in range(leaves):
        f = .18 + .72 * (k + .5) / leaves
        i = int(np.searchsorted(L, f * L[-1])); i = min(max(i, 2), len(P) - 3)
        t = P[i + 2] - P[i - 2]; ta = math.degrees(math.atan2(t[1], t[0]))
        side = 1 if (k + offs) % 2 == 0 else -1
        la = ta + side * rng.uniform(48, 62)
        sz = leaf_len * (1.08 - .5 * f) * rng.uniform(.9, 1.1)
        hh = leaf_half * (1.05 - .4 * f)
        ar = math.radians(la)
        att = P[i]
        tip = (att[0] + math.cos(ar) * sz, att[1] + math.sin(ar) * sz)
        g.leaves.append((tip, la, sz, hh, 'vine'))
    return pts

def glyph_layer(g, shift, **kw):
    idx = g.render(groove=0, **kw)
    return to_scene(idx, shift)

def ridge(w, amp, base, cycles):
    x = np.arange(w)
    y = np.full(w, float(base))
    for (c, a, ph) in cycles:
        y += a * np.sin(2 * np.pi * c * x / W + ph)
    return y

def hill(idx, ridge_y, fill_top, fill_bot, rim, depth=26, dither_to=None):
    """filled silhouette below ridge_y[x]; vertical Bayer-dithered gradient fill_top -> fill_bot; 1px rim light"""
    h, w = idx.shape
    th = np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w]
    for x in range(w):
        y0 = int(round(ridge_y[x]))
        for y in range(max(y0, 0), h):
            t = np.clip((y - y0) / depth, 0, 1)
            f = np.clip((t - .5) * 2.0 + .5, 0, 1)
            idx[y, x] = fill_bot if (f > th[y, x] and t > .15) else fill_top
        if 0 <= y0 < h: idx[y0, x] = rim
    return idx

def tufts(idx, ridge_y, col, rim, xs, hmax=4):
    """tiny two-column grass blades on the crest"""
    h, w = idx.shape
    for x in xs:
        x %= w
        y0 = int(round(ridge_y[x])); k = int(rng.integers(3, hmax + 1))
        for j in range(1, k): idx[y0 - j, x] = col
        idx[y0 - k + 1, x] = rim if k > 3 else col
        if k >= 3:
            for j in range(1, k - 1): idx[y0 - j, (x + 1) % w] = col
            idx[y0 - 1, (x + 1) % w] = col
    return idx

# ---------------------------------------------------------------- far layer: distant ridge + fern spires
def make_far():
    def draw(w, h):
        idx = new(w, h)
        ry = ridge(w, 0, 154, [(2, 5, .6), (5, 2.6, 1.9), (9, 1.2, .3)])
        # spires (tall slender fronds with a curled head) behind/on the ridge
        g = LV.Glyph(w, h)
        r2 = np.random.default_rng(7)
        for k, x0 in enumerate(range(12, W, 40)):
            for rep in range(3):
                bx = x0 + rep * W + int(r2.integers(-6, 6))
                by = ry[bx % w if bx < w else bx - W] + 3
                ang = -90 + r2.uniform(-12, 12)
                ln = r2.uniform(20, 44)
                add_vine(g, (bx, by), ang, ln, r2.uniform(3, 5), r2.uniform(24, 40), r2.uniform(0, 6), 2.4, 1.8, 1 if k % 2 else -1, r2.uniform(5, 6.5), int(ln // 14), 9, 3, rng=r2, offs=k)
        art = glyph_layer(g, -2, gmode='y', line_gain=2.0)
        idx[:] = art
        idx = hill(idx, ry, R(2), R(1), R(4), depth=30)
        # soft dither highlight just under the rim
        return idx
    return tile3(draw)

def make_mid():
    def draw(w, h):
        idx = new(w, h)
        g = LV.Glyph(w, h)
        r2 = np.random.default_rng(23)
        # hanging vines from the top edge
        for k, x0 in enumerate((56, 106, 154, 198)):
            for rep in range(3):
                bx = x0 + rep * W
                ln = r2.uniform(34, 78) if k not in (3,) else 28
                add_vine(g, (bx, -6), 90 + r2.uniform(-10, 10), ln, r2.uniform(4, 7), r2.uniform(30, 46), r2.uniform(0, 6), 3.6, 2.4, 1 if k % 2 else -1, r2.uniform(6, 8.5), int(ln // 13), 13, 4.4, rng=r2, offs=k)
        art = glyph_layer(g, -3, gmode='y', line_gain=2.0)
        # ground: near hill with grass tufts
        ry = ridge(w, 0, 163, [(3, 4.0, 2.2), (7, 1.8, .7)])
        idx[:] = art
        # rising vines from the ground (drawn in a second glyph pass so they overlap the hill edge)
        g2 = LV.Glyph(w, h)
        for k, x0 in enumerate((52, 88, 236, 270)):
            for rep in range(3):
                bx = x0 + rep * W
                by = ry[(bx % W) + W] + 4
                ln = r2.uniform(30, 52)
                add_vine(g2, (bx, by), -90 + r2.uniform(-18, 18), ln, r2.uniform(4, 8), r2.uniform(26, 44), r2.uniform(0, 6), 3.8, 2.2, 1 if k % 2 else -1, r2.uniform(6, 9), int(ln // 12), 13, 4.6, rng=r2, offs=k)
        art2 = glyph_layer(g2, -4, gmode='y', line_gain=1.2)
        idx = np.where(art2 >= 0, art2, idx)
        idx = hill(idx, ry, R(0), 0, R(2), depth=22)
        return idx
    return tile3(draw)

# ---------------------------------------------------------------- foreground frame
class Quad:
    """draw the top-left corner design once; replicate to the four corners (flip points/angles/curl sides)."""
    def __init__(self, g): self.g = g
    def _t(self, p, mx, my): return (p[0] if mx > 0 else W - 1 - p[0], p[1] if my > 0 else H - 1 - p[1])
    def each(self, fn):
        for mx, my in ((1, 1), (-1, 1), (1, -1), (-1, -1)): fn(mx, my)
    def poly(self, pts):
        self.each(lambda mx, my: self.g.body.poly([self._t(p, mx, my) for p in pts]))
    def line(self, path, widths, curl=None):
        def f(mx, my):
            c = (curl[0] * mx * my, *curl[1:]) if curl else None
            self.g.flourish([self._t(p, mx, my) for p in path], widths, curl=c)
        self.each(f)
    def leaf(self, tip, ang, ln, hf, style='fletch'):
        def f(mx, my):
            a = ang
            if mx < 0: a = 180 - a
            if my < 0: a = -a
            self.g.leaves.append((self._t(tip, mx, my), a, ln, hf, style))
        self.each(f)

def make_frame():
    g = LV.Glyph(W, H); q = Quad(g)
    B = g.body
    # edge bars (3px)
    B.poly([(0, 0), (W, 0), (W, 3), (0, 3)]); B.poly([(0, H - 3), (W, H - 3), (W, H), (0, H)])
    B.poly([(0, 0), (3, 0), (3, H), (0, H)]); B.poly([(W - 3, 0), (W, 0), (W, H), (W - 3, H)])
    # corner jewel + inward leaf + two inset rules that end in curls
    q.poly([(9, 0), (19, 9), (9, 19), (0, 9)])
    q.leaf((34, 34), 45, 18, 5.6, style='vine')
    top = catmull([(21, 7.5), (44, 7), (76, 7)], 10)
    q.line(top, [3.0, 3.0, 2.4], curl=(+1, 9, 2.8, 335))
    left = catmull([(7.5, 21), (7, 44), (7, 76)], 10)
    q.line(left, [3.0, 3.0, 2.4], curl=(-1, 9, 2.8, 335))
    # edge-centre jewels
    cx, cy = W // 2, H // 2
    B.poly([(cx - 14, 0), (cx + 14, 0), (cx + 8, 4), (cx, 11), (cx - 8, 4)])
    B.poly([(cx - 14, H), (cx + 14, H), (cx + 8, H - 4), (cx, H - 11), (cx - 8, H - 4)])
    B.poly([(0, cy - 14), (0, cy + 14), (4, cy + 8), (11, cy), (4, cy - 8)])
    B.poly([(W, cy - 14), (W, cy + 14), (W - 4, cy + 8), (W - 11, cy), (W - 4, cy - 8)])
    art = g.render(body_R=3, body_base=4.1, body_gain=3.4, diag=2.2, line_gain=3.0, groove=0)
    art = despeckle(art)
    # the frame is the near-black, lit-from-top-left silhouette: shift ramp down 2 so it stays dark but readable
    out = to_scene(art, -3)
    # dithered inner shadow hugging the frame (ordered dither, void colour)
    X, Y = np.meshgrid(np.arange(W), np.arange(H))
    e = np.minimum(np.minimum(X, W - 1 - X), np.minimum(Y, H - 1 - Y))
    sv = np.clip(1 - (e - 3) / 8.0, 0, 1) * .55
    th = np.tile(BAYER4, (H // 4 + 1, W // 4 + 1))[:H, :W]
    out[(sv > th) & (out < 0)] = 0
    return out

# ---------------------------------------------------------------- twinkle sprite sheet
FS = 15
def make_sparkles():
    sheet = new(FS * 6, FS)
    arm_col = {1: SPEC, 2: R(6), 3: R(5), 4: R(5), 5: R(4), 6: R(4), 7: R(3)}
    for f, (r, diag) in enumerate(((1, 0), (2, 0), (4, 1), (7, 2), (4, 1), (2, 0))):
        ox, oy = f * FS + 7, 7
        sheet[oy, ox] = SPEC
        for k in range(1, r + 1):
            c = arm_col[k] if r > 2 else (R(6) if k == 1 else R(5))
            if r == 1: c = R(6)
            for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)): sheet[oy + dy, ox + dx] = c
        if diag >= 1:
            for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)): sheet[oy + dy, ox + dx] = R(5)
        if diag >= 2:
            for dx, dy in ((2, 2), (-2, 2), (2, -2), (-2, -2)): sheet[oy + dy, ox + dx] = R(4)
    return sheet

# ---------------------------------------------------------------- output
def main():
    V = os.environ.get('V')
    logo_paths = LV.make_all()
    sky = make_sky(); stars, anchors = make_stars(sky); moon = make_moon()
    far = make_far(); mid = make_mid(); frame = make_frame(); spk = make_sparkles()
    layers = [('sky', sky, True), ('stars', stars, False), ('moon', moon, False), ('far', far, False), ('mid', mid, False), ('frame', frame, False)]
    for name, arr, _ in layers:
        to_img(arr).save(os.path.join(HERE, f'layer-{["sky","stars","moon","far","mid","frame"].index(name)}-{name}.png'))
    to_img(spk).save(os.path.join(HERE, 'sparkle-sheet.png'))
    comp = sky.copy()
    for _, L, _ in layers[1:]: comp = np.where(L >= 0, L, comp)
    prev = to_img(comp)
    prev.save(os.path.join(HERE, 'preview.png'))
    prev.resize((W * 4, H * 4), Image.NEAREST).save(os.path.join(HERE, 'preview@4x.png'))
    # logo composited over the scene: scene at 4x, logo at 1x (logo is ~2x the detail of the old 94x122 art, so its pixels are drawn finer than the scene's)
    big = prev.resize((W * 4, H * 4), Image.NEAREST)
    logo = Image.open(logo_paths['L1']).copy(); full = Image.open(os.path.join(os.path.dirname(logo_paths['L1']), 'LLC.png'))
    big.alpha_composite(full, ((big.width - full.width) // 2, (big.height - full.height) // 2 - 30))
    big.save(os.path.join(HERE, 'preview-with-logo@4x.png'))
    # palette files
    pal = [{'name': n, 'hex': h} for n, h in SC]
    json.dump({'name': 'llc-violet-dusk', 'size': [W, H], 'colors': pal,
               'ramp': {'description': '7-step hue-shifted purple ramp, cool indigo shadow -> warm pink-lavender light; light from top-left',
                        'steps': [h for n, h in SC[2:9]], 'specular': SC[9][1]},
               'night_extension': [SC[0][1], SC[1][1]]}, open(os.path.join(HERE, 'palette.json'), 'w'), indent=2)
    css = ['/* LLC hub intro art palette (generated by generate.py) */', ':root{']
    for n, h in SC: css.append(f'  --ia-{n}: {h};')
    css += ['  --ia-ramp-0: var(--ia-r0); --ia-ramp-1: var(--ia-r1); --ia-ramp-2: var(--ia-r2); --ia-ramp-3: var(--ia-r3);',
            '  --ia-ramp-4: var(--ia-r4); --ia-ramp-5: var(--ia-r5); --ia-ramp-6: var(--ia-r6);', '}']
    open(os.path.join(HERE, 'palette.css'), 'w').write('\n'.join(css) + '\n')
    json.dump({'size': [W, H], 'scale_note': 'integer scale only (1x,2x,3x,4x...) with image-rendering:pixelated',
               'layers': [{'file': f'layer-{i}-{n}.png', 'z': i, 'opaque': n == 'sky',
                           'tileable_x': n in ('stars', 'far', 'mid'), 'suggested_drift_px_per_s': {'sky': 0, 'stars': 1, 'moon': 0, 'far': 3, 'mid': 7, 'frame': 0}[n]}
                          for i, (n, _, _) in enumerate(layers)],
               'sparkle': {'file': 'sparkle-sheet.png', 'frame_size': [FS, FS], 'frames': 6, 'sheet_size': [FS * 6, FS],
                           'suggested_css': 'animation: tw 0.8s steps(6) infinite; @keyframes tw { to { background-position-x: -%dpx } }' % (FS * 6),
                           'anchors_center_px': anchors}},
              open(os.path.join(HERE, 'scene.json'), 'w'), indent=2)
    if V:
        prev.resize((W * 4, H * 4), Image.NEAREST).save(f'/tmp/v/scene_{V}.png')

if __name__ == '__main__':
    main()
