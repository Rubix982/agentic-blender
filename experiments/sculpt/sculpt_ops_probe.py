"""Which sculpt-mode operations run headless (-b) in 4.5, and what they need. Each probe runs in its own Blender process,
one after another, because some of them crash Blender outright: the mesh filter with and without an undo step pushed,
every mesh filter type, a mask written as data, the cloth filter, sample_detail_size, dyntopo with detail flood fill,
voxel and QuadriFlow remesh, Multires subdivide and apply, the mask flood fill, and a brush stroke given as data.

Run with the system Python (it starts Blender itself):  python3 experiments/sculpt/sculpt_ops_probe.py
Writes experiments/sculpt/results/sculpt_ops_probe.json.
"""
import datetime
import json
import os
import platform
import subprocess
import sys
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from run import blender  # noqa: E402

B = blender()
TMP = tempfile.mkdtemp(prefix="bfg-sculpt-")
facts, data = [], {}
t_all = time.time()


def fact(sentence, **numbers):
    facts.append(dict(fact=sentence, **numbers))
    print("FACT", sentence, numbers, flush=True)


PRE = r'''
import bpy, bmesh, json, time
import numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
OUT = {}
def sphere(name="S", u=64, v=32):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    return ob
def co(ob):
    me = ob.data; a = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", a); return a.reshape(-1, 3)
def err(fn):
    try:
        return str(fn())
    except Exception as e:
        return f"{type(e).__name__}: {str(e).strip()[:200]}"
def moved(a, b):
    if a.shape != b.shape:
        return dict(moved_max=None, moved_count=None)
    d = np.linalg.norm(a - b, axis=1)
    return dict(moved_max=round(float(d.max()), 5), moved_count=int((d > 1e-6).sum()))
def view3d():
    win = bpy.context.window_manager.windows[0]
    area = next(a for a in win.screen.areas if a.type == "VIEW_3D")
    region = next(r for r in area.regions if r.type == "WINDOW")
    return dict(window=win, area=area, region=region)
ob = sphere()
OUT["undo_steps_pref"] = bpy.context.preferences.edit.undo_steps
'''
POST = r'''
if bpy.context.object and bpy.context.object.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")
print("RESULT " + json.dumps(OUT, default=str), flush=True)
'''

