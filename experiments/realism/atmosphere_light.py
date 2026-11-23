"""C-004, the light and air of realistic scenes (kb/research/realism-breakdowns.md): fog four ways (a volume cube, a
world volume, the mist pass mixed in the compositor, and none), colour temperature on lights (2 of 17 artists set
it with Blackbody nodes; 4.5 lights have their own), portals at a window (3 of the 3 interiors), and an object hidden
from the camera that still casts its shadow (2 artists used off-screen shadow casters).
Fog is measured by how bright identical black posts look at 5, 20, 50, 100 and 200 m."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import math
import time
import bpy
import numpy as np
import OpenImageIO as oiio
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
import exp

E = exp.Experiment(__file__)


def mat(name, color, emission=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = 0.9
    return m


def render(scene, w, h, engine="CYCLES", samples=32):
    scene.render.engine = engine
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    scene.eevee.taa_render_samples = samples
    scene.render.resolution_x, scene.render.resolution_y = w, h
    scene.render.image_settings.file_format = "OPEN_EXR"
    scene.render.image_settings.color_depth = "32"
    scene.render.filepath = E.out("tmp.exr")
    t = time.time()
    bpy.ops.render.render(write_still=True)
    px = oiio.ImageBuf(scene.render.filepath).get_pixels(oiio.FLOAT)
    os.remove(scene.render.filepath)
    return px, round(time.time() - t, 2)


def lum(px):
    return px[:, :, :3] @ np.array([0.2126, 0.7152, 0.0722])


# ------------------------------------------------------------------ fog
scene = bpy.context.scene
scene.view_settings.view_transform = "Standard"
bpy.ops.mesh.primitive_plane_add(size=1000)
bpy.context.object.data.materials.append(mat("Ground", (0.3, 0.3, 0.3)))
DIST = (5, 20, 50, 100, 200)
posts = []
black = mat("Post", (0.02, 0.02, 0.02))
for i, d in enumerate(DIST):
    x = (i - 2) * 0.12 * d                               # spread so none hides another
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, d, 2))
    ob = bpy.context.object
    ob.scale = (0.04 * d, 0.04 * d, 4)                   # the same size in the frame at every distance
    ob.data.materials.append(black)
    posts.append(ob)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3
sun.rotation_euler = (math.radians(90 - 30), 0, math.radians(180 - 180))   # 30 up, from the south, behind the camera
scene.collection.objects.link(sun)
world = bpy.data.worlds.new("Sky")
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = (0.45, 0.55, 0.75, 1)
scene.world = world
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.location = (0, 0, 2)
cam.rotation_euler = (math.radians(90), 0, 0)
cam.data.lens = 35
scene.collection.objects.link(cam)
scene.camera = cam
W, H = 320, 160
scene.render.resolution_x, scene.render.resolution_y = W, H
bpy.context.view_layer.update()


def post_values(px):
    out = []
    for ob in posts:
        v = world_to_camera_view(scene, cam, ob.matrix_world.translation)
        c, r = int(v.x * W), int((1 - v.y) * H)
        out.append(round(float(lum(px)[r - 1:r + 2, c - 1:c + 2].mean()), 4))
    return out


fog = {}
px, t = render(scene, W, H)
fog["none"] = dict(posts=post_values(px), seconds=t)
sky_lum = round(float(lum(px)[2:6, :].mean()), 4)

# a volume cube around everything, 150 m up: the sun crosses it before reaching the ground
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 300, 50))
box = bpy.context.object
box.scale = (1200, 1200, 200)
vm = bpy.data.materials.new("Fog")
vm.use_nodes = True
nt = vm.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
pv = nt.nodes.new("ShaderNodeVolumePrincipled")
pv.inputs["Density"].default_value = 0.01
pv.inputs["Color"].default_value = (1, 1, 1, 1)
nt.links.new(pv.outputs["Volume"], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Volume"])
box.data.materials.append(vm)
for engine in ("CYCLES", "BLENDER_EEVEE_NEXT"):
    px, t = render(scene, W, H, engine)
    fog[f"volume cube 150 m tall, density 0.01, {engine}"] = dict(posts=post_values(px), seconds=t)
# a ground layer: the same fog, 20 m deep
box.location, box.scale = (0, 300, 10), (1200, 1200, 20)
bpy.context.view_layer.update()
for engine, vshadow in (("CYCLES", None), ("BLENDER_EEVEE_NEXT", False), ("BLENDER_EEVEE_NEXT", True)):
    if vshadow is not None:
        scene.eevee.use_volumetric_shadows = vshadow
    px, t = render(scene, W, H, engine)
    tag = "" if vshadow is None else f", use_volumetric_shadows={vshadow}"
    fog[f"ground layer 20 m deep, density 0.01, {engine}{tag}"] = dict(posts=post_values(px), seconds=t)
scene.eevee.use_volumetric_shadows = False
volumetric_end_default = scene.eevee.volumetric_end
scene.eevee.volumetric_end = 400
px, t = render(scene, W, H, "BLENDER_EEVEE_NEXT")
fog["ground layer 20 m deep, density 0.01, BLENDER_EEVEE_NEXT, volumetric_end=400"] = dict(posts=post_values(px), seconds=t)
scene.eevee.volumetric_end = volumetric_end_default
bpy.data.objects.remove(box, do_unlink=True)

# a world volume
pv2 = world.node_tree.nodes.new("ShaderNodeVolumePrincipled")
pv2.inputs["Density"].default_value = 0.01
pv2.inputs["Color"].default_value = (1, 1, 1, 1)
wout = next(n for n in world.node_tree.nodes if n.type == "OUTPUT_WORLD")
world.node_tree.links.new(pv2.outputs["Volume"], wout.inputs["Volume"])
for engine in ("CYCLES", "BLENDER_EEVEE_NEXT"):
    px, t = render(scene, W, H, engine)
    fog[f"world volume, density 0.01, {engine}"] = dict(posts=post_values(px), seconds=t)
world.node_tree.nodes.remove(pv2)

# the mist pass, mixed toward the sky colour in the compositor
scene.view_layers[0].use_pass_mist = True
world.mist_settings.start = 0
world.mist_settings.depth = 200
world.mist_settings.falloff = "LINEAR"
scene.use_nodes = True
tree = scene.node_tree
rl = next(n for n in tree.nodes if n.type == "R_LAYERS")
comp = next(n for n in tree.nodes if n.type == "COMPOSITE")
mix = tree.nodes.new("CompositorNodeMixRGB")
mix.inputs[2].default_value = (0.45, 0.55, 0.75, 1)
tree.links.new(rl.outputs["Mist"], mix.inputs["Fac"])
tree.links.new(rl.outputs["Image"], mix.inputs[1])
tree.links.new(mix.outputs["Image"], comp.inputs["Image"])
px, t = render(scene, W, H)
fog["mist pass (linear, 0 to 200 m) mixed to the sky colour"] = dict(posts=post_values(px), seconds=t)
mist_in_file = True
scene.use_nodes = False
E.fact("a black post's brightness at 5, 20, 50, 100 and 200 m, against a sky of this brightness, for each kind of fog "
       "(the farther a post, the closer to the sky it should read)", sky=sky_lum, distances_m=DIST, rows=fog,
       eevee_volumetric_end_default=volumetric_end_default)

# ------------------------------------------------------------------ colour temperature
exp.empty()
scene = bpy.context.scene
scene.view_settings.view_transform = "Standard"
bpy.ops.mesh.primitive_plane_add(size=2)
bpy.context.object.data.materials.append(mat("White", (0.8, 0.8, 0.8)))
lamp = bpy.data.objects.new("Lamp", bpy.data.lights.new("Lamp", "AREA"))
lamp.location = (0, 0, 2)
lamp.data.size = 1
lamp.data.energy = 200
scene.collection.objects.link(lamp)
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 1
cam.location = (0, 0, 5)
scene.collection.objects.link(cam)
scene.camera = cam
temps = {}
for k in (2250, 2700, 4000, 5200, 6500, 9000):
    lamp.data.use_temperature = True
    lamp.data.temperature = k
    px, _ = render(scene, 32, 32, samples=16)
    rgb = px[:, :, :3].mean(axis=(0, 1))
    temps[k] = dict(rgb=[round(float(c), 4) for c in rgb], r_over_b=round(float(rgb[0] / rgb[2]), 3),
                    temperature_color=[round(c, 4) for c in lamp.data.temperature_color])
lamp.data.use_temperature = False
E.fact("a white plate under an area light with use_temperature at each colour temperature: rendered RGB, red over "
       "blue, and the light's temperature_color", rows=temps,
       default=dict(use_temperature=bpy.types.Light.bl_rna.properties["use_temperature"].default,
                    temperature=bpy.types.Light.bl_rna.properties["temperature"].default))

# ------------------------------------------------------------------ a portal at a window
exp.empty()
scene = bpy.context.scene
scene.view_settings.view_transform = "Standard"
wall = mat("Wall", (0.7, 0.7, 0.7))


def box(lo, hi):
    """A box from corner lo to corner hi (metres)."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=[(a + b) / 2 for a, b in zip(lo, hi)])
    ob = bpy.context.object
    ob.scale = [b - a for a, b in zip(lo, hi)]
    ob.data.materials.append(wall)


