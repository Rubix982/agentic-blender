# Held-out tasks

Written on 2026-11-23, before any of the guide. The guide is not written from these: no area page names them, and no
experiment reproduces one. Each task is given to a fresh agent as written here, once with the skill and once without; it
writes one Python script without running Blender, and that script is run once, headless, on Blender 4.5.14 with factory
settings and `--python-exit-code 1` (`evals/run_eval.py`). A task counts as right first time when that
first script runs without an error and its output passes the check (`evals/checks.py`, written after the tasks and before
any run).

Every task saves to the path given as the script's first argument after `--`.

Amended on 2026-11-23, before any run and before the checks were written: task 2 named one output path for two outputs
(now the `.blend` at the path and the PNG beside it), and task 5's vertex count depended on whether the plane is kept
(now a count of cubes). Task 4's check also names the colours. The tasks themselves are unchanged.

1. **Pierced slab.** A slab 300 x 400 x 60 mm with a 5 x 6 grid of square holes 40 mm wide cut right through it, exported
   as a binary glTF (`.glb`), in metres. Check: one mesh, watertight, volume within 2 % of the solid's, genus 30.
2. **Low sun.** A white sphere of radius 1 m resting on a grey plane, lit only by a sun 20 degrees above the horizon, no
   world light; rendered with Cycles at 256 x 256 with 32 samples. Save the `.blend` to the given path and the render
   next to it, with the same name ending in `.png`. Check: from the saved `.blend`, one sun whose elevation is 20 +- 0.5
   degrees, the world contributing nothing, Cycles at 32 samples and 256 x 256; the PNG exists at 256 x 256 and is lit
   (not uniform).
3. **Heightfield.** A 100 x 100 vertex grid, 2 m across, with z = 0.1 sin(3x) cos(3y), built from arrays (not by
   editing a primitive), shaded smooth except across edges sharper than 30 degrees; saved as `.blend`. Check: 10,000
   vertices, 9,801 faces, every face smooth, and the 30-degree rule present (a modifier or the mesh's sharp-edge data).
4. **Stone material.** A material whose base colour mixes two given colours (#8a5a44 and #b07a5c) by a noise texture
   through a colour ramp, with roughness 0.7 and a bump from the same noise; saved as `.blend`. Check: the node graph
   links noise to ramp to the Principled BSDF's base colour, noise to a Bump node to its normal, roughness 0.7, and the
   ramp's two colours are the two given colours.
5. **Scatter.** A geometry-nodes modifier on a 2 x 2 m plane that scatters exactly 200 points and puts a 5 cm cube on
   each; saved as `.blend`. Check: the evaluated result holds exactly 200 cubes 5 cm across (as instances or as real
   geometry), all over the plane.
6. **Hanging cloth.** A 1 m square cloth (a 20 x 20 grid) pinned at its two top corners, falling for 60 frames under
   gravity, the simulation baked; saved as `.blend`. Check: at frame 60 the pinned corners are within 1 mm of where they
   started and the two free corners at least 30 cm lower.
7. **Falling boxes.** Ten 20 cm cubes dropped from heights 1 to 3 m onto a passive ground plane, simulated for 120
   frames and baked; saved as `.blend`. Check: at frame 120 every cube's centre is 10 +- 1 cm above the plane.
8. **Framing.** Given the default scene's cube scaled to (1, 0.5, 2), a camera with a 50 mm lens on a 36 mm sensor placed
   on the +Y side so the cube's projected height fills 80 +- 3 % of a 1080 x 1080 frame; saved as `.blend`. Check: the
   projected bounding box, from `world_to_camera_view`.
9. **Passes.** A scene rendered with Cycles to a multilayer OpenEXR that holds the depth and normal passes besides the
   image. Check: the EXR's channels include depth and the three normal components.
10. **Bending.** A cylinder 2 m tall skinned with automatic weights to a three-bone armature along its axis, the middle
   bone posed at 45 degrees; saved as `.blend`. Check: the evaluated mesh's top vertices have moved sideways at least
   30 cm, and no vertex has zero total weight.

## Order of work

1. The tasks (above), then the checks (`evals/checks.py`), before any of the guide's area pages existed in full.
2. The skill is frozen as v1 (a git tag) before anyone solves a task.
3. Then reference solutions (`evals/reference/`), written to show that each check passes a correct answer and fails a
   wrong one. Anything learned while writing them waits for v2; it does not go into v1.
4. Then the runs: a fresh agent per task, with v1 and without it.
