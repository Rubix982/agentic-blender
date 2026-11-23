# Lessons: rendering, light and camera

From a project that rendered draped garments in Blender 4.5.14 with Cycles (Metal GPU), EEVEE and Workbench, and matched
renders to catalogue photos through a fitted camera and light.

---

### Engine ids and the GPU device in 4.5
**What happens:** EEVEE's engine id in 4.5 is `BLENDER_EEVEE_NEXT`; Cycles uses the GPU only if the add-on's device
preferences are set in the script (factory settings start on the CPU).
**Evidence:** the project's working code: `scene.render.engine = 'BLENDER_EEVEE_NEXT'` with `scene.eevee.taa_render_samples`;
Cycles: `prefs = bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type = 'METAL';
prefs.get_devices()`, `d.use = True` on each, `scene.cycles.device = 'GPU'`, falling back to CPU in an `except`. (not
re-checked here; this repository's harness does the same in `tools/exp.py`)
**What to do:** as above.
**How it was found:** renders that ran on the CPU.

### Path guiding and fewer samples, on a directly lit studio
**What happens:** path guiding (CPU only in 4.5) learns where light comes from to cut indirect noise; on a scene lit
directly there is little to cut, and the CPU is slower than the GPU anyway.
**Evidence:** an 800 x 1200 denoised frame against a 512-sample reference: GPU 32 samples 13.2 s, mean colour error 0.354;
CPU 32 22.4 s, 0.354; CPU guided 32 33.8 s, 0.365; CPU guided 16 19.4 s, 0.407. GPU 16 samples 9.3 s (0.405), 8 7.7 s
(0.469), 4 6.8 s (0.564). The noise was a small part of the look's overall colour error (3-5). (not re-checked here)
**What to do:** GPU with denoising; 16 samples for renders no measure judges.
**How it was found:** timing a look render against its error.

### Workbench with anti-aliasing off gives exact flat id colours
**What happens:** Workbench in flat light with material colours, no shadows or outlines and `render_aa = 'OFF'` renders
every pixel at its object's id colour, with no partial pixels at edges.
**Evidence:** on 7 id pictures of 3 garments no pixel was partly transparent and every shown pixel was within 2 of its id
colour (dither); linear (1, 0.2158, 0) came out as sRGB (255, 128, 0) under the Standard view. Settings used:
`display.shading.light = 'FLAT'`, `color_type = 'MATERIAL'` (or `'VERTEX'` with a FLOAT_COLOR corner attribute set active
and for render), `show_shadows`, `show_cavity`, `show_object_outline` False, `display.render_aa = 'OFF'`,
`film_transparent = True`, `view_transform = 'Standard'`, `look = 'None'`, `exposure = 0`; OPEN_EXR 32-bit for exact
values. (not re-checked here)
**What to do:** pick id colours in linear so they encode to the sRGB values you want; this replaces Cryptomatte for exact
per-object masks.
**How it was found:** checking whether exact masks needed Cryptomatte.

### The Standard view transform gives back a texture's colour; the default does not
**What happens:** under the default view transform (AgX in 4.x) a texture's sRGB is tone-mapped; product colour matching
needs Standard plus a calibrated exposure.
**Evidence:** a bodice rendered at about twice the photo's brightness until exposure was calibrated on a patch against the
photo. (not re-checked here)
**What to do:** `scene.view_settings.view_transform = 'Standard'`; calibrate `exposure` by measuring a patch.
**How it was found:** colour measured against catalogue photos.

### Keep the background the camera sees apart from the light the world casts
**What happens:** a styled world background otherwise lights the scene too.
**Evidence:** used in the project's looks. (not re-checked here)
**What to do:** in the world tree, plug Light Path "Is Camera Ray" into a Mix Shader's factor: the styled Background on
camera rays, a dim neutral Background (0.35 grey, strength 0.4) for lighting.
**How it was found:** a backdrop tinting the cloth.

### A world volume swallows the sun
**What happens:** haze added to the world absorbs a sun light entirely.
**Evidence:** a hazy look lost its sun. (not re-checked here)
**What to do:** put the Volume Scatter (density low, anisotropy about 0.55) on a box mesh around the subject instead.
**How it was found:** a dark render.

### Ray visibility and light linking light metals without changing the cloth
**What happens:** a camera-facing metal mirrors the even sky and reads grey; what real gold mirrors in a studio is the
softboxes.
**Evidence:** sky about 58 % of the fitted light; gold rendered at lightness 57 against the photo's 84. (not re-checked
here)
**What to do:** `world.cycles_visibility.glossy = False` (the sky lights the cloth but is not mirrored); an area light by
the camera with `visible_camera = False` and `visible_diffuse = False` (reflections only); or
`light.light_linking.receiver_collection` set to the metal objects.
**How it was found:** a reviewer's comparison, then measured lightness.

### Camera intrinsics in pixels
**What happens:** with `sensor_fit = 'AUTO'` the 36 mm sensor spans the longer image side, and shift is a fraction of that
side.
**Evidence:** used to fit cameras to photo keypoints: `f_px = lens / 36 * max(W, H)`; `shift_x = px / max(W, H)`
(positive moves the view right, the picture left); `bpy_extras.object_utils.world_to_camera_view` gives y up, so pixel
row = (1 - y) * H; aim with `(target - loc).to_track_quat('-Z', 'Y')`. (not re-checked here)
**What to do:** as above.
**How it was found:** camera registration against photos.

### A render laid over a photo: shadow catcher and transparent film
**What happens:** a floor marked as shadow catcher with the film transparent composites a render into the photo it was
registered to, the photo's own floor taking the shadows.
**Evidence:** 15.8 s for one frame; wherever the render did not cover the subject, the photo showed through. (not
re-checked here)
**What to do:** `obj.is_shadow_catcher = True` on the floor, `scene.render.film_transparent = True`, composite over the
photo.
**How it was found:** a review view.

### Emission bakes write to the active Image Texture node; materials.clear() resets every face to slot 0
**What happens:** `bpy.ops.object.bake` writes into each material's active Image Texture node; clearing the material list
zeroes every face's material index, so all pieces bake into one map.
**Evidence:** four garment pieces written into the front's map. (not re-checked here)
**What to do:** replace materials in place (`me.materials[i] = new_mat`); in each material set the target `TexImage` node
as `nodes.active`; `bpy.ops.object.bake(type='EMIT', uv_layer=..., margin=..., use_clear=True, target='IMAGE_TEXTURES')`
on the CPU. To feed a per-point float to the bake shader, carry it in a UV layer's u.
**How it was found:** a broken bake.

### scene.ray_cast sees viewport-visible evaluated objects, not render-visible ones
**What happens:** `hide_render` does not remove an object from `scene.ray_cast`; the hit object is the evaluated one and
its face index refers to the evaluated mesh.
**Evidence:** hiding helpers by "hidden from renders" did not hide them from rays; every sleeve read 89 % seen. (not
re-checked here)
**What to do:** hide helpers with `hide_viewport` for the cast, compare `hit_obj.original`, map indices through the
evaluated mesh.
**How it was found:** a visibility measure that disagreed with the render.

### A "missing part" check must read the final render
**What happens:** a part can be whole by area or point count and still be hidden in the render (behind a backdrop, inside
another garment).
**Evidence:** a backdrop flattened into a plane hid a walking figure's trailing leg while every geometric check passed.
(not re-checked here)
**What to do:** count the part's own pixels in the final render (render it alone for the reference).
**How it was found:** a reviewer saw the leg missing.
