# TBOIQ Dungeon-24 - palette notes

24 colours, every ramp hue-shifted (shadows slide toward violet/blue, highlights toward yellow/orange).
There is **no pure black** and no pure white: darkest `#0e0b14` carries a violet tint, brightest `#f5ebcf` is warm cream.

| key | hex | name | role | contrast vs k | vs n |
|---|---|---|---|---|---|
| `k` | `#0e0b14` | void black | outline / page background (tinted, never pure black) | 1.0 | 1.1 |
| `n` | `#17121f` | crypt night | panel / card background | 1.1 | 1.0 |
| `p` | `#281d3a` | deep violet | shadow tone for purples, glass interior | 1.2 | 1.2 |
| `P` | `#43305c` | dusk violet | mid tone purple | 1.7 | 1.6 |
| `u` | `#6e5a9e` | wisp violet | highlight purple | 3.4 | 3.2 |
| `b` | `#1c2646` | abyss blue | shadow tone for blues/steel | 1.3 | 1.2 |
| `B` | `#35508c` | iron blue | mid tone blue/steel | 2.5 | 2.3 |
| `c` | `#74a3c8` | frost blue | highlight blue/steel, glass glint | 7.3 | 6.8 |
| `r` | `#2c0e1c` | clot | darkest blood / red outline | 1.1 | 1.0 |
| `R` | `#6a1527` | dried blood | shadow red | 1.6 | 1.5 |
| `e` | `#a62336` | blood | mid red | 2.7 | 2.6 |
| `E` | `#e2573f` | fresh blood | highlight red (hue-shifted to orange) | 5.3 | 5.0 |
| `q` | `#34252f` | grave dust | bone outline / darkest bone | 1.3 | 1.3 |
| `m` | `#66504f` | old bone | bone shadow | 2.6 | 2.5 |
| `t` | `#a38c76` | bone | bone mid | 6.1 | 5.7 |
| `w` | `#d9c8a2` | pale bone | bone light | 11.8 | 11.1 |
| `W` | `#f5ebcf` | cream | bone highlight / text | 16.4 | 15.5 |
| `g` | `#17352b` | rot green | darkest green | 1.5 | 1.4 |
| `G` | `#35653a` | moss | shadow green | 2.9 | 2.7 |
| `l` | `#78a03a` | sickly green | mid green | 6.4 | 6.0 |
| `L` | `#bfcd5c` | bile | highlight green (hue-shifted to yellow) | 11.2 | 10.6 |
| `y` | `#9c4d1c` | ember brown | torch shadow / rust | 3.2 | 3.1 |
| `Y` | `#e8902a` | torchlight | warm accent | 7.9 | 7.4 |
| `Z` | `#ffd56b` | flame | brightest accent / hover | 13.9 | 13.1 |

## Ramps

- **void/night (tinted near-blacks)**: `k` -> `n` -> `p` -> `P` -> `u`
- **blood reds**: `r` -> `R` -> `e` -> `E`
- **bone / cream**: `q` -> `m` -> `t` -> `w` -> `W`
- **sickly greens**: `g` -> `G` -> `l` -> `L`
- **dusk purples**: `p` -> `P` -> `u`
- **iron / night blues**: `b` -> `B` -> `c`
- **torchlight (warm accent)**: `y` -> `Y` -> `Z`

## Contrast and usage

- Page background: `k` (#0e0b14). Cards/panels: `n` (#17121f) with a `p` border; use `P`/`u` only for hovered panels.
- Body text: `W` on `n` = 15.5:1, `w` on `n` = 11.1:1 (both AAA). Secondary text `t` on `n` = 5.7:1 (AA for normal text).
- Never set text in `m`, `q`, `p`, `P`, `b`, `r`, `R` on dark panels: they fall below 4.5:1 (`m` on `n` = 2.5:1). They are for outlines and shadows only.
- Accent / hover: `Z` flame 13.1:1, `Y` torchlight 7.4:1 on `n`. Use `Y` for focus rings and hovered icons, `Z` for tiny sparks and the single most important highlight per screen.
- Correct = `L`/`l` on `n` (10.6:1 / 6.0:1). Wrong = `E` on `n` (5.0:1); `e` is only 2.6:1, so use it for fills, not text.
- Colour-blind safety: never rely on red vs green alone; correct/wrong icons differ in shape (check vs X).
- Limit any single sprite to 3-4 tones of one ramp + a dark outline tone of the same ramp. Outlines: bone -> `q`, red -> `r`, green -> `g`, purple -> `p`, blue/steel -> `b`, torch/gold -> `R`. `k` is reserved for voids (pupils, keyholes, eye sockets, pips).
- Lighting is always top-left: highlight tone on upper-left edges, shadow tone on lower-right edges.
- Icon-only UI: normal state = bone ramp (`W w t` + `m` outline); hover/active = torch ramp (`Z Y y` + `R` outline). Correct/wrong keep their hue and just brighten.
