"""A short hanging chain of small rigid bodies on point constraints (a tassel on cords): does Bullet's default collision
margin (0.04 m, bigger than the pieces) throw it about, and what calms it: a 1 mm margin, or each piece in its own
collision collection?

Three 2.5 cm cord pieces (cylinders, r 3 mm) and a 5 cm tassel (cone) hang from a passive anchor, joined end to end by
POINT constraints; the anchor swings 10 cm sideways over frames 1-20 and back by 40. The chain's swing is the angle of the
line anchor -> tassel's centre from straight down, over frames 2-80."""
import os, sys, math; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import numpy as np
import exp
E = exp.Experiment(__file__)
N = 80


def build(margin=None, own_collections=False, shape="CONVEX_HULL", jerk=False):
    exp.empty()
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, N
    bpy.ops.rigidbody.world_add()
    sc.rigidbody_world.point_cache.frame_end = N
    bpy.ops.mesh.primitive_cube_add(size=0.01, location=(0, 0, 1.0))
    anchor = bpy.context.object
    bpy.ops.rigidbody.object_add(type="PASSIVE")
    anchor.rigid_body.kinematic = True        # "Animated": follows its keyframes
    anchor.keyframe_insert("location", frame=1)
    if jerk:     # shaken: +-5 cm every 3 frames, like a point riding a walking garment, only harsher
        for k, f in enumerate(range(4, 61, 3)):
            anchor.location.x = 0.05 if k % 2 == 0 else -0.05
            anchor.keyframe_insert("location", frame=f)
    else:
        anchor.location.x = 0.10
        anchor.keyframe_insert("location", frame=20)
        anchor.location.x = 0.0
        anchor.keyframe_insert("location", frame=40)
    pieces, top = [], 1.0 - 0.005
    for k in range(4):
        L = 0.025 if k < 3 else 0.05
        if k < 3:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.003, depth=L, vertices=8, location=(0, 0, top - L / 2))
        else:
            bpy.ops.mesh.primitive_cone_add(radius1=0.012, radius2=0.002, depth=L, vertices=12, location=(0, 0, top - L / 2))
        p = bpy.context.object
        bpy.ops.rigidbody.object_add(type="ACTIVE")
        rb = p.rigid_body
        rb.collision_shape = shape
        rb.mass = 0.002 if k < 3 else 0.01
        if margin is not None:
            rb.use_margin = True
            rb.collision_margin = margin
        if own_collections:
            rb.collision_collections = [i == k + 1 for i in range(20)]
        pieces.append(p)
        top -= L
    joints = []
    chain = [anchor] + pieces
    z = 1.0 - 0.005
    for k in range(4):
        bpy.ops.object.empty_add(location=(0, 0, z))
        j = bpy.context.object
        bpy.ops.rigidbody.constraint_add(type="POINT")
        c = j.rigid_body_constraint
        c.object1, c.object2 = chain[k], chain[k + 1]
        joints.append(c)
        z -= 0.025 if k < 3 else 0.05
    return sc, anchor, pieces, joints


def swing(margin=None, own_collections=False, shape="CONVEX_HULL", jerk=False):
    sc, anchor, pieces, joints = build(margin, own_collections, shape, jerk)
    angles, rise = [], 0.0
    z0 = pieces[-1].matrix_world.translation.z
    for f in range(1, N + 1):
        sc.frame_set(f)
        a = np.array(anchor.matrix_world.translation)
        t = np.array(pieces[-1].matrix_world.translation)
        d = t - a
        if f > 1:
            angles.append(math.degrees(math.atan2(math.hypot(d[0], d[1]), -d[2])))
        rise = max(rise, t[2] - z0)
    return dict(margin=margin if margin is not None else "default 0.04 (use_margin off)", own_collections=own_collections,
                shape=shape, jerk=jerk, disable_collisions=joints[0].disable_collisions,
                swing_p50_deg=round(float(np.percentile(angles, 50)), 1), swing_p95_deg=round(float(np.percentile(angles, 95)), 1),
                swing_max_deg=round(float(max(angles)), 1), tassel_rise_m=round(float(rise), 4))


rows = []
for args in ((None, False), (0.001, False), (None, True), (0.001, True), (None, False, "MESH"), (0.001, False, "MESH"),
             (None, False, "CONVEX_HULL", True), (0.001, False, "CONVEX_HULL", True), (0.001, True, "CONVEX_HULL", True),
             (None, False, "MESH", True)):
    rows.append(swing(*args))
    print("CHAIN", rows[-1], flush=True)
E.fact("a POINT constraint's disable_collisions is on by default: the two bodies it joins never collide with each other",
       disable_collisions=rows[0]["disable_collisions"])
E.fact("a hanging chain of 2.5-5 cm convex-hull pieces swung by its anchor: the swing (degrees from straight down) at "
       "the default margin, a 1 mm margin, each piece in its own collision collection, and both; with MESH shapes; "
       "gently swung (10 cm over 19 frames) and shaken (+-5 cm every 3 frames). Neither a 1 mm margin nor separate collision collections calms it",
       rows=[(r["shape"], r["jerk"], r["margin"], r["own_collections"], r["swing_p50_deg"], r["swing_p95_deg"], r["swing_max_deg"],
              r["tassel_rise_m"]) for r in rows])
E.save(rows=rows)
