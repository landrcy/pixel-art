"""Draws the LLC monogram v2 (L, L, C) as strict pixel art.  Run via generate.py."""
import math, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(__file__))
from pixlib import *

# 7-step hue-shifted ramp (cool indigo shadow -> warm pink-lavender light) + 1 specular
RAMP = ['#1a1245', '#2f1c6b', '#4d2a96', '#7439b5', '#a257c9', '#d083da', '#f5c4ec']
SPEC = '#fff1fb'
PAL = RAMP + [SPEC]
SS = 8

def seg(*segs):
    out = []
    for s in segs:
        pts = catmull(s, 14)
        out += pts if not out else pts[1:]
    return out

def leaf(tip, ang, length, half, notch=.34, bulge=.5):
    """arrow/fletch leaf. `tip` is the pointed end, `ang` the direction the tip points (deg)."""
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); vx, vy = -uy, ux
    def P(s, t): return (tip[0] - ux * s + vx * t, tip[1] - uy * s + vy * t)
    top = catmull([P(0, 0), P(length * .2, -half * .6), P(length * bulge, -half * .95), P(length * .82, -half * .8), P(length, -half * .95)], 10)
    bot = catmull([P(length, half * .95), P(length * .82, half * .8), P(length * bulge, half * .95), P(length * .2, half * .6), P(0, 0)], 10)
    return top + [P(length * (1 - notch), -half * .12), P(length * (1 - notch) , half * .12)] + bot

def leaf_vine(tip, ang, length, half):
    """plain pointed leaf (both ends pointed, slightly asymmetric) for vines. `tip` = free end."""
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); vx, vy = -uy, ux
    def P(s, t): return (tip[0] - ux * s + vx * t, tip[1] - uy * s + vy * t)
    top = catmull([P(0, 0), P(length * .22, -half * .72), P(length * .5, -half), P(length * .8, -half * .55), P(length, 0)], 10)
    bot = catmull([P(length, 0), P(length * .78, half * .6), P(length * .48, half), P(length * .2, half * .7), P(0, 0)], 10)
    return top + bot[1:]

def dots_on(path, step, size=2, start=0):
    """pixel dashes along a polyline at even arc-length spacing -> list of (x,y,dx,dy) tangents"""
    p = np.array(path, float); seg_ = np.hypot(*np.diff(p, axis=0).T); L = np.concatenate([[0], np.cumsum(seg_)])
    res = []
    for s in np.arange(start, L[-1], step):
        i = min(np.searchsorted(L, s), len(p) - 1)
        j = min(i + 1, len(p) - 1); k = max(i - 1, 0)
        t = p[j] - p[k]; t = t / (np.linalg.norm(t) + 1e-9)
        res.append((p[i][0], p[i][1], t[0], t[1]))
    return res

def curl_for(path, side, r0, r1, sweep, n=70):
    """spiral that continues `path` smoothly from its end (side=+1 clockwise on screen, -1 anticlockwise)."""
    p = np.array(path[-1], float); q = np.array(path[-4], float)
    t = (p - q) / np.linalg.norm(p - q)
    nrm = np.array([-t[1], t[0]]) * side
    c = p + nrm * r0
    a0 = math.degrees(math.atan2(*(p - c)[::-1]))
    return spiral(tuple(c), r0, r1, a0, a0 + side * sweep, n)

