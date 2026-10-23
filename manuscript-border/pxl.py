"""pxl.py - tiny mask-based pixel drawing + auto bevel shader for the manuscript kit."""
import math
import numpy as np

# ---- palette (index -> hex) ----
PAL = {
    0: None,
    1: "#1a1245", 2: "#2f1c6b", 3: "#4d2a96", 4: "#7439b5", 5: "#a257c9", 6: "#d083da", 7: "#f5c4ec", 8: "#fff1fb",
    9: "#3d1f17", 10: "#7c4420", 11: "#b9792a", 12: "#e8b546", 13: "#fbe8a0", 14: "#fffbe3",
}
NAMES = {1: "r0", 2: "r1", 3: "r2", 4: "r3", 5: "r4", 6: "r5", 7: "r6", 8: "spec",
         9: "g0", 10: "g1", 11: "g2", 12: "g3", 13: "g4", 14: "glint"}
def rgb(h): return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))

class Masks:
    """a set of boolean layers on one canvas"""
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.L = {k: np.zeros((h, w), bool) for k in ("gold", "wire", "gem", "carve", "dark", "gemdark")}
        self.px = {}  # (x,y)->index explicit overrides applied last (gets applied in order)
    def __getitem__(self, k): return self.L[k]
    def __setitem__(self, k, v): self.L[k] = v

def inb(m, x, y): return 0 <= x < m.shape[1] and 0 <= y < m.shape[0]
def put(m, x, y, v=True):
    if inb(m, x, y): m[y, x] = v

def disc(m, cx, cy, r, rin=None, v=True):
    h, w = m.shape
    ys, xs = np.mgrid[0:h, 0:w]
    d = np.hypot(xs - cx, ys - cy)
    sel = d <= r
    if rin is not None: sel &= d > rin
    if v: m |= sel
    else: m &= ~sel

def ellipse(m, cx, cy, rx, ry, rin=None, v=True):
    h, w = m.shape
    ys, xs = np.mgrid[0:h, 0:w]
    d = np.hypot((xs - cx) / rx, (ys - cy) / ry)
    sel = d <= 1
    if rin is not None: sel &= d > rin
    if v: m |= sel
    else: m &= ~sel

def diamond(m, cx, cy, a, b, v=True):
    h, w = m.shape
    ys, xs = np.mgrid[0:h, 0:w]
    sel = (np.abs(xs - cx) / a + np.abs(ys - cy) / b) <= 1.0
    if v: m |= sel
    else: m &= ~sel

def rect(m, x0, y0, x1, y1, v=True):
    """inclusive"""
    h, w = m.shape
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(w - 1, x1), min(h - 1, y1)
    if x1 >= x0 and y1 >= y0:
        m[y0:y1 + 1, x0:x1 + 1] = v

# ---- paths ----
def _bres(p, q):
    (x0, y0), (x1, y1) = p, q
    pts = []
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx - dy
    while True:
        pts.append((x0, y0))
        if (x0, y0) == (x1, y1): break
        e2 = 2 * err
        if e2 > -dy: err -= dy; x0 += sx
        if e2 < dx: err += dx; y0 += sy
    return pts

def raster(samples):
    """samples: [(x,y,t)] floats -> pixel-perfect ordered [(x,y,t)] (8-connected, no L-corners)"""
    pts = []
    for x, y, t in samples:
        q = (int(math.floor(x + 0.5)), int(math.floor(y + 0.5)))
        if pts and pts[-1][:2] == q: continue
        if pts and max(abs(q[0] - pts[-1][0]), abs(q[1] - pts[-1][1])) > 1:
            for b in _bres(pts[-1][:2], q)[1:]:
                pts.append((b[0], b[1], t))
        else:
            pts.append((q[0], q[1], t))
    # pixel perfect: drop corner pixel of L triples
    out = []
    for p in pts:
        out.append(p)
        while len(out) >= 3:
            a, b, c = out[-3], out[-2], out[-1]
            if abs(a[0] - c[0]) == 1 and abs(a[1] - c[1]) == 1 and (a[0] == b[0] or a[1] == b[1]) and (b[0] == c[0] or b[1] == c[1]):
                out.pop(-2)
            else: break
    return out

def spiral(cx, cy, th0, th1, r0, r1, n=None, power=1.0):
    """angles in degrees, screen coords (y down; +angle = clockwise on screen)"""
    L = abs(th1 - th0) * math.pi / 180 * max(r0, r1)
    n = n or max(8, int(L * 4))
    s = []
    for i in range(n + 1):
        t = i / n
        th = math.radians(th0 + (th1 - th0) * t)
        r = r0 + (r1 - r0) * (t ** power)
        s.append((cx + r * math.cos(th), cy + r * math.sin(th), t))
    return s

