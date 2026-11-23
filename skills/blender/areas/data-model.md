# Blender's data model from Python

Objects, their data and the evaluated depsgraph; context and `temp_override`; collections; removing data; `.blend`
files, append and link; operators against the data API; `mathutils`; importing OBJ, PLY and STL.

Blender 4.5.14 LTS on Apple Silicon. Tags: `[inv]` read from Blender (`scripts/kb.py`), `[exp: path]` measured here
(paths relative to the source repository), `[lesson]` from a real project, `[doc: link]` Blender's documentation.

## What goes wrong most often

1. **Reading derived values right after a change.** After `obj.location = (1, 2, 3)`, `obj.matrix_world` still read
   (0, 0, 0); after `bpy.context.view_layer.update()` it read (1, 2, 3). The same held for `obj.dimensions` after a
   scale change and for a new constraint's effect. `[exp: experiments/data/objects_data_depsgraph.py]`
   `[exp: experiments/meshes/units_scale.py]` "you need to call `bpy.types.ViewLayer.update` after modifying values".
   `[doc: https://docs.blender.org/api/4.5/info_gotchas_internal_data_and_python_objects.html]`
2. **Context overrides the 3.x way.** Passing a dict (`bpy.context.copy()` with changes) as an operator's first
   argument raises `ValueError: 1-2 args execution context is supported`. Use
   `with bpy.context.temp_override(object=ob, active_object=ob, ...):`. `[exp: experiments/modifiers/evaluate_and_apply.py]`
   `temp_override` accepted an unknown keyword without complaint, so a typo in a member name fails silently.
   `[exp: experiments/data/context_background.py]`
3. **Operators that act on "the" active or selected object.** Without an override `modifier_apply` applied the active
   object, not the intended one; with nothing selected, `object.delete` and `transform.translate` returned CANCELLED
   without raising. Check the returned set. `[exp: experiments/modifiers/evaluate_and_apply.py]`
   `[exp: experiments/data/context_background.py]`
4. **Operators in a loop.** 1,000 `primitive_cube_add` calls took 15.2 s and got slower as the scene filled (1.2 s for
   the first 250, 6.4 s for the last 250); 1,000 objects through `bpy.data` took 0.05 s with a mesh each and 0.009 s
   sharing one mesh. Moving 1,000 objects: one `transform.translate` 37 ms, a Python loop over `location` 1.4 ms.
   `[exp: experiments/data/ops_vs_data.py]`
5. **New objects that never show up.** `bpy.data.objects.new` puts the object in no collection: it is not in the scene
   and not evaluated. Link it: `bpy.context.scene.collection.objects.link(ob)`. An appended object is not linked
   either. `[exp: experiments/data/collections.py]` `[exp: experiments/data/blend_files.py]`
6. **Removing a mesh and expecting the object to stay.** `bpy.data.meshes.remove(mesh)` on a mesh an object used also
   deleted the object. Removing an object leaves its mesh behind with 0 users. `[exp: experiments/data/removal_orphans.py]`
7. **Old references after loading a file.** `bpy.ops.wm.open_mainfile` works inside a running script and the script
   carries on, but every Python reference from before raises `ReferenceError`. Re-fetch from `bpy.data` and
   `bpy.context`. `[exp: experiments/data/blend_files.py]`
8. **`*` for matrix products.** `Matrix * Vector` raises `TypeError: Element-wise multiplication: not supported between
   'Matrix' and 'Vector' types` (since 2.8); use `@`. `[exp: experiments/data/mathutils_basics.py]`
9. **BVH queries in the wrong space.** `BVHTree.FromObject(obj, depsgraph)` is in the object's local space: a
   world-space ray at a moved, scaled sphere missed. Transform the ray in, or build from world-space vertices.
   `[exp: experiments/data/bvh_kdtree.py]`
10. **Changing `rotation_mode` after setting the rotation.** Switching to `QUATERNION` converted the current Euler
    rotation into the quaternion, overwriting the one set before (it read identity). Set the mode first.
    `[exp: experiments/data/mathutils_basics.py]`
