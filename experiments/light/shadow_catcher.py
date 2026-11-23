"""How does a shadow catcher behave in 4.5: with film_transparent, what are the colour and alpha of the floor where the
object's shadow falls and where it does not, in Cycles and in EEVEE?"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import numpy as np
import OpenImageIO as oiio
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
bpy.ops.mesh.primitive_plane_add(size=20)
floor = bpy.context.object
floor.is_shadow_catcher = True  # Object property since 3.0 (was cycles.is_shadow_catcher before)
bpy.ops.mesh.primitive_cube_add(size=1, location=(-1, 0, 1.5))  # floating cube: its shadow falls straight down
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3
sun.data.angle = 0
scene.collection.objects.link(sun)
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 4
cam.location = (0, 0, 10)
scene.collection.objects.link(cam)
scene.camera = cam
w = bpy.data.worlds.new("w")
w.color = (0.2, 0.2, 0.2)
scene.world = w
scene.render.film_transparent = True
scene.render.resolution_x = scene.render.resolution_y = 64
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_mode = "RGBA"
scene.render.image_settings.color_depth = "32"
scene.cycles.samples = 64
scene.cycles.use_denoising = False
exp.metal()
import math
sun.rotation_euler = (math.radians(-30), 0, 0)  # the shadow falls beside the cube: image rows 40-56 at column 16
scene.render.image_settings.file_format = "OPEN_EXR_MULTILAYER"  # all passes in one file


def render(engine, catcher_pass=False):
    scene.render.engine = engine
    scene.view_layers[0].cycles.use_pass_shadow_catcher = catcher_pass
    scene.render.filepath = E.out("tmp.exr")
    bpy.ops.render.render(write_still=True)
    buf = oiio.ImageBuf(scene.render.filepath)
    names = list(buf.spec().channelnames)
    px = buf.get_pixels(oiio.FLOAT)
    os.remove(scene.render.filepath)
    def at(layer, y0, y1, x0, x1):
        idx = [i for i, n in enumerate(names) if n.startswith(f"ViewLayer.{layer}.")]
        return [round(float(px[y0:y1, x0:x1, i].mean()), 3) for i in idx]
    out = dict(channels=names,
               combined_in_shadow=at("Combined", 44, 56, 12, 20), combined_open_floor=at("Combined", 44, 56, 44, 52),
               combined_on_cube=at("Combined", 28, 36, 12, 20))
    if catcher_pass:
        out["catcher_pass_in_shadow"] = at("Shadow Catcher", 44, 56, 12, 20)
        out["catcher_pass_open_floor"] = at("Shadow Catcher", 44, 56, 44, 52)
    return out


cy_off = render("CYCLES", False)
cy_on = render("CYCLES", True)
ee = render("BLENDER_EEVEE_NEXT")
for r in (cy_off, cy_on, ee):
    print({k: v for k, v in r.items() if k != "channels"})
E.fact("Cycles shadow catcher with film_transparent and the Shadow Catcher pass OFF: the Combined pass carries the shadow as "
       "black with alpha = shadow density; lit floor is alpha 0; the floor's own colour never shows",
       **{k: v for k, v in cy_off.items() if k != "channels"})
E.fact("with view_layer.cycles.use_pass_shadow_catcher ON, the Combined pass no longer carries the shadow (alpha 0 there); "
       "the shadow goes to the 'Shadow Catcher' pass as a multiplier (1 = no shadow, lower = shadow), to multiply over the backplate",
       **{k: v for k, v in cy_on.items() if k != "channels"}, channels=cy_on["channels"])
E.fact("EEVEE (4.5) has no shadow catcher: an is_shadow_catcher floor renders as a normal opaque floor",
       **{k: v for k, v in ee.items() if k != "channels"})
E.fact("the property is Object.is_shadow_catcher (and Object.is_holdout); the matching pass is view_layer.cycles.use_pass_shadow_catcher",
       has_object_prop=hasattr(floor, "is_shadow_catcher"), has_cycles_object_prop=hasattr(floor.cycles, "is_shadow_catcher"))
E.save()
