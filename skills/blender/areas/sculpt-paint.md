# Sculpt and paint from a script

Blender 4.5.14 LTS. Tags: `[inv]` read from Blender (`scripts/kb.py`), `[exp: path]` measured here (paths relative to
the source repository; results next to each script in `results/`), `[lesson]` from a real project, `[doc: link]`
Blender's documentation. Sculpt and paint modes are built for a hand on a tablet. From a script most of their work is
better done as data: positions, colour attributes, vertex-group weights and image pixels, all written directly. This
page says which sculpt operators still run headless (`-b`), what they need, and how to paint by data instead.
Attribute basics: `meshes.md`; reading attributes in a material: `materials.md`; image colour spaces: `uv-images.md`.

## What goes wrong most often

1. **A sculpt filter crashing the job.** `bpy.ops.sculpt.mesh_filter` in a background Blender with no undo step pushed
   ended the process with a segmentation fault (exit -11, a crash log written, no Python error to catch). One
   `bpy.ops.ed.undo_push()`, either before or after `mode_set(mode="SCULPT")`, was enough: the filter returned
   FINISHED and moved all 1986 points of the test sphere. `[exp: experiments/sculpt/sculpt_ops_probe.py]` `[lesson]`
2. **Expecting the cloth filter to run.** `bpy.ops.sculpt.cloth_filter` returned `PASS_THROUGH` and moved nothing,
   with undo steps pushed, called plainly, as `"EXEC_DEFAULT"`, and inside the 3D View override. Sculpt mode's local
   cloth (gravity, inflate, pinch) cannot be scripted headless. Use the cloth solver (`simulation.md`), displacement,
   or Multires. `[exp: experiments/sculpt/sculpt_ops_probe.py]` (this re-checks, and agrees with, the `[lesson]` in
   `kb/lessons/sculpt.md`)
3. **Brush strokes as data.** `sculpt.brush_stroke`, `paint.vertex_paint` and `paint.weight_paint` all failed their
   poll plainly. Inside the 3D View override (`data-model.md`) they went three different ways: the sculpt stroke,
   given object-space `location`s, FINISHED and moved 233 points near them; the vertex-paint stroke FINISHED but
   changed no colour; the weight-paint stroke crashed Blender (exit -11; the crash log's stack runs through
   `view3d_operator_needs_gpu` to `GPU_viewport`). Write colours and weights as data instead (below).
   `[exp: experiments/sculpt/sculpt_ops_probe.py]`
4. **Vertex-group weights in EEVEE.** The shader's Attribute node with a vertex group's name rendered the weights in
   Cycles (a 0 to 1 ramp read 0.073, 0.258, 0.506, 0.757, 0.945 against 0.07, 0.258, 0.508, 0.758, 0.945 expected) and
   0 everywhere in EEVEE. Copied into a FLOAT POINT attribute, the same weights rendered in EEVEE too.
   `[exp: experiments/sculpt/vertex_groups_weights.py]`
5. **An empty Color Attribute node reads the render colour, not the active one.** With two colour attributes and
   `layer_name = ""`, the render showed the first one made (the default for rendering); making the second one active
   changed nothing; setting `color_attributes.render_color_index` to it did. Name the attribute in `layer_name`. A
   misspelled name rendered black with no error. `[exp: experiments/sculpt/color_attributes.py]`
6. **Values above 1 in a BYTE_COLOR attribute.** Written as (2.0, 0.5, 0.05), a BYTE_COLOR attribute read back and
   rendered (1.0, 0.5029, 0.0497); FLOAT_COLOR kept 2.0. `[exp: experiments/sculpt/color_attributes.py]`
7. **Weights outside 0 to 1.** `vertex_group.add([i], 1.7, "REPLACE")` stored 1.0 and -0.3 stored 0.0, with no error;
   the point stays a member of the group at weight 0. `[exp: experiments/sculpt/vertex_groups_weights.py]`
8. **8-bit sRGB images as data.** 0.5 written to the pixels of a default 8-bit image rendered as 0.216 (the value is
   taken as sRGB). A float image rendered 0.5, and an 8-bit image set to `Non-Color` first rendered 0.502.
   `[exp: experiments/sculpt/texture_pixels.py]`
9. **`sample_detail_size` headless.** It returned CANCELLED plainly and inside the 3D View override, before and after
   `view3d.view_all`; set `tool_settings.sculpt.constant_detail_resolution` directly.
   `[exp: experiments/sculpt/sculpt_ops_probe.py]`

## Sculpt operators that run headless

Each line below ran in its own background Blender on a 64 x 32 UV sphere (1986 points, 2048 faces), with the object
active and undo steps pushed around `mode_set(mode="SCULPT")`. `[exp: experiments/sculpt/sculpt_ops_probe.py]`

