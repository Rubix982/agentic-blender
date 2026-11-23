"""Smooth shading and normals in 4.5: what replaced auto smooth, and what each route writes to the mesh."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import math
import numpy as np
import bpy
import exp
E = exp.Experiment(__file__)


def cyl(name):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=1, depth=2)
    ob = bpy.context.object; ob.name = name
    return ob


def attr_names(me):
    return sorted(a.name for a in me.attributes if not a.name.startswith("."))


def count_true(me, name):
    a = me.attributes.get(name)
    if a is None:
        return None
    v = np.empty(len(a.data), bool); a.data.foreach_get("value", v)
    return int(v.sum())


ob = cyl("plain")
me = ob.data
# 1. old API is gone
gone = {}
for attr in ("use_auto_smooth", "auto_smooth_angle", "calc_normals_split", "free_normals_split", "create_normals_split"):
    gone[attr] = hasattr(me, attr)
E.fact("use_auto_smooth, auto_smooth_angle, calc_normals_split, free_normals_split and create_normals_split no longer exist on Mesh",
       present=gone)
try:
    me.use_auto_smooth = True; err = "accepted"
except Exception as e:
    err = f"{type(e).__name__}: {e}"
E.fact("setting mesh.use_auto_smooth raises", error=err)

E.fact("a fresh primitive cylinder is flat shaded and stores that as a boolean face attribute sharp_face",
       attrs=attr_names(me), sharp_face_true=count_true(me, "sharp_face"), faces=len(me.polygons),
       use_smooth_face0=me.polygons[0].use_smooth)

# 2. mesh.shade_smooth() / shade_flat()
me.shade_smooth()
E.fact("mesh.shade_smooth() removes the sharp_face attribute (all faces smooth)", attrs=attr_names(me),
       sharp_face_true=count_true(me, "sharp_face"), use_smooth_face0=me.polygons[0].use_smooth)
me.shade_flat()
E.fact("mesh.shade_flat() writes sharp_face True on every face", sharp_face_true=count_true(me, "sharp_face"))
me.shade_smooth()
me.polygons[0].use_smooth = False
E.fact("polygon.use_smooth = False on a smooth mesh writes sharp_face (True on that one face)", sharp_face_true=count_true(me, "sharp_face"))
me.shade_flat()
import inspect
def sig(f):
    try:
        return str(inspect.signature(f))
    except Exception:
        return [p.identifier for p in bpy.types.Mesh.bl_rna.functions[f.__name__].parameters] if f.__name__ in bpy.types.Mesh.bl_rna.functions else (f.__doc__ or "")[:200]
E.fact("Mesh.shade_smooth and set_sharp_from_angle parameters in 4.5",
       shade_smooth=sig(bpy.types.Mesh.shade_smooth), shade_smooth_doc=(bpy.types.Mesh.shade_smooth.__doc__ or "")[:300],
       shade_flat=sig(bpy.types.Mesh.shade_flat), in_rna=[f for f in ("shade_smooth", "shade_flat", "set_sharp_from_angle") if f in bpy.types.Mesh.bl_rna.functions],
       set_sharp_from_angle=[(p.identifier, getattr(p, "default", None)) for p in bpy.types.Mesh.bl_rna.functions["set_sharp_from_angle"].parameters])

# 3. set_sharp_from_angle: the data-level replacement of auto smooth
me.shade_smooth()
me.set_sharp_from_angle(angle=math.radians(30))
E.fact("mesh.set_sharp_from_angle(angle=30 deg) on a smooth 16-sided cylinder marks the 32 rim edges sharp via the sharp_edge attribute",
       attrs=attr_names(me), sharp_edge_true=count_true(me, "sharp_edge"), edges=len(me.edges))

# corner normals: split along sharp edges
cn = np.empty(len(me.loops) * 3, np.float32)
me.corner_normals.foreach_get("vector", cn)
cn = cn.reshape(-1, 3)
uniq = len(np.unique(np.round(cn, 4), axis=0))
vn = np.empty(len(me.vertices) * 3, np.float32); me.vertex_normals.foreach_get("vector", vn)
E.fact("after set_sharp_from_angle on the 16-sided cylinder, corner_normals has one normal per corner (96) with 18 distinct directions (16 sides + 2 caps), and normals_domain is CORNER",
       loops=len(me.loops), distinct_corner_normals=uniq, normals_domain=me.normals_domain,
       has_corner_normals_attr=hasattr(me, "corner_normals"))

# 4. operator shade_smooth_by_angle (object mode)
ob2 = cyl("byangle")
ops = {}
try:
    r = bpy.ops.object.shade_smooth_by_angle(angle=math.radians(30), keep_sharp_edges=True)
    ops["shade_smooth_by_angle"] = list(r)
except Exception as e:
    ops["shade_smooth_by_angle"] = f"{type(e).__name__}: {e}"
E.fact("bpy.ops.object.shade_smooth_by_angle runs headless on the active object and writes sharp_edge / removes sharp_face (no modifier)",
       result=ops["shade_smooth_by_angle"], attrs=attr_names(ob2.data), sharp_edge_true=count_true(ob2.data, "sharp_edge"),
       sharp_face_true=count_true(ob2.data, "sharp_face"), modifiers=[m.type for m in ob2.modifiers])

# 5. shade_auto_smooth: adds the "Smooth by Angle" node-group modifier -- in the UI. Headless it needs the asset library.
ob3 = cyl("auto")
import time
results = []
for _ in range(3):
    results.append(list(bpy.ops.object.shade_auto_smooth(use_auto_smooth=True, angle=math.radians(30))))
    if "FINISHED" in results[-1]:
        break
    time.sleep(0.5)
E.fact("headless (-b), bpy.ops.object.shade_auto_smooth returns CANCELLED with the warning 'Asset loading is unfinished', and adds no modifier, even when retried",
       results=results, modifiers=[m.name for m in ob3.modifiers])

# the route that works headless: append the node group from the bundled asset file and add a NODES modifier
path = os.path.join(bpy.utils.system_resource("DATAFILES"), "assets", "geometry_nodes", "smooth_by_angle.blend")
with bpy.data.libraries.load(path, link=False) as (src, dst):
    groups_in_file = list(src.node_groups)
    dst.node_groups = ["Smooth by Angle"]
ng = bpy.data.node_groups["Smooth by Angle"]
m = ob3.modifiers.new("Smooth by Angle", "NODES")
m.node_group = ng
inputs = [(i.identifier, i.name, i.socket_type) for i in ng.interface.items_tree if getattr(i, "in_out", None) == "INPUT"]
ang_id = next(i[0] for i in inputs if i[1] == "Angle")
default_angle = m[ang_id]
m[ang_id] = math.radians(30)
E.fact("appending 'Smooth by Angle' from datafiles/assets/geometry_nodes/smooth_by_angle.blend and assigning it to a NODES modifier works headless",
       file=os.path.relpath(path, bpy.utils.system_resource("DATAFILES")), groups_in_file=groups_in_file, inputs=inputs,
       default_angle_deg=round(math.degrees(default_angle), 3), is_asset=ng.asset_data is not None)
dg = bpy.context.evaluated_depsgraph_get()
ev = ob3.evaluated_get(dg).data
e_flat = count_true(ev, "sharp_edge")
ign_id = next(i[0] for i in inputs if i[1] == "Ignore Sharpness")
m[ign_id] = True
ob3.data.update()
dg = bpy.context.evaluated_depsgraph_get()
e_ignore = count_true(ob3.evaluated_get(dg).data, "sharp_edge")
m[ign_id] = False
ob3.data.shade_smooth()
dg = bpy.context.evaluated_depsgraph_get()
ev2 = ob3.evaluated_get(dg).data
e_smooth = count_true(ev2, "sharp_edge")
E.fact(f"Smooth by Angle (30 deg) on a 16-sided cylinder marks {e_flat} of 48 edges sharp when the mesh was flat shaded (existing flat faces are kept sharp), "
       f"{e_ignore} with Ignore Sharpness on, and {e_smooth} when the mesh was shade_smooth()ed first; the original mesh's attributes are not written",
       flat_input=e_flat, ignore_sharpness=e_ignore, smooth_input=e_smooth, eval_sharp_face_true=count_true(ev2, "sharp_face"),
       orig_sharp_edge_true=count_true(ob3.data, "sharp_edge"))

# 6. custom normals
ob4 = cyl("custom")
me4 = ob4.data
me4.shade_smooth()
up = [(0.0, 0.0, 1.0)] * len(me4.loops)
me4.normals_split_custom_set(up)
cn4 = np.empty(len(me4.loops) * 3, np.float32); me4.corner_normals.foreach_get("vector", cn4)
cnattr = me4.attributes.get("custom_normal")
E.fact("normals_split_custom_set works without any auto smooth flag in 4.5; all corner normals then point +Z, and the custom normals live in an attribute 'custom_normal'",
       custom_normal_domain=cnattr.domain if cnattr else None, custom_normal_type=cnattr.data_type if cnattr else None,
       sharp_edge_true=count_true(me4, "sharp_edge"),
       has_custom_normals=me4.has_custom_normals, all_up=bool(np.allclose(cn4.reshape(-1, 3), [0, 0, 1], atol=1e-3)),
       attrs=attr_names(me4), normals_domain=me4.normals_domain)
me4.normals_split_custom_set_from_vertices([(1.0, 0.0, 0.0)] * len(me4.vertices))
cn4b = np.empty(len(me4.loops) * 3, np.float32); me4.corner_normals.foreach_get("vector", cn4b)
E.fact("normals_split_custom_set_from_vertices sets one normal per vertex", all_x=bool(np.allclose(cn4b.reshape(-1, 3), [1, 0, 0], atol=1e-3)))
# clear
try:
    with bpy.context.temp_override(object=ob4, active_object=ob4, selected_objects=[ob4], selected_editable_objects=[ob4]):
        r = bpy.ops.mesh.customdata_custom_splitnormals_clear()
    clr = list(r)
except Exception as e:
    clr = f"{type(e).__name__}: {e}"
E.fact("custom normals are cleared with bpy.ops.mesh.customdata_custom_splitnormals_clear() (object mode, active object)",
       result=clr, has_custom_normals_after=me4.has_custom_normals)
# 7. normals of a flat face
me6 = cyl("default_angle").data; me6.shade_smooth(); me6.set_sharp_from_angle()
E.fact("set_sharp_from_angle() with no argument uses angle=pi (180 deg) and marks no edge sharp", sharp_edge_true=count_true(me6, "sharp_edge"))
E.fact("normals_domain is FACE for a flat-shaded mesh, POINT for smooth with no sharp edges, CORNER with sharp edges or custom normals",
       flat=cyl("f").data.normals_domain)
me5 = bpy.context.object.data; me5.shade_smooth(); d_smooth = me5.normals_domain
me5.set_sharp_from_angle(angle=math.radians(30)); d_sharp = me5.normals_domain
E.fact("normals_domain values seen", smooth=d_smooth, smooth_with_sharp_edges=d_sharp)
E.save()
