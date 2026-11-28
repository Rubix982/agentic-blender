"""The interface as data: what a key press and a menu click do, read from Blender 4.5 itself.

Runs inside Blender (headless, factory settings):
    python3 scripts/run.py scripts/inventory_ui.py
Writes, next to the other inventory files:
  keymap.jsonl.gz   every item of the default keymap, as the "Blender" preset builds it with its preferences at their
                    defaults (left-click select): the keymap (editor and mode), the event (key, value, modifiers), the
                    operator or modal action, its properties, and whether macOS also accepts Cmd for Ctrl
  menus.jsonl.gz    every menu class: its label, and what its draw() puts in it, in order (operators with their
                    properties and labels, submenus, enum menus, properties, inline menus), recorded by running the
                    menu's own draw function against a layout that writes entries down instead of drawing
In background mode the window manager holds no full keymap (104 keymaps, 12 items), so the keymap is built from the
preset's own data, the way Blender does when a window opens. Menus whose draw needs a real editor are recorded as far
as they draw, with the error.
"""
import gzip
import inspect
import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
INV = os.path.join(HERE, "..", "inventory")
SCRIPTS = bpy.utils.system_resource("SCRIPTS")

# --- the keymap, built by the preset's own load() with its preferences at their defaults ------------------------
preset = bpy.utils.execfile(os.path.join(SCRIPTS, "presets", "keyconfig", "Blender.py"))
import bl_keymap_utils.io as kio                                           # noqa: E402
import bl_keymap_utils.platform_helpers as ph                              # noqa: E402

got = {}
gen0 = preset.blender_default.generate_keymaps


def gen(params):
    got["params"] = {k: getattr(params, k, None) for k in type(params).__slots__}
    got["data"] = gen0(params)
    return got["data"]


preset.blender_default.generate_keymaps = gen
init0 = kio.keyconfig_init_from_data
kio.keyconfig_init_from_data = lambda kc, data: (got.__setitem__("final", data), init0(kc, data))[1]
try:
    bpy.utils.register_class(preset.Prefs)
except ValueError:                                                         # registered at startup, even headless
    pass
preset.load()
kio.keyconfig_init_from_data = init0
data = got["data"]                                                          # before the macOS Cmd copies

mac_ok = {}                                                                # which Ctrl items macOS also takes with Cmd
for km_name, _, items in ph.keyconfig_data_oskey_from_ctrl_for_macos(data):
    for op, ev, _ in items["items"]:
        if ev.get("oskey") and not ev.get("ctrl"):
            mac_ok[(km_name, op, ev["type"], ev.get("value"), bool(ev.get("shift")), bool(ev.get("alt")))] = True


def plain(v):
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    if isinstance(v, (list, tuple)):
        return [plain(x) for x in v]
    return str(v)


rows = []
for km_name, km_parms, items in data:
    for op, ev, extra in items["items"]:
        props = {}
        active = True
        if extra:
            props = {k: plain(v) for k, v in (extra.get("properties") or [])}
            active = extra.get("active", True)
        row = dict(keymap=km_name, space=km_parms.get("space_type"), region=km_parms.get("region_type"),
                   modal=bool(km_parms.get("modal")), op=op, type=ev.get("type"), value=ev.get("value"),
                   shift=plain(ev.get("shift", False)), ctrl=plain(ev.get("ctrl", False)), alt=plain(ev.get("alt", False)),
                   oskey=plain(ev.get("oskey", False)), any=bool(ev.get("any", False)),
                   key_modifier=ev.get("key_modifier"), direction=ev.get("direction"), repeat=ev.get("repeat"),
                   props=props, active=active)
        if ev.get("ctrl"):
            row["mac_cmd"] = (km_name, op, ev["type"], ev.get("value"), bool(ev.get("shift")), bool(ev.get("alt"))) in mac_ok
        rows.append({k: v for k, v in row.items() if v not in (None, False, {}) or k in ("modal",)})


