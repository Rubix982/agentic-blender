"""OBJ / PLY / STL import in 4.5: the C++ operator names, a round trip of a known mesh, and what the old names do."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import time
import bpy
import exp
E = exp.Experiment(__file__)

names = {k: hasattr(bpy.ops.wm, k) for k in ("obj_import", "obj_export", "ply_import", "ply_export", "stl_import", "stl_export", "fbx_import")}
old = {}
for mod, op in (("import_scene", "obj"), ("export_scene", "obj"), ("import_mesh", "ply"), ("import_mesh", "stl"), ("export_mesh", "stl")):
    try:
        getattr(getattr(bpy.ops, mod), op).get_rna_type(); old[f"{mod}.{op}"] = "exists"
    except Exception as e:
        old[f"{mod}.{op}"] = f"{type(e).__name__}"
E.fact("4.5 has the C++ importers/exporters under bpy.ops.wm.*; the old Python add-on operator names are gone", wm=names, old=old)

bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8)
src = bpy.context.object
nv, nf = len(src.data.vertices), len(src.data.polygons)
results = {}
for fmt in ("obj", "ply", "stl"):
    path = E.out(f"sphere.{fmt}")
    exp_op = getattr(bpy.ops.wm, f"{fmt}_export")
    imp_op = getattr(bpy.ops.wm, f"{fmt}_import")
    bpy.ops.object.select_all(action="DESELECT"); src.select_set(True); bpy.context.view_layer.objects.active = src
    kw = dict(filepath=path)
    if fmt == "obj":
        kw.update(export_selected_objects=True, export_materials=False)
    elif fmt in ("ply", "stl"):
        kw.update(export_selected_objects=True)
    t = time.perf_counter(); r1 = list(exp_op(**kw)); t_exp = time.perf_counter() - t
    before = set(bpy.data.objects)
    t = time.perf_counter(); r2 = list(imp_op(filepath=path)); t_imp = time.perf_counter() - t
    new = [o for o in bpy.data.objects if o not in before]
    o = new[0] if new else None
    bpy.context.view_layer.update()
    import numpy as np
    def wbox(ob):
        w = np.array([tuple(ob.matrix_world @ v.co) for v in ob.data.vertices]); return [round(float(x), 3) for x in (*w.min(0), *w.max(0))]
    same_world_box = (wbox(o) == wbox(src)) if o else None
    results[fmt] = dict(export=r1, import_=r2, new_objects=[x.name for x in new], verts=len(o.data.vertices) if o else None,
                        faces=len(o.data.polygons) if o else None, same_world_bbox=same_world_box, rotation_deg=[round(a * 57.2958, 1) for a in o.rotation_euler] if o else None,
                        selected_after=[x.name for x in bpy.context.selected_objects], export_ms=round(t_exp * 1000, 1), import_ms=round(t_imp * 1000, 1),
                        size_kb=round(os.path.getsize(path) / 1024, 1))
    for x in new:
        bpy.data.objects.remove(x)
    os.remove(path)
E.fact(f"round trip of a 16x8 UV sphere ({nv} verts, {nf} faces) through each format", by_format=results)
E.fact("import operator options", obj=[p.identifier for p in bpy.ops.wm.obj_import.get_rna_type().properties if p.identifier not in ("rna_type",) and not p.identifier.startswith("filter")],
       stl=[p.identifier for p in bpy.ops.wm.stl_import.get_rna_type().properties if not p.identifier.startswith("filter") and p.identifier != "rna_type"],
       ply=[p.identifier for p in bpy.ops.wm.ply_import.get_rna_type().properties if not p.identifier.startswith("filter") and p.identifier != "rna_type"])
E.save()
