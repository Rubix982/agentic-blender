"""Read everything Blender says about itself, and write it to the inventory folder next to this one.

  python3 scripts/run.py scripts/inventory.py        (from the skill's folder; takes about 2 s)

Runs inside Blender (headless, factory settings). Writes, one JSON object per line, gzipped:
  structs.jsonl.gz   every RNA type in bpy.types: base, description, properties (type, subtype, unit, default,
                     range, enum items, pointer target), functions (parameters, returns), the add-on that defines it
  operators.jsonl.gz every bpy.ops operator: description, parameters, Python module if it is written in Python
  nodes.jsonl.gz     every node type: the node trees it can be added to, its input and output sockets (name,
                     identifier, socket type, default, whether shown by default), and its own properties
  modules.jsonl.gz   the Python modules around bpy (bmesh, bmesh.ops, mathutils, bpy_extras, ...): every function
                     and class with its docstring
and as plain JSON:
  meta.json          version, build, Python, libraries, counts, add-ons (bundled, on by default, enabled here)
  factory.json       the factory startup file's values for the settings people change most (render, Cycles, EEVEE,
                     colour management, units, the default material and light)
  dynamic_enums.json enums whose items depend on the file or machine (view transforms, colour spaces, devices),
                     read by asking Blender to reject a bad value
  assets.json        the assets bundled with Blender (node groups, brushes) by file
Bundled add-ons are all enabled before the read, so their types and operators are in it; meta.json says which are on in
a fresh Blender.
"""
import gzip
import inspect
import json
import os
import sys
import time

import addon_utils
import bpy

T0 = time.time()
OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "inventory"))   # skills/blender/inventory
os.makedirs(OUT, exist_ok=True)


def plain(v, depth=0):
    """A JSON-safe copy of a Blender value."""
    if v is None or isinstance(v, (bool, int, str)):
        return v
    if isinstance(v, float):
        return round(v, 6) if v == v and abs(v) != float("inf") else str(v)
    if isinstance(v, (set, frozenset)):
        return sorted(str(x) for x in v)
    if hasattr(v, "bl_rna") and hasattr(v, "name") and isinstance(getattr(v, "name", None), str):
        return f"<{type(v).__name__} {v.name!r}>"
    if hasattr(v, "bl_rna"):
        return f"<{type(v).__name__}>"
    if depth < 3:
        try:
            return [plain(x, depth + 1) for x in v]
        except TypeError:
            pass
    return str(v)


def prop_info(p):
    d = dict(id=p.identifier, name=p.name, type=p.type)
    if p.description:
        d["desc"] = p.description
    if p.subtype not in ("NONE", ""):
        d["subtype"] = p.subtype
    if getattr(p, "unit", "NONE") not in ("NONE", ""):
        d["unit"] = p.unit
    if p.is_readonly:
        d["readonly"] = True
    if p.is_required:
        d["required"] = True
    if getattr(p, "is_output", False):
        d["output"] = True
    if p.is_animatable is False and not p.is_readonly:
        d["not_animatable"] = True
    t = p.type
    if t in ("INT", "FLOAT", "BOOLEAN"):
        n = getattr(p, "array_length", 0)
        if n:
            d["array"] = n
            dims = [x for x in getattr(p, "array_dimensions", ()) if x]
            if len(dims) > 1:
                d["dims"] = dims
            d["default"] = plain(p.default_array)
        else:
            d["default"] = plain(p.default)
        if t != "BOOLEAN":
            d["range"] = [plain(p.hard_min), plain(p.hard_max)]
            if (p.soft_min, p.soft_max) != (p.hard_min, p.hard_max):
                d["soft"] = [plain(p.soft_min), plain(p.soft_max)]
            if t == "FLOAT" and getattr(p, "precision", None) is not None:
                d["precision"] = p.precision
    elif t == "STRING":
        d["default"] = p.default
    elif t == "ENUM":
        items = [dict(id=i.identifier, name=i.name, **({"desc": i.description} if i.description else {}))
                 for i in p.enum_items]
        d["items"] = items
        if not items:
            d["dynamic"] = True
        if p.is_enum_flag:
            d["flag"] = True
            d["default"] = sorted(p.default_flag)
        else:
            d["default"] = p.default
    elif t in ("POINTER", "COLLECTION"):
        if p.fixed_type:
            d["to"] = p.fixed_type.identifier
        if t == "COLLECTION" and getattr(p, "srna", None):
            d["api"] = p.srna.identifier
    return d


