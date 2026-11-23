# Curves and text from Python

Blender 4.5.14 LTS on Apple Silicon. Tags: `[inv]` read from Blender (`scripts/kb.py`), `[exp: path]` measured here
(paths relative to the source repository), `[lesson]` from a real project, `[doc: link]` Blender's documentation.

Blender 4.5 has two curve types. **Curve** (`bpy.data.curves`, object type `CURVE`) is the classic one: Bezier, poly
and NURBS splines with bevel, extrude and text (`FONT`). **Curves** (`bpy.data.hair_curves`, object type `CURVES`) is
the attribute-based type that hair and geometry nodes use. `[exp: experiments/curves/hair_curves.py]`

## What goes wrong most often

1. **Poly and NURBS points are 4D.** `spline.points[i].co = (x, y, z)` raises "sequences of dimension 0 should contain
   4 items, not 3"; write `(x, y, z, 1)`. Bezier points (`bezier_points[i].co`) are 3D.
   `[exp: experiments/curves/bezier_poly.py]`
2. **Assuming a new curve is 3D.** `bpy.data.curves.new(name, 'CURVE')` makes a curve with `dimensions = '2D'` and
   `fill_mode = 'NONE'`. It kept its points' z (a point at z 0.5 evaluated to 0.5), but 2D changes the fill and bevel
   options; set `cu.dimensions = '3D'` for a space curve (fill mode then reads `FULL`).
   `[exp: experiments/curves/bezier_poly.py]`
3. **`splines.new()` already has one point.** A new Bezier spline has 1 point; `bezier_points.add(3)` makes 4, not 3.
   `[exp: experiments/curves/bezier_poly.py]`
4. **Expecting a bevelled curve to be a closed solid.** A bevelled open curve with `use_fill_caps` gained cap faces
   (288 -> 300) but was still not manifold; extruded text was not manifold either until `remove_doubles` (860 -> 430
   vertices, then manifold). Clean up after converting if the result must be watertight.
   `[exp: experiments/curves/bezier_poly.py]` `[exp: experiments/curves/text_to_mesh.py]`
5. **`new_from_object` on a Curves (hair) object.** It raised "Object does not have geometry data".
   `bpy.ops.object.convert(target='MESH')` worked (12 points -> 12 vertices, 9 edges).
   `[exp: experiments/curves/hair_curves.py]`
6. **Text characters the font lacks.** "Héllo ✓" with the built-in font raised nothing; glyphs missing from the font
   produce nothing. Load a font that has them (`bpy.data.fonts.load(path)`, untested here).
   `[exp: experiments/curves/text_to_mesh.py]`

## Bezier and poly curves

Copied from `experiments/curves/bezier_poly.py`:

```python
cu = bpy.data.curves.new("path", "CURVE")
cu.dimensions = "3D"
sp = cu.splines.new("BEZIER")                 # starts with 1 point
sp.bezier_points.add(3)
for bp, co in zip(sp.bezier_points, [(0, 0, 0), (1, 1, 0.5), (2, 0, 0), (3, 1, 0)]):
    bp.co = co
    bp.handle_left_type = bp.handle_right_type = "AUTO"     # FREE, VECTOR, ALIGNED, AUTO
ob = bpy.data.objects.new("path", cu)
bpy.context.scene.collection.objects.link(ob)

pc = bpy.data.curves.new("poly", "CURVE")
ps = pc.splines.new("POLY")
ps.points.add(9)
for i, p in enumerate(ps.points):
    p.co = (math.cos(i / 10 * 2 * math.pi), math.sin(i / 10 * 2 * math.pi), 0, 1)   # x, y, z, w
ps.use_cyclic_u = True
```

AUTO handles are computed by Blender as soon as the type is set: the second point's left handle read (0.41, 1.0, 0.5)
before the object existed.
`[exp: experiments/curves/bezier_poly.py]`

## What the curve becomes

Measured by evaluating the object (`ob.evaluated_get(dg).to_mesh()`) `[exp: experiments/curves/bezier_poly.py]`:

| curve | settings | vertices, edges, faces |
|---|---|---|
| open Bezier, 4 points | `resolution_u` 12 (default) | 37, 36, 0 (3 segments x 12 + 1) |
| the same | `resolution_u` 4 | 13, 12, 0 |
| the same | `bevel_depth` 0.1, `bevel_resolution` 2 | 296, 584, 288 (open tube) |
| the same | + `use_fill_caps` | 312, 610, 300 (still not manifold) |
| the same | `extrude` 0.5, no bevel | 74, 109, 36 (a ribbon) |
| the same | `bevel_mode='OBJECT'`, `bevel_object` = a closed square poly curve | 148, 292, 144 (square tube) |
| closed poly, 10 points | none (resolution does not apply to poly) | 10, 10, 0 |
| the same, `dimensions='2D'`, `fill_mode='BOTH'` | filled | 10, 17, 8 |

