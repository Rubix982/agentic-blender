"""What do a light's strength and power numbers mean in 4.5? Measured as the radiance of a white Lambertian floor
(Diffuse BSDF, albedo 0.8) seen straight down by an orthographic camera, in Cycles and EEVEE.

For a Lambertian surface, radiance L = albedo * E / pi, so the irradiance on the floor is E = pi * L / albedo."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import math
import bpy
import numpy as np
import OpenImageIO as oiio
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
ALB = 0.8
bpy.ops.mesh.primitive_plane_add(size=200)
floor = bpy.context.object
m = bpy.data.materials.new("lambert")
m.use_nodes = True
nt = m.node_tree
nt.nodes.remove(next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"))
dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
dif.inputs["Color"].default_value = (ALB, ALB, ALB, 1)
nt.links.new(dif.outputs["BSDF"], next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL").inputs["Surface"])
floor.data.materials.append(m)
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 0.5
cam.location = (0, 0, 50)
cam.data.clip_end = 200
scene.collection.objects.link(cam)
scene.camera = cam
scene.world = None  # no world: black, no ambient light
scene.render.resolution_x = scene.render.resolution_y = 32
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"
scene.view_settings.view_transform = "Standard"
scene.cycles.samples = 256
scene.cycles.use_denoising = False
scene.eevee.taa_render_samples = 16
exp.metal()

E.fact("bpy.data.lights.new gives every light type energy 10, a sun included (10 W/m2, bright under Standard)",
       sun_energy=bpy.data.lights.new("a", "SUN").energy, sun_angle_deg=round(math.degrees(bpy.data.lights["a"].angle), 3),
       point_energy=bpy.data.lights.new("b", "POINT").energy, point_radius=bpy.data.lights["b"].shadow_soft_size,
       spot_energy=bpy.data.lights.new("c", "SPOT").energy, area_energy=bpy.data.lights.new("d", "AREA").energy,
       area_size=bpy.data.lights["d"].size)


def irradiance(engine):
    scene.render.engine = engine
    scene.render.filepath = E.out("tmp.exr")
    bpy.ops.render.render(write_still=True)
    px = oiio.ImageBuf(scene.render.filepath).get_pixels(oiio.FLOAT)[8:24, 8:24, 0]
    os.remove(scene.render.filepath)
    return math.pi * float(px.mean()) / ALB


def add(kind, **kw):
    ob = bpy.data.objects.new(kind, bpy.data.lights.new(kind, kind))
    for k, v in kw.items():
        if k in ("location", "rotation_euler"):
            setattr(ob, k, v)
        else:
            setattr(ob.data, k, v)
    scene.collection.objects.link(ob)
    return ob


rows = []
# sun: strength in W/m2 = irradiance on a surface facing it; tilting by 60 degrees halves it (cos 60)
for strength, tilt in ((1, 0), (3, 0), (3, 60)):
    ob = add("SUN", energy=strength, rotation_euler=(math.radians(tilt), 0, 0))
    for eng in ("CYCLES", "BLENDER_EEVEE_NEXT"):
        rows.append(dict(light="SUN", strength=strength, tilt_deg=tilt, engine=eng, E=round(irradiance(eng), 4),
                         expected=round(strength * math.cos(math.radians(tilt)), 4)))
    bpy.data.objects.remove(ob)
# point: power P watts at height d (radius 0); compare with the isotropic-emitter law P / (4 pi d^2)
for P, d in ((1000, 2), (1000, 4)):
    ob = add("POINT", energy=P, shadow_soft_size=0.0, location=(0, 0, d))
    for eng in ("CYCLES", "BLENDER_EEVEE_NEXT"):
        e = irradiance(eng)
        rows.append(dict(light="POINT", power=P, height=d, engine=eng, E=round(e, 4),
                         P_over_4pi_d2=round(P / (4 * math.pi * d * d), 4)))
    bpy.data.objects.remove(ob)
# spot: same power, pointing straight down; is the on-axis intensity the same as a point light's?
ob = add("SPOT", energy=1000, shadow_soft_size=0.0, location=(0, 0, 2), spot_size=math.radians(45))
for eng in ("CYCLES", "BLENDER_EEVEE_NEXT"):
    rows.append(dict(light="SPOT", power=1000, height=2, spot_size_deg=45, engine=eng, E=round(irradiance(eng), 4)))
bpy.data.objects.remove(ob)
# area: square 1 m, facing down, 1000 W at 4 m; then size 2 m with the same power; compare with P / (pi d^2),
# the on-axis irradiance of a small one-sided Lambertian emitter
for size in (1.0, 2.0):
    ob = add("AREA", energy=1000, size=size, location=(0, 0, 4))
    for eng in ("CYCLES", "BLENDER_EEVEE_NEXT"):
        rows.append(dict(light="AREA", power=1000, size=size, height=4, engine=eng, E=round(irradiance(eng), 4),
                         P_over_pi_d2=round(1000 / (math.pi * 16), 4), normalize=ob.data.normalize))
    bpy.data.objects.remove(ob)
# light.exposure: power is multiplied by 2**exposure
ob = add("SUN", energy=1, exposure=1.0)
rows.append(dict(light="SUN", strength=1, exposure=1.0, engine="CYCLES", E=round(irradiance("CYCLES"), 4)))
bpy.data.objects.remove(ob)
for r in rows:
    print(r)

sun = [r for r in rows if r["light"] == "SUN" and "exposure" not in r]
E.fact("a sun's strength is its irradiance in W/m2 on a surface facing it, the same in Cycles and EEVEE; tilting 60 degrees halves it",
       rows=sun)
pt = [r for r in rows if r["light"] == "POINT"]
c = pt[0]
E.fact("a point light of power P watts gives irradiance P / (4 pi d^2) at distance d, as an isotropic emitter of P radiant watts "
       "would, in both engines; inverse-square holds (2 m -> 4 m divides by 4)",
       rows=pt, ratio_to_law=round(c["E"] / c["P_over_4pi_d2"], 3), ratio_2m_over_4m=round(pt[0]["E"] / pt[2]["E"], 3))
sp = [r for r in rows if r["light"] == "SPOT"]
E.fact("a spot light of the same power gives the same on-axis irradiance as a point light (the cone masks, it does not focus)",
       spot=sp, point_same_height=[r for r in pt if r["height"] == 2])
ar = [r for r in rows if r["light"] == "AREA"]
E.fact("an area light emits from one side only, like a Lambertian panel: on its axis the irradiance is about P / (pi d^2), four "
       "times a point light of the same power; doubling its size at the same power changes it little (power is total output)",
       rows=ar)
ob = bpy.data.objects.new("x", bpy.data.lights.new("x", "AREA"))
E.fact("Light.normalize is on by default: power stays the total output when the area light's size changes", normalize=ob.data.normalize)
E.fact("light.exposure (new in 4.x) multiplies the power by 2**exposure", row=rows[-1])
E.save(rows=rows)