class Glyph:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.body = Mask(W, H, SS)     # outlined, bevelled solids (letter, leaves)
        self.linemask = np.zeros((H, W), bool)   # thin flourish strokes (no outline)
        self.veins = []                # (Mask, delta) detail strokes engraved into the body
        self.leaves = []               # (tip, ang, length, half)
        self.dash_rings = []           # (path, step, start)
        self.sparkles = []             # (x,y)
    def flourish(self, path, widths, curl=None):
        pts = list(path)
        if curl:
            c = curl_for(path, *curl); pts = pts + c[1:]
        # widths spread across whole path by arc-length
        self.linemask |= pp_stroke(pts, widths, self.W, self.H)
        return pts
    def vein(self, path, w, delta):
        m = Mask(self.W, self.H, SS); m.stroke(path, [w, w]); self.veins.append((m, delta))
    def render(self, body_R=6, body_base=3.3, body_gain=3.4, diag=3.4, line_base=3.3, line_gain=5.6, groove=5, gmode='diag', outline=True):
        W, H = self.W, self.H
        bm = clean_mask(self.body.to_bool(), 6)
        lm = clean_mask(self.linemask, 4) & ~bm
        idx = -np.ones((H, W), int)
        occ = lm | bm
        def empty(dy, dx):
            sh = np.roll(np.roll(occ, dy, 0), dx, 1)
            if dy > 0: sh[:dy] = False
            if dy < 0: sh[dy:] = False
            if dx > 0: sh[:, :dx] = False
            if dx < 0: sh[:, dx:] = False
            return ~sh
        up_e, left_e, dn_e, rt_e = empty(1, 0), empty(0, 1), empty(-1, 0), empty(0, -1)
        litE = (up_e | left_e) & ~(dn_e | rt_e)
        shE = (dn_e | rt_e) & ~(up_e | left_e)
        ys, xs = np.nonzero(lm); X, Y = np.meshgrid(np.arange(W), np.arange(H))
        gpos = (X / W + Y / H) / 2 if gmode == 'diag' else Y / H
        v = 3.9 + 1.0 * litE - 1.1 * shE + line_gain * (.5 - gpos) * .55
        q = np.clip(np.floor(v + .5), 2, 6).astype(int)
        idx[lm] = q[lm]
        self.bm, self.lm = bm, lm
        if bm.any():
            v, lit, d = shade_field(bm, body_R, body_base, body_gain, diag, sigma=.9)
            q = quantize(v, K=2.6, lo=1, hi=6)
            idx[bm] = q[bm]
        # engraved inline groove following the contour (dark line, then light lip on lit side)
        if groove and bm.any():
            g1 = bm & (d > groove - .5) & (d <= groove + .5)
            g1 &= ndi.binary_erosion(bm, iterations=groove)
            gl = np.zeros_like(bm)
            idx_g = idx.copy()
            idx[g1] = np.clip(idx[g1] - 2, 1, 6)
            lip = bm & (d > groove + .5) & (d <= groove + 1.5) & (lit > .9)
            idx[lip] = np.clip(idx[lip] + 1, 1, 6)
        for m, delta in self.veins:
            vm = m.to_bool() & bm
            idx[vm] = np.clip(idx[vm] + delta, 1, 6)
        # outline: darker tone of the local fill; lit-facing edges get a bright rim instead
        er = ndi.binary_erosion(bm, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]), border_value=0)
        edge = bm & ~er
        new = idx.copy()
        for y, x in zip(*np.nonzero(edge)):
            ox = oy = 0
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                yy, xx = y + dy, x + dx
                if not (0 <= yy < H and 0 <= xx < W) or not bm[yy, xx]:
                    ox += dx; oy += dy
            facing = ox * -LIGHT[0] + oy * -LIGHT[1]
            c = idx[y, x]
            new[y, x] = min(c + 1, 6) if facing > .4 else max(c - 2, 0)
        idx = new
        for lf in self.leaves: idx = self.draw_leaf(idx, *lf)
        return idx

    def draw_leaf(self, idx, tip, ang, length, half, style='fletch'):
        W, H = self.W, self.H
        m = Mask(W, H, SS); m.poly(leaf(tip, ang, length, half) if style == 'fletch' else leaf_vine(tip, ang, length, half)); lm_ = clean_mask(m.to_bool(), 3)
        a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); vx, vy = -uy, ux
        X, Y = np.meshgrid(np.arange(W) + .0, np.arange(H) + .0)
        s_ = -((X - tip[0]) * ux + (Y - tip[1]) * uy)       # distance back from tip
        t_ = (X - tip[0]) * vx + (Y - tip[1]) * vy           # signed perpendicular
        litside = np.sign(vx * -LIGHT[0] + vy * -LIGHT[1]) or 1.0
        on_lit = (t_ * litside) > 0
        base = np.where(on_lit, 5.2, 2.9)
        # soft ordered-dither band beside the midrib and towards the rim on the lit half
        edge_d = np.maximum(edt_in(lm_) - .5, 0)
        v = base + np.where(on_lit, -.9 * np.clip(1 - edge_d / 4, 0, 1) * 0 , 0) + np.where(on_lit, .6, -.5) * np.clip(1 - np.abs(t_) / (half * .8), 0, 1) * (1 if True else 0)
        v = np.where(on_lit, 5.0 + .9 * np.clip(1 - np.abs(t_) / (half * .9), 0, 1) - .3 * (s_ / length), 3.1 - .8 * np.clip(np.abs(t_) / (half * .9), 0, 1) - .4 * (s_ / length) * 0)
        q = quantize(v, K=2.6, lo=1, hi=6)
        idx[lm_] = q[lm_]
        # midrib: 1px ridge
        rib = pp_stroke([(tip[0] - ux * 2, tip[1] - uy * 2), (tip[0] - ux * length * .8, tip[1] - uy * length * .8)], [1, 1], W, H) & lm_
        if style == 'fletch' or length >= 14: idx[rib] = 6
        if style != 'fletch': return idx
        # outline
        er = ndi.binary_erosion(lm_, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]), border_value=0)
        for y, x in zip(*np.nonzero(lm_ & ~er)):
            ox = oy = 0
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                yy, xx = y + dy, x + dx
                if not (0 <= yy < H and 0 <= xx < W) or not lm_[yy, xx]: ox += dx; oy += dy
            facing = ox * -LIGHT[0] + oy * -LIGHT[1]
            idx[y, x] = 5 if facing > .4 else (1 if on_lit[y, x] and facing > -.4 else 1) if facing <= .4 else 5
        return idx

    def place_dashes(self, idx, pal_i=(4, 5)):
        H, W = idx.shape
        for path, step, start in self.dash_rings:
            for k, (x, y, tx, ty) in enumerate(dots_on(path, step, start=start)):
                xi, yi = int(round(x)), int(round(y))
                if abs(tx) > 1.9 * abs(ty): cells = [(xi, yi), (xi + 1, yi)]
                elif abs(ty) > 1.9 * abs(tx): cells = [(xi, yi), (xi, yi + 1)]
                else:
                    sx = 1 if tx * ty > 0 else -1
                    cells = [(xi, yi), (xi + sx, yi + 1)]
                if k % 4 == 1: cells = cells[:1] if False else cells
                col = 6 if k % 6 == 3 else pal_i[1] if k % 3 == 0 else pal_i[0]
                for cx, cy in cells:
                    if 0 <= cx < W and 0 <= cy < H and idx[cy, cx] < 0:
                        # keep a 1px clear gap around other art
                        y0, y1, x0, x1 = max(cy - 1, 0), cy + 2, max(cx - 1, 0), cx + 2
                        near = idx[y0:y1, x0:x1]
                        if (near >= 0).sum() == 0 or True:
                            idx[cy, cx] = col
        return idx

    def specular(self, idx, n=7, spacing=20, extra=()):
        """sparse bright specular pixels on the brightest top-left-facing spots."""
        cand = np.argwhere(idx == 6)
        # prefer top-left-most first inside each region: sort by distance to light corner weighted
        cand = sorted(cand.tolist(), key=lambda p: p[0] * .9 + p[1])
        chosen = []
        for y, x in cand:
            if all((y - cy) ** 2 + (x - cx) ** 2 > spacing ** 2 for cy, cx in chosen):
                chosen.append((y, x))
            if len(chosen) >= n: break
        for y, x in chosen: idx[y, x] = 7
        for x, y in extra: idx[y, x] = 7
        return idx

    def sparkle(self, idx, x, y, r=4):
        """hand-placed 4-point twinkle: bright core, tapering arms, soft diagonal pips"""
        cols = {0: 7, 1: 7, 2: 6, 3: 5, 4: 4}
        for k in range(0, r + 1):
            c = cols[min(k, 4)]
            for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
                idx[y + dy, x + dx] = c
        for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            idx[y + dy, x + dx] = 4
        return idx

