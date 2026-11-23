# Meshes from Python

Blender 4.5.14 LTS on Apple Silicon. Tags: `[inv]` read from Blender (`scripts/kb.py`), `[exp: path]` measured here
(paths are relative to the source repository), `[lesson]` from a real project, `[doc: link]` Blender's own
documentation. Timings were taken while other Blender jobs shared the machine; repeated runs moved by up to 2x, the
ratios much less.

## What goes wrong most often

1. **Auto smooth from memory.** `mesh.use_auto_smooth`, `auto_smooth_angle`, `calc_normals_split()`,
   `free_normals_split()` and `create_normals_split()` do not exist in 4.5; `mesh.use_auto_smooth = True` raises
   `AttributeError`. `[exp: experiments/meshes/smooth_normals.py]` The replacements:
   - `mesh.set_sharp_from_angle(angle=math.radians(30))` writes the `sharp_edge` attribute (data API, no context).
   - `bpy.ops.object.shade_smooth_by_angle(angle=..., keep_sharp_edges=True)` does the same through an operator; it runs
     headless on the active object and adds no modifier.
   - The **Smooth by Angle** modifier (a geometry-nodes asset) keeps it live. `bpy.ops.object.shade_auto_smooth()`,
     which adds it in the UI, returns `CANCELLED` headless with "Asset loading is unfinished", every time. Append the
     node group from the bundled file instead (code below). `[exp: experiments/meshes/smooth_normals.py]`
2. **`set_sharp_from_angle()` with no argument does nothing.** Its default angle is pi (180 degrees), so no edge is
   marked. Pass the angle. `[exp: experiments/meshes/smooth_normals.py]`
   `[doc: https://docs.blender.org/api/4.5/bpy.types.Mesh.html]`
3. **Smooth by Angle on a flat-shaded mesh marks every edge sharp.** A fresh primitive is flat shaded (a `sharp_face`
   attribute, True on every face). With the modifier's default "Ignore Sharpness" off, those flat faces are kept, and
   48 of 48 edges of a 16-sided cylinder came out sharp. Call `mesh.shade_smooth()` first (then 32: only the rims), or
   switch Ignore Sharpness on. `[exp: experiments/meshes/smooth_normals.py]`
4. **Building or reading big meshes element by element.** At 1M vertices, `from_pydata` with Python lists took 1.0 to
   1.8 s; `vertices.add` + `foreach_set` 0.33 to 0.37 s; writing through the attribute API (`position`,
   `.corner_vert`) 0.07 to 0.14 s. Reading positions: a Python loop 292 ms, `vertices.foreach_get("co")` 16 ms,
   `attributes["position"].data.foreach_get("vector")` 0.2 ms. `[exp: experiments/meshes/build_from_arrays.py]`
   `[exp: experiments/meshes/read_back_numpy.py]`
5. **The wrong array for `foreach_get`.** It wants a flat array of exactly the right length: a 2D `(n, 3)` array or a
   short one raises `RuntimeError: internal error setting the array` (the log line says "Array length mismatch").
   A `float64` array works but took 73 ms against 16 ms for `float32`. `[exp: experiments/meshes/read_back_numpy.py]`
6. **Keeping an attribute reference while adding attributes.** After 5 more `attributes.new` calls, the old
   reference's `.data` had length 0 (`IndexError`); after 1 or 2 it still worked. One longer run crashed Blender
   (exit -11). Re-fetch by name after adding. `[exp: experiments/meshes/attribute_stale_ref.py]` Adding elements
   re-allocates arrays and invalidates earlier references, and mode switches do the same.
   `[doc: https://docs.blender.org/api/4.5/info_gotchas_crashes.html]`
7. **`bm.verts[i]` without a lookup table.** It raises `IndexError: ... outdated internal index table` even right after
   `bm.from_mesh()`. Call `bm.verts.ensure_lookup_table()` (and again after adding elements).
   `[exp: experiments/meshes/bmesh_basics.py]`
8. **`bmesh.ops.bevel` bevels vertices unless told otherwise.** Its `affect` defaults to `'VERTICES'` `[inv]`; with
   `geom=bm.edges[:]` and no `affect` the result was a vertex bevel (96 verts, 62 faces), not an edge bevel (96, 98).
   Pass `affect='EDGES'`. `[exp: experiments/meshes/bmesh_ops.py]`
