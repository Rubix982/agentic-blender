# Bending: a 2 m cylinder skinned with automatic weights to a three-bone armature along its axis; the middle bone at 45 deg.
import math, os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh, bpy
from mathutils import Quaternion
from _common import OUT, link
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new("Tube"); bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.2, radius2=0.2, depth=2.0)
side = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1.5]
bmesh.ops.subdivide_edges(bm, edges=side, cuts=19, use_grid_fill=True)
bm.to_mesh(me); bm.free()
tube = link(bpy.data.objects.new("Tube", me)); tube.location.z = 1.0
arm = link(bpy.data.objects.new("Rig", bpy.data.armatures.new("Rig")))
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
prev = None
for i, (z0, z1) in enumerate(((0, 2 / 3), (2 / 3, 4 / 3), (4 / 3, 2))):
    b = arm.data.edit_bones.new(f"Bone{i}"); b.head = (0, 0, z0); b.tail = (0, 0, z1)
    if prev:
        b.parent = prev; b.use_connect = True
    prev = b
bpy.ops.object.mode_set(mode="OBJECT")
for o in bpy.context.scene.objects:
    o.select_set(o in (tube, arm))
bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type="ARMATURE_AUTO")
pb = arm.pose.bones["Bone1"]; pb.rotation_mode = "QUATERNION"
pb.rotation_quaternion = Quaternion((1, 0, 0), math.radians(45))
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