def qbez(p0, p1, p2, n=14):
    return [((1-t)**2*p0[0]+2*(1-t)*t*p1[0]+t*t*p2[0], (1-t)**2*p0[1]+2*(1-t)*t*p1[1]+t*t*p2[1]) for t in np.linspace(0, 1, n)]

def build_L():
    W, H = 188, 244
    g = Glyph(W, H)
    B = g.body
    poly = []
    poly += [(46, 44), (108, 44), (112, 47), (112, 52)]
    poly += qbez((112, 52), (101, 54), (97, 64))
    poly += [(97, 64), (97, 160)]
    poly += qbez((97, 160), (98, 169), (110, 170))
    poly += [(110, 170), (133, 170), (134, 158), (138, 150), (157, 143)]
    poly += [(157, 143), (158, 172), (156, 190)]
    poly += qbez((156, 190), (153, 200), (141, 201))
    poly += [(141, 201), (63, 201), (58, 198), (58, 193)]
    poly += qbez((58, 193), (69, 190), (72, 174))
    poly += [(72, 174), (72, 64)]
    poly += qbez((72, 64), (66, 57), (51, 55), 14)
    poly += [(42, 54), (38, 51), (38, 47)]
    B.poly(poly)
    # --- flourishes
    outer = catmull([(112, 12.5), (94, 13), (70, 18), (50, 27), (34, 40), (24, 58), (19, 80), (17, 104), (17, 124), (19, 146), (24, 168), (34, 192), (50, 213), (74, 228), (102, 235), (126, 235), (146, 230)], 14)
    g.flourish(outer, [1.4, 3.0, 4.0, 4.4, 4.2, 4.6, 4.4, 3.6, 2.0], curl=None)
    c1 = curl_for(outer[::-1], +1, 0, 0, 0) if False else None
    top_run = catmull([(112, 12.5), (124, 11.5), (134, 12.5)], 10)
    g.flourish(top_run + curl_for(top_run, +1, 10, 3.2, 340)[1:], [2.4, 3.0, 3.2, 3.2, 3.0, 2.4, 2.0])
    bot_run = catmull([(146, 230), (156, 225), (162, 219)], 10)
    g.flourish(bot_run + curl_for(bot_run, -1, 9, 3.0, 340)[1:], [2.4, 3.0, 3.0, 2.8, 2.4, 2.0])
    inner_top = catmull([(96, 31), (108, 30), (116, 31)], 10)
    g.flourish(inner_top + curl_for(inner_top, +1, 7, 2.6, 330)[1:], [3.0, 3.2, 3.0, 2.8, 2.4, 2.0])
    inner = catmull([(98, 31), (92, 31), (66, 38), (49, 50), (39, 68), (35, 90), (34, 124), (36, 150), (42, 172), (54, 192), (70, 207), (94, 215), (120, 216), (142, 210), (154, 201)], 14)
    g.flourish(inner, [1.4, 2.8, 3.4, 3.2, 3.0, 3.4, 3.4, 2.8, 1.6])
    sw = catmull([(108, 50), (126, 52), (146, 62), (162, 78), (170, 96)], 14)
    g.flourish(sw, [3.6, 3.4, 3.0, 2.4, 1.8])
    hook = catmull([(98, 142), (110, 146), (124, 146), (134, 139)], 12)
    g.flourish(hook + curl_for(hook, -1, 10, 3.2, 360)[1:], [2.0, 3.0, 3.4, 3.2, 3.0, 2.6, 2.2])
    g.leaves += [((0, 124), 180, 26, 8.5), ((184, 107), 28, 26, 8.5), ((106, 6), 0, 19, 5), ((162, 193), -38, 17, 5.5)]
    # --- dotted ring between the two brackets
    ring = catmull([(104, 21), (76, 25), (52, 35), (38, 52), (28, 74), (25, 100), (25, 124), (27, 150), (33, 178), (46, 201), (66, 217), (92, 225), (118, 226), (140, 220)], 14)
    g.dash_rings.append((ring, 5.6, 3))
    return g, poly

