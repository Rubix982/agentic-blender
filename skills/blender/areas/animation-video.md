# Animation and video

Blender 4.5.14 LTS on Apple Silicon (16 GB, Metal). Tags: `[inv]` read from Blender (`scripts/kb.py`), `[exp: path]`
measured here (paths relative to the source repository; results next to each script in `results/`), `[doc: link]`
Blender's documentation. Timings are small scenes (64 to 512 px) with other Blender jobs sharing the machine; repeated
runs moved by up to 2x. Keyframes and slotted actions in general: `rigging-animation.md`. Output file naming
(`#` padding) and image formats: `rendering.md`.

## What goes wrong most often

1. **Keys that ease in and out.** `keyframe_insert` makes BEZIER keys, so a turntable keyed 0 to 360 degrees over 24
   frames moved 1.823 degrees on its first frame and 22.448 in the middle. Set each key's `interpolation = "LINEAR"`
   after inserting (code below). Setting `preferences.edit.keyframe_new_interpolation_type = "LINEAR"` does not help
   from a script: it read back LINEAR, yet `keyframe_insert` still made BEZIER keys; only the `anim.keyframe_insert`
   operator used it, and that operator failed its poll headless unless run inside the 3D View override
   (`data-model.md`). `[exp: experiments/animation/turntable.py]`
2. **Reading the FFMPEG settings before choosing FFMPEG.** In a new scene `render.ffmpeg` reads container MPEG1, codec
   NONE, quality NONE, keyframe interval 0. Setting `image_settings.file_format = "FFMPEG"` fills in MKV, H264, MEDIUM
   and interval 18. Set the file format first, then read or change the rest.
   `[exp: experiments/animation/video_codecs.py]`
3. **`-s` and `-e` after `-a`.** Command-line arguments run in order: `-s 2 -e 4 -a` rendered frames 2 to 4, but
   `-a -s 2 -e 4` rendered the file's whole range (1 to 10) and then set the range too late.
   `[exp: experiments/animation/cli_frame_range.py]`
4. **An odd frame size with H.264.** At 127 x 127 `render.render(animation=True)` raised
   `RuntimeError: Error: width not divisible by 2 (127x127)` and wrote nothing. DV raised "Render width has to be 720
   pixels for DV!" at 128 px. `[exp: experiments/animation/video_codecs.py]`
5. **The 4.4 sequencer renames.** `bpy.types.Sequence`, `ImageSequence`, `MovieSequence`, `SequencesTopLevel` and
   `SequenceElement` are gone; they are `Strip`, `ImageStrip`, `MovieStrip`, `StripsTopLevel` and `StripElement`. The
   collection is `sequence_editor.strips`; the old `sequence_editor.sequences` still worked in 4.5 and raised no Python
   warning, but `kb.py` lists it as "(Deprecated: Replaced by '.strips')". `[exp: experiments/animation/sequencer_join.py]`
   `[inv]`
6. **A scene with strips renders the strips.** Once a scene's sequencer has any strip, rendering it gives the
   sequencer's picture: at a frame no strip covers it rendered black (mean 0.0003), not the 3D view. With
   `render.use_sequencer = False` it rendered the 3D scene again (difference 0.0). Keep the 3D scene and the editing
   scene apart. `[exp: experiments/animation/sequencer_join.py]`
7. **Sequencer operators headless.** `bpy.ops.sequencer.image_strip_add` failed its poll ("context is incorrect").
   Use `sequence_editor.strips.new_image` / `new_movie` instead. `[exp: experiments/animation/sequencer_join.py]`
8. **Motion blur in EEVEE's settings.** `scene.eevee.use_motion_blur` is gone since 4.2 (`rendering.md`); one switch,
   `scene.render.use_motion_blur`, serves EEVEE and Cycles. Workbench ignores it.
   `[exp: experiments/animation/motion_blur.py]`
9. **Expecting the GPU to win on small frames.** At 256 px and 16 samples Cycles took 0.079 s a frame on the CPU and
   0.293 s on Metal; Metal's time hardly moved between 16 and 64 samples (0.308 s), a fixed cost per frame.
   `render.use_persistent_data = True` cut Metal to 0.098 s. `[exp: experiments/animation/engine_frame_time.py]`
10. **Old MPEG containers for anything you will read back.** Blender's own movie loading read 20 of 24 frames from an
    MPEG-1 file and 19 from MPEG-2 (written as `.dvd`); every other container read back 24.
    `[exp: experiments/animation/video_codecs.py]`
