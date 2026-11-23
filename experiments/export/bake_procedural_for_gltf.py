"""The full path from a procedural material to a glTF that keeps its look: bake the procedural Base Color (and roughness)
to images with Cycles, wire the images into the Principled BSDF in place of the procedural nodes, export GLB, and check
that the file now carries the textures."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import json
import struct
import bpy
import numpy as np
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=32, ring_count=16)
ob = bpy.context.object
m = bpy.data.materials.new("procedural")
m.use_nodes = True
nt = m.node_tree
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
noise = nt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 6
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (0.05, 0.1, 0.6, 1)
ramp.color_ramp.elements[1].color = (0.9, 0.7, 0.2, 1)
nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(noise.outputs["Fac"], bsdf.inputs["Roughness"])
ob.data.materials.append(m)
scene.render.engine = "CYCLES"
exp.metal()
scene.cycles.samples = 1  # a colour-only bake needs no light sampling
bpy.ops.object.select_all(action="DESELECT")
ob.select_set(True)
bpy.context.view_layer.objects.active = ob


def bake_to(name, kind, colorspace, **kw):
    img = bpy.data.images.new(name, 256, 256)
    img.colorspace_settings.name = colorspace
    node = nt.nodes.new("ShaderNodeTexImage")
    node.image = img
    nt.nodes.active = node
    r = bpy.ops.object.bake(type=kind, margin=8, **kw)
    img.filepath_raw = E.out(f"{name}.png")
    img.file_format = "PNG"
    img.save()
    return node, r


col_node, r1 = bake_to("basecolor", "DIFFUSE", "sRGB", pass_filter={"COLOR"})
rough_node, r2 = bake_to("roughness", "ROUGHNESS", "Non-Color")
# swap the procedural links for the baked images
nt.links.new(col_node.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(rough_node.outputs["Color"], bsdf.inputs["Roughness"])
for n in (noise, ramp):
    nt.nodes.remove(n)
px = np.array(col_node.image.pixels[:], np.float32).reshape(256, 256, 4)
E.fact("DIFFUSE (pass_filter COLOR) and ROUGHNESS bakes of a procedural material into 256 px byte images",
       results=[str(r1), str(r2)], basecolor_std=round(float(px[..., :3].std()), 3),
       basecolor_mean=[round(float(v), 3) for v in px[..., :3].reshape(-1, 3).mean(axis=0)])

path = E.out("baked.glb")
bpy.ops.export_scene.gltf(filepath=path, export_format="GLB")
with open(path, "rb") as f:
    data = f.read()
g = json.loads(data[20:20 + struct.unpack_from("<I", data, 12)[0]])
mat = g["materials"][0]
E.fact("after baking and rewiring, the GLB carries a baseColorTexture and a metallicRoughnessTexture, each an embedded "
       "PNG made from the baked images (before baking, the procedural material exported neither)",
       material=mat, images=[(i.get("name"), i.get("mimeType")) for i in g.get("images", [])], glb_bytes=len(data))
for f in ("basecolor.png", "roughness.png", "baked.glb"):
    if f != "basecolor.png":
        os.remove(E.out(f))
E.fact("the baked base colour is kept as the example image (256 px)", file="bake_procedural_for_gltf-basecolor.png")
E.save(material=mat)
