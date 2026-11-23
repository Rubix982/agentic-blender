# Wrong solution, task 6: keys and cycles everything but leaves the default Bezier interpolation.
import bpy, sys, math

out = sys.argv[sys.argv.index("--") + 1]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 24
sc.render.fps_base = 1.0
sc.frame_start = 1
sc.frame_end = 96

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
ob = bpy.context.active_object
ob.name = "Hopper"

mat = bpy.data.materials.new("Glow")
mat.use_nodes = True
bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
bsdf.inputs["Emission Color"].default_value = (1.0, 0.3, 0.0, 1.0)
ob.data.materials.append(mat)

for frame, x in ((1, 0.0), (25, 4.0), (49, 0.0)):
    ob.location.x = x
    ob.keyframe_insert("location", index=0, frame=frame)

for frame, deg in ((1, 0.0), (49, 360.0)):
    ob.rotation_euler.z = math.radians(deg)
    ob.keyframe_insert("rotation_euler", index=2, frame=frame)

strength = bsdf.inputs["Emission Strength"]
for frame, s in ((1, 0.0), (25, 5.0), (49, 0.0)):
    strength.default_value = s
    strength.keyframe_insert("default_value", frame=frame)   # lands on the node tree's action

for owner in (ob, mat.node_tree):
    for fc in owner.animation_data.action.fcurves:
        fc.modifiers.new('CYCLES')

sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=out)