# inside: x -2..2, y -2..2, z 0..3; walls 0.1 m thick; a 1 x 1 m window in the +Y wall, x -0.5..0.5, z 1..2
box((-2.1, -2.1, -0.1), (2.1, 2.1, 0))          # floor
box((-2.1, -2.1, 3), (2.1, 2.1, 3.1))           # ceiling
box((-2.1, -2.1, 0), (2.1, -2, 3))              # back wall
box((-2.1, -2, 0), (-2, 2, 3))                  # left
box((2, -2, 0), (2.1, 2, 3))                    # right
box((-2.1, 2, 0), (-0.5, 2.1, 3))               # front, left of the window
box((0.5, 2, 0), (2.1, 2.1, 3))                 # front, right of it
box((-0.5, 2, 0), (0.5, 2.1, 1))                # below it
box((-0.5, 2, 2), (0.5, 2.1, 3))                # above it
cen = Vector((0, 2.0, 1.5))
world = bpy.data.worlds.new("Outside")
world.use_nodes = True
next(n for n in world.node_tree.nodes if n.type == "BACKGROUND").inputs["Strength"].default_value = 3
scene.world = world
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.location = (0, 1.5, 1.5)
cam.rotation_euler = (math.radians(90), 0, math.radians(180))          # looks at the back wall, -Y
cam.data.lens = 24
scene.collection.objects.link(cam)
scene.camera = cam
portal_rows = {}
for with_portal in (False, True):
    if with_portal:
        p = bpy.data.objects.new("Portal", bpy.data.lights.new("Portal", "AREA"))
        p.data.size = 1.0
        p.location = (cen.x, cen.y - 0.01, cen.z)
        p.rotation_euler = (math.radians(-90), 0, 0)                      # faces into the room (-Y)
        p.data.cycles.is_portal = True
        scene.collection.objects.link(p)
    px, t = render(scene, 128, 96, samples=16)
    patch = lum(px)[30:66, 40:88]                                        # the back wall, middle of the frame
    portal_rows["with portal" if with_portal else "without"] = dict(mean=round(float(patch.mean()), 4),
                                                                      std=round(float(patch.std()), 4), seconds=t)
