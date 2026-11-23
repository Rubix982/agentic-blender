# Modifiers from Python

Blender 4.5.14 LTS on Apple Silicon. Tags: `[inv]` read from Blender (`scripts/kb.py`), `[exp: path]` measured here
(paths relative to the source repository), `[lesson]` from a real project, `[doc: link]` Blender's documentation.

## What goes wrong most often

1. **Reading `obj.data` and expecting the modifiers in it.** `obj.data` is the base mesh (482 vertices for a UV
   sphere); the result of the stack is `obj.evaluated_get(depsgraph).data` (7,938 with a level-2 subsurf).
   `[exp: experiments/modifiers/evaluate_and_apply.py]`
2. **`bpy.data.meshes.new_from_object(obj)` with the original object.** It returned the base mesh (482 vertices), not
   the evaluated one. Pass `obj.evaluated_get(depsgraph)`. `[exp: experiments/modifiers/evaluate_and_apply.py]`
   "undeformed geometry if object is original, and final evaluated geometry ... if object is evaluated".
   `[doc: https://docs.blender.org/api/4.5/bpy.types.BlendDataMeshes.html]`
3. **`modifier_apply` on the wrong object.** Without an override it acts on the *active* object: with another object
   active, the intended one kept 482 vertices and the active one was applied instead. Use
   `with bpy.context.temp_override(object=ob, active_object=ob):`. The 3.x form, a context dict as the first
   positional argument, raises `ValueError: 1-2 args execution context is supported`.
   `[exp: experiments/modifiers/evaluate_and_apply.py]`
4. **Applying where it cannot work.** `modifier_apply` raised "Modifiers cannot be applied to multi-user data" on a
   shared mesh and "Modifier cannot be applied to a mesh with shape keys" on a mesh with shape keys; on a geometry-nodes
   modifier whose output is instances it raised "Evaluated geometry from modifier does not contain a mesh".
   `[exp: experiments/modifiers/evaluate_and_apply.py]` `[exp: experiments/geonodes/instances_realize.py]`
5. **Keeping an evaluated mesh across a change.** An evaluated mesh read before changing a modifier raised
   `ReferenceError: StructRNA of type Mesh has been removed` after the next evaluation. Copy the numbers out first.
   `[exp: experiments/modifiers/solidify_bevel.py]`
6. **The Fast Boolean solver on touching faces.** With cutters whose caps lay exactly in the slab's faces, the Fast
   solver gave genus 0 instead of 100 holes and 3,184 non-manifold edges; Exact and Manifold were right.
   `[exp: experiments/modifiers/boolean_coplanar.py]` The solver identifiers are `FAST`, `EXACT`, `MANIFOLD` on the
   modifier (default `EXACT`) but `FLOAT`, `EXACT`, `MANIFOLD` on the Mesh Boolean node (default `FLOAT`).
   `[exp: experiments/geonodes/mesh_boolean_node.py]` `[inv]`
7. **The Manifold solver on open meshes fails silently.** Cut by open tubes, it returned the slab uncut (8 vertices);
   the only sign was a console warning "Cannot execute, non-manifold inputs". Check the vertex count after.
   `[exp: experiments/modifiers/boolean_solvers.py]` "the Manifold Solver will not work at all on non-manifold meshes".
   `[doc: https://docs.blender.org/manual/en/4.5/modeling/modifiers/generate/booleans.html]`
8. **Modifier type names from the UI.** The Subdivision Surface type is `SUBSURF`; `'SUBDIVISION'` raises a TypeError
   that lists every valid type. A second modifier with a taken name becomes `Bevel.001`: keep the returned object.
   `[exp: experiments/modifiers/order.py]`
9. **Bevel modifier only touching some edges.** Its default limit method is `ANGLE` at 30 degrees: on a 32-sided
   cylinder only the two rims were bevelled (128 vertices); `limit_method = 'NONE'` bevelled the sides too (192).
   `[exp: experiments/modifiers/solidify_bevel.py]`
10. **Widths and thicknesses on a scaled object.** Modifier values are in object space: a Solidify of 0.1 on an object
    scaled 3x was 0.3 thick. Apply scale first (`meshes.md`). `[exp: experiments/meshes/units_scale.py]`