11. **An F-modifier added after the scene was evaluated.** A Cycles modifier added to a curve after a `frame_set` was
    ignored by later `frame_set` calls (frame 61 still read the held last key, 0.0) though `fcurve.evaluate(61)`
    already gave 1.0; `action.update_tag()` fixed it. A new Cycles modifier starts at REPEAT both ways, with no limit.
    `[exp: experiments/animation/loops_and_node_keys.py]`
12. **Looking for a material's animation on the material.** Keying a node input
    (`node.inputs["Strength"].keyframe_insert("default_value")`) puts the action on `mat.node_tree`;
    `mat.animation_data` stays None. While the material is on no object, `frame_set` leaves the input at the last value
    set; `fcurve.evaluate(frame)` reads the curve. `[exp: experiments/animation/loops_and_node_keys.py]`

## Render a frame range from Python

```python
scene.frame_start, scene.frame_end = 1, 10
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = os.path.join(d, "f_####")     # '#' run -> zero-padded frame number
bpy.ops.render.render(animation=True)                 # blocks; writes f_0001.png ... f_0010.png
```

`render(animation=True)` renders `frame_start` to `frame_end` and writes one file per frame; nothing is returned but
`{'FINISHED'}`. To time frames separately, `bpy.app.handlers.render_pre` and `render_post` fire around each frame in
background mode (used below). `[exp: experiments/animation/engine_frame_time.py]` File naming:
`[exp: experiments/rendering/animation_output.py]`

## Render a frame range from the command line

```bash
blender -b scene.blend -s 2 -e 4 -a                      # frames 2-4 to the file's render.filepath
blender -b scene.blend -s 1 -e 9 -j 3 -a                 # 1, 4, 7
blender -b scene.blend -f 1,3,5..6                       # 1, 3, 5, 6
blender -b scene.blend -f -1                             # the range's last frame
blender -b scene.blend -o //other/g_## -F JPEG -s 1 -e 2 -a   # other/g_01.jpg, g_02.jpg next to the .blend
```

