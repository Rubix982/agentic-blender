"""Does render.use_persistent_data make the second and later Cycles renders of a session faster?"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import time
import bpy
from mathutils import Vector
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
E.fact("render.use_persistent_data is off by default", use_persistent_data=scene.render.use_persistent_data)

# a heavy-ish mesh (subdivided suzanne, about 500k faces) so scene sync and BVH build cost something
bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 1))
mk = bpy.context.object
mod = mk.modifiers.new("sub", "SUBSURF")
mod.levels = mod.render_levels = 5
bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_plane_add(size=10)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.rotation_euler = (0.6, 0.2, 0.4)
scene.collection.objects.link(sun)
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.location = (0, -5, 2)
cam.rotation_euler = (Vector((0, 0, 1)) - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.engine = "CYCLES"
exp.metal()
scene.render.resolution_x = scene.render.resolution_y = 128
scene.cycles.samples = 8
scene.cycles.use_denoising = False
faces = len(mk.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.polygons)


def frames(persistent, n=4):
    scene.render.use_persistent_data = persistent
    out = []
    for f in range(n):
        mk.rotation_euler.z = 0.2 * f  # only a transform changes between renders
        t = time.time()
        bpy.ops.render.render()
        out.append(round(time.time() - t, 2))
    return out


frames(False, 1)  # warm-up: kernel load
off = frames(False)
on = frames(True)
E.fact("with persistent data off, every render of a ~500k-face scene pays scene sync and BVH build again",
       seconds=off, faces=faces)
E.fact("with persistent data on, renders after the first that only move an object are faster",
       seconds=on, faces=faces, first_over_later=round(on[0] / (sum(on[1:]) / 3), 2),
       off_mean_later=round(sum(off[1:]) / 3, 2), on_mean_later=round(sum(on[1:]) / 3, 2))
E.save(off=off, on=on, faces=faces)
