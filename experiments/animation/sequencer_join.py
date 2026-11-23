"""Joining rendered frames into a video with the Video Sequencer from Python in 4.5: the 4.4 renames (Sequence -> Strip,
sequence_editor.sequences -> .strips), new_image + elements.append for an image sequence, new_movie, what the sequencer
does to a scene that also has 3D content, and whether the joined MP4 has every frame."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import shutil
import time
import warnings

import bmesh
import bpy
import numpy as np
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
d = E.out("seq")
shutil.rmtree(d, ignore_errors=True)
os.makedirs(d)


def err(fn):
    try:
        return "ok", fn()
    except Exception as e:  # noqa: BLE001
        return "error", f"{type(e).__name__}: {str(e).strip()[:200]}"


# The 4.4 renames, read from bpy.types.
names = {n: hasattr(bpy.types, n) for n in ("Sequence", "Strip", "ImageSequence", "ImageStrip", "MovieSequence",
                                             "MovieStrip", "SequencesTopLevel", "StripsTopLevel", "SequenceElement",
                                             "StripElement")}
E.fact("4.5 names the sequencer's types Strip, ImageStrip, MovieStrip, StripsTopLevel, StripElement; the pre-4.4 "
       "Sequence names are gone from bpy.types", **names)
fresh = bpy.data.scenes.new("Fresh")
E.fact("a scene made with bpy.data.scenes.new has no sequence editor (None) until sequence_editor_create(); the factory "
       "scene already has one", factory_scene=scene.sequence_editor is not None, new_scene=str(fresh.sequence_editor))
bpy.data.scenes.remove(fresh)
se = scene.sequence_editor_create()
E.fact("sequence_editor_create() returns the editor; .strips and the deprecated .sequences both exist",
       has_strips=hasattr(se, "strips"), has_sequences=hasattr(se, "sequences"))

# 1. Render 12 PNG frames of a moving cube.
me = bpy.data.meshes.new("Cube")
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
cube = bpy.data.objects.new("Cube", me)
scene.collection.objects.link(cube)
cube.location = (-2, 0, 0); cube.keyframe_insert("location", frame=1)
cube.location = (2, 0, 0); cube.keyframe_insert("location", frame=12)
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.location = (0, -8, 0); cam.rotation_euler = (1.5708, 0, 0)
scene.collection.objects.link(cam); scene.camera = cam
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x, scene.render.resolution_y = 128, 96
scene.frame_start, scene.frame_end = 1, 12
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = os.path.join(d, "f_####")
bpy.ops.render.render(animation=True)
frames = sorted(f for f in os.listdir(d) if f.startswith("f_"))

# 2. A new scene holding only the strips (keeps the 3D scene apart).
vse = bpy.data.scenes.new("Edit")
vse.render.resolution_x, vse.render.resolution_y = 128, 96
ed = vse.sequence_editor_create()
s = ed.strips.new_image(name="frames", filepath=os.path.join(d, frames[0]), channel=1, frame_start=1)
one = dict(len_elements=len(s.elements), duration=s.frame_final_duration, type=s.type, cls=type(s).__name__,
           directory=os.path.basename(os.path.normpath(s.directory)))
for f in frames[1:]:
    s.elements.append(f)
E.fact("strips.new_image(name, filepath, channel, frame_start) makes a 1-frame image strip; elements.append(filename) "
       "adds frames from the same directory, and the strip lengthens to match",
       at_creation=one, after_append=dict(len_elements=len(s.elements), duration=s.frame_final_duration,
                                          end=s.frame_final_end))
big = bpy.data.scenes.new("Big")
big.render.resolution_x, big.render.resolution_y = 256, 192
bed = big.sequence_editor_create()
fits = {}
for fm in ("ORIGINAL", "FIT", "FILL", "STRETCH"):
    st_ = bed.strips.new_image(name=fm, filepath=os.path.join(d, frames[0]), channel=1, frame_start=1, fit_method=fm)
    fits[fm] = (round(st_.transform.scale_x, 3), round(st_.transform.scale_y, 3))
fits["default"] = (lambda x: (round(x.transform.scale_x, 3), round(x.transform.scale_y, 3)))(
    bed.strips.new_image(name="dflt", filepath=os.path.join(d, frames[0]), channel=2, frame_start=1))
E.fact("fit_method is only an argument of new_image/new_movie (no strip property); a 128 x 96 image in a 256 x 192 "
       "scene gets transform.scale 1 with ORIGINAL (the default: drawn at its pixel size, a quarter of the frame) and 2 "
       "with FIT", has_strip_property=hasattr(s, "fit_method"), scales=fits)
bpy.data.scenes.remove(big)

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    old = err(lambda: len(ed.sequences))
    old_all = err(lambda: len(ed.sequences_all))
E.fact("the deprecated sequence_editor.sequences still works in 4.5 and warns nothing through Python's warnings",
       sequences=old, sequences_all=old_all, python_warnings=[str(x.message)[:120] for x in w])
ops_try = err(lambda: bpy.ops.sequencer.image_strip_add(directory=d + "/", files=[{"name": f} for f in frames],
                                                         frame_start=1, channel=2))
E.fact("bpy.ops.sequencer.image_strip_add in background mode, without an override", result=ops_try)

vse.frame_start, vse.frame_end = 1, s.frame_final_end - 1
vse.render.image_settings.file_format = "FFMPEG"
vse.render.ffmpeg.format, vse.render.ffmpeg.codec = "MPEG4", "H264"
vse.render.filepath = os.path.join(d, "joined")
t = time.time()
with bpy.context.temp_override(scene=vse):
    r = err(lambda: bpy.ops.render.render(animation=True, scene=vse.name))
dt = time.time() - t
mp4 = [f for f in os.listdir(d) if f.endswith(".mp4")]
clip = bpy.data.movieclips.load(os.path.join(d, mp4[0])) if mp4 else None
E.fact("rendering the strips scene writes one MP4 with every frame (12), read back by movieclips.load",
       render=str(r), files=mp4, frames=clip.frame_duration if clip else None, seconds=round(dt, 3),
       use_sequencer=vse.render.use_sequencer)

# 3. new_movie on that MP4.
mv = ed.strips.new_movie(name="movie", filepath=os.path.join(d, mp4[0]), channel=2, frame_start=1)
E.fact("strips.new_movie reads the clip's length into frame_final_duration (12 here)",
       duration=mv.frame_final_duration, cls=type(mv).__name__, fps=round(mv.fps, 3) if hasattr(mv, "fps") else None)

# 4. A scene with 3D content AND strips: what gets rendered.
se.strips.new_image(name="still", filepath=os.path.join(d, frames[0]), channel=1, frame_start=12)
scene.render.image_settings.file_format = "PNG"
scene.frame_set(6)
scene.render.filepath = os.path.join(d, "gap.png")
bpy.ops.render.render(write_still=True)
g = bpy.data.images.load(os.path.join(d, "gap.png"))
pg = np.array(g.pixels[:]).reshape(g.size[1], g.size[0], 4)
ref6 = bpy.data.images.load(os.path.join(d, frames[5]))
p6 = np.array(ref6.pixels[:]).reshape(ref6.size[1], ref6.size[0], 4)
E.fact("in a scene that has strips, a frame no strip covers renders black, not the 3D view",
       mean_rgb=round(float(pg[..., :3].mean()), 4), max_rgb=round(float(pg[..., :3].max()), 4),
       max_diff_to_3d_frame6=round(float(np.abs(pg - p6).max()), 4))
scene.frame_set(12)
scene.render.filepath = os.path.join(d, "mixed.png")
bpy.ops.render.render(write_still=True)
img = bpy.data.images.load(os.path.join(d, "mixed.png"))
px = np.array(img.pixels[:]).reshape(img.size[1], img.size[0], 4)
ref = bpy.data.images.load(os.path.join(d, frames[0]))
pr = np.array(ref.pixels[:]).reshape(ref.size[1], ref.size[0], 4)
ref12 = bpy.data.images.load(os.path.join(d, frames[-1]))
p12 = np.array(ref12.pixels[:]).reshape(ref12.size[1], ref12.size[0], 4)
diff_strip = float(np.abs(px - pr).max())
diff_3d = float(np.abs(px - p12).max())
scene.render.use_sequencer = False
bpy.ops.render.render(write_still=True)
img2 = bpy.data.images.load(os.path.join(d, "mixed.png"), check_existing=False)
px2 = np.array(img2.pixels[:]).reshape(img2.size[1], img2.size[0], 4)
E.fact("a scene that has strips renders the strips, not its 3D view (frame 12 rendered as the strip's image, frame 1); "
       "with render.use_sequencer = False it renders the 3D scene again",
       max_diff_to_strip_image=round(diff_strip, 4), max_diff_to_3d_frame12=round(diff_3d, 4),
       use_sequencer_off_diff_to_3d=round(float(np.abs(px2 - p12).max()), 4))

shutil.rmtree(d)
E.save(frames=frames)
