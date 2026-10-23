"""Hand-authored pixel grids (original designs). Palette keys: see palette_def.py.
'.' = transparent.  Symmetric designs are authored as LEFT HALVES (S16/S24 mirror them,
swapping highlight->base on the right so light always comes from the top-left)."""

HL = {'W':'w','Z':'Y','c':'B','L':'l','E':'e','u':'P'}                # highlight -> base on mirrored side
DK = {'W':'w','w':'t','t':'m','Z':'Y','Y':'y','y':'R','c':'B','B':'b','u':'P','P':'p',
      'L':'l','l':'G','G':'g','E':'e','e':'R','R':'r','m':'q'}      # one step darker (characters)

def mirror(rows, swap):
    out = []
    for r in rows:
        right = ''.join(swap.get(ch, ch) for ch in reversed(r))
        out.append(r + right)
    return out

def S16(rows, swap=HL): return mirror(rows, swap)
def S24(rows, swap=DK): return mirror(rows, swap)

def edit(grid, ch_at):
    g = [list(r) for r in grid]
    for (x, y), ch in ch_at.items():
        g[y][x] = ch
    return [''.join(r) for r in g]

def shade(grid, T, swap=DK):
    """darken (one step) pixels with x+y >= T : clean diagonal lower-right shadow."""
    out = []
    for y, r in enumerate(grid):
        out.append(''.join(swap.get(c, c) if (x + y >= T and c not in 'kn') else c for x, c in enumerate(r)))
    return out

ICONS = {}   # name -> dict(cat, size, grid)

def add(cat, name, grid, **kw):
    ICONS[(cat, name)] = grid

# ------------------------------------------------------------------ PASSIVE ITEMS
add('passive','heart_jar',[
"................",
".....kkkkkk.....",
".....kwttmk.....",
".....kttmmk.....",
"....bbbbbbbb....",
"...bbcpppppbb...",
"..bcpppppppppb..",
"..bcprrpprrppb..",
"..bcrEErreerpb..",
"..bprEeereRrpb..",
"..bpprEreRrppb..",
"..bpppreRrpppb..",
"..bbppprrpppBb..",
"...bbppppppBb...",
"....bbbbbbbb....",
"................"])

add('passive','tooth_charm',[
"................",
"......qqqq......",
".....qmttmq.....",
".....qt..mq.....",
".....qmttmq.....",
"...qqqqmmqqqq...",
"..qWWwwwwwwtq...",
"..qWwwwwwwttq...",
"..qwwwwwwwttq...",
"...qwwwwwttq....",
"...qwwwq.qttq...",
"...qwwwq.qttq...",
"....qwq...qtq...",
".....q.....q....",
"................",
"................"])

add('passive','gilded_crown', S16([
"........",
"........",
"...k...k",
"..kZk.kZ",
"..kZYkkZ",
"..kZYYYY",
"..kZYYeY",
"..kYYYYY",
"..kyyyyy",
"...kkkkk",
"........",
"........",
"........",
"........",
"........",
"........"], {'Z':'y','Y':'Y','e':'e'}))

add('passive','bat_wing',[
"................",
"..........kk....",
".........kuPk...",
"....kk..kuPPk...",
"...kuPk.kuPPk...",
"...kuPPkkuPPpk..",
"..kuPPPPuPPPpk..",
"..kuPPPPPPPppk..",
".kuPPPPPPPpppk..",
".kPPPpkPPPppkk..",
".kPPpk.kPPpk....",
"..kPk...kPk.....",
"...k.....k......",
"................",
"................",
"................"])

add('passive','eye_amulet',[
".....t....t.....",
"......t..t......",
".......tt.......",
".....kkkkkk.....",
"...kkZYYYYYkk...",
"..kZYYYYYYYYyk..",
"..kYppppppppyk..",
"..kYpwwwwwwpyk..",
"..kYwwlkklwwyk..",
"..kYpwwwwwwpyk..",
"..kyppppppppyk..",
"...kyyyyyyyyk...",
"....kkkkkkkk....",
"................",
"................",
"................"])

