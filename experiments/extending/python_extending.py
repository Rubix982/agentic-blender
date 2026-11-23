"""Extending Blender from Python in 4.5, headless: custom properties (ID properties) and registered properties, what
survives a save, classes registered at runtime (operators, property groups), app handlers (which fire in background
mode, and whether they survive loading a file), timers in background mode, and msgbus."""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy  # noqa: E402
from bpy.app.handlers import persistent  # noqa: E402

import exp  # noqa: E402

E = exp.Experiment(__file__)
BLEND = E.out("ext.blend")

# 1. ID properties: any ID (and bones, pose bones...) holds custom properties set by subscript.
ob = bpy.data.objects.new("Empty", None)
bpy.context.scene.collection.objects.link(ob)
ob["note"] = "hello"
ob["count"] = 3
ob["weights"] = [0.1, 0.2, 0.3]
ob["nested"] = {"a": 1, "b": [1, 2]}
ui = ob.id_properties_ui("count")
ui.update(min=0, max=10, description="how many")
E.fact("Custom properties are set by subscript on any ID (obj['name'] = value): strings, numbers, lists and nested "
       "dicts are accepted; id_properties_ui(name).update(min=, max=, description=) gives a number limits",
       keys=sorted(ob.keys()), weights_type=type(ob["weights"]).__name__, nested_type=type(ob["nested"]).__name__,
       ui=dict(ui.as_dict()))

# 2. A registered property on a type, and a PropertyGroup.
class Settings(bpy.types.PropertyGroup):
    depth: bpy.props.FloatProperty(name="Depth", default=0.06, min=0.0, unit="LENGTH")
    label: bpy.props.StringProperty(default="slab")


bpy.utils.register_class(Settings)
bpy.types.Object.bfg_settings = bpy.props.PointerProperty(type=Settings)
bpy.types.Scene.bfg_count = bpy.props.IntProperty(default=7)
ob.bfg_settings.depth = 0.08
bpy.context.scene.bfg_count = 11
E.fact("A PropertyGroup registered at runtime (bpy.utils.register_class) and attached with a PointerProperty works "
       "headless; class annotations (name: bpy.props.X(...)) declare its properties",
       depth=round(ob.bfg_settings.depth, 4), scene_count=bpy.context.scene.bfg_count,
       stored_as_id_property="bfg_settings" in ob.keys())

# 3. Operators registered at runtime, called headless.
class BFG_OT_add_empties(bpy.types.Operator):
    bl_idname = "object.bfg_add_empties"
    bl_label = "Add Empties"
    bl_options = {"REGISTER", "UNDO"}
    count: bpy.props.IntProperty(default=2, min=1)

    def execute(self, context):
        for i in range(self.count):
            e = bpy.data.objects.new(f"E{i}", None)
            context.scene.collection.objects.link(e)
        return {"FINISHED"}


bpy.utils.register_class(BFG_OT_add_empties)
n0 = len(bpy.data.objects)
r = bpy.ops.object.bfg_add_empties(count=3)
E.fact("An operator registered at runtime is callable headless as bpy.ops.<bl_idname>; its bl_idname must be "
       "'category.name' in lower case", result=str(r), objects_added=len(bpy.data.objects) - n0)
try:
    class BadOp(bpy.types.Operator):
        bl_idname = "BadName"
        bl_label = "Bad"

        def execute(self, context):
            return {"FINISHED"}
    bpy.utils.register_class(BadOp)
    bad = "registered"
except (RuntimeError, ValueError) as e:
    bad = "ERROR " + str(e).splitlines()[0][:160]
E.fact("An operator whose bl_idname is not 'category.name' is refused at registration", result=bad)

# 4. What survives save and reopen in a fresh Blender (no classes registered there).
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
probe = E.out("reopen_probe.py")
with open(probe, "w") as f:
    f.write("import bpy, json\n"
            "o = bpy.data.objects['Empty']\n"
            "print('REOPEN', json.dumps(dict(keys=sorted(o.keys()), note=o.get('note'), "
            "group=(o['bfg_settings'].to_dict() if 'bfg_settings' in o.keys() else None), "
            "has_attr=hasattr(o, 'bfg_settings'), scene_keys=sorted(bpy.context.scene.keys()))))\n")
