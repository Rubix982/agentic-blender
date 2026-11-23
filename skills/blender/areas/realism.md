# Realism: what realistic Blender environments are made of, as settings a script can make

Blender 4.5.14 LTS. Tags: `[exp: path]` measured here, `[study: S5]` a published account by the artist of a
realistic Blender scene (17 of them, three contest winners, collected and checked in `kb/research/realism-breakdowns.md`
in the source repository). Experiments: `experiments/realism/` (atmosphere and light, material layers, the
photographic finish, scattering by density).

What the 17 have in common is mostly not a setting. 14 built from photographs of the real thing (10 from one specific
photo or place), 13 modelled the main objects themselves, and composition was discussed in 4 `[study: S1-S17]`. Those
are judgement, tested by matching a photograph (the next card in `CARD.md`). The settings below are the rest: every
technique at least 4 of the 17 used that a script can set. Each runs headless; each changed the render by the numbers
shown.

## What goes wrong most often

1. **A world volume for haze in a sunlit scene.** A Principled Volume of density 0.01 on the world's Volume output made
   every post read 0.0 in Cycles and in EEVEE: the sun and the world's light both cross infinite fog. Put fog in an
   object (a cube) or use the Mist pass. `[exp: experiments/realism/atmosphere_light.py]`
2. **A fog volume reaching high above the scene.** The same fog in a cube 150 m tall darkened everything in Cycles (a
   black post 5 m away read 0.0063 against 0.0475 with no fog): the sun crosses the whole cube before reaching the
   ground. A layer 20 m deep gave haze instead (0.0519 at 5 m rising to 0.2872 at 200 m, towards the sky's 0.5191).
   `[exp: experiments/realism/atmosphere_light.py]`
3. **EEVEE fog that stops at 100 m, and does not shadow the sun.** `scene.eevee.volumetric_end` is 100 m by default:
   the post at 200 m read 0.1662, barely above the one at 100 m (0.1626); with 400 m it read 0.1908. EEVEE does not dim
   the sun through a volume unless `use_volumetric_shadows` is on, so a tall cube read the same as a shallow one there.
   `[exp: experiments/realism/atmosphere_light.py]`
4. **Pointiness for edge wear in EEVEE, or with a guessed ramp.** EEVEE gives 0.5 everywhere (0.5
   median, 0.5 at the 99th percentile on the box). In Cycles the range on a bevelled,
   subdivided 1 m box was narrow: median 0.5029, 99th percentile 0.5142. Read the values
   on your mesh and set the ramp between them. `[exp: experiments/realism/material_layers.py]`
5. **Expecting EEVEE's Ambient Occlusion node to match Cycles'.** As a dirt mask (1 - AO, distance 0.3 m) it read
   0.177 on the floor beside the box in EEVEE against 0.349 in Cycles.
   `[exp: experiments/realism/material_layers.py]`
6. **Noise on default coordinates.** A Noise Texture with nothing in its Vector input uses Generated coordinates,
   stretched to each object's size: in the combined render the 1 m box got finer moss patches than the 4 m floor. Feed
   it Object coordinates or the Geometry node's Position for one real-world size. `[exp: experiments/realism/material_layers.py]`
7. **A new Glare node is Streaks.** Its registered default is Simple Star, but a new one starts as
   `STREAKS`; set `glare_type`. `[exp: experiments/realism/post_lens.py]`
8. **Chromatic aberration measured at the centre.** Lens Distortion's Dispersion is radial: at an edge 0.8 of the way
   across the frame, 0.05 put blue 0.51 px outside red, and 0.1 put it
   1.54 px; at the centre it moves nothing. `[exp: experiments/realism/post_lens.py]`
9. **Multiplying by a raw ellipse mask.** Ellipse Mask (0.95), blurred 60 px, multiplied in fully: the corners read
   0.0026 against 0.18 at the centre. At Fac 0.3 they read 0.1268. `[exp: experiments/realism/post_lens.py]`

## Light

HDRI lighting (11 of 17) and a sun placed on the HDRI's own (7 of 17 used a sun lamp or boosted the HDRI's)
`[study: S1-S17]`: `asset_import.world_from_hdri` and `asset_import.hdri_sun` with the rotation rule in
`light-world-camera.md`, measured in `remote-assets.md`.

**Colour temperature.** Two artists put a Blackbody node on every light (sun 5200 K at noon, 2250 K at sunrise, lamps
2500 K) `[study: S4, S14]`. 4.5 lights have it built in: `light.use_temperature = True; light.temperature = 2700`.
A white plate under an area light, rendered (linear RGB, and red over blue) `[exp: experiments/realism/atmosphere_light.py]`:

| Temperature | RGB | Red / blue |
|---|---|---|
| 2250 K | 7.9374, 2.5059, 0.2705 | 29.348 |
| 2700 K | 6.7725, 2.8123, 0.671 | 10.093 |
| 4000 K | 4.9492, 3.2326, 1.8678 | 2.65 |
| 5200 K | 4.1421, 3.3791, 2.8119 | 1.473 |
| 6500 K | 3.6488, 3.4441, 3.6233 | 1.007 |
| 9000 K | 3.1642, 3.4787, 4.7003 | 0.673 |

**Portals at windows** (all 3 interiors) `[study: S4, S15, S16]`. A closed 4 x 4 x 3 m room lit only through a 1 x 1
m window, Cycles at 16 samples, no denoising: the back wall's noise (standard deviation) fell from
0.0045 to 0.001 with an area light the window's size set as a portal
(`light.cycles.is_portal = True`), its mean unchanged (0.004); the render took
0.21 s against 0.05 s. `[exp: experiments/realism/atmosphere_light.py]`

**Shadows from things the camera cannot see** (a gobo plane, a row of trees) `[study: S6, S10]`. With
`obj.visible_camera = False` a red plate above the ground vanished from the frame and its shadow stayed, in Cycles
(the ground under it 0.022, open ground
0.487) and in EEVEE
(0.0 and
0.483). `[exp: experiments/realism/atmosphere_light.py]`

## Air

Fog, haze or atmosphere in 6 of 17: 3 with a volume in the render, the others faked (an emission atmosphere, fluid
mist baked to textures, fog cards, painted in, a Z-depth pass) `[study: S3, S6, S7, S8, S10, S12]`. Five identical
black posts at 5, 20, 50, 100 and 200 m, lit by a sun from behind the camera under a sky of brightness 0.5191; the
brightness of each post `[exp: experiments/realism/atmosphere_light.py]`:

| Fog | 5 m | 20 m | 50 m | 100 m | 200 m | Render |
|---|---|---|---|---|---|---|
| none | 0.0475 | 0.0472 | 0.0466 | 0.0469 | 0.047 | 0.14 s |
| Cycles: a fog cube 20 m deep, Principled Volume density 0.01 | 0.0519 | 0.086 | 0.1488 | 0.2165 | 0.2872 | 0.37 s |
| EEVEE: the same cube | 0.0573 | 0.08 | 0.1195 | 0.1626 | 0.1662 | 0.28 s |
| EEVEE: the same, `use_volumetric_shadows` | 0.0572 | 0.0788 | 0.1126 | 0.1441 | 0.147 | 0.33 s |
| EEVEE: the same, `volumetric_end` 400 m | 0.0566 | 0.0777 | 0.1171 | 0.1616 | 0.1908 | 0.31 s |
| Cycles: the cube 150 m tall (the sun crosses it) | 0.0063 | 0.0096 | 0.0161 | 0.0218 | 0.0291 | 0.39 s |
| Cycles: a world volume, density 0.01 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.3 s |
| EEVEE: a world volume, density 0.01 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.14 s |
| the Mist pass (linear, 0 to 200 m) mixing to the sky colour in the compositor | 0.06 | 0.0961 | 0.1683 | 0.2918 | 0.5432 | 0.13 s |

The Mist pass is a factor of distance alone (0 to 1, set by `world.mist_settings`) `[inv]`, so it cannot brighten round
the sun or make shafts of light as a volume can; it was also the quickest fog here.

```python
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 300, 10))
fog = bpy.context.object
fog.scale = (1200, 1200, 20)                                      # a layer 20 m deep, wider than the view
mat = bpy.data.materials.new("Fog"); mat.use_nodes = True
nt = mat.node_tree; nt.nodes.clear()
vol = nt.nodes.new("ShaderNodeVolumePrincipled"); vol.inputs["Density"].default_value = 0.01
nt.links.new(vol.outputs["Volume"], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Volume"])
fog.data.materials.append(mat)
scene.eevee.volumetric_end = 400                                  # EEVEE: past the farthest thing in view
```

## Surfaces

Two or more materials blended through noise, masks or vertex paint in 10 of 17; weathering (dirt, dust, fingerprints,
leaks, rust, moss) in 6 `[study: S1-S17]`. Each mask below was rendered on its own as an emission shader on a 1 m
bevelled box resting on a floor, so a pixel's value is the mask's; the values read at points of the scene
`[exp: experiments/realism/material_layers.py]`:

| Mask | Floor beside the box | Floor far off | Box top | Box front, upper | Box front, lower | Floor left, right |
|---|---|---|---|---|---|---|
| Noise (Object coordinates, scale 4) through a constant ColorRamp at 0.4 / 0.5 / 0.6: share of the frame above 0.5 | 0.884 / 0.481 / 0.111 | | | | | |
| 1 - Ambient Occlusion (distance 0.3 m), Cycles | 0.349 | 0.0 | 0.0 | 0.0 | 0.205 | |
| 1 - Ambient Occlusion, EEVEE | 0.177 | 0.014 | 0.013 | 0.005 | 0.026 | |
| Facing up: Geometry Normal Z through a ColorRamp 0.7 to 0.9 | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 | |
| Height: Geometry Position Z through a ColorRamp 0.45 to 0.55 m | 0.0 | 0.0 | 1.0 | 1.0 | 0.0 | |
| A painted colour attribute, Cycles and EEVEE | | | | | | 1.0, 0.0 and 1.0, 0.0 |