add('passive','sick_mushroom',[
"................",
"....kkkkkkkk....",
"..kkLLllllllkk..",
".kLLlwwllllllGk.",
".kLllwwllllwwGk.",
".kllllllllllGGk.",
".kGGllllllwwGGk.",
"..kkGGGGGGGGkk..",
".....kWwwtk.....",
".....kWwwtk.....",
".....kwwttk.....",
"....kwwwttmk....",
"...kwwwwttmmk...",
"...kkkkkkkkkk...",
"................",
"................"])

add('passive','blood_chalice', S16([
"........",
"..kkkkkk",
"..kuEeee",
"..kcuPPP",
"..kuPPPP",
"...kuPPP",
"....kuPP",
".....kkP",
"......kP",
"......kP",
".....kuP",
"....kuPP",
"...kuPPP",
"...kkkkk",
"........",
"........"], {'u':'p','c':'b','E':'R'}))

add('passive','raven_feather',[
"................",
"..........kkk...",
"........kkBBBk..",
"......kkBBBBBBk.",
".....kBBBcBBbbk.",
"....kBBBcBBbbk..",
"...kBBBcBBbbbk..",
"..kBBBcBBbbbk...",
"..kBBcBBbbbbk...",
".kBBcBBbbbbk....",
".kBcBBbbbbk.....",
".kcBbbbbk.......",
"kwcbbbk.........",
"kwwk............",
".kk.............",
"................"])

# ------------------------------------------------------------------ ACTIVE ITEMS
add('active','candle',[
".......y........",
"......yYy.......",
"......YZY.......",
"......YZY.......",
".......Yy.......",
".......k........",
".....kkkkkk.....",
".....kWWwwk.....",
".....kWwwtk.....",
".....kWwwtk.....",
".....kWwtwtk....",
".....kwwttk.....",
".....kwwttk.....",
"...kkkkkkkkkk...",
"...kyYYYYYyyk...",
"....kkkkkkkk...."])

add('active','potion_flask', S16([
"........",
"......kk",
"......kW",
"......kt",
".....kkk",
"......kc",
"......kc",
".....kcp",
"....kcpp",
"...kcLll",
"..kLllll",
"..kLllll",
"...kLlll",
"....kGGG",
".....kkk",
"........"], {'W':'t','c':'b','L':'G'}))

add('active','hourglass', S16([
"..kkkkkk",
"..kWwwww",
"..kkkkkk",
"....kcpp",
"....kcpY",
".....kpY",
"......kY",
"......kZ",
"......kp",
".....kpZ",
"....kcYY",
"....kYYY",
"....kYYY",
"..kkkkkk",
"..kWwwww",
"..kkkkkk"], {'W':'t','c':'b','Y':'y'}))

add('active','lantern', S16([
".....kkk",
"....kt..",
"...kkkkk",
"...kuPPP",
"...kkkkk",
"...kuyyy",
"...kuyyY",
"...kuyYZ",
"...kuyYZ",
"...kuyyY",
"...kuyyy",
"...kkkkk",
"...kuPPP",
"....kkkk",
"........",
"........"], {'u':'p','t':'m'}))

add('active','ritual_dagger',[
".......kk.......",
"......kWBk......",
".....kWccBk.....",
".....kWccBk.....",
".....kWccBk.....",
".....kWccBk.....",
".....kWccBk.....",
".....kWccBk.....",
".....kWccBk.....",
"...kkkkkkkkkk...",
"...kZYYYYYYyk...",
"...kkkkkkkkkk...",
".....kReRrk.....",
".....kRrRrk.....",
".....kkYYkk.....",
"......kkkk......"])

add('active','toll_bell', S16([
"........",
"......kk",
"......kY",
".....kkk",
"....kZYY",
"...kZYYY",
"...kZYYY",
"..kZYYYY",
"..kZYYYY",
".kZYYYYY",
".kkkkkkk",
".......k",
"......kR",
"......kR",
".......k",
"........"], {'Z':'y','R':'r'}))

