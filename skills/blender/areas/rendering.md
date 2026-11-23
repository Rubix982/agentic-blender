# Rendering: Cycles, EEVEE, Workbench, output files and colour

Blender 4.5.14 LTS on Apple Silicon (M2 Pro, 16 GB, Metal). Tags: `[inv]` read from Blender (`scripts/kb.py`),
`[exp: path]` measured here (paths relative to the source repository; results next to each script in `results/`),
`[lesson]` from a real project, `[doc: link]` Blender's documentation. Timings are small scenes at 256-512 px with other
Blender jobs sharing the machine; repeated runs moved by up to 2x, the ratios much less.

## What goes wrong most often

1. **The EEVEE engine id.** In 4.5 it is `BLENDER_EEVEE_NEXT`. `scene.render.engine = "BLENDER_EEVEE"` (the 2.8 to 4.1
   id) raises `TypeError: enum "BLENDER_EEVEE" not found in ('BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH', 'CYCLES')`.
   With `--factory-startup` in background mode `HYDRA_STORM` is not in that list either.
   `[exp: experiments/rendering/eevee_background.py]` `[inv]`
2. **EEVEE settings from 4.1 and earlier.** These `scene.eevee` attributes are gone (AttributeError):
   `use_soft_shadows`, `shadow_cube_size`, `shadow_cascade_size`, `use_shadow_high_bitdepth`, `use_ssr`,
   `use_ssr_refraction`, `ssr_quality`, `use_bloom`, `bloom_intensity`, `bloom_threshold`, `use_motion_blur`,
   `gi_auto_bake`, `use_volumetric_lights`, `sss_samples`. Also gone: `material.shadow_method`,
   `light.use_contact_shadow`, `light.contact_shadow_distance`, `light.shadow_buffer_bias`. Motion blur is
   `scene.render.use_motion_blur`; soft shadows come from the light's own size (see `light-world-camera.md`);
   screen-space reflections are `scene.eevee.use_raytracing`. `[exp: experiments/rendering/eevee_background.py]`
3. **Reading enum choices from `bl_rna` for a dynamic enum.** `render.engine`, `cycles.denoiser`,
   `view_settings.view_transform` and `export_scene.gltf(export_format=...)` are filled at run time:
   `bl_rna.properties["denoiser"].enum_items` lists nothing (`[]`), `view_transform`'s lists only `NONE`. Assign a bad
   value inside `try/except TypeError`; the message lists the real ones. `kb.py enums` has them for this machine.
   `[exp: experiments/rendering/cycles_denoisers.py]` `[exp: experiments/rendering/view_transforms.py]`
4. **Expecting the GPU without asking for it.** A fresh file renders Cycles on the CPU. Pick the Metal device in the
   Cycles add-on preferences and set `scene.cycles.device = "GPU"` (code below). On this machine the same scene was
   2.6x faster on the GPU (0.80 s vs 2.08 s). `[exp: experiments/rendering/cycles_metal_vs_cpu.py]`
5. **OptiX, CUDA or OIDN-on-GPU from memory.** On this Mac the only denoiser is `OPENIMAGEDENOISE`; `"OPTIX"` raises
   TypeError. `denoising_use_gpu` defaults to False; it helped only at 512 px (0.73 s vs 0.85 s) and was slower at
   256 px (0.65 s vs 0.45 s). `[exp: experiments/rendering/cycles_denoisers.py]`
6. **Reading pixels from `bpy.data.images["Render Result"]`.** In background mode it has 0 pixels. Save the render
   (`write_still=True`, or `Render Result.save_render(path)`) and read the file.
   `[exp: experiments/rendering/view_transforms.py]` `[exp: experiments/rendering/output_formats.py]`
7. **Assuming 1.0 renders as white.** The default view transform is **AgX**: linear 1.0 becomes byte 197, not 255, and
   pure red (1, 0, 0) becomes (219, 57, 33). For exact colours (UI mock-ups, masks, data images) set
   `scene.view_settings.view_transform = "Standard"`. Mid grey 0.18 is 118 under both.
   `[exp: experiments/rendering/view_transforms.py]`
8. **Expecting an EXR to look like the PNG.** A rendered EXR holds scene-linear values: neither the view transform nor
   `view_settings.exposure` is applied (written 0.5, 0.25, 4.0 for an input of 0.5, 0.25, 4.0 under AgX at +1 EV).
   `[exp: experiments/rendering/view_transforms.py]`
9. **Confusing Workbench with a preview of the material.** Workbench (colour type MATERIAL, the default) draws
   `material.diffuse_color`, the viewport colour, not the node tree's Base Color: a material with red nodes and green
   `diffuse_color` rendered green in Workbench and red in Cycles. `[exp: experiments/rendering/workbench.py]`

