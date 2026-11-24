# Production: how studio films and contest entries made in Blender are built, as steps a script can take

Blender 4.5.14 LTS. Tags:
- `[study: A-01]` is a source in `kb/research/competitions-study.md` in the source repository: 49 written accounts
  from 2014 to 2026, 36 of them from 2021 onward. Part A is Blender Studio's open movies and other films made in
  Blender. Part B is the Suzanne Awards, Pwnisher's challenges and character work. Part C is still-image contests,
  Best of Blender Artists and featured work. The two-digit source numbers are unrelated to the three-digit cards
  (C-005) in `CARD.md`.
- `[inv]` is a name read from Blender 4.5's own inventory (`kb.py`).
- `[exp: path]` is measured on this machine.

The sources describe procedures and judgement much more often than values. Only 8 of the 49 give a sample count, 7
name a denoiser and 7 a view transform `[study: analysis 0]`. So this page gives the order to work in and what to spend effort on, and the
values come from the other pages it points to.

## What the sources say decides a contest

Three pages of jury comments survive `[study: C-04, C-05, C-15]`. In all three, the stated reasons for winning were:
- the story or concept;
- the mood and atmosphere;
- a limited, controlled palette;
- the subject separated from its background;
- a silhouette that reads.

The faults that held entries back were technical: noise, "wonky deformations" on a character, flat water, rough
shadows. One entry was "Technical wise ... almost perfect" and did not place, because it had no story (C-05). Read
together, the comments suggest technique works as a floor. Noise or bad deformation can lose an entry, and clean
technique does not win one by itself. This rests on three pages, so it is a pattern in judges' words, not a measured
effect `[study: C-04, C-05, C-15]`.

Placed artists describe spending effort on the subject and cutting corners elsewhere `[study: B-10, B-12, C-11, C-03]`:
- "everything serves the main character", with a background built from cubes and a texture collage in under half a day;
- the look settled in the render, so that only 2–3 passes were needed and the time went to animation;
- only the first quarter of a race track modelled;
- only the exposed organic parts sculpted, with procedural materials on the rest.

For an agent this means three things:
- Name the subject, and what it must read as, before building anything.
- Spend the detail there.
- Before showing a render, check it for the faults the juries named: noise, broken deformation, and a subject that
  does not separate from its background.

The guide's own first shot failed the last check. Its boulder sat behind the plants scattered around it
(`CARD.md`, C-005).

## The procedures, in order

Each procedure is what the sources listed with it have in common. Steps no source stated are not filled in.

### P1. Camera first, then light, then detail only what the camera sees (12 sources)

1. Block out with primitives, and place and lock the camera (lens, height, framing) before modelling detail
   `[study: C-19, C-21, B-01]`. A headless agent sees through test renders, so render the blockout at once: Workbench,
   or Cycles at 16 samples at quarter resolution.
2. Put in the key light and the environment next, and render again `[study: C-19, C-21]`. With a scanned sky this is
   two calls (`remote-assets.md`): `asset_import.world_from_hdri` and `asset_import.hdri_sun`, the second giving a sun
   that agrees with the photograph.
3. Model and detail only what the camera sees `[study: C-07, C-11, B-04, C-21]`. In Cycles, objects outside the view
   can be dropped from a scatter with `scene.cycles.use_camera_cull = True` and `obj.cycles.use_camera_cull = True`
   on the scattered object `[inv]`.
4. For animation, block out the motion too, as an animated blockout `[study: B-05, C-13]` or a rough set explored
   with a virtual camera `[study: A-07]`.

### P2. Split the render, write EXR, rebalance and grade afterwards (9 sources split; 7 write EXR)

1. Split the scene into view layers by depth or role. B-08 used foreground, foreground effects, midground,
   background and atmosphere. C-21 used ground, background, hero object, ships and fog. `[study: B-08, C-21]`
2. Give each main light its own Light Group so it can be turned up or down after the render: add one with
   `view_layer.lightgroups.add(name="key")`, then set `light_object.lightgroup = "key"` `[inv]`
   `[study: B-05, B-12]`. For masks, turn on Cryptomatte with `view_layer.use_pass_cryptomatte_object = True` `[inv]`
   `[study: A-15, B-03, B-09]`.
3. Write multilayer EXR (`compositing.md`). Then rebalance, add glow, grain and vignette, and grade last. This was
   done in Blender's compositor `[study: B-03, B-05]` or outside it.

The alternative is to settle the look in the render and write only 2–3 passes `[study: B-12, A-10, A-07]`. In EEVEE
this is the safer choice. Its passes lack the Combined pass's sample refinement, so the Combined pass cannot be
rebuilt from them `[study: A-10]`.

### P3. Fog, light shafts or a large effect from a cube with a volume shader (6 name it; 11 use volumetrics)

1. Add a cube around the region that needs atmosphere. It can cover the scene `[study: B-03, C-21]`, cover only a
   window and be stretched along the sun's direction `[study: C-20]`, or be aligned to the sun as a light shaft
   `[study: A-02]`.
