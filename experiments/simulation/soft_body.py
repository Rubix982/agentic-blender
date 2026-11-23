"""Soft body, briefly: what the default goal does, how a soft body without a goal falls onto a collider, and baking it
headless."""
import os, sys, time; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import numpy as np
import exp
E = exp.Experiment(__file__)
N = 48


def build(use_goal=True, goal=None):
    exp.empty()
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, N
    bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, 0))
    bpy.context.object.modifiers.new("Collision", "COLLISION")
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.3, subdivisions=3, location=(0, 0, 1.0))
    s = bpy.context.object
    sm = s.modifiers.new("Softbody", "SOFT_BODY")
    sb = s.soft_body
    sb.use_goal = use_goal
    if goal is not None:
        sb.goal_default = goal
    sm.point_cache.frame_start, sm.point_cache.frame_end = 1, N
    return sc, s, sm


def lowest(o):
    e = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = e.to_mesh()
    z = min((e.matrix_world @ v.co).z for v in me.vertices)
    e.to_mesh_clear()
    return round(z, 4)


rows = []
for use_goal, goal in ((True, None), (True, 0.0), (False, None)):
    sc, s, sm = build(use_goal, goal)
    z0 = lowest(s)
    t = time.time()
    for f in range(1, N + 1):
        sc.frame_set(f)
    rows.append(dict(use_goal=use_goal, goal_default=round(s.soft_body.goal_default, 3), lowest_start=z0,
                     lowest_end=lowest(s), seconds_per_frame=round((time.time() - t) / N, 4)))
    print("SOFT", rows[-1], flush=True)
E.fact("a new soft body holds its shape in place: use_goal is on with goal_default 0.7 and no goal group, so every point "
       "is pulled to where the mesh is; with the goal off it falls to the collider",
       rows=[(r["use_goal"], r["goal_default"], r["lowest_start"], r["lowest_end"]) for r in rows])

sc, s, sm = build(False)
err = None
try:
    bpy.ops.ptcache.bake(bake=True)
except Exception as e:
    err = str(e).strip().splitlines()[0]
with bpy.context.temp_override(point_cache=sm.point_cache):
    r = list(bpy.ops.ptcache.bake(bake=True))
sc.frame_set(N)
E.fact("a soft body bakes headless the same way as cloth: ptcache.bake with temp_override(point_cache=modifier.point_cache)",
       no_override_error=err, result=r, is_baked=sm.point_cache.is_baked, lowest_end=lowest(s),
       same_as_stepped=lowest(s) == rows[2]["lowest_end"])
E.save(rows=rows)