11. **Old import operator names.** `bpy.ops.import_scene.obj`, `import_mesh.ply`, `import_mesh.stl` and the matching
    exports are gone; the 4.x C++ ones are `bpy.ops.wm.obj_import`, `wm.ply_import`, `wm.stl_import` (and `_export`).
    `[exp: experiments/data/import_formats.py]`

## Objects, data, evaluated copies

An object holds a transform and points at data (a mesh, a curve, a camera, ...); an object with no data is an Empty.
`[exp: experiments/data/objects_data_depsgraph.py]`

```python
b = a.copy()                        # a linked duplicate: a new object sharing a's mesh (mesh.users == 2)
c = a.copy(); c.data = a.data.copy()   # an independent duplicate
bpy.context.scene.collection.objects.link(b)
```

The depsgraph evaluates modifiers, constraints, drivers and parenting into evaluated copies:

```python
dg = bpy.context.evaluated_depsgraph_get()   # the same object as bpy.context.view_layer.depsgraph
ea = a.evaluated_get(dg)                     # ea.is_evaluated True, ea.original == a, ea.data is another mesh
```

Writing to an evaluated object (`ea.location.x = 100`) raised nothing and left the original as it was.
`[exp: experiments/data/objects_data_depsgraph.py]` Reading evaluated meshes and applying modifiers: `modifiers.md`.

**When to call `view_layer.update()`:** before reading `matrix_world`, `dimensions`, a constraint's or a parent's
effect after you changed a transform, parent or constraint from Python. `evaluated_depsgraph_get()` also brings the
depsgraph up to date. Geometry-nodes inputs set as ID properties need `ob.update_tag()` first (`geometry-nodes.md`).
Writing vertex positions on a mesh without modifiers showed in the evaluated mesh at once.
`[exp: experiments/data/objects_data_depsgraph.py]` `[exp: experiments/geonodes/build_group.py]`

**Parenting**, copied from `experiments/data/objects_data_depsgraph.py` (parent P at x 10, child at x 1):

```python
k.parent = p                                          # child's world position becomes (11, 0, 0)
k2.parent = p
k2.matrix_parent_inverse = p.matrix_world.inverted()  # child stays at (1, 0, 0), like Ctrl+P
k3.parent = p
k3.matrix_world.translation = Vector((5, 5, 5))       # sets location to (-5, 5, 5): world (5, 5, 5) after update
```

## Context in background mode, and `temp_override`

In `-b` mode, `bpy.context` has a window, a screen ("Layout"), the scene, view layer and collection, but
`context.area` and `context.region` are None. `[exp: experiments/data/context_background.py]`

| operator, run headless with the object selected and active | result |
|---|---|
| `mesh.primitive_cube_add`, `primitive_uv_sphere_add` | FINISHED (new object active and selected) |
| `object.mode_set(mode='EDIT')`, `mesh.select_all`, `mesh.subdivide`, `mesh.extrude_region_move`, `mode_set(mode='OBJECT')` | FINISHED |
| `transform.translate`, `object.origin_set`, `object.duplicate`, `object.delete` | FINISHED |
| `object.join` with one object selected | CANCELLED ("No mesh data to join") |
| `view3d.snap_cursor_to_center`, `view3d.view_all` | poll() failed ("context is incorrect", "expected a view3d region") |
| `uv.smart_project` in object mode | poll() failed |

`[exp: experiments/data/context_background.py]`

`temp_override` sets context members for the operators called inside the block. Copied from experiments that ran:

```python
with bpy.context.temp_override(object=ob, active_object=ob):
    bpy.ops.object.modifier_apply(modifier="Sub")                 # modifiers/evaluate_and_apply.py

with bpy.context.temp_override(active_object=o, object=o, selected_objects=[o, c2], selected_editable_objects=[o, c2]):
    bpy.ops.object.join()                                         # data/context_background.py: joined the two
```

**View3D operators headless.** The background window's screen has a VIEW_3D area (its areas: PROPERTIES, OUTLINER,
DOPESHEET_EDITOR, VIEW_3D), and handing it over made `view3d.snap_cursor_to_center` and `view3d.view_all` run.
Copied from `experiments/data/context_background.py`:

