"""Revision pass: overrides / additions to icons_src.ICONS (hand-authored)."""
from icons_src import *

def ol(grid, ch, bands=()):
    """Recolour 'k' pixels touching transparency / border (outer outline) with a dark tone of the
    fill ('selective outlining'); interior k (pupils, holes, pips) stays near-black."""
    H, W = len(grid), len(grid[0]); out = []
    for y in range(H):
        row = ''
        for x in range(W):
            c = grid[y][x]
            if c == 'k':
                edge = any(not (0 <= y+dy < H and 0 <= x+dx < W) or grid[y+dy][x+dx] == '.'
                           for dy in (-1,0,1) for dx in (-1,0,1))
                if edge:
                    c = ch
                    for (r0, r1, bc) in bands:
                        if r0 <= y <= r1: c = bc
            row += c
        out.append(row)
    return out

def rep(cat, name, grid): ICONS[(cat, name)] = grid
def OL(cat, name, ch, bands=()): ICONS[(cat, name)] = ol(ICONS[(cat, name)], ch, bands)

# ---------------------------------------------------------------- passive
rep('passive','heart_jar',[
"................",
".....qqqqqq.....",
".....qWwttq.....",
".....qwttmq.....",
"....bcbbbbbb....",
"..bcccpppppppb..",
"..bcpppppppppb..",
"..bcprrpprrppb..",
"..bcrEErreerpb..",
"..bprEeereRrpb..",
"..bpprEreRrppb..",
"..bpppreRrpppb..",
"..bbppprrpppBb..",
"..bbppppppppBb..",
"...bbbbbbbbbb...",
"................"])

rep('passive','tooth_charm', S16([
"........",
"......mm",
".....mt.",
".....mt.",
"......mt",
"..qqqqq.",
".qWWwwwq",
".qWwwwww",
".qwwwwww",
"..qwwwww",
"..qwwwww",
"...qwwq.",
"...qwwq.",
"....qq..",
"........",
"........"], {'W':'t','t':'m'}))

rep('passive','thorn_rose', [
"................",
".....rrrrr......",
"...rreEEeerr....",
"..reEEeeeeeer...",
"..rEeeRRReeRr...",
"..reeReeeReer...",
"..reeReRReeer...",
"..rReeeeeeeRr...",
"...rRReeeeRr....",
"....rrRRRrr.....",
".....rGgrr......",
"....gGgGg.......",
"..ggGGGgg.......",
"..gGggG.g.g.....",
"...gg..gGg......",
"......gGg......."])

def _amulet():
    g = S16([
"...t....",
"....t...",
".....t..",
".......m",
".....RRR",
"....RZYY",
"...RZYYY",
"..RZYYRR",
"..RZYR..",
"..RYYR..",
"..RYyR..",
"..RyyR..",
"..RyyyRR",
"...Ryyyy",
"....Ryyy",
".....RRR"], {'Z':'y','t':'m'})
    g = [list(r) for r in g]
    eye = {8:"pwwwwp", 9:"wLkkLw", 10:"wLkkLw", 11:"pwwwwp"}
    for y, s in eye.items():
        for i, ch in enumerate(s): g[y][5+i] = ch
    # tidy: iris right side is the darker green
    g[9][10] = 'G'; g[10][10] = 'G'
    return [''.join(r) for r in g]
rep('passive','eye_amulet', _amulet())

rep('passive','sick_mushroom', S16([
"........",
"....gggg",
"..ggLLll",
".gLLlwwl",
".gLllwwl",
".gllllll",
".gGGllll",
"..ggGGGG",
".....qWw",
".....qWw",
".....qWw",
"....qWww",
"...qWwww",
"...qqqqq",
"........",
"........"], {'L':'l','W':'t'}))

OL('passive','blood_chalice','p')
OL('passive','raven_feather','b')

del ICONS[('passive','bat_wing')]

# ---------------------------------------------------------------- active
rep('active','candle',[
".......y........",
"......yYy.......",
"......YZY.......",
"......YZY.......",
".......Yy.......",
".......m........",
".....qqqqqq.....",
".....qWWwwq.....",
".....qWwwtq.....",
".....qWwwtq.....",
".....qWwtwtq....",
".....qwwttq.....",
".....qwwttq.....",
"...RZYYYYYyyR...",
"....RRRRRRRR....",
"................"])

rep('active','potion_flask', shade(S16([
"........",
"......qq",
"......qW",
"......qt",
"......cp",
"......cp",
".....cpp",
"....cppp",
"...cLLll",
"..cLllll",
"..cLllll",
"..cLllll",
"...cLlll",
"....cGGG",
".....bbb",
"........"], {'W':'t','c':'B','L':'l'}), 22, DK))

OL('active','hourglass','q')
OL('active','lantern','p')
OL('active','ritual_dagger','b', [(9,11,'R'),(12,15,'r')])
OL('active','toll_bell','R')
OL('active','spellbook','p')
OL('active','scrying_orb','b', [(11,14,'q')])

# ---------------------------------------------------------------- trinkets
rep('trinket','rusty_coin', shade(S16([
"........",
"........",
"....RRRR",
"...RZYYY",
"..RZYYYY",
"..RZYYYR",
"..RYYYYR",
"..RYRRRR",
"..RYRRRR",
"..RYYYYR",
"..RYYYYR",
"..RYYYYY",
"...RYYYY",
"....RRRR",
"........",
"........"], {'Z':'Y'}), 19, DK))