11. **Mirror with bisect keeps the side you did not expect.** On a mesh spanning x -0.5..1.5, `use_bisect_axis[0]`
    kept the negative side and mirrored it (x -0.5..0.5); `use_bisect_flip_axis[0]` keeps the positive side
    (x -1.5..1.5). `[exp: experiments/modifiers/subsurf_array_mirror.py]`
12. **Blaming the voxel Remesh when its point order changes.** Given the same input it returned the identical array,
    same points in the same order, in 3 processes at `-t 1` and 3 at the default 12 threads, at voxel 0.05, 0.02 and
    0.01. But moving each input point by about 1e-6 m changed the count (60,010 to 60,008) and left only 21,838 points
    at their old index. A remesh that comes back reordered had a different input, however slightly; check what feeds it,
    and re-sort by position if order matters. `[exp: experiments/modifiers/remesh_order.py]`

## Add, order and remove

```python
b = ob.modifiers.new("Bevel", "BEVEL"); b.width = 0.2; b.segments = 2    # appended at the end of the stack
s = ob.modifiers.new("Subdivision", "SUBSURF"); s.levels = 1
ob.modifiers.move(1, 0)                                                  # from_index, to_index; no operator needed
with bpy.context.temp_override(object=ob, active_object=ob):
    bpy.ops.object.modifier_move_to_index(modifier="Bevel", index=0)      # the operator also works headless
ob.modifiers.remove(m2); ob.modifiers.clear()
```

The stack runs top to bottom: bevel-then-subsurf and subsurf-then-bevel on a cube both gave 218 vertices, but different
shapes (sum of |co| 477.2 against 252.6). After `modifiers.move` the next evaluation already used the new order.
`use_pin_to_last` keeps a modifier at the end. `[exp: experiments/modifiers/order.py]`

Headless, `evaluated_depsgraph_get()` evaluates with viewport settings: a subsurf with `levels=1`,
`render_levels=3` gave the level-1 count, and `show_viewport = False` removed the modifier from the result.
`[exp: experiments/modifiers/order.py]` A render uses `render_levels` and `show_render`; untested here.

## Read the result without applying

Copied from `experiments/modifiers/evaluate_and_apply.py`:

```python
dg = bpy.context.evaluated_depsgraph_get()
ev = ob.evaluated_get(dg)
n = len(ev.data.vertices)                    # read numbers now; the evaluated mesh is freed on the next evaluation
tm = ev.to_mesh()                            # a temporary mesh, not in bpy.data
...
ev.to_mesh_clear()
nm = bpy.data.meshes.new_from_object(ev)     # a real datablock (0 users until assigned)
nm = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)   # keep UVs, groups, etc.
```

`to_mesh()` "must be treated as temporary"; for anything kept, use `new_from_object()`.
`[doc: https://docs.blender.org/api/4.5/bpy.types.Depsgraph.html]` `preserve_all_data_layers` keeps layers Blender
otherwise skips (UV maps, vertex groups) and needs the depsgraph.
`[doc: https://docs.blender.org/api/4.5/bpy.types.BlendDataMeshes.html]`

## Apply a modifier headless

Two ways, both measured on a level-3 subsurf (31,746 vertices): 26-29 ms and 28-31 ms over two runs, the same mesh.
`[exp: experiments/modifiers/evaluate_and_apply.py]`

```python
# 1. data API: no context needed; applies the whole stack
dg = bpy.context.evaluated_depsgraph_get()
m = bpy.data.meshes.new_from_object(a.evaluated_get(dg))
a.modifiers.clear()
a.data = m                                   # the old mesh is left with 0 users (an orphan)

# 2. operator: one modifier, on the object you name
with bpy.context.temp_override(object=b, active_object=b):
    bpy.ops.object.modifier_apply(modifier="Sub")
```

The data route applies the whole stack; the operator applies one modifier. The data route also worked on the two
meshes the operator refused: on a mesh shared with another object (that object kept the old 482-vertex mesh) and on a
mesh with shape keys, whose new mesh has no shape keys. `[exp: experiments/modifiers/evaluate_and_apply.py]`

## Boolean

```python
m = s.modifiers.new("Bool", "BOOLEAN")
m.operation = "DIFFERENCE"; m.solver = "MANIFOLD"      # FAST, EXACT (default), MANIFOLD
m.object = cutter                                       # or: m.operand_type = "COLLECTION"; m.collection = col
```

