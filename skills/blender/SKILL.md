---
name: blender
description: Use whenever a task touches Blender or its Python API (bpy) — writing, running or debugging a Blender script; building meshes from data; modifiers and booleans; geometry nodes; materials and shader nodes; lights, world and camera; rendering with Cycles or EEVEE (headless or not); compositing and render passes; cloth, rigid-body and other simulation; armatures, skinning, poses, keyframes and actions; importing or exporting glTF, OBJ, USD, FBX, STL or PLY; or driving a live Blender. Written for Blender 4.5 LTS from what Blender reports about itself (every type, property, operator and node socket, searchable with kb.py), experiments run headless, and lessons from real projects.
---

# Blender 4.5, for an agent

Your memory of Blender mixes versions 2.7 to 4.x. Much of what you remember was renamed, moved or removed (auto smooth,
the EEVEE engine id, Principled BSDF's inputs, node-group sockets, context overrides, actions). This skill replaces
memory with things that can be checked. Paths below are relative to this file's folder.

## Before writing any Blender code

1. **Know the version.** `python3 scripts/run.py --which`. This guide is for 4.5.14 LTS. On another version, regenerate
   the inventory first (`scripts/run.py scripts/inventory.py`) and trust `kb.py` over the area pages.
2. **Look names up; don't recall them.** Every property, enum value, operator parameter and node socket name you are
   about to use: check it with `kb.py`. It answers in a fraction of a second, from Blender itself:

   ```bash
   python3 scripts/kb.py find smooth angle             # anything: types, properties, operators, nodes, Python
   python3 scripts/kb.py struct BooleanModifier        # properties with types, defaults, ranges, enum items
   python3 scripts/kb.py prop SceneEEVEE.use_shadows   # one property in full
   python3 scripts/kb.py path ClothSettings            # how to reach it: bpy.data.objects[...].modifiers[...]<ClothModifier>.settings
   python3 scripts/kb.py op object.modifier_apply      # an operator's parameters
   python3 scripts/kb.py node "Principled BSDF"        # sockets: name, identifier, type, default; * = hidden by default
   python3 scripts/kb.py nodes geometry curve          # node types of one tree, filtered
   python3 scripts/kb.py py bmesh.ops.bevel            # Python helpers with their real argument names
   python3 scripts/kb.py enums                         # machine-dependent enums: engines, view transforms, colour spaces, GPU
   python3 scripts/kb.py factory render                # what a fresh file starts with
   ```
3. **Read the area page** for the task (below). Each opens with what agents most often get wrong there. When an error
   comes back, search `areas/errors.md` for its words first.
4. **For anything the pages don't cover**, search Blender's own manual and Python reference offline:
   `python3 scripts/docs.py search TERM...` (run `docs.py fetch` once; it prints public URLs to cite).
5. **Need an HDRI, a texture or a model?** Fetch a free (CC0) one instead of modelling a stand-in:
   `python3 scripts/assets.py search texture brick wall`, then `assets.py get polyhaven red_brick`, and build it in
   Blender with `scripts/asset_import.py` (a world, a material at real-world size, an imported model).
   → `areas/remote-assets.md`

## How to work

- **Headless by default**, through `python3 scripts/run.py SCRIPT.py -- ARGS`. It uses factory settings, makes a
  Python error fail the run (without `--python-exit-code 1` Blender exits 0 after a traceback), and streams printed
  lines (a plain `print()` inside Blender is otherwise held until the end). See `areas/running.md`.
- **Data API first, operators second.** Most operators assume a window, an area or a selection; in background mode
  `bpy.context.area` is `None`, so view-dependent operators fail their poll as called. Where an operator is the only
  way, give it the context it needs with `bpy.context.temp_override(...)`: the screen's own 3D View area works headless
  (`areas/data-model.md`). Creating 1,000 cubes took 15.2 s with `primitive_cube_add` and 0.05 s through the data API.
- **Registered defaults are not always where a new thing starts.** The Mesh Boolean node is registered with
  `INTERSECT` but `nodes.new` gives `DIFFERENCE`; a new Copy Location constraint copies X, Y and Z although `use_x` is
  registered False; Track To starts at `TRACK_NEGATIVE_Z`/`UP_Y`, the Sky Texture at `NISHITA`, Noise at `FBM`. For
  nodes, modifiers and constraints `kb.py` prints both ("a new one starts at ..."); scene settings a fresh file holds
  are in `kb.py factory` (e.g. `scene.render.bake.normal_space` is `TANGENT`, registered `OBJECT`); for anything else,
  read the value from the object you made.
- **Some enum lists depend on state.** `Curve.fill_mode` lists FULL, BACK, FRONT, HALF for a 3D curve, but a new curve
  is 2D, starts at `NONE` and also accepts `BOTH`. When `kb.py` and Blender disagree on an enum, assign a wrong value
  and read the `TypeError`: it lists what this object accepts now.
- **`kb.py` also knows functions** (`find set_sharp_from_angle`) **and what Blender defines in Python** (`prop
  Mesh.shade_smooth`, `struct Object` shows `children`, `evaluated_geometry`): a name missing from the API's property
  lists may still exist.
- **Check with numbers, not by eye.** Read back what you made: vertex and face counts, bounding boxes, the evaluated
  mesh (`obj.evaluated_get(depsgraph)`), distances with `mathutils.bvhtree`, a light's rotation, a node's links.
  Save the `.blend`, open it again, and read the values from the file.
- **Then look.** Render small (256 to 512 px, few samples), save a PNG, and view it. One change at a time.
- **Keep references, not names.** A new data-block can get `.001`; references to vertices, bones or points die when the
  mode changes or elements are added (`areas/running.md`).
- **Mind the machine.** An empty headless Blender takes about 175 MB, a 1M-vertex mesh about 1 GB, a cloth
  simulation on a figure about 2 GB. Run at most four Blender jobs at once on 16 GB.

## A headless script's skeleton

Each line answers a measured trap (`areas/running.md`, `areas/data-model.md`):

```python
import sys
import bpy

sys.stdout.reconfigure(line_buffering=True)                 # otherwise print() is held until the script ends
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []   # the script's own arguments
bpy.ops.wm.read_factory_settings(use_empty=True)             # a known, empty scene (no camera, light or world)
scene = bpy.context.scene

# ... build with the data API (bpy.data.*.new, collection.objects.link), not operators in loops ...

bpy.context.view_layer.update()                              # matrices, dimensions, drivers, constraints
# read back what you made and check it with numbers here; raise if it is wrong, so the run fails
bpy.ops.wm.save_as_mainfile(filepath=argv[0])                # data nothing uses is not saved
```

Run it with `python3 scripts/run.py script.py -- out.blend` (exit code 1 on any error). An empty scene has no camera:
rendering it raises, and a failed render sets the exit code to 1 even if caught.

## Areas

| Page | What it covers |
|---|---|
| `areas/errors.md` | error messages met in 4.5, each with its cause, fix and page: search it for the words of your error |
| `areas/glossary.md` | Blender's words (data-block, original vs evaluated, depsgraph, RNA, poll, context, attribute domains, view transform, slots...), each pointing to where it is measured |
| `areas/running.md` | running headless, exit codes, output, arguments, background context, drivers, command-line rendering, memory, crashes, add-ons and extensions, bpy as a module, a live Blender |
| `areas/data-model.md` | objects, data and the evaluated depsgraph; context and `temp_override`; collections; files, append and link; `mathutils` |
| `areas/meshes.md` | meshes from arrays, reading them back, normals and smooth shading in 4.1+, attributes, `bmesh` |
| `areas/modifiers.md` | adding, ordering, evaluating and applying modifiers; Boolean solvers; the common modifiers |
| `areas/geometry-nodes.md` | node groups built from Python with the 4.x interface API, modifier inputs, reading results |
| `areas/curves-text.md` | Bezier and poly curves, bevels, curve to mesh, text |
| `areas/remote-assets.md` | free CC0 HDRIs, textures and models from Poly Haven and ambientCG: `assets.py` to search and fetch (cached, checked), `asset_import.py` for a world (and its sun), a material at real-world size, an imported model |
| `areas/instancing-assets.md` | full copies, linked duplicates, collection and vertex instancing, particle systems (costs measured); hair curves; assets and Blender's bundled ones |
| `areas/uv-images.md` | UV maps (from arrays, bmesh, unwrap operators headless, packing); images: colour spaces, pixels, saving, packing |
| `areas/materials.md` | Principled BSDF in 4.5, textures, bump and normal maps, displacement, colour spaces |
| `areas/light-world-camera.md` | light types and units, sky and HDRI worlds, shadow catcher, camera lens and framing |
| `areas/rendering.md` | Cycles on Metal and CPU, samples, denoising, EEVEE in 4.5, view transforms, output |
| `areas/lines.md` | Grease Pencil strokes from Python (the 4.3+ data), its materials and rendering, Line Art, Freestyle |
| `areas/compositing.md` | render passes, the compositor in background mode, multilayer EXR |
| `areas/export-baking.md` | glTF, OBJ, USD, FBX, STL, PLY: what survives; baking textures |
| `areas/animation-video.md` | rendering frame ranges headless, video containers and codecs, the sequencer (4.4+ names), turntables, motion blur, time per frame |
| `areas/sculpt-paint.md` | which sculpt and paint operators run headless (and which crash), colour attributes, vertex groups in shaders, painting textures by pixels |
| `areas/volumes-fluids.md` | mesh to volume and back, SDF grids, OpenVDB files, rendering volumes, Mantaflow bakes and their caches |
| `areas/simulation.md` | cloth, rigid bodies, soft bodies, simulation zones; baking headless; caches |
| `areas/python-extending.md` | custom properties, property groups, operators, handlers (and @persistent), timers and msgbus (not in background mode) |
| `areas/rigging-animation.md` | armatures from Python, automatic weights, poses, keyframes and 4.4+ actions, shape keys, drivers |

Lessons from real projects, by area, with what was measured: `../../kb/lessons/` in the source repository.

Generated reference, exact for 4.5 (`../../kb/reference/`): every shader, geometry, compositor and texture node with
all its sockets and settings, every modifier and constraint with every setting, scene, render, Cycles, EEVEE, light,
camera and world settings with what a fresh file starts with, all 2,482 operators, and `bmesh.ops`, `mathutils` and
`bpy_extras`. Each entry links to its manual page. Grep it, or ask `kb.py` for one item.

## Version traps

What an agent's memory most often gets wrong in 4.5, one line each; the page has the evidence.

**Running**
- A script that raises still exits 0 without `--python-exit-code 1`; `print()` is held until the end through a pipe,
  and `PYTHONUNBUFFERED` does nothing inside Blender. → `running.md`
- `bpy.app.timers` and `bpy.msgbus` never fire in a `-b` script; handlers do, but only `@persistent` ones survive
  `open_mainfile`. → `python-extending.md`
- Context-dict overrides (`bpy.ops.x(ctx, ...)`) raise `ValueError`; use `bpy.context.temp_override(...)`, which also
  accepts misspelt keywords silently. → `data-model.md`
- `scene.update()` and `scene.objects.link()` are gone: `view_layer.update()`, `collection.objects.link()`.
  `matrix_world` and `dimensions` stay stale until `view_layer.update()`. → `data-model.md`
- `bpy.data.objects.remove` leaves `None` in `view_layer.objects` until `view_layer.update()`, so deleting the factory
  cube and then looping over the view layer raises `AttributeError`; start from the empty file instead. → `data-model.md`

**Meshes, modifiers, geometry nodes**
- Auto smooth is gone (`use_auto_smooth`, `calc_normals_split`); `shade_auto_smooth` is CANCELLED headless; append
  "Smooth by Angle" from Blender's bundled assets instead. Custom normals, `sharp_face`, creases and bevel weights are
  attributes. → `meshes.md`
- Importers are `wm.obj_import`, `wm.ply_import`, `wm.stl_import` (the `import_scene.obj` family is gone). → `data-model.md`
- `node_group.inputs.new` is gone: `interface.new_socket`; modifier inputs are keyed `Socket_N` (`mod["Name"]` silently
  makes an unrelated property); call `ob.update_tag()` after setting one. → `geometry-nodes.md`
- Boolean: the modifier's solvers are `FAST`/`EXACT`/`MANIFOLD` (default EXACT), the node's `FLOAT`/`EXACT`/`MANIFOLD`;
  Manifold returns the mesh uncut, with only a console warning, when a cutter is open. → `modifiers.md`
- `new_from_object(original)` gives the base mesh, not the modified one; evaluate first. → `modifiers.md`

**Materials, light, rendering**
- Principled BSDF inputs were renamed in 4.0 (`Subsurface` → `Subsurface Weight`, `Specular` → `Specular IOR Level`,
  `Emission` → `Emission Color`, ...); index order changed too. Musgrave Texture is gone (merged into Noise). → `materials.md`
- `bpy.data.materials.new()` has no node tree until `use_nodes = True`; `Emission Strength` defaults to 0. → `materials.md`
- The EEVEE engine id is `BLENDER_EEVEE_NEXT`; `use_soft_shadows`, `use_contact_shadow` and other 4.1 EEVEE settings
  are gone. → `rendering.md`, `light-world-camera.md`
- Cycles renders on the CPU unless the Metal device is chosen; this Mac's only denoiser is `OPENIMAGEDENOISE`. → `rendering.md`
- The default view transform is AgX: linear 1.0 renders as byte 197, not 255. `image.save_render` applies it,
  `image.save` doesn't. → `rendering.md`, `uv-images.md`
- `is_shadow_catcher` is on the object (`Object.is_shadow_catcher`), not `object.cycles`. → `light-world-camera.md`
- A sun shines down its local -Z: for elevation e and bearing b, `rotation_euler = (radians(90 - e), 0,
  radians(180 - b))`; a Nishita sky's `sun_rotation` is the bearing. Light linking is on the light's object
  (`light_linking.receiver_collection`, `blocker_collection`); each entry's `link_state` is on
  `collection.collection_objects[i].light_linking`, which has no `.object`. → `light-world-camera.md`

**UVs, images, lines**
- Smart UV Project's angle is in radians and silently clamped (passing 66 means 90°); `pack_islands` needs
  `use_uv_select_sync`; `uv_layer.data` is deprecated. → `uv-images.md`
- A new float image saved to EXR is sRGB-encoded unless it is `Non-Color` before its pixels are written; unused data
  (an image nobody uses) is dropped on save. → `uv-images.md`
- Grease Pencil was rewritten in 4.3: `bpy.data.grease_pencils_v3`, `drawing.add_strokes()`; the old types remain for
  annotations, so old code runs and draws nothing. → `lines.md`

**Simulation**
- Jumping frames does not simulate: from frame 1 to 60 a cloth took one solver step over the gap and fell 4.9 m
  through its collider; a rigid body world did nothing. Step frame by frame or bake. → `simulation.md`
- `ptcache.bake` fails its poll headless without `temp_override(point_cache=...)`; `bake_all` works. → `simulation.md`
- Setting almost any cloth or collider property, even to the value it already has, throws away the unbaked frames
  after the current one; a baked cache survives. → `simulation.md`
- Cloth pins at weight 1.0 are exact and do not collide; at 0.99 they are springs that seams can pull 15 cm. A scene
  has no rigid body world until one is added; a MESH collision shape rests 36.6 mm high at the default margin. → `simulation.md`

**Rigging and animation**
- Edit bones exist only in edit mode, and `mode_set` acts on the real active object (`temp_override(active_object=)`
  does not redirect it); a zero-length bone is deleted silently on leaving edit mode. → `rigging-animation.md`
- `parent_set(type="ARMATURE_AUTO")` with the mesh unselected reports FINISHED and does nothing. → `rigging-animation.md`
- Pose bones default to QUATERNION; pose and world matrices are stale until `view_layer.update()`. → `rigging-animation.md`
- Actions are slotted since 4.4: keyed curves live in `action.layers[...].strips[...].channelbag(slot)`; an object given
  another object's action does not move until its slot is set; shape-key animation is on the Key data-block.
  → `rigging-animation.md`

**Animation, video, sculpt, volumes**
- Keyframes made from Python are BEZIER (a turntable eases in and out: 1.8° on its first frame, 22.4° mid-way); set
  each key's `interpolation = "LINEAR"`; the preference for new keys does not reach `keyframe_insert`. → `animation-video.md`
- `-s 2 -e 4 -a` renders frames 2 to 4, but `-a -s 2 -e 4` renders the whole range: arguments apply in order. → `animation-video.md`
- The sequencer's types were renamed in 4.4 (`Sequence` and friends are gone from `bpy.types`; `.sequences` still works,
  deprecated); a new scene's `sequence_editor` is None until `sequence_editor_create()`. → `animation-video.md`
