"""Cycles' film_exposure against the view transform's exposure: what each does to a known value, in the float EXR and
in an 8-bit PNG, and whether film_exposure (a Cycles setting) touches EEVEE.

An emission plane of 0.125 fills an orthographic view. EXR values are read with OpenImageIO; PNG bytes under the Standard
view transform with dither off (linear 0.0625 -> 71, 0.125 -> 99, 0.25 -> 137, 0.5 -> 188)."""
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
scene.cycles.samples = 4
scene.cycles.use_denoising = False
scene.eevee.taa_render_samples = 4
scene.view_settings.view_transform = "Standard"
scene.render.dither_intensity = 0
R = 16
scene.render.resolution_x = scene.render.resolution_y = R
TMP = tempfile.mkdtemp(prefix="bfg-exposure-")

bpy.ops.mesh.primitive_plane_add(size=4)
m = bpy.data.materials.new("e")
m.use_nodes = True
nt = m.node_tree
nt.nodes.clear()
em = nt.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (0.125, 0.125, 0.125, 1)
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(em.outputs[0], out.inputs["Surface"])
bpy.context.object.data.materials.append(m)
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 2
cam.location = (0, 0, 3)
scene.collection.objects.link(cam)
scene.camera = cam


def render(engine, film=1.0, view=0.0):
    scene.render.engine = engine
    scene.cycles.film_exposure = film
    scene.view_settings.exposure = view
    res = {}
    for fmt, ext in (("OPEN_EXR", "exr"), ("PNG", "png")):
        scene.render.image_settings.file_format = fmt
        if fmt == "OPEN_EXR":
            scene.render.image_settings.color_depth = "32"
        p = os.path.join(TMP, f"r.{ext}")
        scene.render.filepath = p
        bpy.ops.render.render(write_still=True)
        fmt_px = oiio.UINT8 if ext == "png" else oiio.FLOAT
        v = oiio.ImageBuf(p).get_pixels(fmt_px)[R // 2, R // 2, 0]
        res[ext] = round(float(v), 4) if ext == "exr" else int(v)
        os.remove(p)
    return res


cases = {}
for film, view in ((1.0, 0.0), (2.0, 0.0), (0.5, 0.0), (1.0, 1.0), (1.0, -1.0), (2.0, 1.0)):
    cases[f"film {film}, view {view:+.0f} EV"] = render("CYCLES", film, view)
E.fact("In Cycles, film_exposure multiplies the rendered values themselves, so it shows in the float EXR (0.125 at "
       "film_exposure 2 wrote 0.25); the view transform's exposure (stops) changes only the display-referred PNG and "
       "leaves the EXR at 0.125. They stack: film 2 with +1 EV wrote byte 188, the PNG of linear 0.5",
       emission=0.125, **cases)

ee = {}
for film, view in ((1.0, 0.0), (2.0, 0.0), (1.0, 1.0)):
    ee[f"film {film}, view {view:+.0f} EV"] = render("BLENDER_EEVEE_NEXT", film, view)
E.fact("EEVEE ignores scene.cycles.film_exposure (the EXR and PNG were unchanged at film_exposure 2); the view "
       "exposure works the same as in Cycles", **ee)

os.rmdir(TMP)
E.save(device=device)