9. **`extrude_face_region` keeps the original face.** The extruded cube was not manifold (11 faces) until the old face
   was deleted (10 faces, manifold). The edit-mode extrude operator hides this. `[exp: experiments/meshes/bmesh_ops.py]`
10. **`validate()` is not a cleanup.** It removes broken faces (duplicates, two-vertex faces, repeated or out-of-range
    indices) but leaves coincident vertices alone. Merging is `bmesh.ops.remove_doubles` or the Weld modifier.
    `[exp: experiments/meshes/validate_broken.py]`
11. **`obj.dimensions` (and `matrix_world`) read right after a change.** After `obj.scale = (2, 1, 1)`, `dimensions`
    still read (2, 2, 2); after `bpy.context.view_layer.update()` it read (4, 2, 2).
    `[exp: experiments/meshes/units_scale.py]`

## Build a mesh from arrays

Small meshes: `from_pydata` is fine (it makes the edges too). Large ones: size the arrays, then write them in one call
each. Copied from `experiments/meshes/build_from_arrays.py` (`co` is a float32 `(n, 3)` array, `quads` an int32
`(f, 4)` array):

```python
me = bpy.data.meshes.new("grid")
nv, nf = len(co), len(quads)
me.vertices.add(nv)
me.attributes["position"].data.foreach_set("vector", co.ravel())      # or me.vertices.foreach_set("co", ...)
me.loops.add(nf * 4)
me.attributes[".corner_vert"].data.foreach_set("value", quads.ravel()) # or me.loops.foreach_set("vertex_index", ...)
me.polygons.add(nf)
me.polygons.foreach_set("loop_start", np.arange(0, nf * 4, 4, dtype=np.int32))
me.update(calc_edges=True)
ob = bpy.data.objects.new("grid", me)
bpy.context.scene.collection.objects.link(ob)
```

- Faces are defined by `loop_start` alone; `loop_total` follows from the next face's start. `polygon.loop_total = 4`
  raises "read-only"; `polygons.foreach_set("loop_total", ...)` raises nothing and is not needed.
  `[exp: experiments/meshes/build_from_arrays.py]`
- Edges: the mesh had 0 edges before `update()` and 180 after a plain `update()` (no `calc_edges`), so `update()`
  fills in missing edges; `calc_edges=True` forces a recalculation. `[exp: experiments/meshes/build_from_arrays.py]`
- Mixed polygon sizes: `loop_start` is the running sum of the sizes (`np.concatenate([[0], np.cumsum(sizes)[:-1]])`);
  untested here.

| vertices | `from_pydata` (incl. `tolist()`) | `vertices.add` + `foreach_set` + `update` | attribute route + `update` |
|---:|---:|---:|---:|
| 10,000 | 5 ms | 3 ms | 1 ms |
| 100,489 | 76 ms | 31 ms | 6 ms |
| 1,000,000 | 0.98 s | 0.33 s | 0.07 s |

`[exp: experiments/meshes/build_from_arrays.py]` (last run; `validate()` on the 1M grid took 0.16 s more)

## Check and clean what you built

`mesh.validate(verbose=False)` returns True when it changed something. What it did to small broken inputs
`[exp: experiments/meshes/validate_broken.py]`:

| input | before (v, e, f) | after | returned |
|---|---|---|---|
| the same quad twice | (4, 4, 2) | (4, 4, 1) | True |
| a face using one vertex twice | (4, 3, 1) | (4, 3, 0) | True |
| a two-vertex face | (3, 1, 1) | (3, 1, 0) | True |
| a face index past the vertex count (`from_pydata` accepted it) | (3, 3, 1) | (3, 1, 0) | True |
| two vertices on one spot | (4, 5, 2) | (4, 5, 2) | False |

Coincident vertices need merging: `bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)` took two overlapping
cubes from (16, 24, 12) to (8, 12, 6). `[exp: experiments/meshes/bmesh_ops.py]` Points on one spot are not harmless:
zero-length edges made a cloth simulation explode, depending on 0.03 mm in a hem. Report the shortest edge before
simulating. `[lesson: kb/lessons/cloth.md]`

## Read a mesh back into numpy

Copied from `experiments/meshes/read_back_numpy.py`:

```python
n = len(me.vertices)
co = np.empty(n * 3, np.float32)                       # flat, float32, exact length
me.attributes["position"].data.foreach_get("vector", co)
co = co.reshape(-1, 3)
corner_vert = np.empty(len(me.loops), np.int32)
me.attributes[".corner_vert"].data.foreach_get("value", corner_vert)
mw = np.array(ob.matrix_world)
world = co @ mw[:3, :3].T + mw[:3, 3]
pn = np.empty(len(me.polygons) * 3, np.float32)
me.polygons.foreach_get("normal", pn)
```

| read, 1M-vertex grid (3,992,004 corners) | time |
|---|---:|
| positions, `attributes["position"].data.foreach_get("vector", float32)` | 0.2 ms |
| positions, `vertices.foreach_get("co", float32)` | 16 ms |
| positions, `vertices.foreach_get("co", float64)` | 74 ms |
| positions, `[v.co[:] for v in me.vertices]` | 292 ms |
| corner vertices, `attributes[".corner_vert"]` | 0.3 ms |
| corner vertices, `loops.foreach_get("vertex_index")` (int32 or int64) | 156 ms |
| face normals, `polygons.foreach_get("normal")` | 34 ms |

`[exp: experiments/meshes/read_back_numpy.py]`. Read an evaluated mesh (after modifiers) the same way, from
`obj.evaluated_get(depsgraph).data`; see `modifiers.md`.

## Smooth shading and normals (4.1+)

Shading is data now: a face is flat when the boolean FACE attribute `sharp_face` is True, an edge splits normals when
the EDGE attribute `sharp_edge` is True, and custom normals live in a CORNER attribute `custom_normal` (`INT16_2D`).
`[exp: experiments/meshes/smooth_normals.py]`

```python
me.shade_smooth()                                  # removes sharp_face (all faces smooth)
me.set_sharp_from_angle(angle=math.radians(30))    # sharp_edge on edges over 30 degrees; the default angle is pi
cn = np.empty(len(me.loops) * 3, np.float32)
me.corner_normals.foreach_get("vector", cn)        # one normal per corner, after sharp edges and custom normals
print(me.normals_domain)                           # 'FACE' flat, 'POINT' smooth, 'CORNER' with sharp edges / custom
```

- `me.shade_flat()` writes `sharp_face` True on every face; `mesh.shade_smooth()` takes no `keep_sharp_edges`
  argument (its signature is `(self)`). `[exp: experiments/meshes/smooth_normals.py]`
- On a smooth 16-sided cylinder, `set_sharp_from_angle(30 deg)` marked the 32 rim edges of 48; `corner_normals` then
  had 96 normals in 18 directions. `[exp: experiments/meshes/smooth_normals.py]`
- `corner_normals` replaces `loop.normal` after `calc_normals_split()`; it is "influenced by vertex normals, sharp
  faces, sharp edges, and custom normals". `[doc: https://docs.blender.org/api/4.5/bpy.types.Mesh.html]`

**The Smooth by Angle modifier, headless.** Copied from `experiments/meshes/smooth_normals.py`:

```python
path = os.path.join(bpy.utils.system_resource("DATAFILES"), "assets", "geometry_nodes", "smooth_by_angle.blend")
with bpy.data.libraries.load(path, link=False) as (src, dst):
    dst.node_groups = ["Smooth by Angle"]
ng = bpy.data.node_groups["Smooth by Angle"]
m = ob.modifiers.new("Smooth by Angle", "NODES")
m.node_group = ng
inputs = [(i.identifier, i.name, i.socket_type) for i in ng.interface.items_tree if getattr(i, "in_out", None) == "INPUT"]
ang_id = next(i[0] for i in inputs if i[1] == "Angle")      # 'Input_1'; 'Ignore Sharpness' is 'Socket_1'
m[ang_id] = math.radians(30)                                # default is 30 degrees
ob.data.shade_smooth()                                      # or every flat face stays sharp
```

The modifier's inputs: `Input_0` Mesh, `Input_1` Angle, `Socket_1` Ignore Sharpness. It writes `sharp_edge` on the
evaluated mesh only; the original mesh is untouched. `[exp: experiments/meshes/smooth_normals.py]` It is "a geometry
nodes asset that is included in the bundled Essentials asset library".
`[doc: https://docs.blender.org/manual/en/4.5/modeling/modifiers/normals/smooth_by_angle.html]`

**Custom normals** need no flag any more:

```python
me4.normals_split_custom_set([(0.0, 0.0, 1.0)] * len(me4.loops))               # one per corner
me4.normals_split_custom_set_from_vertices([(1.0, 0.0, 0.0)] * len(me4.vertices))  # one per vertex
with bpy.context.temp_override(object=ob4, active_object=ob4, selected_objects=[ob4], selected_editable_objects=[ob4]):
    bpy.ops.mesh.customdata_custom_splitnormals_clear()                        # remove them
```

After either call `has_custom_normals` was True and every corner normal matched; the clear operator ran headless and
set it back to False. `[exp: experiments/meshes/smooth_normals.py]`

## Attributes

Everything per element is an attribute: `mesh.attributes.new(name, type, domain)`.
`[exp: experiments/meshes/attributes.py]` `[inv]`

```python
a = me.attributes.new("w", "FLOAT", "POINT")
a.data.foreach_set("value", np.zeros(len(me.vertices), np.float32))
col = me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
uv = me.uv_layers.new(name="UV2")                   # a FLOAT2 CORNER attribute
uvs = np.empty(len(me.loops) * 2, np.float32)
me.uv_layers["UVMap"].uv.foreach_get("vector", uvs)
```

- A fresh cube already has `position`, `sharp_face`, `UVMap` and hidden ones whose names start with a dot:
  `.select_vert`, `.edge_verts` (INT32_2D), `.select_edge`, `.select_poly`, `.corner_vert`, `.corner_edge`.
- `polygon.material_index`, `edge.use_edge_sharp` and `vertex.co` are views onto `material_index`, `sharp_edge` and
  `position`. Edge creases and bevel weights are the attributes `crease_edge`, `crease_vert`, `bevel_weight_edge`,
  `bevel_weight_vert` (`me.edge_creases` returns `crease_edge`; `use_customdata_edge_crease` is gone).
- A FLOAT2 CORNER attribute made with `attributes.new` shows up in `uv_layers` too. UV selection and pin state are
  hidden attributes `.vs.<map>`, `.es.<map>`, `.pn.<map>`, created the first time they are written.
- `attributes.new("position", ...)` on a mesh that has one does not fail: it makes `position.001`. Removing
  `position` raises "Attribute is required and can't be removed".
- `color_attributes.new(name, 'FLOAT', 'POINT')` does not refuse a non-colour type either: it made a plain FLOAT
  attribute that is not listed in `color_attributes`.
- The first colour attribute created became the active and the render (default) colour.
- `mesh.vertex_colors` (the pre-3.2 API) still exists in 4.5; it lists only BYTE_COLOR CORNER attributes.
- A FLOAT_COLOR attribute's `color` is linear; `color_srgb` converts on read (0.5 linear read as 0.735).

All of the above: `[exp: experiments/meshes/attributes.py]`. Attributes written by geometry nodes reach shaders by
name; see `geometry-nodes.md`.

## bmesh

```python
bm = bmesh.new()
bm.from_mesh(me)                       # or bm.from_object(ob, depsgraph) for the evaluated mesh
bm.verts.ensure_lookup_table()         # before bm.verts[i]
bmesh.ops.translate(bm, verts=bm.verts[:], vec=(0, 0, 1))
bm.to_mesh(me)
bm.free()
me.update()
```

- A round trip of a 1M-vertex grid cost 0.22 s `from_mesh` and 0.04 s `to_mesh`.
- `bm.verts.new(...)` gives index -1 until `bm.verts.index_update()`.
- Selection: `face.select_set(True)` and `face.select = True` both selected the face's vertices here; what `to_mesh`
  writes lands in `polygon.select` and the `.select_*` attributes.
- Edit mode works headless: `bpy.ops.object.mode_set(mode='EDIT')`, `bm = bmesh.from_edit_mesh(me)`, change it,
  `bmesh.update_edit_mesh(me)`, `mode_set(mode='OBJECT')`. `from_edit_mesh` on a mesh not in edit mode raises
  `ValueError: The mesh must be in editmode`.
- A freed BMesh raises `ReferenceError` when touched; it did not crash.
- Custom layers: `lay = bm.verts.layers.float.new("weight_x")`, `v[lay] = value`; after `to_mesh` it is a FLOAT POINT
  attribute. Layer kinds on verts: bool, color, deform, float, float_color, float_vector, int, shape, skin, string.

