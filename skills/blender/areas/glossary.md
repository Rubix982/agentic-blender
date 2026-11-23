# Glossary: Blender's words, for reading its API

Blender 4.5.14 LTS. Each term in a line or two, with where this guide measured it. Read this first if the Python
reference or an error message uses a word you don't know; most confusion in Blender scripting is a wrong idea of one of
these. Tags as elsewhere: `[inv]` read from Blender (`scripts/kb.py`), `[exp: path]` measured, `[doc: link]`.

## Data

- **Data-block (ID).** A named, saved unit of a `.blend`: an object, mesh, material, image, scene, node group, action...
  Every one lives in a `bpy.data` collection (`bpy.data.meshes`, `bpy.data.objects` and about 40 more) and derives from
  `bpy.types.ID`. `[inv]` [doc: https://docs.blender.org/manual/en/4.5/files/data_blocks.html]
- **Object vs object data.** An object (`bpy.data.objects`) is placement and settings: transform, parent, modifiers,
  constraints, material slots. Its `data` is the geometry or thing itself: a mesh, curve, light, camera, armature. Many
  objects can share one data-block (linked duplicates, `instancing-assets.md`). An object of type `EMPTY` has no data.
  Object types in 4.5: `MESH`, `CURVE`, `SURFACE`, `META`, `FONT`, `CURVES`, `POINTCLOUD`, `VOLUME`, `GREASEPENCIL`,
  `ARMATURE`, `LATTICE`, `EMPTY`, `LIGHT`, `LIGHT_PROBE`, `CAMERA`, `SPEAKER`. `[inv]`
- **Users, fake user, orphan.** A data-block counts who uses it (`users`). One with no users is an orphan and is **not
  written when the file is saved**; `use_fake_user = True` keeps it. `[exp: experiments/images/images.py]`
- **Linking an object into the scene.** `bpy.data.objects.new()` makes an object that is in no scene; it appears only
  after `collection.objects.link(obj)` (usually `scene.collection`). `data-model.md`
- **Collection.** A named set of objects, nested in a tree under `scene.collection`; also the unit for instancing and
  for excluding things per view layer. [doc: https://docs.blender.org/manual/en/4.5/scene_layout/collections/introduction.html]
- **View layer.** A scene's set of which collections are included and visible, with its own render passes. Objects can
  be in the scene but excluded from a view layer; `bpy.context.view_layer.update()` brings its evaluated state up to
  date. [doc: https://docs.blender.org/manual/en/4.5/scene_layout/view_layers/introduction.html]
- **Attribute.** Named per-element data on geometry: positions, UVs, colours, normals, creases, anything custom. Each
  has a **domain** (`POINT`, `EDGE`, `FACE`, `CORNER`, `CURVE`, `INSTANCE`, `LAYER`) and a **data type** (`FLOAT`,
  `FLOAT_VECTOR`, `FLOAT2`, `FLOAT_COLOR`, `BYTE_COLOR`, `BOOLEAN`, `INT`, `INT8`, `INT16_2D`, `INT32_2D`,
  `QUATERNION`, `FLOAT4X4`, `STRING`). In 4.x much that used to be special is an attribute: UV maps, `sharp_face`,
  `sharp_edge`, creases, bevel weights, custom normals. `[inv]` `meshes.md`
- **Corner (loop).** One face's use of one vertex. Per-corner data (UVs, split normals) lets a vertex have different
  values in each face around it; `mesh.loops` / `corner_vert` map corners to vertices. `meshes.md`, `uv-images.md`

## Evaluation

- **Original vs evaluated.** What you edit (`obj`, `obj.data`) is the original. What is drawn and rendered is the
  evaluated copy, after modifiers, constraints, drivers, animation and geometry nodes:
  `obj.evaluated_get(depsgraph)`, and `.to_mesh()` on it for the mesh. Reading the original mesh shows no modifier's
  effect. `data-model.md`, `modifiers.md`
- **Depsgraph (dependency graph).** Blender's record of what depends on what, which it uses to evaluate. Get it with
  `bpy.context.evaluated_depsgraph_get()`; it lists drawn instances in `depsgraph.object_instances`.
  [doc: https://docs.blender.org/api/4.5/bpy.types.Depsgraph.html]
- **Stale.** A value read before Blender re-evaluated: `matrix_world`, `dimensions`, pose matrices and drivers stay at
  their old values after a change until `bpy.context.view_layer.update()` (or `evaluated_depsgraph_get()`).
  `data-model.md`, `rigging-animation.md`
- **Instance.** Geometry drawn many times from one source (collection instances, vertex instancing, particles, geometry
  nodes' Instance on Points). Instances are not objects: count them in `depsgraph.object_instances`; make them real
  with `object.duplicates_make_real` or the Realize Instances node. `instancing-assets.md`, `geometry-nodes.md`

## Running code

- **`bpy.data`, `bpy.context`, `bpy.ops`, `bpy.types`.** All data-blocks of the open file; the current state (scene,
  active object, selection, mode, and in the UI the window and area); operators, the actions a user can run; the classes
  of everything. [doc: https://docs.blender.org/api/4.5/info_overview.html]
- **RNA.** Blender's description of its own data: every type, property, default, range and enum, which `bpy` is built on
  and which `kb.py` reads (`bl_rna`). [doc: https://docs.blender.org/api/4.5/bpy.types.bpy_struct.html]
- **Operator.** An action with a name like `object.select_all`, run as `bpy.ops.object.select_all(...)`; it works on
  the context (active object, selection, the area under the mouse) and returns `{'FINISHED'}`, `{'CANCELLED'}` or
  raises. Many have a data-API equivalent that is faster and needs no context: 1,000 cubes took 15.2 s with operators
  and 0.05 s through `bpy.data`. `data-model.md` [doc: https://docs.blender.org/api/4.5/bpy.ops.html]
- **Poll.** An operator's check that the context suits it. "poll() failed, context is incorrect" means a missing
  active object, wrong mode, or no suitable area. `running.md`, `data-model.md`
- **Context override.** `with bpy.context.temp_override(window=..., area=..., object=...):` runs operators with other
  context members; the 3.x dict form (`bpy.ops.x(ctx, ...)`) raises in 4.x. `data-model.md`
- **Area, region, space.** The UI's panels: an area (a 3D View, a node editor) has regions (header, main window) and a
  space with its settings. In background mode `bpy.context.area` is `None`, but the open file's screen still has areas
  you can pass to `temp_override`. `running.md` [doc: https://docs.blender.org/manual/en/4.5/interface/window_system/areas.html]
- **Mode.** Object, Edit, Sculpt, Pose, Weight Paint...: `object.mode_set(mode=...)` on the active object. Mesh data
  is held separately in edit mode, so references to vertices, bones or points die across a switch. `running.md`,
  `rigging-animation.md`
- **bmesh.** A separate, editable mesh structure for topology work (`bm.from_mesh(me)`, ops, `bm.to_mesh(me)`);
  `ensure_lookup_table()` before indexing. `meshes.md`
- **Handler, timer, msgbus.** Functions Blender calls on events (frame change, load, render...), after a delay, or when
  a property changes. Handlers fire in background mode; timers and msgbus don't. `python-extending.md`
- **Background mode (`-b`).** Blender without a window, run from the command line; what this guide's `scripts/run.py`
  uses. `running.md`

## Rendering and look

- **Render engine.** `CYCLES` (path tracing), `BLENDER_EEVEE_NEXT` (rasterised, real-time; the id changed in 4.2),
  `BLENDER_WORKBENCH` (viewport-style), `HYDRA_STORM`. `[inv]` `rendering.md`
- **Scene-linear, view transform, display.** Colours inside Blender are linear light. A view transform (AgX by default
  in 4.5, also Standard, Filmic, Khronos PBR Neutral...) maps them to the display; an EXR keeps the linear values, a PNG
  gets the transformed ones. `rendering.md`, `uv-images.md`
- **Colour space (of an image).** How an image's stored numbers are read: `sRGB` for colour pictures, `Non-Color` for
  data (roughness, normals, heights), `Linear Rec.709` for linear float images. `uv-images.md`, `materials.md`
- **Pass.** One component of a render written separately (depth, normal, AO, cryptomatte...), turned on per view layer.
  `compositing.md`
- **Principled BSDF.** The general physically based surface shader; its inputs were renamed in 4.0. `materials.md`

## Animation and simulation

- **Action, slot, channelbag, F-curve.** An action holds animation; since 4.4 it has slots (one per animated
  data-block) and the F-curves (one per animated property channel) live in a channelbag per slot. `rigging-animation.md`
- **Driver.** A property computed from others by an expression; Python-only expressions in a loaded file need
  auto-run (`-y`). `running.md`, `rigging-animation.md`
- **Point cache, bake.** Where a simulation stores its frames; baking fills it for a frame range so later frames can be
  read in any order. Unbaked simulations must be stepped frame by frame. `simulation.md`
- **Armature, bone, pose bone.** An armature object's data holds bones (rest positions, edited in edit mode); the
  object's pose holds pose bones (the posed transforms). `rigging-animation.md`