```python
win = bpy.context.window_manager.windows[0]
area = next(a for a in win.screen.areas if a.type == "VIEW_3D")
region = next(r for r in area.regions if r.type == "WINDOW")
with bpy.context.temp_override(window=win, area=area, region=region):
    bpy.ops.view3d.snap_cursor_to_center()                        # FINISHED; cursor went from (1, 2, 3) to (0, 0, 0)
```

This depends on the startup file having that area; with `--factory-startup` it did. `temp_override` takes `window`,
`area`, `region` and "additional keywords override context members"; switching to full-screen or temporary screens
raises. `[doc: https://docs.blender.org/api/4.5/bpy.types.Context.html]` When an operator's poll fails, "typically
operators check for the active area type, a selection or active object". `[doc: https://docs.blender.org/api/4.5/info_gotchas_operators.html]`

## Collections

Copied from `experiments/data/collections.py`:

```python
sc.collection.objects.link(ob)                 # the scene's master collection ("Scene Collection")
col = bpy.data.collections.new("Parts")
sc.collection.children.link(col)               # a collection is in the scene only once linked under it
sub = bpy.data.collections.new("Sub"); col.children.link(sub)
sub.objects.link(ob)                           # an object can be in several collections
for c in list(ob.users_collection):            # move = unlink everywhere, link once
    c.objects.unlink(ob)
col.objects.link(ob)
```

- Linking an object twice into one collection raises `RuntimeError: Object 'lonely' already in collection ...`.
- With `--factory-startup` and an empty scene, `bpy.context.collection` is the scene collection.
- `scene.objects` lists objects in all nested collections.
- An Empty with `instance_type = 'COLLECTION'` and `instance_collection = col` instances the collection (seen in
  `depsgraph.object_instances`).

What removes an object from the viewport depsgraph (the one `evaluated_depsgraph_get()` returns in `-b`):
`layer_collection.exclude = True` and `collection.hide_viewport = True` removed it; `obj.hide_set(True)` removed it;
`collection.hide_render = True` did not. `[exp: experiments/data/collections.py]` What a final render includes was not
measured here.

## Removing data

```python
bpy.data.objects.remove(ob)                    # the mesh stays, with 0 users
bpy.data.orphans_purge(do_recursive=True)      # removes 0-user data, and what only they used
bpy.data.batch_remove(objs)                    # many at once
keep.use_fake_user = True                      # survives purge and saving
```

- After removing an object, its mesh had 0 users and its material 1 (from the orphan mesh). `orphans_purge()` with
  `do_recursive=False` removed the 6 orphan meshes and left the material; `do_recursive=True` removed it next.
- A Python reference to removed data raises `ReferenceError: StructRNA of type Object has been removed`.
- A 0-user datablock is not written to the `.blend`; one with `use_fake_user` is.
- Removing 2,000 empties: a loop of `objects.remove` 0.17 s, `bpy.data.batch_remove` 0.006 s.
- `BlendDataMeshes.remove(mesh, do_unlink=True, do_id_user=True, do_ui_user=True)`.

All: `[exp: experiments/data/removal_orphans.py]`

## `.blend` files

Copied from `experiments/data/blend_files.py`:

```python
bpy.ops.wm.save_as_mainfile(filepath=lib_path, copy=True)   # writes; bpy.data.filepath stays as it was
bpy.ops.wm.save_as_mainfile(filepath=main_path)             # writes and makes it the current file

with bpy.data.libraries.load(lib_path, link=False) as (src, dst):
    print(list(src.objects), list(src.materials))           # names available in the file
    dst.objects = ["Suzanne"]                               # append by name
ob = bpy.data.objects["Suzanne"]                            # appended: not in any scene yet
bpy.context.scene.collection.objects.link(ob)

with bpy.data.libraries.load(lib_path, link=True) as (src, dst):
    dst.collections = ["Heads"]
c = dst.collections[0]                                      # after the block, dst holds datablocks, not names
inst = bpy.data.objects.new("Heads_instance", None)
inst.instance_type = "COLLECTION"; inst.instance_collection = c
bpy.context.scene.collection.objects.link(inst)

bpy.ops.wm.open_mainfile(filepath=main_path)                # every old reference is now invalid
```