| Arguments (after `-b scene.blend`, range 1-10 in the file) | Files written |
|---|---|
| `-a` | `out/f_0001.png` ... `f_0010.png` (the file's own path `//out/f_####`) |
| `-s 2 -e 4 -a` | `f_0002` to `f_0004` |
| `-a -s 2 -e 4` | all ten: the range came too late |
| `-s 1 -e 9 -j 3 -a` | `f_0001`, `f_0004`, `f_0007` |
| `-f 3` / `-f 1,3,5..6` / `-f -1` | `f_0003` / 1, 3, 5, 6 / `f_0010` |
| `-o //other/g_## -F JPEG -s 1 -e 2 -a` | `other/g_01.jpg`, `other/g_02.jpg` |
| `-o /abs/h_ -x 0 -f 1` | `h_0001` (no extension) |
| `-F FFMPEG -s 1 -e 10 -a` | `out/f_0001-0010.mkv` |

`[exp: experiments/animation/cli_frame_range.py]` Each run of this small Workbench file took about 0.5 s, start-up
included. `//` is the `.blend`'s folder. `-F FFMPEG` on a file that never chose FFMPEG still wrote a video, with the
defaults of item 2 (MKV). `[exp: experiments/animation/cli_frame_range.py]`

## Write a video directly

```python
st = scene.render.image_settings
st.file_format = "FFMPEG"                     # first: this fills in the FFMPEG defaults
ff = scene.render.ffmpeg
ff.format = "MPEG4"                           # container
ff.codec = "H264"
ff.constant_rate_factor = "MEDIUM"            # LOSSLESS, PERC_LOSSLESS, HIGH, MEDIUM, LOW, VERYLOW, LOWEST, NONE
scene.render.filepath = os.path.join(d, "clip")
bpy.ops.render.render(animation=True)         # -> clip0001-0024.mp4

clip = bpy.data.movieclips.load(path)         # check it: frame count and size
clip.frame_duration, tuple(clip.size)         # 24, (128, 128)
```

One file per range, named with the range (`clip0001-0024.mp4`). Reading it back with `bpy.data.movieclips.load` gave
24 frames at 128 x 128; `bpy.data.images.load` on the same file gave an image with `source` `MOVIE` and
`frame_duration` 24. `[exp: experiments/animation/video_codecs.py]`

Containers and codecs this build offers: containers `MPEG4`, `MKV` (default), `WEBM`, `AVI`, `DV`, `FLASH`, `MPEG1`,
`MPEG2`, `OGG`, `QUICKTIME`; codecs `NONE`, `AV1`, `H264`, `H265`, `WEBM` (VP9), `DNXHD`, `DV`, `FFV1`, `FLASH`,
`HUFFYUV`, `MPEG1`, `MPEG2`, `MPEG4`, `PNG`, `PRORES`, `QTRLE`, `THEORA`; audio `NONE` (default), `AAC`, `AC3`, `FLAC`,
`MP2`, `MP3`, `OPUS`, `PCM`, `VORBIS`. `[inv]` (`kb.py struct FFmpegSettings`)

**PNG frames or one video?** 24 frames at 512 px (Workbench): a PNG sequence took 0.28 s and 1,588,350 bytes; one H.264
MP4 took 0.188 s and 4,785 bytes. Frames survive a crash mid-range and can be re-encoded; a video cannot be resumed.
`[exp: experiments/animation/video_codecs.py]` (the second sentence is general knowledge, not measured here)

## Join frames into a video with the Video Sequencer

```python
vse = bpy.data.scenes.new("Edit")                         # a separate scene: strips take over a scene's render
vse.render.resolution_x, vse.render.resolution_y = 128, 96
ed = vse.sequence_editor_create()                         # a new scene's sequence_editor is None until this
s = ed.strips.new_image(name="frames", filepath=os.path.join(d, frames[0]), channel=1, frame_start=1)
for f in frames[1:]:
    s.elements.append(f)                                  # file names in the same folder; the strip lengthens
vse.frame_start, vse.frame_end = 1, s.frame_final_end - 1
vse.render.image_settings.file_format = "FFMPEG"
vse.render.ffmpeg.format, vse.render.ffmpeg.codec = "MPEG4", "H264"
vse.render.filepath = os.path.join(d, "joined")
with bpy.context.temp_override(scene=vse):
    bpy.ops.render.render(animation=True, scene=vse.name)   # -> joined0001-0012.mp4

mv = ed.strips.new_movie(name="movie", filepath=mp4_path, channel=2, frame_start=1)
mv.frame_final_duration                                   # 12
```

`new_image` made a 1-frame `ImageStrip`; after 11 `elements.append` calls it held 12 elements and lasted 12 frames
(`frame_final_end` 13, one past the last frame). The joined MP4 read back with all 12 frames; `new_movie` on it gave a
`MovieStrip` of 12 frames at 24 fps. A scene made with `bpy.data.scenes.new` had no sequence editor (`None`); the
factory startup scene already had one. `[exp: experiments/animation/sequencer_join.py]`

**Scaling.** `fit_method` is an argument of `new_image` and `new_movie` only, not a strip property. A 128 x 96 image in
a 256 x 192 scene got `transform.scale_x` 1.0 with the default `ORIGINAL` (drawn at its own pixel size, a quarter of
the frame) and 2.0 with `FIT`, `FILL` or `STRETCH`. `[exp: experiments/animation/sequencer_join.py]`

## A turntable

The camera parented to an empty at the subject's centre, the empty's Z rotation keyed from 0 at frame 1 to 360
degrees at frame N + 1, keys made LINEAR, and frames 1 to N rendered: frame N + 1 would repeat frame 1, so the loop
closes without a doubled frame. 24 frames gave steps of exactly 15.0 degrees and a full 360.
`[exp: experiments/animation/turntable.py]`

```python
from bpy_extras import anim_utils
pivot = bpy.data.objects.new("Pivot", None); scene.collection.objects.link(pivot)
cam.parent = pivot
cam.location = (R, 0, H)
cam.rotation_euler = (Vector((0, 0, 0)) - Vector((R, 0, H))).to_track_quat("-Z", "Y").to_euler()
pivot.rotation_euler.z = 0;           pivot.keyframe_insert("rotation_euler", index=2, frame=1)
pivot.rotation_euler.z = 2 * math.pi; pivot.keyframe_insert("rotation_euler", index=2, frame=N + 1)
ad = pivot.animation_data
fc = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot).fcurves.find("rotation_euler", index=2)
for kp in fc.keyframe_points:
    kp.interpolation = "LINEAR"
scene.frame_start, scene.frame_end = 1, N
```

`[exp: experiments/animation/turntable.py]` The F-curve is also reachable as `ad.action.fcurves.find(...)` (one-slot
actions still allow it in 4.5) and as `ad.action.layers[0].strips[0].channelbag(ad.action_slot).fcurves`; all three
found it. Past the last key the rotation holds (CONSTANT extrapolation, the default); with `fc.extrapolation =
"LINEAR"` it kept turning (450 degrees six frames after the 360 key). `[exp: experiments/animation/turntable.py]`

| Rig | Step per frame (24 frames) | Radius | Aim error |
|---|---|---|---|
| empty rotated, BEZIER keys (default) | 1.823 first, 22.448 middle | constant | 0 |
| empty rotated, LINEAR keys | 15.0 every frame | constant | 0 |
| Follow Path on a 16-point NURBS circle + Track To, `eval_time` keyed linearly | 15.0 to 15.001 | within 0.84 mm | 0 |
| Follow Path on a 4-point Bezier circle + Track To | 14.998 to 15.002 | within 1.24 mm | 0 |

`[exp: experiments/animation/turntable.py]`

- **Follow Path does not animate by itself.** With only the constraint the camera stayed put between frames 1 and 50:
  the path's `eval_time` has to be keyed (set `curve.path_duration = N`, key `eval_time` 0 at frame 1 and N at
  N + 1, LINEAR). Constraint defaults: `use_curve_follow` False, `forward_axis` FORWARD_Y, `up_axis` UP_Z; the curve's
  `path_duration` 100. `[exp: experiments/animation/turntable.py]`
