# Error messages: what they mean in 4.5 and what fixes them

Blender 4.5.14 LTS. Every message here was produced by an experiment in this guide; search this page for the words of
the error you got. Each entry: the message, the cause measured, the fix, and the page with the details. Tags as
elsewhere.

## Context and operators

- **`Operator bpy.ops.<x>.poll() failed, context is incorrect`** — the operator needs something the context lacks: an
  active object, a selection, a mode (UV operators need edit mode), or a screen area (view3d, screen, sequencer and
  keyframe operators in background mode, where `bpy.context.area` is `None`). Fix: use the data API, or set the missing
  piece (select, make active, `mode_set`), or run it inside `bpy.context.temp_override(window=..., area=...,
  region=...)` with an area of the right type from `bpy.context.window.screen.areas`.
  `[exp: experiments/running/cli_behaviour.py]` `[exp: experiments/data/context_background.py]` → `running.md`, `data-model.md`
- **`Operator bpy.ops.view3d.view_all.poll() expected a view3d region`** — as above, with an area but not its `WINDOW`
  region; pass `region=` too. `[exp: experiments/data/context_background.py]` → `data-model.md`
- **`ValueError: 1-2 args execution context is supported`** — the 3.x way of overriding context (`bpy.ops.x(ctx_dict,
  ...)`); use `bpy.context.temp_override(...)`. `[exp: experiments/modifiers/evaluate_and_apply.py]` → `data-model.md`
- **`Error: Registering operator class: 'X', invalid bl_idname 'Y', at position 0`** — `bl_idname` must be
  `category.name` in lower case. `[exp: experiments/extending/python_extending.py]` → `python-extending.md`
- **`AttributeError: 'Calling operator "bpy.ops.export_scene.obj" error, could not be found'`** (also `import_scene.obj`,
  `export_mesh.stl`, `import_mesh.ply`...) — removed in 4.x; the C++ versions are `wm.obj_export`, `wm.obj_import`,
  `wm.stl_import`, `wm.ply_import`... `[exp: experiments/export/formats_roundtrip.py]` → `export-baking.md`,
  `data-model.md`

## Rendering

- **`Error: Cannot render, no camera`** — the scene has no `scene.camera`; an empty factory scene has none. A failed
  render also sets Blender's exit code to 1 even if the script catches it. `[exp: experiments/rendering/empty_scene_render.py]`
  `[exp: experiments/running/caught_errors.py]` → `running.md`, `rendering.md`
- **`TypeError: bpy_struct: item.attr = val: enum "BLENDER_EEVEE" not found in (...)`** — the EEVEE engine id is
  `BLENDER_EEVEE_NEXT` in 4.2 to 4.5; the message lists the valid values (the reliable way to read a dynamic enum).
  `[exp: experiments/rendering/eevee_background.py]` → `rendering.md`
- **`AttributeError: 'SceneEEVEE' object has no attribute 'use_soft_shadows'`** (also `use_ssr`, `use_bloom`,
  `shadow_method`, ...) — EEVEE settings removed in 4.2. `[exp: experiments/rendering/eevee_background.py]` → `rendering.md`
- **`TypeError ... "OPTIX" not found`** for `cycles.denoiser` — this Mac has only `OPENIMAGEDENOISE`.
  `[exp: experiments/rendering/cycles_denoisers.py]` → `rendering.md`
- **`Error: Current render engine does not support baking`** / **`No active UV layer found in the object`** — bake with
  Cycles, and give the mesh a UV map. A bake with no image node selected returns `{'CANCELLED'}` with no message.
  `[exp: experiments/export/cycles_bake.py]` → `export-baking.md`

## Materials and nodes

- **`KeyError: 'bpy_prop_collection[key]: key "Subsurface" not found'`** (also `Specular`, `Sheen`, `Clearcoat`,
  `Transmission`, `Emission`, ...) — Principled BSDF inputs renamed in 4.0 (`Subsurface Weight`, `Specular IOR Level`,
  `Coat Weight`, `Transmission Weight`, `Emission Color`...). `kb.py node "Principled BSDF"` lists the 4.5 names.
  `[exp: experiments/materials/principled_bsdf.py]` → `materials.md`
- **`RuntimeError: Error: Node type ShaderNodeTexMusgrave undefined`** — Musgrave Texture was merged into Noise Texture
  in 4.1 (its `noise_type`). `[exp: experiments/materials/procedural_textures.py]` → `materials.md`
