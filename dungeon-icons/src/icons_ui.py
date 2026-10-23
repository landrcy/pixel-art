"""16x16 UI icons. Shapes are painted as 'w' fill on a canvas, then auto-bevelled
(top-left edges W, bottom-right edges t) and outlined in m. Each icon has a normal and a
hover/active colour variant (bone -> torchlight)."""

class Cv:
    def __init__(s, n=16): s.n = n; s.g = [['.'] * n for _ in range(n)]
    def px(s, x, y, c='w'):
        if 0 <= x < s.n and 0 <= y < s.n: s.g[y][x] = c
    def rect(s, x, y, w, h, c='w'):
        for yy in range(y, y + h):
            for xx in range(x, x + w): s.px(xx, yy, c)
    def span(s, y, x0, x1, c='w'):
        for xx in range(x0, x1 + 1): s.px(xx, y, c)
    def line(s, x0, y0, x1, y1, c='w', sq=1):
        n = max(abs(x1 - x0), abs(y1 - y0)) or 1
        for i in range(n + 1):
            x = round(x0 + (x1 - x0) * i / n); y = round(y0 + (y1 - y0) * i / n)
            s.rect(x, y, sq, sq, c)
    def filled(s, y, x): return s.g[y][x] != '.' if 0 <= x < s.n and 0 <= y < s.n else False
    def bevel(s, hi='W', mid='w', lo='t'):
        o = [r[:] for r in s.g]
        for y in range(s.n):
            for x in range(s.n):
                if s.g[y][x] == 'w':
                    up = not s.filled(y-1, x); lf = not s.filled(y, x-1)
                    dn = not s.filled(y+1, x); rt = not s.filled(y, x+1)
                    o[y][x] = hi if (up or lf) else (lo if (dn or rt) else mid)
        s.g = o
    def outline(s, c='m'):
        o = [r[:] for r in s.g]
        for y in range(s.n):
            for x in range(s.n):
                if s.g[y][x] == '.' and any(s.filled(y+dy, x+dx) for dx, dy in ((1,0),(-1,0),(0,1),(0,-1))):
                    o[y][x] = c
        s.g = o
    def rows(s): return [''.join(r) for r in s.g]

def finish(cv): cv.bevel(); cv.outline(); return cv

# ---- home
def home():
    c = Cv()
    for i, y in enumerate(range(1, 8)): c.span(y, 7 - i, 8 + i)
    c.rect(11, 1, 2, 4)                      # chimney
    for y in range(8, 15): c.span(y, 3, 12)
    c.rect(6, 10, 4, 5, 'q')                 # door
    c.rect(4, 9, 0, 0)
    finish(c)
    c.rect(6, 10, 4, 5, 'q'); c.px(9, 12, 'Y')   # door + knob (after bevel so it stays dark)
    c.rect(6, 15, 4, 1, 'm')
    return c.rows()

# ---- item (gem)
def item():
    c = Cv()
    spans = {1:(4,11),2:(2,13),3:(1,14),4:(1,14),5:(2,13),6:(3,12),7:(4,11),8:(5,10),9:(6,9),10:(7,8)}
    for y, (a, b) in spans.items(): c.span(y, a, b)
    finish(c)
    for x in range(2, 14): c.px(x, 4 if False else 3, 't') if c.g[3][x] in 'wW' else None
    c.line(5, 1, 4, 3, 't'); c.line(10, 1, 11, 3, 't')
    c.line(3, 4, 7, 9, 't'); c.line(12, 4, 8, 9, 't')
    c.px(6, 4, 'W'); c.px(5, 5, 'W'); c.px(4, 6, 'W')
    c.px(3, 2, 'W'); c.px(2, 3, 'W')
    return c.rows()