def build_C():
    W, H = 216, 244
    g = Glyph(W, H); B = g.body
    cx, cy = 108, 124
    outer = arc((cx, cy), 54, 82, -38, -322, 120)
    inner = arc((122, cy), 30, 58, -322, -38, 120)[::1]
    # outer runs top->left->bottom, inner returns bottom->left->top
    poly = outer + inner
    B.poly(poly)
    # terminals (flag serifs) top & bottom
    top_t = [(136, 67), (150, 60), (163, 61), (169, 65), (167, 84), (161, 103), (156, 94), (147, 96), (136, 95)]
    B.poly(top_t)
    bot_t = [(x, 2 * cy - y) for x, y in top_t]
    B.poly(bot_t)
    # flourishes
    brk = catmull([(150, 13), (130, 12.5), (100, 16), (68, 28), (44, 50), (30, 80), (24, 108), (23, 124), (24, 140), (30, 168), (44, 198), (68, 220), (100, 231), (130, 234.5), (150, 234)], 14)
    g.flourish(brk, [1.8, 3.4, 4.2, 4.6, 4.4, 4.0, 4.0, 4.6, 4.2, 3.4, 1.8])
    t_run = catmull([(150, 13), (170, 14), (186, 15.5)], 10)
    g.flourish(t_run + curl_for(t_run, +1, 11, 3.2, 345)[1:], [2.6, 3.0, 3.2, 3.2, 3.0, 2.6, 2.0])
    b_run = catmull([(150, 234), (170, 233), (186, 230.5)], 10)
    g.flourish(b_run + curl_for(b_run, -1, 11, 3.2, 345)[1:], [2.6, 3.0, 3.2, 3.2, 3.0, 2.6, 2.0])
    inn = catmull([(142, 31), (112, 30), (88, 34), (66, 47), (51, 70), (44, 98), (42, 124), (44, 150), (51, 178), (66, 201), (88, 214), (112, 218), (142, 217)], 14)
    g.flourish(inn, [1.4, 2.8, 3.4, 3.4, 3.2, 3.0, 3.0, 3.2, 3.4, 3.4, 2.8, 1.4])
    sw = catmull([(160, 62), (178, 60), (194, 68), (204, 80)], 12)
    g.flourish(sw, [3.4, 3.2, 2.6, 2.0])
    sw2 = catmull([(160, 186), (178, 188), (194, 180), (204, 168)], 12)
    g.flourish(sw2, [3.4, 3.2, 2.6, 2.0])
    hook = catmull([(94, 134), (108, 142), (124, 144), (138, 138)], 12)
    g.flourish(hook + curl_for(hook, -1, 11, 3.2, 360)[1:], [2.0, 3.0, 3.4, 3.2, 3.0, 2.6, 2.2])
    g.leaves += [((0, 124), 180, 26, 8.5), ((214, 90), 24, 24, 8), ((214, 158), -24, 24, 8), ((118, 5), 0, 19, 5)]
    ring = catmull([(150, 21.5), (118, 21), (86, 26), (58, 40), (38, 62), (31, 92), (30, 124), (31, 156), (38, 186), (58, 208), (86, 222), (118, 227), (150, 226.5)], 14)
    g.dash_rings.append((ring, 5.6, 3))
    return g

