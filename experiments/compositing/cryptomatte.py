"""Cryptomatte in 4.5, headless: turn on the pass, pull a matte for one object with the Cryptomatte node
(CompositorNodeCryptomatteV2) during a background render, write it with a File Output node and read it back.

Three cubes (CubeA, CubeB, CubeC, each its own material) seen from above. The Object Index pass (pass_index 1, 2, 3)
is the reference: the matte for CubeB should be 1 where IndexOB is 2 and 0 where it is not."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy  # noqa: E402
import numpy as np  # noqa: E402
import OpenImageIO as oiio  # noqa: E402

import exp  # noqa: E402

E = exp.Experiment(__file__)
scene = bpy.context.scene
device = exp.metal()
scene.render.engine = "CYCLES"
scene.cycles.samples = 16
scene.cycles.use_denoising = False
scene.eevee.taa_render_samples = 16
R = 128
scene.render.resolution_x = scene.render.resolution_y = R
TMP = tempfile.mkdtemp(prefix="bfg-crypto-")

for i, (name, x) in enumerate((("CubeA", -1.6), ("CubeB", 0.0), ("CubeC", 1.6))):
    bpy.ops.mesh.primitive_cube_add(size=1.2, location=(x, 0, 0))
    ob = bpy.context.object
    ob.name = name
    ob.pass_index = i + 1
    m = bpy.data.materials.new("Mat" + name[-1])
    ob.data.materials.append(m)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
scene.collection.objects.link(sun)
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 5
cam.location = (0, 0, 5)
scene.collection.objects.link(cam)
scene.camera = cam

vl = scene.view_layers[0]
vl.use_pass_cryptomatte_object = True
vl.use_pass_cryptomatte_material = True
vl.use_pass_object_index = True
crypto_settings = dict(depth=vl.pass_cryptomatte_depth, accurate=getattr(vl, "use_pass_cryptomatte_accurate", None))

scene.use_nodes = True
tree = scene.node_tree
rl = next(n for n in tree.nodes if n.type == "R_LAYERS")
cm = tree.nodes.new("CompositorNodeCryptomatteV2")
new_node = dict(source=cm.source, scene=cm.scene.name if cm.scene else None, layer_name=cm.layer_name,
                matte_id=cm.matte_id, inputs=[s.name for s in cm.inputs], outputs=[s.name for s in cm.outputs],
                layer_names=[i.identifier for i in cm.bl_rna.properties["layer_name"].enum_items])
tree.links.new(rl.outputs["Image"], cm.inputs["Image"])
fo = tree.nodes.new("CompositorNodeOutputFile")
fo.base_path = TMP + os.sep
fo.format.file_format = "OPEN_EXR"
fo.format.color_depth = "32"
fo.file_slots[0].path = "matte_"
tree.links.new(cm.outputs["Matte"], fo.inputs[0])
fo.file_slots.new("image_")
tree.links.new(cm.outputs["Image"], fo.inputs["image_"])
scene.render.image_settings.file_format = "OPEN_EXR_MULTILAYER"
scene.render.image_settings.color_depth = "32"
main = os.path.join(TMP, "render.exr")
scene.render.filepath = main
E.fact("Rendering with view_layer.use_pass_cryptomatte_object on writes CryptoObject00-02 layers and adds those outputs "
       "to the Render Layers node; a new Cryptomatte node starts with these settings",
       render_layers_outputs=[s.name for s in rl.outputs if s.enabled and s.name.startswith("Crypto")],
       view_layer=crypto_settings, new_node=new_node)


try:
    cm.layer_name = "CryptoObject"
    plain_name = "accepted"
except TypeError as e:
    plain_name = str(e)
E.fact("layer_name is a dynamic enum: the registered items say 'CryptoObject', 'CryptoMaterial', 'CryptoAsset', but "
       "the node only takes '<view layer>.CryptoObject' and so on; the plain name raises TypeError", error=plain_name,
       registered=new_node["layer_names"], default=new_node["layer_name"])


def run(matte_id, layer="ViewLayer.CryptoObject", engine="CYCLES"):
    scene.render.engine = engine
    cm.layer_name = layer
    cm.matte_id = matte_id
    for f in os.listdir(TMP):
        os.remove(os.path.join(TMP, f))
    bpy.ops.render.render(write_still=True)
    files = sorted(os.listdir(TMP))
    buf = oiio.ImageBuf(main)
    names = list(buf.spec().channelnames)
    idx = buf.get_pixels(oiio.FLOAT)[..., names.index("ViewLayer.IndexOB.X")] if "ViewLayer.IndexOB.X" in names else None
    mfile = next((f for f in files if f.startswith("matte_")), None)
    matte = oiio.ImageBuf(os.path.join(TMP, mfile)).get_pixels(oiio.FLOAT)[..., 0] if mfile else None
    ifile = next((f for f in files if f.startswith("image_")), None)
    img = oiio.ImageBuf(os.path.join(TMP, ifile)).get_pixels(oiio.FLOAT) if ifile else None
    return dict(files=files, entries=[e.name for e in cm.entries]), idx, matte, img


def score(idx, matte, want):
    mask = np.isin(np.round(idx).astype(int), want)
    inside = matte[mask]
    outside = matte[~mask]
    # interior pixels: away from the mask's edge by 2 px
    core = mask.copy()
    for ax in (0, 1):
        for sh in (-2, 2):
            core &= np.roll(mask, sh, axis=ax)
    return dict(mask_px=int(mask.sum()), matte_sum=round(float(matte.sum()), 1),
                interior_min=round(float(matte[core].min()), 4), interior_mean=round(float(matte[core].mean()), 4),
                outside_max=round(float(outside.max()), 4),
                agree_at_0_5=round(float(((matte > 0.5) == mask).mean()), 4))


info, idx, matte, img = run("CubeB")
idx_cycles = idx
sc = score(idx, matte, [2])
alpha = img[..., 3] if img is not None else None
E.fact("cm.matte_id = 'CubeB' (the object's name) pulled CubeB's matte in a background render: 1.0 inside the object, "
       "0 outside; thresholded at 0.5 it agreed with the Object Index pass on every pixel, and edge pixels just outside "
       "the index mask held partial coverage (anti-aliasing, up to 0.375). The node's Image output is the "
       "render with alpha multiplied by the matte; cm.entries lists the names", **info, score=sc,
       image_alpha_vs_matte_max_diff=round(float(np.abs(alpha - matte).max()), 4) if alpha is not None else None)

info2, idx, matte, _ = run("CubeA,CubeC")
info3, idx, matte3, _ = run("CubeA, CubeC")
E.fact("Several objects: matte_id is a comma-separated list; 'CubeA,CubeC' and 'CubeA, CubeC' gave the same matte",
       **info2, score=score(idx, matte, [1, 3]), with_space=score(idx, matte3, [1, 3]), entries_with_space=info3["entries"])

info4, idx, matte, _ = run("CubeX")
E.fact("A name that matches no object gives an all-zero matte and no error", **info4,
       matte_max=round(float(matte.max()), 4))

info5, idx, matte, _ = run("MatB", layer="ViewLayer.CryptoMaterial")
E.fact("layer_name = 'ViewLayer.CryptoMaterial' with a material name pulls the objects using that material", **info5,
       score=score(idx, matte, [2]))

info6, idx, matte, _ = run("CubeB", engine="BLENDER_EEVEE_NEXT")
E.fact("The same node pulls the matte from an EEVEE render; EEVEE writes no Object Index pass, so the check uses "
       "the Cycles render's index", **info6, eevee_index_pass=idx is not None, score=score(idx_cycles, matte, [2]))

for f in os.listdir(TMP):
    os.remove(os.path.join(TMP, f))
os.rmdir(TMP)
E.save(device=device, resolution=R)