PROBES = {
    "mesh_filter, no undo push": r'''
before = co(ob)
bpy.ops.object.mode_set(mode="SCULPT")
print("REACHED", flush=True)
OUT["ret"] = err(lambda: bpy.ops.sculpt.mesh_filter(type="INFLATE", strength=0.5))
bpy.ops.object.mode_set(mode="OBJECT"); OUT.update(moved(before, co(ob)))
''',
    "mesh_filter, undo push after mode_set only": r'''
before = co(ob)
bpy.ops.object.mode_set(mode="SCULPT"); bpy.ops.ed.undo_push()
print("REACHED", flush=True)
OUT["ret"] = err(lambda: bpy.ops.sculpt.mesh_filter(type="INFLATE", strength=0.5))
bpy.ops.object.mode_set(mode="OBJECT"); OUT.update(moved(before, co(ob)))
''',
    "mesh_filter, undo push before mode_set only": r'''
before = co(ob)
bpy.ops.ed.undo_push(); bpy.ops.object.mode_set(mode="SCULPT")
print("REACHED", flush=True)
OUT["ret"] = err(lambda: bpy.ops.sculpt.mesh_filter(type="INFLATE", strength=0.5))
bpy.ops.object.mode_set(mode="OBJECT"); OUT.update(moved(before, co(ob)))
''',
    "mesh_filter, every type, undo push before and after": r'''
res = {}
for t in ("SMOOTH", "SCALE", "INFLATE", "SPHERE", "RANDOM", "RELAX", "SURFACE_SMOOTH", "SHARPEN", "ENHANCE_DETAILS",
          "ERASE_DISPLACEMENT", "RELAX_FACE_SETS"):
    before = co(ob)
    bpy.ops.ed.undo_push(); bpy.ops.object.mode_set(mode="SCULPT"); bpy.ops.ed.undo_push()
    t0 = time.time()
    r = err(lambda: bpy.ops.sculpt.mesh_filter(type=t, strength=0.5))
    dt = round(time.time() - t0, 4)
    bpy.ops.object.mode_set(mode="OBJECT")
    res[t] = dict(ret=r, seconds=dt, **moved(before, co(ob)))
OUT["types"] = res
OUT["verts"] = len(ob.data.vertices)
''',
    "mesh_filter, mask written as data": r'''
me = ob.data
z = co(ob)[:, 2]
m = me.attributes.new(".sculpt_mask", "FLOAT", "POINT")
m.data.foreach_set("value", (z > 0).astype(np.float32))
before = co(ob)
bpy.ops.ed.undo_push(); bpy.ops.object.mode_set(mode="SCULPT"); bpy.ops.ed.undo_push()
OUT["ret"] = err(lambda: bpy.ops.sculpt.mesh_filter(type="INFLATE", strength=0.5))
bpy.ops.object.mode_set(mode="OBJECT")
d = np.linalg.norm(co(ob) - before, axis=1)
OUT["moved_masked_top"] = int((d[z > 0] > 1e-6).sum()); OUT["top"] = int((z > 0).sum())
OUT["moved_unmasked_bottom"] = int((d[z <= 0] > 1e-6).sum()); OUT["bottom"] = int((z <= 0).sum())
''',
    "mask_flood_fill": r'''
bpy.ops.ed.undo_push(); bpy.ops.object.mode_set(mode="SCULPT"); bpy.ops.ed.undo_push()
OUT["ret"] = err(lambda: bpy.ops.paint.mask_flood_fill(mode="VALUE", value=0.75))
bpy.ops.object.mode_set(mode="OBJECT")
a = ob.data.attributes.get(".sculpt_mask")
if a:
    v = np.empty(len(a.data), np.float32); a.data.foreach_get("value", v)
    OUT["mask_min"], OUT["mask_max"], OUT["domain"], OUT["type"] = float(v.min()), float(v.max()), a.domain, a.data_type
else:
    OUT["mask"] = None
''',
    "cloth_filter, undo push": r'''
before = co(ob)
bpy.ops.ed.undo_push(); bpy.ops.object.mode_set(mode="SCULPT"); bpy.ops.ed.undo_push()
print("REACHED", flush=True)
OUT["ret_default"] = err(lambda: bpy.ops.sculpt.cloth_filter(type="GRAVITY", strength=1.0))
OUT["ret_exec"] = err(lambda: bpy.ops.sculpt.cloth_filter("EXEC_DEFAULT", type="GRAVITY", strength=1.0))
with bpy.context.temp_override(**view3d()):
    OUT["ret_view3d"] = err(lambda: bpy.ops.sculpt.cloth_filter(type="GRAVITY", strength=1.0, iteration_count=20))
bpy.ops.object.mode_set(mode="OBJECT"); OUT.update(moved(before, co(ob)))
''',
    "sample_detail_size": r'''
bpy.ops.ed.undo_push(); bpy.ops.object.mode_set(mode="SCULPT"); bpy.ops.ed.undo_push()
ts = bpy.context.scene.tool_settings.sculpt
OUT["detail_before"] = ts.constant_detail_resolution
OUT["ret_plain"] = err(lambda: bpy.ops.sculpt.sample_detail_size(location=(100, 100), mode="DYNTOPO"))
ov = view3d()
w, h = ov["region"].width, ov["region"].height
OUT["region_size"] = [w, h]
with bpy.context.temp_override(**ov):
    OUT["ret_view3d"] = err(lambda: bpy.ops.sculpt.sample_detail_size(location=(w // 2, h // 2), mode="DYNTOPO"))
    OUT["view_all"] = err(lambda: bpy.ops.view3d.view_all())
    OUT["ret_view3d_after_view_all"] = err(lambda: bpy.ops.sculpt.sample_detail_size(location=(w // 2, h // 2), mode="DYNTOPO"))
OUT["detail_after"] = ts.constant_detail_resolution
''',
    "dyntopo and detail_flood_fill": r'''
f0 = len(ob.data.polygons)
bpy.ops.ed.undo_push(); bpy.ops.object.mode_set(mode="SCULPT"); bpy.ops.ed.undo_push()
OUT["toggle"] = err(lambda: bpy.ops.sculpt.dynamic_topology_toggle())
OUT["use_dynamic_topology_sculpting"] = ob.use_dynamic_topology_sculpting
ts = bpy.context.scene.tool_settings.sculpt
OUT["detail_type_default"] = ts.detail_type_method
ts.detail_type_method = "CONSTANT"; ts.constant_detail_resolution = 4.0
t0 = time.time()
OUT["flood"] = err(lambda: bpy.ops.sculpt.detail_flood_fill())
OUT["flood_seconds"] = round(time.time() - t0, 3)
OUT["toggle_off"] = err(lambda: bpy.ops.sculpt.dynamic_topology_toggle())
bpy.ops.object.mode_set(mode="OBJECT")
OUT["faces_before"], OUT["faces_after"] = f0, len(ob.data.polygons)
OUT["tris_after"] = int(sum(1 for p in ob.data.polygons if len(p.vertices) == 3))
''',
    "voxel_remesh and quadriflow": r'''
me = ob.data
OUT["voxel_size_default"] = me.remesh_voxel_size
me.remesh_voxel_size = 0.05
f0 = len(me.polygons)
bpy.ops.ed.undo_push(); bpy.ops.object.mode_set(mode="SCULPT"); bpy.ops.ed.undo_push()
t0 = time.time(); OUT["voxel_in_sculpt"] = err(lambda: bpy.ops.object.voxel_remesh()); OUT["voxel_seconds"] = round(time.time() - t0, 3)
bpy.ops.object.mode_set(mode="OBJECT")
OUT["faces_before"], OUT["faces_after_voxel_0.05"] = f0, len(ob.data.polygons)
ob.data.remesh_voxel_size = 0.1
t0 = time.time(); OUT["voxel_in_object"] = err(lambda: bpy.ops.object.voxel_remesh()); OUT["voxel_obj_seconds"] = round(time.time() - t0, 3)
OUT["faces_after_voxel_0.1"] = len(ob.data.polygons)
t0 = time.time()
OUT["quadriflow"] = err(lambda: bpy.ops.object.quadriflow_remesh(target_faces=500, mode="FACES"))
OUT["quadriflow_seconds"] = round(time.time() - t0, 3)
OUT["faces_after_quadriflow"] = len(ob.data.polygons)
OUT["quads_after_quadriflow"] = int(sum(1 for p in ob.data.polygons if len(p.vertices) == 4))
''',
    "multires subdivide, sculpt, apply": r'''
ob2 = sphere("M", 16, 8)
f0 = len(ob2.data.polygons)
mr = ob2.modifiers.new("Multires", "MULTIRES")
OUT["sub1"] = err(lambda: bpy.ops.object.multires_subdivide(modifier="Multires", mode="CATMULL_CLARK"))
OUT["sub2"] = err(lambda: bpy.ops.object.multires_subdivide(modifier="Multires", mode="CATMULL_CLARK"))
OUT["levels"] = [mr.levels, mr.sculpt_levels, mr.render_levels, mr.total_levels]
dg = bpy.context.evaluated_depsgraph_get()
ev = ob2.evaluated_get(dg).data
OUT["faces_base"], OUT["faces_evaluated"] = f0, len(ev.polygons)
def evco():
    dg = bpy.context.evaluated_depsgraph_get(); m = ob2.evaluated_get(dg).data
    a = np.empty(len(m.vertices) * 3, np.float32); m.vertices.foreach_get("co", a); return a.reshape(-1, 3)
before = evco()
bpy.ops.ed.undo_push(); bpy.ops.object.mode_set(mode="SCULPT"); bpy.ops.ed.undo_push()
OUT["filter_on_multires"] = err(lambda: bpy.ops.sculpt.mesh_filter(type="INFLATE", strength=0.5))
bpy.ops.object.mode_set(mode="OBJECT")
OUT["filter_moved"] = moved(before, evco())
OUT["apply"] = err(lambda: bpy.ops.object.modifier_apply(modifier="Multires"))
OUT["faces_after_apply"] = len(ob2.data.polygons)
OUT["modifiers_left"] = [m.name for m in ob2.modifiers]
''',
    "brush_stroke as data": r'''
before = co(ob)
bpy.ops.ed.undo_push(); bpy.ops.object.mode_set(mode="SCULPT"); bpy.ops.ed.undo_push()
stroke = [dict(name="", location=(0, -1, 0), mouse=(100 + 5 * i, 100), mouse_event=(100 + 5 * i, 100), pressure=1.0,
               size=50, x_tilt=0, y_tilt=0, time=i * 0.01, is_start=(i == 0)) for i in range(10)]
OUT["ret_plain"] = err(lambda: bpy.ops.sculpt.brush_stroke(stroke=stroke, mode="NORMAL"))
with bpy.context.temp_override(**view3d()):
    OUT["ret_view3d"] = err(lambda: bpy.ops.sculpt.brush_stroke(stroke=stroke, mode="NORMAL"))
bpy.ops.object.mode_set(mode="OBJECT"); OUT.update(moved(before, co(ob)))
d = np.linalg.norm(co(ob) - before, axis=1)
OUT["moved_centroid"] = [round(float(x), 3) for x in before[d > 1e-6].mean(axis=0)] if (d > 1e-6).any() else None
''',
    "vertex_paint stroke as data": r'''
me = ob.data
ca = me.color_attributes.new("Col", "BYTE_COLOR", "POINT")
me.color_attributes.active_color = ca
OUT["new_attribute_value"] = list(ca.data[0].color)
ca.data.foreach_set("color", np.tile(np.array([0, 0, 0, 1], np.float32), len(ca.data)))
ov = view3d()
cx, cy = ov["region"].width // 2, ov["region"].height // 2
with bpy.context.temp_override(**ov):
    OUT["view_all"] = err(lambda: bpy.ops.view3d.view_all())
stroke = [dict(name="", location=(0, 0, 0), mouse=(cx - 20 + 4 * i, cy), mouse_event=(cx - 20 + 4 * i, cy), pressure=1.0,
               size=60, x_tilt=0, y_tilt=0, time=i * 0.01, is_start=(i == 0)) for i in range(10)]
bpy.ops.ed.undo_push(); bpy.ops.object.mode_set(mode="VERTEX_PAINT"); bpy.ops.ed.undo_push()
vp = bpy.context.scene.tool_settings.vertex_paint
OUT["brush"] = vp.brush.name if vp.brush else None
if vp.brush:
    OUT["brush_color"] = list(vp.brush.color); vp.brush.color = (1, 0, 0)
ups = bpy.context.scene.tool_settings.unified_paint_settings
OUT["unified_color"] = list(ups.color); ups.color = (1, 0, 0)
print("STEP plain", flush=True)
OUT["vp_plain"] = err(lambda: bpy.ops.paint.vertex_paint(stroke=stroke))
print("STEP view3d", flush=True)
with bpy.context.temp_override(**ov):
    OUT["vp_view3d"] = err(lambda: bpy.ops.paint.vertex_paint(stroke=stroke))
print("STEP done", flush=True)
bpy.ops.object.mode_set(mode="OBJECT")
c = np.empty(len(me.vertices) * 4, np.float32); me.color_attributes["Col"].data.foreach_get("color", c)
c = c.reshape(-1, 4)
OUT["col_start_value"] = [round(float(x), 3) for x in c[0]]
OUT["vp_changed_points"] = int((np.abs(c - c[0]).max(axis=1) > 1e-3).sum())
''',
    "weight_paint stroke as data": r'''
me = ob.data
vg = ob.vertex_groups.new(name="W")
ov = view3d()
cx, cy = ov["region"].width // 2, ov["region"].height // 2
with bpy.context.temp_override(**ov):
    OUT["view_all"] = err(lambda: bpy.ops.view3d.view_all())
stroke = [dict(name="", location=(0, 0, 0), mouse=(cx - 20 + 4 * i, cy), mouse_event=(cx - 20 + 4 * i, cy), pressure=1.0,
               size=60, x_tilt=0, y_tilt=0, time=i * 0.01, is_start=(i == 0)) for i in range(10)]
bpy.ops.ed.undo_push(); bpy.ops.object.mode_set(mode="WEIGHT_PAINT"); bpy.ops.ed.undo_push()
print("STEP plain", flush=True)
OUT["wp_plain"] = err(lambda: bpy.ops.paint.weight_paint(stroke=stroke))
print("STEP view3d", flush=True)
with bpy.context.temp_override(**ov):
    OUT["wp_view3d"] = err(lambda: bpy.ops.paint.weight_paint(stroke=stroke))
print("STEP done", flush=True)
bpy.ops.object.mode_set(mode="OBJECT")
w = np.array([next((g.weight for g in v.groups if g.group == vg.index), 0.0) for v in me.vertices])
OUT["wp_points_with_weight"] = int((w > 0).sum()); OUT["wp_max_weight"] = round(float(w.max()), 3)
''',
}

