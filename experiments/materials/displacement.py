"""Does material displacement move geometry in 4.5, and where is the setting now? A 2 m grid (200x200) gets a wave
height through a Displacement node; an orthographic side view measures how high its silhouette rises, for each
displacement_method, in Cycles and EEVEE. Also: the Bump and Normal Map node sockets."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import math
import bpy
import numpy as np
import OpenImageIO as oiio
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
m = bpy.data.materials.new("disp")
E.fact("displacement_method lives on the Material in 4.5 (material.displacement_method), not on material.cycles",
       on_material=hasattr(m, "displacement_method"), on_cycles=hasattr(m.cycles, "displacement_method"),
       default=m.displacement_method,
       items=[i.identifier for i in type(m).bl_rna.properties["displacement_method"].enum_items])
m.use_nodes = True
nt = m.node_tree
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
wave = nt.nodes.new("ShaderNodeTexWave")
wave.inputs["Scale"].default_value = 1.5
wave.bands_direction = "Y"  # ridges across the view direction; ridges along it would be edge-on sheets that rays slip under
disp = nt.nodes.new("ShaderNodeDisplacement")
disp.inputs["Midlevel"].default_value = 0.0
disp.inputs["Scale"].default_value = 0.2  # height 0..1 -> 0..0.2 m along the normal
nt.links.new(wave.outputs["Fac"], disp.inputs["Height"])
nt.links.new(disp.outputs["Displacement"], out.inputs["Displacement"])
E.fact("Displacement node sockets and space; the Material Output's Displacement input takes its output",
       inputs=[s.name for s in disp.inputs], space=disp.space, defaults=dict(midlevel_new=0.5, scale_new=1.0),
       output_inputs=[s.name for s in out.inputs])
bump = nt.nodes.new("ShaderNodeBump")
nmap = nt.nodes.new("ShaderNodeNormalMap")
E.fact("Bump and Normal Map nodes in 4.5: their inputs and defaults; Normal Map's space defaults to TANGENT and needs a UV map",
       bump_inputs={s.name: (round(s.default_value, 3) if isinstance(s.default_value, float) else None) for s in bump.inputs if s.enabled},
       bump_invert=bump.invert,
       normal_map_inputs=[s.name for s in nmap.inputs], normal_map_space=nmap.space,
       normal_map_space_items=[i.identifier for i in type(nmap).bl_rna.properties["space"].enum_items])
nt.nodes.remove(bump)
nt.nodes.remove(nmap)

bpy.ops.mesh.primitive_grid_add(x_subdivisions=200, y_subdivisions=200, size=2)
grid = bpy.context.object
grid.data.materials.append(m)
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 2.4
cam.location = (0, -5, 0.3)
cam.rotation_euler = (math.radians(90), 0, 0)
scene.collection.objects.link(cam)
scene.camera = cam
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
scene.collection.objects.link(sun)
scene.render.film_transparent = True
R = 240
scene.render.resolution_x, scene.render.resolution_y = R, R
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_mode = "RGBA"
scene.cycles.samples = 4
scene.cycles.use_denoising = False
scene.eevee.taa_render_samples = 4
exp.metal()


def rise_mm(engine):
    scene.render.engine = engine
    scene.render.filepath = E.out("tmp.exr")
    bpy.ops.render.render(write_still=True)
    a = oiio.ImageBuf(scene.render.filepath).get_pixels(oiio.FLOAT)[..., 3]
    os.remove(scene.render.filepath)
    rows = np.nonzero(a.max(axis=1) > 0.5)[0]
    if not len(rows):
        return 0  # nothing above the flat grid: a zero-thickness sheet seen edge-on covers no pixels
    m_per_px = cam.data.ortho_scale / R
    top = (R / 2 - rows.min()) * m_per_px + cam.location.z  # world z of the highest silhouette pixel
    return round(top * 1000)


rows = []
for method in ("BUMP", "DISPLACEMENT", "BOTH"):
    m.displacement_method = method
    for eng in ("CYCLES", "BLENDER_EEVEE_NEXT"):
        rows.append(dict(method=method, engine=eng, silhouette_top_mm=rise_mm(eng)))
for r in rows:
    print(r)
E.fact("with displacement_method BUMP (the default) the grid's silhouette stays flat (shading only); DISPLACEMENT and BOTH "
       "move the vertices up to the 0.2 m the node asks for, in Cycles and in EEVEE. Displacement moves existing vertices: "
       "the mesh must be dense (here 200x200)",
       rows=rows)
E.save(rows=rows)
