"""What does the 4.5 Sky Texture offer (types, parameters, defaults), how much light does it put on a white floor, and
does a world built from an Environment Texture (an equirectangular image) light the floor as expected?

Floor: Diffuse BSDF albedo 0.8 facing up, seen straight down by an orthographic camera; irradiance E = pi * L / 0.8."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import math
import bpy
import numpy as np
import OpenImageIO as oiio
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
w0 = bpy.data.worlds.new("fresh")
E.fact("bpy.data.worlds.new gives a world with use_nodes False and no node tree; world.color is used until use_nodes is set",
       use_nodes=w0.use_nodes, node_tree=None if w0.node_tree is None else w0.node_tree.name, color=list(w0.color))
w0.use_nodes = True
E.fact("setting world.use_nodes = True creates a Background node (Color, Strength, Weight inputs) wired to World Output",
       nodes=[n.bl_idname for n in w0.node_tree.nodes],
       background_inputs=[s.name for s in w0.node_tree.nodes["Background"].inputs])

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
cam.location = (0, 0, 5)
scene.collection.objects.link(cam)
scene.camera = cam
world = bpy.data.worlds.new("World")
world.use_nodes = True
wnt = world.node_tree
bg = wnt.nodes["Background"]
scene.world = world
scene.render.resolution_x = scene.render.resolution_y = 32
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"
scene.view_settings.view_transform = "Standard"
scene.cycles.samples = 256
scene.cycles.use_denoising = False
scene.eevee.taa_render_samples = 16
exp.metal()


def floor_E(engine="CYCLES"):
    scene.render.engine = engine
    scene.render.filepath = E.out("tmp.exr")
    bpy.ops.render.render(write_still=True)
    px = oiio.ImageBuf(scene.render.filepath).get_pixels(oiio.FLOAT)[8:24, 8:24, :3].mean(axis=(0, 1))
    os.remove(scene.render.filepath)
    return [round(math.pi * float(v) / ALB, 3) for v in px]


# uniform world colour: radiance L everywhere -> a horizontal floor sees half the sphere: E = pi * L
bg.inputs["Color"].default_value = (0.5, 0.5, 0.5, 1)
uni = {eng: floor_E(eng) for eng in ("CYCLES", "BLENDER_EEVEE_NEXT")}
bg.inputs["Strength"].default_value = 2.0
uni2 = floor_E()
bg.inputs["Strength"].default_value = 1.0
E.fact("a uniform world of radiance L lights a horizontal Lambertian floor with irradiance pi * L (0.5 -> 1.571), in both "
       "engines; Background Strength multiplies it", E_uniform_05=uni, E_strength_2=uni2, expected=round(math.pi * 0.5, 3))

# Sky Texture
sky = wnt.nodes.new("ShaderNodeTexSky")
wnt.links.new(sky.outputs["Color"], bg.inputs["Color"])
E.fact("Sky Texture in 4.5: types and the defaults of a new node",
       sky_type_items=[i.identifier for i in type(sky).bl_rna.properties["sky_type"].enum_items], sky_type=sky.sky_type,
       sun_elevation_deg=round(math.degrees(sky.sun_elevation), 2), sun_rotation_deg=round(math.degrees(sky.sun_rotation), 2),
       sun_size_deg=round(math.degrees(sky.sun_size), 3), sun_intensity=sky.sun_intensity, sun_disc=sky.sun_disc,
       altitude_m=sky.altitude, air_density=sky.air_density, dust_density=sky.dust_density, ozone_density=sky.ozone_density,
       turbidity=sky.turbidity, ground_albedo=sky.ground_albedo, sun_direction=[round(v, 3) for v in sky.sun_direction])
rows = []
for elev in (5, 15, 45, 90):
    sky.sky_type = "NISHITA"
    sky.sun_elevation = math.radians(elev)
    for eng in ("CYCLES", "BLENDER_EEVEE_NEXT"):
        rows.append(dict(type="NISHITA", elevation_deg=elev, engine=eng, E=floor_E(eng)))
sky.sun_elevation = math.radians(45)
sky.sun_disc = False
rows.append(dict(type="NISHITA", elevation_deg=45, sun_disc=False, engine="CYCLES", E=floor_E()))
sky.sun_disc = True
for t in ("PREETHAM", "HOSEK_WILKIE"):
    sky.sky_type = t
    sky.sun_direction = (0, -math.cos(math.radians(45)), math.sin(math.radians(45)))
    for eng in ("CYCLES", "BLENDER_EEVEE_NEXT"):
        rows.append(dict(type=t, elevation_deg=45, engine=eng, E=floor_E(eng)))
for r in rows:
    print(r)
nis = [r for r in rows if r["type"] == "NISHITA"]
n45 = next(r for r in nis if r["elevation_deg"] == 45 and r["engine"] == "CYCLES" and "sun_disc" not in r)
E.fact("in Cycles a Nishita sky at strength 1 puts irradiance of about 80-160 on a white floor with the sun at 45-90 degrees, "
       "far past what Standard or AgX can show at exposure 0 (a floor clips above about 1-3); about 90 % of it is the sun disc",
       rows=[r for r in nis if r["engine"] == "CYCLES"], E_45_with_disc=n45["E"],
       E_45_without_disc=next(r for r in nis if "sun_disc" in r)["E"])
ee = [r for r in nis if r["engine"] == "BLENDER_EEVEE_NEXT"]
sky.sky_type = "NISHITA"
sky.sun_elevation = math.radians(45)
thr = {}
for t in (10.0, 1.0):  # 10 is the default world.sun_threshold
    world.sun_threshold = t
    thr[t] = floor_E("BLENDER_EEVEE_NEXT")
world.sun_threshold = 10.0
E.fact("EEVEE does not light the scene with the Nishita sun disc (the manual marks Sun Disc 'Cycles Only'): its floor "
       "irradiance stays near Cycles' no-disc value at every elevation; lowering world.sun_threshold to 1 recovers only a "
       "fraction. In EEVEE, add a Sun light for the sun",
       eevee_rows=ee, eevee_45_by_sun_threshold=thr, cycles_45_without_disc=next(r for r in nis if "sun_disc" in r)["E"])
E.fact("Preetham and Hosek-Wilkie skies (no sun disc of their own) are far dimmer than Nishita at the same sun elevation",
       rows=[r for r in rows if r["type"] != "NISHITA"])

# Environment Texture from an equirectangular EXR made here: uniform radiance 0.25, rotated by a Mapping node
W, H = 64, 32
pix = np.full((H, W, 3), 0.25, np.float32)
path = E.out("env.exr")
out = oiio.ImageOutput.create(path)
out.open(path, oiio.ImageSpec(W, H, 3, oiio.FLOAT))
out.write_image(pix)
out.close()
wnt.nodes.remove(sky)
env = wnt.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(path)
wnt.links.new(env.outputs["Color"], bg.inputs["Color"])
e_env = floor_E()
E.fact("an Environment Texture with a uniform 0.25 equirect EXR lights the floor with pi * 0.25 (0.785); the EXR loads as "
       "Linear Rec.709 (scene linear)", E=e_env, expected=round(math.pi * 0.25, 3), colorspace=env.image.colorspace_settings.name)
os.remove(path)
E.save(rows=rows)