## Pick an engine and a device

```python
# Cycles on the Metal GPU (tools/exp.py: exp.metal(), used by every experiment here)
prefs = bpy.context.preferences.addons["cycles"].preferences
for kind in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
    try:
        prefs.compute_device_type = kind
    except TypeError:
        continue
    prefs.get_devices()
    devs = [d for d in prefs.devices if d.type == kind]
    if devs:
        for d in prefs.devices:
            d.use = d.type == kind
        scene.cycles.device = "GPU"
        break
```

`prefs.devices` lists `Apple M2 Pro` (type CPU) and `Apple M2 Pro (GPU - 19 cores)` (type METAL); only the METAL one is
switched on above. `[exp: experiments/running/smoke.py]` `[inv]` The first Metal render of a session took 0.91 s and
the next 0.80 s; the small gap suggests the Metal kernels were already compiled and cached on this machine. GPU and CPU renders with the same seed differ by at
most 0.0085 per pixel: the same noise pattern. Two GPU renders differ by at most 1e-5, so they are not bit-identical.
`[exp: experiments/rendering/cycles_metal_vs_cpu.py]`

EEVEE renders in background mode on macOS. A 256 px frame took 0.07 s at 1 TAA sample, 0.11 s at 16, 0.32 s at 64
(`scene.eevee.taa_render_samples`, default 64); the session's first EEVEE render took 0.35 s, probably shader
compilation.
`[exp: experiments/rendering/eevee_background.py]` Workbench: 0.02 s at 512 px. `[exp: experiments/rendering/workbench.py]`

## Samples, noise and denoising (Cycles)

Defaults in 4.5: `samples` 4096, `use_adaptive_sampling` True, `adaptive_threshold` 0.01, `adaptive_min_samples` 0
(automatic), `use_denoising` True. `[exp: experiments/rendering/cycles_samples_noise.py]` With adaptive sampling on,
the threshold decides the time, not the sample cap: the 4096-sample default took 0.80 s, the same as a 1024 cap.
Measured on a 256 px scene with a gold sphere and one area light, noise as RMSE against a 4096-sample reference:

| samples | adaptive | seconds | RMSE (linear) |
|---|---|---|---|
| 16 | off | 0.31 | 0.126 |
| 64 | off | 0.39 | 0.055 |
| 256 | off | 0.64 | 0.031 |
| 1024 | off | 1.62 | 0.017 |
| 1024 | threshold 0.01 | 0.74 | 0.029 |
| 1024 | threshold 0.05 | 0.40 | 0.087 |
| 4096 | threshold 0.01 (default) | 0.80 | 0.028 |

`[exp: experiments/rendering/cycles_samples_noise.py]` About 0.3 s of each render is fixed cost (sync, BVH, kernel
launch); noise fell by 2.3x from 16 to 64 samples and 1.8x from 64 to 256, near the 2x that 1/sqrt(N) predicts.

Denoising (OpenImageDenoise, quality HIGH, input passes RGB_ALBEDO_NORMAL, prefilter ACCURATE: the defaults) took a
16-sample render from display RMSE 0.0206 to 0.0039 in 0.65 s; 1024 samples without denoising reached 0.0025 in
1.68 s. Display RMSE is measured after clipping to 0..1 and a 2.2 gamma; linear RMSE barely moved (0.126 to 0.090),
which is consistent with the denoiser leaving fireflies brighter than 1 in place, though that was not checked pixel by
pixel. FAST quality: 0.0049; BALANCED: 0.0045. `[exp: experiments/rendering/cycles_denoisers.py]`

```python
scene.cycles.samples = 64
scene.cycles.use_adaptive_sampling = False      # for timing; leave on for production
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPENIMAGEDENOISE"      # the only one on this Mac
scene.cycles.denoising_use_gpu = True           # faster only at larger sizes here
scene.cycles.denoising_quality = "HIGH"         # HIGH, BALANCED, FAST
```

## Light paths (bounces)

Defaults: `max_bounces` 12, `diffuse_bounces` 4, `glossy_bounces` 4, `transmission_bounces` 12, `volume_bounces` 0,
`transparent_max_bounces` 8, `sample_clamp_indirect` 10, `sample_clamp_direct` 0 (off), caustics on, light tree on.
`[exp: experiments/rendering/cycles_light_paths.py]` In a closed white room (albedo 0.8, one point light) the image
kept brightening up to 32 bounces: 0 bounces gave 15 % of the 32-bounce brightness, 4 gave 67 %, 12 gave 95 %. The
default settings landed slightly above "4 bounces of everything" (mean 1.665 vs 1.610) because the Principled BSDF's
specular layer spends glossy bounces on top of the 4 diffuse ones: with `glossy_bounces = 0` the mean fell to 1.453.
For interiors, raise `diffuse_bounces`; the cap is per type, and `max_bounces` caps the total.
`[exp: experiments/rendering/cycles_light_paths.py]`