def func_info(f):
    params = [prop_info(p) for p in f.parameters]
    d = dict(id=f.identifier, params=[p for p in params if not p.get("output")],
             returns=[p for p in params if p.get("output")])
    if f.description:
        d["desc"] = f.description
    if not f.use_self:
        d["static"] = True
    return d


# 0. Enums whose items depend on the file or the machine (read first, before any extra add-on is on: a fresh Blender's lists): ask Blender to reject a bad value; its message lists the
# accepted ones.
def accepted(obj, prop):
    try:
        setattr(obj, prop, "__not_a_value__")
    except TypeError as e:
        msg = str(e)
        if "(" in msg and ")" in msg:
            inner = msg[msg.rfind("(") + 1: msg.rfind(")")]
            return [x.strip().strip("'") for x in inner.split(",") if x.strip()]
        return msg
    except Exception as e:  # noqa: BLE001
        return repr(e)[:200]
    return "accepted a bad value?"


img = bpy.data.images.new("inv_probe", 4, 4)
cyprefs = bpy.context.preferences.addons["cycles"].preferences if "cycles" in bpy.context.preferences.addons else None
dynamic = {
    "Scene.render.engine": accepted(bpy.context.scene.render, "engine"),
    "ColorManagedViewSettings.view_transform": accepted(bpy.context.scene.view_settings, "view_transform"),
    "ColorManagedViewSettings.look": accepted(bpy.context.scene.view_settings, "look"),
    "ColorManagedDisplaySettings.display_device": accepted(bpy.context.scene.display_settings, "display_device"),
    "ColorManagedInputColorspaceSettings.name (Image.colorspace_settings.name)": accepted(img.colorspace_settings, "name"),
    "ColorManagedSequencerColorspaceSettings.name": accepted(bpy.context.scene.sequencer_colorspace_settings, "name"),
}
if cyprefs:
    dynamic["CyclesPreferences.compute_device_type"] = accepted(cyprefs, "compute_device_type")
    cyprefs.get_devices()
    dynamic["CyclesPreferences.devices (this machine)"] = [dict(name=d.name, type=d.type) for d in cyprefs.devices]
    dynamic["CyclesRenderSettings.device"] = accepted(bpy.context.scene.cycles, "device")
    dynamic["CyclesRenderSettings.denoiser"] = accepted(bpy.context.scene.cycles, "denoiser")
bpy.data.images.remove(img)

# 1. Add-ons: what a fresh Blender has on, then everything bundled switched on.
bpy.context.preferences.use_preferences_save = False   # enabling add-ons below must never reach the user's preferences
SYSTEM = os.path.realpath(bpy.utils.system_resource("SCRIPTS"))
bundled, default_on, enabled_here, failed = [], [], [], {}
for m in addon_utils.modules():
    if not os.path.realpath(getattr(m, "__file__", "") or "").startswith(SYSTEM):
        continue   # add-ons and extensions the user installed are this machine's, not Blender's
    info = addon_utils.module_bl_info(m)
    bundled.append(dict(module=m.__name__, name=info.get("name"), category=info.get("category"),
                        description=info.get("description"), version=plain(info.get("version"))))
    if addon_utils.check(m.__name__)[1]:
        default_on.append(m.__name__)
for a in bundled:
    if a["module"] in default_on:
        continue
    try:
        addon_utils.enable(a["module"], default_set=True, handle_error=lambda e: (_ for _ in ()).throw(e))
        enabled_here.append(a["module"])
    except BaseException as e:  # noqa: BLE001
        failed[a["module"]] = repr(e)[:200]
print("ADDONS", len(bundled), "on by default", len(default_on), "enabled", len(enabled_here), "failed", len(failed), flush=True)
dynamic["Scene.render.engine, with every bundled add-on on (Hydra Storm is an add-on, off by default)"] = accepted(
    bpy.context.scene.render, "engine")

# 2. The factory file's values, before anything below touches the scene.
sc = bpy.context.scene


def values(obj, skip=()):
    out = {}
    if obj is None:
        return None
    for p in obj.bl_rna.properties:
        if p.identifier in ("rna_type",) + tuple(skip) or p.type == "COLLECTION":
            continue
        try:
            v = getattr(obj, p.identifier)
        except Exception:  # noqa: BLE001
            continue
        if p.type == "POINTER":
            if v is not None and not hasattr(v, "name"):
                continue  # nested settings structs are read on their own
        out[p.identifier] = plain(v)
    return out