- `scene.eevee.use_motion_blur` is gone: `render.use_motion_blur` covers both engines. → `animation-video.md`
- An F-modifier (Cycles, to loop) added after a `frame_set` is ignored until `action.update_tag()`; a keyed node
  input's action is on `mat.node_tree`, not the material; a Geometry Nodes input is keyed on the object as
  `modifiers["GN"]["Socket_2"]`. → `animation-video.md`
- The sculpt mesh filter segfaults headless unless an undo step was pushed first (`bpy.ops.ed.undo_push()`); the cloth
  filter does nothing; `weight_paint` strokes crash. → `sculpt-paint.md`
- EEVEE reads a vertex group through the Attribute node as 0; copy it into a FLOAT attribute. → `sculpt-paint.md`
- Saving a volume's original data-block writes an empty `.vdb`: only the evaluated volume has grids. A Principled
  Volume wired to Surface renders black. `fluid.bake_all` needs an active domain (`temp_override(object=...,
  active_object=...)`), and `free_all` returns before it finishes. → `volumes-fluids.md`

**Compositing and export**
- In background mode `bpy.data.images["Render Result"]` has 0 pixels, `bpy` loads a multilayer EXR as size (0, 0), and
  the Viewer node's image is a placeholder: save to files and read them back (OpenImageIO is bundled). → `compositing.md`
- The compositor is still `scene.node_tree` (with `scene.use_nodes`) in 4.5. → `compositing.md`
- `export_scene.obj` and `export_mesh.stl/ply` are gone (`wm.obj_export`, ...); glTF does not apply modifiers unless
  `export_apply=True`, drops procedural textures (bake them first), and writes Specular IOR Level doubled. → `export-baking.md`
- A Cycles bake with no image node selected returns CANCELLED silently. → `export-baking.md`
- A failed render sets Blender's exit code to 1 even when the script catches the error. → `running.md`