res = {}
for label, body in PROBES.items():
    p = os.path.join(TMP, "probe.py")
    with open(p, "w") as f:
        f.write(PRE + body + POST)
    t = time.time()
    r = subprocess.run([B, "-b", "--factory-startup", "--python-exit-code", "1", "--python", p],
                       capture_output=True, text=True, timeout=300)
    out = [l for l in r.stdout.splitlines() if l.startswith("RESULT ")]
    res[label] = dict(exit=r.returncode, seconds=round(time.time() - t, 2), reached="REACHED" in r.stdout,
                      steps=[l[5:] for l in r.stdout.splitlines() if l.startswith("STEP ")],
                      result=json.loads(out[0][7:]) if out else None,
                      crash=("Segmentation" in r.stdout + r.stderr) or r.returncode < 0,
                      tail=None if out else (r.stdout + r.stderr).strip().splitlines()[-4:])
    print(label, json.dumps(res[label])[:900], flush=True)
data["probes"] = res

R = {k: (v["result"] or {}) for k, v in res.items()}
fact("the sculpt mesh filter crashes a background Blender when no undo step was pushed; Blender exits without a result",
     exit=res["mesh_filter, no undo push"]["exit"], crash=res["mesh_filter, no undo push"]["crash"],
     reached_the_call=res["mesh_filter, no undo push"]["reached"], tail=res["mesh_filter, no undo push"]["tail"])
