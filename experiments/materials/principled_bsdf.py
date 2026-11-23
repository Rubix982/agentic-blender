"""The Principled BSDF in 4.5: every input with its name and identifier, what the 3.x names and indices now do, and the
emission default that makes a glowing material dark."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import OpenImageIO as oiio
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
m = bpy.data.materials.new("probe")
E.fact("bpy.data.materials.new gives use_nodes False and no node tree in 4.5; setting use_nodes = True creates a Principled "
       "BSDF wired to a Material Output",
       use_nodes=m.use_nodes, node_tree_before=m.node_tree is not None)
m.use_nodes = True
nodes = m.node_tree.nodes
b = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
E.fact("the default node is found by type 'BSDF_PRINCIPLED' (bl_idname ShaderNodeBsdfPrincipled); its name/label is "
       "'Principled BSDF' in English but node names follow the UI language, so look up by type",
       nodes=[(n.name, n.bl_idname, n.type) for n in nodes],
       links=[(l.from_socket.identifier, l.to_node.type, l.to_socket.identifier) for l in m.node_tree.links])
rows = [dict(i=i, name=s.name, identifier=s.identifier, type=s.bl_idname.replace("NodeSocket", ""),
             default=(list(s.default_value) if hasattr(s.default_value, "__len__") else round(s.default_value, 4))
             if hasattr(s, "default_value") else None, hidden=not s.enabled or s.hide)
        for i, s in enumerate(b.inputs)]
for r in rows:
    print(r)
E.fact(f"the Principled BSDF has {len(rows)} inputs in 4.5, two of them hidden (Weight, Subsurface IOR); every input's name "
       f"{'equals' if all(r['name'] == r['identifier'] for r in rows) else 'does not always equal'} its identifier",
       n=len(rows), inputs=rows,
       name_ne_identifier=[(r["name"], r["identifier"]) for r in rows if r["name"] != r["identifier"]])
fresh = nodes.new("ShaderNodeBsdfPrincipled")
E.fact("node properties of a new Principled BSDF: MULTI_GGX and RANDOM_WALK both in a use_nodes material and from nodes.new",
       use_nodes_distribution=b.distribution, use_nodes_subsurface_method=b.subsurface_method,
       nodes_new_distribution=fresh.distribution, nodes_new_subsurface_method=fresh.subsurface_method)
nodes.remove(fresh)

old = ["Subsurface", "Subsurface Color", "Specular", "Specular Tint", "Sheen", "Sheen Tint", "Clearcoat",
       "Clearcoat Roughness", "Clearcoat Normal", "Transmission", "Transmission Roughness", "Emission",
       "Emission Strength", "Base Color"]
res = {}
for k in old:
    try:
        s = b.inputs[k]
        res[k] = f"exists ({s.bl_idname.replace('NodeSocket', '')})"
    except KeyError:
        res[k] = "KeyError"
E.fact("3.x input names that raise KeyError in 4.5: Subsurface, Subsurface Color, Specular, Sheen, Clearcoat*, "
       "Transmission, Transmission Roughness, Emission. 'Specular Tint' and 'Sheen Tint' still exist but are now colours",
       results=res)
v3 = {6: "Metallic", 7: "Specular", 9: "Roughness", 17: "Transmission", 19: "Emission", 20: "Emission Strength", 21: "Alpha"}
E.fact("3.x input indices now point at other sockets (inputs[6] was Metallic, inputs[9] Roughness, inputs[21] Alpha)",
       index_then_now={i: (was, b.inputs[i].name) for i, was in v3.items()})

# emission: Emission Strength defaults to 0, so setting only the colour gives no light
bpy.ops.mesh.primitive_plane_add(size=4)
plane = bpy.context.object
plane.data.materials.append(m)
b.inputs["Base Color"].default_value = (0, 0, 0, 1)
b.inputs["Emission Color"].default_value = (1, 0.2, 0.05, 1)
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.location = (0, 0, 3)
scene.collection.objects.link(cam)
scene.camera = cam
scene.world = None
scene.render.engine = "CYCLES"
scene.cycles.samples = 4
scene.render.resolution_x = scene.render.resolution_y = 16
scene.render.image_settings.file_format = "OPEN_EXR"


def centre():
    scene.render.filepath = E.out("tmp.exr")
    bpy.ops.render.render(write_still=True)
    v = oiio.ImageBuf(scene.render.filepath).get_pixels(oiio.FLOAT)[8, 8, :3]
    os.remove(scene.render.filepath)
    return [round(float(x), 3) for x in v]


only_colour = centre()
b.inputs["Emission Strength"].default_value = 5.0
with_strength = centre()
E.fact("Emission Strength defaults to 0.0 in 4.5, so a material with only Emission Color set does not glow; "
       "the emitted radiance is Emission Color x Emission Strength",
       emission_color_only=only_colour, with_strength_5=with_strength)
E.save(inputs=rows)
