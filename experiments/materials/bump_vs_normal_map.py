"""Bump node vs Normal Map node on the same surface in Cycles: what normal each gives for a known slope, what Bump's
Distance and Strength mean in units, what object scale does to each, what an sRGB normal map does, whether a normal map
works without UVs, whether the Normal pass carries the bumped normal, and whether the two shade the same under a sun.

The normal a node produces is read by emitting it (n * 0.5 + 0.5) under the Raw view into a float EXR, seen straight
down by an orthographic camera at the middle of a 2 m plane whose height field is a ramp in U (h = u, 0..1 over the
plane's width). Expected bumped normal for distance d: normalize(-d * dh/dx, 0, 1), dh/dx = 0.5 per metre at scale 1."""
import math
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
scene.render.engine = "CYCLES"
device = exp.metal()
scene.cycles.samples = 4
scene.cycles.use_denoising = False
scene.view_settings.view_transform = "Raw"
R = 32
scene.render.resolution_x = scene.render.resolution_y = R
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"
TMP = tempfile.mkdtemp(prefix="bfg-bump-")

bpy.ops.mesh.primitive_plane_add(size=2)      # has a UV map 'UVMap', u = 0..1 along x
plane = bpy.context.object
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 0.5                     # the middle 0.5 m of the plane
cam.location = (0, 0, 3)
scene.collection.objects.link(cam)
scene.camera = cam


def material(build):
    m = bpy.data.materials.new("m")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    normal_socket = build(nt)                   # returns the output socket carrying the normal
    ma = nt.nodes.new("ShaderNodeVectorMath")
    ma.operation = "MULTIPLY_ADD"
    ma.inputs[1].default_value = (0.5, 0.5, 0.5)
    ma.inputs[2].default_value = (0.5, 0.5, 0.5)
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(normal_socket, ma.inputs[0])
    nt.links.new(ma.outputs[0], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def bump(distance=1.0, strength=1.0, invert=False, coord="UV"):
    def b(nt):
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs[coord], sep.inputs[0])
        bp = nt.nodes.new("ShaderNodeBump")
        bp.inputs["Distance"].default_value = distance
        bp.inputs["Strength"].default_value = strength
        bp.invert = invert
        nt.links.new(sep.outputs["X"], bp.inputs["Height"])
        return bp.outputs["Normal"]
    return b


def save_image(name, rgb, float_buffer, colorspace):
    img = bpy.data.images.new(name, 4, 4, float_buffer=float_buffer)
    img.pixels.foreach_set(np.tile(np.array(list(rgb) + [1.0], np.float32), 16))
    path = os.path.join(TMP, name + (".exr" if float_buffer else ".png"))
    img.filepath_raw = path
    img.file_format = "OPEN_EXR" if float_buffer else "PNG"
    img.save()
    bpy.data.images.remove(img)
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = colorspace
    return img


def normal_map(rgb, strength=1.0, float_buffer=True, colorspace="Non-Color", uv_map=""):
    def b(nt):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = save_image(f"nm{len(bpy.data.images)}", rgb, float_buffer, colorspace)
        tex.interpolation = "Closest"
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.uv_map = uv_map
        nm.inputs["Strength"].default_value = strength
        nt.links.new(tex.outputs["Color"], nm.inputs["Color"])
        return nm.outputs["Normal"]
    return b


