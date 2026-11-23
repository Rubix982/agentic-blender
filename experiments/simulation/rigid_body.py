"""Rigid bodies headless: making the world and the bodies, the collision margin's gap, baking against stepping, jumps.

1. rigidbody.world_add / object_add in background mode, with and without selection (temp_override).
2. A 2 cm cube dropped from 10 cm onto a passive 2 m box (its top at z = 0): where does it come to rest, by collision
   shape and margin? Touching means its centre at z = 0.010.
3. bake_all / ptcache.bake (override) against stepping frame_set; and jumping frames with nothing cached."""
import os, sys, time; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import numpy as np
import exp
E = exp.Experiment(__file__)
N = 60


def scene(shape="CONVEX_HULL", margin=None, use_margin=None, ground_shape="BOX", drop=0.10, size=0.02):
    exp.empty()
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, N
    bpy.ops.rigidbody.world_add()
    sc.rigidbody_world.point_cache.frame_end = N
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, -1.0))
    ground = bpy.context.object
    bpy.ops.rigidbody.object_add(type="PASSIVE")
    ground.rigid_body.collision_shape = ground_shape
    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, drop))
    cube = bpy.context.object
    bpy.ops.rigidbody.object_add(type="ACTIVE")
    rb = cube.rigid_body
    rb.collision_shape = shape
    if use_margin is not None:
        rb.use_margin = use_margin
    if margin is not None:
        rb.collision_margin = margin
    return sc, ground, cube


def settle(sc, cube):
    for f in range(1, N + 1):
        sc.frame_set(f)
    return round(cube.matrix_world.translation.z, 4)


# 1. operators headless
exp.empty()
sc = bpy.context.scene
r_world = list(bpy.ops.rigidbody.world_add())
bpy.ops.mesh.primitive_cube_add()
c = bpy.context.object
c.select_set(False)
bpy.context.view_layer.objects.active = None
err = None
try:
    bpy.ops.rigidbody.object_add()
except Exception as e:
    err = str(e).strip().splitlines()[0]
with bpy.context.temp_override(object=c, active_object=c, selected_objects=[c]):
    r_obj = list(bpy.ops.rigidbody.object_add())
E.fact("rigidbody.world_add and rigidbody.object_add run in background mode; object_add with no active object fails "
       "its poll, and temp_override(object=...) is enough", world_add=r_world, no_active_error=err,
       with_override=r_obj, has_rigid_body=c.rigid_body is not None)

# 2. margin and shape
rows = []
for shape, um, m in (("CONVEX_HULL", None, None), ("CONVEX_HULL", True, 0.001), ("CONVEX_HULL", False, 0.001),
                     ("BOX", None, None), ("BOX", True, 0.04), ("MESH", None, None), ("MESH", True, 0.001),
                     ("SPHERE", None, None)):
    sc, ground, cube = scene(shape, m, um)
    z = settle(sc, cube)
    rows.append(dict(shape=shape, use_margin=cube.rigid_body.use_margin, margin=round(cube.rigid_body.collision_margin, 4),
                     rest_centre_z=z, gap_m=round(z - 0.01, 4)))
    print("MARGIN", rows[-1], flush=True)
# the ground's own margin, the cube's set small
sc, ground, cube = scene("CONVEX_HULL", 0.001, True, ground_shape="CONVEX_HULL")
z = settle(sc, cube)
rows.append(dict(shape="CONVEX_HULL (margin 1 mm) on a CONVEX_HULL ground (default margin)", use_margin=True, margin=0.001,
                 rest_centre_z=z, gap_m=round(z - 0.01, 4)))
print("MARGIN", rows[-1], flush=True)
E.fact("the gap a 2 cm cube leaves above the ground it rests on, by collision shape and margin (default margin 0.04 m, "
       "use_margin off): only the MESH shape leaves a gap at the default margin (about 37 mm); convex hull, box and "
       "sphere rest on the ground (rows: shape, use_margin, margin, gap in m)",
       rows=[(r["shape"], r["use_margin"], r["margin"], r["gap_m"]) for r in rows])

# 3. bake vs step, and jumps
sc, ground, cube = scene("BOX", drop=1.0, size=0.2)
t = time.time()
stepped = {}
for f in range(1, N + 1):
    sc.frame_set(f)
    stepped[f] = cube.matrix_world.translation.z
ts = time.time() - t
pc = sc.rigidbody_world.point_cache
info_stepped = pc.info
sc, ground, cube = scene("BOX", drop=1.0, size=0.2)
pc = sc.rigidbody_world.point_cache
t = time.time()
with bpy.context.temp_override(point_cache=pc):
    rb = list(bpy.ops.ptcache.bake(bake=True))
tb = time.time() - t
baked = {}
for f in (30, 10, 60, 45):     # out of order: a baked cache can be read at any frame
    sc.frame_set(f)
    baked[f] = cube.matrix_world.translation.z
diff = max(abs(baked[f] - stepped[f]) for f in baked)
E.fact("the rigid body world's cache bakes headless with ptcache.bake and temp_override(point_cache="
       "scene.rigidbody_world.point_cache); the bake matches stepping and can be read out of order",
       result=rb, is_baked=pc.is_baked, max_diff_m=diff, bake_s=round(tb, 3), step_s=round(ts, 3),
       stepped_info=info_stepped)

sc, ground, cube = scene("BOX", drop=1.0, size=0.2)
sc.frame_set(1)
z1 = cube.matrix_world.translation.z
sc.frame_set(30)
z30 = cube.matrix_world.translation.z
E.fact("jumping from frame 1 to frame 30 with nothing cached does not simulate a rigid body: it stays where it was",
       z_frame1=round(z1, 4), z_after_jump=round(z30, 4), stepped_z30=round(stepped[30], 4))

# 4. many bodies: time per frame
exp.empty()
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, N
bpy.ops.rigidbody.world_add()
sc.rigidbody_world.point_cache.frame_end = N
bpy.ops.mesh.primitive_plane_add(size=20)
bpy.ops.rigidbody.object_add(type="PASSIVE")
for i in range(10):
    for j in range(10):
        bpy.ops.mesh.primitive_cube_add(size=0.2, location=(i * 0.3 - 1.5, j * 0.3 - 1.5, 1 + 0.05 * ((i + j) % 3)))
        bpy.ops.rigidbody.object_add()
t = time.time()
for f in range(1, N + 1):
    sc.frame_set(f)
E.fact("100 convex-hull cubes on a plane: seconds per frame at the default 10 substeps",
       seconds_per_frame=round((time.time() - t) / N, 4))
E.save(margin_rows=rows)