E.fact("a closed 4 x 4 x 3 m room lit only through a 1 x 1 m window, Cycles at 16 samples, no denoising: the back "
       "wall's mean and noise (standard deviation) without and with a portal (an area light with cycles.is_portal)",
       rows=portal_rows)

# ------------------------------------------------------------------ a shadow caster the camera cannot see
exp.empty()
scene = bpy.context.scene
scene.view_settings.view_transform = "Standard"
bpy.ops.mesh.primitive_plane_add(size=20)
bpy.context.object.data.materials.append(mat("Ground", (0.5, 0.5, 0.5)))
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 3))
caster = bpy.context.object
caster.scale = (2, 2, 0.1)
caster.data.materials.append(mat("Red", (0.8, 0.05, 0.05)))
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3
scene.collection.objects.link(sun)                                      # straight down
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 8
cam.location = (0, 0, 10)
scene.collection.objects.link(cam)
scene.camera = cam
hidden = {}
for engine in ("CYCLES", "BLENDER_EEVEE_NEXT"):
    for vis in (True, False):
        caster.visible_camera = vis
        px, _ = render(scene, 64, 64, engine, samples=16)
        centre = px[28:36, 28:36, :3].mean(axis=(0, 1))                  # under the caster
        edge = px[2:8, 2:8, :3].mean(axis=(0, 1))                         # open ground
        hidden[f"{engine}, visible_camera={vis}"] = dict(centre_rgb=[round(float(c), 3) for c in centre],
                                                          open_ground_rgb=[round(float(c), 3) for c in edge])
E.fact("a red plate 3 m above the ground, seen from straight above, sun straight down: the centre of the frame (the "
       "plate, or the ground in its shadow) and open ground, with the plate visible to the camera and not",
       rows=hidden)
E.save()
