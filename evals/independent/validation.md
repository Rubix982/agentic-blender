# Validation of the independent task set

Blender 4.5.14 LTS, Apple Silicon, CPU only. For each task I ran the reference solution and the wrong solution, each writing to a temporary folder outside the repository, and then ran the check on each output:

```
"$BLENDER" -b --factory-startup --python-exit-code 1 --python reference/taskN.py  -- OUT
"$BLENDER" -b --factory-startup --python-exit-code 1 --python reference/wrongN.py -- OUT
"$BLENDER" -b --factory-startup --python-exit-code 1 --python checks.py -- N OUT
```

One Blender process at a time; all twenty solutions and twenty checks took about 17 s of wall time. Every solution script exited 0 and wrote its file, so each wrong answer below is caught by the check reading the output, not by a crash.

## Results

| Task | Reference | Wrong solution (the mistake) | Wrong |
| --- | --- | --- | --- |
| 1 Terrain from a height table | pass (exit 0) | sets `use_auto_smooth` / `auto_smooth_angle` (removed in 4.1) inside try/except, so the faces end up smooth everywhere | fail (exit 1) |
| 2 Weighted bevel and array | pass | writes `edge.bevel_weight` (removed in 4.0), falls back to a made-up `bevel_weight` attribute the modifier ignores | fail |
| 3 Coated car paint | pass | sets Principled inputs by their 3.x names (`Clearcoat`, `Sheen`, `Transmission`, `Emission`) and skips names it cannot find | fail |
| 4 Light linking | pass | puts the right sphere in the sun's blocker collection (shadow linking) instead of excluding it as a receiver | fail |
| 5 360° panorama | pass | sets `camera.cycles.panorama_type` (where 2.8x kept it), catches the AttributeError, renders the default fisheye | fail |
| 6 Looping slide, spin and glow | pass | adds the keys and Cycles modifiers but leaves the default Bezier interpolation | fail |
| 7 Baked rigid-body drop | pass | plays frames 1–120 through and saves, expecting the cache to persist, instead of baking | fail |
| 8 Sphere grid with an exposed Scale | pass | sets `mod["Scale"] = 0.5` by socket name; the modifier keys inputs by identifier (`Socket_1`), so 1.0 stays in effect | fail |
| 9 STL for a 3D printer | pass | exports with scale 1, so the metre-sized model is written as a 0.1 × 0.1 × 0.02 "mm" part | fail |
| 10 Composite over a brand colour | pass | everything right except the view transform, left at the default AgX | fail |

## What each check measured

**Task 1.** Reference: 35 vertices, 24 quads, vertex error 0.0 m; 8 edges over 30° (all with split normals), 30 edges under 30° (all with shared normals). The cliff edges sit at 57.6–60.6° and every other edge at 5.7° or less, so the 30° threshold has a wide margin on both sides. Wrong: same geometry, but all 8 steep edges shaded smooth.

**Task 2.** Reference: modifiers [BEVEL, ARRAY], 8 base vertices, 96 evaluated vertices, x −1.0 to 6.0, y −1.0 to 1.0, z values {0, 1}, 0 bad corners, corner arc radius 0.1 at every profile point. Wrong: 24 evaluated vertices (no bevel), all 12 vertical corners still sharp (distance 0.1414 from the would-be arc centre).

**Task 3.** Reference: all ten inputs at their values, render method BLENDED, transparency overlap off. Wrong: Coat Weight 0.0, Coat Roughness 0.03, Sheen Weight 0.0, Transmission Weight 0.0, Emission Color (1, 1, 1); its `blend_method = 'BLEND'` and `show_transparent_back = False` still map onto the 4.2+ settings in 4.5, so the check accepts that older route for those two settings.

**Task 4.** Reference: left sphere centre 0.887, right sphere centre 0.0004 (ratio 0.0005), ground 0.899–0.905. Wrong: right sphere centre 0.886 (ratio 0.999).

**Task 5.** Reference: all 17 probes as expected (red centre, green right, yellow left, blue at both edges, white top row, magenta bottom row, black between). Wrong: only the centre is red; the fisheye image is black at every other marker position.