# --- the menus, by running each menu's draw() against a recording layout -------------------------------------------
class Stub:
    """Stands for any value a draw function reads from an editor that does not exist in background mode."""
    def __getattr__(self, name):
        return Stub()

    def __call__(self, *a, **k):
        return Stub()

    def __iter__(self):
        return iter(())

    def __getitem__(self, key):
        return Stub()

    def __setitem__(self, key, value):
        pass

    def __len__(self):
        return 0

    def __float__(self):
        return 0.0

    def __int__(self):
        return 0

    __index__ = __int__

    def __str__(self):
        return "?"                                                     # a value only a real editor could supply

    def __bool__(self):
        return False

    def __eq__(self, other):
        return False

    __hash__ = object.__hash__


class Props:
    def __init__(self):
        object.__setattr__(self, "_set", {})

    def __setattr__(self, name, value):
        self._set[name] = plain(value)

    def __getattr__(self, name):
        return Stub()


def op_label(idname):
    try:
        mod, name = idname.split(".")
        return getattr(getattr(bpy.ops, mod), name).get_rna_type().name
    except Exception:
        return None


def enum_items_of_op(idname, prop):
    try:
        mod, name = idname.split(".")
        p = getattr(getattr(bpy.ops, mod), name).get_rna_type().properties[prop]
        return [(i.identifier, i.name) for i in p.enum_items]
    except Exception:
        return []


def prop_label(data, prop):
    try:
        return data.bl_rna.properties[prop].name
    except Exception:
        return None


class Rec:
    def __init__(self, entries):
        object.__setattr__(self, "entries", entries)
        object.__setattr__(self, "ctx", None)

    def __setattr__(self, name, value):
        if name == "operator_context":
            object.__setattr__(self, "ctx", value if isinstance(value, str) else None)

    def operator(self, operator, text=None, **k):
        idname = operator
        p = Props()
        self.entries.append(dict(kind="op", op=idname, label=text if isinstance(text, str) else op_label(idname),
                                 props=p._set, context=self.ctx))
        return p

    def menu(self, menu=None, text=None, **k):
        cls = getattr(bpy.types, menu, None)
        self.entries.append(dict(kind="menu", menu=menu, label=text if isinstance(text, str) else getattr(cls, "bl_label", menu)))

    def operator_menu_enum(self, operator=None, property=None, text=None, **k):
        idname, prop = operator, property
        self.entries.append(dict(kind="enum_menu", op=idname, prop=prop, label=text if isinstance(text, str) else op_label(idname),
                                 items=enum_items_of_op(idname, prop)))
        return Props()

    def operator_enum(self, operator=None, property=None, **k):
        idname, prop = operator, property
        for ident, name in enum_items_of_op(idname, prop):
            self.entries.append(dict(kind="op", op=idname, label=name, props={prop: ident}, context=self.ctx))

    def prop(self, data=None, property=None, text=None, **k):
        prop = property
        self.entries.append(dict(kind="prop", struct=type(data).__name__, prop=prop,
                                 label=text if isinstance(text, str) else prop_label(data, prop)))

    def prop_menu_enum(self, data=None, property=None, text=None, **k):
        prop = property
        self.entries.append(dict(kind="prop_menu", struct=type(data).__name__, prop=prop,
                                 label=text if isinstance(text, str) else prop_label(data, prop)))

    def prop_enum(self, data=None, property=None, value=None, text=None, **k):
        prop = property
        self.entries.append(dict(kind="prop_value", struct=type(data).__name__, prop=prop, value=plain(value),
                                 label=text if isinstance(text, str) else str(value)))

    def label(self, text="", **k):
        if text:
            self.entries.append(dict(kind="label", label=text))

    def menu_contents(self, menu=None):
        self.entries.append(dict(kind="inline", menu=menu))

    def __getattr__(self, name):                                    # column(), row(), box(), separator(), menu_pie()...
        if name == "operator_context":                              # draw functions save it and put it back
            return self.ctx
        return lambda *a, **k: self


class Ctx:
    """bpy.context, with stand-ins for what only a real editor has."""
    def __getattr__(self, name):
        if name in ("space_data", "area", "region", "region_data", "edit_text", "tool_settings_ui"):
            return Stub()
        try:
            return getattr(bpy.context, name)
        except Exception:
            return Stub()