2. Give it a volume shader, with its density shaped by a noise texture through a ramp. A-02 multiplied the result by
   0.070 `[study: A-02]`.
3. Keep the cube shallow in a sunlit scene. A 150 m cube darkened everything, and a world volume blacked it out; the
   measured numbers are in `realism.md` (items 1–3). EEVEE's fog also stops at `scene.eevee.volumetric_end`, which
   is 100 m by default `[exp: experiments/realism/atmosphere_light.py]`.

### P4. Scatter vegetation or clutter, then keep it light (9 sources)

1. Bring in assets: scanned ones (`remote-assets.md`), or a scatter add-on's library in the sources.
2. Scatter by a painted density: Geometry Nodes' Distribute Points on Faces, with the density read from a named
   attribute (`realism.md`, scattering by density).
3. Instance, never copy `[study: C-21, B-02, B-03]`. A Poly Haven plant is often a set of variants in one file. Pick
   among them with Collection Info (Separate Children, Reset Children) and Pick Instance (`instancing-assets.md` item 6,
   `geometry-nodes.md` item 8).
4. Cap the cost. Turn on `scene.render.use_simplify` and set `scene.cycles.texture_limit_render = "2048"` `[inv]`. C-01
   wrote that 2k "will do just fine most of the time". Use low-resolution meshes in the background `[study: C-01]`, and
   decimate small repeated objects. B-02 took raindrops from 80 faces to 12, which "looked quite bad as a still
   object, but you can't see that once it's all in movement" `[study: B-02]`.
5. Close the view behind the scatter with a photograph on a plane `[study: C-10]`.

### P5. Animate: key poses first, then in-betweens, then the camera, then polish (7 sources)

1. Key the main poses with Constant interpolation, so the timing reads without in-betweens `[study: B-10, A-04]`.
   From Python: `for k in fcurve.keyframe_points: k.interpolation = "CONSTANT"`. Switch to `"BEZIER"` when the timing
   is approved. A-04 starts lighting from this pass: "We can start lighting a shot as soon as there is a first blocking
   pass available".
2. Add in-betweens, anticipation and transitions `[study: B-10, B-15]`. Animate secondary characters to the main one's
   rhythm, first as stand-ins `[study: B-10]`.
3. Adjust the camera after the first animation pass, so it answers the action `[study: A-07, B-15]`.
4. Polish secondary motion (tails, earrings, fingers) and contact with the ground, and remove intersections
   `[study: A-04]`.
5. Check before delivery: the frame rate, the linked assets, and motion blur on the first and last frames and at
   parent switches `[study: A-04]`. Motion blur samples between frames, so a constraint switch keyed with Bezier
   interpolation streaks. Key such switches with Constant interpolation, and check a sub-frame with
   `scene.frame_set(f, subframe=0.5)`.

For shots too long to check frame by frame, Flow's animators worked from written behaviour rules per character, such
as ears turning to sounds and the tail moving on its own `[study: A-07]`.

### P6. One light rig per sequence, checked across shots (4 sources)

1. Make one World per sequence for the base tint, and a rig of lights linked into every shot of that sequence
   `[study: A-09, A-10]`. Linking is in `data-model.md`.
2. Reduce the lights to a few roles with stored values. A-04 used key, key-soft, fill and rim, with the colours in a
   linked node group so a change reaches every shot `[study: A-04]`.
3. Light the wide shot first and derive the close-ups from it `[study: A-04]`.
4. Check continuity on a contact sheet of every shot `[study: A-03]`. `shots/morning-clearing/finish.py` makes one
   from a frame sequence.

### P7. Fake an effect instead of simulating it (4 sources, all 2024–2025)

1. Decide what the effect must read as on screen. B-01: "a big dark silhouette, so it didn't need a lot of detail".
2. Build it from a shader or Geometry Nodes. B-01 made a tornado from a volume cube with its density shaped into a
   cone. B-03 moved bricks with a Geometry Nodes effector sphere. B-10 made an explosion from a scaled sphere rendered
   with motion blur `[study: B-01, B-03, B-10]`.
3. Animate one or two values instead of running a simulation: the effector's radius, the noise offset, the scale.

The reasons given: it can be changed without re-running a simulation `[study: B-03]`, and it is faster
`[study: B-01]`.

### P8. Scan it yourself (4 sources)

The sources photographed props, buildings and their own heads with a phone (KIRI Engine, Scaniverse), then cleaned
the mesh in Blender `[study: B-01, B-02, B-11]`. A headless agent cannot do this. The free scanned assets in
`remote-assets.md` stand in for it.

### P9. Simulate, bake to a cache, then render (3 sources; 3 more bring simulations from Houdini)

Bake before rendering, so every render plays the same cached frames `[study: B-02, B-07, A-07]`. Baking headless is
in `simulation.md`.

