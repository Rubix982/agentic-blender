"""Boolean modifier solvers in 4.5 (FAST, EXACT, MANIFOLD): time and correctness for a slab cut by an n x n grid of round holes.

Run: python3 tools/run.py experiments/modifiers/boolean_solvers.py -- N   (N = holes per side; results-<N>.json)
Correctness: a slab with k through-holes is a closed surface of genus k, so V - E + F = 2 - 2k; every edge should have
exactly two faces (manifold); the volume should be slab volume minus k prism volumes.
"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import math, time
import bpy, bmesh
from mathutils import Matrix
import exp
E = exp.Experiment(__file__)
N = int(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv and len(sys.argv) > sys.argv.index("--") + 1 else 10
E.name = f"boolean_solvers-{N}"
SEG, R, T = 16, 0.3, 0.2          # hole polygon sides, radius; slab thickness (spacing 1)


def slab():
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(N, N, T), verts=bm.verts[:])
    me = bpy.data.meshes.new("slab"); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("slab", me); bpy.context.scene.collection.objects.link(ob)
    return ob


def cutters_joined(open_ends=False):
    bm = bmesh.new()
    for i in range(N):
        for j in range(N):
            x, y = i - (N - 1) / 2, j - (N - 1) / 2
            bmesh.ops.create_cone(bm, cap_ends=not open_ends, segments=SEG, radius1=R, radius2=R, depth=1.0,
                                  matrix=Matrix.Translation((x, y, 0)))
    me = bpy.data.meshes.new("cutters"); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("cutters", me); bpy.context.scene.collection.objects.link(ob)
    ob.hide_render = True; ob.display_type = "WIRE"
    return ob


def cutters_collection():
    col = bpy.data.collections.new("cutter_col"); bpy.context.scene.collection.children.link(col)
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=SEG, radius1=R, radius2=R, depth=1.0)
    me = bpy.data.meshes.new("cyl"); bm.to_mesh(me); bm.free()
    for i in range(N):
        for j in range(N):
            o = bpy.data.objects.new("c", me); o.location = (i - (N - 1) / 2, j - (N - 1) / 2, 0)
            col.objects.link(o)
    return col


def check(me):
    bm = bmesh.new(); bm.from_mesh(me)
    non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
    boundary = sum(1 for e in bm.edges if e.is_boundary)
    chi = len(bm.verts) - len(bm.edges) + len(bm.faces)
    vol = bm.calc_volume(signed=False)
    bm.free()
    return dict(verts=len(me.vertices), faces=len(me.polygons), non_manifold_edges=non_manifold, boundary_edges=boundary,
                euler=chi, genus=(2 - chi) / 2, volume=round(vol, 4))


hole_area = 0.5 * SEG * R * R * math.sin(2 * math.pi / SEG)
expected = dict(genus=N * N, volume=round(N * N * T - N * N * hole_area * T, 4))
rows = []
for operand in ("OBJECT", "COLLECTION"):
    for solver in ("FAST", "EXACT", "MANIFOLD"):
        exp.empty()
        s = slab()
        if operand == "OBJECT":
            c = cutters_joined()
        else:
            c = cutters_collection()
        bpy.context.evaluated_depsgraph_get()            # evaluate the inputs first, so the timing is the boolean alone
        m = s.modifiers.new("Bool", "BOOLEAN")
        m.operation = "DIFFERENCE"; m.solver = solver
        if operand == "OBJECT":
            m.object = c
        else:
            m.operand_type = "COLLECTION"; m.collection = c
        t = time.perf_counter()
        dg = bpy.context.evaluated_depsgraph_get()
        ev = s.evaluated_get(dg)
        me = ev.to_mesh()
        dt = time.perf_counter() - t
        r = dict(operand=operand, solver=solver, seconds=round(dt, 3), **check(me))
        r["correct"] = (r["non_manifold_edges"] == 0 and r["genus"] == expected["genus"] and abs(r["volume"] - expected["volume"]) < 1e-3)
        ev.to_mesh_clear()
        rows.append(r)
        print(r, flush=True)
        E.fact(f"{N}x{N} holes, {operand.lower()} operand, {solver}: {dt:.2f} s, {r['non_manifold_edges']} non-manifold edges, genus {r['genus']} (expected {expected['genus']}), volume {r['volume']} (expected {expected['volume']})",
               **r)

# non-manifold cutter (open tubes): what each solver does
for solver in ("FAST", "EXACT", "MANIFOLD"):
    exp.empty()
    s = slab(); c = cutters_joined(open_ends=True)
    m = s.modifiers.new("Bool", "BOOLEAN"); m.operation = "DIFFERENCE"; m.solver = solver; m.object = c
    dg = bpy.context.evaluated_depsgraph_get()
    me = s.evaluated_get(dg).to_mesh()
    r = dict(solver=solver, cutter="open tubes (non-manifold)", **check(me))
    s.evaluated_get(dg).to_mesh_clear()
    E.fact(f"{N}x{N} holes cut by OPEN tubes (no caps), {solver}: {r['verts']} verts, genus {r['genus']}, {r['non_manifold_edges']} non-manifold edges",
           **r)
E.save(rows=rows, expected=expected, segments=SEG, radius=R, thickness=T)
