# Render passes and the compositor

Blender 4.5.14 LTS on Apple Silicon. Tags: `[inv]` read from Blender (`scripts/kb.py`), `[exp: path]` measured here
(paths relative to the source repository), `[lesson]` from a real project, `[doc: link]` Blender's documentation.

## What goes wrong most often

1. **Reading passes back through `bpy`.** `bpy.data.images.load()` of a multilayer EXR gave an image of size (0, 0)
   with no pixels in background mode, and `image.update()` raised `RuntimeError: Error: Image '...' does not have any
   image data`. Read multilayer EXRs with OpenImageIO, which ships inside Blender's Python (`import OpenImageIO as
   oiio`). `[exp: experiments/compositing/multilayer_readback.py]`
2. **Getting pixels from the Viewer or Render Result image.** After a background render, `bpy.data.images["Render
   Result"]` has 0 pixels and the "Viewer Node" image was a 256 x 256 placeholder that did not match the 64 x 64 render.
   Write a file and read it. `[exp: experiments/rendering/view_transforms.py]`
   `[exp: experiments/compositing/passes_and_compositor.py]`
3. **Expecting the compositor without `use_nodes`.** In 4.5 the compositor is `scene.node_tree`; it is None until
   `scene.use_nodes = True`. `scene.compositing_node_group` does not exist in 4.5.
   `[exp: experiments/compositing/passes_and_compositor.py]`
4. **Assuming the default tree is Render Layers -> Composite.** A new 4.5 compositor tree also holds a Viewer and a
   Reroute: Render Layers Image -> Reroute -> Composite and Viewer. Code that looks for "the link into Composite" finds
   it coming from the Reroute; look nodes up by `type` (`R_LAYERS`, `COMPOSITE`, `VIEWER`).
   `[exp: experiments/compositing/passes_and_compositor.py]`
5. **Asking each engine for a pass it does not have.** With the same view-layer switches on, Cycles wrote `IndexOB`
   but no `Shadow` pass; EEVEE wrote `Shadow` but no `IndexOB`. Neither raised an error. Cycles' shadow for compositing
   is the Shadow Catcher pass (`light-world-camera.md`). `[exp: experiments/compositing/passes_and_compositor.py]`
6. **Reading Depth as distance from the camera.** Cycles' Depth pass is planar: the distance along the view axis. At
   an image corner it read 12.70 m, the planar distance; the distance along the ray was 14.03 m.
   `[exp: experiments/compositing/passes_and_compositor.py]`
7. **File Output slots in multilayer mode.** With `format.file_format = "OPEN_EXR_MULTILAYER"` the inputs are
   `layer_slots`, not `file_slots`, and the node writes one file. `[exp: experiments/compositing/multilayer_readback.py]`

## Turn passes on and write them all to one file

```python
vl = scene.view_layers[0]
for p in ("use_pass_z", "use_pass_normal", "use_pass_ambient_occlusion", "use_pass_mist", "use_pass_position",
          "use_pass_diffuse_color", "use_pass_shadow", "use_pass_object_index", "use_pass_cryptomatte_object",
          "use_pass_cryptomatte_material"):
    setattr(vl, p, True)
scene.render.image_settings.file_format = "OPEN_EXR_MULTILAYER"
scene.render.image_settings.color_depth = "32"
scene.render.filepath = path
bpy.ops.render.render(write_still=True)
```

`[exp: experiments/compositing/passes_and_compositor.py]` Layers written (channel names are
`<ViewLayer>.<Pass>.<channel>`, e.g. `ViewLayer.Depth.Z`, `ViewLayer.Normal.X`):

| pass | view-layer switch | Cycles | EEVEE |
|---|---|---|---|
| Combined | `use_pass_combined` | Combined | Combined |
| Depth | `use_pass_z` | Depth | Depth |
| Normal (world space) | `use_pass_normal` | Normal | Normal |
| AO | `use_pass_ambient_occlusion` | AO | AO |
| Mist | `use_pass_mist` | Mist | Mist |
| Position | `use_pass_position` | Position | Position |
| Diffuse colour | `use_pass_diffuse_color` | DiffCol | DiffCol |
| Shadow | `use_pass_shadow` | (not written) | Shadow |
| Object index | `use_pass_object_index` | IndexOB | (not written) |
| Cryptomatte object, material | `use_pass_cryptomatte_object`, `_material` | CryptoObject00-02, CryptoMaterial00-02 | same |
| Shadow catcher | `view_layer.cycles.use_pass_shadow_catcher` | Shadow Catcher | n/a |

`[exp: experiments/compositing/passes_and_compositor.py]` `[exp: experiments/light/shadow_catcher.py]` The Normal pass
is world space: floor pixels read (0, 0, 1) with the camera looking down at 45 degrees.
`[exp: experiments/compositing/multilayer_readback.py]` All view-layer pass switches: `kb.py struct ViewLayer`. `[inv]`

## Read the passes back

```python
import OpenImageIO as oiio
buf = oiio.ImageBuf(path)
names = list(buf.spec().channelnames)          # ['ViewLayer.Combined.R', ..., 'ViewLayer.Depth.Z', 'ViewLayer.Normal.X', ...]
px = buf.get_pixels(oiio.FLOAT)                # (height, width, channels), row 0 at the top
nrm = px[..., [names.index(f"ViewLayer.Normal.{c}") for c in "XYZ"]]
```

The whole multilayer file is one subimage. `[exp: experiments/compositing/multilayer_readback.py]` Note the row order:
OpenImageIO puts the top row first, while `bpy` `Image.pixels` start at the bottom row.
`[exp: experiments/compositing/passes_and_compositor.py]` (the Viewer comparison flips rows with `[::-1]`).

## The compositor in background mode

```python
scene.use_nodes = True
tree = scene.node_tree
rl = next(n for n in tree.nodes if n.type == "R_LAYERS")
comp = next(n for n in tree.nodes if n.type == "COMPOSITE")
inv = tree.nodes.new("CompositorNodeInvert")
tree.links.new(rl.outputs["Image"], inv.inputs["Color"])
tree.links.new(inv.outputs["Color"], comp.inputs["Image"])
bpy.ops.render.render(write_still=True)        # the written image is what reaches Composite
```

The written file equalled 1 - (the plain render) to 5e-7, so compositor nodes run during background renders
(`scene.render.use_compositing` is True by default `[inv]`). The Render Layers node has one output per enabled pass,
named as in the table (Image, Alpha, Depth, Mist, Position, Normal, IndexOB, DiffCol, AO, CryptoObject00, ...).
`[exp: experiments/compositing/passes_and_compositor.py]`

### File Output node

```python
fo = tree.nodes.new("CompositorNodeOutputFile")
fo.base_path = out_dir + os.sep
fo.format.file_format = "OPEN_EXR"
fo.file_slots[0].path = "depth_"
tree.links.new(rl.outputs["Depth"], fo.inputs[0])
fo.file_slots.new("normal_")
tree.links.new(rl.outputs["Normal"], fo.inputs["normal_"])
```

One file per slot, written during the render, named base_path + slot path + 4-digit frame + extension:
`depth_0001.exr`, `normal_0001.exr`. `[exp: experiments/compositing/passes_and_compositor.py]`

Multilayer, one file:

```python
fo.format.file_format = "OPEN_EXR_MULTILAYER"
fo.base_path = out_dir + os.sep + "passes_"
fo.layer_slots.clear()
for name, out in (("beauty", "Image"), ("depth", "Depth"), ("normal", "Normal")):
    fo.layer_slots.new(name)
    tree.links.new(rl.outputs[out], fo.inputs[name])
```

This wrote `passes_0001.exr` with channels `beauty.R/G/B/A`, `depth.V`, `normal.X/Y/Z`: a single-value slot's channel
is named `V`, not `Z`. `[exp: experiments/compositing/multilayer_readback.py]` `File Output.save_as_render` (default
False) applies the display transform when saving byte images. `[inv]`

## Reference

| thing | 4.5 name | note |
|---|---|---|
| compositor tree | `scene.node_tree` after `scene.use_nodes = True` | |
| node types | `R_LAYERS`, `COMPOSITE`, `VIEWER`, `OUTPUT_FILE` | `CompositorNodeRLayers`, `CompositorNodeComposite`, `CompositorNodeViewer`, `CompositorNodeOutputFile` |
| compositor device / precision | `scene.render.compositor_device`, `compositor_precision` | `[inv]` |
| compositor denoise | `scene.render.compositor_denoise_device`, `compositor_denoise_final_quality` | for the Denoise node `[inv]`; not measured |
| pass switches | `view_layer.use_pass_*`, `view_layer.cycles.use_pass_shadow_catcher`, `view_layer.eevee.use_pass_transparent` | `[inv]` |
| all compositor nodes | `kb.py nodes compositor` | `[inv]` |
