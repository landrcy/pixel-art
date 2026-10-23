# Pixel Art Playbook for "pixel boss"

Audience: the `pixel boss` agent making pixel-art backgrounds, animated scenes and sprites for the **central website** and the **fish site** (fish / underwater and other themes), working alongside the central-website and fish-site bots.
Goal: art that reads as **hand-made by a skilled pixel artist** and **not AI-generated**.
Written 2026-10-23. Companion code (tested, runs on Python 3 + Pillow + numpy):
- `/workspace/pixel_tools.py` – palettes, hue-shift ramps, 10 dither patterns, gradients, quantize, upscale, sheets, palette-cycling, `lint()` for AI tells. Run `python3 pixel_tools.py` for the self-test + demo PNGs.
- `/workspace/pixel_scene_demo.py` – the underwater scene recipe of section 7 as runnable code (320x180, 8-frame loop).
- Dithering study reference (user-supplied image, analysed in section 2): a sheet with 2-, 3- and 4-colour rows × 10 dither styles in a navy → mauve → dusty-pink → cream sunset palette.

---

## 0. The 12 non-negotiables (read this first)

1. **One pixel size per image/scene.** Draw at native low resolution (e.g. 320x180 or 480x270), export 1x, scale only by **integers** with nearest-neighbour. Never mix sprite scales, never rotate/scale a sprite by a non-integer, never blur.
2. **Every pixel is an opaque palette colour.** No alpha < 255 (except fully transparent 0), no glows, no soft shadows, no filters, no JPEG. Run `lint()` before delivering.
3. **Small palette, chosen up front.** Whole scene 16–32 colours (a hero background can go to ~48). Sprite: 4–12 colours. Reuse the same ramps across layers.
4. **Colour in ramps with hue shift:** shadows drift cool/purple, highlights drift warm/yellow-cyan; saturation peaks in the mids; never pure black or pure white.
5. **One light direction** for the whole scene (default: upper-left; underwater: from the top, slightly left).
6. **Gradients are hard bands of uneven height**, with dithering *only* on the 2–4 pixel seam between bands (or a half-pixel "bridge" row). Never a smooth gradient, never full-area noise.
7. **Cluster, don't speckle.** Few big clean shapes; no orphan pixels except deliberate sparkles/eyes/stars; no "doubles" in lines; no pillow shading.
8. **Selective outlines (sel-out):** darkest colour of the *neighbouring fill's ramp*, thinner/lighter on the lit side; no uniform black outline, no outline on far background layers.
9. **Anti-alias by hand, sparingly:** 1–2 intermediate pixels on long shallow curve steps only; check at 1x.
10. **Depth by colour, then detail, then speed:** farther layers = paler, cooler, less contrast, fewer details (closer to the sky/water colour behind them).
11. **Animate with spacing and uneven frame timing**, 2–8 frames, loops that close exactly; movement ≤1 px per frame for ambient water; keep cluster structure stable between frames.
12. **Squint + 1x test + grayscale test** on every deliverable (section 8 QA checklist).

---

## 1. Colour theory for pixel art

### 1.1 Palette size limits (concrete numbers)
| Asset | Colours | Notes |
|---|---|---|
| Small sprite 16–32 px | 4–8 (+ outline ramp) | one 3–4 step ramp per material; share the dark outline colour(s) |
| Large sprite 48–96 px | 8–16 | |
| Tileable water/ground tile | 4–8 | low contrast base + small bright overlay |
| One background layer | 3–6 (far layers 2–3) | far layers nearly flat |
| Whole scene | 16–32 (up to ~48 hero) | from a *named palette* (below); log the hex list in the asset folder |
- A **ramp** = 3–5 colours going dark → light of one material. Palette = several ramps that share hue-shifted neighbours so they harmonise.
- Constraint is the style: if a scene "needs" 80 colours you have too many shapes or too much noise, not too few colours. Fix shapes first (pixeli: *"Clean shapes in 5 colours beat a noisy texture in 5 colours"*).
- Adopt an existing palette for consistency across the two sites, then extend it with 2–4 custom ramps for brand colours.

### 1.2 Hue shifting & saturation/brightness curves (Slynyrd's HSB method)
- Work in **HSB/HSV**. Slynyrd's recipe for a general-purpose palette: ramps of **9 swatches**, brightness rising steadily left→right (rarely starting at 0 unless you want black), saturation peaking around the middle and never at 0 or 100, **up to +20° hue shift per swatch** (positive shift = warms as it brightens), and avoid max-saturation + max-brightness together. [S1]
- Rules of thumb:
  - **Shadows**: lower brightness, hue rotates toward blue/violet (≈240–280°); keep saturation equal or higher than the mid (rich, not grey) — Slynyrd: "darker colors have more saturation", but very dark + very saturated gets heavy/weighty.
  - **Highlights**: brightness up, **saturation down**, hue rotates toward yellow (warm light) — or toward cyan for underwater/cool light. Pure-white highlights only for specular glints.
  - **Straight ramps** (only brightness/saturation change, no hue shift) look dull and don't harmonise with other ramps — use only for deliberately monochrome looks. [S1]
  - Hue shift per step: 8–20° is the useful range; 3–5 step ramps need only ~10–14° per step. The ramp generator default is 14°.
  - Make contrast between adjacent ramp steps **even** (check in grayscale: steps should be evenly spaced).
- Underwater: apply a *global* cool shift — red/orange vanish first with depth (warm colours only near the surface or near a light source), leaving blue/cyan/violet at low contrast. [S11]
- Typical numbers (HSB) for a 5-step ramp, dark→light, base hue H:
  `step1: H-20..-30°, S 55–70, B 20–30` · `step2: H-10°, S 65–80, B 40–50` · `step3: H, S 70–85, B 62–72` · `step4: H+10..15°, S 55–65, B 82–88` · `step5: H+20..30°, S 25–35, B 95`. (Starting point — hand-tune and snap to your palette.)
- Tool: `pixel_tools.make_ramp(base_hex, steps=5, hue_shift=14)` returns hex dark→light with these curves (see §6.3). It is a **starting point**; round results to your palette with `quantize` or hand-nudge them.

Example generated ramps (`make_ramp(base, 5)`, dark → light):
| Material | Base | Ramp |
|---|---|---|
| Ocean blue | `#3b82c4` | `#1a1c40 #263a6b #2d6496 #59a8c2 #92eced` |
| Teal water | `#2e9bb0` | `#182740 #224e6b #278496 #53c2ba #8dedd0` |
| Clownfish orange | `#e07438` | `#40171c #6b2a21 #964e26 #c29451 #eddc8b` (highlights are very yellow – tone down by hand) |
| Kelp green | `#33984b` | `#1c4035 #296b48 #32964a #5ec25e #aaed96` |
| Sand | `#c09473` | `#402a2b #6b4b43 #96745a #c2ad86 #ede8b9` |
| Coral pink | `#e86a73` | `#402232 #6b3546 #96454b #c27d70 #edc2a6` |
| Violet shadow | `#7a367b` | `#312140 #5d346b #954296 #c26eaf #eda4cc` |