fact("one undo push, either before or after entering sculpt mode, is enough: the mesh filter FINISHED and moved every "
     "point",
     after_only=dict(exit=res["mesh_filter, undo push after mode_set only"]["exit"],
                     ret=R["mesh_filter, undo push after mode_set only"].get("ret"),
                     moved=R["mesh_filter, undo push after mode_set only"].get("moved_count")),
     before_only=dict(exit=res["mesh_filter, undo push before mode_set only"]["exit"],
                      ret=R["mesh_filter, undo push before mode_set only"].get("ret"),
                      moved=R["mesh_filter, undo push before mode_set only"].get("moved_count")))
fact("with an undo step pushed before and after entering sculpt mode, every mesh filter type FINISHED and moved points "
     "except ERASE_DISPLACEMENT (CANCELLED; it acts on Multires displacement); the types ran one after another on the "
     "same 64 x 32 UV sphere, strength 0.5", types=R["mesh_filter, every type, undo push before and after"].get("types"),
     verts=R["mesh_filter, every type, undo push before and after"].get("verts"))
fact("a mask written as data (a FLOAT POINT attribute named .sculpt_mask, 1 = masked) holds the mesh filter: the masked "
     "top half did not move", **R["mesh_filter, mask written as data"])
fact("paint.mask_flood_fill runs headless and writes the .sculpt_mask attribute", **R["mask_flood_fill"])
fact("the sculpt cloth filter, with undo steps pushed, returns PASS_THROUGH and moves nothing headless: called plainly, "
     "as EXEC_DEFAULT, or inside the 3D View override", exit=res["cloth_filter, undo push"]["exit"],
     reached=res["cloth_filter, undo push"]["reached"], **R["cloth_filter, undo push"],
     tail=res["cloth_filter, undo push"]["tail"])
