"""Two ways to aim a camera at a target (a Track To constraint, or a rotation computed with to_track_quat), and does
depth of field blur what it should? DOF is measured as the width of a black/white edge in a Cycles render."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import math
import bpy
import numpy as np
import OpenImageIO as oiio
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
target = bpy.data.objects.new("Target", None)
target.location = (1.0, 2.0, 0.5)
scene.collection.objects.link(target)

# 1) computed rotation: the camera looks down its local -Z with local +Y up
a = bpy.data.objects.new("CamA", bpy.data.cameras.new("CamA"))
a.location = (6, -7, 4)
a.rotation_euler = (target.location - a.location).to_track_quat("-Z", "Y").to_euler()
scene.collection.objects.link(a)
# 2) Track To constraint
b = bpy.data.objects.new("CamB", bpy.data.cameras.new("CamB"))
b.location = (6, -7, 4)
scene.collection.objects.link(b)
con = b.constraints.new("TRACK_TO")
con.target = target
E.fact("a new Track To constraint defaults to track_axis TRACK_NEGATIVE_Z and up_axis UP_Y, which is right for cameras and "
       "lights (2.8+; older scripts set them by hand)", track_axis=con.track_axis, up_axis=con.up_axis)
bpy.context.view_layer.update()
scene.camera = a
pa = world_to_camera_view(scene, a, target.location)
scene.camera = b
pb = world_to_camera_view(scene, b, target.location)
up_a = a.matrix_world.to_3x3() @ Vector((0, 1, 0))
up_b = b.matrix_world.to_3x3() @ Vector((0, 1, 0))
E.fact("both put the target at the frame centre (0.5, 0.5) with the same camera up vector; the constraint's result is in "
       "matrix_world (after a view_layer.update()), while rotation_euler stays (0, 0, 0)",
       computed_ndc=[round(pa.x, 4), round(pa.y, 4)], constraint_ndc=[round(pb.x, 4), round(pb.y, 4)],
       up_dot=round(up_a.dot(up_b), 5), constraint_rotation_euler=[round(v, 3) for v in b.rotation_euler])
# without the update, matrix_world is stale
target.location = (-3, 0, 0)
stale = world_to_camera_view(scene, b, target.location)
bpy.context.view_layer.update()
fresh = world_to_camera_view(scene, b, target.location)
E.fact("after moving the target, the constrained camera's matrix_world is stale until bpy.context.view_layer.update()",
       before_update_ndc=[round(stale.x, 3), round(stale.y, 3)], after_update_ndc=[round(fresh.x, 3), round(fresh.y, 3)])
# what a wrong axis pair gives: to_track_quat('Z', 'Y') looks away from the target
c = bpy.data.objects.new("CamC", bpy.data.cameras.new("CamC"))
c.location = (6, -7, 4)
c.rotation_euler = (Vector((1.0, 2.0, 0.5)) - c.location).to_track_quat("Z", "Y").to_euler()
scene.collection.objects.link(c)
bpy.context.view_layer.update()
scene.camera = c
pc = world_to_camera_view(scene, c, Vector((1.0, 2.0, 0.5)))
E.fact("to_track_quat('Z', 'Y') points the camera away from the target: its depth is negative", depth=round(pc.z, 3))

# 3) depth of field: a black/white checker card at 2 m and another at 6 m; focus on the near one
exp.empty()
scene = bpy.context.scene
mat = bpy.data.materials.new("edge")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.remove(next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"))
em = nt.nodes.new("ShaderNodeEmission")
chk = nt.nodes.new("ShaderNodeTexChecker")
chk.inputs["Scale"].default_value = 2.0  # scale 1 over 0..1 Generated coords is a single square (all Color2): no edge
chk.inputs["Color1"].default_value = (1, 1, 1, 1)
chk.inputs["Color2"].default_value = (0, 0, 0, 1)
nt.links.new(chk.outputs["Color"], em.inputs["Color"])
nt.links.new(em.outputs[0], next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL").inputs["Surface"])
cards = []
for y in (2.0, 6.0):
    bpy.ops.mesh.primitive_plane_add(size=0.5 * y, location=(0, y, 0), rotation=(math.radians(90), 0, 0))
    bpy.context.object.data.materials.append(mat)
    cards.append(bpy.context.object)
cards[0].location.x = -0.25 * 2  # near card on the left half of the frame
cards[1].location.x = 0.25 * 6   # far card on the right half
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.rotation_euler = (math.radians(90), 0, 0)
scene.collection.objects.link(cam)
scene.camera = cam
scene.world = None
scene.render.engine = "CYCLES"
exp.metal()
scene.cycles.samples = 64
scene.cycles.use_denoising = False
scene.render.resolution_x, scene.render.resolution_y = 256, 128
scene.render.image_settings.file_format = "OPEN_EXR"


def edge_widths():
    scene.render.filepath = E.out("tmp.exr")
    bpy.ops.render.render(write_still=True)
    a = oiio.ImageBuf(scene.render.filepath).get_pixels(oiio.FLOAT)[..., 0]
    os.remove(scene.render.filepath)
    out = []
    for x0, x1 in ((0, 128), (128, 256)):
        col = a[:, x0:x1]
        # the checker's horizontal edge through each card's centre: the 10-90 % rise along a column
        prof = col[:, (x1 - x0) // 2 - 8:(x1 - x0) // 2 + 8].mean(axis=1)
        lo, hi = prof.min(), prof.max()
        f = (prof - lo) / max(hi - lo, 1e-6)
        centre = len(f) // 2
        seg = f[centre - 30:centre + 30]
        out.append(int(np.sum((seg > 0.1) & (seg < 0.9))))
    return out


cam.data.dof.use_dof = False
sharp = edge_widths()
cam.data.dof.use_dof = True
cam.data.dof.focus_object = cards[0]
cam.data.dof.aperture_fstop = 1.4
near_focus = edge_widths()
cam.data.dof.focus_object = None
cam.data.dof.focus_distance = 6.0
far_focus = edge_widths()

def coc_px(focus, d, f=50.0, N=1.4, sensor=36.0, W=256):
    """Thin-lens blur circle on the sensor, in pixels: aperture (f/N) * f/(s - f) * |d - s| / d, all in mm."""
    s, d = focus * 1000, d * 1000
    return round((f / N) * f / (s - f) * abs(d - s) / d / sensor * W, 1)


E.fact("with camera.data.dof.use_dof and f/1.4 (50 mm), the card at the focus stays as sharp as without DOF and the other "
       "blurs by about the thin-lens circle of confusion (edge width in px, 10-90 %, [near card at 2 m, far card at 6 m])",
       dof_off=sharp, focus_object_near=near_focus, focus_distance_6=far_focus,
       predicted_coc_px_far_when_focus_near=coc_px(2, 6), predicted_coc_px_near_when_focus_far=coc_px(6, 2))
E.save()
