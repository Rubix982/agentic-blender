"""Remesh (voxel), Weld and Decimate: how their main parameter maps to the output size, and whether the result is clean."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import math, time
import bpy, bmesh
import exp
E = exp.Experiment(__file__)


def ev(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    me = ob.evaluated_get(dg).data
    bm = bmesh.new(); bm.from_mesh(me)
    r = dict(verts=len(bm.verts), faces=len(bm.faces), manifold=all(e.is_manifold for e in bm.edges),
             tris=sum(1 for f in bm.faces if len(f.verts) == 3), quads=sum(1 for f in bm.faces if len(f.verts) == 4),
             volume=round(bm.calc_volume(), 4))
    bm.free()
    return r

# Remesh voxel on a torus (two separate shells joined into one mesh to show it fuses)
bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.3)
t = bpy.context.object
base = ev(t)
r = t.modifiers.new("Remesh", "REMESH")
E.fact("a new Remesh modifier defaults to mode VOXEL", mode=r.mode, voxel_size=r.voxel_size, adaptivity=r.adaptivity,
       modes=[e.identifier for e in r.bl_rna.properties["mode"].enum_items])
rows = {}
for vs in (0.1, 0.05, 0.025):
    r.voxel_size = vs
    tt = time.perf_counter(); res = ev(t); dt = time.perf_counter() - tt
    rows[vs] = dict(seconds=round(dt, 3), **res)
E.fact("voxel remesh of a torus (major 1, minor 0.3): halving voxel_size roughly quadruples the face count; output is all quads and manifold",
       base=base, by_voxel_size=rows, torus_volume_exact=round(2 * math.pi**2 * 1 * 0.3**2, 4))
r.voxel_size = 0.05; r.adaptivity = 0.5
E.fact("adaptivity 0.5 reduces faces and introduces triangles", **ev(t))
r.adaptivity = 0.0
r.mode = "SHARP"; r.octree_depth = 5
E.fact("Remesh mode SHARP (octree_depth 5)", **ev(t))
t.modifiers.clear()

# Weld: duplicate vertices
bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, location=(4, 0, 0))
s = bpy.context.object
bm = bmesh.new(); bm.from_mesh(s.data)
bmesh.ops.split_edges(bm, edges=bm.edges[:])                    # every face loose: many coincident verts
bm.to_mesh(s.data); bm.free()
before = ev(s)
w = s.modifiers.new("Weld", "WELD")
E.fact("Weld modifier defaults", merge_threshold=w.merge_threshold, mode=w.mode, modes=[e.identifier for e in w.bl_rna.properties["mode"].enum_items])
after = ev(s)
E.fact("Weld (default 0.001 m, mode ALL) rejoins a sphere whose faces were all split apart: verts back to 114 and manifold",
       before=before, after=after)
w.mode = "CONNECTED"
E.fact("Weld mode CONNECTED only merges along existing edges, so split faces stay split", **ev(s))
s.modifiers.clear()

# Decimate
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, location=(8, 0, 0))
d = bpy.context.object
base = ev(d)
m = d.modifiers.new("Decimate", "DECIMATE")
E.fact("Decimate defaults", decimate_type=m.decimate_type, ratio=m.ratio, types=[e.identifier for e in m.bl_rna.properties["decimate_type"].enum_items])
rat = {}
for ratio in (0.5, 0.1):
    m.ratio = ratio; res = ev(d); res["face_count_reported"] = m.face_count; rat[ratio] = res
E.fact("Decimate COLLAPSE ratio is a fraction of the triangle count; the output is mostly triangles", base=base, by_ratio=rat)
m.decimate_type = "DISSOLVE"; m.angle_limit = math.radians(5)
bpy.ops.mesh.primitive_cube_add(location=(12, 0, 0)); c = bpy.context.object
sub = c.modifiers.new("s", "SUBSURF"); sub.levels = 2; sub.subdivision_type = "SIMPLE"
dm = c.modifiers.new("d", "DECIMATE"); dm.decimate_type = "DISSOLVE"; dm.angle_limit = math.radians(5)
E.fact("Decimate DISSOLVE (planar, 5 deg) on a simple-subdivided cube gets back to 6 faces", **ev(c))
dm.decimate_type = "UNSUBDIV"; dm.iterations = 2
E.fact("Decimate UNSUBDIV with 2 iterations undoes 2 levels of simple subdivision on the cube", **ev(c))
E.save()
