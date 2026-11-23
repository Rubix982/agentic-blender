"""Which rotation puts a Sun light at a given elevation and compass bearing, and how does the Sky Texture's
sun_rotation map to a bearing? Convention here: +Y is north, +X is east, the bearing is measured clockwise from north.
A Sun light shines along its local -Z, so the direction towards the sun is its local +Z.
Checked three ways: the light's matrix, the length of a 1 m pole's shadow found by ray casts, and the brightest pixel of
an equirectangular render of a Nishita sky, with a control lamp at a known bearing to fix the panorama's orientation."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import math
import bpy
import numpy as np
import OpenImageIO as oiio
from mathutils import Vector
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
vl = bpy.context.view_layer


def sun_rotation(elevation_deg, bearing_deg):
    return (math.radians(90 - elevation_deg), 0.0, math.radians(180 - bearing_deg))


def towards_sun(ob):
    vl.update()
    return (ob.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()


def elevation_bearing(v):
    return math.degrees(math.asin(max(-1, min(1, v.z)))), math.degrees(math.atan2(v.x, v.y)) % 360


sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
scene.collection.objects.link(sun)
rows = []
for e, b in [(30, 0), (30, 90), (60, 225), (10, 135), (45, 300)]:
    sun.rotation_euler = sun_rotation(e, b)
    me, mb = elevation_bearing(towards_sun(sun))
    rows.append(dict(elevation=e, bearing=b, measured_elevation=round(me, 3), measured_bearing=round(mb, 3)))
E.fact("rotation_euler = (radians(90 - elevation), 0, radians(180 - bearing)) puts the sun at that elevation and "
       "bearing (+Y north, +X east, bearing clockwise from north)", rows=rows,
       max_error_deg=max(max(abs(r["measured_elevation"] - r["elevation"]),
                             abs((r["measured_bearing"] - r["bearing"] + 180) % 360 - 180)) for r in rows))

sun.rotation_euler = (math.radians(30), 0, 0)
me, mb = elevation_bearing(towards_sun(sun))
E.fact("tilting the sun by its elevation (rotation_euler.x = radians(30)) puts it at elevation 60, not 30",
       measured_elevation=round(me, 3), measured_bearing=round(mb, 3))

# a 1 m pole's shadow, found by casting rays from the ground towards the sun
bpy.ops.mesh.primitive_plane_add(size=40)
bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=1.0, location=(0, 0, 0.5))
pole = bpy.context.object
shadows = []
for e, b in [(30, 0), (45, 90), (20, 200)]:
    sun.rotation_euler = sun_rotation(e, b)
    d = towards_sun(sun)
    away = Vector((-d.x, -d.y, 0)).normalized()          # the shadow falls away from the sun
    dg = bpy.context.evaluated_depsgraph_get()
    last = 0.0
    for i in range(1, 2000):
        s = i * 0.005
        hit, loc, nrm, idx, obj, mat = scene.ray_cast(dg, away * s + Vector((0, 0, 0.001)), d)
        if hit and obj is not None and obj.name == pole.name:
            last = s
    shadows.append(dict(elevation=e, bearing=b, shadow_m=round(last, 3), predicted_m=round(1 / math.tan(math.radians(e)), 3),
                        shadow_points_to_bearing=round(math.degrees(math.atan2(away.x, away.y)) % 360, 1)))
E.fact("a 1 m pole's shadow under that rotation is 1 / tan(elevation) long, to within the 5 mm step (and 0.02 m pole "
       "radius), and points away from the sun's bearing", rows=shadows)
bpy.data.objects.remove(pole, do_unlink=True)
vl.update()

# the Sky Texture's sun_rotation as a bearing: render a panorama and find the sun disc
cam = bpy.data.objects.new("Pano", bpy.data.cameras.new("Pano"))
cam.data.type = "PANO"
cam.data.panorama_type = "EQUIRECTANGULAR"
cam.rotation_euler = (math.radians(90), 0, 0)            # looks north (+Y), up +Z
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.engine = "CYCLES"
scene.cycles.samples = 4
scene.cycles.use_denoising = False
scene.render.resolution_x, scene.render.resolution_y = 360, 180      # 1 degree per pixel
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"
for ob in [o for o in scene.objects if o.type == "MESH"]:
    bpy.data.objects.remove(ob, do_unlink=True)
sun.hide_render = True
vl.update()


def brightest(path):
    px = oiio.ImageBuf(path).get_pixels(oiio.FLOAT)[:, :, :3].sum(axis=2)
    r, c = np.unravel_index(np.argmax(px), px.shape)
    os.remove(path)
    # file row 0 is the top (elevation +90); column centres at 0.5 px
    return 90 - (r + 0.5) * 180 / px.shape[0], (c + 0.5) * 360 / px.shape[1]


world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = (0, 0, 0, 1)

# control: a small bright lamp due east, 10 degrees up
bpy.ops.mesh.primitive_ico_sphere_add(radius=0.3, location=(10 * math.cos(math.radians(10)), 0, 10 * math.sin(math.radians(10))))
ctrl = bpy.context.object
m = bpy.data.materials.new("Glow")
m.use_nodes = True
nt = m.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
em = nt.nodes.new("ShaderNodeEmission")
em.inputs["Strength"].default_value = 100
nt.links.new(em.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
ctrl.data.materials.append(m)
scene.render.filepath = E.out("tmp.exr")
bpy.ops.render.render(write_still=True)
ce, cu = brightest(scene.render.filepath)
E.fact("in an equirectangular render from a camera at rotation (90, 0, 0) degrees, a lamp due east (bearing 90) at "
       "elevation 10 lands at column 269.5 of 360: column = bearing + 180, so the image centre is north (where the camera "
       "looks) and east is right of centre",
       lamp_found_elevation=round(ce, 1), lamp_found_column_deg=round(cu, 1))
bpy.data.objects.remove(ctrl, do_unlink=True)
vl.update()
# the lamp's column gives the mapping: column_deg = bearing + offset
offset = (cu - 90) % 360

sky = world.node_tree.nodes.new("ShaderNodeTexSky")
sky.sky_type = "NISHITA"
world.node_tree.links.new(sky.outputs["Color"], bg.inputs["Color"])
skyrows = []
for rot in (0, 90, 180, 270):
    sky.sun_elevation = math.radians(30)
    sky.sun_rotation = math.radians(rot)
    scene.render.filepath = E.out("tmp.exr")
    bpy.ops.render.render(write_still=True)
    se, su = brightest(scene.render.filepath)
    skyrows.append(dict(sun_rotation=rot, found_elevation=round(se, 1), found_bearing=round((su - offset) % 360, 1)))
E.fact("the Nishita sky's sun_rotation r puts its sun at bearing r (clockwise from +Y, as in the Sun light rule above) "
       "and sun_elevation is its elevation, to within the 1-degree pixels in bearing and 3 degrees in elevation", rows=skyrows, column_offset_deg=round(offset, 1))
E.save()
