# Wrong (resolution not set): Framing: the default cube scaled to (1, 0.5, 2); a 50 mm camera on a 36 mm sensor on the +Y side, the cube's projected
# height filling 80 % of a 1080 x 1080 frame.
import math, os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
from _common import OUT
sc = bpy.context.scene
cube = bpy.data.objects["Cube"]; cube.scale = (1, 0.5, 2)
cam = sc.camera
cam.data.lens = 50; cam.data.sensor_width = 36
# wrong: the frame left at the default 1920 x 1080
cam.rotation_euler = (math.radians(90), 0, math.radians(180))   # looks along -Y, Z up
def fill(d):
    cam.location = (0, d, 0); bpy.context.view_layer.update()
    pts = [world_to_camera_view(sc, cam, cube.matrix_world @ Vector(c)) for c in cube.bound_box]
    return max(p.y for p in pts) - min(p.y for p in pts)
lo, hi = 2.0, 50.0                                              # fill shrinks as the camera backs away
for _ in range(60):
    mid = (lo + hi) / 2
    lo, hi = (mid, hi) if fill(mid) > 0.80 else (lo, mid)
fill((lo + hi) / 2)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