import subprocess  # noqa: E402

out = subprocess.run([bpy.app.binary_path, "-b", "--factory-startup", BLEND, "--python", probe],
                     capture_output=True, text=True).stdout
line = [l for l in out.splitlines() if l.startswith("REOPEN")]
import json  # noqa: E402

reopened = json.loads(line[0][7:]) if line else out[-400:]
E.fact("Saved and reopened in a Blender where the classes are not registered: custom properties come back, and the "
       "registered properties' values are still in the file as ID properties (obj['bfg_settings'] holds a group), but "
       "obj.bfg_settings does not exist until the classes are registered again", reopened=reopened)

# 5. App handlers in background mode, and across loading a file.
calls = {"frame_change_post": 0, "depsgraph_update_post": 0, "load_post": 0, "save_post": 0,
         "render_post": 0, "plain_after_load": 0, "persistent_after_load": 0}


def on_frame(scene, depsgraph=None):
    calls["frame_change_post"] += 1


def on_dg(scene, depsgraph=None):
    calls["depsgraph_update_post"] += 1


@persistent
def on_load(*a):
    calls["load_post"] += 1


def on_save(*a):
    calls["save_post"] += 1


def on_render(*a):
    calls["render_post"] += 1


def plain(scene, depsgraph=None):
    calls["plain_after_load"] += 1


@persistent
def kept(scene, depsgraph=None):
    calls["persistent_after_load"] += 1


H = bpy.app.handlers
H.frame_change_post.append(on_frame)
H.depsgraph_update_post.append(on_dg)
H.load_post.append(on_load)
H.save_post.append(on_save)
H.render_post.append(on_render)
H.frame_change_post.append(plain)
H.frame_change_post.append(kept)
sc = bpy.context.scene
for f in (2, 3, 4):
    sc.frame_set(f)
ob.location.x = 1.0
bpy.context.view_layer.update()
try:
    bpy.ops.render.render(write_still=False)
    no_cam = "rendered"
except RuntimeError as e:
    no_cam = "ERROR " + str(e).splitlines()[0]
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
sc.collection.objects.link(cam)
sc.camera = cam
sc.render.engine = "BLENDER_WORKBENCH"
sc.render.resolution_x = sc.render.resolution_y = 32
sc.render.filepath = E.out("h.png")
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
before_load = dict(calls)
bpy.ops.wm.open_mainfile(filepath=BLEND)
for f in (5, 6):
    bpy.context.scene.frame_set(f)
E.fact("Handlers fire in background mode: frame_change_post (6 calls over 3 frame_set calls and 2 render calls), "
       "depsgraph_update_post, render_post, save_post. Opening a file removes every handler not marked @persistent: "
       "after open_mainfile only the persistent frame handler still fired, and the persistent load_post ran once. (render.render with no scene camera raises 'Cannot render, no "
       "camera'.)", render_without_camera=no_cam, before_load=before_load, after_load=dict(calls),
       handler_names=sorted(h for h in dir(H) if not h.startswith(("_", "n_")) and h not in ("persistent", "count", "index")))

# 6. Timers in background mode.
fired = []
bpy.app.timers.register(lambda: fired.append(time.time()) and None, first_interval=0.1)
t = time.time()
while time.time() - t < 1.0:
    time.sleep(0.05)
E.fact("bpy.app.timers do not fire while a background script runs: a timer due after 0.1 s had not fired after the "
       "script waited 1 s (timers run from Blender's event loop, which a -b script blocks)", fired=len(fired),
       is_registered=None)

# 7. msgbus.
owner = object()
seen = []
bpy.msgbus.subscribe_rna(key=(bpy.types.Object, "location"), owner=owner, args=(), notify=lambda: seen.append(1))
bpy.data.objects["Empty"].location.x = 5
bpy.context.view_layer.update()
E.fact("bpy.msgbus subscriptions are not notified in a background script (notifications are sent from the event loop, "
       "like timers)", notified=len(seen))
bpy.msgbus.clear_by_owner(owner)
for p in (BLEND, probe, E.out("h.png")):
    if os.path.exists(p):
        os.remove(p)
E.save()