## Rendering the same scene many times

`scene.render.use_persistent_data` (off by default) keeps the synced scene and BVH between renders. On a 504k-face
scene where only an object's rotation changed between renders, renders after the first took 0.23 s with it on and
0.71 s on average with it off. `[exp: experiments/rendering/cycles_persistent_data.py]`

## EEVEE settings that matter in 4.5

| setting | default | what it does |
|---|---|---|
| `scene.eevee.taa_render_samples` | 64 | "Number of samples per pixel for rendering" |
| `scene.eevee.use_shadows` | True | all shadows on/off |
| `scene.eevee.shadow_ray_count`, `shadow_step_count` | 1, 6 | shadow rays per light; shadow-map samples per ray |
| `scene.eevee.use_raytracing` | False | "Enable the ray-tracing module"; `ray_tracing_method` PROBE or SCREEN (default SCREEN) |
| `scene.eevee.use_fast_gi` | True in a new file (RNA default False) | "faster global illumination technique for high roughness surfaces" |
| `scene.eevee.use_gtao` | False | ambient occlusion, "medium scale indirect shadowing" |
| `scene.eevee.gi_diffuse_bounces` | 3 | times light is reinjected inside light grids |
| `light.use_shadow_jitter` (on PointLight, SunLight, SpotLight, AreaLight) | False | jittered soft shadows; needed for physically sized penumbrae |
| `material.surface_render_method` | DITHERED | `BLENDED` for sorted transparency; `material.blend_method = "BLEND"` still works and maps to BLENDED |

Defaults `[inv]` (`kb.py factory eevee`); removals and `blend_method` mapping `[exp: experiments/rendering/eevee_background.py]`.
Turning on `use_raytracing` changed the image (mean absolute change 0.026 on a chrome sphere) at 0.13 s vs 0.11 s.
`[exp: experiments/rendering/eevee_background.py]`

## Colour management: view transforms and exposure

A new scene: view transform `AgX`, look `None`, exposure 0, gamma 1, display `sRGB`. View transforms in 4.5:
Standard, Khronos PBR Neutral, AgX, Filmic, Filmic Log, False Color, Raw. `[exp: experiments/rendering/view_transforms.py]`
"Filmic is deprecated and is superseded by AgX". `[doc: https://docs.blender.org/manual/en/4.5/render/color_management.html]`

What each does to a known scene-linear colour, as the bytes of an 8-bit PNG (dither off):

| linear in | Standard | AgX (default) | Filmic | Khronos PBR Neutral | Raw |
|---|---|---|---|---|---|
| 0.18 grey | 118 | 118 | 128 | 105 | 46 |
| 0.5 grey | 188 | 170 | 177 | 181 | 128 |
| 1.0 white | 255 | 197 | 206 | 239 | 255 |
| 4.0 | 255 (clipped) | 233 | 242 | 253 | 255 |
| red 1, 0, 0 | 255, 0, 0 | 219, 57, 33 | 206, 0, 0 | 240, 35, 35 | 255, 0, 0 |
| orange 0.8, 0.3, 0.05 | 231, 149, 63 | 197, 140, 82 | 197, 153, 70 | 226, 140, 36 | 204, 77, 13 |

`[exp: experiments/rendering/view_transforms.py]` Exposure is in stops before the transform: under Standard, 0.18 at
+1 EV wrote 162, the same as linear 0.36. AgX contrast looks pivot on mid grey (0.18 stays 118 under High Contrast and
Base Contrast); `AgX - Punchy` darkens it to 88. `[exp: experiments/rendering/view_transforms.py]`

```python
scene.view_settings.view_transform = "Standard"   # exact sRGB; 'AgX' is the default
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0                # stops
scene.render.dither_intensity = 0                 # default 1.0 adds noise to 8-bit output
```

## Writing files

```python
scene.render.image_settings.file_format = "PNG"   # or OPEN_EXR, OPEN_EXR_MULTILAYER, JPEG, TIFF, WEBP, HDR, ...
scene.render.image_settings.color_depth = "16"    # a string; valid values depend on the format
scene.render.image_settings.color_mode = "RGBA"
scene.render.filepath = "/abs/path/frame.png"
bpy.ops.render.render(write_still=True)
# or, after any render: write the Render Result with the current image_settings
bpy.data.images["Render Result"].save_render("/abs/path/again.exr", scene=scene)
```

`save_render` works in background mode. `[exp: experiments/rendering/output_formats.py]` Over a 0..2 linear ramp 1024 px
wide (512 px in 0..1), read back with OpenImageIO:

| format | depths accepted | alpha | stored as | kept above 1.0 | distinct levels in 0..1 (of 512) |
|---|---|---|---|---|---|
| PNG | 8, 16 | yes | uint8 / uint16 | no | 216 / 513 |
| JPEG | 8 | no (BW, RGB only) | uint8 | no | 216 |
| TIFF | 8, 16 | yes | uint8 / uint16 | no | 216 / 513 |
| WEBP | 8 | yes (an all-opaque alpha was not written) | uint8 | no | 152 (lossy) |
| OPEN_EXR, OPEN_EXR_MULTILAYER | 16 (half), 32 (float) | yes | half / float | yes | 1024 |
| HDR | 32 | no | float (RGBE) | yes | 512 |
| DPX | 8, 10, 12, 16 | yes | uint8 / uint16 | no | 256 / 512 / 513 / 513 |
| CINEON | 10 | no | uint16 (log; 1.0 read back as 0.67) | no | 185 |
| JPEG2000 | 8, 12, 16 | yes | uint8 / uint16 / uint16 | no | 216 / 513 / 516 |
| BMP, IRIS, TARGA, TARGA_RAW | 8 | yes | uint8 | no | 216 |

`[exp: experiments/rendering/output_formats.py]` EXR codecs: NONE, ZIP (default), PIZ, DWAA, DWAB, ZIPS, RLE, PXR24, B44,
B44A. JPEG 2000 refused to write an image 8 px tall ("Could not write image: internal error"); 32 px tall worked.
`[exp: experiments/rendering/output_formats.py]`

Reading pixels back: an 8-bit PNG loaded with `bpy.data.images.load` gives `.pixels` equal to its bytes / 255, still
sRGB-encoded (118 for mid grey), not linear. `[exp: experiments/rendering/view_transforms.py]` OpenImageIO is bundled
with Blender's Python (`import OpenImageIO as oiio`; `oiio.ImageBuf(path).get_pixels(oiio.FLOAT)` returns a
(height, width, channels) array, top row first). `[exp: experiments/compositing/multilayer_readback.py]`

## Animation and video

```python
scene.frame_start, scene.frame_end = 1, 10
scene.render.filepath = "/abs/out/frame_###"       # '#' run -> zero-padded frame number there
bpy.ops.render.render(animation=True)
# video
scene.render.image_settings.file_format = "FFMPEG"
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"
scene.render.filepath = "/abs/out/clip"
bpy.ops.render.render(animation=True)              # -> clip0001-0010.mp4
```

A new scene renders frames 1-250 at 24 fps to `/tmp/`. With no `#` in the path a 4-digit frame number is appended
(`frame_0001.png`); `frame_###` gave `frame_001.png`; `f_##_v2` gave `f_01_v2.png`; `use_file_extension = False`
dropped `.png`. FFMPEG defaults to container MKV, codec H264, quality MEDIUM; with MPEG4/H264 a 10-frame range wrote one
file `clip0001-0010.mp4`. `[exp: experiments/rendering/animation_output.py]`

## Reference: render settings that matter

| setting | default (new file) | note |
|---|---|---|
| `scene.render.engine` | `BLENDER_EEVEE_NEXT` | also `CYCLES`, `BLENDER_WORKBENCH` `[inv]` |
| `scene.render.resolution_x/_y`, `resolution_percentage` | 1920, 1080, 100 | `[inv]` |
| `scene.render.film_transparent` | False | alpha background |
| `scene.render.filter_size` | 1.5 px | pixel filter width `[inv]` |
| `scene.render.dither_intensity` | 1.0 | noise added to 8-bit output `[inv]` |
| `scene.render.use_persistent_data` | False | `[exp: experiments/rendering/cycles_persistent_data.py]` |
| `scene.render.threads_mode`, `threads` | AUTO, 12 here | `[inv]` |
| `scene.cycles.device` | CPU | set GPU and pick a device |
| `scene.cycles.samples`, `use_adaptive_sampling`, `adaptive_threshold` | 4096, True, 0.01 | |
| `scene.cycles.time_limit` | 0 (off) | stops sampling after N seconds, render time only `[doc: https://docs.blender.org/manual/en/4.5/render/cycles/render_settings/sampling.html]` |
| `scene.cycles.use_denoising`, `denoiser` | True, OPENIMAGEDENOISE | |
| `scene.cycles.film_exposure` | 1.0 | "Image brightness scale", a multiplier, separate from the view's exposure in stops `[inv]`; not measured here |
| `scene.view_settings.view_transform` | AgX | |
| `scene.display.shading.light`, `color_type` | STUDIO, MATERIAL | Workbench `[exp: experiments/rendering/workbench.py]` |