A slab cut by an n x n grid of 16-sided round holes, timed from the evaluation, checked by genus (holes), non-manifold
edges and volume against the exact value `[exp: experiments/modifiers/boolean_solvers.py]`:

| holes | operand | FAST | EXACT | MANIFOLD |
|---|---|---:|---:|---:|
| 10 x 10 | one joined cutter object | 0.06 s | 0.38 s | 0.02 s |
| 10 x 10 | collection of 100 objects | 0.27 s | 0.57 s | 0.02 s |
| 30 x 30 | one joined cutter object | 3.1 s | 4.1 s | 0.31 s |
| 30 x 30 | collection of 900 objects | 17.7 s | 5.5 s | 0.35 s |

All twelve results were correct: genus 100 or 900, 0 non-manifold edges, volume within 0.001 of exact. Manifold was
13 to 28x faster than Exact (0.377 against 0.024 s and 0.567 against 0.020 s at 10 x 10; 4.09 against 0.31 s and 5.5
against 0.35 s at 30 x 30). Fast with a collection of 900 cutters was the slowest of all and left 35,876 vertices
against 28,808 for the others. `[exp: experiments/modifiers/boolean_solvers.py]`

The cases that broke:

| case | FAST | EXACT | MANIFOLD |
|---|---|---|---|
| cutter caps coplanar with the slab's faces (10 x 10) | wrong: genus 0, 3,184 non-manifold edges | right, 0.48 s | right, 0.02 s |
| open tubes as cutters (non-manifold) | right | right | slab returned uncut, warning only |

`[exp: experiments/modifiers/boolean_coplanar.py]` `[exp: experiments/modifiers/boolean_solvers.py]`

So: Manifold when every operand is closed (check `all(e.is_manifold for e in bm.edges)` first); Exact when one is not;
Fast only when speed matters more than correctness and nothing touches. The manual adds that with Fast the
Intersect operation is not allowed on a collection operand, and that Exact has Self Intersection and Hole Tolerant
options. `[doc: https://docs.blender.org/manual/en/4.5/modeling/modifiers/generate/booleans.html]`

## Solidify

A new Solidify has thickness 0.01, offset -1, rim on, even thickness off, mode `EXTRUDE` ("Simple").
`[exp: experiments/modifiers/solidify_bevel.py]` `[inv]`

| setting | measured on a plane (normal +Z), thickness 0.1 |
|---|---|
| `offset = -1` | shell from z -0.1 to 0 (grows behind the normal) |
| `offset = 0` | -0.05 to 0.05 |
| `offset = 1` | 0 to 0.1 |
| `use_rim = True` | closed and manifold (8 vertices, 6 faces) |
| `use_rim = False` | two loose shells (2 faces), not manifold |

On an open box with thickness 0.2, the inner corner vertex moved 0.2 along the corner's averaged normal, which left it
only 0.1155 (0.2 / sqrt 3) in from each wall; with `use_even_offset = True` it sat the full 0.2 in.
`[exp: experiments/modifiers/solidify_bevel.py]`

## Bevel

A new Bevel: width 0.1, segments 1, affect `EDGES`, limit method `ANGLE` at 30 degrees, clamp overlap on, profile 0.5,
offset type `OFFSET`. `[exp: experiments/modifiers/solidify_bevel.py]`

| on a size-2 cube | result |
|---|---|
| segments 1, 2, 3, 4, 8 | (24, 26), (56, 54), (96, 98), (152, 150), (488, 486) vertices, faces |
| profile 0.0 / 0.25 / 0.5 / 0.75 / 1.0 (4 segments) | nearest vertex to the old corner 0.141 / 0.116 / 0.073 / 0.035 / 0.0: 0.5 is round, 1.0 square, 0 concave |
| width 1.5 (over half an edge), clamp on | 0 inverted faces |
| width 1.5, clamp off | 12 inverted faces |
| `limit_method='WEIGHT'`, one edge with `bevel_weight_edge` = 1 (cylinder) | only that edge bevelled (64 -> 66 vertices) |

`[exp: experiments/modifiers/solidify_bevel.py]`

## Subdivision Surface, Array, Mirror

```python
s = ob.modifiers.new("Subdivision", "SUBSURF")      # levels 1, render_levels 2, CATMULL_CLARK, quality 3
a = ob.modifiers.new("Array", "ARRAY")              # count 2, FIXED_COUNT, relative offset (1, 0, 0), merge off
mi = ob.modifiers.new("Mirror", "MIRROR")           # X axis across the object's origin, merge on (0.001), clip off
```

