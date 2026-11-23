# Reference solution, task 7: a cube dropped onto the ground, rigid-body cache baked into the file.
import bpy, sys

out = sys.argv[sys.argv.index("--") + 1]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 24
sc.render.fps_base = 1.0
sc.frame_start = 1
sc.frame_end = 120

bpy.ops.mesh.primitive_plane_add(size=20.0, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"
bpy.ops.rigidbody.object_add(type='PASSIVE')
ground.rigid_body.collision_shape = 'BOX'

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 10))
cube = bpy.context.active_object
cube.name = "Crate"
bpy.ops.rigidbody.object_add(type='ACTIVE')
cube.rigid_body.mass = 2.0
cube.rigid_body.collision_shape = 'BOX'

rbw = sc.rigidbody_world
rbw.substeps_per_frame = 10          # was steps_per_second before 2.91
rbw.solver_iterations = 20
rbw.point_cache.frame_start = 1
rbw.point_cache.frame_end = 120

sc.frame_set(1)
# No dict context overrides in 4.x; bake via temp_override with the point cache.
with bpy.context.temp_override(scene=sc, point_cache=rbw.point_cache):
    bpy.ops.ptcache.bake(bake=True)

bpy.ops.wm.save_as_mainfile(filepath=out)