factory = dict(
    objects=[dict(name=o.name, type=o.type, location=plain(o.location), rotation_euler=plain(o.rotation_euler),
                  data=o.data.name if o.data else None) for o in sc.objects],
    render=values(sc.render), image_settings=values(sc.render.image_settings),
    cycles=values(getattr(sc, "cycles", None)), eevee=values(sc.eevee),
    view_settings=values(sc.view_settings), display_settings=values(sc.display_settings),
    unit_settings=values(sc.unit_settings), scene=values(sc), bake=values(sc.render.bake),
    world=values(sc.world) if sc.world else None,
    lights={l.name: values(l) for l in bpy.data.lights}, cameras={c.name: values(c) for c in bpy.data.cameras},
    materials={m.name: dict(use_nodes=m.use_nodes, nodes=[dict(type=n.type, idname=n.bl_idname, name=n.name)
                                                          for n in (m.node_tree.nodes if m.node_tree else [])])
               for m in bpy.data.materials},
)

# 3. Every RNA type: those named in bpy.types, then every type reachable from them through a pointer, a collection or
# a function parameter (Python-defined settings, such as Cycles' CyclesRenderSettings, are only reachable that way).
UI = ("_PT_", "_MT_", "_UL_", "_HT_", "_OT_", "_GT_", "_GGT_", "_WT_", "_AST_")
found = {}   # identifier -> (rna, class or None, name in bpy.types or None)
for name in sorted(dir(bpy.types)):
    cls = getattr(bpy.types, name, None)
    rna = getattr(cls, "bl_rna", None)
    if rna is not None and rna.identifier not in found:
        found[rna.identifier] = (rna, cls, name)
for addon in bpy.context.preferences.addons:   # add-on preferences (CyclesPreferences: the GPU devices) hang off a generic pointer
    ap = addon.preferences
    if ap is not None and ap.bl_rna.identifier not in found:
        found[ap.bl_rna.identifier] = (ap.bl_rna, type(ap), None)
queue = [v[0] for v in found.values()]
while queue:
    rna = queue.pop()
    nxt = []
    for p in rna.properties:
        if p.type in ("POINTER", "COLLECTION"):
            nxt += [p.fixed_type, getattr(p, "srna", None)]
    for f in rna.functions:
        nxt += [p.fixed_type for p in f.parameters if p.type in ("POINTER", "COLLECTION")]
    nxt.append(rna.base)
    for t in nxt:
        if t is not None and t.identifier not in found:
            found[t.identifier] = (t, None, None)
            queue.append(t)
structs = []
for ident in sorted(found):
    rna, cls, name = found[ident]
    d = dict(id=rna.identifier, name=rna.name)
    if any(u in rna.identifier for u in UI):
        d["ui"] = True
    if name is None:
        d["reachable_only"] = True
    if rna.description:
        d["desc"] = rna.description
    if rna.base:
        d["base"] = rna.base.identifier
    mod = getattr(cls, "__module__", "")
    if mod and mod not in ("bpy.types", "bpy_types") and not mod.startswith("bpy_types"):
        d["module"] = mod
    base_props = {p.identifier for p in rna.base.properties} if rna.base else set()
    d["props"] = [prop_info(p) for p in rna.properties if p.identifier != "rna_type" and p.identifier not in base_props]
    base_funcs = {f.identifier for f in rna.base.functions} if rna.base else set()
    d["funcs"] = [func_info(f) for f in rna.functions if f.identifier not in base_funcs]
    if cls is not None and not d.get("ui"):   # methods and properties Blender defines in Python (bpy_types), outside the RNA
        rna_names = {p.identifier for p in rna.properties} | {f.identifier for f in rna.functions}
        pym = []
        for k in cls.__mro__:
            if not str(getattr(k, "__module__", "")).startswith("bpy_types"):
                continue
            for mname, v in k.__dict__.items():
                if mname.startswith("_") or mname in rna_names or mname in {m["id"] for m in pym}:
                    continue
                kind = ("property" if isinstance(v, property) else "classmethod" if isinstance(v, classmethod)
                        else "staticmethod" if isinstance(v, staticmethod) else "function" if callable(v) else None)
                if not kind:
                    continue
                fn = v.fget if isinstance(v, property) else getattr(v, "__func__", v)
                e = dict(id=mname, kind=kind, defined_on=k.__name__)
                if kind != "property":
                    try:
                        e["signature"] = str(inspect.signature(fn))
                    except (TypeError, ValueError):
                        pass
                doc = inspect.getdoc(fn)
                if doc:
                    e["desc"] = doc[:1200]
                pym.append(e)
        if pym:
            d["py"] = pym
    if name and name != rna.identifier:
        d["alias"] = name
    structs.append(d)
