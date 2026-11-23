"""Writing video straight from a render in 4.5: which FFMPEG container + codec pairs this build writes, how long a short
clip takes and how big it is, whether Blender's own movie loading reads back the right frame count, what an odd frame
size does to H.264, and what the quality presets cost in bytes. Workbench, 128 px, 24 frames, so it is fast."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import shutil
import time

import bpy
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
d = E.out("clips")
shutil.rmtree(d, ignore_errors=True)
os.makedirs(d)

# A cube crossing the frame, seen by a camera; Workbench so encoding dominates.
me = bpy.data.meshes.new("Cube")
import bmesh
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
cube = bpy.data.objects.new("Cube", me)
scene.collection.objects.link(cube)
cube.location = (-2, 0, 0); cube.keyframe_insert("location", frame=1)
cube.location = (2, 0, 0); cube.keyframe_insert("location", frame=24)
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.location = (0, -8, 0); cam.rotation_euler = (1.5708, 0, 0)
scene.collection.objects.link(cam); scene.camera = cam
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = scene.render.resolution_y = 128
scene.frame_start, scene.frame_end = 1, 24

st = scene.render.image_settings
ff = scene.render.ffmpeg
before = dict(file_format=st.file_format, format=ff.format, codec=ff.codec, crf=ff.constant_rate_factor,
              preset=ff.ffmpeg_preset, gopsize=ff.gopsize, audio_codec=ff.audio_codec)
st.file_format = "FFMPEG"
after = dict(file_format=st.file_format, format=ff.format, codec=ff.codec, crf=ff.constant_rate_factor,
             preset=ff.ffmpeg_preset, gopsize=ff.gopsize, audio_codec=ff.audio_codec)
E.fact("a new scene's FFMPEG settings read MPEG1 / no codec / CRF NONE / keyframe interval 0 until file_format is set to "
       "FFMPEG; setting it fills in MKV / H264 / MEDIUM / interval 18 (so read them after, not before)",
       before=before, after=after)
st.file_format = "PNG"


def err(fn):
    try:
        return "ok", fn()
    except Exception as e:  # noqa: BLE001
        return "error", f"{type(e).__name__}: {str(e).strip()[:200]}"


def clear():
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))


def encode(container, codec, w=128, h=128, crf=None, label=None):
    clear()
    scene.render.resolution_x, scene.render.resolution_y = w, h
    st.file_format = "FFMPEG"
    set_c = err(lambda: setattr(ff, "format", container))
    set_v = err(lambda: setattr(ff, "codec", codec))
    if crf:
        ff.constant_rate_factor = crf
    scene.render.filepath = os.path.join(d, "clip")
    t = time.time()
    r = err(lambda: bpy.ops.render.render(animation=True))
    dt = time.time() - t
    files = sorted(os.listdir(d))
    out = dict(set_format=set_c[0], set_codec=set_v[0], codec_now=ff.codec, render=r[0] if r[0] == "error" else str(r[1]),
               render_error=r[1] if r[0] == "error" else None, files=files, seconds=round(dt, 3),
               bytes=os.path.getsize(os.path.join(d, files[0])) if files else 0)
    if files:
        p = os.path.join(d, files[0])
        clip = err(lambda: bpy.data.movieclips.load(p))
        if clip[0] == "ok":
            out["movieclip_frames"] = clip[1].frame_duration
            out["movieclip_size"] = list(clip[1].size)
            bpy.data.movieclips.remove(clip[1])
        else:
            out["movieclip_error"] = clip[1]
        img = err(lambda: bpy.data.images.load(p))
        if img[0] == "ok":
            out["image_source"] = img[1].source
            out["image_frames"] = img[1].frame_duration
            bpy.data.images.remove(img[1])
    if crf:
        ff.constant_rate_factor = "MEDIUM"
    return out


pairs = [("MPEG4", "H264"), ("MPEG4", "H265"), ("MPEG4", "AV1"), ("MPEG4", "MPEG4"),
         ("MKV", "H264"), ("MKV", "FFV1"), ("MKV", "AV1"),
         ("WEBM", "WEBM"), ("WEBM", "AV1"),
         ("QUICKTIME", "PRORES"), ("QUICKTIME", "QTRLE"), ("QUICKTIME", "PNG"), ("QUICKTIME", "H264"),
         ("OGG", "THEORA"), ("AVI", "HUFFYUV"), ("MPEG2", "MPEG2"), ("MPEG1", "MPEG1"), ("DV", "DV"),
         ("FLASH", "FLASH")]
res = {}
for c, v in pairs:
    res[f"{c}/{v}"] = encode(c, v)
    print("PAIR", c, v, res[f"{c}/{v}"], flush=True)

ok = {k: (r["bytes"], r["seconds"], r.get("movieclip_frames")) for k, r in res.items() if r["bytes"] > 0}
bad = {k: (r["render_error"] or "no file", r["codec_now"]) for k, r in res.items() if r["bytes"] == 0}
E.fact("every pair tried except DV/DV wrote a 24-frame 128 px clip that movieclips.load reads back (bytes, seconds, "
       "frames read back); MPEG1/MPEG1 and MPEG2/MPEG2 read back 20 and 19 frames, every other pair 24", written=ok)
E.fact("DV/DV wrote nothing: render() raised RuntimeError 'Render width has to be 720 pixels for DV!'", failed=bad)
E.fact("an .mp4 (MPEG4/H264) read back by bpy.data.movieclips.load has the rendered frame count (24) and size",
       frames=res["MPEG4/H264"].get("movieclip_frames"), size=res["MPEG4/H264"].get("movieclip_size"),
       image_source=res["MPEG4/H264"].get("image_source"), image_frames=res["MPEG4/H264"].get("image_frames"),
       name=res["MPEG4/H264"]["files"])

odd = encode("MPEG4", "H264", 127, 127)
E.fact("H.264 refuses an odd frame size: at 127 x 127 render() raised RuntimeError 'width not divisible by 2' and "
       "wrote no file", **{k: odd[k] for k in ("render", "render_error", "bytes")},
       size_read_back=odd.get("movieclip_size"))

q = {}
for crf in ("LOSSLESS", "PERC_LOSSLESS", "HIGH", "MEDIUM", "LOW", "LOWEST"):
    r = encode("MPEG4", "H264", crf=crf)
    q[crf] = r["bytes"]
E.fact("H.264 file size falls steadily from constant_rate_factor LOSSLESS to LOWEST for the same 24-frame 128 px "
       "clip (bytes)", sizes=q)

# PNG frames vs one MP4 at 512 px: time and bytes for the same 24 frames.
clear()
scene.render.resolution_x = scene.render.resolution_y = 512
st.file_format = "PNG"
scene.render.filepath = os.path.join(d, "f_####")
t = time.time(); bpy.ops.render.render(animation=True); png_s = time.time() - t
png_files = [f for f in os.listdir(d) if f.endswith(".png")]
png_bytes = sum(os.path.getsize(os.path.join(d, f)) for f in png_files)
mp4 = encode("MPEG4", "H264", 512, 512)
E.fact("24 frames at 512 px (Workbench): a PNG sequence against one MP4 (H.264, MEDIUM): seconds and bytes",
       png_seconds=round(png_s, 2), png_files=len(png_files), png_bytes=png_bytes, mp4_seconds=mp4["seconds"],
       mp4_bytes=mp4["bytes"])

shutil.rmtree(d)
E.save(pairs=res, odd=odd, quality=q)
