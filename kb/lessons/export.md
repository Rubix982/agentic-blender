# Lessons: exporting and saving

From a project that exported draped garments as glTF (GLB), Alembic and USD, and saved .blend asset files for others, in
Blender 4.5.14.

---

### glTF takes colour from the Principled Base Color only, and a factor stops at 1
**What happens:** the glTF exporter reads a plain graph (Principled + Image Texture + UV Map); colour gains, Math or
Mapping nodes that transform UVs, and factors above 1 do not reach the file. Height maps (relief) are not exported as
such.
**Evidence:** an exported garment's colour map was its plain ground (median 214, 204, 202) while the colour the look had
fitted (error 6.95 -> 2.92) was in no exported file; its relief and metal maps existed only in the .blend, so in the GLB the
embroidery was flat and the gold was cloth. Converting each piece's height map into a tangent-space normal map on the GLB's
own UV (strength 0.6, 1.5 mm) and wiring the metal map gave 8 materials a normal map and 9 metal, 14.0 -> 18.7 MB. (not
re-checked here)
**What to do:** bake gains into the colour texture (encode back to sRGB, clip); bake UV transforms into a plain UV layer;
for export, swap each material for Principled + Image Texture + UV Map (`uv_map='tex'`), data maps in Non-Color, a Normal
Map node in tangent space; copy Alpha and Transmission Weight for sheer cloth; swap the originals back afterwards.
**How it was found:** an asset that did not carry the look.

### glTF and Blender agree on normal maps; Blender's image row 0 is v = 0
**What happens:** both use green-up (OpenGL) normal maps, and Blender image rows run bottom-up with v; drawings indexed
top-down need flipping.
**Evidence:** unflipped, every embroidered element landed on the rows below. (not re-checked here)
**What to do:** generate normal maps green-up; compute v-derivatives with row 0 at v = 0; flip y for anything drawn from
the top.
**How it was found:** misplaced elements.

### export_apply exports a live cloth modifier's current state: remove the cloth first
**What happens:** `export_apply=True` evaluates modifiers, so a cloth modifier still on the stack is exported as whatever
frame it shows.
**Evidence:** the project removed the CLOTH modifier first ("the rest drape exports as it shows"), selected garments and
rig, ran `bpy.ops.export_scene.gltf(filepath=..., export_format='GLB', use_selection=True, export_apply=True,
export_skins=True, export_animations=False, export_yup=True)`, then re-added the cloth setup. (not re-checked here)
**What to do:** as above.
**How it was found:** building exportable assets.

### Alembic and USD export a simulated clip in seconds, and read back exactly
**What happens:** a scene holding every cloth frame in memory exports to Alembic or USD quickly.
**Evidence:** a 129-frame walk: Alembic 1.3 s (37.3 MB), USD 2.1 s (15.1 MB); the Alembic read back moved the garment
exactly as the scene did (366.8, 1185.6, 1306.5 mm from frame 61 at frames 81, 101, 129). (not re-checked here)
**What to do:** `bpy.ops.wm.alembic_export` / `bpy.ops.wm.usd_export` after the cloth is simulated or baked.
**How it was found:** testing an animated-asset export.

### UV layouts export as SVG in a fraction of a second
**What happens:** the bundled UV layout exporter writes a mesh's UV islands as SVG or PNG headless.
**Evidence:** one SVG per garment in 0.04-0.05 s (747 KB and 459 KB). (not re-checked here)
**What to do:** `bpy.ops.uv.export_layout` with the object in edit mode (or a context override).
**How it was found:** an asset file for painters.

### A saved .blend carries absolute paths in places its path settings do not reach
**What happens:** a .blend kept the machine's home path in five places after "make paths relative": image `filepath` and
`filepath_raw` even when packed; each packed file's own record (`image.packed_files[...].filepath`); the render output
path and a file browser's folder in the saved interface, both fixed-size character fields that keep the old path's bytes
after the terminator when shorter text is written; and the preview's metadata stamp.
**Evidence:** a scrub found the home path 34 times in one .blend and once in its preview PNG (6 times in the raw compressed
bytes); 24 of 25 path fields absolute, 12 packed records, 8 custom properties. After the fixes the scrub found nothing and
the files reopened with their 12 maps packed. (not re-checked here)
**What to do:** write `'/' * 1023` then `'//'` into `render.filepath` (`'/' * 767` for a file browser's `params.directory`);
`bpy.ops.file.make_paths_relative()` and `bpy.ops.file.pack_all()`; set each packed file's `filepath` to the image's
relative path; turn the filename stamp off; `bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True,
do_recursive=True)`; save; then scan the saved bytes (decompressed) for your home path. A background job could not remove
workspaces in 4.5.
**How it was found:** a scrub of a file meant for others.

### Saving over a .blend leaves a .blend1 backup each time
**What happens:** Blender keeps the previous version beside the new one.
**Evidence:** 9.7 MB extra each time. (not re-checked here)
**What to do:** remove the old file before `bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)`; setting
`preferences.filepaths.save_version = 0` should also prevent it (not tested by the project).
**How it was found:** disk use.

### Marking assets for the Asset Browser from a script
**What happens:** the catalogue tree shows only paths written to the catalogue file, parents included.
**Evidence:** working sequence: write `<library>/blender_assets.cats.txt` (`VERSION 1`, lines `uuid:path:simple-name`, every
parent path too); `idb.asset_mark()`, `idb.asset_data.catalog_id = uuid`, `asset_data.tags.new(t, skip_if_exists=True)`;
a preview with `bpy.ops.ed.lib_id_load_custom_preview(filepath=...)` under `temp_override(id=idb)`. (not re-checked here)
**What to do:** verify by reopening in a fresh `--factory-startup` Blender.
**How it was found:** assets that did not show in their catalogue.

### Third-party glTF packs disagree on units, heads and layout
**What happens:** downloaded asset packs come in mm, cm, m, or a rig scaled to 3 mm, with display heads, one style or a
grid of twelve, and stray pieces.
**Evidence:** about fifty hair glTFs; a fragment fitted as a style came out at twice the scale. (not re-checked here)
**What to do:** fit by measurements taken on your own model, never the file's numbers; keep the first UV layer (where
alpha maps live); keep the importer's up-axis rotation.
**How it was found:** importing a hair library.
