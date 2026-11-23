"""Found by C-005's shot: resuming a frame sequence. With render.use_overwrite off and render.use_placeholder on, which
frames does a second run render, after one frame's file is deleted and one is left empty (a placeholder a crashed run
leaves)? Frames counted by a render_post handler."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import tempfile
import bpy
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
bpy.ops.mesh.primitive_cube_add()
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.location = (0, -6, 0)
cam.rotation_euler = (1.5708, 0, 0)
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x, scene.render.resolution_y = 32, 32
scene.frame_start, scene.frame_end = 1, 5
d = tempfile.mkdtemp(prefix="ab-resume-")
scene.render.filepath = os.path.join(d, "")
scene.render.image_settings.file_format = "PNG"
rendered = []
bpy.app.handlers.render_post.append(lambda s, *a: rendered.append(s.frame_current))

E.fact("the defaults", use_overwrite=scene.render.use_overwrite, use_placeholder=scene.render.use_placeholder)
scene.render.use_overwrite, scene.render.use_placeholder = False, True
bpy.ops.render.render(animation=True)
first = list(rendered)
os.remove(os.path.join(d, "0002.png"))
open(os.path.join(d, "0004.png"), "w").close()                    # an empty file, as a crashed run's placeholder
rendered.clear()
bpy.ops.render.render(animation=True)
E.fact("with use_overwrite off and use_placeholder on: the first run renders every frame; after deleting frame 2's "
       "file and emptying frame 4's, the second run renders only these", first_run=first, second_run=list(rendered),
       frame4_bytes_after=os.path.getsize(os.path.join(d, "0004.png")))
E.save()