```python
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.ed.undo_push()                          # without one, the mesh filter crashes -b
bpy.ops.object.mode_set(mode="SCULPT")
bpy.ops.ed.undo_push()
bpy.ops.sculpt.mesh_filter(type="INFLATE", strength=0.5)
bpy.ops.object.mode_set(mode="OBJECT")          # then read positions with foreach_get("co")
```

| Operation | Result headless | Measured |
|---|---|---|
| `sculpt.mesh_filter`, no undo push | crash (exit -11) | |
| `sculpt.mesh_filter`, one undo push | FINISHED | INFLATE 0.5 moved all 1986 points |
| mesh filter types SMOOTH, SCALE, INFLATE, SPHERE, RANDOM, RELAX, SURFACE_SMOOTH, SHARPEN, ENHANCE_DETAILS, RELAX_FACE_SETS | FINISHED | each moved all 1986 points |
| mesh filter ERASE_DISPLACEMENT (no Multires) | CANCELLED | 0 moved |
| `sculpt.cloth_filter` | PASS_THROUGH | 0 moved |
| `paint.mask_flood_fill(mode="VALUE", value=0.75)` | FINISHED | wrote `.sculpt_mask` (FLOAT, POINT) = 0.75 |
| `sculpt.dynamic_topology_toggle`, then `detail_flood_fill` (constant detail 4) | FINISHED | 2048 faces became about 1,320 triangles |
| `sculpt.sample_detail_size` | CANCELLED | detail unchanged |
| `object.voxel_remesh` (from sculpt or object mode) | FINISHED | voxel 0.05: 7830 faces; 0.1: 1998 faces |
| `object.quadriflow_remesh(target_faces=500)` | FINISHED | 537 quads in 0.11 s |
| `object.multires_subdivide` x2, then `object.modifier_apply` | FINISHED | 128 faces -> 1920; applied: 1920 in the mesh |
| `sculpt.mesh_filter` on a Multires level | FINISHED | moved 1922 points of the evaluated mesh |
| `sculpt.brush_stroke` (stroke as data) | poll fails; in the 3D View override FINISHED | 233 points moved near the stroke |

`[exp: experiments/sculpt/sculpt_ops_probe.py]` The filter types ran one after another on the same sphere, so their
sizes of movement are not comparable with each other. Dyntopo's face count varied by a few faces between runs (1322,
1324, 1334). `[exp: experiments/sculpt/sculpt_ops_probe.py]`

**Masking by data.** The sculpt mask is a FLOAT POINT attribute named `.sculpt_mask` (1 = fully masked). Written from
Python before entering sculpt mode, it held the filter: with the top half masked, 0 of its 961 points moved and all 1025
of the bottom half did. `[exp: experiments/sculpt/sculpt_ops_probe.py]`

```python
m = me.attributes.new(".sculpt_mask", "FLOAT", "POINT")
m.data.foreach_set("value", (z > 0).astype(np.float32))      # z: each point's height
```

**A sculpt stroke as data.** Only inside the 3D View override, and with object-space locations (the `mouse` values do
not place it): ten stroke points at (0, -1, 0), brush size 50, moved 233 points whose centre was (0, -0.832, 0).

```python
stroke = [dict(name="", location=(0, -1, 0), mouse=(100 + 5 * i, 100), mouse_event=(100 + 5 * i, 100), pressure=1.0,
               size=50, x_tilt=0, y_tilt=0, time=i * 0.01, is_start=(i == 0)) for i in range(10)]
with bpy.context.temp_override(window=win, area=area, region=region):    # the screen's VIEW_3D area
    bpy.ops.sculpt.brush_stroke(stroke=stroke, mode="NORMAL")
```

`[exp: experiments/sculpt/sculpt_ops_probe.py]` Which brush it used and how size maps to a radius were not checked.

**Remesh and Multires** are the dependable tools: `mesh.remesh_voxel_size` (default 0.1) then
`bpy.ops.object.voxel_remesh()`; `ob.modifiers.new("Multires", "MULTIRES")`, then
`bpy.ops.object.multires_subdivide(modifier="Multires", mode="CATMULL_CLARK")` once per level with the object active;
`levels`, `sculpt_levels`, `render_levels` and `total_levels` all read 2 after two. `[exp: experiments/sculpt/sculpt_ops_probe.py]`

## Colour attributes: painting by data

```python
ca = me.color_attributes.new("paint", "FLOAT_COLOR", "POINT")     # or BYTE_COLOR, and/or CORNER
ca.data.foreach_set("color", np.tile(np.array((0.5, 0.25, 0.1, 1.0), np.float32), len(ca.data)))   # linear RGBA
m = bpy.data.materials.new("m"); m.use_nodes = True
n = m.node_tree.nodes.new("ShaderNodeVertexColor")                  # the "Color Attribute" node
n.layer_name = "paint"                                              # name it; "" means the render colour
```