print("STRUCTS", len(structs), round(time.time() - T0, 1), flush=True)

# 4. Every operator.
operators = []
for modname in sorted(dir(bpy.ops)):
    mod = getattr(bpy.ops, modname)
    for opname in sorted(dir(mod)):
        try:
            op = getattr(mod, opname)
            rna = op.get_rna_type()
        except Exception as e:  # noqa: BLE001
            operators.append(dict(id=f"{modname}.{opname}", error=repr(e)[:200]))
            continue
        d = dict(id=f"{modname}.{opname}", idname=rna.identifier, name=rna.name)
        if rna.description:
            d["desc"] = rna.description
        cls = getattr(bpy.types, rna.identifier, None)
        m = getattr(cls, "__module__", "") if cls else ""
        if m and m not in ("bpy.types", "bpy_types"):
            d["module"] = m
        d["params"] = [prop_info(p) for p in rna.properties if p.identifier != "rna_type"]
        operators.append(d)
print("OPERATORS", len(operators), round(time.time() - T0, 1), flush=True)

# 5. Every node type, added to every kind of node tree it accepts.
trees = {}
for kind in ("ShaderNodeTree", "GeometryNodeTree", "CompositorNodeTree", "TextureNodeTree"):
    try:
        trees[kind] = bpy.data.node_groups.new(f"inv_{kind}", kind)
    except Exception as e:  # noqa: BLE001
        print("TREE", kind, e)


def socket_info(s):
    d = dict(name=s.name, id=s.identifier, type=s.bl_idname)
    if not s.enabled:
        d["hidden_by_default"] = True
    if getattr(s, "hide_value", False):
        d["no_value"] = True
    if hasattr(s, "default_value"):
        try:
            d["default"] = plain(s.default_value)
        except Exception:  # noqa: BLE001
            pass
        rna = s.bl_rna.properties.get("default_value")
        if rna is not None and rna.type in ("INT", "FLOAT"):
            d["range"] = [plain(rna.soft_min), plain(rna.soft_max)]
            if rna.subtype not in ("NONE", ""):
                d["subtype"] = rna.subtype
    if getattr(s, "is_multi_input", False):
        d["multi_input"] = True
    return d


def node_values(n, props):
    """Values of a new node's own simple settings. Only plain types are read: reading some pointer and collection
    properties of a bare node crashed Blender 4.5 (segfault) while this inventory was written."""
    out = {}
    for p in props:
        if p["type"] in ("BOOLEAN", "INT", "FLOAT", "STRING", "ENUM") and not p.get("readonly"):
            try:
                out[p["id"]] = plain(getattr(n, p["id"]))
            except Exception:  # noqa: BLE001
                pass
    return out


node_classes = []
for name in sorted(dir(bpy.types)):
    cls = getattr(bpy.types, name, None)
    try:
        if cls is not None and isinstance(cls, type) and issubclass(cls, bpy.types.Node) and cls is not bpy.types.Node:
            node_classes.append(cls)
    except TypeError:
        pass
nodes = []
for cls in node_classes:
    idname = cls.bl_rna.identifier
    d = dict(id=idname, name=cls.bl_rna.name, trees=[])
    if cls.bl_rna.description:
        d["desc"] = cls.bl_rna.description
    base_props = {p.identifier for p in bpy.types.Node.bl_rna.properties}
    d["props"] = [prop_info(p) for p in cls.bl_rna.properties if p.identifier not in base_props]
    for kind, tree in trees.items():
        try:
            n = tree.nodes.new(idname)
        except Exception:  # noqa: BLE001
            continue
        d["trees"].append(kind)
        if "inputs" not in d:
            d["label"] = n.bl_label if hasattr(n, "bl_label") else n.name
            d["inputs"] = [socket_info(s) for s in n.inputs]
            d["outputs"] = [socket_info(s) for s in n.outputs]
            d["type"] = n.type
            d["new_values"] = node_values(n, d["props"])   # what nodes.new gives, not the registered default
        tree.nodes.remove(n)
    if not d["trees"]:
        d["abstract_or_unavailable"] = True
    nodes.append(d)
