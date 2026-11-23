"""What does each 4.5 view transform (AgX, Standard, Filmic, Khronos PBR Neutral, ...) do to a known linear colour in an
8-bit PNG, what does exposure do, and is an EXR written before or after the view transform?

The camera sees only the world background, so every pixel's scene-linear value is exactly the world colour."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import numpy as np
import OpenImageIO as oiio
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
vs = scene.view_settings
E.fact("a new scene's colour management in 4.5: view transform AgX, look None, exposure 0, gamma 1, display sRGB",
       view_transform=vs.view_transform, look=vs.look, exposure=vs.exposure, gamma=vs.gamma,
       display=scene.display_settings.display_device, sequencer=scene.sequencer_colorspace_settings.name)
try:
    vs.view_transform = "__nope__"
except TypeError as e:
    vt_items = str(e)
E.fact("view_transform is a dynamic enum; the TypeError for a bad value lists the valid ones", type_error=vt_items)

world = bpy.data.worlds.new("World")
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
scene.world = world
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.engine = "CYCLES"
scene.cycles.samples = 1
scene.cycles.use_denoising = False
scene.render.resolution_x = scene.render.resolution_y = 8
scene.render.dither_intensity = 0  # dither adds noise to 8-bit output; off for exact values


def png_value(color, transform, look="None", exposure=0.0):
    bg.inputs["Color"].default_value = (*color, 1)
    vs.view_transform, vs.look, vs.exposure = transform, look, exposure
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_depth = "8"
    scene.render.filepath = E.out("tmp.png")
    bpy.ops.render.render(write_still=True)
    px = oiio.ImageBuf(scene.render.filepath).get_pixels(oiio.UINT8)  # the bytes in the file
    return [int(v) for v in px[4, 4, :3]]


colors = {"black": (0, 0, 0), "mid grey 0.18": (0.18, 0.18, 0.18), "grey 0.5": (0.5, 0.5, 0.5), "white 1.0": (1, 1, 1),
          "over-white 4.0": (4, 4, 4), "pure red 1,0,0": (1, 0, 0), "orange 0.8,0.3,0.05": (0.8, 0.3, 0.05)}
transforms = ["Standard", "AgX", "Filmic", "Khronos PBR Neutral", "Raw"]
table = {t: {name: png_value(c, t) for name, c in colors.items()} for t in transforms}
for t, row in table.items():
    print(t, row)
E.fact("Standard maps scene-linear to sRGB bytes with the plain sRGB curve: 0.18 -> 118, 0.5 -> 188, 1.0 -> 255, 4.0 clips to 255",
       standard=table["Standard"])
E.fact("AgX (the default) keeps mid grey 0.18 at the same byte as Standard (118) but maps linear 1.0 white to 197, not 255, "
       "keeps 4.0 below clipping (233), and desaturates pure red 1,0,0 to 219,57,33",
       agx=table["AgX"])
E.fact("Filmic and Khronos PBR Neutral values for the same colours", filmic=table["Filmic"],
       khronos_pbr_neutral=table["Khronos PBR Neutral"])
E.fact("Raw writes the linear value straight to bytes (0.18 -> 46, 0.5 -> 128)", raw=table["Raw"])

# exposure: +1 stop doubles the linear value before the transform
exp_rows = {ev: png_value((0.18, 0.18, 0.18), "Standard", exposure=ev) for ev in (-1, 0, 1, 2)}
std_036 = png_value((0.36, 0.36, 0.36), "Standard")
E.fact("view_settings.exposure +1 under Standard gives the same bytes as doubling the linear colour (0.18 at +1 EV == 0.36)",
       by_ev=exp_rows, linear_036=std_036)
looks = {lk: png_value((0.18, 0.18, 0.18), "AgX", look=lk) for lk in ("None", "AgX - Punchy", "AgX - High Contrast", "AgX - Base Contrast")}
E.fact("AgX contrast looks pivot on mid grey (0.18 stays 118); Punchy darkens it", mid_grey_by_look=looks)

# EXR: written scene-linear, no view transform
bg.inputs["Color"].default_value = (0.5, 0.25, 4.0, 1)
vs.view_transform, vs.look, vs.exposure = "AgX", "None", 1.0
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"
scene.render.filepath = E.out("tmp.exr")
bpy.ops.render.render(write_still=True)
exr = oiio.ImageBuf(scene.render.filepath).get_pixels(oiio.FLOAT)[4, 4, :3]
E.fact("a rendered EXR stores scene-linear values: neither the view transform (AgX) nor exposure (+1) is applied",
       written=[round(float(v), 4) for v in exr], linear_in=[0.5, 0.25, 4.0])

# reading pixels back in Blender: Image.pixels of a PNG are the file bytes / 255 (display values, not linear)
img = bpy.data.images.load(E.out("tmp.png"))
E.fact("bpy Image.pixels of a loaded 8-bit PNG are its bytes / 255, still display-encoded (not linearised); colorspace sRGB",
       pixels_x255=[round(v * 255) for v in img.pixels[:3]], colorspace=img.colorspace_settings.name)
rr = bpy.data.images.get("Render Result")
E.fact("in background mode the Render Result image has no readable pixels: save to a file and load it instead",
       render_result_pixels=len(rr.pixels) if rr else None)
os.remove(E.out("tmp.png"))
os.remove(E.out("tmp.exr"))
E.save(table=table, exposure=exp_rows, looks=looks)