**Task 6.** Reference, (x, Z rotation, emission strength) at frames 7, 13, 25, 37, 55, 73, 91: (1.0, 45°, 1.25), (2.0, 90°, 2.5), (4.0, 180°, 5.0), (2.0, 270°, 2.5), (1.0, 45°, 1.25), (4.0, 180°, 5.0), (1.0, 315°, 1.25). Wrong: x 0.625 and emission 0.781 at frames 7, 55 and 91 (eased). Its Z rotation still read 45° at frame 7, so on this curve the spin alone would not reveal the easing; the X position and the emission strength do.

**Task 7.** Reference: baked, cache 1–120, 10 substeps, 20 iterations, one active body of 2 kg, one passive; z = 10.0 / 5.141 / 0.500 at frames 1 / 25 / 120 (5.141 against 5.095 for exact free fall; the 0.3 m tolerance covers the integration step). Wrong: not baked, and after reopening the file the cube stays at z = 10.0 on every frame jumped to.

**Task 8.** Reference: input `Scale` (Socket_1, float), default 1.0, modifier value 0.5, 432 vertices, 12 per grid point, every vertex 0.100 m from its point. Wrong: modifier value 1.0, every vertex 0.200 m from its point.

**Task 9.** Reference: 57 684 bytes = 84 + 50 × 1152, extent 100.0 × 100.0 × 20.0 mm centred on the origin, 0 non-manifold edges, volume 75 183 mm³ (0.952 of an ideal torus, as expected for a 48 × 12 polygon approximation), 1152 of 1152 normals agree. Wrong: extent 0.1 × 0.1 × 0.02, volume about 0.

**Task 10.** Reference: background within 0.28/255 of #1A2B3C, 9997 red pixels centred at (299.5, 99.5). Wrong: background off by 7.7/255 and 0 pure red pixels (AgX turns the emission red into a desaturated orange-red).

## Other valid solutions tried

To check that the checks do not insist on my way of doing a task, I ran some alternatives (outputs in the temporary folder only):

- Task 1 with `bpy.ops.object.shade_smooth_by_angle(angle=30°)`: pass. Task 1 with smooth faces plus a "Smooth by Angle" Geometry Nodes modifier appended from Blender's bundled asset file, angle 30°: pass. The same modifier without first making the faces smooth: fail, correctly, since the modifier keeps existing flat faces and the result is flat-shaded.
- Task 1 with `bpy.ops.object.shade_auto_smooth(angle=30°)`: in background mode the operator prints "Asset loading is unfinished" and adds nothing, so the saved mesh is flat-shaded and the check fails. The file really is wrong, so I left this as a fail.
- Task 4 with an include-style receiver collection (ground and left sphere) instead of excluding the right sphere: pass, identical numbers.
- Task 5 with the default AgX view transform and denoising on: pass (red comes out as (0.855, 0.218, 0.124), still classified red).
- Task 7 baked with `bpy.ops.ptcache.bake_all(bake=True)` instead of a `temp_override` around `ptcache.bake`: pass, identical numbers.

## Changes made to make the checks sound

1. **Task 3, clearcoat roughness 0.03 → 0.08.** 0.03 is the 4.x default of Coat Roughness, so the first wrong solution passed that input without ever setting it. The task and the check now ask for 0.08.
2. **Task 5, colour classification.** It first matched each patch to the nearest pure colour within 0.25. Rendering the reference with the default AgX view transform moves red to (0.855, 0.218, 0.124) and green to (0.433, 0.773, 0.319), which would fail a correct camera for a colour-management reason. It now classifies a patch by which channels exceed 70 % of its brightest channel (black below 0.15), which passes both Standard and AgX and still fails the fisheye.
3. **Task 4, absolute threshold → ratio.** The check first required the right sphere's centre below 0.15. With the default grey world and AgX, a correct light-linking setup gives 0.20 on the right and 0.74 on the left, so the check now requires the right sphere below 35 % of the left (correct setups: 0.0005 with a black world, 0.27 with a grey world; the shadow-linking mistake: 0.999), with the left sphere and ground above 0.4.
4. **Task 10, background patches.** Blender dithers 8-bit output, so single reference pixels were 1/255 off. The check now compares 5 × 5 patch means (reference error 0.28/255) against the 2/255 tolerance.
5. **Object lookup.** Tasks 2 and 3 do not name their object, so the checks pick the mesh that fits (the one with Bevel and Array modifiers; the one with a material whose vertices all lie 1 m from the origin). The sphere test matters: a script that leaves the factory default cube in the scene would otherwise give two candidates, since the cube also has a material and a 2 m extent.
