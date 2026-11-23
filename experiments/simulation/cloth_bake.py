"""Baking cloth headless: stepping frame_set, bpy.ops.ptcache.bake with and without a context override, bake_all,
bake_from_cache, and jumping straight to a late frame. Do they give the same cloth?

Scene: a 1 m grid (31 x 31 points) at z = 1, its back edge pinned, falling over a sphere collider (r 0.3 m at z = 0.5)."""
import os, sys, time; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import numpy as np
import exp
E = exp.Experiment(__file__)
N = 60


def build():
    exp.empty()
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, N
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(0, 0, 0.5))
    ball = bpy.context.object
    ball.modifiers.new("Collision", "COLLISION")
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=30, y_subdivisions=30, size=1.0, location=(0, 0, 1.0))
    g = bpy.context.object
    g.name = "cloth"
    vg = g.vertex_groups.new(name="pin")
    ymax = max(v.co.y for v in g.data.vertices)
    vg.add([v.index for v in g.data.vertices if v.co.y > ymax - 1e-6], 1.0, "REPLACE")
    cm = g.modifiers.new("Cloth", "CLOTH")
    cm.settings.vertex_group_mass = "pin"
    cm.point_cache.frame_start, cm.point_cache.frame_end = 1, N
    return g, cm


def coords(o):
    dg = bpy.context.evaluated_depsgraph_get()
    e = o.evaluated_get(dg)
    me = e.to_mesh()
    a = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", a)
    e.to_mesh_clear()
    a = a.reshape(-1, 3)
    return (np.array(o.matrix_world)[:3, :3] @ a.T).T + np.array(o.matrix_world)[:3, 3]


# A: step every frame
g, cm = build()
sc = bpy.context.scene
t = time.time()
for f in range(1, N + 1):
    sc.frame_set(f)
tA = time.time() - t
A = coords(g)
infoA = cm.point_cache.info
bakedA = cm.point_cache.is_baked
# go back to an earlier frame: served from the memory cache?
t = time.time(); sc.frame_set(30); back_s = time.time() - t
A30 = coords(g)
sc.frame_set(N)
E.fact("stepping frame_set 1..60 simulates the cloth into a memory cache that is not 'baked'",
       seconds=round(tA, 2), is_baked=bakedA, info=infoA, lowest_z=round(float(A[:, 2].min()), 4))
E.fact("going back to frame 30 after stepping is a cache read, not a re-simulation", seconds=round(back_s, 3))

# bake_from_cache turns the stepped memory cache into a bake
with bpy.context.temp_override(point_cache=cm.point_cache):
    r = bpy.ops.ptcache.bake_from_cache()
E.fact("ptcache.bake_from_cache (with point_cache in the context) marks the stepped cache baked",
       result=list(r), is_baked=cm.point_cache.is_baked)

# B: ptcache.bake without override
g, cm = build()
sc = bpy.context.scene
err = None
try:
    bpy.ops.ptcache.bake(bake=True)
except Exception as e:
    err = str(e).strip().splitlines()[0]
E.fact("bpy.ops.ptcache.bake without a point_cache in the context fails its poll in background mode", error=err)

# B2: with temp_override(point_cache=...)
sc.frame_set(1)
t = time.time()
with bpy.context.temp_override(point_cache=cm.point_cache):
    r = bpy.ops.ptcache.bake(bake=True)
tB = time.time() - t
frame_after = sc.frame_current
sc.frame_set(N)
B = coords(g)
E.fact("ptcache.bake with temp_override(point_cache=...) bakes headless and gives the same cloth as stepping",
       result=list(r), seconds=round(tB, 2), is_baked=cm.point_cache.is_baked, frame_after_bake=frame_after,
       max_diff_vs_stepping_m=float(np.abs(B - A).max()))

# C: bake_all
g, cm = build()
sc = bpy.context.scene
t = time.time()
err = None
try:
    r = list(bpy.ops.ptcache.bake_all(bake=True))
except Exception as e:
    r, err = None, str(e).strip().splitlines()[0]
tC = time.time() - t
sc.frame_set(N)
C = coords(g)
E.fact("ptcache.bake_all(bake=True) needs no override and bakes every cache in the scene",
       result=r, error=err, seconds=round(tC, 2), is_baked=cm.point_cache.is_baked,
       max_diff_vs_stepping_m=float(np.abs(C - A).max()))
# free it again
r_free = list(bpy.ops.ptcache.free_bake_all())
E.fact("ptcache.free_bake_all clears the bake", result=r_free, is_baked=cm.point_cache.is_baked)

# D: jump straight to the last frame with no cache
g, cm = build()
sc = bpy.context.scene
sc.frame_set(1)
rest = coords(g)
sc.frame_set(N)
D = coords(g)
E.fact("jumping from frame 1 straight to frame 60 (nothing cached) takes ONE solver step stretched over the 59 frames: "
       "the free cloth falls metres, straight through the collider, nothing like the stepped result",
       moved_max_m=round(float(np.abs(D - rest).max()), 3), lowest_z=round(float(D[:, 2].min()), 3),
       stepped_lowest_z=round(float(A[:, 2].min()), 3), max_diff_vs_stepping_m=round(float(np.abs(D - A).max()), 3),
       cache_info=cm.point_cache.info)
# D2: a short jump, then a long one
g, cm = build()
sc = bpy.context.scene
sc.frame_set(1)
rest = coords(g)
sc.frame_set(3)
D3 = coords(g)
info3 = cm.point_cache.info
sc.frame_set(N)
D60 = coords(g)
E.fact("a jump of 2 frames from the start is also taken as one step; a further jump after it does not simulate at all "
       "(the cloth shows the last simulated state)",
       fell_at_3_m=round(float(-(D3 - rest)[:, 2].min()), 4), cache_info_at_3=info3,
       moved_between_3_and_60_m=float(np.abs(D60 - D3).max()))

# E: the pinned row
g, cm = build()
sc = bpy.context.scene
ymax = 0.5
pinned = [i for i, v in enumerate(g.data.vertices) if v.co.y > ymax - 1e-6]
P0 = coords(g)[pinned]
for f in range(1, N + 1):
    sc.frame_set(f)
P = coords(g)[pinned]
E.fact("points pinned at weight 1.0 do not move at all under gravity (default pin stiffness 1)",
       pinned=len(pinned), max_move_m=float(np.abs(P - P0).max()))
E.save(frames=N, points=len(A))