def finish(g, sparkles=()):
    idx = g.render()
    idx = despeckle(idx)
    idx = g.specular(idx)
    idx = g.place_dashes(idx)
    for (x, y) in sparkles: idx = g.sparkle(idx, x, y)
    return idx

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logo', 'v2')
def make_all(out=OUT):
    os.makedirs(out, exist_ok=True)
    gl, _ = build_L(); il = finish(gl, [(52, 98)])
    gl2, _ = build_L(); il2 = finish(gl2, [(150, 120)])
    gc = build_C(); ic = finish(gc, [(150, 124)])
    paths = {}
    for name, idx in (('L1', il), ('L2', il2), ('C', ic)):
        p = os.path.join(out, name + '.png'); save_rgba(idx, PAL, p); paths[name] = p
    # composed preview
    ims = [Image.open(paths[n]) for n in ('L1', 'L2', 'C')]
    xs = [0, 190, 190 + 188]
    Wt = xs[2] + ims[2].width; prev = Image.new('RGBA', (Wt, 244), (0, 0, 0, 0))
    for im, x in zip(ims, xs): prev.alpha_composite(im, (x, 0))
    prev.save(os.path.join(out, 'LLC.png'))
    return paths

if __name__ == '__main__':
    make_all()
    v = os.environ.get('V', '0')
    for n in ('L1', 'C', 'LLC'):
        im = Image.open(os.path.join(OUT, n + '.png'))
        up(im, 4, (13, 10, 26, 255)).save(f'/tmp/v/{n}_{v}.png')
