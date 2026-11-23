"""What does an empty scene (read_factory_settings(use_empty=True), the harness's starting point) have for a world and a
camera, and what happens when you render it without a camera?"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
E.fact("an empty factory scene has no world (scene.world is None) and no camera; bpy.data.worlds may still hold one",
       world=None if scene.world is None else scene.world.name, camera=None if scene.camera is None else scene.camera.name,
       worlds_in_file=[w.name for w in bpy.data.worlds], engine=scene.render.engine)
bpy.ops.mesh.primitive_cube_add()
res = {}
for eng in ("CYCLES", "BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH"):
    scene.render.engine = eng
    scene.render.resolution_x = scene.render.resolution_y = 32
    try:
        r = bpy.ops.render.render()
        res[eng] = str(r)
    except RuntimeError as e:
        res[eng] = str(e).strip()
E.fact("bpy.ops.render.render() without a scene camera raises RuntimeError 'Error: Cannot render, no camera' in every engine; "
       "the Blender process then exits 1 under --python-exit-code 1 even though this script catches the error (run it)",
       results=res)
E.save()