- **Track To needs no axis setting for a camera.** A constraint made with `constraints.new("TRACK_TO")` starts at
  `TRACK_NEGATIVE_Z` with `UP_Y`; aimed at an empty at the origin, the camera's view was 0.0 degrees off.
  `[exp: experiments/animation/turntable.py]`
- The empty-and-parent rig is the simplest of the three: one F-curve, exact steps, nothing to aim. Rotating the subject
  instead of the camera gives the same frames with fixed lighting moving over it (not measured here).

## Loops and keyed inputs

```python
from bpy_extras import anim_utils

def fcurve(id_block, path, index=0):
    ad = id_block.animation_data
    return anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot).fcurves.find(path, index=index)

# a slide that repeats forever: keys at 1, 25 and 49 (back where it started), then a Cycles modifier
for f, x in ((1, 0.0), (25, 2.0), (49, 0.0)):
    ob.location.x = x; ob.keyframe_insert("location", index=0, frame=f)
fcurve(ob, "location", 0).modifiers.new("CYCLES")     # REPEAT before and after, no limit
ob.animation_data.action.update_tag()                 # needed if the scene was evaluated since the keys were made

# a material's node input: the action is on the node tree
s = mat.node_tree.nodes["Emission"].inputs["Strength"]
s.default_value = 0;  s.keyframe_insert("default_value", frame=1)
s.default_value = 10; s.keyframe_insert("default_value", frame=25)
fcurve(mat.node_tree, 'nodes["Emission"].inputs[1].default_value')

# a Geometry Nodes modifier input: keyed on the object, by the input's identifier
mod[ident] = 1.0; ob.keyframe_insert(data_path=f'modifiers["{mod.name}"]["{ident}"]', frame=1)
```

Measured `[exp: experiments/animation/loops_and_node_keys.py]`:

- With the Cycles modifier (after `update_tag`) frame 61 read 1.0 like frame 13, frame 73 read 2.0 like frame 25,
  frame 97 read 0.0 like frame 1, and frame -11 read 1.0: the 48-frame cycle repeats both ways. Without it the curve
  held 0.0 after frame 49 (extrapolation CONSTANT). `[exp: experiments/animation/loops_and_node_keys.py]`
- The node input's action sat on the node tree (slot `NTShader Nodetree`, path
  `nodes["Emission"].inputs[1].default_value`). Once the material was on a plane in the scene, `frame_set(13)` gave
  5.0 on the original input and on the evaluated copy, and renders of an emission plane at frames 1, 13 and 25 read
  0.0, 5.0 and 10.0. `[exp: experiments/animation/loops_and_node_keys.py]`
- A Geometry Nodes input keyed at 1.0 and 3.0 read 2.0 at frame 13, path `modifiers["GN"]["Socket_2"]`, in the
  object's action; `mod.keyframe_insert('["Socket_2"]')` added a key to the same curve.
  `[exp: experiments/animation/loops_and_node_keys.py]`

## Motion blur

```python
scene.render.use_motion_blur = True        # EEVEE and Cycles; off by default
scene.render.motion_blur_shutter = 0.5     # in frames, centred on the frame (motion_blur_position CENTER)
scene.eevee.motion_blur_steps = 1          # EEVEE only; motion_blur_max 32 px
```