print("NODES", len(nodes), sum(1 for n in nodes if n["trees"]), round(time.time() - T0, 1), flush=True)

# 5b. Modifiers and constraints made for real: which type each enum value gives, and the values a new one starts with.
typed = {"modifiers": {}, "constraints": {}}
hosts = []
for label, data in (("mesh", bpy.data.meshes.new("inv_mesh")), ("grease_pencil", bpy.data.grease_pencils_v3.new("inv_gp")),
                    ("curve", bpy.data.curves.new("inv_curve", "CURVE")), ("lattice", bpy.data.lattices.new("inv_lat")),
                    ("volume", bpy.data.volumes.new("inv_vol"))):
    ob = bpy.data.objects.new(f"inv_{label}", data)
    bpy.context.scene.collection.objects.link(ob)
    hosts.append((label, ob))
for item in bpy.types.Modifier.bl_rna.properties["type"].enum_items:
    for label, ob in hosts:
        try:
            m = ob.modifiers.new("inv", item.identifier)
        except (RuntimeError, TypeError):
            continue
        if m is None:
            continue
        typed["modifiers"][item.identifier] = dict(struct=m.bl_rna.identifier, object=label,
                                                   new_values={k: v for k, v in values(m).items() if k not in ("name",)})
        ob.modifiers.remove(m)
        break
    else:
        typed["modifiers"][item.identifier] = dict(struct=None, error="no host object accepted it")
for item in bpy.types.Constraint.bl_rna.properties["type"].enum_items:
    ob = hosts[0][1]
    try:
        c = ob.constraints.new(item.identifier)
        typed["constraints"][item.identifier] = dict(struct=c.bl_rna.identifier,
                                                     new_values={k: v for k, v in values(c).items() if k not in ("name",)})
        ob.constraints.remove(c)
    except (RuntimeError, TypeError) as e:
        typed["constraints"][item.identifier] = dict(struct=None, error=str(e)[:120])
for label, ob in hosts:
    bpy.data.objects.remove(ob)
print("TYPED", len(typed["modifiers"]), len(typed["constraints"]), round(time.time() - T0, 1), flush=True)

# 6. The Python modules around bpy.
import importlib  # noqa: E402
import re  # noqa: E402

MODULE_REPR_SIG = re.compile(r"<module '[^']*' from '[^']*'>")

MODULES = ["bpy", "bpy.utils", "bpy.path", "bpy.props", "bpy.app", "bpy.app.handlers", "bpy.app.timers",
           "bpy.app.translations", "bpy.msgbus",
           "bmesh", "bmesh.ops", "bmesh.types", "bmesh.utils", "bmesh.geometry",
           "mathutils", "mathutils.geometry", "mathutils.bvhtree", "mathutils.kdtree", "mathutils.noise",
           "mathutils.interpolate", "bpy_extras", "bpy_extras.object_utils", "bpy_extras.view3d_utils",
           "bpy_extras.mesh_utils", "bpy_extras.image_utils", "bpy_extras.io_utils", "bpy_extras.anim_utils",
           "bpy_extras.node_utils", "bpy_extras.node_shader_utils", "bpy_extras.keyconfig_utils", "bl_math",
           "idprop.types", "gpu", "gpu.types", "gpu.matrix", "gpu.state", "gpu.shader", "gpu.texture",
           "gpu_extras.batch", "gpu_extras.presets", "aud", "imbuf", "freestyle", "bl_ui", "addon_utils",
           "bpy.ops"]
