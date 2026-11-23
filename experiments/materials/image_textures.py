"""What value does an Image Texture node hand the shader for a known PNG byte, under each colour space setting, and what
are the image and node defaults? Read back as emission in a Raw-view EXR."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import numpy as np
import OpenImageIO as oiio
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
# an 8-bit PNG whose every pixel is (128, 64, 255, 255), written with OIIO so Blender has not touched it
png = E.out("byte128.png")
o = oiio.ImageOutput.create(png)
o.open(png, oiio.ImageSpec(4, 4, 4, oiio.UINT8))
o.write_image(np.tile(np.array([128, 64, 255, 255], np.uint8), (4, 4, 1)))
o.close()
exr = E.out("half.exr")
o = oiio.ImageOutput.create(exr)
o.open(exr, oiio.ImageSpec(4, 4, 3, oiio.FLOAT))
o.write_image(np.full((4, 4, 3), 0.5, np.float32))
o.close()

img = bpy.data.images.load(png)
fimg = bpy.data.images.load(exr)
E.fact("bpy.data.images.load: an 8-bit PNG loads as colorspace sRGB (byte image), an EXR as Linear Rec.709 (float image); "
       "alpha_mode defaults to STRAIGHT",
       png=dict(colorspace=img.colorspace_settings.name, is_float=img.is_float, alpha_mode=img.alpha_mode, depth=img.depth),
       exr=dict(colorspace=fimg.colorspace_settings.name, is_float=fimg.is_float, depth=fimg.depth))
again = bpy.data.images.load(png, check_existing=True)
E.fact("images.load(path, check_existing=True) returns the already-loaded datablock instead of a duplicate",
       same=again == img, n_images=len(bpy.data.images))

bpy.ops.mesh.primitive_plane_add(size=2)
m = bpy.data.materials.new("img")
m.use_nodes = True
nt = m.node_tree
nt.nodes.remove(next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"))
em = nt.nodes.new("ShaderNodeEmission")
nt.links.new(em.outputs[0], next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL").inputs["Surface"])
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = img
nt.links.new(tex.outputs["Color"], em.inputs["Color"])
bpy.context.object.data.materials.append(m)
E.fact("Image Texture node defaults and options",
       interpolation=tex.interpolation, projection=tex.projection, extension=tex.extension,
       interpolation_items=[i.identifier for i in type(tex).bl_rna.properties["interpolation"].enum_items],
       extension_items=[i.identifier for i in type(tex).bl_rna.properties["extension"].enum_items],
       outputs=[s.name for s in tex.outputs])
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 1
cam.location = (0, 0, 2)
scene.collection.objects.link(cam)
scene.camera = cam
scene.world = None
scene.render.engine = "CYCLES"
scene.cycles.samples = 1
scene.render.resolution_x = scene.render.resolution_y = 8
scene.view_settings.view_transform = "Raw"
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"


def shader_value():
    scene.render.filepath = E.out("tmp.exr")
    bpy.ops.render.render(write_still=True)
    v = oiio.ImageBuf(scene.render.filepath).get_pixels(oiio.FLOAT)[4, 4, :3]
    os.remove(scene.render.filepath)
    return [round(float(x), 4) for x in v]


srgb_to_lin = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
rows = {}
for cs in ("sRGB", "Non-Color", "Linear Rec.709"):
    img.colorspace_settings.name = cs
    rows[cs] = shader_value()
E.fact("an Image Texture hands the shader linear values: bytes (128, 64, 255) arrive as (0.216, 0.051, 1.0) under sRGB, "
       "and as byte/255 (0.502, 0.251, 1.0) under Non-Color or a linear space. Normal, roughness and other data maps must be "
       "Non-Color", by_colorspace=rows,
       expected_srgb=[round(srgb_to_lin(b / 255), 4) for b in (128, 64, 255)], expected_raw=[round(b / 255, 4) for b in (128, 64, 255)])
try:
    img.colorspace_settings.name = "Linear"
    bad = "accepted"
except TypeError as e:
    bad = str(e)[:160]
E.fact("the pre-4.0 colour space name 'Linear' is rejected in 4.5 (it is 'Linear Rec.709'); the 3.x-era 'Non-Color' still works",
       error=bad)
img.pack()
E.fact("image.pack() embeds the file in the .blend: packed_file is set", packed=img.packed_file is not None,
       size=img.packed_file.size if img.packed_file else None)
new = bpy.data.images.new("blank", 16, 16, alpha=True, float_buffer=False)
E.fact("bpy.data.images.new makes a generated image (source GENERATED) with colorspace sRGB; float_buffer=True gives Linear Rec.709",
       source=new.source, colorspace=new.colorspace_settings.name,
       float_colorspace=bpy.data.images.new("f", 16, 16, float_buffer=True).colorspace_settings.name)
for p in (png, exr):
    os.remove(p)
E.save(rows=rows)
