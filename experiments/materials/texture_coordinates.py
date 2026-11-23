"""What do the Texture Coordinate outputs (Generated, Object, UV) give on an object whose scale is not applied, and what
does a Mapping node's Scale do? Each coordinate is rendered as emission colour (Raw view) and read at the plane's corners."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import OpenImageIO as oiio
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
bpy.ops.mesh.primitive_plane_add(size=2)  # local -1..1
plane = bpy.context.object
plane.scale = (3, 1.5, 1)  # not applied
plane.location = (10, 0, 0)  # away from the origin
m = bpy.data.materials.new("coords")
m.use_nodes = True
nt = m.node_tree
nt.nodes.remove(next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"))
em = nt.nodes.new("ShaderNodeEmission")
nt.links.new(em.outputs[0], next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL").inputs["Surface"])
tc = nt.nodes.new("ShaderNodeTexCoord")
mp = nt.nodes.new("ShaderNodeMapping")
plane.data.materials.append(m)
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 6.0
cam.location = (10, 0, 5)
scene.collection.objects.link(cam)
scene.camera = cam
scene.world = None
scene.render.engine = "CYCLES"
scene.cycles.samples = 1
scene.cycles.use_denoising = False
scene.render.filter_size = 0.01  # no pixel filter blur: corners read exact values
scene.render.resolution_x, scene.render.resolution_y = 120, 60
scene.view_settings.view_transform = "Raw"
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"
E.fact("Texture Coordinate outputs and Mapping node types in 4.5",
       outputs=[s.name for s in tc.outputs], mapping_types=[i.identifier for i in type(mp).bl_rna.properties["vector_type"].enum_items],
       mapping_inputs=[s.name for s in mp.inputs if s.enabled], mapping_default=mp.vector_type)


def corners(out_socket):
    nt.links.new(out_socket, em.inputs["Color"])
    scene.render.filepath = E.out("tmp.exr")
    bpy.ops.render.render(write_still=True)
    px = oiio.ImageBuf(scene.render.filepath).get_pixels(oiio.FLOAT)
    os.remove(scene.render.filepath)
    # the plane spans 6 x 3 m = the whole 120 x 60 frame; sample just inside the bottom-left and top-right corners
    bl, tr = px[58, 1, :3], px[1, 118, :3]
    return dict(bottom_left=[round(float(v), 2) for v in bl], top_right=[round(float(v), 2) for v in tr])


res = {k: corners(tc.outputs[k]) for k in ("Generated", "Object", "UV")}
nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
mp.inputs["Scale"].default_value = (2, 2, 1)
res["UV through Mapping (POINT, Scale 2)"] = corners(mp.outputs["Vector"])
mp.vector_type = "TEXTURE"
res["UV through Mapping (TEXTURE, Scale 2)"] = corners(mp.outputs["Vector"])
for k, v in res.items():
    print(k, v)
E.fact("on a 2 m plane scaled (3, 1.5, 1) without applying, away from the origin: Generated runs 0..1 over the bounding box, "
       "Object gives local coordinates -1..1 (object scale and location ignored), UV runs 0..1; so a texture on Object or "
       "Generated stretches with an unapplied scale",
       **{k.split(" ")[0] if " " not in k else k: v for k, v in res.items()})
E.fact("Mapping type POINT multiplies the coordinate by Scale (texture looks smaller, repeats more); type TEXTURE divides "
       "(the inverse transform: texture looks bigger)",
       point=res["UV through Mapping (POINT, Scale 2)"], texture=res["UV through Mapping (TEXTURE, Scale 2)"])
E.save(results=res)