- Catmull-Clark on a cube: 6, 24, 96, 384, 1536 faces for levels 0-4; with `use_limit_surface` (on by default) the
  vertices sit on the limit surface, so the cube's half-width was 0.8395 at every level 1-4. `SIMPLE` keeps the cube
  (1.0), and `crease_edge` = 1.0 on every edge did too. `[exp: experiments/modifiers/subsurf_array_mirror.py]`
- Array count 5 with relative offset 1: touching copies, 40 vertices; `use_merge_vertices` merged them to 24.
  `fit_type='FIT_LENGTH'` with `fit_length=20` and a constant offset of 3 made 7 copies (x -1 to 19).
  `[exp: experiments/modifiers/subsurf_array_mirror.py]`
- Mirror of a cube touching the plane merged the seam (16 -> 12 vertices); with merge off the duplicates stayed. A mesh
  crossing the plane overlaps its mirror unless `use_bisect_axis` is on (and see the side trap above).
  `[exp: experiments/modifiers/subsurf_array_mirror.py]`

## Remesh, Weld, Decimate

- **Remesh** defaults to mode `VOXEL`, voxel size 0.1. On a torus (major 1, minor 0.3, exact volume 1.777): voxel
  0.1 gave 1,568 quads (volume 1.607), 0.05 gave 6,548 (1.678), 0.025 gave 26,804 (still under 0.06 s); all quads,
  all manifold. Halving the voxel size quadrupled the faces. `adaptivity = 0.5` at 0.05 gave 571 faces, 210 of them
  triangles. `[exp: experiments/modifiers/remesh_weld_decimate.py]` A voxel-remeshed closed copy of a body made a much
  better cloth collider than the body itself: no lumps, and 4x faster. `[lesson: kb/lessons/cloth.md]`