def line(x0, y0, x1, y1):
    n = max(2, int(math.hypot(x1 - x0, y1 - y0) * 3))
    return [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n, i / n) for i in range(n + 1)]

def seg_join(*parts):
    out = []
    for p in parts:
        out += p
    return out

def stroke(m, samples, widths=((0.0, 3),), flip=False):
    """widths: [(t_from, w)] piecewise; w in 1 (single), 2 (2x2), 3 (plus), 4 (plus-ish fat 3x3 square)"""
    pts = raster(samples)
    for x, y, t in pts:
        w = widths[0][1]
        for tf, ww in widths:
            if t >= tf: w = ww
        if w == 1: offs = [(0, 0)]
        elif w == 2: offs = [(0, 0), (1, 0), (0, 1), (1, 1)] if not flip else [(0, 0), (-1, 0), (0, 1), (-1, 1)]
        elif w == 3: offs = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]
        else: offs = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
        for dx, dy in offs: put(m, x + dx, y + dy)
    return pts

def mirror_x(m, axis2=None):
    """OR in the horizontal mirror about the canvas centre"""
    m |= m[:, ::-1]

# ---- shading ----
def _sh(m, dx, dy):
    """neighbour exists in m at (x+dx,y+dy)"""
    h, w = m.shape
    out = np.zeros_like(m)
    ys = slice(max(0, -dy), h - max(0, dy)); yd = slice(max(0, dy), h - max(0, -dy))
    xs = slice(max(0, -dx), w - max(0, dx)); xd = slice(max(0, dx), w - max(0, -dx))
    out[ys, xs] = m[yd, xd]
    return out

def shade(m, ramp, outline=None, outline_all=False):
    """convex bevel: ramp=(shadow, mid, light); returns (index image of fill, outline mask)"""
    up, lf, dn, rt = _sh(m, 0, -1), _sh(m, -1, 0), _sh(m, 0, 1), _sh(m, 1, 0)
    ul_empty = m & (~up | ~lf)
    dr_empty = m & (~dn | ~rt)
    img = np.zeros(m.shape, np.uint8)
    img[m] = ramp[1]
    img[ul_empty & ~dr_empty] = ramp[2]
    img[dr_empty & ~ul_empty] = ramp[0]
    # outline: pixel right of / below a pixel that has a same-direction neighbour (width>=2)
    ol = np.zeros(m.shape, bool)
    if outline is not None:
        thick_h = m & lf   # pixel has left neighbour -> outline to its right if empty
        thick_v = m & up
        ol |= _sh(thick_h, -1, 0) & ~m
        ol |= _sh(thick_v, 0, -1) & ~m
        if outline_all:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ol |= _sh(m, dx, dy) & ~m
    return img, ol

def render(M, extra_px=(), pad=6, wrap=None):
    """compose layers -> index image. Masks are edge-padded (or wrapped on `wrap`='x'/'y'/'xy') before
    shading so rails running off the canvas shade exactly like their continuation, then cropped."""
    w, h = M.w, M.h
    P = {}
    for k, m in M.L.items():
        px = py = pad
        mode = ["edge", "edge"]
        if wrap and "x" in wrap: mode[1] = "wrap"
        if wrap and "y" in wrap: mode[0] = "wrap"
        t = np.pad(m, ((pad, pad), (0, 0)), mode=mode[0])
        t = np.pad(t, ((0, 0), (pad, pad)), mode=mode[1])
        P[k] = t
    H, W = h + 2 * pad, w + 2 * pad
    out = np.zeros((H, W), np.uint8)
    gold = (P["gold"] | P["wire"]) & ~P["carve"]
    gi, _ = shade(gold, (10, 11, 12))
    _, gol = shade(P["gold"] & ~P["carve"], (10, 11, 12), outline=9)
    gol &= ~gold
    up, lf, dn, rt = _sh(gold, 0, -1), _sh(gold, -1, 0), _sh(gold, 0, 1), _sh(gold, 1, 0)
    gi[gold & ~up & ~lf & dn & rt] = 13
    out[gol] = 9
    out[gold] = gi[gold]
    out[P["dark"] & gold] = 9
    gem = P["gem"]
    ei, _ = shade(gem, (3, 4, 6))
    ring = np.zeros_like(gem)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ring |= _sh(gem, dx, dy) & ~gem
    out[ring] = 1
    out[gem] = ei[gem]
    out[P["gemdark"] & gem] = 2
    out = out[pad:pad + h, pad:pad + w]
    for (x, y), v in extra_px:
        if 0 <= x < w and 0 <= y < h: out[y, x] = v
    return out