## Tricks a beginner would not think of, with the 4.5 setting

| Trick | In Blender 4.5 | Source |
|---|---|---|
| Shadow casters the camera cannot see (a gobo, a row of trees) | `obj.visible_camera = False`; also `obj.visible_diffuse = False` so it casts no bounce light `[inv]` | A-03 |
| Darken the corners with blockers in the scene, not a post vignette, which "can look fake in the highlights" | the same visibility switches on planes near the camera | A-02 |
| A background only the camera sees, while the HDRI lights the scene | in the World, mix two backgrounds by the Light Path node's `Is Camera Ray` output `[inv]` | A-02 |
| A hair light that adds only highlights | the light's `visible_diffuse = False` | A-02 |
| A light only at the window, as a volume cube stretched along the sun, not volume through the whole room | P3, with the cube scaled along the sun's direction | C-20 |
| Never rotate furniture by exactly 90° or 180° | for example 93.32° or 175.4°; a random jitter of a few degrees in a script | C-17 |
| One light at the camera, for photo-like character realism | a spot or area light with the camera's transform: `light_obj.matrix_world = cam.matrix_world.copy()` | C-17 |
| Smooth reflections on cut-up panels | model a smooth guide surface; Shrinkwrap modifier onto it | C-07 |
| The colour map reused as a bump map, on top of the normal map | the image's Color into a Bump node's Height | C-12 |
| Repeated slats that do not repeat their texture | Array modifier with `offset_u` / `offset_v` set `[inv]` | C-10 |
| Objects dropped into place | rigid bodies on a passive floor, bake (`simulation.md`), then `bpy.ops.object.visual_transform_apply()` on the settled frame `[inv]` | C-08 |
| Subsurface shown by a light behind the subject, the rest kept dark | an Emission shader driven by the Light Falloff node's `Quadratic` output `[inv]` | C-08 |
| Film grain and colour fringing in the compositor | Lens Distortion: in 4.5 `Jitter` and `Fit` are input sockets (the `use_jitter` property is deprecated) `[inv]`; C-06 mixed the jittered image back at 0.333 and used Dispersion about 0.02 with Fit on; the guide's measured grain is in `realism.md` | C-06 |
| A whole growth played by one value | `mesh.shape_keys.use_relative = False`, then animate `mesh.shape_keys.eval_time` `[inv]` | B-07 |
| Objects carried by deforming water | Surface Deform: turn the water's deformation off, `bpy.ops.object.surfacedeform_bind(modifier=...)` `[inv]`, then back on | B-07 |
| Screen textures (paper, canvas) that stay on moving objects | put them in the material, not the compositor | A-08 |
| Viewport speed without changing the render | Geometry Nodes' Is Viewport node `[inv]` switches between merged geometry and instances; B-03 went from 27,000 objects at 10–12 fps to 6 objects at 60 fps | B-03 |
| Room for shake and lens distortion in compositing | B-08 rendered 10 % overscan. Blender has no output overscan (EEVEE's `use_overscan` is for screen-space effects); raise the resolution and the camera's sensor width by the same factor. Not measured here | B-08 |
| A fault hidden behind staging | time something across the frame where the fault is, as B-02 did with a passing car | B-02 |

## Keeping an animation steady

Only 4 of the 49 sources discuss flicker, and only A-01 in depth. What they report `[study: A-01, A-08, A-12, C-02]`:
1. Low-sample denoising flickers in animation, because the denoiser invents different detail on each frame. Raising
   the samples six times did not remove it in A-01.
2. A fixed seed helps only while the camera is still. With a moving camera the fixed noise pattern slides across the
   picture.
3. Temporal denoising came from outside Blender in these sources (C-02 used multi-frame denoisers in post).
4. Vegetation with translucency, moving moss, and volumes flicker most. Blender Studio avoided moving foliage in day
   shots for this reason.
5. Anything procedural must stick to the surface. A paper texture went in the shader, not the compositor (A-08), and
   brushstrokes on a deforming mesh need a rest position (A-12) `[study: A-08, A-12]`.

This machine measured the first three on a moving forest shot (card C-006; `animation-video.md`, "Flicker in a
moving shot"). At 128 samples with OpenImageDenoise the noise was 2.5 % of the flicker and the rest was motion; only
samples lowered it; an animated seed raised it by 21 %; and `bpy.ops.cycles.denoise_animation` was not temporal with
OpenImageDenoise. `[exp: experiments/animation/flicker.py]`

Other consistency practice:
- In EEVEE, light probes are baked per shot, and a baked probe cannot be shared between scenes `[study: A-10]`.
- A cached simulation plays back the same each time `[study: B-02]`.

## What a frame costs in practice

| Where | Time per frame | Source (`[study: ID]`, or this repository's card) |
|---|---|---|
| EEVEE, 4K or HD, studio and feature film | 0.5–10 s (Flow), about 3 min median (Charge) | A-07, A-06 |
| Cycles, one consumer GPU, contest entries | about 5 min at 450 samples; about 10 min on an RTX 4090; up to 1 h unoptimised | B-03, C-12, B-12 |
| Cycles, CPU farms, before 2018 | hours; over 100 h for some frames until a fix for motion-blurred hair | A-14, A-05 |
| Cycles on this laptop (M2 Pro, Metal), 1280 x 720, 128 samples, a scattered forest with fog | 22.6 s (240 frames in 1.5 h; peak 3.6 GB) | C-005, `shots/morning-clearing/results.json` |

Several solo entrants moved to a render farm days before their deadline `[study: B-07, B-11, B-12]`.

## Rebuilding a pierced object from one photograph

Cards C-007 to C-011 rebuilt a carved red-sandstone window screen (a jali) from one frontal museum photograph, by
script: its openings traced from the photo, the trace extruded, lit to the photo, and rendered from the photo's camera
(`shots/jali-match/`; `make.py` runs it). Each was judged beside the photo. C-007, a flat slab with holes: "very
surreal", "something plain but it is not", "a darker muddier look". C-008, with the photo's dark lines cut as grooves
into rounded bars: "little incisions across the model, but they don't capture the symmetrical alignment and
pertuberance". C-009, its motif averaged over its own repeats and heights read from the shading: "vastly improved even
further", though not taken for the photo. C-011, with a learned normal map of the photo and its own weathering: "At a
glance, yes, it seems like, it would become better if we worked on the lighting part" (the user's words, CARD.md).
What the builds found, in the order a script meets it:

1. **Find the openings by a property that holds across the whole photo.** Light on a backdrop falls off: here the
   wall behind the screen was white at the bottom and dim and warm at the top. Saturation below 0.22 with luminance
   at least 0.30 found 3.5 % openings in the top half; green over red above 0.86 found 10.9 %, because the stone is red
   at every brightness and the wall is not. Check a rule in bands from top to bottom before trusting it. Where the wall
   was dim and warm the cut still missed it, so a second rule joins it: smooth, and close
   to the wall's colour where it is, a field estimated from the pixels the cut is sure of (12.6 % in the top half). In a
   render, where stone is smooth everywhere, that rule also needs green over red above 0.80, or it takes the stone.
   `[exp: shots/jali-match/read_photo.py]`
2. **Dark pixels inside the object are its own shadows, until their colour says otherwise.** The dark pixels in the
   carved field (5.6 % of it) had green over red of 0.355 at the median and 0.469 at the 90th percentile: stone in
   shadow, not wall. Trace them as solid; only dark pixels connected to the photo's edge are the surround, and only
   if they are neutral too: once the light pooled in the centre, the frame's corners were dark enough to be cut away
   with the surround, and the glowing wall showed through them. Counting a dark pixel as surround only if its green
   over red is above 0.8 (or it is too dark to tell) took the surround cut from the box from 38321 px to 17270.
   `[exp: shots/jali-match/read_photo.py]` `[exp: shots/jali-match/build.py]`
3. **What a photo shows through an opening is already narrowed by the depth.** The camera sees the hole's front
   outline overlapping its back outline, and the back appears scaled towards the picture's centre by
   distance / (distance + thickness): 0.9546 for 6.1 cm at 1.28 m. Extrude the seen region and every hole narrows
   twice. For straight-through holes the front outline holds both the seen region and the seen region scaled back
   out, so trace their union. At the catalogue's 6.1 cm this widened too far here (it took in a whole carved flower),
   and the openings agreed better the thinner the field was assumed; either the pierced field is thinner than the
   whole screen or its holes splay. C-008 took 20 mm (CARD.md has the sweep). `[exp: shots/jali-match/build.py]`
4. **Trace into a 2D curve with `offset` 0** and shrink the shape before tracing instead: a negative offset grows the
   holes into each other and the fill turns inside out (`curves-text.md`, item 8). Set `use_smooth` on every spline;
   flat facets on the holes' inner walls read as stripes. `[exp: experiments/curves/curve_offset_fill.py]`
5. **Size a backdrop for its depth.** A panel the object's size, 0.4 m behind it, appeared 0.7486 of the object's size
   from the camera, and the top and bottom openings looked past it into black. Scale it up by
   (distance to the panel) / (distance to the object). `[exp: shots/jali-match/build.py]`
6. **Set a glowing backdrop from the photo; do not fit it.** Seen straight through the openings and only emitting, its
   colour on screen is its emission through the sRGB curve. Decode the photo's openings' median colour in bands from
   top to bottom into a colour ramp on the panel (each row looks onto the panel at its own height over the panel's
   scale): the openings' median luminance came out 0.6803 against the photo's 0.6856. A two-number fit, which counted
   the dim backdrop out at the photo's brightness threshold, dimmed it each round instead.
   `[exp: shots/jali-match/compare.py]`
7. **Cut lines are not carving.** Tracing the photo's thin dark lines and cutting them as grooves into bars rounded by
   distance from the openings found the shadowed sides of shapes in pieces: 57 % of the render's lines lay within 2 px
   of the photo's and 39 % of the photo's within 2 px of the render's, and the judge saw scattered incisions with
   neither the motifs' symmetry nor their raised forms. Letting each piece between lines rise on its own was worse:
   the stone read as crumbled rock. `[exp: shots/jali-match/compare.py]`
8. **Average the object's own repeats: the near ones only, each registered.** A carved lattice repeats. The peaks of
   its openings' autocorrelation gave two repeat vectors, (141.06, -177.12) and (146.15, 173.27) px, and the best
   match with its own mirror image put the axis at x = 613 (correlation 0.3596). Averaging the photo over its copies
   takes out noise and the light's slow change, but copies far apart differ (the light, the depth narrowing the
   openings, a fraction of a pixel of error in the vectors growing at every step): registered against the average,
   copies one step away agree at a median 0.6436, two steps 0.4947, three 0.4665, and farther ones less. Average
   only up to three steps, with the mirror half, and register each copy to the reference pixel by pixel within 3 px,
   weighted by how well it matched; unregistered, 37 copies a few pixels apart blurred and ghosted the motif. Keep the
   openings the photo's own: the averaged openings smoothed each repeat's edges and, in the arch at the top, mixed in
   copies that do not belong. `[exp: shots/jali-match/symmetry.py]`
9. **Solve the heights from the shading; do not sum them down each column.** Lit from above, a surface brighter than
   its surroundings faces up, so the averaged shading is the height's up-down slope. Summed down each column, every
   error ran on to the column's end as a streak. Solved by least squares over the whole field (conjugate gradients,
   290 iterations), the streaks went. Then scale them: about 4 mm at the 99th percentile, clipped at one and a half
   times that, read as raised forms; higher and unclipped, they read as melted. Even so the forms come out soft: a
   slope summed into a height rounds every carved step. `[exp: shots/jali-match/symmetry.py]`
10. **Do not shrink the solid to make room for the bevel.** A one-pixel shrink, so the half-millimetre bevel would not
    widen the stone, took most of the photo's thin connecting strips (4 px wide or less), which the user saw as missing
    pieces. Without it, 89 % of the thin stone shows in the render (0.8949). `[exp: shots/jali-match/compare.py]`
11. **Keep every layer inside the outline, smooth the outline, and soften the render as the lens did.** The user saw
    rough edges, and there were three causes at once. A carved skin, built from the stone mask after a closing that
    bridged every narrow opening, stood past the outline with its pixel steps. The outline followed the mask's pixel
    noise. And the render's edges were crisper than the photo's. Fill only the holes the stone nearly closes over,
    keep the skin 2 px inside the stone with its relief faded out towards its edge, smooth the outline without
    shrinking it (Taubin smoothing), and widen Cycles' pixel filter to 1.8 px with `scene.cycles.filter_width` (Cycles
    ignores `render.filter_size`; `rendering.md`): the openings' edge gradient came out 1.038 times the photo's.
    `[exp: shots/jali-match/build.py]` `[exp: shots/jali-match/compare.py]`