- An appended object brought its mesh and material. Appending it again made `Suzanne.001`; appending a material that
  existed twice already gave `Skin.002`. Use the returned `dst` datablocks, not the names you asked for.
- A linked object has `library` set and `is_editable` False, yet `location.x = 3` on it raised nothing.
- After `save_as_mainfile`, `bpy.data.is_dirty` still read True.
- `save_as_mainfile` options include `compress`, `relative_remap` and `copy`; `open_mainfile` has `load_ui` and
  `use_scripts`.

All: `[exp: experiments/data/blend_files.py]`

## Import OBJ, PLY, STL

```python
bpy.ops.wm.obj_export(filepath=path, export_selected_objects=True, export_materials=False)
bpy.ops.wm.obj_import(filepath=path)        # also wm.ply_import / wm.stl_import, wm.ply_export / wm.stl_export
```

A 16 x 8 UV sphere (114 vertices, 128 faces) exported and imported back, each in under 2 ms
`[exp: experiments/data/import_formats.py]`:

| format | imported vertices, faces | object rotation | world bounding box |
|---|---|---|---|
| OBJ | 114, 128 | (90, 0, 0) degrees | same as the source |
| PLY | 151, 128 (split along UV seams) | 0 | same |
| STL | 114, 224 (triangulated) | 0 | same |

The imported object is selected and named after the object (OBJ) or the file (PLY, STL). Import options include
`global_scale`, `forward_axis`, `up_axis` for all three, `validate_meshes` (OBJ), `use_mesh_validate` (STL) and
`merge_verts` (PLY). `[exp: experiments/data/import_formats.py]` `bpy.ops.wm.fbx_import` also exists in 4.5 next to
`import_scene.fbx` `[inv]`; neither was tried here.
Export details belong to `export-baking.md`.

## mathutils

Copied from `experiments/data/mathutils_basics.py`:

```python
M = Matrix.Translation((1, 2, 3)); R = Matrix.Rotation(math.radians(90), 4, "Z"); S = Matrix.Diagonal((2, 2, 2, 1))
TRS = M @ R @ S                                 # scale first, then rotate, then translate
lrs = Matrix.LocRotScale(Vector((1, 2, 3)), Euler((0, 0, math.radians(90))), Vector((2, 2, 2)))   # the same matrix
loc, rot, sca = TRS.decompose()                 # Vector, Quaternion, Vector
TRS.to_3x3() @ d                                # a direction (no translation)
NS.to_3x3().inverted().transposed() @ n         # a normal under non-uniform scale
direction.to_track_quat("-Z", "Y")              # aim -Z (a camera's view axis) along direction
loc_copy = ob.location.copy()                   # ob.location is live: it changes with the object
{Vector((1, 2, 3)).freeze(): 1}                 # a Vector is hashable only once frozen
```

- `Vector * Vector` is element-wise; `dot` and `cross` are methods.
- A 4x4 matrix applied to a 3D direction also translates it: (1, 0, 0) became (1, 4, 3) with the 4x4 and (0, 2, 0)
  with the 3x3.
- Under scale (1, 4, 1) the plain 3x3 turned the normal (0.707, 0.707, 0) into (0.24, 0.97, 0); the inverse transpose
  gave (0.97, 0.24, 0), which is the right one.
- `Euler` defaults to order XYZ. Assigning `ob.matrix_world = TRS` set location (1, 2, 3) and scale (2, 2, 2).

All: `[exp: experiments/data/mathutils_basics.py]`

**BVHTree and KDTree**, copied from `experiments/data/bvh_kdtree.py`:

```python
bvh = BVHTree.FromObject(s, dg)                       # local space, evaluated mesh (modifiers on)
mi = s.matrix_world.inverted()
o_local = mi @ Vector((5, 0, 10)); d_local = (mi.to_3x3() @ Vector((0, 0, -1))).normalized()
loc, nor, idx, dist = bvh.ray_cast(o_local, d_local)  # all None on a miss
hit_world = s.matrix_world @ loc

tris = me.loop_triangles                              # world-space tree instead
tri_idx = np.empty(len(tris) * 3, np.int32); tris.foreach_get("vertices", tri_idx)
bvh2 = BVHTree.FromPolygons(wco.tolist(), tri_idx.reshape(-1, 3).tolist(), all_triangles=True)

kd = KDTree(len(pts))
for i, p in enumerate(pts):
    kd.insert(p, i)
kd.balance()                                          # find() before balance() raises
co, index, dist = kd.find(q)
near5 = kd.find_n(q, 5)                               # sorted by distance
within = kd.find_range(q, 0.05)
```

