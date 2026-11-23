# Falling boxes: ten 20 cm cubes dropped from 1 to 3 m onto a passive ground, 120 frames, baked.
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from _common import OUT
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.frame_start, sc.frame_end = 1, 120
bpy.ops.rigidbody.world_add()
sc.rigidbody_world.point_cache.frame_start, sc.rigidbody_world.point_cache.frame_end = 1, 120
bpy.ops.mesh.primitive_plane_add(size=30)
ground = bpy.context.active_object
with bpy.context.temp_override(object=ground, active_object=ground, selected_objects=[ground]):
    bpy.ops.rigidbody.object_add(type="PASSIVE")
ground.rigid_body.collision_shape = "BOX"
for i in range(10):
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=(-4.5 + i, 0, 1 + 2 * i / 9))
    c = bpy.context.active_object
    with bpy.context.temp_override(object=c, active_object=c, selected_objects=[c]):
        bpy.ops.rigidbody.object_add(type="ACTIVE")
    c.rigid_body.collision_shape = "BOX"
bpy.ops.ptcache.bake_all(bake=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
