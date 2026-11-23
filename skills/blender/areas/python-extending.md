# Extending Blender with Python: properties, classes, handlers, timers

Blender 4.5.14 LTS. Tags: `[inv]` read from Blender (`scripts/kb.py`), `[exp: path]` measured here, `[doc: link]`
Blender's documentation. Experiment: `experiments/extending/python_extending.py` in the source repository.

## What goes wrong most often

1. **Waiting for a timer or a msgbus notification in a background script.** Neither runs while a `-b` script runs:
   a timer due after 0.1 s had not fired after the script waited 1 s, and a `msgbus` subscription on
   `Object.location` was not notified when the location changed. Both are driven by Blender's event loop, which the
   script holds. Call the function directly instead, or use a handler. `[exp: experiments/extending/python_extending.py]`
2. **Handlers that vanish after loading a file.** `bpy.ops.wm.open_mainfile` removes every handler not decorated with
   `@bpy.app.handlers.persistent`: after opening a file only the persistent `frame_change_post` handler still ran, and a
   persistent `load_post` ran once. `[exp: experiments/extending/python_extending.py]`
3. **Expecting registered properties to come back by themselves.** In a Blender where the classes are not registered,
   a reopened file still holds the values as ID properties (`obj["bfg_settings"]` was a group with `depth`), but
   `obj.bfg_settings` does not exist until the `PropertyGroup` and the `PointerProperty` are registered again. Plain
   custom properties (`obj["note"]`) come back as they were. Only values that differ from the default are stored.
   `[exp: experiments/extending/python_extending.py]`
4. **An operator `bl_idname` that is not `category.name`.** `bl_idname = "BadName"` was refused at registration
   ("invalid bl_idname 'BadName', at position 0"); `"object.bfg_add_empties"` works and is called as
   `bpy.ops.object.bfg_add_empties(...)`. `[exp: experiments/extending/python_extending.py]`
5. **Rendering with no scene camera.** `bpy.ops.render.render()` raises `Cannot render, no camera`; set
   `scene.camera`. `[exp: experiments/extending/python_extending.py]`
6. **Python threads touching `bpy`.** Not supported; they crash Blender in ways that are hard to trace.
   `[doc: https://docs.blender.org/api/4.5/info_gotchas_threading.html]`

## Custom properties (ID properties)

Any ID (objects, meshes, materials, scenes...) and bones and pose bones hold custom properties set by subscript:

```python
ob["note"] = "hello"; ob["count"] = 3; ob["weights"] = [0.1, 0.2, 0.3]; ob["nested"] = {"a": 1, "b": [1, 2]}
ob.id_properties_ui("count").update(min=0, max=10, description="how many")
```

Lists come back as `IDPropertyArray`, dicts as `IDPropertyGroup` (`.to_dict()` gives plain Python). They are saved
with the file and need no registration. `[exp: experiments/extending/python_extending.py]` They are also what
drivers and geometry-node attributes can read by name.

## Registered properties and property groups

```python
class Settings(bpy.types.PropertyGroup):
    depth: bpy.props.FloatProperty(name="Depth", default=0.06, min=0.0, unit="LENGTH")   # annotations, not assignment
    label: bpy.props.StringProperty(default="slab")

bpy.utils.register_class(Settings)
bpy.types.Object.bfg_settings = bpy.props.PointerProperty(type=Settings)
bpy.types.Scene.bfg_count = bpy.props.IntProperty(default=7)
ob.bfg_settings.depth = 0.08
```

Works headless. Unregister in reverse order (`del bpy.types.Object.bfg_settings`, then
`bpy.utils.unregister_class(Settings)`). `[exp: experiments/extending/python_extending.py]`

## Operators

```python
class BFG_OT_add_empties(bpy.types.Operator):
    bl_idname = "object.bfg_add_empties"     # category.name, lower case
    bl_label = "Add Empties"
    bl_options = {"REGISTER", "UNDO"}
    count: bpy.props.IntProperty(default=2, min=1)

    def execute(self, context):
        ...
        return {"FINISHED"}

bpy.utils.register_class(BFG_OT_add_empties)
bpy.ops.object.bfg_add_empties(count=3)      # -> {'FINISHED'}, headless
```

`[exp: experiments/extending/python_extending.py]`. An operator is worth writing when something else (a menu, a key, a
user) needs to call it; a script can just call a function.

## Handlers

`bpy.app.handlers` in 4.5: `animation_playback_pre/post`, `annotation_pre/post`, `blend_import_pre/post`,
`composite_pre/post/cancel`, `depsgraph_update_pre/post`, `frame_change_pre/post`, `load_pre/post/post_fail`,
`load_factory_preferences_post`, `load_factory_startup_post`, `object_bake_pre/complete/cancel`, `redo_pre/post`,
`render_init/pre/post/stats/write/complete/cancel`, `save_pre/post/post_fail`, `translation_update_post`,
`undo_pre/post`, `version_update`, `xr_session_start_pre`. `[exp: experiments/extending/python_extending.py]`

In background mode `frame_change_post` (6 calls over 3 `frame_set` and 2 renders), `depsgraph_update_post`,
`render_post` and `save_post` all fired. Handlers take `(scene, depsgraph)` for frame and depsgraph events. Mark a
handler `@persistent` if it must survive loading a file. `[exp: experiments/extending/python_extending.py]`

```python
from bpy.app.handlers import persistent

@persistent
def on_frame(scene, depsgraph):
    ...
bpy.app.handlers.frame_change_post.append(on_frame)
```

## Timers and msgbus

`bpy.app.timers.register(fn, first_interval=...)` and `bpy.msgbus.subscribe_rna(...)` belong to an interactive
Blender (a live session, an add-on): neither ran in a background script. `[exp: experiments/extending/python_extending.py]`
In a live Blender, a timer is the safe way to run work on the main thread, including work handed over from another
thread through a queue. [doc: https://docs.blender.org/api/4.5/bpy.app.timers.html]