Bevel modes are `ROUND`, `OBJECT` and `PROFILE`. `[exp: experiments/curves/bezier_poly.py]`

## Curve to mesh

```python
me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))   # data, no context

with bpy.context.temp_override(active_object=ob, object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
    bpy.ops.object.convert(target="MESH")      # replaces the object's data with a mesh; the curve datablock stays
```

`new_from_object` gave the 37-vertex polyline; `convert` turned the bevelled curve object into a MESH object with 296
vertices, and the curve datablocks stayed in `bpy.data.curves` (orphans to purge). `[exp: experiments/curves/bezier_poly.py]`
The geometry-nodes route is the Curve to Mesh node (`GeometryNodeCurveToMesh`) `[inv]`; untested here.

## Text

Copied from `experiments/curves/text_to_mesh.py`:

```python
cu = bpy.data.curves.new("txt", "FONT")        # a TextCurve; font "Bfont Regular" (built in)
cu.body = "Hello"
cu.extrude = 0.05
cu.align_x = "CENTER"                          # LEFT, CENTER, RIGHT, JUSTIFY, FLUSH
ob = bpy.data.objects.new("txt", cu)
bpy.context.scene.collection.objects.link(ob)
me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
```

| "Hello", size 1 | vertices, faces | width, depth |
|---|---|---|
| flat | 215, 209 | 2.087, 0 |
| `extrude` 0.05 | 860, 633 | 2.087, 0.1 (extrude goes both ways) |
| + `bevel_depth` 0.01 | 2,150, 1,923 | 2.107, 0.12 |
| `size` 2, flat | 215, 209 | 4.174, 0 |

`align_x='CENTER'` put the text from x -1.02 to 1.06. A newline in `body` starts a second line. After
`new_from_object` the extruded text had 860 vertices and was not manifold; `bmesh.ops.remove_doubles(dist=1e-5)`
made it 430 and manifold, with no n-gons left. `[exp: experiments/curves/text_to_mesh.py]`

Fonts shipped with Blender are in `datafiles/fonts` (`DejaVuSansMono.woff2`, `Inter.woff2`, Noto families for CJK,
Arabic, Devanagari and others). `[exp: experiments/curves/text_to_mesh.py]` Loading them as text fonts was not tried.

## The Curves (hair) type, briefly

Copied from `experiments/curves/hair_curves.py`:

```python
hc = bpy.data.hair_curves.new("hair")          # empty: 0 curves, a 'position' attribute
hc.add_curves([4, 4, 4])                       # three curves of 4 points
hc.attributes["position"].data.foreach_set("vector", pos.ravel())   # pos: float32 (12, 3)
r = hc.attributes.get("radius") or hc.attributes.new("radius", "FLOAT", "POINT")
r.data.foreach_set("value", np.full(12, 0.01, np.float32))
hc.set_types(type="POLY")                      # writes a CURVE-domain INT8 'curve_type'; absent = Catmull-Rom
ob = bpy.data.objects.new("hair", hc)          # ob.type == 'CURVES'
```

`hc.curves[i].first_point_index` gave 0, 4, 8. Functions on the type: `add_curves`, `remove_curves`, `resize_curves`,
`reorder_curves`, `set_types`. `[exp: experiments/curves/hair_curves.py]` Shaping hair is done with the bundled hair
node groups (`geometry-nodes.md`).

## Reference

| want | 4.5 |
|---|---|
| new curve data | `bpy.data.curves.new(name, 'CURVE' / 'SURFACE' / 'FONT')` `[exp: experiments/curves/bezier_poly.py]` |
| spline types | `cu.splines.new('BEZIER' / 'POLY' / 'NURBS')` |
| point coordinates | Bezier: `bezier_points[i].co` (3D) and `handle_left`, `handle_right`; poly/NURBS: `points[i].co` (4D) |
| closed spline | `spline.use_cyclic_u = True` |
| sweep a profile | `bevel_depth` + `bevel_resolution`, or `bevel_mode='OBJECT'` + `bevel_object` |
| hair-type curves | `bpy.data.hair_curves.new(name)`, `add_curves([...])`, attributes `position`, `radius`, `curve_type` |