class Self:
    def __init__(self, cls, entries):
        self._cls = cls
        self.layout = Rec(entries)
        self.bl_idname = getattr(cls, "bl_idname", None) or cls.__name__      # a real menu instance always has one

    def __getattr__(self, name):
        raw = inspect.getattr_static(self._cls, name)
        if inspect.isfunction(raw):                                         # a plain method: bind it to this stand-in
            return raw.__get__(self)
        return getattr(self._cls, name)                                     # static and class methods, values


def subclasses(c):
    for s in c.__subclasses__():
        yield s
        yield from subclasses(s)


menus, seen = [], set()
ctx = Ctx()
for cls in subclasses(bpy.types.Menu):
    idname = getattr(cls, "bl_idname", None) or cls.__name__
    if idname in seen or getattr(bpy.types, idname, None) is None:
        continue
    seen.add(idname)
    entries, err = [], None
    try:
        cls.draw(Self(cls, entries), ctx)
    except Exception as e:
        err = f"{type(e).__name__}: {str(e).splitlines()[0][:160]}" if str(e) else type(e).__name__
    menus.append(dict(id=idname, label=getattr(cls, "bl_label", ""), entries=entries, error=err))

# A menu that failed for want of another kind of active object is drawn again with one of each kind active, first in
# object mode, then in edit mode; the first full draw is kept, with the object it needed.
def kinds():
    out = []
    for kind, make in (("ARMATURE", lambda: bpy.data.armatures.new("A")), ("CURVE", lambda: bpy.data.curves.new("C", "CURVE")),
                       ("FONT", lambda: bpy.data.curves.new("T", "FONT")), ("GREASEPENCIL", lambda: bpy.data.grease_pencils_v3.new("G")),
                       ("CURVES", lambda: bpy.data.hair_curves.new("H")), ("MESH", lambda: bpy.data.meshes.new("M"))):
        try:
            ob = bpy.data.objects.new(kind.lower(), make())
            bpy.context.scene.collection.objects.link(ob)
            out.append((kind, ob))
        except Exception as e:
            print("KIND", kind, type(e).__name__, e)
    return out


retried = 0
for kind, ob in kinds():
    for mode in ("OBJECT", "EDIT"):
        failed = [m for m in menus if m["error"]]
        if not failed:
            break
        bpy.context.view_layer.objects.active = ob
        try:
            if mode == "EDIT":
                bpy.ops.object.mode_set(mode="EDIT")
        except Exception as e:
            print("MODE", kind, type(e).__name__, str(e)[:80])
            continue
        for m in failed:
            cls = getattr(bpy.types, m["id"])
            entries = []
            try:
                cls.draw(Self(cls, entries), ctx)
            except Exception:
                continue
            m.update(entries=entries, error=None, drawn_with=f"{kind} in {mode.lower()} mode")
            retried += 1
        try:
            bpy.ops.object.mode_set(mode="OBJECT")
        except Exception:
            pass
print("RETRIED", retried, "still failing:", [m["id"] for m in menus if m["error"]])
menus.sort(key=lambda m: m["id"])


RES = bpy.utils.resource_path("LOCAL")              # Blender's own scripts and presets: <resources>/scripts/...


def dump(name, rows_):
    text = "".join(json.dumps(r, sort_keys=True, default=str) + "\n" for r in rows_)
    text = text.replace(RES, "<resources>").replace(os.path.expanduser("~"), "~")   # no machine's paths in the repo
    with open(os.path.join(INV, name), "wb") as f:
        f.write(gzip.compress(text.encode("utf-8"), mtime=0))


dump("keymap.jsonl.gz", rows)
dump("menus.jsonl.gz", menus)
meta = dict(blender=bpy.app.version_string, platform=sys.platform, keymaps=len(data), keymap_items=len(rows),
            macos_items_after_cmd_copies=sum(len(i["items"]) for _, _, i in got["final"]),
            params={k: plain(v) for k, v in got["params"].items()},
            menus=len(menus), menus_with_error=sum(1 for m in menus if m["error"]),
            menu_entries=sum(len(m["entries"]) for m in menus))
with open(os.path.join(INV, "ui_meta.json"), "w") as f:
    json.dump(meta, f, indent=1, sort_keys=True)
print("UI", json.dumps({k: v for k, v in meta.items() if k != "params"}), flush=True)
