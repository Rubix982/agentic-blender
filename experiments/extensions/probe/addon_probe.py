"""Inside Blender, run by ../top_addons.py in a sandbox: enable one add-on, record what it registers, and call each of
its operators headless with default settings on a fresh cube (object mode; edit mode, all selected, if object mode's
poll fails), noting whether the scene changed.
Arguments after --: MODULE OUT_JSON PROGRESS_FILE [SKIP,LIST]."""
import json
import os
import re
import sys
import time
import traceback

import addon_utils
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
module, out_path, progress_path = argv[0], argv[1], argv[2]
skip = set(x for x in (argv[3] if len(argv) > 3 else "").split(",") if x)
# never run: these may open a browser, change preferences or keymaps, or install things
NOT_RUN = re.compile(r"url|web|browser|update|install|uninstall|preference|keymap|keyconfig|register|report_bug|"
                     r"open_folder|reveal|explore|file_browser|translat", re.I)
IDS = ("Scene", "Object", "WindowManager", "Mesh", "Material", "World", "ViewLayer", "Collection", "Image", "Curve",
       "Armature", "Bone", "PoseBone", "EditBone", "Node", "NodeTree", "Camera", "Light")


def ops_now():
    out = set()
    for cat in dir(bpy.ops):
        if not cat.startswith("_"):
            for name in dir(getattr(bpy.ops, cat)):
                if not name.startswith("_"):
                    out.add(f"{cat}.{name}")
    return out


def props_now():
    return {t: {p.identifier for p in getattr(bpy.types, t).bl_rna.properties} for t in IDS if hasattr(bpy.types, t)}


def kind(name):
    t = getattr(bpy.types, name, None)
    for base in ("Panel", "Menu", "Operator", "PropertyGroup", "UIList", "Header", "Gizmo", "GizmoGroup",
                 "AddonPreferences", "Node", "NodeTree", "NodeSocket", "RenderEngine", "KeyingSet"):
        try:
            if isinstance(t, type) and issubclass(t, getattr(bpy.types, base)):
                return base
        except TypeError:
            pass
    return "other"


def state():
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    return dict(objects=len(bpy.data.objects), verts=sum(len(o.data.vertices) for o in meshes),
                co=round(sum(abs(c) for o in meshes for v in o.data.vertices for c in v.co), 3),
                **{k: len(getattr(bpy.data, k)) for k in ("meshes", "curves", "materials", "images", "node_groups",
                                                           "actions", "armatures", "collections", "texts")})


def reset(mode):
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.data.batch_remove(list(bpy.data.objects))
    bpy.data.orphans_purge(do_recursive=True)
    bpy.context.view_layer.update()                       # removed objects leave None in the view layer until this
    bpy.ops.mesh.primitive_cube_add(size=2)
    if mode == "EDIT":
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")


def log(line):
    with open(progress_path, "a") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())


ops0, types0, props0 = ops_now(), set(dir(bpy.types)), props_now()
t = time.time()
err = None
try:
    mod = addon_utils.enable(module, default_set=True, persistent=True)
except Exception:
    mod, err = None, traceback.format_exc().splitlines()[-1]
rec = dict(module=module, enabled=mod is not None, enable_seconds=round(time.time() - t, 3), enable_error=err)
ops1, types1, props1 = ops_now(), set(dir(bpy.types)), props_now()
new_ops = sorted(ops1 - ops0)
new_types = sorted(types1 - types0)
reg = {}
for n in new_types:
    reg[kind(n)] = reg.get(kind(n), 0) + 1
reg["operators"] = len(new_ops)
rec["registers"] = reg
rec["new_properties"] = {k: sorted(props1[k] - props0.get(k, set())) for k in props1 if props1[k] - props0.get(k, set())}

results = []
for op_id in new_ops:
    cat, name = op_id.split(".", 1)
    op = getattr(getattr(bpy.ops, cat), name)
    try:
        rna = op.get_rna_type()
        info = dict(id=op_id, label=rna.name, description=(rna.description or "")[:160],
                    params=[p.identifier for p in rna.properties if p.identifier != "rna_type"][:25])
    except Exception:
        info = dict(id=op_id)
    if op_id in skip:
        info.update(result="crashed or hung before: skipped")
        results.append(info)
        continue
    if NOT_RUN.search(op_id) or "filepath" in info.get("params", []) or "directory" in info.get("params", []):
        info.update(result="not run")
        results.append(info)
        continue
    log(f"TRY {op_id}")
    for mode in ("OBJECT", "EDIT"):
        try:
            reset(mode)
            before = state()
            if not op.poll():
                res = "poll failed"
            else:
                t = time.time()
                res = sorted(op())
                info["seconds"] = round(time.time() - t, 3)
        except Exception as e:
            res = f"{type(e).__name__}: {str(e).strip().splitlines()[0][:160] if str(e).strip() else ''}"
        try:
            if bpy.context.object and bpy.context.object.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")
        except Exception:
            pass
        after = state()
        info.update(mode=mode, result=res, changed=before != after,
                    delta={k: after[k] - before[k] for k in after if after[k] != before[k]})
        if res != "poll failed":
            break
    results.append(info)
rec["operators"] = results
json.dump(rec, open(out_path, "w"), indent=1, default=str)
print("PROBE DONE", module, len(new_ops), flush=True)
