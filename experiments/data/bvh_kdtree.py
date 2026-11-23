"""BVHTree and KDTree: building from an object, from polygons and from bmesh; ray casts, nearest-point, overlap; spaces; timings."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import time, random
import numpy as np
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
import exp
E = exp.Experiment(__file__)

bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0, location=(5, 0, 0))
s = bpy.context.object
s.scale = (2, 2, 2)
s.modifiers.new("sub", "SUBSURF").levels = 1
dg = bpy.context.evaluated_depsgraph_get()
t = time.perf_counter(); bvh = BVHTree.FromObject(s, dg); t_obj = time.perf_counter() - t
hit = bvh.ray_cast(Vector((5, 0, 10)), Vector((0, 0, -1)))
E.fact("BVHTree.FromObject(obj, depsgraph) is built in the object's LOCAL space, from the evaluated mesh: a world-space ray misses or hits the wrong place",
       world_ray_result=None if hit[0] is None else tuple(round(x, 4) for x in hit[0]), build_ms=round(t_obj * 1000, 2))
mi = s.matrix_world.inverted()
o_local = mi @ Vector((5, 0, 10)); d_local = (mi.to_3x3() @ Vector((0, 0, -1))).normalized()
loc, nor, idx, dist = bvh.ray_cast(o_local, d_local)
E.fact("transforming the ray into local space (matrix_world.inverted()) gives the right hit; map it back with matrix_world",
       hit_world=tuple(round(x, 4) for x in s.matrix_world @ loc), local_dist=round(dist, 4), face_index=idx)
params = BVHTree.FromObject.__doc__.split("\n")[0:3]
bvh_w = BVHTree.FromObject(s, dg, deform=True, cage=False, epsilon=0.0)
E.fact("FromObject signature", doc=" ".join(x.strip() for x in params))
# FromPolygons with world coordinates
ev = s.evaluated_get(dg); me = ev.data
co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
mw = np.array(s.matrix_world); wco = co @ mw[:3, :3].T + mw[:3, 3]
tris = me.loop_triangles
tri_idx = np.empty(len(tris) * 3, np.int32); tris.foreach_get("vertices", tri_idx)
t = time.perf_counter(); bvh2 = BVHTree.FromPolygons(wco.tolist(), tri_idx.reshape(-1, 3).tolist(), all_triangles=True); t_poly = time.perf_counter() - t
loc2, _, _, _ = bvh2.ray_cast(Vector((5, 0, 10)), Vector((0, 0, -1)))
E.fact("BVHTree.FromPolygons on world-space vertices (here: loop_triangles) answers world-space queries directly",
       hit=tuple(round(x, 4) for x in loc2), build_ms=round(t_poly * 1000, 2), tris=len(tris))
# ray_cast distance limit
miss = bvh2.ray_cast(Vector((5, 0, 10)), Vector((0, 0, -1)), 1.0)
E.fact("ray_cast(origin, direction, distance) returns (None, None, None, None) when nothing is within distance", result=str(miss))
# find_nearest
loc3, n3, i3, d3 = bvh2.find_nearest(Vector((5, 0, 0)))
E.fact("find_nearest from the centre returns a point at about radius 2 (scaled sphere)", dist=round(d3, 4))
nr = bvh2.find_nearest(Vector((50, 0, 0)), 1.0)
E.fact("find_nearest(point, distance) returns all None beyond distance", result=str(nr))
# overlap
bpy.ops.mesh.primitive_cube_add(size=1, location=(6.9, 0, 0)); c = bpy.context.object
bvh_c = BVHTree.FromObject(c, bpy.context.evaluated_depsgraph_get())
pairs_local = bvh_c.overlap(BVHTree.FromObject(s, bpy.context.evaluated_depsgraph_get()))
bm = bmesh.new(); bm.from_mesh(c.data); bm.transform(c.matrix_world)
bvh_cw = BVHTree.FromBMesh(bm); bm.free()
pairs_world = bvh_cw.overlap(bvh2)
E.fact("overlap() needs both trees in the same space: two FromObject trees (each local) find no overlap here, world-space trees do",
       local_pairs=len(pairs_local), world_pairs=len(pairs_world))

# KDTree
random.seed(0)
pts = [Vector((random.random(), random.random(), random.random())) for _ in range(100000)]
t = time.perf_counter()
kd = KDTree(len(pts))
for i, p in enumerate(pts):
    kd.insert(p, i)
kd.balance()
t_build = time.perf_counter() - t
q = Vector((0.5, 0.5, 0.5))
t = time.perf_counter()
for _ in range(1000):
    kd.find(q)
t_find = (time.perf_counter() - t) / 1000
n5 = kd.find_n(q, 5)
rng = kd.find_range(q, 0.05)
E.fact(f"KDTree of 100k points: build+balance {t_build:.2f} s, find() {t_find*1e6:.1f} us; find_n returns (co, index, dist) sorted by distance",
       build_s=round(t_build, 3), find_us=round(t_find * 1e6, 2), find_n_dists=[round(d, 4) for _, _, d in n5], in_range=len(rng))
kd2 = KDTree(10)
kd2.insert((0, 0, 0), 0)
try:
    kd2.find((1, 1, 1)); nb = "accepted"
except Exception as e:
    nb = f"{type(e).__name__}: {e}"
E.fact("querying a KDTree before balance() raises", error=nb)
E.save()
