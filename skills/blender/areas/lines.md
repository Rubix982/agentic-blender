# Lines: Grease Pencil strokes, Line Art, Freestyle

Blender 4.5.14 LTS. Tags: `[inv]` read from Blender (`scripts/kb.py`), `[exp: path]` measured here, `[doc: link]`
Blender's documentation. Experiment: `experiments/lines/lines.py` in the source repository.

## What goes wrong most often

1. **Writing Grease Pencil code for the pre-4.3 API.** Grease Pencil was rewritten in 4.3. A Grease Pencil object's
   type is now `GREASEPENCIL` and its data a `GreasePencilv3` from `bpy.data.grease_pencils_v3`: layers, then frames,
   then a drawing, then strokes. The old `bpy.data.grease_pencils` and `GPencilStroke` still exist (annotations use
   them), so old code may run without error and still draw nothing on a Grease Pencil object.
   `[exp: experiments/lines/lines.py]` `[inv]`
2. **Looking for `strokes.new()`.** Strokes are added in one call, `drawing.add_strokes([points_per_stroke, ...])`,
   then filled through attributes. A new drawing has only `curve_type` and `position`; `radius` (per point, metres) and
   `cyclic` (per stroke) are added when needed. `[exp: experiments/lines/lines.py]`
3. **A normal material on a Grease Pencil object.** It needs Grease Pencil settings:
   `bpy.data.materials.create_gpencil_data(mat)`, then `mat.grease_pencil.color`. `[exp: experiments/lines/lines.py]`
4. **Freestyle that draws nothing, silently.** In a scene built from an empty factory file the view layer's line set has
   no line style. The render printed a Python error (`'NoneType' object has no attribute 'use_chaining'`), raised
   nothing, and had no lines (0 % dark pixels). With `lineset.linestyle = bpy.data.linestyles.new("Ink")` the lines
   appeared (3.4 % of a white frame). `[exp: experiments/lines/lines.py]`

## Strokes from Python

```python
gp = bpy.data.grease_pencils_v3.new("Lines")
ob = bpy.data.objects.new("Lines", gp); scene.collection.objects.link(ob)
layer = gp.layers.new("Ink")
drawing = layer.frames.new(1).drawing                   # frame number 1
drawing.add_strokes([len(star), len(circle)])           # one entry per stroke: its point count
drawing.attributes["position"].data.foreach_set("vector", np.array(star + circle, np.float32).ravel())
cyc = drawing.attributes.get("cyclic") or drawing.attributes.new("cyclic", "BOOLEAN", "CURVE")
cyc.data.foreach_set("value", [True, True])             # close both strokes
rad = drawing.attributes.get("radius") or drawing.attributes.new("radius", "FLOAT", "POINT")
rad.data.foreach_set("value", np.full(n_points, 0.03, np.float32))
mat = bpy.data.materials.new("Ink"); bpy.data.materials.create_gpencil_data(mat)
mat.grease_pencil.color = (0.05, 0.03, 0.02, 1); gp.materials.append(mat)
```

`[exp: experiments/lines/lines.py]`. Other drawing functions in 4.5: `remove_strokes`, `resize_strokes`,
`reorder_strokes`, `set_types` (e.g. `CATMULL_ROM`), `tag_positions_changed`, vertex-group functions. Frames:
`new`, `remove`, `copy`, `move`. Layers: `new(name, set_active=True, layer_group=None)`, `remove`, `move`,
`move_top`, `move_bottom`, `move_to_layer_group`. `[inv]`

## Rendering

A star and a circle, 0.03 m radius, under an orthographic camera at 256 px: the ink covered 5.9 % of the frame in
EEVEE (1.23 s), Cycles (0.15 s) and Workbench (0.01 s) alike. Grease Pencil is drawn as its own layer over the render,
so the engine barely matters. `[exp: experiments/lines/lines.py]`

## Line Art: lines from 3D geometry

`bpy.ops.object.grease_pencil_add(type="LINEART_SCENE")` works headless (also `LINEART_COLLECTION`,
`LINEART_OBJECT`) and gives a Grease Pencil object with a Line Art modifier. On a Suzanne seen from the side it made
121 strokes, 545 points, read from the evaluated object (`ob.evaluated_get(depsgraph).data.layers[0].frames[0].drawing`).
`[exp: experiments/lines/lines.py]` The modifier's settings: `kb.py struct GreasePencilLineartModifier`. `[inv]`

## Freestyle: lines on a render

```python
scene.render.use_freestyle = True
lineset = scene.view_layers[0].freestyle_settings.linesets[0]
if lineset.linestyle is None:                       # true in a scene built from an empty file
    lineset.linestyle = bpy.data.linestyles.new("Ink")
lineset.linestyle.thickness = 2.0
```

Cycles render at 256 px: 0.15 s without lines, 0.31 s with. `[exp: experiments/lines/lines.py]`