All: `[exp: experiments/meshes/bmesh_basics.py]`

**Operators, with their real argument names** (signatures from Blender `[inv]`; results on a size-2 cube unless said
`[exp: experiments/meshes/bmesh_ops.py]`):

| call | result (v, e, f) | note |
|---|---|---|
| `create_cube(bm, size=2.0)` | (8, 12, 6) | size is the edge length: spans -1..1 |
| `create_grid(bm, x_segments=4, y_segments=4, size=1.0)` | (25, 40, 16) | size is HALF the width: also spans -1..1 |
| `create_uvsphere(bm, u_segments=16, v_segments=8, radius=1.0)` | (114, 240, 128) | |
| `create_icosphere(bm, subdivisions=2, radius=1.0)` | (42, 120, 80) | |
| `create_circle(bm, cap_ends=True, segments=12, radius=1.0)` | (12, 12, 1) | the cap is one n-gon |
| `create_cone(bm, cap_ends=True, segments=12, radius1=1.0, radius2=0.0, depth=2.0)` | (13, 24, 13) | all `create_*` take `matrix=` |
| `extrude_face_region(bm, geom=[top])` then `translate(verts=new_verts, vec=(0,0,1))` | (12, 20, 11) | not manifold: old face kept |
| ... then `delete(bm, geom=[top], context='FACES')` | (12, 20, 10) | manifold |
| `extrude_discrete_faces(bm, faces=...)` | (32, 60, 30) | returns `faces` |
| `inset_region(bm, faces=[top], thickness=0.2, depth=0.0)` | (12, 20, 10) | |
| `inset_individual(bm, faces=all, thickness=0.2, depth=-0.1)` | (32, 60, 30) | |
| `bevel(bm, geom=edges, offset=0.1, segments=3, profile=0.5, affect='EDGES', clamp_overlap=True)` | (96, 192, 98) | adding verts to geom changed nothing |
| the same without `affect` | (96, 156, 62) | a vertex bevel |
| `bisect_plane(bm, geom=all, plane_co=(0,0,0.3), plane_no=(0,0,1), clear_outer=True)` | (8, 12, 5) | open; `geom_cut` has the 8 new elements |
| `holes_fill(bm, edges=boundary_edges, sides=0)` | (8, 12, 6) | closes it again |
| `triangulate(bm, faces=all, quad_method='BEAUTY', ngon_method='BEAUTY')` | (8, 18, 12) | |
| `remove_doubles(bm, verts=all, dist=1e-4)` on two overlapping cubes | (16,24,12) -> (8,12,6) | |
| `find_doubles(...)` -> `weld_verts(bm, targetmap=r['targetmap'])` | 8 pairs, (8, 12, 6) | the two-step version |
| `convex_hull(bm, input=200 random verts)` | 45 hull verts, 86 faces | delete `geom_interior` verts yourself |
| `delete(bm, geom=[face], context='FACES_ONLY')` | (8, 12, 5) | contexts: VERTS, EDGES, FACES_ONLY, EDGES_FACES, FACES, FACES_KEEP_BOUNDARY, TAGGED_ONLY |
| `subdivide_edges(bm, edges=all, cuts=2, use_grid_fill=True)` | (56, 108, 54) | |
| `dissolve_limit(bm, angle_limit=radians(5), verts=all, edges=all)` on that | (8, 12, 6) | back to the cube |
| `reverse_faces(...)`, then `recalc_face_normals(bm, faces=all)` | 6 inward, then 6 outward | |
| `solidify(bm, geom=faces, thickness=0.1)` on a 2x2 grid | (18, 32, 16) | manifold |
| `spin(bm, geom=verts+edges, cent=(0,0,0), axis=(0,0,1), angle=2*pi, steps=12, use_merge=True)` on one edge | (24, 36, 12) | a tube |
| `bridge_loops(bm, edges=two 8-vertex circles)` | (16, 24, 8) | |
| `poke(bm, faces=all)` | (14, 36, 24) | |
| `wireframe(bm, faces=all, thickness=0.05, use_replace=True)` | (40, 96, 48) | |

A wrong enum value is listed in the error, e.g. `delete(..., context='FACE')` raised
`ValueError: context: 'FACE' not found in (['VERTS', 'EDGES', ...])`. `[exp: experiments/meshes/bmesh_ops.py]`
Look up any other op with `python3 scripts/kb.py py bmesh.ops.NAME`.