fact("sculpt.sample_detail_size returns CANCELLED headless, plainly and inside the 3D View override, before and after "
     "view3d.view_all; the constant detail stays 3.0",
     exit=res["sample_detail_size"]["exit"], **R["sample_detail_size"], tail=res["sample_detail_size"]["tail"])
fact("dyntopo toggles headless and detail_flood_fill (constant detail 4) retriangulates the sphere",
     exit=res["dyntopo and detail_flood_fill"]["exit"], **R["dyntopo and detail_flood_fill"],
     tail=res["dyntopo and detail_flood_fill"]["tail"])
fact("object.voxel_remesh runs headless from sculpt mode and object mode (mesh.remesh_voxel_size); quadriflow_remesh "
     "too", exit=res["voxel_remesh and quadriflow"]["exit"], **R["voxel_remesh and quadriflow"],
     tail=res["voxel_remesh and quadriflow"]["tail"])
fact("Multires: multires_subdivide (object mode, active object) adds levels headless; the mesh filter in sculpt mode "
     "moves the multires surface; modifier_apply bakes the levels into the mesh",
     exit=res["multires subdivide, sculpt, apply"]["exit"], **R["multires subdivide, sculpt, apply"],
     tail=res["multires subdivide, sculpt, apply"]["tail"])
fact("paint.vertex_paint given a stroke as data fails its poll plainly; inside the 3D View override (after view_all) "
     "it returns FINISHED but changes no colour",
     exit=res["vertex_paint stroke as data"]["exit"], steps=res["vertex_paint stroke as data"]["steps"],
     **R["vertex_paint stroke as data"], tail=res["vertex_paint stroke as data"]["tail"])
