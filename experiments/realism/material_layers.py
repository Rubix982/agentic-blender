"""C-004, materials blended through masks (10 of the 17 realistic scenes) and weathering layers (6 of 17): where each
mask a script can build puts its layer. Each mask is rendered on its own as an emission shader (pixel = mask value)
on a 1 m bevelled box resting on a floor, and read at known points: the floor beside the box and far from it, the
box's top, its front face (upper and lower), its top front edge, and the floor's two halves.
Masks: noise through a ColorRamp; ambient occlusion (dirt in crevices); pointiness (edge wear, Cycles); an up-facing
mask (snow on tops); height; a painted colour attribute. Then one beauty render with the layers combined."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import math
import bpy
import numpy as np
import OpenImageIO as oiio
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
scene.view_settings.view_transform = "Standard"
W, H = 200, 150

bpy.ops.mesh.primitive_grid_add(x_subdivisions=64, y_subdivisions=64, size=4)
floor = bpy.context.object
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
block = bpy.context.object
bev = block.modifiers.new("Bevel", "BEVEL")
bev.width, bev.segments = 0.04, 4
sub = block.modifiers.new("Sub", "SUBSURF")
sub.subdivision_type, sub.levels, sub.render_levels = "SIMPLE", 3, 3
for o in (floor, block):
    bpy.context.view_layer.objects.active = o
    for m in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)       # pointiness needs real vertices
# a painted colour attribute on the floor: 1 on the left half, 0 on the right
ca = floor.data.color_attributes.new("Dirt", "FLOAT_COLOR", "POINT")
for i, v in enumerate(floor.data.vertices):
    ca.data[i].color = (1, 1, 1, 1) if v.co.x < 0 else (0, 0, 0, 1)

cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 3.2
cam.location = (0, -6, 4.2)
cam.rotation_euler = (math.radians(55), 0, 0)
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.film_transparent = True
world = bpy.data.worlds.new("W")
world.use_nodes = True
next(n for n in world.node_tree.nodes if n.type == "BACKGROUND").inputs["Strength"].default_value = 1.0
scene.world = world
bpy.context.view_layer.update()

POINTS = {"floor beside box": (0, -0.58, 0), "floor far": (1.2, -1.3, 0), "box top": (0, 0, 1),
          "box front, upper": (0, -0.5, 0.85), "box front, lower": (0, -0.5, 0.15),
          "box top front edge": (0, -0.5, 1.0), "floor left half": (-1.2, -1.0, 0), "floor right half": (1.2, -1.0, 0)}


def render(engine="CYCLES", samples=32):
    scene.render.engine = engine
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    scene.eevee.taa_render_samples = samples
    scene.render.resolution_x, scene.render.resolution_y = W, H
    scene.render.image_settings.file_format = "OPEN_EXR"
    scene.render.image_settings.color_depth = "32"
    scene.render.filepath = E.out("tmp.exr")
    bpy.ops.render.render(write_still=True)
    px = oiio.ImageBuf(scene.render.filepath).get_pixels(oiio.FLOAT)
    os.remove(scene.render.filepath)
    return px


def read(px):
    out = {}
    for k, p in POINTS.items():
        v = world_to_camera_view(scene, cam, Vector(p))
        c, r = int(v.x * W), int((1 - v.y) * H)
        out[k] = round(float(px[r - 1:r + 2, c - 1:c + 2, 0].mean()), 3)
    vis = px[:, :, 3] > 0.5
    out["coverage of the visible frame"] = round(float((px[:, :, 0][vis] > 0.5).mean()), 3)
    return out


def mask_material(build):
    """A material whose emission is the mask built by build(nodes, links) -> output socket (0..1)."""
    m = bpy.data.materials.new("Mask")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(build(nt.nodes, nt.links), em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    for o in (floor, block):
        o.data.materials.clear()
        o.data.materials.append(m)
    return m


def ramp(nodes, links, src, a, b, constant=False):
    r = nodes.new("ShaderNodeValToRGB")
    r.color_ramp.elements[0].position, r.color_ramp.elements[1].position = a, b
    if constant:
        r.color_ramp.interpolation = "CONSTANT"
    links.new(src, r.inputs["Fac"])
    return r.outputs["Color"]


rows = {}
for t in (0.4, 0.5, 0.6):
    def noise_mask(nodes, links, t=t):
        n = nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = 4
        links.new(nodes.new("ShaderNodeTexCoord").outputs["Object"], n.inputs["Vector"])
        return ramp(nodes, links, n.outputs["Fac"], t, t + 0.001, constant=True)
    mask_material(noise_mask)
    rows[f"noise, ColorRamp step at {t}"] = read(render())


def ao_mask(nodes, links):
    ao = nodes.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.3
    inv = nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    links.new(ao.outputs["AO"], inv.inputs[1])
    return inv.outputs[0]


mask_material(ao_mask)
for engine in ("CYCLES", "BLENDER_EEVEE_NEXT"):
    rows[f"1 - ambient occlusion (distance 0.3 m), {engine}"] = read(render(engine))


# pointiness: first its raw values over the box alone, then a ColorRamp set from them
mask_material(lambda nodes, links: nodes.new("ShaderNodeNewGeometry").outputs["Pointiness"])
floor.hide_render = True
raw = {}
for engine in ("CYCLES", "BLENDER_EEVEE_NEXT"):
    px = render(engine)
    vals = px[:, :, 0][px[:, :, 3] > 0.5]
    raw[engine] = {f"p{q}": round(float(np.percentile(vals, q)), 4) for q in (5, 50, 90, 99)}
floor.hide_render = False
P_LO = raw["CYCLES"]["p50"] + 0.002
P_HI = max(raw["CYCLES"]["p99"], P_LO + 0.002)
rows["raw pointiness over the box's pixels (percentiles)"] = raw


def pointy(nodes, links):
    return ramp(nodes, links, nodes.new("ShaderNodeNewGeometry").outputs["Pointiness"], P_LO, P_HI)


mask_material(pointy)
floor.hide_render = True
for engine in ("CYCLES", "BLENDER_EEVEE_NEXT"):
    px = render(engine)
    vis = px[:, :, 3] > 0.5
    rows[f"pointiness through a ColorRamp {P_LO:.4f} to {P_HI:.4f}, box only, {engine}"] = dict(
        share_of_box_above_half=round(float((px[:, :, 0][vis] > 0.5).mean()), 4), **read(px))
floor.hide_render = False


def up(nodes, links):
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(nodes.new("ShaderNodeNewGeometry").outputs["Normal"], sep.inputs["Vector"])
    return ramp(nodes, links, sep.outputs["Z"], 0.7, 0.9)


mask_material(up)
rows["up-facing: normal Z through a ColorRamp 0.7 to 0.9"] = read(render())


def height(nodes, links):
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(nodes.new("ShaderNodeNewGeometry").outputs["Position"], sep.inputs["Vector"])
    return ramp(nodes, links, sep.outputs["Z"], 0.45, 0.55)


mask_material(height)
rows["height: world Z through a ColorRamp 0.45 to 0.55 m"] = read(render())


def painted(nodes, links):
    c = nodes.new("ShaderNodeVertexColor")
    c.layer_name = "Dirt"
    return c.outputs["Color"]


mask_material(painted)
for engine in ("CYCLES", "BLENDER_EEVEE_NEXT"):
    rows[f"painted colour attribute 'Dirt' (Color Attribute node), {engine}"] = read(render(engine))

E.fact("mask values (0 to 1) at each point, and the share of the visible frame above 0.5, for each mask",
       points=POINTS, rows=rows)

# one beauty render: stone, dirt in the crevices (AO), lighter worn edges (pointiness), moss on top (up x noise)
m = bpy.data.materials.new("Layered")
m.use_nodes = True
nt = m.node_tree
nodes, links = nt.nodes, nt.links
bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")


def mixc(fac, a, b):
    mx = nodes.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    links.new(fac, mx.inputs["Factor"])
    for sock, val in ((mx.inputs["A"], a), (mx.inputs["B"], b)):
        if isinstance(val, tuple):
            sock.default_value = val
        else:
            links.new(val, sock)
    return mx.outputs["Result"]


stone = (0.55, 0.52, 0.47, 1)
c = mixc(ao_mask(nodes, links), stone, (0.12, 0.09, 0.06, 1))
c = mixc(pointy(nodes, links), c, (0.8, 0.78, 0.74, 1))
nz = nodes.new("ShaderNodeTexNoise")
nz.inputs["Scale"].default_value = 6
moss = nodes.new("ShaderNodeMath")
moss.operation = "MULTIPLY"
links.new(up(nodes, links), moss.inputs[0])
links.new(ramp(nodes, links, nz.outputs["Fac"], 0.45, 0.6), moss.inputs[1])
c = mixc(moss.outputs[0], c, (0.12, 0.3, 0.06, 1))
links.new(c, bsdf.inputs["Base Color"])
for o in (floor, block):
    o.data.materials.clear()
    o.data.materials.append(m)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3
sun.rotation_euler = (math.radians(90 - 40), 0, math.radians(180 - 210))
scene.collection.objects.link(sun)
scene.render.film_transparent = False
scene.render.engine = "CYCLES"
scene.cycles.samples = 64
scene.render.resolution_x, scene.render.resolution_y = 400, 300
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_depth = "8"
scene.view_settings.view_transform = "AgX"
scene.render.filepath = E.out("layered.png")
bpy.ops.render.render(write_still=True)
E.fact("the combined material rendered (Cycles, 64 samples, AgX)", image=os.path.basename(scene.render.filepath))
E.save()