Pointiness, for worn edges, is Cycles only: through a ColorRamp from just above its median to its 99th percentile it
marked 0.0775 of the box's pixels, along the edges; in EEVEE it marked
0.0. `[exp: experiments/realism/material_layers.py]`

```python
nodes, links = mat.node_tree.nodes, mat.node_tree.links

def ramp(src, lo, hi):                      # a mask from any value
    r = nodes.new("ShaderNodeValToRGB")
    r.color_ramp.elements[0].position, r.color_ramp.elements[1].position = lo, hi
    links.new(src, r.inputs["Fac"]); return r.outputs["Color"]

ao = nodes.new("ShaderNodeAmbientOcclusion"); ao.inputs["Distance"].default_value = 0.3   # dirt where things meet
geo = nodes.new("ShaderNodeNewGeometry")
up = nodes.new("ShaderNodeSeparateXYZ"); links.new(geo.outputs["Normal"], up.inputs["Vector"])
moss = ramp(up.outputs["Z"], 0.7, 0.9)                                 # on what faces the sky
mix = nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"               # layer B over A where the mask is 1
links.new(moss, mix.inputs["Factor"])
```

A combined render (stone, dirt from AO, worn edges from pointiness, moss from facing-up times noise) is
`experiments/realism/results/material_layers-layered.png`. Procedural main surfaces (5 of 17) and displacement (4 of
17) `[study: S1-S17]` are in `materials.md`.

## Scattering by painted density

4 of 17 painted where things grow (weight or vertex groups) `[study: S4, S6, S9, S10]`. A vertex group read in
Geometry Nodes with a Named Attribute node drives Distribute Points on Faces. On a 10 x 10 m grid weighted 1.0 on its
left half and 0.25 on its right `[exp: experiments/realism/scatter_density.py]`:

| Method | Points | Left | Right | Left / right | Closest pair |
|---|---|---|---|---|---|
| Random, Density = 20 x weight | 1237 | 977 | 260 | 3.758 | 0.0156 m |
| Poisson disk, Density Max 20, Distance Min 0.15 m, Density Factor = weight | 821 | 650 | 171 | 3.801 | 0.1506 m |

Poisson disk kept every pair at least 0.15 m apart, as asked; random let two land 0.0156 m
apart. Instance on Points put 1237 instances on the 1237 random points.
`[exp: experiments/realism/scatter_density.py]` Hand placement (4 of 17) and add-on scatter tools (Geo-Scatter 3, botaniq 3, Graswald 2)
`[study: S1-S17]` are the other routes.

## The photographic finish

9 of 17 graded or composited in another program; grain and glow in 4 each, chromatic aberration in 3, vignette in 2,
lens distortion in none, and one artist chose not to add "lots of chromatic aberration" `[study: S4, S5, S6, S9, S12]`.
Blender's compositor does each headless `[exp: experiments/realism/post_lens.py]`:

| Effect | Measured |
|---|---|
| Glare, Bloom (threshold 1): luminance 4, 8, 16, 32 px from a bright dot | 0.5533, 0.1694, 0.0581, 0.0295 (no glare: 0.02 throughout) |
| Glare, Fog Glow | 0.7158, 0.1891, 0.0506, 0.0228 |
| Lens Distortion, Dispersion 0.02 / 0.05 / 0.1: blue outside red at an edge 0.8 across | 0.24 / 0.51 / 1.54 px |
| Vignette (Ellipse Mask 0.95, Blur 60 px, Multiply), Fac 1 / 0.3: corner against centre 0.18 | 0.0026 / 0.1268 |
| Grain (Texture node with a Noise texture, Overlay at 0.15) on flat 0.18 grey | standard deviation 0.01112, mean 0.1597; frames 1 and 2 correlate 0.01: a new pattern every frame |
| Grade (Color Balance, gain colour 1.1, 1.0, 0.9) | red / blue 1.5373 from 1.0 |

The grade moved red over blue further than 1.1 / 0.9 = 1.22 would suggest: Lift/Gamma/Gain does not scale linear
values by the gain. Read the result back rather than predicting it. `[exp: experiments/realism/post_lens.py]`

## What the settings leave to judgement

Everything above can be set from a script and checked by numbers. What the 17 did that it does not cover: working
from photographs of a real place (14), modelling the main objects (13), composition in layers of foreground, middle
and background (4), and deciding where imperfection belongs ("fingerprints on the glass where someone would actually
hold the glass") `[study: S4, S13, S17]`. Whether an agent can make those choices is the photo match's question.
