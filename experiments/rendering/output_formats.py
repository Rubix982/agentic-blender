"""Which still-image formats can a 4.5 render be written to, with which colour depths and alpha, and what comes back
when the file is read: precision (distinct levels across a smooth ramp), values above 1, alpha, file size?"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import numpy as np
import OpenImageIO as oiio
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
# the camera sees only the world: a horizontal ramp 0..2 (linear), via Gradient Texture on Window coordinates
world = bpy.data.worlds.new("World")
world.use_nodes = True
nt = world.node_tree
tc = nt.nodes.new("ShaderNodeTexCoord")
gr = nt.nodes.new("ShaderNodeTexGradient")
mul = nt.nodes.new("ShaderNodeMath")
mul.operation = "MULTIPLY"
mul.inputs[1].default_value = 2.0
nt.links.new(tc.outputs["Window"], gr.inputs["Vector"])
nt.links.new(gr.outputs["Fac"], mul.inputs[0])
nt.links.new(mul.outputs["Value"], nt.nodes["Background"].inputs["Color"])
scene.world = world
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.engine = "CYCLES"
scene.cycles.samples = 4
scene.cycles.use_denoising = False
scene.render.resolution_x, scene.render.resolution_y = 1024, 32
scene.render.film_transparent = False
scene.view_settings.view_transform = "Standard"
scene.render.dither_intensity = 0
bpy.ops.render.render()
rr = bpy.data.images["Render Result"]

rows = []
fmts = [i.identifier for i in bpy.types.ImageFormatSettings.bl_rna.properties["file_format"].enum_items if i.identifier != "FFMPEG"]
for fmt in fmts:
    st = scene.render.image_settings
    st.file_format = fmt
    depths, modes = [], []
    for d in ("8", "10", "12", "16", "32"):
        try:
            st.color_depth = d
            depths.append(d)
        except TypeError:
            pass
    for m in ("BW", "RGB", "RGBA"):
        try:
            st.color_mode = m
            modes.append(m)
        except TypeError:
            pass
    for d in depths:
        st.file_format = fmt
        st.color_depth = d
        st.color_mode = "RGBA" if "RGBA" in modes else "RGB"
        path = E.out(f"tmp_{fmt}_{d}{scene.render.file_extension}")
        try:
            rr.save_render(path, scene=scene)
            buf = oiio.ImageBuf(path)
            px = buf.get_pixels(oiio.FLOAT)
            spec = buf.spec()
            row = px[4, :, 0]
            rows.append(dict(format=fmt, depth=d, ext=scene.render.file_extension, mode=st.color_mode,
                             channels=spec.nchannels, stored_type=str(spec.format), bytes=os.path.getsize(path),
                             levels=int(len(np.unique(np.round(row, 7)))), max=round(float(row.max()), 3)))
        except Exception as e:
            rows.append(dict(format=fmt, depth=d, error=str(e)[:200]))
        if os.path.exists(path):
            os.remove(path)
    print(fmt, depths, modes)
for r in rows:
    print(r)
get = lambda f, d: next(r for r in rows if r["format"] == f and r["depth"] == d)
E.fact("Render Result.save_render(path, scene=scene) writes the last render in background mode, using scene.render.image_settings",
       ok=not any("error" in r for r in rows))
E.fact("over a 0..2 linear ramp 1024 px wide (Standard view; 512 px lie in 0..1), 8-bit PNG keeps about 215 distinct levels and "
       "clips at 1.0; 16-bit PNG keeps every pixel distinct and also clips at 1.0; half and full float EXR keep all 1024 and values above 1",
       png8=get("PNG", "8"), png16=get("PNG", "16"), exr16=get("OPEN_EXR", "16"), exr32=get("OPEN_EXR", "32"))
E.fact("JPEG accepts only 8-bit RGB (no alpha); the colour depths each format accepts in 4.5",
       jpeg=get("JPEG", "8"), depths={f: [r["depth"] for r in rows if r["format"] == f] for f in fmts})
E.fact("Radiance HDR stores values above 1 at 32-bit float, without alpha", hdr=get("HDR", "32"))
E.fact("EXR codecs in 4.5 (image_settings.exr_codec)",
       codecs=[i.identifier for i in bpy.types.ImageFormatSettings.bl_rna.properties["exr_codec"].enum_items],
       default=scene.render.image_settings.exr_codec)
# JPEG 2000 refuses very small images
scene.render.resolution_x, scene.render.resolution_y = 1024, 8
bpy.ops.render.render()
scene.render.image_settings.file_format = "JPEG2000"
scene.render.image_settings.color_depth = "8"
try:
    bpy.data.images["Render Result"].save_render(E.out("tmp.jp2"), scene=scene)
    j2k = "ok"
except RuntimeError as e:
    j2k = str(e)
if os.path.exists(E.out("tmp.jp2")):
    os.remove(E.out("tmp.jp2"))
E.fact("JPEG 2000 fails to write an image only 8 px tall ('Could not write image: internal error'); 32 px tall works",
       result_8px=j2k[:120], ok_32px=any(r["format"] == "JPEG2000" and "error" not in r for r in rows))
E.save(rows=rows)
