"""Cycles texture baking headless in 4.5: what does bpy.ops.object.bake need (engine, selection, an active Image Texture
node, UVs), what errors come when something is missing, and what do DIFFUSE (colour only), NORMAL, AO and COMBINED bakes
write into the image?"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import time
import bpy
import numpy as np
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
bpy.ops.mesh.primitive_plane_add(size=2)
plane = bpy.context.object
m = bpy.data.materials.new("bake")
m.use_nodes = True
nt = m.node_tree
b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
b.inputs["Base Color"].default_value = (0.8, 0.2, 0.1, 1)
plane.data.materials.append(m)
# a cube floating above the plane, for AO and shadows
bpy.ops.mesh.primitive_cube_add(size=0.6, location=(0, 0, 0.5))
blocker = bpy.context.object
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3
scene.collection.objects.link(sun)
w = bpy.data.worlds.new("w")
w.color = (0.2, 0.2, 0.2)
scene.world = w
scene.render.engine = "CYCLES"
dev = exp.metal()
scene.cycles.samples = 32
E.fact("bake settings: bake type is scene.cycles.bake_type (the op's type= overrides it); margin and other options are on "
       "scene.render.bake; defaults", cycles_bake_type=scene.cycles.bake_type, margin=scene.render.bake.margin,
       margin_type=scene.render.bake.margin_type, use_clear=scene.render.bake.use_clear, target=scene.render.bake.target,
       normal_space=scene.render.bake.normal_space, device=dev)


def select_only(ob):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def bake(kind, **kw):
    select_only(plane)
    try:
        t = time.time()
        r = bpy.ops.object.bake(type=kind, **kw)
        return f"{r} in {time.time() - t:.2f} s"
    except RuntimeError as e:
        return str(e).strip()


errors = {"no image node": bake("DIFFUSE")}
img = bpy.data.images.new("baked", 128, 128, float_buffer=True)
node = nt.nodes.new("ShaderNodeTexImage")
node.image = img
nt.nodes.active = node  # the bake target: the ACTIVE image node of each material
uv_backup = plane.data.uv_layers[0].name
plane.data.uv_layers.remove(plane.data.uv_layers[0])
errors["no UV map"] = bake("DIFFUSE")
plane.data.uv_layers.new(name=uv_backup)
scene.render.engine = "BLENDER_EEVEE_NEXT"
try:
    bpy.ops.object.bake(type="DIFFUSE")
    errors["engine EEVEE"] = "ran"
except (RuntimeError, TypeError) as e:
    errors["engine EEVEE"] = str(e).strip()[:200]
scene.render.engine = "CYCLES"
E.fact("bpy.ops.object.bake raises RuntimeError when the mesh has no UV map ('No active UV layer found') or the engine is "
       "not Cycles ('Current render engine does not support baking'); with no Image Texture node in the material it does "
       "not raise: it returns {'CANCELLED'} and bakes nothing, so check the return value", errors=errors)


def pixels():
    return np.array(img.pixels[:], np.float32).reshape(128, 128, 4)


res = {}
res["DIFFUSE color only"] = bake("DIFFUSE", pass_filter={"COLOR"}, margin=4)
px = pixels()
diffuse_colour = [round(float(v), 3) for v in px[100, 100, :3]]
res["DIFFUSE direct+indirect+color"] = bake("DIFFUSE", pass_filter={"DIRECT", "INDIRECT", "COLOR"})
lit = pixels()
res["NORMAL tangent"] = bake("NORMAL")
nrm = pixels()
res["AO"] = bake("AO")
ao = pixels()
res["COMBINED"] = bake("COMBINED")
comb = pixels()
b.inputs["Specular IOR Level"].default_value = 0.0
bake("DIFFUSE", pass_filter={"COLOR"}, margin=4)
no_spec = [round(float(v), 3) for v in pixels()[100, 100, :3]]
b.inputs["Specular IOR Level"].default_value = 0.5
E.fact("DIFFUSE with pass_filter={'COLOR'} writes the diffuse albedo alone, linear, in a float image: Base Color "
       "(0.8, 0.2, 0.1) bakes as about 0.96 of itself, because the Principled specular layer takes its share; with "
       "Specular IOR Level 0 it bakes as the Base Color itself",
       result=res["DIFFUSE color only"], texel=diffuse_colour, texel_specular_level_0=no_spec)
E.fact("DIFFUSE with DIRECT+INDIRECT+COLOR bakes lighting in: the texel under the cube is darker than an open one",
       open_texel=[round(float(v), 3) for v in lit[120, 120, :3]], under_cube=[round(float(v), 3) for v in lit[64, 64, :3]])
E.fact("NORMAL (tangent space, the default) of a flat face is (0.5, 0.5, 1.0)", texel=[round(float(v), 3) for v in nrm[100, 100, :3]])
E.fact("AO is 1 on open floor and darker next to the cube", open=round(float(ao[120, 120, 0]), 3),
       near_cube=round(float(ao[64, 80, 0]), 3))
E.fact("bake times on Metal at 128 px, 32 samples", times=res)
E.fact("a baked image lives only in memory (is_dirty True) until it is saved: set filepath_raw and file_format, then "
       "image.save()", is_dirty=img.is_dirty)
img.filepath_raw = E.out("baked.png")
img.file_format = "PNG"
img.save()
E.fact("image.save() wrote the bake to disk", exists=os.path.exists(E.out("baked.png")), bytes=os.path.getsize(E.out("baked.png")))
E.save(times=res)
