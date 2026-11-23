"""Bezier and poly curves from Python: building splines, bevel/extrude, resolution, and turning a curve into a mesh."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import math
import bpy, bmesh
import exp
E = exp.Experiment(__file__)


def evmesh(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    r = (len(me.vertices), len(me.edges), len(me.polygons)) if me else None
    man = None
    if me and len(me.polygons):
        bm = bmesh.new(); bm.from_mesh(me); man = all(e.is_manifold for e in bm.edges); bm.free()
    ev.to_mesh_clear()
    return dict(counts=r, manifold=man)

cu = bpy.data.curves.new("path", "CURVE")
E.fact("bpy.data.curves.new(name, 'CURVE') makes curve data that is 2D (dimensions '2D'), resolution_u 12, no bevel", dimensions=cu.dimensions,
       resolution_u=cu.resolution_u, bevel_depth=cu.bevel_depth, extrude=cu.extrude, fill_mode=cu.fill_mode,
       types=[e.identifier for e in bpy.types.BlendDataCurves.bl_rna.functions["new"].parameters["type"].enum_items])
sp = cu.splines.new("BEZIER")
E.fact("splines.new('BEZIER') starts with 1 bezier point; add more with bezier_points.add(n)", points=len(sp.bezier_points))
sp.bezier_points.add(3)
pts = [(0, 0, 0), (1, 1, 0.5), (2, 0, 0), (3, 1, 0)]
for bp, co in zip(sp.bezier_points, pts):
    bp.co = co
    bp.handle_left_type = bp.handle_right_type = "AUTO"
E.fact("handle types; AUTO handles are computed when the curve is evaluated",
       types=[e.identifier for e in sp.bezier_points[0].bl_rna.properties["handle_left_type"].enum_items],
       handle_left_0=list(sp.bezier_points[1].handle_left))
ob = bpy.data.objects.new("path", cu); bpy.context.scene.collection.objects.link(ob)
dg = bpy.context.evaluated_depsgraph_get(); tm = ob.evaluated_get(dg).to_mesh(); zmax2d = max(v.co.z for v in tm.vertices); ob.evaluated_get(dg).to_mesh_clear()
cu.dimensions = "3D"
dg = bpy.context.evaluated_depsgraph_get(); tm = ob.evaluated_get(dg).to_mesh(); zmax3d = max(v.co.z for v in tm.vertices); ob.evaluated_get(dg).to_mesh_clear()
E.fact(("a 2D curve flattens its points to z=0 when evaluated" if zmax2d < 1e-6 else "a 2D curve keeps its points' z when evaluated (the 2D flag changes the fill and bevel options, and the fill_mode default is 'NONE' until set to 3D, where it becomes 'FULL')"), z_max_2d=round(zmax2d, 4), z_max_3d=round(zmax3d, 4),
       fill_mode_3d=cu.fill_mode)
r0 = evmesh(ob)
E.fact("an open bezier with 4 points and resolution_u 12 becomes 37 vertices / 36 edges with no faces", **r0)
cu.resolution_u = 4
E.fact("resolution_u 4 gives 3 segments x 4 + 1 = 13 vertices", **evmesh(ob))
cu.resolution_u = 12
cu.bevel_depth = 0.1; cu.bevel_resolution = 2
r1 = evmesh(ob)
E.fact("bevel_depth 0.1 sweeps a round profile along it; open ends stay open unless use_fill_caps", **r1)
cu.use_fill_caps = True
r2 = evmesh(ob)
E.fact("use_fill_caps closes the ends" + (" (the result is manifold)" if r2["manifold"] else " (but the result is still not manifold: cap vertices are separate from the tube)"), **r2)
cu.use_fill_caps = False; cu.bevel_depth = 0.0
cu.extrude = 0.5
E.fact("extrude 0.5 (no bevel) makes a ribbon", **evmesh(ob))
cu.extrude = 0.0
# bevel object
prof = bpy.data.curves.new("prof", "CURVE"); ps = prof.splines.new("POLY"); ps.points.add(3)
for p, co in zip(ps.points, [(-0.1, -0.1, 0, 1), (0.1, -0.1, 0, 1), (0.1, 0.1, 0, 1), (-0.1, 0.1, 0, 1)]):
    p.co = co
ps.use_cyclic_u = True
pob = bpy.data.objects.new("prof", prof); bpy.context.scene.collection.objects.link(pob)
cu.bevel_mode = "OBJECT"; cu.bevel_object = pob
E.fact("bevel_mode 'OBJECT' with a closed square poly curve as bevel_object sweeps a square tube", bevel_modes=[e.identifier for e in cu.bl_rna.properties["bevel_mode"].enum_items], **evmesh(ob))
cu.bevel_mode = "ROUND"; cu.bevel_object = None

# poly spline: points are 4D (x, y, z, w)
pc = bpy.data.curves.new("poly", "CURVE")
ps = pc.splines.new("POLY")
try:
    ps.points[0].co = (1, 2, 3); three = "accepted"
except Exception as e:
    three = f"{type(e).__name__}: {e}"
E.fact("POLY/NURBS spline points have 4D co (x, y, z, w); assigning a 3-tuple raises", error=three)
ps.points.add(9)
for i, p in enumerate(ps.points):
    p.co = (math.cos(i / 10 * 2 * math.pi), math.sin(i / 10 * 2 * math.pi), 0, 1)
ps.use_cyclic_u = True
pob2 = bpy.data.objects.new("poly", pc); bpy.context.scene.collection.objects.link(pob2)
E.fact("a closed 10-point POLY circle evaluates to 10 verts and 10 edges (resolution does not apply to poly)", **evmesh(pob2))
pc.dimensions = "2D"; pc.fill_mode = "BOTH"
E.fact("2D curve with fill_mode BOTH fills the closed shape with faces", fill_modes_2d=[e.identifier for e in pc.bl_rna.properties["fill_mode"].enum_items], **evmesh(pob2))

# curve -> mesh object: data route and operator route
me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
E.fact("new_from_object(evaluated curve object) gives a mesh datablock of the evaluated curve", verts=len(me.vertices), faces=len(me.polygons))
cu.bevel_depth = 0.1
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
with bpy.context.temp_override(active_object=ob, object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
    r = list(bpy.ops.object.convert(target="MESH"))
E.fact("bpy.ops.object.convert(target='MESH') works headless with an override and replaces the curve object's data with a mesh",
       result=r, type=ob.type, verts=len(ob.data.vertices), curves_left=[c.name for c in bpy.data.curves])
E.save()
