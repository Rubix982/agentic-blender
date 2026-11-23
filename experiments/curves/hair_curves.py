"""The Curves object type (hair curves, 3.3+) from Python: creating curves, writing positions, and how it differs from Curve."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import numpy as np
import bpy
import exp
E = exp.Experiment(__file__)

E.fact("the new curves type lives in bpy.data.hair_curves (type Curves), separate from bpy.data.curves (type Curve)",
       has_hair_curves=hasattr(bpy.data, "hair_curves"), curves_type=bpy.types.Curves.__name__)
hc = bpy.data.hair_curves.new("hair")
E.fact("a new Curves datablock is empty", curves=len(hc.curves), points=len(hc.points), attrs=[a.name for a in hc.attributes])
fns = [f.identifier for f in bpy.types.Curves.bl_rna.functions]
E.fact("Curves functions in 4.5", functions=fns)
hc.add_curves([4, 4, 4])   # three curves of 4 points
E.fact("add_curves([sizes]) adds curves with the given point counts", curves=len(hc.curves), points=len(hc.points),
       attrs=[(a.name, a.domain, a.data_type) for a in hc.attributes])
pos = np.zeros((12, 3), np.float32)
for c in range(3):
    pos[c * 4:(c + 1) * 4, 0] = c * 0.1
    pos[c * 4:(c + 1) * 4, 2] = np.linspace(0, 1, 4)
hc.attributes["position"].data.foreach_set("vector", pos.ravel())
E.fact("positions are the 'position' POINT attribute; curve offsets give each curve's first point",
       offsets=[c.first_point_index for c in hc.curves], z_last=float(hc.points[3].position.z))
ob = bpy.data.objects.new("hair", hc); bpy.context.scene.collection.objects.link(ob)
E.fact("an object made from it has type CURVES", type=ob.type)
# radius attribute
r = hc.attributes.get("radius") or hc.attributes.new("radius", "FLOAT", "POINT")
r.data.foreach_set("value", np.full(12, 0.01, np.float32))
E.fact("radius is a FLOAT POINT attribute", radius0=hc.points[0].radius)
# curve type
before = [a.name for a in hc.attributes]
sig = [p.identifier for p in bpy.types.Curves.bl_rna.functions["set_types"].parameters]
hc.set_types(type="POLY")
ct = hc.attributes.get("curve_type")
E.fact("there is no curve_type attribute until set_types(type=...) writes one (absent means Catmull-Rom)",
       attrs_before=before, set_types_params=sig, after=(ct.domain, ct.data_type, ct.data[0].value) if ct else None)
# convert Curves -> mesh via new_from_object
try:
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg)); res = f"{len(me.vertices)} verts, {len(me.edges)} edges"
except Exception as e:
    res = f"{type(e).__name__}: {e}"
E.fact("new_from_object on a Curves object", result=res)
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
try:
    with bpy.context.temp_override(active_object=ob, object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
        r = list(bpy.ops.object.convert(target="MESH"))
    res2 = f"{r}, type now {bpy.data.objects['hair'].type}"
    o2 = bpy.data.objects["hair"]
    if o2.type == "MESH":
        res2 += f", {len(o2.data.vertices)} verts, {len(o2.data.edges)} edges"
except Exception as e:
    res2 = f"{type(e).__name__}: {e}"
E.fact("bpy.ops.object.convert(target='MESH') on a Curves object", result=res2)
E.save()
