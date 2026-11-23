"""What of a Principled BSDF material survives glTF 2.0 export in 4.5, what is dropped (procedural textures), which
KHR extensions appear, and what comes back on import? Also: are modifiers applied by default, and which axis is up?"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import json
import struct
import bpy
import numpy as np
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene


def principled(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def read_glb(path):
    with open(path, "rb") as f:
        data = f.read()
    n = struct.unpack_from("<I", data, 12)[0]
    return json.loads(data[20:20 + n])


# 1) plain factors: base colour, metallic, roughness, emission, alpha, plus the 4.x layers (coat, sheen, transmission, specular)
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
a = bpy.context.object
a.name = "factors"
m, b = principled("factors")
b.inputs["Base Color"].default_value = (0.8, 0.2, 0.1, 1)
b.inputs["Metallic"].default_value = 0.3
b.inputs["Roughness"].default_value = 0.6
b.inputs["Emission Color"].default_value = (0, 1, 0, 1)
b.inputs["Emission Strength"].default_value = 2.0
b.inputs["Alpha"].default_value = 0.5
b.inputs["Coat Weight"].default_value = 0.7
b.inputs["Sheen Weight"].default_value = 0.4
b.inputs["Transmission Weight"].default_value = 0.2
b.inputs["IOR"].default_value = 1.7
b.inputs["Specular IOR Level"].default_value = 0.8
a.data.materials.append(m)
# 2) an image texture into Base Color (UV mapped) and a normal map
bpy.ops.mesh.primitive_cube_add(location=(3, 0, 0))
c = bpy.context.object
c.name = "imagetex"
m2, b2 = principled("imagetex")
img = bpy.data.images.new("checker", 64, 64)
img.generated_type = "COLOR_GRID"
tex = m2.node_tree.nodes.new("ShaderNodeTexImage")
tex.image = img
m2.node_tree.links.new(tex.outputs["Color"], b2.inputs["Base Color"])
nimg = bpy.data.images.new("flatnormal", 32, 32)
nimg.generated_color = (0.5, 0.5, 1, 1)
nimg.colorspace_settings.name = "Non-Color"
ntex = m2.node_tree.nodes.new("ShaderNodeTexImage")
ntex.image = nimg
nmap = m2.node_tree.nodes.new("ShaderNodeNormalMap")
m2.node_tree.links.new(ntex.outputs["Color"], nmap.inputs["Color"])
m2.node_tree.links.new(nmap.outputs["Normal"], b2.inputs["Normal"])
c.data.materials.append(m2)
# 3) a procedural Noise into Base Color
bpy.ops.mesh.primitive_cube_add(location=(6, 0, 0))
d = bpy.context.object
d.name = "procedural"
m3, b3 = principled("procedural")
noise = m3.node_tree.nodes.new("ShaderNodeTexNoise")
m3.node_tree.links.new(noise.outputs["Color"], b3.inputs["Base Color"])
d.data.materials.append(m3)
# 4) a subdivision modifier, to test export_apply
bpy.ops.mesh.primitive_cube_add(location=(9, 0, 3))
s = bpy.context.object
s.name = "subsurf"
s.modifiers.new("sub", "SUBSURF").levels = 2

items = None
try:
    bpy.ops.export_scene.gltf(filepath=E.out("x.glb"), export_format="__nope__")
except TypeError as e:
    items = str(e)[str(e).find("("):][:120]
E.fact("export_scene.gltf's export_format is a dynamic enum; valid values", type_error=items)
path = E.out("scene.glb")
bpy.ops.export_scene.gltf(filepath=path, export_format="GLB")
g = read_glb(path)
mats = {mm["name"]: mm for mm in g["materials"]}
for k, v in mats.items():
    print(k, json.dumps(v))
E.fact("glTF export (GLB) of a Principled BSDF keeps base colour (linear factor), metallic, roughness, emission (colour as "
       "emissiveFactor, strength above 1 as KHR_materials_emissive_strength), alpha < 1 (alphaMode BLEND, alpha in the "
       "baseColorFactor) and coat, transmission and IOR as KHR extensions; Specular IOR Level 0.8 becomes specularColorFactor "
       "1.6 (2x); Sheen Weight 0.4 is lost (sheenColorFactor written as the tint, 1.0)",
       factors=mats["factors"], extensionsUsed=g.get("extensionsUsed"))
E.fact("an Image Texture into Base Color exports as baseColorTexture with the image embedded; a Normal Map node exports as "
       "normalTexture", imagetex=mats["imagetex"], images=[(i.get("name"), i.get("mimeType")) for i in g.get("images", [])])
E.fact("a procedural texture (Noise) into Base Color is dropped silently: the material exports with no baseColorTexture and "
       "no baseColorFactor, which glTF reads as white (1, 1, 1); bake it to an image first", procedural=mats["procedural"])
counts = {mesh["name"]: [g["accessors"][p["attributes"]["POSITION"]]["count"] for p in mesh["primitives"]] for mesh in g["meshes"]}
bpy.ops.export_scene.gltf(filepath=E.out("applied.glb"), export_format="GLB", export_apply=True)
g2 = read_glb(E.out("applied.glb"))
counts2 = {mesh["name"]: [g2["accessors"][p["attributes"]["POSITION"]]["count"] for p in mesh["primitives"]] for mesh in g2["meshes"]}
E.fact("export_apply defaults to False: modifiers are NOT applied unless export_apply=True (a cube with Subdivision level 2 "
       "exports 24 vertices by default, 384 when applied). glTF mesh names are the mesh datablock names (Cube.003), and an "
       "applied mesh is renamed 'Mesh'",
       default_vertices=counts.get("Cube.003"), applied_vertices=counts2.get("Mesh"), all_default=counts, all_applied=counts2)
node = next(n for n in g["nodes"] if n["name"] == "subsurf")
E.fact("export_yup (default True) converts Blender's +Z up to glTF's +Y up: an object at Blender (9, 0, 3) is at glTF "
       "(9, 3, 0)", gltf_translation=node.get("translation"))

# import back
exp.empty()
bpy.ops.import_scene.gltf(filepath=path)
back = {}
for o in bpy.data.objects:
    if o.type != "MESH" or not o.material_slots:
        continue
    mm = o.material_slots[0].material
    bb = next((n for n in mm.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    back[o.name] = dict(material=mm.name, node_types=sorted({n.type for n in mm.node_tree.nodes}),
                        base_color=[round(v, 3) for v in bb.inputs["Base Color"].default_value] if bb else None,
                        coat=round(bb.inputs["Coat Weight"].default_value, 3) if bb else None,
                        sheen=round(bb.inputs["Sheen Weight"].default_value, 3) if bb else None,
                        transmission=round(bb.inputs["Transmission Weight"].default_value, 3) if bb else None,
                        emission_strength=round(bb.inputs["Emission Strength"].default_value, 3) if bb else None,
                        surface_render_method=mm.surface_render_method)
for k, v in back.items():
    print(k, v)
E.fact("import_scene.gltf rebuilds a Principled BSDF with the exported factors (coat 0.7, transmission 0.2, emission 2, "
       "alpha -> surface_render_method BLENDED) and image textures; sheen comes back 1.0 (was 0.4); the procedural material "
       "comes back white with no texture", imported=back)
for f in ("scene.glb", "applied.glb"):
    os.remove(E.out(f))
E.save(materials=mats)
