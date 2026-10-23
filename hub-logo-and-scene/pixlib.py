"""Tiny pixel-art helper library used by generate.py / logo_v2.py.
Everything is drawn on a single pixel grid; supersampled vector shapes are
thresholded (no anti-aliasing survives) and shaded with a limited ramp."""
import math
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

def hexrgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

BAYER2 = (np.array([[0, 2], [3, 1]]) + .5) / 4
BAYER4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + .5) / 16
BAYER8 = None
def _b8():
    b = BAYER4 * 16 - .5
    top = np.hstack([4 * b, 4 * b + 2]); bot = np.hstack([4 * b + 3, 4 * b + 1])
    return (np.vstack([top, bot]) + .5) / 64
BAYER8 = _b8()

def catmull(pts, n=24, closed=False):
    """Catmull-Rom spline through pts -> dense polyline (list of (x,y))."""
    P = [np.array(p, float) for p in pts]
    if closed: P = [P[-1]] + P + [P[0], P[1]]
    else: P = [2 * P[0] - P[1]] + P + [2 * P[-1] - P[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(tuple(.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)))
    out.append(tuple(P[-2]))
    return out

def spiral(c, r0, r1, a0, a1, n=60):
    """points on a spiral: angle a0->a1 (degrees, y-down screen coords), radius r0->r1."""
    return [(c[0] + (r0 + (r1 - r0) * t) * math.cos(math.radians(a0 + (a1 - a0) * t)),
             c[1] + (r0 + (r1 - r0) * t) * math.sin(math.radians(a0 + (a1 - a0) * t))) for t in np.linspace(0, 1, n)]

def arc(c, rx, ry, a0, a1, n=80):
    return [(c[0] + rx * math.cos(math.radians(a)), c[1] + ry * math.sin(math.radians(a))) for a in np.linspace(a0, a1, n)]

class Mask:
    """supersampled binary-ish canvas; to_bool() thresholds coverage at 50%."""
    def __init__(self, W, H, ss=8):
        self.W, self.H, self.ss = W, H, ss
        self.im = Image.new('L', (W * ss, H * ss), 0); self.d = ImageDraw.Draw(self.im)
    def poly(self, pts, v=255):
        s = self.ss; self.d.polygon([(x * s, y * s) for x, y in pts], fill=v)
    def ellipse(self, c, rx, ry, v=255):
        s = self.ss; self.d.ellipse([(c[0] - rx) * s, (c[1] - ry) * s, (c[0] + rx) * s, (c[1] + ry) * s], fill=v)
    def stroke(self, pts, widths, v=255):
        """variable width stroke; widths = list (same length as pts) or (w0,w1) or a callable(t)."""
        pts = np.array(pts, float)
        seg = np.hypot(*np.diff(pts, axis=0).T); L = np.concatenate([[0], np.cumsum(seg)])
        T = L / L[-1]
        if callable(widths): wf = widths
        elif len(widths) == 2: wf = lambda t: widths[0] + (widths[1] - widths[0]) * t
        else: wf = lambda t: np.interp(t, np.linspace(0, 1, len(widths)), widths)
        # resample finely
        m = max(int(L[-1] * 6), 2); ts = np.linspace(0, 1, m)
        xs = np.interp(ts, T, pts[:, 0]); ys = np.interp(ts, T, pts[:, 1])
        for t, x, y in zip(ts, xs, ys):
            r = wf(t) / 2; self.ellipse((x, y), r, r, v)
    def to_bool(self, thr=.5):
        a = np.asarray(self.im.resize((self.W, self.H), Image.BOX), float) / 255
        return a >= thr

def clean_mask(m, min_size=3):
    """remove orphan pixels / tiny specks, fill 1px pinholes (4-connected components)."""
    m = m.copy()
    lab, n = ndi.label(m)
    if n:
        sizes = ndi.sum(m, lab, range(1, n + 1))
        for i, s in enumerate(sizes, 1):
            if s < min_size: m[lab == i] = False
    holes = ~m
    lab, n = ndi.label(holes)
    for i in range(1, n + 1):
        if (lab == i).sum() <= 1: m[lab == i] = True
    return m

def edt_in(m):
    p = np.pad(m, 1, constant_values=False)
    return ndi.distance_transform_edt(p)[1:-1, 1:-1]

LIGHT = np.array([-.55, -.62, .56]); LIGHT /= np.linalg.norm(LIGHT)

def shade_field(m, R, base, gain, diag=0.0, sigma=.7, bump=None):
    """continuous 'ramp index' field for mask m: rounded-bevel normal lit from top-left."""
    d = np.maximum(edt_in(m) - .5, 0)
    t = np.minimum(d, R) / R
    h = R * np.sqrt(np.clip(1 - (1 - t) ** 2, 0, 1))
    if bump is not None: h = h + bump
    mf = m.astype(float)
    hs = ndi.gaussian_filter(h * mf, sigma) / np.maximum(ndi.gaussian_filter(mf, sigma), 1e-3)
    gy, gx = np.gradient(hs)
    n = np.stack([-gx, -gy, np.ones_like(gx)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    lit = n @ LIGHT
    v = base + gain * (lit - LIGHT[2])
    if diag:
        ys, xs = np.nonzero(m); x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        X, Y = np.meshgrid(np.arange(m.shape[1]), np.arange(m.shape[0]))
        g = ((X - x0) / max(x1 - x0, 1) + (Y - y0) / max(y1 - y0, 1)) / 2
        v = v + diag * (.5 - g)
    return v, lit, d

def quantize(v, bayer=BAYER4, K=2.4, lo=0, hi=6):
    H, W = v.shape
    th = np.tile(bayer, (H // bayer.shape[0] + 1, W // bayer.shape[1] + 1))[:H, :W]
    fl = np.floor(v); f = v - fl
    f2 = np.clip((f - .5) * K + .5, 0, 1)
    return np.clip(fl + (f2 > th), lo, hi).astype(int)

def save_rgba(idx, pal, path, spec=None):
    """idx: int array, -1 = transparent. pal: list of hex. spec: optional extra colours index >= len(pal)"""
    H, W = idx.shape; a = np.zeros((H, W, 4), np.uint8)
    for i, h in enumerate(pal):
        a[idx == i] = (*hexrgb(h), 255)
    Image.fromarray(a, 'RGBA').save(path)

def up(im, k, bg=None):
    if bg is not None:
        b = Image.new('RGBA', im.size, bg); b.alpha_composite(im); im = b
    return im.resize((im.width * k, im.height * k), Image.NEAREST)

def audit(path):
    im = Image.open(path).convert('RGBA'); a = np.asarray(im)
    alphas = set(np.unique(a[..., 3]).tolist())
    cols = {tuple(p[:3]) for p in a.reshape(-1, 4) if p[3] > 0}
    return im.size, alphas, len(cols)


def pp_stroke(pts, widths, W, H, step=.08):
    """'Hand-drawn' variable-width stroke on the pixel grid.  One run of pixels per row (steep parts) or per
    column (flat parts) with an integer width, so curves get clean, evenly-stepped staircases."""
    p = np.array(pts, float)
    seg = np.hypot(*np.diff(p, axis=0).T); L = np.concatenate([[0], np.cumsum(seg)])
    n = max(int(L[-1] / step), 4); s = np.linspace(0, L[-1], n)
    x = np.interp(s, L, p[:, 0]); y = np.interp(s, L, p[:, 1])
    t = s / L[-1]
    if callable(widths): w = np.array([widths(v) for v in t])
    else: w = np.interp(t, np.linspace(0, 1, len(widths)), widths)
    k = 12
    tx = ndi.uniform_filter1d(np.gradient(x), k); ty = ndi.uniform_filter1d(np.gradient(y), k)
    nn = np.hypot(tx, ty) + 1e-9; tx /= nn; ty /= nn
    out = np.zeros((H, W), bool)
    steep = np.abs(ty) >= np.abs(tx)
    # split into runs of constant orientation, then group by row/column inside each run
    cuts = np.nonzero(np.diff(steep.astype(int)))[0] + 1
    for r0, r1 in zip(np.r_[0, cuts], np.r_[cuts, len(x)]):
        st = steep[r0]
        xs_, ys_, ws_ = x[r0:r1], y[r0:r1], w[r0:r1]
        txs, tys = tx[r0:r1], ty[r0:r1]
        key = np.round(ys_ if st else xs_).astype(int)
        cen = xs_ if st else ys_
        ww = ws_ / np.maximum(np.abs(tys if st else txs), .55)
        for kv in np.unique(key):
            m = key == kv
            c = cen[m].mean(); wp = max(1, int(round(ww[m].mean())))
            lo = int(math.floor(c - wp / 2 + .5))
            for q in range(lo, lo + wp):
                yy, xx = (kv, q) if st else (q, kv)
                if 0 <= yy < H and 0 <= xx < W: out[yy, xx] = True
    return out


def despeckle(idx, passes=2):
    """replace pixels that share colour with none of their 8 neighbours by the most common neighbour colour."""
    H, W = idx.shape
    for _ in range(passes):
        out = idx.copy()
        for y in range(H):
            for x in range(W):
                c = idx[y, x]
                if c < 0: continue
                nb = [idx[yy, xx] for yy in range(max(y - 1, 0), min(y + 2, H)) for xx in range(max(x - 1, 0), min(x + 2, W)) if (yy, xx) != (y, x)]
                if c in nb: continue
                opaque = [v for v in nb if v >= 0]
                if len(opaque) < 3: out[y, x] = -1 if len(opaque) <= 1 else c; continue
                vals, cnt = np.unique(opaque, return_counts=True)
                out[y, x] = vals[cnt.argmax()]
        idx = out
    return idx