- **Remesh output order.** A monkey head and a sphere in one mesh, remeshed in six separate Blender processes (`-t 1`
  and the default 12 threads, three each) and twice inside each: at voxel 0.05 (9,358 points), 0.02 (60,010) and 0.01
  (242,820) every run gave the identical array, and so did `bpy.ops.object.voxel_remesh()` (9,944, 61,368, 245,146
  points: a slightly different result from the modifier's). The same input with its points shuffled also gave the
  identical array; 1e-6 m of noise on the input gave 60,008 points with the first difference at index 797. At voxel 0.01
  the modifier took 0.292 s at `-t 1` and 0.065 s on 12 threads. `[exp: experiments/modifiers/remesh_order.py]`
- **Remesh order on a project.** A remeshed body had 15,184 of 41,244 points at other indices between runs, even at
  `-t 1` `[lesson]`. With identical input that did not happen in the experiment above, so the probable cause there is
  an input that differed slightly between runs (not checked).
- **Weld** defaults to 0.001 m, mode `ALL`: it rejoined a sphere whose faces had all been split apart (480 -> 114
  vertices, manifold). Mode `CONNECTED` merges only along existing edges and left it split.
  `[exp: experiments/modifiers/remesh_weld_decimate.py]`
- **Decimate** defaults to `COLLAPSE`, ratio 1.0. On a 64 x 32 UV sphere (2,048 faces) ratio 0.5 gave 1,409 faces
  (834 triangles) and 0.1 gave 381; `decimate.face_count` reports the result. `DISSOLVE` at 5 degrees took a
  simple-subdivided cube back to 6 faces; `UNSUBDIV` with 2 iterations took it from 96 to 24.
  `[exp: experiments/modifiers/remesh_weld_decimate.py]`

## Displace and Shrinkwrap

```python
d = g.modifiers.new("Displace", "DISPLACE")         # strength 1, mid_level 0.5, direction NORMAL, no texture
tex = bpy.data.textures.new("clouds", "CLOUDS")     # texture types: BLEND, CLOUDS, ..., IMAGE, VORONOI, WOOD
tex.noise_scale = 0.5
d.texture = tex
d.mid_level = 0.0; d.strength = 0.2
```

- Displacement is `(texture value - mid_level) * strength` along the normal: with no texture every vertex moved 0.5;
  with clouds at mid 0.5 it ranged -0.36 to 0.34; at mid 0 and strength 0.2, 0.03 to 0.17. An IMAGE texture (a ramp
  made with `bpy.data.images.new` and `pixels.foreach_set`) with `texture_coords='UV'` displaced 0 to 1 across the
  grid. `[exp: experiments/modifiers/displace_shrinkwrap.py]`
- A new Shrinkwrap is `NEAREST_SURFACEPOINT`, `ON_SURFACE`, offset 0. A subdivided cube (size 3) on a unit sphere:
  NEAREST_SURFACEPOINT, NEAREST_VERTEX and TARGET_PROJECT put every vertex on the target; `PROJECT` with no axis
  casts along each vertex normal and left the vertices whose ray missed where they were (up to 1.4 off).
  `offset = 0.1` kept every vertex 0.1 off the surface. `[exp: experiments/modifiers/displace_shrinkwrap.py]`

## Reference: modifier type identifiers (4.5)

Mesh modifiers you can pass to `modifiers.new(name, type)` `[inv]`:

| group | types |
|---|---|
| generate | `ARRAY`, `BEVEL`, `BOOLEAN`, `BUILD`, `DECIMATE`, `EDGE_SPLIT`, `NODES`, `MASK`, `MIRROR`, `MESH_TO_VOLUME`, `MULTIRES`, `REMESH`, `SCREW`, `SKIN`, `SOLIDIFY`, `SUBSURF`, `TRIANGULATE`, `VOLUME_TO_MESH`, `WELD`, `WIREFRAME` |
| deform | `ARMATURE`, `CAST`, `CURVE`, `DISPLACE`, `HOOK`, `LAPLACIANDEFORM`, `LATTICE`, `MESH_DEFORM`, `SHRINKWRAP`, `SIMPLE_DEFORM`, `SMOOTH`, `CORRECTIVE_SMOOTH`, `LAPLACIANSMOOTH`, `SURFACE_DEFORM`, `WARP`, `WAVE`, `VOLUME_DISPLACE` |
| edit / normals | `DATA_TRANSFER`, `MESH_CACHE`, `MESH_SEQUENCE_CACHE`, `NORMAL_EDIT`, `WEIGHTED_NORMAL`, `UV_PROJECT`, `UV_WARP`, `VERTEX_WEIGHT_EDIT`, `VERTEX_WEIGHT_MIX`, `VERTEX_WEIGHT_PROXIMITY` |
| physics | `CLOTH`, `COLLISION`, `DYNAMIC_PAINT`, `EXPLODE`, `FLUID`, `OCEAN`, `PARTICLE_INSTANCE`, `PARTICLE_SYSTEM`, `SOFT_BODY`, `SURFACE` |

There is no `SMOOTH_BY_ANGLE` type: Smooth by Angle is a `NODES` modifier with a bundled node group (`meshes.md`).
`EDGE_SPLIT` still exists. Grease Pencil has its own `GREASE_PENCIL_*` types. `[inv]`

## Reference: defaults of a new modifier

What `modifiers.new` gave `[exp]` (paths above). Note that `kb.py struct` shows the RNA default, which is not always
what a new modifier gets: it lists the Bevel's `edge_weight` default as "" while a new Bevel had `bevel_weight_edge`.

| modifier | defaults |
|---|---|
| BEVEL | width 0.1, segments 1, affect EDGES, limit ANGLE 30 deg, clamp on, profile 0.5, edge_weight `bevel_weight_edge`, vertex_weight `bevel_weight_vert` |
| BOOLEAN | operation DIFFERENCE, solver EXACT, operand OBJECT (`[inv]`) |
| SOLIDIFY | thickness 0.01, offset -1, rim on, even off, EXTRUDE |
| SUBSURF | levels 1, render_levels 2, CATMULL_CLARK, quality 3, use_limit_surface on |
| ARRAY | count 2, FIXED_COUNT, relative (1, 0, 0), merge off (threshold 0.01) |
| MIRROR | axis X, bisect off, merge on (0.001), clip off |
| REMESH | VOXEL, voxel_size 0.1, adaptivity 0 |
| WELD | merge_threshold 0.001, mode ALL |
| DECIMATE | COLLAPSE, ratio 1.0 |
| DISPLACE | strength 1, mid_level 0.5, NORMAL, texture_coords LOCAL, no texture |
| SHRINKWRAP | NEAREST_SURFACEPOINT, ON_SURFACE, offset 0 |
| NODES | no node group (assign one) |
