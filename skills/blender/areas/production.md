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

Card C-007 rebuilt a carved red-sandstone window screen (a jali) from one frontal museum photograph, by script: its
openings traced from the photo, the trace extruded to the screen's thickness, lit to the photo's medians, and rendered
from the photo's camera (`shots/jali-match/`). Judged beside the photo it failed: "very surreal", "something plain
but it is not", "a darker muddier look" (the user's words, CARD.md). The openings landed within a few pixels; the
carving inside the stone was never built. What the build found, in the order a script meets it:

1. **Find the openings by a property that holds across the whole photo.** Light on a backdrop falls off: here the
   wall behind the screen was white at the bottom and dim and warm at the top. Saturation below 0.22 with luminance
   at least 0.30 found 3.5 % openings in the top half; green over red above 0.86 found 10.9 %, because the stone is red
   at every brightness and the wall is not. Check a rule in bands from top to bottom before trusting it.
   `[exp: shots/jali-match/read_photo.py]`
2. **Dark pixels inside the object are its own shadows, until their colour says otherwise.** The dark pixels in the
   carved field (5.6 % of it) had green over red of 0.355 at the median and 0.469 at the 90th percentile: stone in
   shadow, not wall. Trace them as solid; only dark pixels connected to the photo's edge are the surround.
   `[exp: shots/jali-match/read_photo.py]`
3. **What a photo shows through an opening is already narrowed by the depth.** The camera sees the hole's front
   outline overlapping its back outline, and the back appears scaled towards the picture's centre by
   distance / (distance + thickness): 0.9546 for 6.1 cm at 1.28 m. Extrude the seen region and every hole narrows
   twice. For straight-through holes the front outline holds both the seen region and the seen region scaled back
   out, so trace their union. `[exp: shots/jali-match/build.py]`
4. **Trace into a 2D curve with `offset` 0** and shrink the shape before tracing instead: a negative offset grows the
   holes into each other and the fill turns inside out (`curves-text.md`, item 8). Set `use_smooth` on every spline;
   flat facets on the holes' inner walls read as stripes. `[exp: experiments/curves/curve_offset_fill.py]`
5. **Size a backdrop for its depth.** A panel the object's size, 0.4 m behind it, appeared 0.7486 of the object's size
   from the camera, and the top and bottom openings looked past it into black. Scale it up by
   (distance to the panel) / (distance to the object). `[exp: shots/jali-match/build.py]`
6. **Fit the lights to the photo's medians, but find the backdrop in the render by colour alone.** With the photo's
   brightness threshold the dim backdrop drops out of the count, and each round of the fit makes it dimmer.

```python
# 3: the hole's front outline from what the photo sees through it (seen: a boolean mask, H x W)
k = dist / (dist + thickness)                      # the back face's size, seen from the camera, against the front's
yy, xx = np.mgrid[0:H, 0:W]
sy = np.clip(np.round(H / 2 + (yy - H / 2) * k).astype(int), 0, H - 1)
sx = np.clip(np.round(W / 2 + (xx - W / 2) * k).astype(int), 0, W - 1)
hole = seen | seen[sy, sx]
```

What the measures said about the judgement: the openings agreed at an IoU of 0.5652, with the misses in slivers
along every edge. The stone's median colour matched the photo's (0.4392, 0.3294, 0.251 against 0.435, 0.322, 0.239),
but its bright end did not: 0.4927 at the 90th percentile against 0.657, because a flat slab has no raised surfaces
to catch the light. An extruded trace gives the holes and loses the carving between them.
`[exp: shots/jali-match/compare.py]`