12. **Lit edges are stone, however pale.** Lit sandstone washes towards cream and passed item 1's cut as wall: the user
    saw a bar's lit edge rendered as a gap. Wall pixels sit near the local wall's brightness: of those the cut was sure
    of, the middle half lie between 0.982 and 1.045 of the local wall's luminance, and the top tenth above 1.275. A
    pixel more than 12 % plus 0.03 above the local wall is now stone. That took 9.57 % of what the cut had called
    opening, 17.45 % in the top half, where the light catches the bars' upper edges against a dim wall, and 1.95 % in
    the bottom. Rebuilding from it, the trace broke Blender's fill at metre scale (`curves-text.md`, item 9).
    `[exp: shots/jali-match/read_photo.py]`
13. **Stone can also be darker than the wall behind it.** At the bottom of this photo the wall was lit almost white,
    and the pale, greyish stone in front of it passed the colour cut as wall; the user saw the bottom row's arches
    missing. A pixel more than 15 % below the local wall's luminance, less 0.03, is stone too: that took 10.86 % of
    what the rule had called opening, 0.32 %, 2.25 % and 28.84 % by thirds from the top. Test a pale-backdrop rule
    both ways. `[exp: shots/jali-match/read_photo.py]`
14. **A learned normal map gives the carving that one photo's shading cannot.** Marigold normals v1.1
    (`prs-eth/marigold-normals-v1-1`, CreativeML OpenRAIL++-M, through `diffusers`; it needs PyTorch, so it runs in its
    own Python environment, not Blender's, and hands the build an `.npy`). On overlapping 768 px tiles of the photo
    at the working size 1230 x 1402, so nothing is shrunk to fit one pass, with ensembles of three and the model's
    four steps: 8.3 s a tile on this laptop's GPU, 53.4 s for the six, and tiles disagree by a median 6.22 degrees
    where they overlap. Its frame (x right, y up, z towards the viewer) is the object's own when the object faces the
    camera. Plain weathered stone comes out flat (item 17). `[exp: shots/jali-match/normals.py]`
15. **Use the normals as normals; integrate them only for the shadows.** Integrated into heights by least squares,
    they came out as broad bulges about a hundred pixels across, slope errors summed over the wide stone: a 99th
    percentile of 0.0148 m, and scaled down to fit, the carving went flat (the forms band 0.2797, under the shading
    method's 0.3986). Screened (each height also pulled to 0 with weight 1 / 30 px squared), 0.00885 m and 0.3796:
    the solve and the relief's fade at the edges still took the carving. As the front's object-space normal map, used
    only where the surface faces the camera, with the screened heights kept for the forms' shadows: 0.5487, where the
    photo against itself 2 px off scores 0.5571. `[exp: shots/jali-match/build.py]` `[exp: shots/jali-match/compare.py]`
16. **Re-fit the depth whenever the rule that reads the photo changes.** The same rule reads the render, and with item
    13 it counted the darkened inner walls of every hole as stone, as they are; the thickness fitted under the old rule
    left the render's openings too small. Swept again at 0.010, 0.015, 0.020 and 0.025 m: openings IoU 0.7596, 0.7501,
    0.7354, 0.715. `[exp: shots/jali-match/build.py]` `[exp: shots/jali-match/compare.py]`
17. **Weathering the model smoothed away: tilt its normals by the photo's own light and dark.** On the plain frame the
    normals were flat, and the render's fine texture there was 0.2594 of the photo's. A bump from the photo's light and
    dark (dark as low) gave texture in the wrong place: a bump's shading follows its slope, not its height, so each
    feature's light and dark land half a feature off (the fine band's correlation -0.1973, the forms band 0.485 from
    0.5481). Tilting each normal towards the light from above by A x the photo's band puts them in place: at A = 2, 4,
    8 and 12 the frame's fine texture came to 0.358, 0.5521, 0.9389 and 1.2504 of the photo's. Where the normals carry
    carving, the fine band at 0.3 of A: at full strength the photo's pale specks read as crust. From here the detail
    measure partly measures the photo against itself. `[exp: shots/jali-match/build.py]`
    `[exp: shots/jali-match/compare.py]`
18. **Check the fill after every build.** A traced curve's fill can fail on one small outline, at any scale
    (`curves-text.md`, item 9); `build.py` halves the outlines to find it and swaps in its unsmoothed outline.
19. **Fit where the light pools, not only its power.** Matching the stone's median brightness left the photo's light
    wrong in place: a light map (the stone's median in 6 x 7 cells, each over the median cell) of the photo pooled in
    the upper middle and fell away at the sides, while the render's fell evenly from top to bottom, an error (the RMS
    of log(render / photo) over the cells) of 0.4426. The spot's direction was right, since the photo's shading under
    Marigold's normals matched best within a few degrees of it; its pool was not. Rendering candidates at 25 % size
    and searching the spot's aim, distance, the pool's half-height on the screen, its width (the spot object scaled
    sideways; `light-world-camera.md`) and its edge: 0.2629 one setting at a time, then 0.2063 at that size with the
    six together (Nelder-Mead, 126 renders), 0.1979 at full size: a spot 4.6936 m out, its pool 1.1079 times as wide
    as round, fully soft, aimed 0.0923 m above the centre. Set the pool by its size on the screen, not the cone's
    angle, or distance and pool size fight; a beam from 59 degrees up stretches a round pool to about twice as tall
    as wide. The bright end (0.5139 against 0.6744) and the contrast (0.6517 of the photo's) stayed short.
    `[exp: shots/jali-match/build.py]` `[exp: shots/jali-match/compare.py]`
20. **Let the normals veto the colour rule.** Brighter light showed holes the colour rule had cut: fragments of lit
    rim, a few per cent brighter than a bright wall. Marigold sees an opening's wall as one flat surface facing the
    camera; the fragments sit on bars facing up. An opening under 400 px whose normals lean more than 15 degrees from
    the wall's, on average, is stone: that took 6.16 % of the openings, and the openings' IoU went from 0.762 to 0.7914
    and the thin stone shown from 0.9586 to 0.9747. Take the wall's normal locally if the model's wall drifts across
    the picture. `[exp: shots/jali-match/read_photo.py]` `[exp: shots/jali-match/compare.py]`
21. **Put the render through the photo's tone curve, with what emits set through its inverse.** With the light's pool
    fitted, the stone's median matched and its bright end did not: 0.5139 against 0.6744, a darker bottom and brighter
    top about the same median, the shape an edited photo's S-curve gives. A curve on luminance through the stone's
    median (a power below it and a mirrored one above, the two exponents fitted to the stone's 10th and 90th
    percentiles) brought it to 0.6743, the contrast to 0.9466 of the photo's and the forms band's amplitude to 0.8283.
    Set anything seen directly (here the glowing wall) through the curve's inverse, then iterate: the wall lights the
    stone's sides, so the curve moves when the wall does. Fitted once, the openings came out 0.5001 against 0.4483;
    iterated, 0.4665 and 0.8478 against 0.8428. Apply it to luminance, R, G and B scaled together: per channel the
    curve never settled (its upper exponent 2.4173, 3.0, 3.231, 3.3183, 3.3508) and a dim grey wall turned warm
    enough to fail the colour rule (openings IoU 0.7576). On luminance it settled in three rounds at 1.0199 and
    2.3742. Blender's contrast looks brighten the emitters too (item 6 sets them exactly).
    `[exp: shots/jali-match/build.py]` `[exp: shots/jali-match/compare.py]`
22. **A pierced screen's frame has no openings: find the carved field and keep openings inside it.** The frame's top
    edge caught the light, pale and greyish, and the colour rule cut holes along it; the normals could not veto them,
    since a plain frame is as flat as a wall. The carved field is the box around every opening of 400 px or more that
    does not reach within 20 px of the screen's box (a pale band along the top edge was one such part and stretched the
    field), padded 6 px: here [160, 148, 1057, 1221], where the share of opening per row and column falls away. That
    took 8824 px of false openings out of the frame and lifted the openings' IoU from 0.7872 to 0.8393, partly because
    the render, solid there, could never match them. Apply it inside the screen's box only: turned on the whole
    image, it made the lit floor below the screen stone, and the box grew to take it in.
    `[exp: shots/jali-match/read_photo.py]` `[exp: shots/jali-match/compare.py]`
23. **Give the stone its age from the photo's albedo, with the specks as colour, not relief.** One stone colour with
    procedural noise read as "VERY fresh" (the user's words): the stone's colour varied 0.2914 as much as the photo's
    (the spread of log(R/G) and log(B/G) over a 5 px blur, on the stone). Marigold's intrinsic decomposition
    (`prs-eth/marigold-iid-lighting-v1-1`, OpenRAIL++-M; diffusers' `MarigoldIntrinsicsPipeline`) on tiles like the
    normals, 90.5 s, tiles differing by a median 0.0109 where they overlap: its albedo comes at its true scale (the
    shading only up to a scale per tile, so it is not used). Scale it channel by channel to the albedo already fitted,
    so the light and the tone curve keep their level, and project it like the normal map where the surface faces the
    camera. Two things it does not do: the photo's pale mineral specks are not in it (alone, the carving read as clean
    clay), and dividing the photo by it does not take them out of the relief. So put the specks into the albedo (the
    photo's luminance over its 3 x 3 grey-scale opening, capped at 1.6 times: at 2.5 some went white and the render's
    rule took them for wall, the openings' IoU 0.7951), and take them out of the detail tilt by a 5 x 5 opening. The
    colour spread rose to 0.4863 of the photo's, the frame's texture from 1.2179 to 1.1674 (crinkled to mottled), and
    with the light refitted over the stained albedo the light map's error fell from 0.207 to 0.1498. Judged "this
    looks so real". The colour spread is partly the wrong measure: about a third of the photo's colour variation goes
    with brightness (lit faces paler, shadows redder), which is light or processing, not stone.
    `[exp: shots/jali-match/intrinsics.py]` `[exp: shots/jali-match/build.py]` `[exp: shots/jali-match/compare.py]`
24. **Paler highlights are not the light's colour once the stone's colour is fitted.** In the photo log(R/G) falls
    and log(B/G) rises with luminance over the stone (slopes -0.0997 and 0.1133), the render's far less (-0.0311,
    0.0249). A spot from 2700 K to 10000 K, the stone's colour divided by the spot's so the lit stone keeps its colour,
    moved the render's slopes by under 0.03 (at 25 % size, against the photo's -0.0671 and 0.0774 there): the lit
    faces keep their colour by design, and the shadows are lit mostly by light bounced off the same stone. Look to
    the photo's processing instead (item 25). `[exp: shots/jali-match/build.py]` `[exp: shots/jali-match/compare.py]`
25. **The photo's processing takes colour out of its highlights: one saturation curve on luminance.** After the tone
    curve, each pixel's distance from grey (luminance kept) scaled by (Y / m)^-k, m the stone's median: less colour above
    it, more below. Fitted on stone in both images, k = 0.3 brought the slopes to -0.0997 and 0.1196 against the photo's
    -0.0998 and 0.1134 (from -0.0311 and 0.0222), and the stone's colour spread from 0.4839 of the photo's to 0.7457.
    Fit it where the comparison measures: on the photo's stone alone it took in the render's wall at the openings'
    edges and fitted k = 0.1, which the comparison then measured at -0.0557 and 0.055. And give the render the photo's
    normals' veto too (item 20): its lit faces, now paler like the photo's, otherwise read as wall (openings' IoU
    0.7701). Judged "so realistic". `[exp: shots/jali-match/build.py]` `[exp: shots/jali-match/compare.py]`
26. **Keep only a learned albedo's slow change.** Marigold's albedo of a plain stone surface is soft round blobs 8 to 15
    px across; projected on the frame they read as blur (the user's "bluriness"). The frame's top band, its fine band
    over its forms band: the photo 0.6831, the render 0.3922. A 9 px blur, smaller than the blobs, changed nothing
    (0.3825); 41 px, within the stone only, took them out (0.467), the fine detail left to the photo's own specks.
    Blurring across the openings spread the wall's grey into the stone (openings' IoU 0.7779).
    `[exp: shots/jali-match/compare.py]` `[exp: shots/jali-match/build.py]`

### A standard for a photo match (C-016)

Which numbers say a render is nearer its photo? Every measure the cards used, recomputed on all eight judged sheets
(C-007's "no" to C-015's "this looks so real!"), each ranked against the verdicts: Spearman 1 is in step with them,
on the same full-size patch of the carved field and on the whole screen at half size. A measure is in the standard
if it follows the verdicts in both views. `shots/jali-match/compare.py` prints this as `scorecard`; the bars are this
asset's accepted state or the bars the cards set, and a second asset (T-018) will test them.

| measure | sees | follows the verdicts (patch, whole) | bar | accepted |
|---|---|---|---|---|
| SSIM of luminance, screen's box | structure, at every scale | 0.898, 0.922 | at least 0.50 | 0.5536 |
| openings' IoU (full size) | the outline | 0.922 (from the cards' own comparisons) | at least 0.75 | 0.8215 |
| stone's bright end, render over photo | the light's strength | 0.874, 0.838 | 0.85 to 1.15 | 0.9994 |
| render's cut lines within 2 px of the photo's | where the carving's dark lines fall | 0.886, 0.826 | at least 0.60 | 0.6067 |
| forms band correlation (secondary) | the carving's light and dark | 0.731, 0.898 | at least 0.50 | 0.6433 |
| stone's colour spread, render over photo (secondary) | stains, age | 0.527, 0.922 | at least 0.45 | 0.4863 |