### 1.3 Famous Lospec palettes (hex verified from `lospec.com/palette-list/<slug>.hex` on 2026-10-23)
**Endesga 32** (32 colours) – https://lospec.com/palette-list/endesga-32
```
#be4a2f #d77643 #ead4aa #e4a672 #b86f50 #733e39 #3e2731 #a22633 #e43b44 #f77622 #feae34 #fee761 #63c74d #3e8948 #265c42 #193c3e #124e89 #0099db #2ce8f5 #ffffff #c0cbdc #8b9bb4 #5a6988 #3a4466 #262b44 #181425 #ff0044 #68386c #b55088 #f6757a #e8b796 #c28569
```
**Endesga 64** (64 colours) – https://lospec.com/palette-list/endesga-64
```
#ff0040 #131313 #1b1b1b #272727 #3d3d3d #5d5d5d #858585 #b4b4b4 #ffffff #c7cfdd #92a1b9 #657392 #424c6e #2a2f4e #1a1932 #0e071b #1c121c #391f21 #5d2c28 #8a4836 #bf6f4a #e69c69 #f6ca9f #f9e6cf #edab50 #e07438 #c64524 #8e251d #ff5000 #ed7614 #ffa214 #ffc825 #ffeb57 #d3fc7e #99e65f #5ac54f #33984b #1e6f50 #134c4c #0c2e44 #00396d #0069aa #0098dc #00cdf9 #0cf1ff #94fdff #fdd2ed #f389f5 #db3ffd #7a09fa #3003d9 #0c0293 #03193f #3b1443 #622461 #93388f #ca52c9 #c85086 #f68187 #f5555d #ea323c #c42430 #891e2b #571c27
```
**Resurrect 64** (64 colours) – https://lospec.com/palette-list/resurrect-64
```
#2e222f #3e3546 #625565 #966c6c #ab947a #694f62 #7f708a #9babb2 #c7dcd0 #ffffff #6e2727 #b33831 #ea4f36 #f57d4a #ae2334 #e83b3b #fb6b1d #f79617 #f9c22b #7a3045 #9e4539 #cd683d #e6904e #fbb954 #4c3e24 #676633 #a2a947 #d5e04b #fbff86 #165a4c #239063 #1ebc73 #91db69 #cddf6c #313638 #374e4a #547e64 #92a984 #b2ba90 #0b5e65 #0b8a8f #0eaf9b #30e1b9 #8ff8e2 #323353 #484a77 #4d65b4 #4d9be6 #8fd3ff #45293f #6b3e75 #905ea9 #a884f3 #eaaded #753c54 #a24b6f #cf657f #ed8099 #831c5d #c32454 #f04f78 #f68181 #fca790 #fdcbb0
```
**Apollo** (46 colours) – https://lospec.com/palette-list/apollo
```
#172038 #253a5e #3c5e8b #4f8fba #73bed3 #a4dddb #19332d #25562e #468232 #75a743 #a8ca58 #d0da91 #4d2b32 #7a4841 #ad7757 #c09473 #d7b594 #e7d5b3 #341c27 #602c2c #884b2b #be772b #de9e41 #e8c170 #241527 #411d31 #752438 #a53030 #cf573c #da863e #1e1d39 #402751 #7a367b #a23e8c #c65197 #df84a5 #090a14 #10141f #151d28 #202e37 #394a50 #577277 #819796 #a8b5b2 #c7cfcc #ebede9
```
**AAP-64** (64 colours) – https://lospec.com/palette-list/aap-64
```
#060608 #141013 #3b1725 #73172d #b4202a #df3e23 #fa6a0a #f9a31b #ffd541 #fffc40 #d6f264 #9cdb43 #59c135 #14a02e #1a7a3e #24523b #122020 #143464 #285cc4 #249fde #20d6c7 #a6fcdb #ffffff #fef3c0 #fad6b8 #f5a097 #e86a73 #bc4a9b #793a80 #403353 #242234 #221c1a #322b28 #71413b #bb7547 #dba463 #f4d29c #dae0ea #b3b9d1 #8b93af #6d758d #4a5462 #333941 #422433 #5b3138 #8e5252 #ba756a #e9b5a3 #e3e6ff #b9bffb #849be4 #588dbe #477d85 #23674e #328464 #5daf8d #92dcba #cdf7e2 #e4d2aa #c7b08b #a08662 #796755 #5a4e44 #423934
```
**Sweetie 16** (16 colours) – https://lospec.com/palette-list/sweetie-16
```
#1a1c2c #5d275d #b13e53 #ef7d57 #ffcd75 #a7f070 #38b764 #257179 #29366f #3b5dc9 #41a6f6 #73eff7 #f4f4f4 #94b0c2 #566c86 #333c57
```
**PICO-8** (16 colours) – https://lospec.com/palette-list/pico-8
```
#000000 #1d2b53 #7e2553 #008751 #ab5236 #5f574f #c2c3c7 #fff1e8 #ff004d #ffa300 #ffec27 #00e436 #29adff #83769c #ff77a8 #ffccaa
```

**Which to use for what**
- **Endesga 32** (EDG32, by Endesga) – best "all-rounder" for sprites + scenes; clean skin/earth/green/blue ramps with hue shift built in.
- **Resurrect 64** (by Kerrie Lake) – rich hue-shifted ramps, good for atmospheric backgrounds and underwater (teals `0b5e65 0b8a8f 0eaf9b 30e1b9 8ff8e2`, blues `323353 484a77 4d65b4 4d9be6 8fd3ff`).
- **Apollo** (by AdamCYounis) – 46 colours, naturalistic; excellent blue ramp for skies/water (`172038 253a5e 3c5e8b 4f8fba 73bed3 a4dddb`).
- **AAP-64** (by Adigun A. Polack) – very complete, great for big scenes; has cyan/teal (`143464 285cc4 249fde 20d6c7 a6fcdb`) and warm neutrals.
- **Endesga 64** – superset flavour of EDG32 with more ramps (blues `0069aa 0098dc 00cdf9`, deep indigos `03193f 1a1932 0e071b`).
- **Sweetie 16** (by GrafxKid) – small, punchy, reads well at tiny sizes; good for UI/small sprites.
- **PICO-8** (Lexaloffle) – 16 fixed fantasy-console colours; strong retro look, but harsh saturated primaries; use only when you want *that* look.
- Pick **one master palette per site** (e.g., fish site = Resurrect 64 / Apollo subset; central site = Endesga 32) and put the chosen subset in `palette.hex` next to the assets so all bots share it.

