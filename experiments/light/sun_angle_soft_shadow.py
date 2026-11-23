"""How wide is the soft edge of a sun's shadow for a given sun.angle, in Cycles and in EEVEE (with and without
use_shadow_jitter)? A 2 m plate 1 m above the floor, sun straight down; the penumbra is measured along x across the
plate's shadow edge with an orthographic top view. Geometry predicts width = 2 h tan(angle / 2) ~ h * angle."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import math
import bpy
import numpy as np
import OpenImageIO as oiio
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene

# what the two ways of making a light give
bpy.ops.object.light_add(type="POINT")
op_point = bpy.context.object.data
bpy.ops.object.light_add(type="SUN")
op_sun = bpy.context.object.data
E.fact("in background mode with factory settings, bpy.ops.object.light_add gives a point light 10 W with radius 0 and a sun "
       "1 W/m2 with angle 0.526 degrees; bpy.data.lights.new gives energy 10 for every type, a sun included",
       op_point_energy=op_point.energy, op_point_radius=op_point.shadow_soft_size, op_sun_energy=op_sun.energy,
       op_sun_angle_deg=round(math.degrees(op_sun.angle), 3),
       data_point_energy=bpy.data.lights.new("p", "POINT").energy, data_point_radius=bpy.data.lights["p"].shadow_soft_size)
exp.empty()
scene = bpy.context.scene

H = 1.0
# for a uniform disc source the lit fraction across the penumbra is the disc's area left of a line; 5 % and 95 % of the area
# lie at +-0.805 of the radius, so the 5-95 % width is 0.805 of the full penumbra 2 h tan(angle / 2)
seg = lambda t: (math.acos(-t) + t * math.sqrt(1 - t * t)) / math.pi  # area fraction left of x = t (radius 1)
lo_t = next(t / 10000 for t in range(-10000, 10000) if seg(t / 10000) > 0.05)
K = -lo_t  # 5-95 % width as a fraction of the full penumbra (2 radii)
bpy.ops.mesh.primitive_plane_add(size=20)
bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, H))  # the occluder: edge at x = +1
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3
scene.collection.objects.link(sun)
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 0.6  # 0.6 m across, centred on the edge
cam.data.clip_start = 0.01
cam.data.clip_end = 2
cam.location = (1.0, 0.5, 0.5)  # below the plate's height, so the camera sees the floor and not the plate
scene.collection.objects.link(cam)
scene.camera = cam
scene.world = None
R = 256
scene.render.resolution_x, scene.render.resolution_y = R, 32
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"
scene.view_settings.view_transform = "Standard"
scene.cycles.samples = 512
scene.cycles.use_denoising = False
scene.eevee.taa_render_samples = 64
exp.metal()


def penumbra(engine):
    scene.render.engine = engine
    scene.render.filepath = E.out("tmp.exr")
    bpy.ops.render.render(write_still=True)
    prof = oiio.ImageBuf(scene.render.filepath).get_pixels(oiio.FLOAT)[:, :, 0].mean(axis=0)
    os.remove(scene.render.filepath)
    lo, hi = float(np.median(prof[:20])), float(np.median(prof[-20:]))
    f = (prof - lo) / (hi - lo)  # 0 in shadow, 1 in full sun
    px = cam.data.ortho_scale / R
    i05, i95 = int(np.argmax(f > 0.05)), int(np.argmax(f > 0.95))
    return round((i95 - i05) * px * 1000, 1)  # mm, 5 %..95 %


rows = []
for deg in (0.0, 2.0, 10.0):
    sun.data.angle = math.radians(deg)
    full = 2 * H * math.tan(math.radians(deg) / 2) * 1000
    pred = round(full * K, 1)
    rows.append(dict(engine="CYCLES", angle_deg=deg, width_5_95_mm=penumbra("CYCLES"), predicted_5_95_mm=pred))
    for jit in (False, True):
        sun.data.use_shadow_jitter = jit
        rows.append(dict(engine="EEVEE", jitter=jit, angle_deg=deg, width_5_95_mm=penumbra("BLENDER_EEVEE_NEXT"),
                         predicted_5_95_mm=pred))
for r in rows:
    print(r)
cy = [r for r in rows if r["engine"] == "CYCLES"]
E.fact("in Cycles the sun's shadow edge is within 20 % of the width geometry predicts for a disc of angular diameter "
       "sun.angle (full penumbra 2 h tan(angle/2), about h * angle); angle 0 leaves only the pixel filter's blur (~5 mm here)",
       rows=cy, k_5_95=round(K, 4), mm_per_px=round(cam.data.ortho_scale / R * 1000, 2))
ev = [r for r in rows if r["engine"] == "EEVEE"]
E.fact("in EEVEE the shadow edge matches Cycles' width only with light.use_shadow_jitter on (off by default); without it "
       "the soft edge is about a quarter narrower", rows=ev, use_shadow_jitter_default=bpy.data.lights.new("q", "SUN").use_shadow_jitter)
E.save(rows=rows)