A 1 m square moving 1 m (32 px) per frame, seen from above at 32 px per metre, 64 samples, 256 x 64:
`[exp: experiments/animation/motion_blur.py]`

| Engine | off: lit width | shutter 0.5 | shutter 1.0 |
|---|---|---|---|
| Workbench | 34 px | 34 px (ignored) | 34 px (ignored) |
| EEVEE | 34 px | 50 px | 65 px |
| Cycles (Metal) | 34 px | 48 px | 63 px |

`[exp: experiments/animation/motion_blur.py]` So the smear is about the shutter times the distance moved in a frame.
EEVEE with `motion_blur_steps = 4` gave the same 50 px for this straight-line motion. Blur did not make frames slower at
this size (EEVEE 0.175 s at shutter 0.5 and 0.167 s at 1.0; its first render, without blur, took 0.307 s). `[exp: experiments/animation/motion_blur.py]`

## Render time per frame

A sphere on a plane under an area light, 256 x 256, 5 frames in one `render(animation=True)`, each frame timed between
the `render_pre` and `render_post` handlers. No denoising, no adaptive sampling.
`[exp: experiments/animation/engine_frame_time.py]`

| Engine | first frame | median of frames 2-5 |
|---|---|---|
| Workbench | 0.105 s | 0.007 s |
| EEVEE, 16 samples | 0.168 s | 0.104 s |
| EEVEE, 64 samples | 0.303 s | 0.298 s |
| Cycles CPU, 16 samples | 0.095 s | 0.079 s |
| Cycles CPU, 64 samples | 0.305 s | 0.298 s |
| Cycles Metal, 16 samples | 0.404 s | 0.293 s |
| Cycles Metal, 64 samples | 0.31 s | 0.308 s |
| Cycles Metal, 64 samples, `use_persistent_data` | 0.294 s | 0.098 s |

`[exp: experiments/animation/engine_frame_time.py]` EEVEE's first frame was slower than the rest only in the first
EEVEE run (16 samples); that this is shader compilation was not checked. For a quick preview of motion, Workbench at
0.007 s a frame is two orders of magnitude cheaper than either renderer. `[exp: experiments/animation/engine_frame_time.py]`

## Reference: containers and codecs, measured

24 frames of a moving cube, Workbench, 128 x 128, quality MEDIUM, read back with `bpy.data.movieclips.load`.
`[exp: experiments/animation/video_codecs.py]`

| Container / codec | Extension | Bytes | Frames read back |
|---|---|---|---|
| MPEG4 / H264 | `.mp4` | 2,938 | 24 |
| MPEG4 / H265 | `.mp4` | 4,583 | 24 |
| MPEG4 / AV1 | `.mp4` | 2,724 | 24 |
| MPEG4 / MPEG4 | `.mp4` | 3,078 | 24 |
| MKV / H264 | `.mkv` | 2,757 | 24 |
| MKV / FFV1 (lossless) | `.mkv` | 61,560 | 24 |
| MKV / AV1 | `.mkv` | 12,147 | 24 |
| WEBM / WEBM (VP9) | `.webm` | 2,820 | 24 |
| WEBM / AV1 | `.webm` | 12,073 | 24 |
| QUICKTIME / PRORES | `.mov` | 14,551 | 24 |
| QUICKTIME / QTRLE | `.mov` | 48,286 | 24 |
| QUICKTIME / PNG | `.mov` | 67,359 | 24 |
| QUICKTIME / H264 | `.mov` | 12,308 | 24 |
| OGG / THEORA | `.ogv` | 6,651 | 24 |
| AVI / HUFFYUV | `.avi` | 409,556 | 24 |
| MPEG2 / MPEG2 | `.dvd` | 12,288 | 19 |
| MPEG1 / MPEG1 | `.mpg` | 6,144 | 20 |
| FLASH / FLASH | `.flv` | 4,785 | 24 |
| DV / DV | none | 0 | "Render width has to be 720 pixels for DV!" |

`[exp: experiments/animation/video_codecs.py]` Each encode took about 0.1 to 0.2 s at this size. Why QuickTime/H264
came out four times the size of MP4/H264 was not traced. `bpy.data.images.load` did not recognise the `.dvd` file as a
movie (`source` FILE, 1 frame). `[exp: experiments/animation/video_codecs.py]`

H.264 file size by `constant_rate_factor`, same clip: LOSSLESS 13,392 bytes, PERC_LOSSLESS 4,118, HIGH 3,235, MEDIUM
2,938, LOW 2,758, LOWEST 2,500. `[exp: experiments/animation/video_codecs.py]`
