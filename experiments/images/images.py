"""Images from Python in 4.5: making them, writing pixels fast, what the pixel values mean for 8-bit and float images,
and what each way of saving does to them (save() keeps the pixels; save_render() applies the scene's view transform)."""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy  # noqa: E402
import numpy as np  # noqa: E402

import exp  # noqa: E402

E = exp.Experiment(__file__)
OUT = E.out("")


def srgb(x):
    return 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055


# 1. New images: defaults.
byte = bpy.data.images.new("byte", 64, 64)
flt = bpy.data.images.new("float", 64, 64, float_buffer=True)
E.fact("A new image's colour space: 8-bit images start as sRGB, float images as Linear Rec.709; both start black and "
       "opaque, with alpha", byte_colorspace=byte.colorspace_settings.name, float_colorspace=flt.colorspace_settings.name,
       byte_first_pixel=[round(v, 3) for v in byte.pixels[:4]], float_first_pixel=[round(v, 3) for v in flt.pixels[:4]],
       channels=byte.channels, is_float=[byte.is_float, flt.is_float])

# 2. Writing pixels: foreach_set against slice assignment, 1024 x 1024.
big = bpy.data.images.new("big", 1024, 1024, float_buffer=True)
arr = np.random.default_rng(0).random(1024 * 1024 * 4, dtype=np.float32)
t = time.time()
big.pixels.foreach_set(arr)
fs = time.time() - t
t = time.time()
big.pixels[:] = arr.tolist()
sl = time.time() - t
back = np.empty(1024 * 1024 * 4, dtype=np.float32)
t = time.time()
big.pixels.foreach_get(back)
fg = time.time() - t
E.fact("Writing 1024 x 1024 RGBA pixels: image.pixels.foreach_set(float32 array) is many times faster than "
       "image.pixels[:] = list; foreach_get reads them back the same way. Pixel rows run bottom to top",
       foreach_set_s=round(fs, 4), slice_assign_s=round(sl, 3), foreach_get_s=round(fg, 4),
       round_trip_exact=bool(np.array_equal(back, arr)))
bpy.data.images.remove(big)

# 3. What the numbers mean: write a known value into an 8-bit and a float image, save both, read them back.
val = 0.5
res = {}
for kind in ("byte", "float"):
    for fmt, ext in (("PNG", "png"), ("OPEN_EXR", "exr")):
        img = bpy.data.images.new(f"{kind}_{fmt}", 64, 64, float_buffer=(kind == "float"))
        img.pixels.foreach_set(np.tile(np.array([val, val, val, 1.0], dtype=np.float32), 64 * 64))
        path = f"{OUT}{kind}.{ext}"
        img.filepath_raw = path
        img.file_format = fmt
        img.save()
        back = bpy.data.images.load(path, check_existing=False)
        p = back.pixels[0]
        res[f"{kind} -> {fmt}"] = dict(read_back=round(p, 4), colorspace=back.colorspace_settings.name)
        if fmt == "PNG":
            import struct
            import zlib
            raw = open(path, "rb").read()
            # first pixel byte of the first scanline (after the filter byte), from the IDAT stream
            idat = b"".join(raw[i + 8:i + 8 + struct.unpack(">I", raw[i:i + 4])[0]]
                            for i in range(8, len(raw)) if raw[i + 4:i + 8] == b"IDAT")
            res[f"{kind} -> {fmt}"]["png_byte"] = zlib.decompress(idat)[1]
        bpy.data.images.remove(back)
E.fact("What image.save() writes for a pixel value of 0.5 (no view transform is applied). An 8-bit image stores 0.5 "
       "as byte 128, already sRGB-encoded: its PNG holds 128, and its EXR holds 0.2158, the linear value of that byte. "
       "A new float image's 0.5 is treated as linear: its PNG holds byte 188 (0.5 encoded as sRGB), and its EXR holds "
       "0.7354, not 0.5 (the next fact)", value_written=val, results=res, srgb_of_half=round(srgb(0.5), 4))

# 3a. A float image's colour space when it is saved to EXR, and when the colour space is set.
import OpenImageIO as oiio  # noqa: E402  (bundled with Blender 4.5)


def file_value(path):
    i = oiio.ImageInput.open(path)
    a = i.read_image("float")
    i.close()
    return round(float(a[0, 0, 0]), 4)


cs_res = {}
for label, cs, when in (("as created (Linear Rec.709)", None, None), ("Non-Color, set before the pixels", "Non-Color", "before"),
                        ("Linear Rec.709, set after the pixels", "Linear Rec.709", "after")):
    img = bpy.data.images.new(f"cs_{len(cs_res)}", 8, 8, float_buffer=True)
    if when == "before":
        img.colorspace_settings.name = cs
    img.pixels.foreach_set(np.full(256, 0.5, dtype=np.float32))
    if when == "after":
        img.colorspace_settings.name = cs
    path = f"{OUT}cs_{len(cs_res)}.exr"
    img.file_format = "OPEN_EXR"
    img.save(filepath=path)
    cs_res[label] = dict(value_in_file=file_value(path), colorspace_after_save=img.colorspace_settings.name,
                         pixels_in_memory_after_save=len(img.pixels))