## Units and scale

- A fresh scene is metric with `scale_length` 1.0: one unit is one metre. `primitive_cube_add()` makes a 2 m cube.
  Setting `scale_length` to 0.01 did not change the size of new primitives. `[exp: experiments/meshes/units_scale.py]`
- Apply scale with the data API: `me.transform(Matrix.Diagonal((*ob.scale, 1.0)))`, then `ob.scale = (1, 1, 1)`. The
  operator `bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)` works headless on the selected
  objects, but refuses a mesh with two users: "Cannot apply to a multi user". `[exp: experiments/meshes/units_scale.py]`
- Modifier sizes are in object space: Solidify of thickness 0.1 on an object scaled 3x was 0.3 thick in the world.
  Apply scale before setting thicknesses and bevel widths. `[exp: experiments/meshes/units_scale.py]`
- A mirrored transform (negative determinant) flips normals; a cloth collider built that way pulled cloth in.
  Check `ob.matrix_world.determinant() > 0`. `[lesson: kb/lessons/cloth.md]`

## Reference: renamed and removed (2.8 to 4.5)

| old | in 4.5 | evidence |
|---|---|---|
| `mesh.use_auto_smooth`, `auto_smooth_angle` | `mesh.set_sharp_from_angle(angle=)`, `ops.object.shade_smooth_by_angle`, Smooth by Angle modifier | `[exp: experiments/meshes/smooth_normals.py]` |
| `mesh.calc_normals_split()`, `loop.normal` after it | `mesh.corner_normals` (always available) | `[exp: experiments/meshes/smooth_normals.py]` `[doc: https://docs.blender.org/api/4.5/bpy.types.Mesh.html]` |
| `create_normals_split()`, `free_normals_split()` | not needed | `[exp: experiments/meshes/smooth_normals.py]` |
| custom normals as hidden custom data | attribute `custom_normal`, CORNER, INT16_2D | `[exp: experiments/meshes/smooth_normals.py]` |
| `polygon.use_smooth` as stored data | attribute `sharp_face`; `use_smooth = False` on one face wrote `sharp_face` True on it | `[exp: experiments/meshes/smooth_normals.py]` |
| `use_customdata_edge_crease`, edge `crease` custom data | attributes `crease_edge`, `crease_vert` | `[exp: experiments/meshes/attributes.py]` |
| `bevel_weight` custom data | attributes `bevel_weight_edge`, `bevel_weight_vert` | `[exp: experiments/meshes/solidify_bevel.py]` |
| `mesh.vertex_colors` | `mesh.color_attributes` (`vertex_colors` still present for BYTE_COLOR CORNER) | `[exp: experiments/meshes/attributes.py]` |
| `polygon.loop_total` writable | read-only; set `loop_start` only | `[exp: experiments/meshes/build_from_arrays.py]` |
| `object.shade_auto_smooth` adding a checkbox | adds the Smooth by Angle modifier (UI only; CANCELLED headless) | `[exp: experiments/meshes/smooth_normals.py]` |

## Reference: attribute types and the property to use with foreach

| type | item property | numpy dtype that round-tripped, values per element |
|---|---|---|
| FLOAT | `value` | float32, 1 |
| INT | `value` | int32, 1 |
| INT8 | `value` | int8, 1 |
| BOOLEAN | `value` | bool, 1 |
| FLOAT2 (UVs) | `vector` | float32, 2 |
| FLOAT_VECTOR | `vector` | float32, 3 |
| FLOAT_COLOR, BYTE_COLOR | `color` (linear), `color_srgb` | float32, 4 (BYTE_COLOR too) |
| INT16_2D | `value` | int16 or int32, 2 |
| INT32_2D | `value` | int32, 2 |
| QUATERNION | `value` | float32, 4 |
| FLOAT4X4 | `value` | float32, 16 |
| STRING | `value` | per element (no foreach tried) |

Every row except STRING was written with `foreach_set` and read back identical with `foreach_get`.
`[exp: experiments/meshes/attributes.py]` Domains: POINT, EDGE, FACE, CORNER (and CURVE, INSTANCE, LAYER for other
geometry) `[inv]`. Domain sizes of a cube: 8, 12, 6, 24 (`me.attributes.domain_size("CORNER")`).