def read_normal(m, ob=None):
    ob = ob or plane
    ob.data.materials.clear()
    ob.data.materials.append(m)
    p = os.path.join(TMP, "n.exr")
    scene.render.filepath = p
    bpy.ops.render.render(write_still=True)
    px = oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[R // 4: 3 * R // 4, R // 4: 3 * R // 4, :3].reshape(-1, 3)
    n = px.mean(axis=0) * 2 - 1
    spread = float(np.abs(px * 2 - 1 - n).max())
    n = n / np.linalg.norm(n)
    return [round(float(x), 4) for x in n], round(spread, 4)


def tilt_deg(n):
    return round(math.degrees(math.acos(max(-1.0, min(1.0, n[2])))), 2)


def expected(d, grad=0.5):
    v = np.array([-d * grad, 0, 1.0])
    return [round(float(x), 4) for x in v / np.linalg.norm(v)]


# 1. Bump: Distance in metres of height per unit of the Height input.
rows = {}
for d in (0.001, 0.25, 1.0, 2.0):
    n, sp = read_normal(material(bump(distance=d)))
    rows[f"distance {d}"] = dict(normal=n, tilt_deg=tilt_deg(n), expected=expected(d), expected_tilt=tilt_deg(expected(d)),
                                 spread=sp)
E.fact("Bump's Distance is the height in scene units that one unit of the Height input stands for: on a ramp h = u "
       "(0..1 over 2 m, so 0.5 per metre), the normal matched normalize(-Distance x 0.5, 0, 1); the default Distance "
       "0.001 tilts it by under 0.03 degrees, so a 0..1 texture at the default barely shows", **rows)

rows = {}
for s in (1.0, 0.5, 0.25, 0.0):
    n, _ = read_normal(material(bump(distance=1.0, strength=s)))
    full = np.array(expected(1.0))
    lerp = s * full + (1 - s) * np.array([0, 0, 1.0])
    lerp = lerp / np.linalg.norm(lerp)
    rows[f"strength {s}"] = dict(normal=n, tilt_deg=tilt_deg(n), lerp_of_normals=[round(float(x), 4) for x in lerp],
                                 lerp_tilt=tilt_deg(lerp))
n_bump1 = rows["strength 1.0"]["normal"]
n_inv, _ = read_normal(material(bump(distance=1.0, invert=True)))
E.fact("Bump's Strength blends the bumped normal with the unbumped one and normalises (not a scale on the height): "
       "Strength 0.5 at Distance 1 gave the tilt of the normalised average, not of Distance 0.5; invert flips the "
       "slope's sign", **rows, invert=dict(normal=n_inv, tilt_deg=tilt_deg(n_inv)),
       distance_half_tilt=tilt_deg(expected(0.5)))

# 2. The normal map that encodes the same normal, and how it is read.
target = np.array(expected(1.0))
rgb = target * 0.5 + 0.5
n_float, _ = read_normal(material(normal_map(rgb)))
n_png, _ = read_normal(material(normal_map(rgb, float_buffer=False)))
n_srgb, _ = read_normal(material(normal_map(rgb, float_buffer=False, colorspace="sRGB")))
E.fact("A tangent-space Normal Map whose colour encodes the bumped normal (rgb = n x 0.5 + 0.5) gives the same normal "
       "as the Bump node, from a float EXR or an 8-bit PNG under Non-Color; the same PNG left in sRGB gives a different, "
       "wrong normal", colour=[round(float(x), 4) for x in rgb], bump_distance_1=n_bump1,
       float_exr_non_color=n_float, png_non_color=n_png, png_srgb=n_srgb, srgb_tilt_deg=tilt_deg(n_srgb))

n_g, _ = read_normal(material(normal_map((0.5, 0.8, 0.9))))
n_r, _ = read_normal(material(normal_map((0.8, 0.5, 0.9))))
E.fact("Tangent space follows the UV map: red above 0.5 tilts the normal toward +U (here +x), green above 0.5 toward "
       "+V (here +y), the OpenGL convention; a DirectX-style map needs its green channel inverted",
       green_high=n_g, red_high=n_r)

rows = {}
for s in (1.0, 0.5, 2.0):
    n, _ = read_normal(material(normal_map(rgb, strength=s)))
    rows[f"strength {s}"] = dict(normal=n, tilt_deg=tilt_deg(n))
E.fact("Normal Map's Strength scales the tilt away from the surface normal (2.0 tilts further than the map)", **rows)

# 3. Object scale: the bump depends on it, the normal map does not.
plane.scale = (2, 2, 1)
bpy.context.view_layer.update()
nb, _ = read_normal(material(bump(distance=1.0)))
nn, _ = read_normal(material(normal_map(rgb)))
plane.scale = (1, 1, 1)
E.fact("Scaling the object changes the bump but not the normal map: at object scale 2 the same UV ramp spans 4 m and "
       "the bump's tilt fell to that of half the slope (Distance stays in world units: the height is not scaled with "
       "the object), while the normal map's normal was unchanged",
       bump_scale_1=n_bump1, bump_scale_2=nb, bump_scale_2_tilt=tilt_deg(nb),
       expected_world_units=expected(1.0, grad=0.25), expected_object_units=expected(1.0, grad=0.5),
       normal_map_scale_2=nn, normal_map_scale_1=n_float)

# 4. A normal map on a mesh with no UV map.
me = bpy.data.meshes.new("noUV")
me.from_pydata([(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], [], [(0, 1, 2, 3)])
nouv = bpy.data.objects.new("noUV", me)
scene.collection.objects.link(nouv)
plane.hide_render = True
n_nouv, _ = read_normal(material(normal_map(rgb)), ob=nouv)
n_nouv_bump, _ = read_normal(material(bump(distance=1.0, coord="Object")), ob=nouv)
plane.hide_render = False
nouv.hide_render = True
E.fact("On a mesh with no UV map the tangent-space Normal Map still renders without an error but its normal is not "
       "the encoded one; Bump needs no UVs (here driven by Object coordinates: h = x, 1 per metre)",
       normal_map_no_uv=n_nouv, normal_map_no_uv_tilt=tilt_deg(n_nouv), expected=list(target),
       bump_object_coords=n_nouv_bump, bump_object_expected=expected(1.0, grad=1.0))

# 5. The Normal pass, and shading under a sun.
def lit(build):
    m = bpy.data.materials.new("lit")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (1, 1, 1, 1)
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Specular IOR Level"].default_value = 0.0
    nt.links.new(build(nt), bsdf.inputs["Normal"])
    return m


sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 1.0
sun.data.angle = 0.0
sun.rotation_euler = (0, math.radians(-45), 0)   # light arrives from -x, 45 degrees up
scene.collection.objects.link(sun)
scene.cycles.samples = 64
vl = scene.view_layers[0]
vl.use_pass_normal = True
scene.render.image_settings.file_format = "OPEN_EXR_MULTILAYER"


def lit_read(m):
    plane.data.materials.clear()
    plane.data.materials.append(m)
    p = os.path.join(TMP, "lit.exr")
    scene.render.filepath = p
    bpy.ops.render.render(write_still=True)
    buf = oiio.ImageBuf(p)
    names = list(buf.spec().channelnames)
    px = buf.get_pixels(oiio.FLOAT)[R // 4: 3 * R // 4, R // 4: 3 * R // 4]
    comb = px[..., names.index("ViewLayer.Combined.G")].mean()
    nrm = px[..., [names.index(f"ViewLayer.Normal.{c}") for c in "XYZ"]].reshape(-1, 3).mean(axis=0)
    return round(float(comb), 4), [round(float(x), 4) for x in nrm]


flat = lit_read(lit(lambda nt: nt.nodes.new("ShaderNodeTexCoord").outputs["Normal"]))
lb = lit_read(lit(bump(distance=1.0)))
ln = lit_read(lit(normal_map(rgb)))
L = np.array([-math.sin(math.radians(45)), 0, math.cos(math.radians(45))])
lam = lambda n: round(float(max(0.0, np.dot(n, L)) / math.pi), 4)   # white Lambert under a sun of 1 W/m2
E.fact("Under a sun from -x at 45 degrees, a white diffuse surface with the bump and with the matching normal map "
       "rendered the same brightness, brighter than the flat surface as Lambert predicts; Cycles' Normal pass holds "
       "the bumped (shading) normal, not the geometric one",
       flat=dict(combined_g=flat[0], normal_pass=flat[1], lambert=lam(np.array([0, 0, 1.0]))),
       bump=dict(combined_g=lb[0], normal_pass=lb[1], lambert=lam(target)),
       normal_map=dict(combined_g=ln[0], normal_pass=ln[1]))

for f in os.listdir(TMP):
    os.remove(os.path.join(TMP, f))
os.rmdir(TMP)
E.save(device=device, resolution=R)