| | BYTE_COLOR | FLOAT_COLOR |
|---|---|---|
| a new one holds | (1, 1, 1, 1) | (1, 1, 1, 1) |
| written (0.5, 0.25, 0.1), rendered in Cycles | (0.5029, 0.2502, 0.0999) | (0.5, 0.25, 0.1) |
| same, EEVEE | (0.5024, 0.25, 0.0999) | (0.5, 0.25, 0.1) |
| written 2.0 | stored and rendered 1.0 | 2.0 |
| POINT vs CORNER | same render for a uniform colour | same |

`[exp: experiments/sculpt/color_attributes.py]` All four kinds (both types on either domain) reached both engines
through the Color Attribute node. POINT holds one colour per vertex, blended across faces; CORNER one per face corner,
so neighbouring faces can differ (the blend itself was not measured here). The Attribute node with
`attribute_name` set to a colour attribute's name read it too. `[exp: experiments/sculpt/color_attributes.py]`

- **Speed.** 100,000 colours: a loop over `.data[i].color` took 0.078 s, one `foreach_set("color", flat)` 0.0001 s.
  `[exp: experiments/sculpt/color_attributes.py]`
- **BYTE_COLOR stores sRGB.** `foreach_get("color")` returned the linear values to within 0.0045; a linear 0.5 reads
  0.7373 through `.color_srgb`. `[exp: experiments/sculpt/color_attributes.py]`
- **Which one renders.** `color_attributes.active_color` (what paint mode edits) and `render_color_index` / 
  `default_color_name` (what an empty `layer_name` reads) are separate; both start at the first attribute made.
  `[exp: experiments/sculpt/color_attributes.py]`

## Vertex groups and weights by data

```python
vg = ob.vertex_groups.new(name="ramp")
vg.add(list(range(n)), 1.0, "REPLACE")          # one weight for many points: one call
for i in range(n):
    vg.add([i], float(w[i]), "REPLACE")         # one weight each: one call per point (no foreach_set)
vg.weight(i)                                    # RuntimeError "Vertex not in group" if i is not a member
vg.remove([i])
```

| Operation, 100,489 points | Time |
|---|---|
| `vg.add(all indices, 1.0)` | 0.005 s |
| `vg.add([i], w)` per point | 0.06 s |
| `vg.weight(i)` per point | 0.03 s |
| loop over `mesh.vertices[i].groups` | 0.06 s |

`[exp: experiments/sculpt/vertex_groups_weights.py]` Both reads matched what was written (error 0.0). `ADD` and
`SUBTRACT` change an existing weight (0.5 + 0.25 = 0.75; 0.5 - 0.25 = 0.25). Vertex groups are not in
`mesh.attributes` (a 4.5 grid listed only `position` and `sharp_face` there).
`[exp: experiments/sculpt/vertex_groups_weights.py]`

- **Used by modifiers:** a Displace modifier with `vertex_group = "ramp"`, direction Z, strength 1, mid level 0 and no
  texture moved each point by exactly its weight (error 0.0). `[exp: experiments/sculpt/vertex_groups_weights.py]`
- **Normalising:** `bpy.ops.object.vertex_group_normalize_all(lock_active=False)` ran headless with the object active;
  a point at 0.6 in two groups summed to 1.0 afterwards. `[exp: experiments/sculpt/vertex_groups_weights.py]`
- **Rendering:** Cycles only, through the Attribute node; for EEVEE copy the weights into a FLOAT POINT attribute
  (item 4 above).

## A texture painted by writing pixels

```python
img = bpy.data.images.new("paint", 256, 256)            # 8-bit, sRGB, black
px = np.zeros((256, 256, 4), np.float32); px[..., 3] = 1
px[:, :128, :3] = (1, 0, 0)                              # left half red
px[:64, :, :3] = (0, 1, 0)                               # rows 0-63: the BOTTOM of the image
img.pixels.foreach_set(px.ravel())
tex = mat.node_tree.nodes.new("ShaderNodeTexImage"); tex.image = img     # on a mesh with a UV map
```

The image was never saved or packed and still rendered in Cycles and EEVEE: left half red, right half blue, the first
rows green at the bottom of the plane (UV (0, 0)). Pixels rewritten after a render showed in the next render in both
engines without `image.update()`. `[exp: experiments/sculpt/texture_pixels.py]` For the image to survive a save, pack
it or save it to a file (`uv-images.md`).

A trap met on the way: `bmesh.ops.create_grid(..., calc_uvs=True)` made no UV map at all (0 UV layers) until the
bmesh had one (`bm.loops.layers.uv.new("UVMap")` before the call). `[exp: experiments/sculpt/texture_pixels.py]`
