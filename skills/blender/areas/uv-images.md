# UV maps and images

Blender 4.5.14 LTS. Tags: `[inv]` read from Blender (`scripts/kb.py`), `[exp: path]` measured here, `[doc: link]`
Blender's documentation. Experiments: `experiments/uv/uv_unwrap.py`, `experiments/images/images.py` in the source
repository.

## What goes wrong most often

1. **Smart UV Project's angle in degrees.** `bpy.ops.uv.smart_project(angle_limit=...)` takes radians: default 1.1519
   (66°), soft range up to 1.5533 (89°), hard limit 1.5708 (90°). Passing `66` raises nothing; it is clamped to the
   hard limit, and the result matched 90° (2 islands on a 32 x 16 UV sphere), not 66° (6 islands). Use
   `math.radians(66)`. `[inv]` `[exp: experiments/uv/uv_unwrap.py]` (`kb.py op uv.smart_project` prints both ranges.)
2. **Unwrap operators outside edit mode.** `uv.smart_project` in object mode fails its poll ("context is incorrect").
   They work headless once the object is active, in edit mode, with its faces selected. `[exp: experiments/uv/uv_unwrap.py]`
3. **`uv.pack_islands` doing nothing.** It acts on the UV editor's own selection, not the mesh's. After Smart UV
   Project with every face selected, it returned `CANCELLED`; with
   `scene.tool_settings.use_uv_select_sync = True` (UV selection follows the mesh's; off by default) it packed.
   `[exp: experiments/uv/uv_unwrap.py]`
4. **Expecting a new UV map to be empty.** `mesh.uv_layers.new()` gives every face the whole unit square: corners at
   (0,0), (1,0), (1,1), (0,1). `[exp: experiments/uv/uv_unwrap.py]`
5. **bmesh's `verify()` naming.** `bm.loops.layers.uv.verify()` creates a layer when there is none, named `Float2`,
   not `UVMap`. To name it: `bm.loops.layers.uv.new("UVMap")`. `[exp: experiments/uv/uv_unwrap.py]`
6. **`uv_layer.data[i].uv` in a loop.** Deprecated in 4.5 (`MeshUVLoop (Deprecated)`) and slow: setting 160,000
   corners took 0.125 s in a loop and 0.0001 s with `uv_layer.uv.foreach_set("vector", flat)`. `[inv]`
   `[exp: experiments/uv/uv_unwrap.py]`
7. **Saving a float image and expecting the numbers back.** A new float image saved to EXR held 0.7354 for a pixel of
   0.5 (0.5 encoded as sRGB): on save its colour space switched from Linear Rec.709 to sRGB. Only a colour space of
   `Non-Color`, set **before** writing the pixels, kept 0.5. Setting the colour space after writing the pixels threw
   them away (the file held 0). The mechanism was not traced. `[exp: experiments/images/images.py]`
8. **`save_render` where `save` was meant.** `image.save_render(path)` applies the scene's view transform, like a
   render: a linear 0.5 grey read back as 0.7373 (Standard), 0.6667 (AgX, the 4.5 default), 0.6941 (Filmic).
   `image.save()` applies none. `[exp: experiments/images/images.py]`
9. **Images (or any data) that nothing uses.** A data-block with no users is not written to the `.blend`. An image
   made with `images.new` and used by nothing was gone after save and reopen. With `use_fake_user = True` it survived,
   but if it was never saved to a file or packed, it came back as a generated image with its pixels lost (painted
   blue, reopened red, its generated colour). `image.pack()` kept them. `[exp: experiments/images/images.py]`
10. **Saving the same image twice in different formats.** After `save()`, the image becomes a `FILE` image tied to
    that path. A float image saved as EXR and then as PNG failed ("does not have any image data"). With
    `save(filepath=..., save_copy=True)` the image stays as it was and can be saved again. `[exp: experiments/images/images.py]`

## UV maps

A UV map is an attribute: `FLOAT2` on the `CORNER` domain, under the map's name. `[exp: experiments/uv/uv_unwrap.py]`
`MeshUVLoopLayer` has `uv`, `vertex_selection`, `edge_selection` and `pin`, each a per-corner collection. `[inv]`

**From arrays** (fast, no operators):

```python
lay = mesh.uv_layers.new(name="UVMap")
loop_vert = np.empty(len(mesh.loops), dtype=np.int32)
mesh.loops.foreach_get("vertex_index", loop_vert)          # corner -> vertex
uv = vertex_uv[loop_vert].astype(np.float32)               # (corners, 2)
lay.uv.foreach_set("vector", uv.ravel())
```

**Through bmesh:**

```python
uvl = bm.loops.layers.uv.new("UVMap")      # or .verify() for the active one (a new one is named "Float2")
for f in bm.faces:
    for loop in f.loops:
        loop[uvl].uv = (loop.vert.co.x, loop.vert.co.y)
```

**With the unwrap operators** (headless):

```python
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
# or, along seams (edge.use_seam; bmesh: edge.seam = True):
bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.02)      # 4.5: ANGLE_BASED, CONFORMAL, MINIMUM_STRETCH
bpy.context.scene.tool_settings.use_uv_select_sync = True  # before packing
bpy.ops.uv.pack_islands(margin=0.01, rotate=True)
bpy.ops.object.mode_set(mode="OBJECT")
```

| Operator | Measured |
|---|---|
| `uv.smart_project` | 32 x 16 UV sphere: 6 islands at 66°, 28 at 30°, 4 at 89°, 2 at 90°, inside (0.004, 0.004) to (0.996, 0.699) |
| `uv.unwrap` | cylinder with seams round both caps and down one side: 3 islands with each of the three methods |
| `uv.pack_islands` | options in 4.5: `margin`, `margin_method`, `merge_overlap`, `pin`, `pin_method`, `rotate`, `rotate_method`, `scale`, `shape_method`, `udim_source` |
| `uv.lightmap_pack` | a cube: one island per face (6) |

`[exp: experiments/uv/uv_unwrap.py]`

## Images

| | 8-bit (`images.new(name, w, h)`) | float (`float_buffer=True`) |
|---|---|---|
| colour space at creation | `sRGB` | `Linear Rec.709` |
| a pixel of 0.5 means | byte 128, sRGB-encoded (reads 0.502) | linear 0.5 |
| saved as PNG | byte 128 | byte 188 (0.5 encoded as sRGB) |
| saved as EXR | 0.2158 (that byte's linear value) | 0.7354 unless `Non-Color` was set first |

`[exp: experiments/images/images.py]`. Both start black and opaque, with 4 channels.

- **Pixels.** `image.pixels.foreach_set(float32_array)` wrote 1024 x 1024 RGBA in 0.0006 s; `image.pixels[:] = list`
  took 0.1 s. `foreach_get` reads back the same. Rows run from the bottom of the image to the top.
  `[exp: experiments/images/images.py]`
- **Data textures** (roughness, normals, heights, masks): set `colorspace_settings.name = "Non-Color"` (then
  `colorspace_settings.is_data` is True), and set it before writing pixels. `[exp: experiments/images/images.py]`
- **Colour spaces available** on this machine: `kb.py enums` (21 in 4.5, among them `sRGB`, `Non-Color`,
  `Linear Rec.709`, `ACEScg`, `AgX Log`). `[inv]`
- **Saving:** `image.save(filepath=..., quality=0, save_copy=False)` after setting `image.file_format`;
  `image.save_render(filepath, scene=...)` for a render-like result with the view transform; `image.pack()` to keep
  the pixels inside the `.blend`. `[inv]`
- **Reading a file's real values,** bypassing Blender's colour handling: `import OpenImageIO as oiio` is bundled with
  4.5; `oiio.ImageInput.open(path).read_image("float")`. `[exp: experiments/images/images.py]`