Guards, which did not follow the verdicts but catch a break: the contrast and the forms band's amplitude (0.8 to 1.2
of the photo's), the thin stone shown (at least 0.90), the openings' brightness in each half (within 0.02), the light
map (at most 0.20), the frame's texture (0.8 to 1.2). Not in it: the edge gradient (0.06, 0.335), which a lens and a
pixel filter set, not the likeness. On the half-size sheets the rule's openings drift with the render's tones (IoU
-0.205, -0.263 against the verdicts), so measure openings at full size. The lines measure, set aside in C-009 when it
fell for one card, follows the verdicts over all eight. Eight sheets, one photo, one judge: a pattern to keep testing.
`[exp: shots/jali-match/measure_history.py]` `[exp: shots/jali-match/compare.py]`

```python
# 3: the hole's front outline from what the photo sees through it (seen: a boolean mask, H x W)
k = dist / (dist + thickness)                      # the back face's size, seen from the camera, against the front's
yy, xx = np.mgrid[0:H, 0:W]
sy = np.clip(np.round(H / 2 + (yy - H / 2) * k).astype(int), 0, H - 1)
sx = np.clip(np.round(W / 2 + (xx - W / 2) * k).astype(int), 0, W - 1)
hole = seen | seen[sy, sx]
```

What the measures said about the judgements. In C-007 the openings agreed at an IoU of 0.5652, with the misses in
slivers along every edge; the stone's median colour matched the photo's (0.4392, 0.3294, 0.251 against 0.435, 0.322,
0.239), but its bright end did not: 0.4927 at the 90th percentile against 0.657, a flat slab having no raised surfaces
to catch the light. In C-008 the openings agreed at 0.7252, and the bright end was still 0.4655 against 0.6557: rounded
bars and grooves did not give the forms that catch the light. In C-009 the openings agreed at 0.7641; 41.93 % of the
render's lines lay within 2 px of the photo's and 24.85 % the other way; and the bright end was 0.4652 against 0.6669
(the photo's rose when its lit edges became stone): the averaged motif placed the forms, but they are too soft to
catch the light as the carving does. In C-011 the openings agreed at 0.7598 and 95.89 % of the thin pieces showed; the
forms band was 0.6527 (partly the photo's own detail), its amplitude 0.531 of the photo's, and the bright end 0.4776
against 0.6685: judged a photograph at a glance, with the light still even and dim where the photo's spot pools on
the centre and lights the rims. With the pool fitted (C-012) the light map's error fell from 0.4426 to 0.1979 and the
bright end rose to 0.5139: "it reads better". With the tone curve, the borders and the albedo (C-013 to C-015) the
bright end is 0.6732 against 0.6736 and the openings agree at 0.8215: "this looks so real!".
`[exp: shots/jali-match/compare.py]`
