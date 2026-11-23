"""A named attribute written by geometry nodes (Store Named Attribute) read in a material by the Attribute node: does the colour reach the render?"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import numpy as np
import bpy
import exp
E = exp.Experiment(__file__)

# GN: store a constant red colour on the POINT domain under the name "tint"
ng = bpy.data.node_groups.new("Tint", "GeometryNodeTree")
ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
N, L = ng.nodes, ng.links
gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
st = N.new("GeometryNodeStoreNamedAttribute")
st.data_type = "FLOAT_COLOR"; st.domain = "POINT"
st.inputs["Name"].default_value = "tint"
val = next(s for s in st.inputs if s.name == "Value" and s.enabled)
val.default_value = (1.0, 0.2, 0.0, 1.0)
L.new(gi.outputs[0], st.inputs["Geometry"]); L.new(st.outputs["Geometry"], go.inputs[0])
E.fact("Store Named Attribute's Value socket changes type with data_type: the enabled Value input for FLOAT_COLOR",
       value_inputs=[(s.identifier, s.type, s.enabled) for s in st.inputs if s.name == "Value"])

bpy.ops.mesh.primitive_plane_add(size=2)
ob = bpy.context.object
m = ob.modifiers.new("GN", "NODES"); m.node_group = ng
dg = bpy.context.evaluated_depsgraph_get()
ev = ob.evaluated_get(dg).data
at = ev.attributes.get("tint")
E.fact("the evaluated mesh has the stored attribute; the original mesh does not",
       evaluated=(at.domain, at.data_type) if at else None, original="tint" in ob.data.attributes,
       value=list(at.data[0].color) if at else None)

# material: emission from Attribute node
mat = bpy.data.materials.new("AttrMat"); mat.use_nodes = True
nt = mat.node_tree; nt.nodes.clear()
an = nt.nodes.new("ShaderNodeAttribute"); an.attribute_name = "tint"; an.attribute_type = "GEOMETRY"
em = nt.nodes.new("ShaderNodeEmission")
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(an.outputs["Color"], em.inputs["Color"]); nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
ob.data.materials.append(mat)
E.fact("ShaderNodeAttribute.attribute_type options", types=[e.identifier for e in an.bl_rna.properties["attribute_type"].enum_items])

# tiny render looking straight down
sc = bpy.context.scene
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
cam.location = (0, 0, 3); sc.camera = cam
sc.render.engine = "CYCLES"; sc.cycles.samples = 4; sc.cycles.device = "CPU"
sc.render.resolution_x = sc.render.resolution_y = 32; sc.render.resolution_percentage = 100
sc.view_settings.view_transform = "Standard"
sc.render.image_settings.file_format = "PNG"
path = E.out("render.png"); sc.render.filepath = path
bpy.ops.render.render(write_still=True)
img = bpy.data.images.load(path)
px = np.array(img.pixels[:]).reshape(32, 32, 4)
centre = px[16, 16, :3]
E.fact("the rendered centre pixel shows the colour from geometry nodes (red 1.0, green 0.2 linear -> about 0.48 sRGB, blue 0)",
       centre_rgb=[round(float(x), 3) for x in centre])
# a typo in the name gives black, silently
an.attribute_name = "tnit"
bpy.ops.render.render(write_still=True)
img.reload()
px = np.array(img.pixels[:]).reshape(32, 32, 4)
E.fact("a misspelt attribute name renders black without any error", centre_rgb=[round(float(x), 3) for x in px[16, 16, :3]])
E.save()
