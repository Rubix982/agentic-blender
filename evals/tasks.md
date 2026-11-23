# Held-out tasks

Written on 2026-11-23, before any of the guide. The guide is not written from these: no area page names them, and no
experiment reproduces one. Each task is given to a fresh agent as written here, once with the skill and once without; it
writes one Python script, run headless on Blender 4.5.14 by `tools/run.py`. A task counts as right first time when that
first script runs without an error and its output passes the check (`evals/check_*.py`, written after the tasks and before
any run).

Every task saves to the path given as the script's first argument after `--`.

1. **Pierced slab.** A slab 300 x 400 x 60 mm with a 5 x 6 grid of square holes 40 mm wide cut right through it, exported
   as a binary glTF (`.glb`), in metres. Check: one mesh, watertight, volume within 2 % of the solid's, genus 30.
2. **Low sun.** A white sphere of radius 1 m resting on a grey plane, lit only by a sun 20 degrees above the horizon, no
   world light; rendered with Cycles at 256 x 256 with 32 samples to a PNG. Check: the sun's elevation read back from the
   saved `.blend` is 20 +- 0.5 degrees; the world contributes nothing; the image's lit half of the sphere is brighter than
   its shadow half.
3. **Heightfield.** A 100 x 100 vertex grid, 2 m across, with z = 0.1 sin(3x) cos(3y), built from arrays (not by
   editing a primitive), shaded smooth except across edges sharper than 30 degrees; saved as `.blend`. Check: 10,000
   vertices, 9,801 faces, every face smooth, and the 30-degree rule present (a modifier or the mesh's sharp-edge data).
4. **Stone material.** A material whose base colour mixes two given colours (#8a5a44 and #b07a5c) by a noise texture
   through a colour ramp, with roughness 0.7 and a bump from the same noise; saved as `.blend`. Check: the node graph
   links noise to ramp to the Principled BSDF's base colour, noise to a Bump node to its normal, roughness 0.7.
5. **Scatter.** A geometry-nodes modifier on a 2 x 2 m plane that scatters exactly 200 points and puts a 5 cm cube on
   each; saved as `.blend`. Check: the evaluated object has 1,600 vertices.
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