# ---- character (head + shoulders)
def character():
    c = Cv()
    for y, (a, b) in {1:(5,10),2:(4,11),3:(4,11),4:(4,11),5:(4,11),6:(4,11),7:(5,10),8:(6,9)}.items(): c.span(y, a, b)
    c.span(9, 6, 9)
    for y, (a, b) in {10:(4,11),11:(3,12),12:(2,13),13:(2,13),14:(2,13)}.items(): c.span(y, a, b)
    finish(c)
    c.rect(5, 4, 2, 2, 'q'); c.rect(9, 4, 2, 2, 'q')    # eye hollows
    c.px(5, 4, 'm'); c.px(9, 4, 'm')
    c.rect(7, 7, 2, 1, 'm')                            # mouth tick
    return c.rows()

# ---- sound
def _speaker(c):
    c.rect(1, 5, 3, 6)
    for x in range(4, 8):
        c.span_v = None
        for y in range(5 - (x - 4), 11 + (x - 4) + 1): c.px(x, y)
    return c
def sound_on():
    c = _speaker(Cv()); finish(c)
    for (x, y) in [(10,5),(11,6),(11,7),(11,8),(11,9),(10,10)]: c.px(x, y, 'w')
    for (x, y) in [(12,3),(13,4),(13,5),(13,6),(13,7),(13,8),(13,9),(13,10),(13,11),(12,12)]: c.px(x, y, 'w')
    return c.rows()
def sound_off():
    c = _speaker(Cv()); finish(c)
    for i in range(6):
        c.px(9 + i, 5 + i, 'e'); c.px(10 + i, 5 + i, 'e'); c.px(14 - i, 5 + i, 'e'); c.px(13 - i, 5 + i, 'e')
    return c.rows()

# ---- how to play
def howto():
    c = Cv()
    spans = {1:[(5,10)],2:[(4,11)],3:[(4,6),(9,11)],4:[(9,11)],5:[(8,10)],6:[(7,9)],7:[(7,8)],8:[(7,8)],
             10:[(7,8)],11:[(7,8)],12:[(7,8)]}
    for y, ss in spans.items():
        for a, b in ss: c.span(y, a, b)
    finish(c)
    return c.rows()

# ---- back / share / correct / wrong / close
def back():
    c = Cv()
    for x in range(2, 8):
        h = x - 2
        for y in range(7 - h, 8 + h + 1): c.px(x, y)
    c.rect(7, 5, 7, 5)
    finish(c); return c.rows()
def share():
    c = Cv()
    c.line(4, 8, 11, 3, 'w', 2); c.line(4, 8, 11, 12, 'w', 2)
    c.rect(1, 6, 4, 4); c.rect(10, 1, 4, 4); c.rect(10, 11, 4, 4)
    finish(c); return c.rows()
def correct():
    c = Cv()
    c.line(2, 8, 5, 11, 'w', 2); c.line(5, 11, 12, 2, 'w', 2)
    c.bevel('L', 'l', 'G'); c.outline('g'); return c.rows()
def wrong():
    c = Cv()
    c.line(2, 2, 12, 12, 'w', 2); c.line(12, 2, 2, 12, 'w', 2)
    c.bevel('E', 'e', 'R'); c.outline('r'); return c.rows()
def close():
    c = Cv()
    c.line(3, 3, 12, 12, 'w', 1); c.line(12, 3, 3, 12, 'w', 1)
    finish(c); return c.rows()

HOVER_DEFAULT = {'W':'Z','w':'Y','t':'y','m':'R','q':'r','e':'E','R':'e','r':'R','l':'L','G':'l','L':'W','g':'G','E':'Z'}
UI = {
 'home': home(), 'item': item(), 'character': character(),
 'sound_on': sound_on(), 'sound_off': sound_off(), 'how_to_play': howto(),
 'back': back(), 'share': share(), 'correct': correct(), 'wrong': wrong(), 'close': close(),
}
HOVER_MAP = {k: dict(HOVER_DEFAULT) for k in UI}
HOVER_MAP['correct'] = {'L':'W','l':'L','G':'l','g':'G'}
HOVER_MAP['wrong']   = {'E':'Z','e':'E','R':'e','r':'R'}
def hover(name):
    mp = HOVER_MAP[name]
    return [''.join(mp.get(ch, ch) for ch in r) for r in UI[name]]
