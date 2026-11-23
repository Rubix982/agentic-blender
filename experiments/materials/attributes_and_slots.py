"""How do mesh attributes reach a shader in 4.5 (colour attributes, generic float attributes, object custom properties),
and how are materials assigned per face? Four quads, one per image quadrant, rendered as emission (Raw view)."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import numpy as np
import OpenImageIO as oiio
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
# a 2x2 grid of quads: face 0 bottom-left, 1 bottom-right, 2 top-left, 3 top-right
verts = [(x, y, 0) for y in (-1, 0, 1) for x in (-1, 0, 1)]
faces = [(0, 1, 4, 3), (1, 2, 5, 4), (3, 4, 7, 6), (4, 5, 8, 7)]
me = bpy.data.meshes.new("quads")
me.from_pydata(verts, [], faces)
ob = bpy.data.objects.new("quads", me)
scene.collection.objects.link(ob)
E.fact("mesh.vertex_colors (the pre-3.2 API) still exists in 4.5 next to mesh.color_attributes, the current API for colour "
       "attributes (types FLOAT_COLOR, BYTE_COLOR; domains POINT, CORNER)",
       has_vertex_colors=hasattr(me, "vertex_colors"), has_color_attributes=hasattr(me, "color_attributes"),
       color_attribute_types=["FLOAT_COLOR", "BYTE_COLOR"], domains=["POINT", "CORNER"])
# a per-face colour (CORNER domain, every corner of a face the same) as BYTE_COLOR
ca = me.color_attributes.new("paint", "BYTE_COLOR", "CORNER")
face_col = [(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1), (0.5, 0.5, 0.5, 1)]
for poly in me.polygons:
    for li in poly.loop_indices:
        ca.data[li].color = face_col[poly.index]
E.fact("ByteColorAttribute values: .color reads and writes scene-linear, .color_srgb the stored sRGB-encoded value",
       color=[round(v, 4) for v in ca.data[me.polygons[3].loop_indices[0]].color],
       color_srgb=[round(v, 4) for v in ca.data[me.polygons[3].loop_indices[0]].color_srgb])
# a generic float attribute on points
fa = me.attributes.new("height", "FLOAT", "POINT")
for i, v in enumerate(me.vertices):
    fa.data[i].value = 0.25
ob["tint"] = (0.1, 0.2, 0.3)  # custom property read by an OBJECT attribute

m = bpy.data.materials.new("attr")
m.use_nodes = True
nt = m.node_tree
nt.nodes.remove(next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"))
em = nt.nodes.new("ShaderNodeEmission")
nt.links.new(em.outputs[0], next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL").inputs["Surface"])
me.materials.append(m)
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 2
cam.location = (0, 0, 2)
scene.collection.objects.link(cam)
scene.camera = cam
scene.world = None
scene.render.engine = "CYCLES"
scene.cycles.samples = 1
scene.render.resolution_x = scene.render.resolution_y = 32
scene.view_settings.view_transform = "Raw"
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"


def quadrants(engine="CYCLES"):
    scene.render.engine = engine
    scene.render.filepath = E.out("tmp.exr")
    bpy.ops.render.render(write_still=True)
    px = oiio.ImageBuf(scene.render.filepath).get_pixels(oiio.FLOAT)
    os.remove(scene.render.filepath)
    r = lambda y, x: [round(float(v), 3) for v in px[y, x, :3]]
    return dict(f0_bl=r(24, 8), f1_br=r(24, 24), f2_tl=r(8, 8), f3_tr=r(8, 24))


vc = nt.nodes.new("ShaderNodeVertexColor")  # UI name "Color Attribute"
vc.layer_name = "paint"
nt.links.new(vc.outputs["Color"], em.inputs["Color"])
via_color_node = {e: quadrants(e) for e in ("CYCLES", "BLENDER_EEVEE_NEXT")}
E.fact("the Color Attribute node (ShaderNodeVertexColor, layer_name) delivers the colour attribute linear, in both engines",
       **via_color_node)
at = nt.nodes.new("ShaderNodeAttribute")
at.attribute_name = "height"
nt.links.new(at.outputs["Fac"], em.inputs["Color"])
E.fact("an Attribute node (attribute_type GEOMETRY, the default) reads a generic float attribute by name through Fac",
       attribute_type_items=[i.identifier for i in type(at).bl_rna.properties["attribute_type"].enum_items],
       result=quadrants())
at.attribute_type = "OBJECT"
at.attribute_name = "tint"
nt.links.new(at.outputs["Color"], em.inputs["Color"])
E.fact("an Attribute node with attribute_type OBJECT reads an object custom property (obj['tint'])", result=quadrants())
at.attribute_name = "no_such_attribute"
at.attribute_type = "GEOMETRY"
E.fact("a missing attribute name renders as black (0), with no error", result=quadrants())

# material slots: two materials, faces 1 and 3 use slot 1
m2 = bpy.data.materials.new("second")
m2.use_nodes = True
n2 = m2.node_tree
n2.nodes.remove(next(n for n in n2.nodes if n.type == "BSDF_PRINCIPLED"))
e2 = n2.nodes.new("ShaderNodeEmission")
e2.inputs["Color"].default_value = (1, 1, 0, 1)
n2.links.new(e2.outputs[0], next(n for n in n2.nodes if n.type == "OUTPUT_MATERIAL").inputs["Surface"])
me.materials.append(m2)
for p in me.polygons:
    p.material_index = 1 if p.index in (1, 3) else 0
nt.links.new(vc.outputs["Color"], em.inputs["Color"])
E.fact("polygon.material_index picks the slot per face (mesh.materials.append adds a slot on the mesh data); faces 1 and 3 "
       "on slot 1 render yellow", result=quadrants(), slots=[s.material.name for s in ob.material_slots],
       link=ob.material_slots[0].link)
E.save()