### 1.4 Curated sub-palettes (copy/paste)
- **Sunset dither-study palette** (extracted from the user's study image; navy → mauve → dusty pink → cream):
  `#272744` navy · `#8b6d9c` mauve purple · `#c69fa5` dusty pink · `#f2d3ab` cream. Built in as `PALETTES["sunset_study"]`. Note the hue behaviour: navy-violet shadows → purple → warm pink → warm cream highlight: exactly the "shadows cool/purple, highlights warm" rule in 4 colours. Outline colour in the study sheet is near-black `#000000`-ish; for web art prefer `#1a1932`/`#272744`.
- **Underwater depth ramp (surface → abyss)**, Endesga 64: `#0cf1ff`(rare glints) `#0098dc` · `#0069aa` · `#00396d` · `#0c2e44` · `#1a1932`. (Hue goes cyan-blue → violet-indigo with depth.)
- **Tropical seabed (dark → light)**, Resurrect 64: `#1a1932`(E64) `#0c2e44`(E64) `#0b5e65` `#0eaf9b` `#8ff8e2`; sand: `#c09473 #d7b594 #e7d5b3` (Apollo), shade `#7a4841 #ad7757`.
- **Kelp/seaweed**, Endesga 64: `#134c4c #1e6f50 #33984b #5ac54f #99e65f`.
- **Clownfish / coral warm set**, Endesga 64: outline `#571c27`, `#8e251d #c64524 #e07438 #ffa214`, stripe white `#f9e6cf`, coral pinks `#891e2b #c42430 #f5555d #f68187`.
- **Night / deep sea**: `#0e071b #1a1932 #2a2f4e #424c6e #657392`(E64) with bioluminescent accents `#00cdf9 #94fdff #f389f5`.
- **Dusk sky (Slynyrd-style sunset)**: `#2f3a85 #6e5aa3 #e58fa6 #f7c58a #f08a45 #d9503a` + ground silhouette `#2a1f3d` (from the Pixeli sunset template [S6]).

### 1.5 Colour rules that kill "AI look"
- AI output has "hundreds of near-duplicate colours" instead of deliberate ramps. [S9]
- Never pure `#000000` or `#ffffff` for large areas; darkest dark ≈ `#0e071b`–`#1a1932`, lightest ≈ `#f9e6cf`/`#ede8b9` (tinted).
- Don't use one hue for everything: pair a dominant ramp (60%), secondary (30%), accent (10%).
- Squint test: collapse to grayscale; if the value structure doesn't read, colour won't save it.

---

## 2. Gradients & dithering

### 2.1 Core ideas
- Banding (the problem): too few colours for a smooth ramp → visible stripes. **Pixel-art banding** (a different defect): two clusters running the same diagonal creating a long parallel seam (§3.5). Don't confuse them. [S3]
- **Hand-made gradients = hard bands + dithered seams.** Fully dithered full-area gradients look "filtered"/computer-made; flat full-area bands look like stripes.
- **Dither vs band decision** [S2,S3,S4,S6]:
  - **Band (no dither)**: small sprites, anything that moves, faces, canvases ≤32 px tall, UI, anything where you can add 1 more ramp colour instead.
  - **Dither**: large static areas (sky, water, fog, light falloff, big walls/ground) where the palette is locked; **only between adjacent ramp colours**; 2–4 rows, never across the whole area; if dither covers ≈half an object, add a colour instead.
  - **Never**: random noise as a gradient (clumps + orphans), error diffusion (Floyd–Steinberg boils in animation, can't be hand-edited) [S4].

### 2.2 Dither types (ASCII, `#`=lighter colour; levels low→high)
```
checker 50%      25% (bayer2)      75%             bayer4 (16 levels)   threshold matrix /16
# . # .          # . . .           # # # .          0  8  2 10           (0.5 offset added)
. # . #          . . . .           # . # #         12  4 14  6
# . # .          . . # .           # # # .          3 11  1  9
. # . #          . . . .           . # # #         15  7 13  5
```
- **Ordered / Bayer (2×2, 4×4, 8×8)**: 5 / 17 / 65 tones between two colours. Fixed pattern = stable in animation, editable by hand, looks like what a human would draw. **4×4 is the default**; 8×8 smoother but looks computer-made at small sizes. [S2,S4]
- **Checker (50%)**: cleanest single mid-tone; no two same pixels touch sideways. Build the transition from the middle: 50% checker at the centre of the change, 25/75 outward, then flat. 3–5 levels are plenty. [S6]
- **Noise / random**: only as intentional texture (gravel, sand, rust), never as the gradient.
- **Never a "wide pixel"**: two touching dither pixels (2×1) read as a mistake — usually a phase break where two patches meet; keep one phase `(x+y) mod 2` across the area. [S6]

### 2.3 The 10 styles in the user's dithering study (all implemented in `pixel_tools.threshold_map`)
The study sheet has columns = styles, rows = 2 / 3 / 4 colours (navy → mauve → dusty pink → cream). What each column is and the `pixel_tools` name:
| # | Look in the study | `pattern=` | Use for |
|---|---|---|---|
| 1 | Ordered **zig-zag / diamond** rows (Bayer-like, tight) | `bayer2` / `diamond` | sky seams, chunky retro |
| 2 | Fine ordered, soft | `bayer4` | **default** skies/water |
| 3 | Finer ordered (mixed checker/dots) | `bayer8` | large wide backdrops |
| 4 | **Dashes** (2×1 brick offsets) | `dashes` | water ripples, brick/stone, horizontal-flow textures |
| 5 | **Horizontal line / stripe** dither (thin→thick lines) | `hlines` | water, horizon haze, floors, sunsets (lines follow the horizon) |
| 6 | Lines + dotted rows (fine scanline) | `hlines_dots` | softer line dither, fog |
| 7 | Heavier line + dot mix with chunky bars | `diamond` / `hlines_dots` | stylised sunset |
| 8 | **Hard band** with a single alternating "bridge" row at the edge | `band_bridge` | the cheapest hand-made seam: small/animated areas |
| 9 | **Noise / organic scatter** (density rising toward the seam) | `noise` | texture only, sparingly |
| 10 | **Cross / star (plus-shaped)** dither | `cross_sparse` (period 8) / `cross` (period 4) | starry dusk skies, magical/underwater sparkle, stylised look |
Observations from the study to copy:
- In the **2-colour** row the transition is a thin dithered seam between two big flat blocks; in **3/4-colour** rows each *segment* has its own seam and **flat colour dominates** — i.e. dither only the middle ~30–40% of each segment (`transition=0.35` in `dither_gradient`). This is the single biggest "hand-made" lever.
- Band heights are **unequal** (cream is the thickest at the bottom, navy thick at the top, the mauve band thickest among the middle ones).
- Patterns follow the subject: **horizontal line dither** and dashes for water/horizon, **cross/star** for sky, diamond for generic ordered fades.
- Same 4 colours in every column – the palette is the constraint; the pattern is the "brush".

### 2.4 Band-width progression (recipes)
- Bands must be **uneven**; equal bands read as stripes. Slynyrd's measured valley sky: **13/17/10/7/16 rows**. [S6]
- Sky/water in a 4–5 colour vertical ramp: top and bottom bands thickest, seams get **thinner toward the focal edge (horizon)**; progression example for 4 colours: relative heights **1 : 1.6 : 2.4** (`progression=[1,1.6,2.4]`) top→bottom; for the underwater ramp (surface→abyss) use **1 : 1.4 : 2 : 2.8** (deeper = thicker, since little changes at depth).
- Dither seam depth: 2–4 rows (checker first; 25/75 rows on tall skies). Size guide (Pixeli) [S6]: ≤32 px tall sky → 3–4 hard bands, **no dither**; ≤48 px → 2 dithered seams; 64–96 px → 3 seams; ≥128 px → bands ≥2 rows with ~4-row dither.
- Don't align seams with obvious pixel stairs of a nearby silhouette; stagger breaks by 1 px.

### 2.5 Gradient recipes (hex-ready)
**Sunset sky (4 colours, study palette):**
`#272744 → #8b6d9c → #c69fa5 → #f2d3ab`, `bayer4` or `cross_sparse`, `progression=[1,1.6,2.4]`, `transition=0.35`. Add a sun as 3–5 px disc `#f2d3ab` with ≤2 dither halo rings; ground silhouette `#1a1932`.
**Warm sunset (6 colours, Pixeli):** top→horizon `#2f3a85 #6e5aa3 #e58fa6 #f7c58a #f08a45 #d9503a`; lit objects warm gold, shadows blue-violet (hue 240–260°). [S6]
**Day sky:** `#3c70c9 #5aa0e6 #8ccaf0 #c6e8f2` (horizon lightest, least saturated), bands growing taller toward the horizon, 2-row checker joins. [S6]
**Water surface → abyss:** `#0098dc #0069aa #00396d #0c2e44 #1a1932`, thin bright band + sparkle line at the surface, depth bands thicker. Looking down into water: dark near-bed tint; far water mirrors the sky. [S5]
**Depth ramp (shallows → deep):** `#d9c27a #7da35a #3e9a8c #2f6fa0 #243a78` (red/ochre bed in the shallows → teal → blue → indigo). [S5]
**Night sky:** `#141a3d #232f66`, dim stars `#5566a8`, bright `#d6e0ff`, never `#000`. [S6]

---

## 3. Shapes, edges and shading

### 3.1 Clusters, orphans, jaggies
- **Cluster** = touching same-colour pixels (orthogonal contact joins; diagonal is weak). Design with few, large, clean clusters; squint and a few big masses of light/dark must survive. [S3,S7]
- **Orphan pixel** = isolated 1-px cluster. Delete it, merge it into a neighbour, or grow it to 2–3 px. Allowed orphans: specular highlight, tiny-sprite eye, star/spark, AA pixel, last frame of a particle; budget **≤1 per object at 16–32 px**. Never random speckle, never near a face. [S3,S7]
- **Jaggies**: a line is clean when its run lengths are consistent: `2,2,2,2` or `4,4,4,4`, not `3,2,4,1`. 45° = 1 px per step. Shallow lines = runs of N, N, N (same N). Curves: run lengths should progress smoothly (e.g. 1,2,3,... or 6,3,2,1,1,2,3,6) – never a lone pixel that breaks an even run. [S7,S8]
- **Doubles**: a pixel too many in a line (two pixels touching on the flat side where one diagonal step would do) → delete one. [S8]
- **Unintentional squares**: where two regions of one colour meet, pixels clump into 2×2 blocks – stagger colour changes brick-like. [S7]

### 3.2 Anti-aliasing (AA) by hand
- Place 1–2 in-between colour pixels on the *longer* steps of a curve/diagonal; stop. Over-AA makes edges blurry and kills the crisp look; if you can't see the AA at 1x it isn't needed. [S8]
- Never AA against transparency (semi-transparent alpha = AI-tell); against a varied background use sel-out or draw the background colour in.
- Don't fake distance with AA or blur: use lower contrast + fewer details. [S6]

### 3.3 Selective outlining (sel-out) — procedure [S9,S10]
1. Draw with a plain dark outline for a solid silhouette.
2. Pick the light direction (upper-left).
3. Walk the outline: replace the dark colour with the **darkest shade of the ramp of the shape it touches** (not black).
4. On the lit side step the outline 1–2 shades lighter or remove it where the shape is bright.
5. Keep the darkest outline on the shadow side; keep it 1 px; avoid L-shaped double corners.
6. Check on a dark and a light background and at 1x. Backgrounds/far layers: **no outlines**. Inner lines (between parts) use the same method.
Outline styles: none (backgrounds), full dark (icons), **selective (default for sprites)**, coloured (soft, painterly).

### 3.4 Pillow shading — avoid
Shade rings that follow the silhouette inward ignore the light. Pick a direction, model the form, **end the shade abruptly at a terminator** instead of blending back; one value cluster per plane facing; straight edges for flat planes, curved for round forms. [S7]

### 3.5 Banding (the parallel-seam kind) — fixes
Boundaries that run the same length and end on the same row/column make the grid show. Fix in this order: (a) **stagger** the breaks by 1 px so ends don't line up; (b) **compress** the bands so the step is crossed in 1–2 px; (c) **interlock** (zip) the two edges or dither the join; (d) change the angle/curve of the bands. [S3,S7]

### 3.6 Consistent light & pixel size
- Write down the light direction in the asset notes; every sprite and layer follows it (highlight rim on the side facing the light; cast shadows on the other side; underwater = from above).
- One pixel size: all assets in a scene share the same native resolution; if you must show a "big pixel" asset (UI icon), render the whole scene at the lower resolution first. Check with `lint(img, assumed_scale=k)` — `clean_block_ratio` must be 1.0.
- Keep sprite heights consistent across frames (ground-align the feet / fin base).

---

## 4. AI-tells to avoid and how to fix

| AI tell | Why it happens | How to fix (action for pixel boss) |
|---|---|---|
| **Mixed pixel sizes ("mixels")**: blocks of 3×3, 4×3, 3×4 or drifting off-grid | models generate high-res continuous images, no grid constraint [S9,S12] | Never ship generated art. Draw natively with code/palette. If given AI source: find the true cell size (flat run of one colour), snap with nearest-neighbour, rebuild one colour per cell, or redraw from reference at the target resolution. |
| **Blurry / sub-pixel edges**, soft halos, fade to transparent | diffusion denoising smooths edges [S9] | Nearest-neighbour only; `quantize()` to palette; threshold alpha; run `lint()`; never rotate/scale sprites in the browser unless by integers. |
| **Too many colours / near-duplicates** | blending noise [S9] | Cap scene at 16–32; map to a named palette; merge ramp steps that differ by <~8% brightness. |
| **Noisy detail, texture everywhere, orphan speckle** | no concept of clusters | Remove before adding: fewer colours, bigger clusters; texture = a few repeated glyphs + empty space; scatter quasi-random at uniform density, no two accents sharing a row/col. [S7] |
| **Inconsistent lighting** (highlights on both sides, shadows random) | no global light model | Fix the light direction; re-colour from ramps: lit planes = upper ramp, shadows = lower ramp with cool shift. |
| **Smooth gradients / glow / soft shadows** | continuous colour output | Hard bands + dithered seams; glow = ≤3 concentric dither rings; shadow = one dark-ramp cluster, not alpha. |
| **Over-symmetry, perfect repetition, "everything outlined"** | | Break symmetry with intentional asymmetry; vary band heights/cluster sizes; sel-out. |
| **Equal-height bands, perfectly even dither field** | | Uneven band heights (e.g. 13/17/10/7/16), dither only seams. |
| **Pillow shading, clip-art cotton-ball clouds** | | Terminator shading; clouds = overlapping lobes sharing a flat base, tinted from the sky colour, no outline. [S6] |
| **Cluttered composition, no focal point** | | One focal area with the highest contrast and detail; the rest simplified. |
Pipeline guard: `pixel_tools.lint(img, palette, max_colors=32, assumed_scale=k)` reports semi-transparent pixels, off-palette pixels, colour count, orphan ratio (**note:** dithered backgrounds legitimately have high orphan counts; lint sprites and ungridded art, ignore it for dithered skies), and block uniformity for upscaled exports. Fail the asset on any non-zero `semi_transparent_pixels`, `off_palette_pixels`, or `clean_block_ratio < 1`.

---

## 5. Animation

### 5.1 Frame counts & timing (rules of thumb) [S13,S14]
| Cycle | Frames | Timing |
|---|---|---|
| Idle / breathing (fish hover, tail) | 2–4 (up to 8 for fluid) | 200–400 ms per pose for subtle idles; fish tail 4 frames @ 120–200 ms |
| Walk | 4–8 | 100–150 ms, hold contact poses longer |
| Run | 6–8 | 60–100 ms |
| Attack | 3–6 | 40–60 ms strike, 150–250 ms hold |
| Ocean/wave surface | 8 frames @ ~8 fps | fewer = choppy |
| Water tile | 2–4 frames | 100 ms |
| Star twinkle | 3 frames (dot→plus→large plus), out of phase | 150–300 ms |
- **Non-uniform timing carries life**: Slynyrd's 8-frame idle uses 100 ms ×4 then 50 ms ×4 (slow fall, fast rise). Uniform timing reads mechanical. [S14]
- **Easing comes from spacing**: poses close together = slow, far apart = fast; no tween engine. Draw extremes first, then in-betweens; never nudge pixels frame-to-frame (drift). [S13]
- Keep cluster structure stable across frames (no one-frame orphans), same height/limb thickness/light direction; the last frame must be a plausible predecessor of frame 1. [S7,S13]
- Secondary motion: overlap and follow-through (fin trailing the body, kelp phase offset up the stem).

### 5.2 Water surface, caustics, wave loops [S5]
- Water = depth gradient + a **surface layer that moves ≤1 px per frame** + (reflection/shore cut into strips). White dashes on blue fill = "a rug".
- Two layers: top ripples/wave shapes where nothing moves more than 1 px (each ripple one chunk, never split; path up→left→down→right closed loop); bottom base tile scrolls at constant speed (≈0.5 px/frame at 100 ms in saint11's tile).
- Measured 16×16 water tile: base `#627aea` with 17% flecks one step darker (`#5b6ee1`), overlay mid `#639bff` 28%, cyan glint `#5fcde4` 7%, pale `#cbdbfc` <2%; overlay shapes are 1–2 px thick dashes 4–7 px long. Overlay ≤30% of pixels.
- **Caustics**: a network of 1-px wavy lines in the *lightest water tone* on the seabed/objects (mask to lit surfaces), shifting 1 px alternately over **4–8 frames**; make lines broken (not continuous) and irregular. Vertical **god rays** from above: varying widths, dithered not alpha, fade with depth. Bubbles: random horizontal drift, rise, fade (dither away). [S5]
- Waves: chain of ovals as the guide (circles = short deep waves, wide ovals = shallow; crests steeper than troughs). Period must divide the loop: waterfall "period 8, shift 2 → 4 frames". [S5]
- Reflections: only upright objects, mirror about contact line, shorten ~25%, darken one ramp step, cut into 1-px strips offset ±1 px on a 2-row period, fade lowest third by replacing every other pixel with water colour. [S5]
- Surface sparkle: a 6-frame loop of simple linear moves.

### 5.3 Parallax layers (design; implementation in §6/§7) [S15,S16]
- 3 layers is the sweet spot, 5 max. Factors: sky/sun 0–0.2 · far 0.2–0.4 · middle 0.4–0.6 · near-bg 0.6–0.8 · gameplay 1.0 · foreground 1.1–1.5.
- **Whole-pixel scroll only**; for looping previews the px/frame rate must divide the layer width (e.g. 320 px layers: 1,2,4,5,8,10,16,20,32,40…); rates <1 px/frame jitter — repeat the image twice instead. Left edge = right edge pixel-for-pixel. [S15]
- Every non-sky layer fills solid to the bottom (no hovering); the sun/moon is a separate fixed sprite (it repeats if baked into a looping sky).
- Depth by colour: per receding layer −20–40% saturation, compressed values, hue toward the sky/water colour, drop interior details; the farthest layer = 1–2 flat colours. Never scale layers to fake distance (mixed pixel sizes). [S15]

### 5.4 Idle loops (fish, creatures, props)
- Fish idle: 4-frame tail pose cycle (0,1,0,2 = neutral, up, neutral, down), 2-px vertical bob over 8 frames (one sine period, integer rounding), fins offset a frame behind the body. Swim motion is done at runtime (CSS/JS translate by integer pixels), not baked.
- Props: kelp sway 1–2 px with phase offset per height (`sin(2π(f/N − j/22))`), jellyfish pulse 4 frames (bell squash 1 px), bubbles 1 px/frame.
- Pace the frames with uneven durations (hold the extreme pose longer).

### 5.5 Palette cycling (Mark Ferrari) [S17]
- Keep ONE static indexed image and rotate palette slots: the pixels don't move, their colours cycle in a looping sequence, creating moving bands (marquee-light principle). Needs the image + palette authored for it. 4–5 entries per cycling band for water; offset adjacent bands so the colour change reads as motion; cycle length should divide the frame rate (4 frames @12 fps = 1 s loop). [S17,S18]
- Web: draw index buffer once, update only the pixels that reference cycling entries (EffectGames optimisation) or use CSS custom properties on SVG rects. `pixel_tools.palette_cycle_frames(indexed, palette, [(lo,hi)], n)` bakes a GIF/sheet.
- Great for: shimmering water surface, waterfalls, glow, aurora, bioluminescence in the fish site. Time-of-day = swap/blend whole palettes without repainting. [S6]

### 5.6 Sprite sheets
- One horizontal strip per animation (frame size constant, e.g. 32×24), transparent background, padded identically, ground/baseline aligned across frames; tag name, frame count and per-frame ms in a JSON next to the PNG. Export 1x; upscale in CSS/canvas only.
- `pixel_tools.sprite_sheet(frames)` → strip; `save_gif(frames, path, ms=[...], scale=k)` for preview.

---

## 6. Web implementation

### 6.1 Rendering crisply [S19, S20]
```css
.pixel, canvas.pixel { image-rendering: pixelated; }   /* Chrome, Safari, Firefox, Edge */
.pixel { image-rendering: crisp-edges; }               /* fallback is okay; list pixelated LAST so it wins where supported */
```
- Store art at **native resolution** (small PNG, palette-indexed 8-bit where possible); never ship pre-blurred JPEG/WebP-lossy. Use **PNG**.
- Scale by **integers**: CSS `width: calc(var(--w) * var(--scale))` with `--scale` an integer (2, 3, 4…). Non-integer scale or browser zoom (devicePixelRatio non-integer, e.g. 110%) makes some pixels bigger than others — MDN documents this; mitigate by choosing the scale with JS: `scale = Math.max(1, Math.floor(containerWidth / nativeW))` and letterbox the rest with the palette's darkest colour. [S19]
- Full-bleed backgrounds: render the canvas at native res (e.g. 480×270), CSS-scale by the largest integer that fits (or `Math.ceil` + `overflow:hidden` + `object-fit`/center crop); keep `aspect-ratio` and center. Pick native sizes that multiply into 1920×1080: 320×180, 384×216, 480×270, 640×360, 960×540. [S15]
- Always `ctx.imageSmoothingEnabled = false;` and draw at **integer** coordinates and **integer** dest sizes (`dWidth = sWidth * n`). `ctx.scale(non-integer)` → blur.
- `devicePixelRatio`: for canvases, size the backing store to native res and let CSS scale, as MDN does (`width/height` attributes = native, CSS = ×scale). [S19]
- Respect `prefers-reduced-motion: reduce` (stop loops, show frame 0).

### 6.2 CSS sprite-sheet animation with `steps()` [S20]
```html
<div class="fish" role="img" aria-label="clownfish swimming"></div>
```
```css
.fish {
  --scale: 4;                       /* integer */
  --fw: 14px; --fh: 8px; --frames: 4;
  width:  calc(var(--fw) * var(--scale));
  height: calc(var(--fh) * var(--scale));
  background: url("fish-sheet.png") 0 0 / calc(var(--fw) * var(--frames) * var(--scale)) calc(var(--fh) * var(--scale)) no-repeat;
  image-rendering: pixelated;
  animation: fish-tail 0.64s steps(var(--frames)) infinite;     /* 4 frames, 160 ms each */
}
@keyframes fish-tail { to { background-position-x: calc(var(--fw) * var(--frames) * var(--scale) * -1); } }
/* swimming: translate by whole device pixels, in steps for chunky motion; move by multiples of --scale */
.fish { animation: fish-tail .64s steps(4) infinite, swim 20s steps(240) infinite linear; }
@keyframes swim { from { translate: -20% 0; } to { translate: 120vw 0; } }
@media (prefers-reduced-motion: reduce) { .fish { animation: none; } }
```
- `steps(N)` = jump discretely: **N = number of frames**. For uneven timing use keyframe percentages: `0%{background-position-x:0} 30%{…-1 frame…}` with `steps(1, end)` per keyframe, e.g. hold frame 0 for 35%.
- Backgrounds that scroll forever (parallax strip): animate `background-position-x` by exactly the **tile width × scale** with `steps(tileW)` (one step per native pixel), `linear infinite`, so every step is a whole native pixel:
```css
.layer-far  { background: url(far.png) repeat-x bottom / auto 100%; animation: pan-far  96s steps(320) infinite linear; }
@keyframes pan-far  { to { background-position-x: calc(-320px * var(--scale)); } }  /* 320 native px layer */
```
- Hard-banded CSS gradient fallback (no dither): `background: linear-gradient(#272744 0 22%, #8b6d9c 22% 45%, #c69fa5 45% 70%, #f2d3ab 70%);` (uneven stops; **never** soft `linear-gradient(a,b)` — smooth gradient is an AI tell). Dither seams need an image.

### 6.3 Canvas rendering with palette + Bayer dithering (JS, tested in Node)
```js
const BAYER4 = [[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]].map(r => r.map(v => (v + 0.5) / 16));
const hex = h => [1,3,5].map(i => parseInt(h.slice(i, i + 2), 16));
// vertical multi-colour gradient: hard bands of uneven height, dither only the middle 35% of each segment
function ditherGradient(w, h, colors, bandWeights, transition = 0.35) {
  const n = colors.length, cols = colors.map(hex), tot = bandWeights.reduce((a, b) => a + b, 0);
  const edges = [0]; bandWeights.forEach(b => edges.push(edges.at(-1) + b / tot * h));
  const out = new ImageData(w, h);
  for (let y = 0; y < h; y++) {
    let s = 0; while (s < n - 2 && y + 0.5 >= edges[s + 1]) s++;
    let f = (y + 0.5 - edges[s]) / (edges[s + 1] - edges[s]);
    f = Math.min(1, Math.max(0, (f - (0.5 - transition / 2)) / transition));
    for (let x = 0; x < w; x++) {
      const c = cols[f > BAYER4[y & 3][x & 3] ? s + 1 : s], i = (y * w + x) * 4;
      out.data.set([c[0], c[1], c[2], 255], i);
    }
  }
  return out;
}
const cv = document.querySelector('canvas');          // <canvas width=320 height=180 class="pixel">
const ctx = cv.getContext('2d'); ctx.imageSmoothingEnabled = false;
ctx.putImageData(ditherGradient(320, 180, ['#272744','#8b6d9c','#c69fa5','#f2d3ab'], [1,1.6,2.4]), 0, 0);
function fit() {                                       // integer scale to container
  const k = Math.max(1, Math.floor(cv.parentElement.clientWidth / cv.width));
  cv.style.width = cv.width * k + 'px'; cv.style.height = cv.height * k + 'px';
}
addEventListener('resize', fit); fit();
```
(The core algorithm was tested in Node with a plain `Uint8ClampedArray`: output contains exactly the 4 palette colours, first row = navy, last row = cream. `ImageData` wrapper not run in a browser.)

**Render loop with a sprite sheet and integer positions**
```js
function frameLoop(ts) {
  const f = Math.floor(ts / 160) % 4;                          // 160 ms per frame
  ctx.drawImage(sheet, f * 14, 0, 14, 8,  Math.round(x), Math.round(y), 14, 8);   // integers only
  requestAnimationFrame(frameLoop);
}
```
**Parallax at runtime (whole pixels, factors from §5.3)**
```js
const layers = [{img: far, k: .25}, {img: mid, k: .5}, {img: near, k: 1.0}];
function drawParallax(cameraX) {
  for (const L of layers) {
    const w = L.img.width, ox = -Math.round(cameraX * L.k) % w;     // round AFTER multiply
    for (let x = ox - w; x < cv.width; x += w) ctx.drawImage(L.img, x, 0);
  }
}
```
**Palette cycling (index buffer)**
```js
// idx: Uint8Array of palette indices, pal: array of [r,g,b]; cycle slots lo..hi one step per tick
function cycle(pal, lo, hi, t) { const seg = pal.slice(lo, hi + 1), n = seg.length;
  return pal.map((c, i) => (i >= lo && i <= hi) ? seg[(i - lo - t % n + n) % n] : c); }
```

### 6.4 Generating pixel art in Python — `/workspace/pixel_tools.py`
```python
from pixel_tools import *
sky   = dither_gradient(160, 90, ["#272744","#8b6d9c","#c69fa5","#f2d3ab"],
                        pattern="cross_sparse", progression=[1,1.6,2.4], transition=0.35)
upscale(sky, 4).save("sky.png")                       # integer nearest-neighbour
ramp  = make_ramp("#2e9bb0", steps=5)                 # hue-shifted dark->light hex list
q     = quantize(Image.open("ref.png"), "endesga32", dither="bayer4")   # snap to palette (no new colours)
print(lint(q, "endesga32", max_colors=32))            # AI-tell checker
```
Function map: `load_palette(name|file|hexlist)` · `make_ramp()` · `threshold_map(name)` (bayer2/4/8, checker, diamond, dashes, hlines, hlines_dots, cross, cross_sparse, noise) · `dither_gradient(w,h,colors,pattern,direction,progression,transition)` incl. `band` and `band_bridge` · `bayer_gradient()` · `quantize(img, palette, dither)` · `upscale(img,k)` · `sprite_sheet()` · `save_gif()` · `palette_cycle_frames()` · `scroll_wrap()` · `lint()` · `dither_study()` reproduces the 3×10 study sheet.
Built-in palettes: `endesga32 endesga64 resurrect64 apollo sweetie16 aap64 pico8 sunset_study`.
Python snapping rule: always `Image.NEAREST`; never `Image.LANCZOS/BILINEAR/BICUBIC`; never `img.convert("P")` with dithering on.

### 6.5 File & delivery conventions
- Folder per asset: `name@1x.png` (native), `name-sheet.png`, `name.json` (frames, ms), `palette.hex`, `NOTES.md` (light direction, palette, native size). Optionally `name@4x.png` for previews only.
- Deliver PNG (not lossy WebP/JPEG). Optimise losslessly only (e.g. `oxipng`); do **not** run `pngquant`/palette-reduction with dithering – it re-dithers and changes pixels.
- Add alt text; animated assets must have a reduced-motion fallback.

---

## 7. Recipes

### 7.1 Underwater / fish scene (runnable: `python3 /workspace/pixel_scene_demo.py` → `pixel_tools_demo/underwater.gif`, `underwater_f0.png`)
**Canvas**: 320×180 native (scales ×6 to 1920×1080); 8-frame ambient loop @ 120 ms.
**Palette (16–17 colours total)**: water `#0098dc #0069aa #00396d #0c2e44 #1a1932` · seabed `#0c2e44 #0b5e65 #0eaf9b` · kelp `#134c4c #1e6f50 #33984b #5ac54f` · fish `#571c27 #c64524 #e07438 #ffa214 #f9e6cf #131313`.
Steps:
1. **Water gradient**: 5 colours, vertical, bands thicker with depth (`progression=[1,1.4,2,2.8]`), Bayer-4 dither on the seams only (`transition=0.35`). Surface band thin + bright, a sparkle line of `#8fd3ff`-ish single pixels on the top row (animate 6-frame twinkle).
2. **God rays**: two diagonal shafts per 80 px, width grows with depth; lift each lit pixel **one ramp step** using a Bayer mask whose strength fades with depth (so rays are dithered, never alpha); drift ≤1 px/frame.
3. **Parallax layers back→front** (each filled to the bottom, edges seamless via sines with integer periods): far ridge (colours ≈ water band behind it, 2–3 colours, no detail), mid rocks (`#0b5e65 #134c4c #0c2e44`), near seabed (rim `#0eaf9b`, body `#0b5e65`, base `#0c2e44` with a checker bridge between body and base). Colour/value contrast increases toward the camera; saturation decreases for far.
4. **Caustics on the seabed**: 3 broken 1-px wavy lines in the lighter seabed tone (`#0eaf9b`), y = base + round(sin(2π(x/period − f/N + φ))), different periods/phases, never continuous.
5. **Kelp**: 1-px stems, 2-px wide leaf accents, 1–2 px sway with phase offset up the stem; highlight pixels `#5ac54f` on the lit (left) side, `#1e6f50` dark.
6. **Fish sprites** (14×8 clownfish): outline = sel-out dark red `#571c27` (no black), body ramp `#c64524 → #e07438 → #ffa214`, white stripe `#f9e6cf`, 1-px eye `#131313`; 3-pose tail (0,1,0,2) @ 160 ms, 2-px bob over 8 frames. Add 2–3 species at different scales **drawn natively at different sizes** (not scaled copies): small shoal fish 6–8 px (2 colours + eye), mid fish 14–20 px, a rare large 32–48 px silhouette in the far layer drawn paler. Swim paths in CSS/JS translate by integer px; slower far fish.
7. **Bubbles**: 1×1 and 2×2 clusters, rise 1 px/frame, horizontal drift ±1 every ~6 frames, fade by dithering to water colour at the top.
8. **Foreground**: dark narrow kelp/rocks along the bottom edge (`#0c2e44`/`#1a1932`, factor 1.2–1.5), never blocking the focal area.
9. **Palette check**: `lint(frame0, max_colors=48)` → 0 semi-transparent pixels; orphans in dithering/kelp are expected; run `lint` on sprites separately.
10. **QA**: 1x preview, 3× copy side by side for seams, grayscale squint (depth should read as dark/abyss at bottom/far, light at the surface), filmstrip of the loop.
Fish-site extras: coral = lobes with sel-out in `#891e2b`→`#f5555d`→`#f68187`; jellyfish = translucent *simulated* via dithered 50% checker (no alpha), pulsing 4 frames; bioluminescence = palette-cycle two accent entries (`#00cdf9`,`#94fdff`) in dark water; shallows version swaps to the warm depth ramp (§2.5).

### 7.2 Parallax background recipe (any theme; central site)
1. Canvas 480×270 (or 320×180). Layers (back→front): **sky** (static, banded + dither seams, 4–6 colours; sun/moon as separate sprite), **far** (mountains/skyline, 2–3 colours, no outlines, haze band at the foot), **mid** (hills/trees/buildings, 3–5 colours), **near** (silhouette with rim light, 4–6 colours), optional **foreground** (dark narrow strip, factor 1.2).
2. Factors: sky 0 · clouds 0.1 · far 0.25 · mid 0.5 · near 0.8 · fg 1.2 (CSS: `animation-duration ∝ 1/factor`; JS: `render_x = −round(camera_x × factor) mod width`).
3. Make each layer the same height as the canvas, filled to the bottom, left edge == right edge (verify with 3 copies side-by-side), landmarks every 1–2 screens, objects crossing the seam drawn twice.
4. Colour/distance rule (Pixeli): blend layers toward the sky colour ≈ 0/25/50/75/90% from nearest to farthest; −20–40% saturation per step; farthest layer 1–2 flat entries; slowest = palest = simplest. At sunset the far ramp is the warmest, saturated; near = cooler neutrals. [S6, S15]
5. Whole-pixel steps only; px/frame divides layer width; slower than 1 px/frame → repeat the image twice or use `steps()`.
6. Readability pass: every layer but the nearest gets ≈ −20% saturation, −15% contrast, +15% brightness. Backgrounds softer than the gameplay/content layer so UI text stays legible (add a darkest-colour panel behind text).
7. Clouds: lobes sharing a flat base; tints of the sky (within one ramp step), rim light on upper-left, no outline, no pillow rings; distant banks baked into the sky as dithered horizontal streaks (`hlines`). [S6]
8. Day/dusk/night variants = palette swaps of the same index map; don't repaint.

### 7.3 Sprite checklist (fish, creatures, icons)
Size first (e.g. 16×10 / 24×16 / 32×20) → silhouette (readable at 1x, squint) → flat base ramp fill → light direction shading with hue shift → sel-out → one or two highlight pixels (intentional orphans) → AA on long curves only → animation keys → lint → export sheet. Keep 3–4 colours per material; outline from the darkest ramp tone; eye = 1–2 px.

---

## 8. QA checklist (pixel boss runs this on every deliverable)
- [ ] Native resolution file is the source of truth; export upscales are integer nearest-neighbour only (`lint(..., assumed_scale=k)['clean_block_ratio'] == 1.0`).
- [ ] 0 semi-transparent pixels, 0 off-palette pixels, colour count ≤ budget (sprite ≤12, scene ≤32/48).
- [ ] Palette hex file saved next to the asset; ramps hue-shifted (shadows cool/purple, highlights warm/cyan).
- [ ] No pure black/white areas; darkest ≈ `#0e071b`–`#1a1932`.
- [ ] Gradients: uneven hard bands, dither only on seams, one dither phase per area, no wide (2×1) dither pixels, no noise gradients.
- [ ] Light direction consistent across sprites + layers; sel-out outlines; no pillow shading; no parallel banding seams; no doubles/jaggies; orphans only intentional.
- [ ] Squint/grayscale test passes (value structure + focal point).
- [ ] 1x check (AA/dither not too busy); view on light and dark page backgrounds.
- [ ] Animation: loop closes (frame N → frame 1), movement ≤1 px for ambient water, uneven timings, cluster structure stable, `prefers-reduced-motion` handled.
- [ ] Parallax: factors ordered, whole-pixel rates, seams invisible on 3 copies, layers filled to bottom.
- [ ] Web: `image-rendering: pixelated`, integer scale, `imageSmoothingEnabled=false`, integer draw coords, PNG, alt text.
- [ ] Never ship raw AI-generated art; if unavoidable as reference, redraw natively.

## 9. Team notes (central website & fish site bots)
- Share `palette.hex` (one master palette per site) and `pixel_tools.py` through the shared store; each bot may add themed ramps but must not add colours outside the agreed palette without pixel boss approval.
- Handoff format: native PNG(s) + sheet + JSON + NOTES.md (native size, scale used on the page, palette, light dir, frame ms).
- Integer `--scale` is set by the site CSS; art is delivered at 1x.

---

## Sources
- [S1] Slynyrd, Pixelblog 1 – Color Palettes (HSB ramps, hue shifting, saturation/brightness curves, Mondo palette): https://www.slynyrd.com/blog/2018/1/10/pixelblog-1-color-palettes
- [S2] the-pixel.art, Dithering in Pixel Art: What It Is, Bayer Patterns and When to Stop: https://the-pixel.art/articles/dithering/
- [S3] the-pixel.art, Pixel Art Banding, Clusters and Orphan Pixels: https://the-pixel.art/articles/pixel-art-clusters-orphan-pixels-banding/
- [S4] Plotcaster, Pixel art dithering: patterns, rules and tools (Bayer vs Floyd–Steinberg, hand-dither rules): https://www.plotcaster.com/learn/dithering-pixel-art/
- [S5] Pixeli rules 64 – Water (depth ramp, ripples, caustics, reflections, waterfall loops, measured saint11 tile): https://pixeli.pebbly.space/knowledge/rules/64-water
- [S6] Pixeli rules 60 – Skies and atmosphere (band progression, sky/sunset ramps, atmospheric perspective) https://pixeli.pebbly.space/knowledge/rules/60-skies-and-atmosphere ; rules 13 – Dithering and texture: https://pixeli.pebbly.space/knowledge/rules/13-dithering-and-texture
- [S7] Pixeli rules 11 – Clusters and noise (orphans, banding types, pillow shading, scatter): https://pixeli.pebbly.space/knowledge/rules/11-clusters-and-noise
- [S8] Pixeli rules 04 – Outlines and edges: https://pixeli.pebbly.space/knowledge/rules/04-outlines-and-edges ; pixelart.school, Pixel Art Terms (doubles, jaggies, over-AA, pillow shading): https://pixelart.school/learn/pixel-art-terms
- [S9] Pixor, What is selout? Selective outlines in pixel art: https://pixor.art/learn/selout/
- [S10] (same as S9, how-to-by-hand procedure)
- [S11] Pixeli rules 64 – Water, "Colour and depth" (red vanishes first, depth ramp).
- [S12] Technical considerations for using GenAI to make pixel art for games (sub-pixel bleeding, inconsistent pixel sizes, AA): https://coffeenwhiskers.hashnode.dev/my-issues-with-using-genai-to-make-pixel-art-for-games ; LoopSprite, How to Fix AI-Generated Pixel Art (soft edges, off-grid blocks, palette explosion, nearest-neighbour downscale): https://loopsprite.com/slice/guide-fix-ai-pixel-art ; Pixel Snapper (grid recovery): https://github.com/kyh/vibedgames/blob/main/plugins/asset-pipeline/skills/pixel-snapper/SKILL.md ; pixfix: https://github.com/lovelaced/pixfix
- [S13] Pixeli rules 05 – Animation (timing table, key poses, easing by spacing): https://pixeli.pebbly.space/knowledge/rules/05-animation
- [S14] Slynyrd, Pixelblog 52 – Idle Fighting Stance (8-frame idle, 100 ms/50 ms timing): https://www.slynyrd.com/blog/2024/9/26/pixelblog-52-idle-fighting-stance ; Pixeli rules 41 – Idle and breathing: https://pixeli.pebbly.space/knowledge/rules/41-idle-and-breathing
- [S15] Pixeli rules 62 – Parallax backgrounds (layer counts, factors, divisor loops, seams, colour/depth): https://pixeli.pebbly.space/knowledge/rules/62-parallax-backgrounds ; Slynyrd, Pixelblog 23 – Parallax Scrolling: https://www.slynyrd.com/blog/2019/11/12/pixelblog-23-parallax-scrolling
- [S16] Slynyrd, Pixelblog 11 – Landscape Pixeling: https://www.slynyrd.com/blog/2018/11/16/pixelblog-11-landscape-pixeling
- [S17] EffectGames, Q&A with Mark J. Ferrari (colour cycling explained): https://www.effectgames.com/effect/article-Q_A_with_Mark_J_Ferrari.html ; Old School Color Cycling with HTML5: https://www.effectgames.com/effect/article-Old_School_Color_Cycling_with_HTML5.html
- [S18] Palette Cycling: Retro with JavaScript Canvas: https://www.emergentmind.com/visualizations/palette-cycling ; Color cycling in pixel art: https://blog.prototypr.io/color-cycling-in-pixel-art-c8f20e61b4c4
- [S19] MDN, Crisp pixel art look with image-rendering: https://developer.mozilla.org/en-US/docs/Games/Techniques/Crisp_pixel_art_look ; image-rendering: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/image-rendering ; imageSmoothingEnabled: https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/imageSmoothingEnabled
- [S20] Codelamp, CSS spritesheet keyframe animation: https://blog.codelamp.co.uk/2016/05/07/keyframed-spritesheet-animation-in-css.html ; Engineered.at, Sprites on the Web: https://engineered.at/articles/sprites-on-the-web
- Palettes (hex lists): Lospec palette list – https://lospec.com/palette-list/endesga-32 · /endesga-64 · /resurrect-64 · /apollo · /sweetie-16 · /aap-64 · /pico-8 (append `.hex` for the raw list).
- Lospec dithering tutorials index: https://lospec.com/pixel-art-tutorials/tags/dithering
- Pixeli (aggregated pixel-art rules; itself cites saint11, Slynyrd, Gurney "Color and Light", Silber "Pixel Art for Game Developers"): https://pixeli.pebbly.space/knowledge/rules/
- User-supplied reference image: dithering/gradient study (2/3/4 colour × 10 dither styles, sunset palette `#272744 #8b6d9c #c69fa5 #f2d3ab`).
