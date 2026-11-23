# Wrong solution, task 3: Principled BSDF inputs set by their Blender 3.x names, skipping names that are missing.
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

values = {
    "Base Color": (0.05, 0.2, 0.6, 1.0),
    "Metallic": 0.6,
    "Roughness": 0.4,
    "Clearcoat": 1.0,
    "Clearcoat Roughness": 0.08,
    "Sheen": 0.3,
    "Transmission": 0.25,
    "Emission": (1.0, 0.5, 0.1, 1.0),
    "Emission Strength": 0.5,
    "Alpha": 0.9,
}
for name, v in values.items():
    if name in bsdf.inputs:
        bsdf.inputs[name].default_value = v
    else:
        print("skipping missing input", name)

if not out_node.inputs["Surface"].is_linked:
    nt.links.new(bsdf.outputs["BSDF"], out_node.inputs["Surface"])

mat.blend_method = 'BLEND'
mat.show_transparent_back = False

ob.data.materials.clear()
ob.data.materials.append(mat)

bpy.ops.wm.save_as_mainfile(filepath=out)
