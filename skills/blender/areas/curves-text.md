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
6. **Text characters the font lacks.** The built-in font falls back to Blender's bundled fonts: it drew a check mark,
   CJK, Devanagari, Arabic and an emoji ("Héllo ✓" had 225 vertices, "Héllo " 219). A font loaded with
   `bpy.data.fonts.load(path)` does not fall back: a character it lacks comes out as its missing-glyph box (8 vertices
   in DejaVu Sans Mono), with no error. Neither shapes complex scripts (below).
   `[exp: experiments/curves/text_fonts.py]`
7. **Curve to Mesh without caps, or with the curve's radius.** The node's tube is open (16 boundary edges on an
   8-point profile) until `Fill Caps` is on, and in 4.5 the curve's point radius does nothing unless a Radius node is
   wired into the node's `Scale` input (radius 3 left the tube at 0.1 m; wired, 0.3).
   `[exp: experiments/curves/curve_to_mesh_node.py]`
8. **Shrinking a 2D outline with holes by its Offset.** A 2D curve's fill cuts every outline nested inside another as
   a hole, whichever way it winds, and the bevel widens the solid by its radius on each side: a 1 m square with
   `bevel_depth` 0.003 came out 1.006 m wide. A negative `offset` pulls every outline into the solid, the outer edge in
   and each hole out (1.0 m wide at -0.003), but where holes grow into each other the overlaps fill in: with 4 mm gaps
   between holes, offset -0.003 took the front face from 0.404 m2 to 0.8236 instead of shrinking it. A screen traced
   from a photograph came out inside out this way (`production.md`). Keep `offset` at 0, shrink the shape before
   tracing it, and check the evaluated mesh's front-face area against the outlines' own.
   `[exp: experiments/curves/curve_offset_fill.py]`
9. **Build a traced curve at one unit a pixel, and scale its mesh.** A 2D curve of 420 outlines traced from a photo,
   built in metres at 0.000924 m a pixel, filled to a front face of 0.3116 m2; the same outlines built in pixels gave
   1.0485 m2. Halving the outlines down to the one that broke it found a small smoothed island (15 x 4 px), and it
   broke the fill of the whole curve. Build the curve in pixels (extrude and bevel divided by the scale too), make a
   mesh of it with `bpy.data.meshes.new_from_object`, and scale the mesh, not the object, when a material reads object
   coordinates. Then check the front face against the outlines' area, as in item 8. Why the fill breaks in metres is
   not checked; the fill merging points closer than a fixed distance would fit it. `[exp: shots/jali-match/build.py]`

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

### The Curve to Mesh node

A geometry-nodes modifier on the Curve object, Group Input -> Curve to Mesh -> Group Output, with a Curve Circle
(Resolution 8, Radius 0.1) wired into Profile Curve `[exp: experiments/curves/curve_to_mesh_node.py]`:

```python
c2m = ng.nodes.new("GeometryNodeCurveToMesh")          # inputs Curve, Profile Curve, Scale (1.0), Fill Caps (False)
circle = ng.nodes.new("GeometryNodeCurvePrimitiveCircle")
circle.inputs["Resolution"].default_value = 8
circle.inputs["Radius"].default_value = 0.1
ng.links.new(gi.outputs[0], c2m.inputs["Curve"])
ng.links.new(circle.outputs["Curve"], c2m.inputs["Profile Curve"])
c2m.inputs["Fill Caps"].default_value = True
ng.links.new(c2m.outputs["Mesh"], go.inputs[0])
```

The same 4-point open Bezier as above (37 evaluated points) `[exp: experiments/curves/curve_to_mesh_node.py]`:

| profile | vertices, edges, faces | boundary edges | manifold | signed volume |
|---|---|---|---|---|
| none | 37, 36, 0 (a polyline) | | no | |
| circle | 296, 584, 288 | 16 | no | |
| circle, Fill Caps | 296, 584, 290 (two 8-gon caps) | 0 | yes | 0.10899 (normals outward) |
| circle, path closed (`use_cyclic_u`) | 384, 768, 384 | 0 | yes, caps or not | 0.21202 |
| a line 0.2 m wide | 74, 109, 36 (a ribbon) | 74 | no | |

Unlike a bevelled curve with `use_fill_caps` (300 faces, still not manifold, above), Fill Caps made a closed solid.
The size is the profile times the `Scale` input: Scale 2 gave a 0.2 m tube. Points with radius 3 left it at 0.1 until a
Radius node (`GeometryNodeInputRadius`) was wired into Scale (then 0.3). `[exp: experiments/curves/curve_to_mesh_node.py]`

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
Arabic, Devanagari and others). `[exp: experiments/curves/text_to_mesh.py]`

### Fonts from files

Copied from `experiments/curves/text_fonts.py`:

```python
fdir = os.path.join(bpy.utils.system_resource("DATAFILES"), "fonts")
f = bpy.data.fonts.load(os.path.join(fdir, "NotoSansDevanagari-Regular.woff2"), check_existing=True)
cu.font = f                                    # cu: a FONT curve; regular glyphs only (font_bold etc. are separate)
```

Each bundled `.woff2` loaded, and so did a system `.ttf` (Arial) and a `.ttc` collection (Helvetica, its first face).
`check_existing` defaults to False: loading the same path again made a second datablock (`Inter Variable
Regular.001`); with True it returned the one already loaded. `[exp: experiments/curves/text_fonts.py]`

Which characters each font drew (a character counts as drawn when it differs from the font's own missing-glyph shape,
read from an unassigned code point) `[exp: experiments/curves/text_fonts.py]`:

| font | H, é | ✓ | 日 | क | ب | 😀 |
|---|---|---|---|---|---|---|
| built in (Bfont Regular) | yes | yes | yes | yes | yes | yes |
| DejaVu Sans Mono | yes | yes | no | no | yes | no |
| Inter | yes | yes | no | no | no | no |
| Noto Sans CJK | yes | yes | yes | no | no | no |
| Noto Sans Devanagari | no | no | no | yes | no | no |
| Noto Sans Arabic | no | no | no | no | yes | no |
| Noto Emoji | no | no | no | no | no | yes |

The built-in font's क, ب and 😀 had exactly the vertex counts of the same characters in the bundled Noto fonts (336,
413, 1058), drawn larger: it falls back to those files. A loaded font has no fallback, so mixed scripts in one text object
need the built-in font. `[exp: experiments/curves/text_fonts.py]`

No shaping: the Devanagari conjunct क्ष (ka, virama, ssa) in Noto Sans Devanagari had 592 vertices, exactly the 336 +
98 + 158 of its three characters drawn alone, so it came out as separate letters rather than the joined form. Arabic
joining was not checked. `[exp: experiments/curves/text_fonts.py]`

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
| a font from a file | `bpy.data.fonts.load(path, check_existing=True)`, then `text_curve.font = f` `[exp: experiments/curves/text_fonts.py]` |
| sweep in geometry nodes | `GeometryNodeCurveToMesh`: Curve, Profile Curve, Scale, Fill Caps `[exp: experiments/curves/curve_to_mesh_node.py]` |