OL('trinket','bone_key','q')

rep('trinket','gem_ring', S16([
"........",
"......gg",
".....gLl",
".....gLl",
"......gg",
"....RZYY",
"...RZYYY",
"..RZYYRR",
"..RZYR..",
"..RYYR..",
"..RYyR..",
"..RyyR..",
"..RyyyRR",
"...Ryyyy",
"....Ryyy",
".....RRR"], {'Z':'y','Y':'y','L':'G'}))

OL('trinket','iron_padlock','b')

rep('trinket','rusty_nail',[
"................",
"................",
"...RRRRRRRRRR...",
"..RZYYYYYYyyyR..",
"..RYYYYYYyyyyR..",
"...RRRRYyRRRR...",
"......RYyR......",
"......RYyR......",
"......RyyR......",
"......RYRR......",
"......RYyR......",
"......RyyR......",
"......RYyR......",
".......RR.......",
"................",
"................"])

OL('trinket','bone_button','q')
OL('trinket','knuckle_die','q')
OL('trinket','dead_clover','g')

# ---------------------------------------------------------------- familiars
OL('familiar','tiny_skull','q')
OL('familiar','wandering_eye','q', [(12,14,'r')])

rep('familiar','bile_slime', S16([
"........",
"........",
"........",
".....ggg",
"...ggLll",
"..gLllll",
".gLlWlll",
".gllllll",
".gllwkll",
".gllwkll",
".gGlllll",
".ggGGGGG",
"..gggggg",
"........",
"........",
"........"], {'L':'l','W':'l'}))

rep('familiar','cave_bat', S16([
"........",
"........",
".....p..",
".p...pp.",
".pup.pup",
".puupuuP",
".puuuEuP",
".pupuuuP",
".ppppuPp",
"..p.ppPp",
"........",
"........",
"........",
"........",
"........",
"........"], {'u':'P','E':'E'}))

rep('familiar','sheet_ghost', S16([
"........",
"....qqqq",
"..qqWWww",
".qWWwwww",
".qWwwwww",
".qwwkkww",
".qwwkkww",
".qwwwwww",
".qwwwwwk",
".qwwwwwk",
".qwwwwww",
".qwwwwww",
".qwk.kwk",
"..q...q.",
"........",
"........"], {'W':'c','w':'w'}))

rep('familiar','crypt_spider', S16([
"........",
"........",
"..uu..pp",
"...u.pEP",
"...uupPP",
"uuuppPPu",
"...pPPuP",
"..upPPPP",
".uuppPPP",
"u..uppPP",
"....uppp",
"........",
"........",
"........",
"........",
"........"], {'u':'P','E':'E'}))

rep('familiar','grave_fly', S16([
"........",
"........",
".bbb....",
"bcWcb...",
"bcWBBb..",
".bBBb.gg",
"...bbgGG",
"..gggEEE",
"..gGgEEE",
"...gGGEe",
"....gGGG",
".....ggg",
"........",
"........",
"........",
"........"], {'c':'B','W':'B','E':'e','G':'G'}))

rep('familiar','horned_imp', S16([
"........",
"..tt....",
"..twq...",
"..qwqrrr",
"...qrEEE",
"..qrEEee",
"..qrYYee",
"..qrYkee",
"..qreeee",
"..qrekkk",
"..qRrwkw",
"...qqrRR",
".....rrr",
"........",
"........",
"........"], {'t':'m','E':'e','Y':'Y','e':'R','w':'w'}))

# ---------------------------------------------------------------- pass 2 fixes
def sub(cat, name, mapping, rows=None):
    g = ICONS[(cat, name)]
    ICONS[(cat, name)] = [''.join(mapping.get(c, c) if (rows is None or rows[0] <= y <= rows[1]) else c
                                  for c in r) for y, r in enumerate(g)]

sub('active','lantern', {'k':'p'})
sub('active','ritual_dagger', {'k':'R'}, (9, 11))
sub('active','ritual_dagger', {'k':'r'}, (12, 15))
sub('active','toll_bell', {'k':'R'})

rep('trinket','gem_ring', S16([
"........",
"......rr",
".....rEe",
".....rEe",
"......rr",
"....kcBB",
"...kcBBB",
"..kcBBkk",
"..kcBk..",
"..kBBk..",
"..kBbk..",
"..kbbk..",
"..kbbbkk",
"...kbbbb",
"....kbbb",
".....kkk"], {'c':'B','B':'B','E':'e'}))

rep('familiar','sheet_ghost', shade(S16([
"........",
"....bbbb",
"..bbWWww",
".bWWwwww",
".bWwwwww",
".bwwkkww",
".bwwkkww",
".bwwwwww",
".bwwwwkk",
".bwwwwwk",
".bwwwwww",
".bwwwwww",
".bwk.kwk",
"..b...b.",
"........",
"........"], {'W':'w','w':'w'}), 21, {'W':'w','w':'c','c':'B'}))

rep('familiar','grave_fly', S16([
"........",
"....gggg",
"....gEEg",
"....gEeG",
".bbb.gGG",
"bcWcbgGG",
"bcWBBbGG",
".bBBb.gG",
"..bb.gGG",
".....gGG",
".....gGg",
"......gg",
"........",
"........",
"........",
"........"], {'c':'B','W':'B','E':'e','e':'R','G':'G','B':'b'}))
