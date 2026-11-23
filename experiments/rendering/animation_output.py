"""Rendering a frame range headless: how render.filepath turns into file names (frame-number padding with '#'), and
writing an MP4 (H.264) through FFMPEG. Workbench, 64 px, so it is fast."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glob
import shutil
import time
import bpy
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
E.fact("a new scene renders frames 1-250 at 24 fps to render.filepath '/tmp/'", frame_start=scene.frame_start,
       frame_end=scene.frame_end, fps=scene.render.fps, filepath=scene.render.filepath)
bpy.ops.mesh.primitive_cube_add()
cube = bpy.context.object
cube.keyframe_insert("location", frame=1)
cube.location.x = 2
cube.keyframe_insert("location", frame=10)
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.location = (0, -8, 0)
cam.rotation_euler = (1.5708, 0, 0)
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = scene.render.resolution_y = 64
scene.frame_start, scene.frame_end = 1, 10
d = E.out("anim")
os.makedirs(d, exist_ok=True)
names = {}
for pattern in ("frame_", "frame_###", "f_##_v2", "noext"):
    scene.render.filepath = os.path.join(d, pattern)
    scene.render.image_settings.file_format = "PNG"
    scene.render.use_file_extension = pattern != "noext"
    scene.frame_end = 2
    bpy.ops.render.render(animation=True)
    names[pattern] = sorted(os.listdir(d))
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
E.fact("render(animation=True) names files from render.filepath: no '#' appends a 4-digit frame number; a run of '#' is "
       "replaced by the zero-padded frame number at that place; use_file_extension adds .png",
       results=names)
scene.frame_end = 10
scene.render.use_file_extension = True
st = scene.render.image_settings
st.file_format = "FFMPEG"
ff = scene.render.ffmpeg
E.fact("FFMPEG output defaults: container MKV, codec H264, quality MEDIUM (constant_rate_factor)",
       format=ff.format, codec=ff.codec, crf=ff.constant_rate_factor, preset=ff.ffmpeg_preset)
ff.format = "MPEG4"
ff.codec = "H264"
scene.render.filepath = os.path.join(d, "clip")
t = time.time()
bpy.ops.render.render(animation=True)
files = sorted(os.listdir(d))
E.fact("with format MPEG4 + codec H264 a 10-frame range renders to one .mp4 named with the frame range (clip0001-0010.mp4)",
       files=files, bytes=[os.path.getsize(os.path.join(d, f)) for f in files], seconds=round(time.time() - t, 2))
shutil.rmtree(d)
E.save(names=names)