fact("paint.weight_paint given a stroke as data fails its poll plainly; inside the 3D View override it crashes "
     "Blender (the crash log's stack: wpaint_stroke_update_step -> view3d_operator_needs_gpu -> GPU_viewport)",
     exit=res["weight_paint stroke as data"]["exit"], steps=res["weight_paint stroke as data"]["steps"],
     **R["weight_paint stroke as data"], tail=res["weight_paint stroke as data"]["tail"])
fact("sculpt.brush_stroke given a stroke as data fails its poll plainly; inside the 3D View override a stroke of "
     "object-space locations at (0, -1, 0) FINISHED and moved the points around there",
     exit=res["brush_stroke as data"]["exit"], **R["brush_stroke as data"], tail=res["brush_stroke as data"]["tail"])

import shutil  # noqa: E402
shutil.rmtree(TMP)
version = subprocess.run([B, "--version"], capture_output=True, text=True).stdout.splitlines()[0].replace("Blender ", "")
rec = dict(experiment=os.path.relpath(os.path.abspath(__file__), ROOT), blender=version,
           machine=f"{platform.system()} {platform.machine()}", date=datetime.date.today().isoformat(),
           seconds=round(time.time() - t_all, 2), facts=facts, data=data, args=[])
text = json.dumps(rec, indent=1, default=str).replace(os.path.expanduser("~"), "~").replace(TMP, "<tmp>")
import re  # noqa: E402
text = re.sub(r"/(?:private/)?var/folders/[^\s\"]+?/T/", "<tmpdir>/", text)
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"), exist_ok=True)
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "sculpt_ops_probe.json"), "w") as f:
    f.write(text)
print("SAVED")