modules = []
for mname in MODULES:
    try:
        m = importlib.import_module(mname)
    except Exception as e:  # noqa: BLE001
        modules.append(dict(module=mname, error=repr(e)[:200]))
        continue
    members = []
    if mname == "bpy.ops":
        modules.append(dict(module=mname, doc=(m.__doc__ or "")[:2000], members=[]))
        continue
    for k in sorted(dir(m)):
        if k.startswith("_"):
            continue
        try:
            v = getattr(m, k)
        except Exception:  # noqa: BLE001
            continue
        if inspect.ismodule(v):
            continue
        kind = "class" if inspect.isclass(v) else ("function" if callable(v) else "value")
        e = dict(name=k, kind=kind)
        doc = inspect.getdoc(v) if kind != "value" else None
        if doc:
            e["doc"] = doc[:4000]
        if kind == "function":
            try:
                sig = MODULE_REPR_SIG.sub("<module>", str(inspect.signature(v)))
                e["signature"] = sig if len(sig) < 400 else sig[:200] + " ...)"
            except (TypeError, ValueError):
                pass
        if kind == "value":
            e["value"] = plain(v)[:300] if isinstance(plain(v), str) else plain(v)
        if kind == "class" and mname not in ("bl_ui",):
            meths = []
            for mk in sorted(dir(v)):
                if mk.startswith("_"):
                    continue
                try:
                    mv = getattr(v, mk)
                except Exception:  # noqa: BLE001
                    continue
                md = inspect.getdoc(mv)
                if md and md != doc and not inspect.isclass(mv):
                    meths.append(dict(name=mk, doc=md[:2000]))
            if meths:
                e["members"] = meths
        members.append(e)
    modules.append(dict(module=mname, doc=(m.__doc__ or "")[:2000], members=members))
print("MODULES", len(modules), sum(len(m.get("members", [])) for m in modules), round(time.time() - T0, 1), flush=True)


# 8. Bundled assets.
assets = {}
base = os.path.join(bpy.utils.system_resource("DATAFILES"), "assets")
for dirpath, _, files in os.walk(base):
    for f in sorted(files):
        if not f.endswith(".blend"):
            continue
        p = os.path.join(dirpath, f)
        rel = os.path.relpath(p, base)
        try:
            with bpy.data.libraries.load(p, assets_only=True) as (src, _):
                assets[rel] = {k: sorted(getattr(src, k)) for k in dir(src) if getattr(src, k)}
        except Exception as e:  # noqa: BLE001
            assets[rel] = repr(e)[:200]

meta = dict(
    blender=bpy.app.version_string, version=list(bpy.app.version), build_hash=plain(bpy.app.build_hash),
    build_date=plain(bpy.app.build_date), python=sys.version.split()[0], platform=sys.platform,
    binary=os.path.basename(bpy.app.binary_path),
    libraries={k: plain(getattr(bpy.app, k).version_string) for k in ("ffmpeg", "ocio", "oiio", "opensubdiv", "openvdb", "alembic", "usd", "sdl")
               if hasattr(bpy.app, k) and hasattr(getattr(bpy.app, k), "version_string")},
    build_options=[k for k in dir(bpy.app.build_options) if not k.startswith("_") and getattr(bpy.app.build_options, k) is True],
    addons=dict(bundled=bundled, on_by_default=default_on, enabled_for_this_read=enabled_here, failed=failed),
    counts=dict(structs=len(structs), properties=sum(len(s["props"]) for s in structs),
                functions=sum(len(s["funcs"]) for s in structs), operators=len(operators),
                nodes=len(nodes), nodes_addable=sum(1 for n in nodes if n["trees"]),
                node_sockets=sum(len(n.get("inputs", [])) + len(n.get("outputs", [])) for n in nodes),
                python_members=sum(len(m.get("members", [])) for m in modules),
                python_defined_on_types=sum(len(s.get("py", [])) for s in structs)),
    seconds=round(time.time() - T0, 1),
)


HOME = os.path.expanduser("~")
MODULE_REPR = __import__("re").compile(r"<module '[^']*' from '[^']*'>")


def scrub(text):
    """No machine paths in the output: the home folder becomes ~, module reprs become <module>."""
    return MODULE_REPR.sub("<module>", text).replace(HOME, "~")


def dump(name, rows):
    text = "".join(scrub(json.dumps(r, ensure_ascii=False, separators=(",", ":"))) + "\n" for r in rows)
    with open(os.path.join(OUT, name), "wb") as f:   # mtime=0: the same inventory gives the same bytes
        f.write(gzip.compress(text.encode("utf-8"), mtime=0))


dump("structs.jsonl.gz", structs)
dump("operators.jsonl.gz", operators)
dump("nodes.jsonl.gz", nodes)
dump("modules.jsonl.gz", modules)
for name, obj in (("meta.json", meta), ("factory.json", factory), ("dynamic_enums.json", dynamic), ("assets.json", assets),
                  ("typed.json", typed)):
    with open(os.path.join(OUT, name), "w") as f:
        f.write(scrub(json.dumps(obj, indent=1, ensure_ascii=False, default=str)))
print("INVENTORY", json.dumps(meta["counts"]), f"{time.time() - T0:.1f} s", flush=True)