add('active','spellbook', [
"................",
"..kkkkkkkkkkkk..",
"..kuuPPPPPPPwk..",
"..kuPPPPPPPPwk..",
"..kPPPPYYPPPwk..",
"..kPPPYZZYPPtk..",
"..kPPPYZkYPPtk..",
"..kPPPYZZYPPtk..",
"..kPPPPYYPPPwk..",
"..kPPPPPPPPPtk..",
"..kPPPPPPPpptk..",
"..kppppppppptk..",
"..kkkkkkkkkkkk..",
"................",
"................",
"................"])

add('active','scrying_orb', S16([
"........",
"....kkkk",
"...kcWBB",
"..kcWBBB",
"..kWBBBP",
"..kBBBPu",
"..kBBPPP",
"..kBBBPP",
"..kbBBBB",
"...kbbBB",
"....kkbb",
"....kkmt",
"...kmttt",
"..kmttww",
"..kkkkkk",
"........"], {'c':'B','W':'B','u':'P','m':'m'}))

# ------------------------------------------------------------------ TRINKETS
add('trinket','rusty_coin', S16([
"........",
"....kkkk",
"...kYZYY",
"..kYZYYY",
"..kZYYyy",
"..kYYyyR",
"..kYYyRl",
"..kYyyRl",
"..kyyyyR",
"..kyyYyy",
"..kyyyyy",
"...kRyyy",
"....kkRR",
"........",
"........",
"........"], {'Z':'y','Y':'y','l':'l'}))

add('trinket','bone_key',[
".....kkkkkk.....",
"....kWwwwwtk....",
"....kwkkkkmk....",
"....kwkkkkmk....",
"....kwtttmmk....",
".....kkmmkk.....",
"......kwtk......",
"......kwtk......",
"......kwtkk.....",
"......kwttmk....",
"......kwtkk.....",
"......kwttkk....",
"......kwttmk....",
"......kkkkk.....",
"................",
"................"])

add('trinket','gem_ring',[
"................",
"................",
"................",
"......kkkk......",
".....kLlllk.....",
".....kLlGgk.....",
"......kkkk......",
"....kkZYYYkk....",
"...kZYYYYYYyk...",
"...kZYkkkkyyk...",
"...kYk....kyk...",
"...kYk....kyk...",
"...kYykkkkyyk...",
"....kyyyyyyk....",
".....kkkkkk.....",
"................"])

add('trinket','iron_padlock', S16([
"........",
".....kkk",
"....kWcc",
"....kWc.",
"....kWc.",
"....kWc.",
"..kkkkkk",
"..kWcccc",
"..kcBBBB",
"..kcBBBk",
"..kBBBkk",
"..kBBBBk",
"..kBBBBk",
"..kbbbbb",
"..kkkkkk",
"........"], {'W':'b','c':'B'}))

add('trinket','rusty_nail',[
"................",
"...kkkkkkkkkk...",
"...kZYYYYyyyk...",
"....kkYyRkk.....",
"......kYyk......",
"......kYRk......",
"......kyRk......",
"......kYyk......",
"......kyRk......",
"......kYyk......",
"......kyRk......",
"......kyRk......",
".......kRk......",
"........k.......",
"................",
"................"])

add('trinket','bone_button', [
"................",
"................",
"....kkkkkkkk....",
"...kWwwwwwwtk...",
"..kWwwwwwwwwtk..",
"..kWwkkwwkkwtk..",
"..kWwkkwwkkwtk..",
"..kwwwwwwwwwtk..",
"..kwwkkwwkkwtk..",
"..kwwkkwwkkwmk..",
"..kwwwwwwwwtmk..",
"...kmttttttmk...",
"....kkmmmmkk....",
".....kkkkkk.....",
"................",
"................"])

add('trinket','knuckle_die',[
"................",
"................",
"...kkkkkkkkkk...",
"..kWwwwwwwwwtk..",
"..kwkkwwwwkktk..",
"..kwkkwwwwkktk..",
"..kwwwwwwwwwtk..",
"..kwwwwkkwwwtk..",
"..kwwwwkkwwwtk..",
"..kwwwwwwwwwtk..",
"..kwkkwwwwkktk..",
"..kwkkwwwwkkmk..",
"..kwwwwwwwwtmk..",
"...kkkkkkkkkk...",
"................",
"................"])

