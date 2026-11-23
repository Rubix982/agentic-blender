"""Boolean solvers when the cutters' caps are exactly coplanar with the slab's faces (cutter depth == slab thickness)."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import math, time
import bpy, bmesh
from mathutils import Matrix
import exp
E = exp.Experiment(__file__)
N, SEG, R, T = 10, 16, 0.3, 0.2


def build(depth):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(N, N, T), verts=bm.verts[:])
    me = bpy.data.meshes.new("slab"); bm.to_mesh(me); bm.free()
    s = bpy.data.objects.new("slab", me); bpy.context.scene.collection.objects.link(s)
    bm = bmesh.new()
    for i in range(N):
        for j in range(N):
            bmesh.ops.create_cone(bm, cap_ends=True, segments=SEG, radius1=R, radius2=R, depth=depth,
                                  matrix=Matrix.Translation((i - (N - 1) / 2, j - (N - 1) / 2, 0)))
    me = bpy.data.meshes.new("cut"); bm.to_mesh(me); bm.free()
    c = bpy.data.objects.new("cut", me); bpy.context.scene.collection.objects.link(c)
    return s, c


hole_area = 0.5 * SEG * R * R * math.sin(2 * math.pi / SEG)
exp_vol = round(N * N * T - N * N * hole_area * T, 4)
for solver in ("FAST", "EXACT", "MANIFOLD"):
    exp.empty()
    s, c = build(T)
    m = s.modifiers.new("b", "BOOLEAN"); m.solver = solver; m.object = c
    t = time.perf_counter()
    dg = bpy.context.evaluated_depsgraph_get(); me = s.evaluated_get(dg).to_mesh(); dt = time.perf_counter() - t
    bm = bmesh.new(); bm.from_mesh(me)
    nm = sum(1 for e in bm.edges if not e.is_manifold); chi = len(bm.verts) - len(bm.edges) + len(bm.faces); vol = bm.calc_volume()
    bm.free(); s.evaluated_get(dg).to_mesh_clear()
    E.fact(f"coplanar caps, {N}x{N} holes, {solver}: genus {(2-chi)/2} (expected {N*N}), {nm} non-manifold edges, volume {vol:.4f} (expected {exp_vol}), {dt:.2f} s",
           solver=solver, genus=(2 - chi) / 2, non_manifold_edges=nm, volume=round(vol, 4), expected_volume=exp_vol, seconds=round(dt, 3),
           correct=(nm == 0 and (2 - chi) / 2 == N * N and abs(vol - exp_vol) < 1e-3))
E.save()