- `FromObject(object, depsgraph, deform=True, render=False, cage=False, epsilon=0.0)`.
- On a sphere scaled 2x at x 5 (16,128 triangles): `FromObject` took 151 ms, `FromPolygons` 4 ms; both found the top
  at z 1.9993. `ray_cast(origin, direction, distance)` and `find_nearest(point, distance)` return four Nones beyond
  the distance.
- `overlap()` between two `FromObject` trees found 0 pairs (each in its own local space); between world-space trees,
  90.
- KDTree of 100,000 points: built and balanced in 0.03 s, `find()` 0.5 microseconds.

All: `[exp: experiments/data/bvh_kdtree.py]`

**mathutils.geometry**, from `experiments/data/geometry_funcs.py`:

- `delaunay_2d_cdt(vert_coords, edges, faces, output_type, epsilon, need_ids=True)` returns
  `(verts, edges, faces, orig_verts, orig_edges, orig_faces)`; vertices must be 2D (3D tuples raised "sequence
  length is 3, expected 2") `[inv]` `[exp]`. A 4x4 square with a 2x2 hole: given as edges only, no output type left the
  hole out (area 16, or 20 for type 3). Given as two faces (outer, inner), output type 2 gave 8 triangles of area 12
  and type 5 gave 2 faces of area 12 (hole left out); the inner loop's winding made no difference.
- `tessellate_polygon([outer, inner])` treated the second loop as a hole: 8 triangles, indices into the concatenated
  loops.
- `intersect_ray_tri(v1, v2, v3, ray, orig, clip=True)` `[inv]` takes the direction BEFORE the origin; it returned
  (0.2, 0.2, 0) for a hit and None for a triangle behind the ray.
- `intersect_line_plane(a, b, plane_co, plane_no)` treats the line as infinite; `intersect_point_line(pt, a, b)`
  returns (closest point, factor along a-b); `intersect_line_line` returns the two closest points of skew lines;
  `intersect_line_line_2d` works on segments and returns None when they do not cross.
- Also there: `area_tri`, `barycentric_transform`, `box_fit_2d`, `box_pack_2d`, `closest_point_on_tri`,
  `convex_hull_2d` (returns indices), `distance_point_to_plane`, `interpolate_bezier`, `intersect_line_sphere`,
  `intersect_plane_plane`, `intersect_point_tri`, `intersect_sphere_sphere_2d`, `intersect_tri_tri_2d`, `normal`,
  `points_in_planes`, `volume_tetrahedron`.

## Reference: changed between 2.8 and 4.5

| old | 4.5 | evidence |
|---|---|---|
| `bpy.ops.x.y(override_dict, ...)` | `with bpy.context.temp_override(**members): bpy.ops.x.y(...)` (3.2+) | `[exp: experiments/modifiers/evaluate_and_apply.py]` |
| `matrix * vector` (2.7x) | `matrix @ vector` | `[exp: experiments/data/mathutils_basics.py]` |
| `bpy.ops.import_scene.obj`, `export_scene.obj` | `bpy.ops.wm.obj_import`, `wm.obj_export` | `[exp: experiments/data/import_formats.py]` |
| `bpy.ops.import_mesh.ply` / `.stl`, `export_mesh.stl` | `bpy.ops.wm.ply_import` / `wm.stl_import`, `wm.ply_export` / `wm.stl_export` | `[exp: experiments/data/import_formats.py]` |
| `scene.objects.link(ob)` (2.7x) | `scene.collection.objects.link(ob)` or any collection's `objects.link` (`scene.objects` has no `link`) | `[exp: experiments/data/objects_data_depsgraph.py]` |
| `bpy.context.scene.update()` (2.7x) | `bpy.context.view_layer.update()` (`scene.update` does not exist) | `[exp: experiments/data/objects_data_depsgraph.py]` |
