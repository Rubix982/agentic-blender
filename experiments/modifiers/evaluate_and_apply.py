"""Reading a modifier stack's result without applying it, and the ways to apply it headless (-b)."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import time
import bpy
import exp
E = exp.Experiment(__file__)


def sphere(name, loc=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=loc)
    ob = bpy.context.object; ob.name = name
    m = ob.modifiers.new("Sub", "SUBSURF"); m.levels = 2
    return ob

ob = sphere("eval")
base = len(ob.data.vertices)
dg = bpy.context.evaluated_depsgraph_get()
ev = ob.evaluated_get(dg)
E.fact("obj.evaluated_get(depsgraph).data is the evaluated mesh (modifiers applied); obj.data stays the base mesh",
       base_verts=base, evaluated_verts=len(ev.data.vertices), same_object=ev == ob, ev_is_evaluated=ev.is_evaluated)

t = time.perf_counter(); tm = ev.to_mesh(); t_to = time.perf_counter() - t
n_to = len(tm.vertices)
in_data = any(m == tm for m in bpy.data.meshes)
ev.to_mesh_clear()
E.fact("evaluated.to_mesh() gives a temporary mesh not in bpy.data; release it with to_mesh_clear()",
       verts=n_to, in_bpy_data=in_data, ms=round(t_to * 1000, 2))
t = time.perf_counter(); nm = bpy.data.meshes.new_from_object(ev); t_nfo = time.perf_counter() - t
E.fact("bpy.data.meshes.new_from_object(evaluated_obj) gives a real mesh datablock with modifiers applied (0 users until assigned)",
       verts=len(nm.vertices), in_bpy_data=any(m == nm for m in bpy.data.meshes), users=nm.users, ms=round(t_nfo * 1000, 2))
nm2 = bpy.data.meshes.new_from_object(ob)
E.fact("new_from_object(original object) " + ("also applies the modifiers" if len(nm2.vertices) == len(nm.vertices) else "returns the BASE mesh without modifiers: pass the evaluated object"),
       verts_from_original=len(nm2.vertices), verts_from_evaluated=len(nm.vertices))
nm3 = bpy.data.meshes.new_from_object(ob, preserve_all_data_layers=True, depsgraph=dg)
E.fact("new_from_object accepts preserve_all_data_layers and depsgraph keywords",
       params=[p.identifier for p in bpy.types.BlendDataMeshes.bl_rna.functions["new_from_object"].parameters])

# 'apply' via data: swap mesh, clear modifiers
old = ob.data
ob.modifiers.clear()
ob.data = nm
E.fact("swapping obj.data for the new_from_object mesh and clearing the modifiers is an apply that needs no context",
       verts=len(ob.data.vertices), modifiers=len(ob.modifiers), old_mesh_users=old.users)

# operator route
ob2 = sphere("op_active")                       # active, selected
t = time.perf_counter()
try:
    r = list(bpy.ops.object.modifier_apply(modifier="Sub")); err = None
except Exception as e:
    r, err = None, f"{type(e).__name__}: {str(e).strip()}"
t_op = time.perf_counter() - t
E.fact("bpy.ops.object.modifier_apply(modifier=name) works headless without any override when the object is the active one",
       result=r, error=err, verts=len(ob2.data.vertices), ms=round(t_op * 1000, 2))

ob3 = sphere("op_not_active", loc=(3, 0, 0))
ob4 = sphere("other_active", loc=(6, 0, 0))     # now ob4 is active
try:
    r = list(bpy.ops.object.modifier_apply(modifier="Sub")); err = None
except Exception as e:
    r, err = None, f"{type(e).__name__}: {str(e).strip()}"
E.fact("without an override, modifier_apply acts on the ACTIVE object, not the one you meant",
       result=r, error=err, intended_verts=len(ob3.data.vertices), active_verts=len(ob4.data.vertices))

ob5 = sphere("override", loc=(9, 0, 0))
bpy.context.view_layer.objects.active = ob4
try:
    with bpy.context.temp_override(object=ob5, active_object=ob5):
        r = list(bpy.ops.object.modifier_apply(modifier="Sub")); err = None
except Exception as e:
    r, err = None, f"{type(e).__name__}: {str(e).strip()}"
E.fact("with bpy.context.temp_override(object=ob, active_object=ob), modifier_apply applies on ob even when another object is active",
       result=r, error=err, verts=len(ob5.data.vertices), modifiers_left=[m.name for m in ob5.modifiers])

# old override style: dict as first positional argument
ob6 = sphere("dict_override", loc=(12, 0, 0))
try:
    ctx = bpy.context.copy(); ctx["object"] = ob6
    r = list(bpy.ops.object.modifier_apply(ctx, modifier="Sub")); err = None
except Exception as e:
    r, err = None, f"{type(e).__name__}: {str(e).strip()}"
E.fact("the pre-3.2 style override (a context dict as the first positional argument) fails in 4.5", result=r, error=err)

# multi-user mesh
ob7 = sphere("multi", loc=(15, 0, 0))
ob8 = ob7.copy(); bpy.context.collection.objects.link(ob8)
try:
    with bpy.context.temp_override(object=ob7, active_object=ob7):
        r = list(bpy.ops.object.modifier_apply(modifier="Sub")); err = None
except Exception as e:
    r, err = None, f"{type(e).__name__}: {str(e).strip()}"
E.fact("modifier_apply on an object whose mesh is shared by another object", result=r, error=err, verts=len(ob7.data.vertices),
       shared_after=ob7.data == ob8.data)

# shape keys
ob9 = sphere("shapekeys", loc=(18, 0, 0))
ob9.shape_key_add(name="Basis"); ob9.shape_key_add(name="Key1")
try:
    with bpy.context.temp_override(object=ob9, active_object=ob9):
        r = list(bpy.ops.object.modifier_apply(modifier="Sub")); err = None
except Exception as e:
    r, err = None, f"{type(e).__name__}: {str(e).strip()}"
E.fact("modifier_apply on a mesh with shape keys", result=r, error=err, verts=len(ob9.data.vertices))

# timing at size: new_from_object vs operator on a level-3 subsurf of a 32x16 sphere
for lvl in (3,):
    a = sphere("tA", loc=(0, 5, 0)); a.modifiers["Sub"].levels = lvl
    b = sphere("tB", loc=(3, 5, 0)); b.modifiers["Sub"].levels = lvl
    dg = bpy.context.evaluated_depsgraph_get()
    t = time.perf_counter(); m = bpy.data.meshes.new_from_object(a.evaluated_get(dg)); a.modifiers.clear(); a.data = m; t1 = time.perf_counter() - t
    t = time.perf_counter()
    with bpy.context.temp_override(object=b, active_object=b):
        bpy.ops.object.modifier_apply(modifier="Sub")
    t2 = time.perf_counter() - t
    E.fact(f"applying a level-{lvl} subsurf ({len(a.data.vertices)} verts): new_from_object + swap {t1*1000:.0f} ms, modifier_apply {t2*1000:.0f} ms (depsgraph already evaluated for the first)",
           data_route_ms=round(t1 * 1000, 1), operator_ms=round(t2 * 1000, 1), verts=len(a.data.vertices), same=len(a.data.vertices) == len(b.data.vertices))
E.save()