- **`AttributeError: 'GeometryNodeTree' object has no attribute 'inputs'`** — group sockets are declared with
  `node_group.interface.new_socket(name, in_out=..., socket_type=...)` since 4.0. `[exp: experiments/geonodes/build_group.py]`
  → `geometry-nodes.md`
- **`TypeError: Cannot assign a 'float' value to the existing 'Socket_2' Int IDProperty`** — a geometry-nodes modifier
  input keeps its socket's type; assign an `int` to an integer socket. `[exp: experiments/geonodes/build_group.py]` →
  `geometry-nodes.md`
- **`TypeError: bpy_struct: item.attr = val: enum "FAST" not found`** on the Mesh Boolean node — the node's solvers are
  `FLOAT`/`EXACT`/`MANIFOLD`; `FAST` is the modifier's name. `[exp: experiments/geonodes/mesh_boolean_node.py]` →
  `geometry-nodes.md`
- **`RuntimeError: Error: Evaluated geometry from modifier does not contain a mesh`** — the node tree outputs instances
  only; add Realize Instances before applying. `[exp: experiments/geonodes/instances_realize.py]` → `geometry-nodes.md`
- **A segfault (exit -11) touching a Closure zone** — reading a Closure Input's `paired_output` or calling
  `pair_with_output` crashed 4.5.14. `[exp: experiments/geonodes/zone_paired_output.py]` → `geometry-nodes.md`

## Meshes, modifiers, attributes

- **`AttributeError: 'Mesh' object has no attribute 'use_auto_smooth'`** — removed in 4.1; use the Smooth by Angle
  node group (append it from Blender's assets) or `mesh.set_sharp_from_angle(angle=...)`.
  `[exp: experiments/meshes/smooth_normals.py]` → `meshes.md`
- **`IndexError: BMElemSeq[index]: outdated internal index table, run ensure_lookup_table() first`** — even right after
  `from_mesh`. `[exp: experiments/meshes/bmesh_basics.py]` → `meshes.md`
- **`ValueError: The mesh must be in editmode`** — `bmesh.from_edit_mesh` on a mesh not in edit mode.
  `[exp: experiments/meshes/bmesh_basics.py]` → `meshes.md`
- **`ValueError: context: 'FACE' not found in (['VERTS', 'EDGES', 'FACES_ONLY', ...])`** — bmesh ops take their own
  enum words (`bmesh.ops.delete(bm, geom=..., context="FACES")`); `kb.py py bmesh.ops.<op>` shows them.
  `[exp: experiments/meshes/bmesh_ops.py]` → `meshes.md`
- **`IndexError: bpy_prop_collection[index]: ...`** on an attribute you held — adding several attributes re-allocates
  them, and an old reference's `.data` goes empty; look the attribute up again by name.
  `[exp: experiments/meshes/attribute_stale_ref.py]` → `meshes.md`
- **`RuntimeError: Error: Attribute is required and can't be removed`** — `position` and the topology attributes can't
  be removed. `[exp: experiments/meshes/attributes.py]` → `meshes.md`
- **`RuntimeError: internal error setting the array`** — `foreach_set` given an array of the wrong length or a 2D array;
  pass a flat array of `count x components` values. `[exp: experiments/meshes/read_back_numpy.py]` → `meshes.md`
- **`RuntimeError: Error: Modifiers cannot be applied to multi-user data`** / **`... to a mesh with shape keys`** /
  **`Cannot apply to a multi user: Object ...`** — `modifier_apply` and `transform_apply` refuse shared meshes and shape
  keys; use `bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))` and swap the mesh in.
  `[exp: experiments/modifiers/evaluate_and_apply.py]` `[exp: experiments/meshes/units_scale.py]` → `modifiers.md`
- **`TypeError: ObjectModifiers.new(): error with argument 2, "type" - enum "SUBDIVISION" not found`** — the type is
  `SUBSURF`. `[exp: experiments/modifiers/order.py]` → `modifiers.md`

## Data and Python

- **`ReferenceError: StructRNA of type Object has been removed`** (or `Mesh`, `BMesh data ... has been removed`) — the
  data-block was removed, the file was reloaded (`open_mainfile` invalidates every reference), or an evaluated mesh was
  read after the next evaluation. Look it up again. `[exp: experiments/data/blend_files.py]`
  `[exp: experiments/modifiers/solidify_bevel.py]` → `data-model.md`
- **`ValueError: Cannot load from the current blend file.`** — `bpy.data.libraries.load` on the open file;
  `save_as_mainfile(..., copy=True)` keeps the open file elsewhere. `[exp: experiments/instancing/repeat_geometry.py]` →
  `instancing-assets.md`
- **`RuntimeError: Error: Object 'x' already in collection 'Scene Collection'`** — linking an object twice.
  `[exp: experiments/data/collections.py]` → `data-model.md`
- **`TypeError: Element-wise multiplication: not supported between 'Matrix' and 'Vector' types`** — matrix times vector
  is `@` since 2.8. `[exp: experiments/data/mathutils_basics.py]` → `data-model.md`
- **`TypeError: Vector is not frozen (mutable), call freeze first`** — a `Vector` used as a dict key or set member needs
  `.freeze()`. `[exp: experiments/data/mathutils_basics.py]` → `data-model.md`
- **`RuntimeError: KDTree must be balanced before calling find()`** — call `kd.balance()` after inserting.
  `[exp: experiments/data/bvh_kdtree.py]` → `data-model.md`
- **`ValueError: delaunay_2d_cdt: sequence length is 3, expected 2`** — it takes 2D points.
  `[exp: experiments/data/geometry_funcs.py]` → `data-model.md`
- **`ValueError: bpy_struct: item.attr = val: sequences of dimension 0 should contain 4 items, not 3`** — a poly or NURBS
  spline point's `co` is 4D (x, y, z, w). `[exp: experiments/curves/bezier_poly.py]` → `curves-text.md`
- **`RuntimeError: Error: Object does not have geometry data`** — `new_from_object` on a hair-curves object; convert with
  `object.convert` instead. `[exp: experiments/curves/hair_curves.py]` → `curves-text.md`

## Images

- **`RuntimeError: Error: Image 'x' does not have any image data`** — saving a float image again after its first save
  (it became a file image tied to the first path); save with `save_copy=True`. `[exp: experiments/images/images.py]` →
  `uv-images.md`
- **`Error: Could not write image: internal error, see console`** — a format that can't hold the image (JPEG 2000 at
  8 px tall, here). `[exp: experiments/rendering/output_formats.py]` → `rendering.md`