add('trinket','dead_clover',[
"................",
"...kkk....kkk...",
"..kLllk..kLllk..",
"..kLlllkklllGk..",
"..kllllGGlllGk..",
"...kkllGGllkk...",
"....kkGllGkk....",
"..kkllllllllkk..",
".kLllllGGllllGk.",
".kLlllkGGklllGk.",
"..kkkk.kGk.kkk..",
"........kGk.....",
".......kGk......",
".......kGk......",
"......kgk.......",
"................"])

# ------------------------------------------------------------------ FAMILIARS
add('familiar','tiny_skull', S16([
"........",
"....kkkk",
"..kkWWww",
".kWWwwww",
".kWwwwww",
".kwwkkww",
".kwwkkww",
".kwwwwwk",
"..kwwwww",
"...kmwmw",
"...kkwmw",
"....kkkk",
"........",
"........",
"........",
"........"], {'W':'w','w':'w','m':'m'}))

add('familiar','wandering_eye', [
"................",
".....kkkkkk.....",
"...kkWwwwwwkk...",
"..kWwwwLLLwwtk..",
".kWwwwLllLGwwtk.",
".kwwwwLlkkGwwtk.",
".kwweLlkkkGwwtk.",
".kwwwwLllGwwttk.",
".kwwwwwGGwwwttk.",
".kwwewwwwwwwttk.",
"..kwwwwwwwwttk..",
"...kkwwwwwtkk...",
".....kkReRk.....",
"......kRek......",
".......kk.......",
"................"])

add('familiar','cave_bat', S16([
"........",
"........",
".k....k.",
".kk..kPk",
".kPkkkPP",
".kPPkPPe",
"..kPPPPP",
"..kPkPPk",
"...kk.kP",
"........",
"........",
"........",
"........",
"........",
"........",
"........"], {'P':'P','e':'e','u':'P'}))

add('familiar','crypt_spider', S16([
"........",
"........",
"...k....",
"..k.kkkk",
".k.kPPuu",
"k.kPPuuP",
"kkkPPPPP",
"..kPPrrP",
".kkPPPPP",
"k.kkPPPP",
"k..kkkkk",
"........",
"........",
"........",
"........",
"........"], {'u':'P'}))

add('familiar','sheet_ghost', S16([
"........",
"....kkkk",
"...kWWww",
"..kWwwww",
"..kWwwww",
"..kwkkww",
"..kwkkww",
"..kwwwkk",
"..kwwwww",
"..kwwwtt",
"..kwwtt.",
"..kwtkwt",
"..kkk.kk",
"........",
"........",
"........"], {'W':'t','w':'w'}))

add('familiar','bile_slime', S16([
"........",
"........",
"........",
".....kkk",
"...kkLll",
"..kLllll",
".kLllWll",
".kLlllll",
".kllkkll",
".kllkkll",
".kGllllG",
".kGGGGGG",
"..kkkkkk",
"........",
"........",
"........"], {'L':'G','W':'l','G':'g'}))

add('familiar','grave_fly', S16([
"........",
"........",
"..kkk...",
".kcWBk..",
".kcWBBk.",
"..kkBBkk",
"....kkgG",
"...kgGGG",
"..kgGeeG",
"..kgGGGG",
"...kgGGG",
"....kkkk",
"........",
"........",
"........",
"........"], {'c':'B','W':'B','B':'b','G':'G','g':'g','e':'e'}))

add('familiar','horned_imp', S16([
"........",
".kk.....",
".kEk.kkk",
".kEkkkRR",
"..kkReRR",
"..kReeee",
"..kRZkee",
"..kReeee",
"...kReee",
"..kkkeee",
".kReekRe",
".kRRekRR",
"..kkkkkk",
"........",
"........",
"........"], {'E':'e','R':'R','Z':'Z','e':'R'}))

