"""The attribute API in 4.5: domains, types, colour attributes, UV maps as attributes, built-in names."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import numpy as np
import bpy
import exp
E = exp.Experiment(__file__)

A = bpy.types.AttributeGroupMesh if hasattr(bpy.types, "AttributeGroupMesh") else bpy.types.AttributeGroup
fn = A.bl_rna.functions["new"]
E.fact("mesh.attributes.new(name, type, domain): the type and domain enums in 4.5",
       group_type=A.__name__,
       types=[e.identifier for e in fn.parameters["type"].enum_items],
       domains=[e.identifier for e in fn.parameters["domain"].enum_items])

bpy.ops.mesh.primitive_cube_add()
me = bpy.context.object.data
E.fact("a primitive cube's attributes (internal names start with a dot)",
       attrs=[(a.name, a.domain, a.data_type) for a in me.attributes])

# value property per type
probe = {}
for t, d in [("FLOAT", "POINT"), ("INT", "FACE"), ("FLOAT_VECTOR", "POINT"), ("FLOAT_COLOR", "CORNER"),
             ("BYTE_COLOR", "POINT"), ("STRING", "POINT"), ("BOOLEAN", "EDGE"), ("FLOAT2", "CORNER"),
             ("INT8", "POINT"), ("INT16_2D", "CORNER"), ("INT32_2D", "EDGE"), ("QUATERNION", "POINT"), ("FLOAT4X4", "FACE")]:
    try:
        a = me.attributes.new(f"t_{t}", t, d)
        el = a.data[0]
        props = [p.identifier for p in el.bl_rna.properties if p.identifier != "rna_type"]
        probe[t] = dict(domain=d, n=len(a.data), item_props=props)
    except Exception as e:
        probe[t] = f"{type(e).__name__}: {e}"
E.fact("the property to read/write per attribute type with foreach_get/set", per_type=probe)

# round trip each numeric type through foreach_set/foreach_get with a numpy array of a given dtype
rt = {}
for t, prop, dt, k in [("FLOAT", "value", np.float32, 1), ("INT", "value", np.int32, 1), ("INT8", "value", np.int8, 1),
                       ("BOOLEAN", "value", bool, 1), ("FLOAT2", "vector", np.float32, 2), ("FLOAT_VECTOR", "vector", np.float32, 3),
                       ("FLOAT_COLOR", "color", np.float32, 4), ("BYTE_COLOR", "color", np.float32, 4), ("INT16_2D", "value", np.int16, 2),
                       ("INT16_2D", "value", np.int32, 2), ("INT32_2D", "value", np.int32, 2), ("QUATERNION", "value", np.float32, 4),
                       ("FLOAT4X4", "value", np.float32, 16)]:
    a = me.attributes[f"t_{t}"]
    n = len(a.data) * k
    src = (np.arange(n) % 2).astype(dt) if dt is bool else (np.arange(n) % 7).astype(dt)
    if t in ("FLOAT_COLOR", "BYTE_COLOR"):
        src = (np.arange(n) % 2).astype(dt)
    try:
        a.data.foreach_set(prop, src)
        back = np.empty(n, dt); a.data.foreach_get(prop, back)
        rt[f"{t}/{np.dtype(dt).name}"] = bool(np.array_equal(back, src))
    except Exception as e:
        rt[f"{t}/{np.dtype(dt).name}"] = f"{type(e).__name__}: {str(e)[:80]}"
E.fact("foreach_set then foreach_get round trip per attribute type, with the numpy dtype named (True = identical)", round_trip=rt)

# FLOAT_COLOR via foreach_set 'color'; also color_srgb
a = me.attributes["t_FLOAT_COLOR"]
cols = np.tile(np.array([1.0, 0.5, 0.0, 1.0], np.float32), len(a.data))
a.data.foreach_set("color", cols)
back = np.empty(len(a.data) * 4, np.float32); a.data.foreach_get("color", back)
srgb = list(a.data[0].color_srgb) if hasattr(a.data[0], "color_srgb") else None
E.fact("FLOAT_COLOR stores linear values in 'color' and also exposes 'color_srgb' (converted on read)",
       color0=back[:4].tolist(), color_srgb0=srgb)

# color_attributes vs attributes
ca = me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
E.fact("color_attributes.new creates a normal attribute that also appears in mesh.attributes; the first one becomes active and default (render) colour",
       in_attributes="Col" in me.attributes, color_attributes=[c.name for c in me.color_attributes],
       active_color=me.color_attributes.active_color.name if me.color_attributes.active_color else None,
       render_color_index=me.color_attributes.render_color_index, active_color_name=getattr(me.attributes, "active_color_name", None),
       default_color_name=getattr(me.attributes, "default_color_name", None))
try:
    b = me.color_attributes.new("bad", "FLOAT", "POINT"); bad = f"accepted: made {b.name} {b.data_type} {b.domain}" if b else "returned None"
except Exception as e:
    bad = f"{type(e).__name__}: {e}"
E.fact("color_attributes.new('bad', 'FLOAT', 'POINT') with a non-colour type: " + bad, listed_as_color="bad" in [c.name for c in me.color_attributes])
if "bad" in me.attributes:
    me.attributes.remove(me.attributes["bad"])
vc = getattr(me, "vertex_colors", None)
E.fact("mesh.vertex_colors (the pre-3.2 API) " + ("still exists in 4.5 and lists only BYTE_COLOR CORNER attributes" if vc is not None else "is gone in 4.5"),
       vertex_colors=[v.name for v in vc] if vc is not None else None)

# UV maps are FLOAT2 corner attributes
uv = me.uv_layers.new(name="UV2")
E.fact("a UV map is a FLOAT2 attribute on the CORNER domain; uv_layers.new adds one and uv_layers lists them",
       uv_layers=[u.name for u in me.uv_layers], attr=(me.attributes["UV2"].domain, me.attributes["UV2"].data_type),
       active=me.uv_layers.active.name, active_render=[u.name for u in me.uv_layers if u.active_render])
uvs = np.empty(len(me.loops) * 2, np.float32)
t = me.uv_layers["UVMap"].uv
me.uv_layers["UVMap"].uv.foreach_get("vector", uvs)
E.fact("uv_layers[name].uv.foreach_get('vector', a) reads UVs (the old .data[i].uv path also works)",
       first=uvs[:2].tolist(), old_path=list(me.uv_layers["UVMap"].data[0].uv))
# a FLOAT2 corner attribute made via attributes.new appears in uv_layers?
me.attributes.new("UV3", "FLOAT2", "CORNER")
E.fact("a FLOAT2 CORNER attribute made with attributes.new is listed in uv_layers too",
       uv_layers=[u.name for u in me.uv_layers])
# UV selection/pin sub-attributes
hidden_before = [a.name for a in me.attributes if a.name.startswith(".") and "UV" in a.name]
uvl = me.uv_layers["UVMap"]
uvl.vertex_selection[0].value = True
uvl.pin[0].value = True
uvl.edge_selection[0].value = True
hidden_after = [a.name for a in me.attributes if a.name.startswith(".") and "UV" in a.name]
E.fact("UV selection/pin state lives in hidden bool attributes named after the map, created only when first written",
       before=hidden_before, after=hidden_after)

# reserved / built-in names and remove
try:
    r = me.attributes.new("position", "FLOAT", "POINT"); res = f"accepted, returned {r.name if r else None}"
except Exception as e:
    res = f"{type(e).__name__}: {e}"
E.fact("attributes.new('position', 'FLOAT', 'POINT') on a mesh that has position: " + res,
       positions=[(a.name, a.data_type) for a in me.attributes if a.name.startswith("position")])
try:
    me.attributes.remove(me.attributes["position"]); rem = "accepted"
except Exception as e:
    rem = f"{type(e).__name__}: {e}"
E.fact("the built-in 'position' attribute cannot be removed", error=rem)
# material_index, sharp_face, sharp_edge, crease
for name, typ, dom in [("material_index", "INT", "FACE"), ("sharp_face", "BOOLEAN", "FACE"), ("sharp_edge", "BOOLEAN", "EDGE"),
                       ("crease_edge", "FLOAT", "EDGE"), ("crease_vert", "FLOAT", "POINT"), ("bevel_weight_edge", "FLOAT", "EDGE")]:
    if name not in me.attributes:
        me.attributes.new(name, typ, dom)
me.polygons[0].material_index = 2
mi = np.empty(len(me.polygons), np.int32); me.attributes["material_index"].data.foreach_get("value", mi)
me.edges[0].use_edge_sharp = True
se = np.empty(len(me.edges), bool); me.attributes["sharp_edge"].data.foreach_get("value", se)
E.fact("polygon.material_index and edge.use_edge_sharp are views onto the material_index and sharp_edge attributes",
       material_index=mi.tolist(), sharp_edge=se.astype(int).tolist())
E.fact("crease is stored in attributes: Mesh.edge_creases / vertex_creases return the crease_edge / crease_vert attributes",
       has_edge_creases=hasattr(me, "edge_creases"), edge_creases=me.edge_creases.name if getattr(me, "edge_creases", None) else None,
       vertex_creases=me.vertex_creases.name if getattr(me, "vertex_creases", None) else None,
       bevel_modifier_weight_names=(lambda m: (m.edge_weight, m.vertex_weight))(bpy.context.object.modifiers.new("bv", "BEVEL")),
       old_use_customdata_edge_crease=hasattr(me, "use_customdata_edge_crease"))

# (a reference kept across attributes.new calls: see attribute_stale_ref.py -- it can crash Blender)

# domain sizes
E.fact("domain sizes of a cube: POINT 8, EDGE 12, FACE 6, CORNER 24",
       sizes={d: me.attributes.domain_size(d) if hasattr(me.attributes, "domain_size") else None for d in ("POINT", "EDGE", "FACE", "CORNER")})
E.save()