## Animation, video, sculpt, volumes

- **`RuntimeError: Error: Render width has to be 720 pixels for DV!`** — the DV codec takes only DV frame sizes; the
  other 18 container and codec pairs tried wrote a 128 px clip. `[exp: experiments/animation/video_codecs.py]` →
  `animation-video.md`
- **`Error: width not divisible by 2`** — H.264 and most codecs need even frame sizes. `[exp: experiments/animation/video_codecs.py]`
  → `animation-video.md`
- **`Operator bpy.ops.sequencer.image_strip_add.poll() failed`** / **`anim.keyframe_insert.poll() failed`** — use the
  data API: `sequence_editor.strips.new_image(...)`, `obj.keyframe_insert(data_path=..., frame=...)`.
  `[exp: experiments/animation/sequencer_join.py]` `[exp: experiments/animation/turntable.py]` → `animation-video.md`
- **A segfault from `sculpt.mesh_filter`** — push an undo step first (`bpy.ops.ed.undo_push()`); `weight_paint` strokes
  crash in `GPU_viewport` regardless. `[exp: experiments/sculpt/sculpt_ops_probe.py]` → `sculpt-paint.md`
- **`RuntimeError: Error: Vertex not in group`** — `vertex_group.weight(index)` on a vertex the group doesn't hold.
  `[exp: experiments/sculpt/vertex_groups_weights.py]` → `sculpt-paint.md`
- **`fluid.bake_all` poll failure** — needs the domain active: `temp_override(object=dom, active_object=dom)`.
  `[exp: experiments/volumes/fluid_bake.py]` → `volumes-fluids.md`

## Simulation and rigging

- **`RuntimeError: Error: Armature 'Rig' not in edit mode, cannot add an editbone`** — `armature.edit_bones` exist only
  in edit mode (`object.mode_set(mode="EDIT")` with the armature active). `[exp: experiments/rigging/armature_build.py]`
  → `rigging-animation.md`
- **`ptcache.bake` poll failure** — headless it needs `temp_override(point_cache=...)`; `ptcache.bake_all` works
  without. `[exp: experiments/simulation/cloth_bake.py]` → `simulation.md`

## Crashes (no message)

A segfault ends Blender with exit code −11 and a backtrace in `$TMPDIR/blender.crash.txt` (`running.md`). Crashes met
while writing this guide: the Closure zone from Python (above); holding references to vertices, bones or points across
a mode switch or after adding elements [doc: https://docs.blender.org/api/4.5/info_gotchas_crashes.html]; an attribute
reference after several `attributes.new` calls once segfaulted (not repeated) `[exp: experiments/meshes/attribute_stale_ref.py]`.