E.fact("Saving a new float image to EXR does not keep 0.5 as 0.5 unless its colour space is 'Non-Color' set before the "
       "pixels are written: as created it is switched to sRGB on save and the file holds 0.7354 (0.5 encoded as sRGB); "
       "setting a colour space after writing the pixels throws them away (the file holds 0). After save() the image's "
       "pixel buffer can read as empty until the image is reloaded. Mechanism not traced; measured with OpenImageIO",
       results=cs_res)

# 3b. Saving the same image twice.
twice = {}
for kind in ("byte", "float"):
    for copy in (False, True):
        img = bpy.data.images.new(f"twice_{kind}_{copy}", 8, 8, float_buffer=(kind == "float"))
        img.pixels.foreach_set(np.full(256, 0.5, dtype=np.float32))
        img.file_format = "OPEN_EXR"
        img.save(filepath=f"{OUT}twice_{kind}_{copy}.exr", save_copy=copy)
        src = img.source
        img.file_format = "PNG"
        try:
            img.save(filepath=f"{OUT}twice_{kind}_{copy}.png", save_copy=copy)
            second = "ok"
        except RuntimeError as e:
            second = "ERROR " + str(e).splitlines()[0]
        twice[f"{kind}, save_copy={copy}"] = dict(source_after_first_save=src, second_save_as_png=second)
E.fact("After image.save(), a new image becomes a FILE image tied to the saved path. A float image saved as EXR and "
       "then saved again as PNG fails ('does not have any image data'); with save_copy=True the image stays as it was "
       "and can be saved again in another format", results=twice)

# 4. save_render applies the scene's colour management.
sc = bpy.context.scene
out = {}
for vt in ("Standard", "AgX", "Filmic"):
    sc.view_settings.view_transform = vt
    path = f"{OUT}save_render_{vt}.png"
    src = bpy.data.images.new(f"sr_{vt}", 64, 64, float_buffer=True)
    src.pixels.foreach_set(np.tile(np.array([val, val, val, 1.0], dtype=np.float32), 64 * 64))
    src.save_render(path, scene=sc)
    back = bpy.data.images.load(path, check_existing=False)
    out[vt] = round(back.pixels[0], 4)
    bpy.data.images.remove(back)
E.fact("image.save_render(path) applies the scene's view transform and look, like a render: the same linear 0.5 grey "
       "comes out differently under each view transform (AgX is 4.5's default); use image.save() to keep the values",
       read_back_8bit=out, factory_default_view_transform="AgX")

# 5. Data textures: colour space matters when a texture is not a colour.
img = bpy.data.images.new("rough", 8, 8)
img.colorspace_settings.name = "Non-Color"
E.fact("A texture that holds data (roughness, normals, heights) must be read with colour space 'Non-Color', set on the "
       "image: colorspace_settings.name accepts it", set_to=img.colorspace_settings.name,
       is_data=img.colorspace_settings.is_data)

# 6. Packing into the .blend, and what happens to a generated image on save.
orphan = bpy.data.images.new("orphan", 16, 16)
gen = bpy.data.images.new("generated", 16, 16)
gen.generated_color = (1, 0, 0, 1)
gen.pixels.foreach_set(np.tile(np.array([0, 0, 1, 1], dtype=np.float32), 256))   # painted blue
gen.use_fake_user = True
blend = f"{OUT}pack.blend"
bpy.ops.wm.save_as_mainfile(filepath=blend)
bpy.ops.wm.open_mainfile(filepath=blend)
g = bpy.data.images.get("generated")
E.fact("A data-block with no users is not written to the .blend: an image nobody uses is gone after save and reopen. "
       "With use_fake_user it survives, but an image never saved or packed comes back as a GENERATED image: the pixels "
       "written into it are lost (painted blue, reopened red, its generated colour); pack() or saving it to a file "
       "keeps them", orphan_after_reopen=bpy.data.images.get("orphan") is not None,
       fake_user_after_reopen=None if g is None else dict(source=g.source, first_pixel=[round(v, 3) for v in g.pixels[:4]]))
bpy.ops.wm.read_factory_settings(use_empty=True)
p2 = bpy.data.images.new("packed", 16, 16)
p2.pixels.foreach_set(np.tile(np.array([0, 1, 0, 1], dtype=np.float32), 256))
p2.pack()
p2.use_fake_user = True
blend2 = f"{OUT}pack2.blend"
bpy.ops.wm.save_as_mainfile(filepath=blend2)
bpy.ops.wm.open_mainfile(filepath=blend2)
p2 = bpy.data.images.get("packed")
E.fact("A packed image keeps its pixels through save and reopen", source=p2.source, packed=p2.packed_file is not None,
       first_pixel=[round(v, 3) for v in p2.pixels[:4]])
for f in os.listdir(os.path.dirname(OUT)):
    if f.startswith(os.path.basename(OUT)) and not f.endswith(".json"):
        os.remove(os.path.join(os.path.dirname(OUT), f))
E.save()
