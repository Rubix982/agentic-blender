"""A texture painted by data: an image's pixels written from Python, mapped through UVs and an Image Texture node, and
read back from Cycles and EEVEE renders. Also: does a render see pixels changed after an earlier render without
image.update(), and does an image that was never saved render at all."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bmesh
import bpy
import numpy as np
import OpenImageIO as oiio
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
S = 256

me0 = bpy.data.meshes.new("NoUV")
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0, calc_uvs=True)
bm.to_mesh(me0); bm.free()
E.fact("bmesh.ops.create_grid(calc_uvs=True) writes no UV map unless the bmesh already has a UV layer",
       uv_layers_without=len(me0.uv_layers))
me = bpy.data.meshes.new("Plane")
bm = bmesh.new()
bm.loops.layers.uv.new("UVMap")
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0, calc_uvs=True)
bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("Plane", me)
scene.collection.objects.link(ob)
uv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers.active.uv.foreach_get("vector", uv)

img = bpy.data.images.new("paint", S, S)          # 8-bit, sRGB, black
mat = bpy.data.materials.new("Tex"); mat.use_nodes = True
nt = mat.node_tree; nt.nodes.clear()
tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img
em = nt.nodes.new("ShaderNodeEmission"); out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(tex.outputs["Color"], em.inputs["Color"]); nt.links.new(em.outputs[0], out.inputs["Surface"])
me.materials.append(mat)
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.data.type = "ORTHO"; cam.data.ortho_scale = 2.0; cam.location = (0, 0, 3)
scene.collection.objects.link(cam); scene.camera = cam
scene.world = bpy.data.worlds.new("W")
scene.render.resolution_x = scene.render.resolution_y = 128
scene.view_settings.view_transform = "Standard"
scene.render.image_settings.file_format = "OPEN_EXR"
scene.cycles.samples = 4; scene.cycles.use_denoising = False
scene.eevee.taa_render_samples = 4
path = E.out("t.exr")


def paint(left, right):
    px = np.zeros((S, S, 4), np.float32)
    px[..., 3] = 1
    px[:, : S // 2, :3] = left
    px[:, S // 2:, :3] = right
    px[: S // 4, :, :3] = (0, 1, 0)                 # the bottom quarter of the image (first rows) green
    img.pixels.foreach_set(px.ravel())


def render(engine):
    scene.render.engine = engine
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    p = oiio.ImageBuf(path).get_pixels(oiio.FLOAT)    # top row first
    pick = lambda r, c: [round(float(v), 3) for v in p[r, c, :3]]   # noqa: E731
    return dict(top_left=pick(40, 32), top_right=pick(40, 96), bottom=pick(120, 64))


paint((1, 0, 0), (0, 0, 1))
first = {e: render(e) for e in ("CYCLES", "BLENDER_EEVEE_NEXT")}
E.fact("pixels written with image.pixels.foreach_set into a new, never-saved 8-bit image render through UVs in Cycles "
       "and EEVEE: left half red, right half blue, image row 0 at the bottom of the plane (green there)",
       uv_corners=uv.reshape(-1, 2).round(3).tolist(), **first)

paint((1, 1, 0), (0, 1, 1))                         # yellow | cyan, no update()
no_update = {e: render(e) for e in ("CYCLES", "BLENDER_EEVEE_NEXT")}
img.update()
with_update = {e: render(e) for e in ("CYCLES", "BLENDER_EEVEE_NEXT")}
E.fact("pixels rewritten with foreach_set after a render (yellow | cyan) show in the next render in Cycles and EEVEE "
       "without image.update()", without_update=no_update, after_update=with_update)

# 0.5 grey written to an 8-bit sRGB image: what the render sees (alpha 1).
grey = np.tile(np.array([0.5, 0.5, 0.5, 1.0], np.float32), 16)
img2 = bpy.data.images.new("grey", 4, 4)
img2.pixels.foreach_set(grey)
tex.image = img2
g = render("CYCLES")["top_left"]
img3 = bpy.data.images.new("greyf", 4, 4, float_buffer=True)
img3.pixels.foreach_set(grey)
tex.image = img3
gf = render("CYCLES")["top_left"]
img4 = bpy.data.images.new("greyd", 4, 4)
img4.colorspace_settings.name = "Non-Color"
img4.pixels.foreach_set(grey)
tex.image = img4
gd = render("CYCLES")["top_left"]
E.fact("0.5 written to an 8-bit sRGB image renders as about 0.216 linear (0.5 read as an sRGB value); in a float image or a "
       "Non-Color 8-bit image it renders as 0.5 (alpha 1 in all three)", byte_srgb=g, float_linear=gf, byte_noncolor=gd)
os.remove(path)
E.save(size=S)
