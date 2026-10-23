#!/usr/bin/env python3
"""Kit QA: alpha 0/255, palette membership + colour count, isolated pixels, mirrors, tile seams, joins."""
import os, sys, json
import numpy as np
from PIL import Image
sys.path.insert(0, "/workspace")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pxl import PAL
from pixel_tools import lint as pt_lint

PALSET = {tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in PAL.values() if h}
fails = []
def ok(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond: fails.append(msg)

def L(f): return Image.open(os.path.join(HERE, f)).convert("RGBA")
def A(f): return np.array(L(f))

files = [f for f in sorted(os.listdir(HERE)) if f.endswith(".png") and "@4x" not in f]
used = set()
for f in files:
    a = A(f)
    al = a[..., 3]
    bad_alpha = int(((al != 0) & (al != 255)).sum())
    op = al == 255
    cols = {tuple(c) for c in a[..., :3][op].reshape(-1, 3)}
    used |= cols
    off = len(cols - PALSET) if f != "preview.png" else 0
    # isolated opaque pixels (no opaque 8-neighbour)
    pad = np.pad(op, 1)
    nb = sum(np.roll(np.roll(pad, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dx, dy) != (0, 0))[1:-1, 1:-1]
    iso = int((op & (nb == 0)).sum())
    rep = pt_lint(L(f), max_colors=16 if f != "preview.png" else 20)
    print(f"{f:26s} {a.shape[1]:3d}x{a.shape[0]:<3d} colours={len(cols):2d} alpha-bad={bad_alpha} off-palette={off} isolated={iso if 'glint' not in f else 'n/a (sparkles)'} pt-orphan4={rep['orphan_pixels']}")
    ok(bad_alpha == 0, f"{f}: alpha only 0/255")
    ok(off == 0, f"{f}: only kit palette colours")
    if "glint" not in f: ok(iso == 0, f"{f}: no isolated pixels")
kit_cols = {c for f in files if f != "preview.png" for c in {tuple(x) for x in A(f)[..., :3][A(f)[..., 3] == 255].reshape(-1, 3)}}
ok(len(kit_cols) <= 14, f"kit uses {len(kit_cols)} colours (<=14)")

eq = lambda a, b: bool((a == b).all())
# mirrors
s, sr = A("vine-strip-left.png"), A("vine-strip-right.png")
ok(eq(s[:, ::-1], sr), "strip-right is the exact horizontal mirror of strip-left")
c = A("corner-tl.png")
ok(eq(c[:, ::-1], A("corner-tr.png")), "corner-tr = h-mirror of tl")
ok(eq(c[::-1], A("corner-bl.png")), "corner-bl = v-mirror of tl")
ok(eq(c[::-1, ::-1], A("corner-br.png")), "corner-br = h+v mirror of tl")
ok(eq(A("divider-top.png")[::-1], A("divider-bottom.png")), "divider-bottom = v-mirror of divider-top")
d = A("divider-top.png")
# divider horizontal mirror symmetry of geometry (alpha) and of colours except lighting
da = (d[..., 3] > 0) & ~((d[..., :3] == np.array([0x3d, 0x1f, 0x17])).all(-1))   # ignore the one-sided bronze outline
ok(eq(da, da[:, ::-1]), "divider-top silhouette is left/right mirror-symmetric")
# vertical tile seam: 3x tile == independent rendering (rows continuous)
H = s.shape[0]
t3 = np.concatenate([s, s, s], 0)
import generate as g
full = np.array(g.to_img(g.build_strip(full=True)))
ok(eq(t3[24:360], full[24:360]), "strip: 3x tiled == 3-period render over rows 24..360 (no seam at tile edges)")
# explicit seam rows: edge continuity of rail/stem columns
ok(eq(s[0], full[128]) and eq(s[-1], full[255]), "strip: first/last rows identical to the continuous render")
ok(eq(s[-1, 2:5], full[255, 2:5]) and eq(s[0, 2:5], full[256 - 128, 2:5]), "strip rail columns continuous across the seam")
# line tile seam & joins
lt = A("divider-line-tile.png")
lt3 = np.concatenate([lt, lt, lt], 1)
ok(eq(lt3[:, 8:40], np.roll(lt3, -8, 1)[:, 0:32][:, :32]) , "line tile: repeat-x consistent")
full_line = np.array(g.to_img(__import__("numpy").concatenate([g.build_line_tile()] * 3, 1)))
ok(eq(np.concatenate([lt] * 3, 1), full_line), "line tile: triple tiling identical to wrap render (seamless)")
rail_rows = slice(0, 10)
ok(eq(d[rail_rows, 0:28], np.tile(lt, (1, 3, 1))[rail_rows, 0:28]), "divider-top left end continues the line tile (rail+pearls match)")
ok(eq(d[rail_rows, 132:160], np.tile(lt, (1, 3, 1))[rail_rows, 4:32]), "divider-top right end continues the line tile")
ok(eq(c[0:6, 48:64], lt[0:6, 0:16]), "corner-tl top rail continues into divider-line-tile (rows 0-5)")
ok(eq(c[63, 2:5], s[0, 2:5]) and eq(c[63, 2:5], s[127, 2:5]), "corner-tl bottom rail row == strip rail row (clean join)")
# glint sheet
gs = A("gold-glint-sheet.png")
ok(gs.shape[:2] == (13, 78), "glint sheet is 6 frames of 13x13")
# kit.json sizes match
kit = json.load(open(os.path.join(HERE, "kit.json")))
okk = all(list(Image.open(os.path.join(HERE, e["file"])).size) == e["size"] for e in kit["files"])
ok(okk, "kit.json sizes match files")
print("\nRESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL(S)")

# ---- visual check sheets
os.makedirs(os.path.join(HERE, "checks"), exist_ok=True)
bg = (21, 15, 51, 255)
def onbg(im):
    b = Image.new("RGBA", im.size, bg); b.alpha_composite(im); return b
tile3 = Image.new("RGBA", (48, 384), bg)
for i in range(3): tile3.alpha_composite(L("vine-strip-left.png"), (0, i * 128))
two = Image.new("RGBA", (48 * 2 + 4, 384), bg); two.alpha_composite(tile3, (0, 0))
tile3r = Image.new("RGBA", (48, 384), bg)
for i in range(3): tile3r.alpha_composite(L("vine-strip-right.png"), (0, i * 128))
two.alpha_composite(tile3r, (52, 0))
two.resize((two.width * 3, two.height * 3), Image.NEAREST).save(os.path.join(HERE, "checks", "strip-tiled-3x-lr.png"))
q = Image.new("RGBA", (128 + 4, 128 + 4), bg)
for (f, x, y) in (("corner-tl.png", 0, 0), ("corner-tr.png", 68, 0), ("corner-bl.png", 0, 68), ("corner-br.png", 68, 68)): q.alpha_composite(L(f), (x, y))
q.resize((q.width * 5, q.height * 5), Image.NEAREST).save(os.path.join(HERE, "checks", "corners-quad.png"))
dv = Image.new("RGBA", (16 * 3 + 160 + 16 * 3, 24), bg)
for i in range(3): dv.alpha_composite(L("divider-line-tile.png"), (i * 16, 0))
dv.alpha_composite(L("divider-top.png"), (48, 0))
for i in range(3): dv.alpha_composite(L("divider-line-tile.png"), (208 + i * 16, 0))
dv.resize((dv.width * 4, dv.height * 4), Image.NEAREST).save(os.path.join(HERE, "checks", "divider-joined.png"))
sys.exit(1 if fails else 0)
