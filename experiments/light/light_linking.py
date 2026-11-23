"""Light linking and shadow linking from Python, in Cycles and EEVEE: which objects a light lights (receiver
collection) and which objects cast its shadow (blocker collection). Found missing by the C-001 comparison: the session
without the skill guessed `CollectionObject.object`, which does not exist (evals/results.md).
Scene: a ground plane, two spheres of radius 0.5 m resting at x = -1.5 (left) and x = +1.5 (right), a sun at elevation
50 from the south (shadows fall north, +Y), a black world, an orthographic camera looking straight down. Measured: the
brightness of each sphere's top and of the ground in each sphere's shadow, against lit ground."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import math
import bpy
import OpenImageIO as oiio
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
vl = bpy.context.view_layer
S, W = 6.0, 120                      # 6 m across in 120 px: 0.05 m a pixel

bpy.ops.mesh.primitive_plane_add(size=20)
ground = bpy.context.object
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(-1.5, 0, 0.5))
left = bpy.context.object
left.name = "Left"
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(1.5, 0, 0.5))
right = bpy.context.object
right.name = "Right"
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3
sun.data.angle = math.radians(1)
sun.rotation_euler = (math.radians(90 - 50), 0, math.radians(180 - 180))      # elevation 50, bearing 180 (sun_elevation.py)
scene.collection.objects.link(sun)
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = S
cam.location = (0, 0, 10)
scene.collection.objects.link(cam)
scene.camera = cam
scene.world = bpy.data.worlds.new("Black")
scene.world.use_nodes = True
next(n for n in scene.world.node_tree.nodes if n.type == "BACKGROUND").inputs["Color"].default_value = (0, 0, 0, 1)
scene.render.resolution_x = scene.render.resolution_y = W
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"
scene.cycles.samples = 16
scene.cycles.use_denoising = False
scene.eevee.taa_render_samples = 16
scene.view_settings.view_transform = "Standard"

shadow_y = 0.85                      # on the ground north of each sphere: inside its shadow, outside its outline


def at(px, x, y):
    c = int((x + S / 2) / S * W)
    r = int((S / 2 - y) / S * W)      # file row 0 is the top (+Y)
    return round(float(px[r - 1:r + 2, c - 1:c + 2, :3].mean()), 3)


def measure(engine):
    scene.render.engine = engine
    scene.render.filepath = E.out("tmp.exr")
    bpy.ops.render.render(write_still=True)
    px = oiio.ImageBuf(scene.render.filepath).get_pixels(oiio.FLOAT)
    os.remove(scene.render.filepath)
    return dict(left_top=at(px, -1.5, 0), right_top=at(px, 1.5, 0), left_shadow=at(px, -1.5, shadow_y),
                right_shadow=at(px, 1.5, shadow_y), lit_ground=at(px, 0, -2))


ENGINES = ("CYCLES", "BLENDER_EEVEE_NEXT")
rows = {}
rows["no linking"] = {e: measure(e) for e in ENGINES}

# receivers: a collection holding the ground and the left sphere
recv = bpy.data.collections.new("SunLights")
recv.objects.link(ground)
recv.objects.link(left)
E.fact("an object linked into a collection gets a CollectionObject entry whose light_linking.link_state starts at "
       "INCLUDE; a CollectionObject has no .object, so pair the entries with collection.objects by position",
       states=[c.light_linking.link_state for c in recv.collection_objects],
       has_object_attr=hasattr(recv.collection_objects[0], "object"),
       same_order=[o.name for o in recv.objects])
sun.light_linking.receiver_collection = recv
rows["receivers = ground + left, INCLUDE"] = {e: measure(e) for e in ENGINES}

# receivers: a collection holding only the right sphere, set to EXCLUDE
sun.light_linking.receiver_collection = None
excl = bpy.data.collections.new("NotLitBySun")
excl.objects.link(right)
excl.collection_objects[0].light_linking.link_state = "EXCLUDE"
sun.light_linking.receiver_collection = excl
rows["receivers = right only, EXCLUDE"] = {e: measure(e) for e in ENGINES}

# blockers: the right sphere excluded from casting this light's shadow
sun.light_linking.receiver_collection = None
block = bpy.data.collections.new("NoShadow")
block.objects.link(right)
block.collection_objects[0].light_linking.link_state = "EXCLUDE"
sun.light_linking.blocker_collection = block
rows["blockers = right only, EXCLUDE"] = {e: measure(e) for e in ENGINES}

E.fact("brightness (mean of 3x3 px, linear) of each sphere's top, of the ground in each sphere's shadow, and of lit "
       "ground, for each linking setup and engine", rows=rows)
E.fact("the linking collections need not be in the scene: none of them was linked to scene.collection",
       in_scene=[c.name for c in scene.collection.children])
E.save()
