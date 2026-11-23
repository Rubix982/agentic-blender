# Reference solution, task 3: a coated, slightly see-through car-paint material on a sphere.
import bpy, sys

out = sys.argv[sys.argv.index("--") + 1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(0, 0, 0))
ob = bpy.context.active_object
bpy.ops.object.shade_smooth()

mat = bpy.data.materials.new("CarPaint")
mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
out_node = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')

# Principled BSDF v2 (Blender 4.0+) socket names.
values = {
    "Base Color": (0.05, 0.2, 0.6, 1.0),
    "Metallic": 0.6,
    "Roughness": 0.4,
    "Coat Weight": 1.0,
    "Coat Roughness": 0.03,
    "Sheen Weight": 0.3,
    "Transmission Weight": 0.25,
    "Emission Color": (1.0, 0.5, 0.1, 1.0),
    "Emission Strength": 0.5,
    "Alpha": 0.9,
}
for name, v in values.items():
    bsdf.inputs[name].default_value = v

if not out_node.inputs["Surface"].is_linked:
    nt.links.new(bsdf.outputs["BSDF"], out_node.inputs["Surface"])

# EEVEE (4.2+): blended render method, back faces hidden.
mat.surface_render_method = 'BLENDED'
mat.use_transparency_overlap = False

ob.data.materials.clear()
ob.data.materials.append(mat)

bpy.ops.wm.save_as_mainfile(filepath=out)
