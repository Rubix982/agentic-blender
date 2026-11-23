"""Rotating an HDRI with a Mapping node in front of the Environment Texture: which way does a Z rotation turn the
lighting, and where does the middle of an equirectangular image point with no rotation?

The HDRI is made here: a black equirectangular EXR with one bright spot at u = 0.5 (the image's middle column),
30 degrees above the horizon. A white diffuse sphere at the origin is rendered from straight above (orthographic,
image right = +x, image up = +y); the brightness-weighted centre of the sphere's pixels gives the azimuth the light
comes from (degrees counter-clockwise from +x, seen from above)."""
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
scene.cycles.samples = 64
scene.cycles.use_denoising = False
scene.view_settings.view_transform = "Raw"
scene.render.film_transparent = True
R = 128
scene.render.resolution_x = scene.render.resolution_y = R
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"
TMP = tempfile.mkdtemp(prefix="bfg-hdri-")

# the HDRI: 256 x 128, one Gaussian spot at u = 0.5, elevation 30 degrees (v = 0.5 + 30/180)
W, H = 256, 128
u0, elev = 0.5, 30.0
v0 = 0.5 + elev / 180.0
yy, xx = np.mgrid[0:H, 0:W]
row0 = (1.0 - v0) * H - 0.5          # OpenImageIO writes the top row first; Blender's v = 1 is the top
col0 = u0 * W - 0.5
spot = 2000.0 * np.exp(-((xx - col0) ** 2 + (yy - row0) ** 2) / (2 * 2.0 ** 2))
img = np.repeat(spot[..., None].astype(np.float32), 3, axis=2)
hdri = os.path.join(TMP, "spot.exr")
out = oiio.ImageOutput.create(hdri)
out.open(hdri, oiio.ImageSpec(W, H, 3, oiio.FLOAT))
out.write_image(img)
out.close()

world = bpy.data.worlds.new("W")
scene.world = world
world.use_nodes = True
wnt = world.node_tree
bg = next(n for n in wnt.nodes if n.type == "BACKGROUND")
env = wnt.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(hdri)
wnt.links.new(env.outputs["Color"], bg.inputs["Color"])
tc = wnt.nodes.new("ShaderNodeTexCoord")
mp = wnt.nodes.new("ShaderNodeMapping")
wnt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])

bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=64, ring_count=32)
sph = bpy.context.object
sph.data.shade_smooth()
m = bpy.data.materials.new("white")
m.use_nodes = True
b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
b.inputs["Base Color"].default_value = (1, 1, 1, 1)
b.inputs["Roughness"].default_value = 1.0
b.inputs["Specular IOR Level"].default_value = 0.0
sph.data.materials.append(m)
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 2.2
cam.location = (0, 0, 5)
scene.collection.objects.link(cam)
scene.camera = cam


def lit_azimuth():
    p = os.path.join(TMP, "r.exr")
    scene.render.filepath = p
    bpy.ops.render.render(write_still=True)
    px = oiio.ImageBuf(p).get_pixels(oiio.FLOAT)
    os.remove(p)
    lum = px[..., :3].mean(axis=2) * (px[..., 3] > 0.99)
    rows, cols = np.mgrid[0:R, 0:R]
    x = (cols + 0.5) / R - 0.5          # +x to the right
    y = 0.5 - (rows + 0.5) / R          # +y up (row 0 is the top)
    w = lum.sum()
    cx, cy = float((lum * x).sum() / w), float((lum * y).sum() / w)
    return round(math.degrees(math.atan2(cy, cx)), 1)


def setup(linked=True, kind="POINT", rot_z=0.0):
    if linked and not env.inputs["Vector"].is_linked:
        wnt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    if not linked:
        for l in list(env.inputs["Vector"].links):
            wnt.links.remove(l)
    mp.vector_type = kind
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(rot_z))


setup(linked=False)
no_vector = lit_azimuth()
setup(linked=True, rot_z=0)
generated_0 = lit_azimuth()
E.fact("With nothing in the Environment Texture's Vector input, the middle column of an equirectangular image "
       "(u = 0.5) lights the scene from +x (azimuth 0); Texture Coordinate Generated -> Mapping at rotation 0 gives "
       "the same", azimuth_no_vector=no_vector, azimuth_generated_mapping_0=generated_0)

rows = {}
for kind in ("POINT", "TEXTURE"):
    for rz in (90.0, 30.0, -90.0):
        setup(kind=kind, rot_z=rz)
        rows[f"{kind} {rz:+.0f}"] = lit_azimuth()
E.fact("A Mapping node of type POINT (the default) rotated +90 degrees about Z turns the lighting by -90 degrees "
       "(clockwise seen from above): the light that came from +x comes from -y. Type TEXTURE turns it the other way, "
       "by the rotation as written. The amount matches the angle in both", azimuths=rows, start=generated_0)

for f in os.listdir(TMP):
    os.remove(os.path.join(TMP, f))
os.rmdir(TMP)
E.save(device=device, hdri=dict(width=W, height=H, spot_u=u0, spot_elevation_deg=elev))
