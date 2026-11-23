"""Does bpy_extras.object_utils.world_to_camera_view predict where a point lands in the rendered image, and how do lens,
sensor, sensor_fit, shift and orthographic scale set the view? Checked against the pixel centroid of a small emissive
sphere in real renders."""
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
cd = bpy.data.cameras.new("Camera")
E.fact("a new camera: lens 50 mm, sensor 36 mm wide (24 tall), sensor_fit AUTO, clip 0.1 to 1000 m, perspective, ortho_scale 6, "
       "depth of field off at f/2.8",
       lens=cd.lens, sensor_width=cd.sensor_width, sensor_height=cd.sensor_height, sensor_fit=cd.sensor_fit,
       clip_start=cd.clip_start, clip_end=cd.clip_end, type=cd.type, ortho_scale=cd.ortho_scale,
       lens_unit=cd.lens_unit, dof_use=cd.dof.use_dof, fstop=cd.dof.aperture_fstop)
cam = bpy.data.objects.new("Camera", cd)
scene.collection.objects.link(cam)
scene.camera = cam
cam.location = (0, -10, 0)
cam.rotation_euler = (math.radians(90), 0, 0)  # looking along +Y
mat = bpy.data.materials.new("glow")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.remove(next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"))
em = nt.nodes.new("ShaderNodeEmission")
nt.links.new(em.outputs[0], next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL").inputs["Surface"])
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08, location=(1.5, 0, 0.7))
ball = bpy.context.object
ball.data.materials.append(mat)
scene.world = None
scene.render.engine = "CYCLES"
scene.cycles.samples = 16
scene.cycles.use_denoising = False
scene.render.image_settings.file_format = "OPEN_EXR"


def centroid():
    scene.render.filepath = E.out("tmp.exr")
    bpy.ops.render.render(write_still=True)
    a = oiio.ImageBuf(scene.render.filepath).get_pixels(oiio.FLOAT)[..., 0]
    os.remove(scene.render.filepath)
    ys, xs = np.nonzero(a > 0.5)
    return (float(xs.mean()) + 0.5, float(ys.mean()) + 0.5) if len(xs) else None


def predicted():
    bpy.context.view_layer.update()
    p = world_to_camera_view(scene, cam, ball.location)
    W = scene.render.resolution_x * scene.render.resolution_percentage / 100
    H = scene.render.resolution_y * scene.render.resolution_percentage / 100
    return (p.x * W, (1 - p.y) * H), p


rows = []
cases = [("landscape 320x200, 50 mm", dict(res=(320, 200))),
         ("portrait 200x320, 50 mm, AUTO fit", dict(res=(200, 320))),
         ("portrait 200x320, sensor_fit HORIZONTAL", dict(res=(200, 320), fit="HORIZONTAL")),
         ("landscape, 25 mm", dict(res=(320, 200), lens=25)),
         ("landscape, shift_x 0.1, shift_y -0.05", dict(res=(320, 200), shift=(0.1, -0.05))),
         ("landscape, resolution_percentage 50", dict(res=(320, 200), pct=50)),
         ("orthographic, ortho_scale 6", dict(res=(320, 200), ortho=6))]
for name, c in cases:
    cd.lens, cd.sensor_fit, cd.shift_x, cd.shift_y, cd.type = c.get("lens", 50), c.get("fit", "AUTO"), *c.get("shift", (0, 0)), "PERSP"
    if "ortho" in c:
        cd.type, cd.ortho_scale = "ORTHO", c["ortho"]
    scene.render.resolution_x, scene.render.resolution_y = c["res"]
    scene.render.resolution_percentage = c.get("pct", 100)
    got = centroid()
    pred, p = predicted()
    rows.append(dict(case=name, rendered_px=[round(v, 1) for v in got], predicted_px=[round(v, 1) for v in pred],
                     err_px=round(math.dist(got, pred), 2), ndc=[round(p.x, 4), round(p.y, 4), round(p.z, 3)]))
    print(rows[-1])
E.fact("world_to_camera_view(scene, cam, point) returns (x, y, depth) with x, y in 0..1 from the bottom-left of the frame; "
       "pixel = (x * W, (1 - y) * H) lands within 1 px of the rendered position for every case: aspect, sensor_fit, lens, "
       "shift, resolution_percentage, orthographic",
       rows=rows, max_err_px=max(r["err_px"] for r in rows))

# field of view: angle_x follows sensor_width and lens for a landscape frame; for a portrait frame AUTO fits the sensor
# width to the longer (vertical) side
cd.type, cd.lens, cd.sensor_fit, cd.shift_x, cd.shift_y = "PERSP", 50, "AUTO", 0, 0
fov = dict(angle_deg=round(math.degrees(cd.angle), 3), angle_x_deg=round(math.degrees(cd.angle_x), 3),
           formula_deg=round(math.degrees(2 * math.atan(cd.sensor_width / 2 / cd.lens)), 3))
E.fact("camera.angle (= angle_x for AUTO fit) is 2*atan(sensor_width / 2 / lens): 39.6 degrees at 50 mm on a 36 mm sensor", **fov)
# orthographic: ortho_scale is the frame's width in metres along its longer side
cd.type, cd.ortho_scale = "ORTHO", 6
scene.render.resolution_x, scene.render.resolution_y = 320, 200
edge = world_to_camera_view(scene, cam, Vector((3.0, 0, 0)))
E.fact("for an orthographic camera, ortho_scale is the frame's extent in metres along the longer side: a point 3 m right of "
       "centre with ortho_scale 6 sits at x = 1.0", x=round(edge.x, 4))
# the operator that frames selected objects: does it run headless, and does it frame?
cd.type = "PERSP"
bpy.ops.object.select_all(action="DESELECT")
ball.select_set(True)
bpy.context.view_layer.objects.active = ball
before = tuple(round(v, 3) for v in cam.location)
try:
    res = bpy.ops.view3d.camera_to_view_selected()
    op = str(res)
except RuntimeError as e:
    op = str(e).strip()
bpy.context.view_layer.update()
after = tuple(round(v, 3) for v in cam.location)
p = world_to_camera_view(scene, cam, ball.location)
corners = [world_to_camera_view(scene, cam, ball.matrix_world @ Vector(c)) for c in ball.bound_box]
E.fact("bpy.ops.view3d.camera_to_view_selected runs in background mode without a 3D viewport: it moves the active camera "
       "(keeping its rotation) so the selected objects fill the frame",
       result=op, cam_before=before, cam_after=after, ball_ndc=[round(p.x, 3), round(p.y, 3)],
       bbox_x_range=[round(min(c.x for c in corners), 3), round(max(c.x for c in corners), 3)],
       bbox_y_range=[round(min(c.y for c in corners), 3), round(max(c.y for c in corners), 3)])
E.save(rows=rows)
