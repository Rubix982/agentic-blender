# Export, import and texture baking

Blender 4.5.14 LTS on Apple Silicon. Tags: `[inv]` read from Blender (`scripts/kb.py`), `[exp: path]` measured here
(paths relative to the source repository), `[lesson]` from a real project, `[doc: link]` Blender's documentation.
Round trips used each exporter's and importer's defaults unless a parameter is shown.

## What goes wrong most often

1. **Exporter names from 2.x/3.x.** `bpy.ops.export_scene.obj`, `import_scene.obj`, `export_mesh.stl`,
   `import_mesh.stl`, `export_mesh.ply`, `import_mesh.ply` do not exist: calling one raises
   `AttributeError: Calling operator "bpy.ops.export_scene.obj" error, could not be found`. The 4.5 operators:
   `wm.obj_export` / `wm.obj_import`, `wm.stl_export` / `wm.stl_import`, `wm.ply_export` / `wm.ply_import`,
   `wm.usd_export` / `wm.usd_import`, `export_scene.fbx` / `import_scene.fbx` (4.5 also has a new `wm.fbx_import`),
   `export_scene.gltf` / `import_scene.gltf`; `wm.collada_export` still exists. `[exp: experiments/export/formats_roundtrip.py]`
2. **Procedural textures in a glTF.** A Noise texture into Base Color was dropped without a warning in the file: the
   material had no `baseColorTexture` and no `baseColorFactor`, which glTF reads as white, and it imported back white.
   Bake procedural inputs to images first (below). `[exp: experiments/export/gltf_materials.py]`
3. **Modifiers missing from a glTF.** `export_apply` defaults to False: a cube with a level-2 Subdivision modifier
   exported 24 vertices, and 384 with `export_apply=True`. (OBJ, STL and PLY apply modifiers by default:
   `apply_modifiers` True `[inv]`.) `[exp: experiments/export/gltf_materials.py]`
4. **Baking without an active Image Texture node.** `bpy.ops.object.bake` writes into the *active* Image Texture node of
   each material (`nt.nodes.active = node`). With none it did not raise; it returned `{'CANCELLED'}` and baked nothing.
   Check the return value. Without a UV map it raised `RuntimeError: No active UV layer found in the object "Plane"`;
   under EEVEE, `Current render engine does not support baking`; with no active object, `poll() failed, context is
   incorrect`. `[exp: experiments/export/cycles_bake.py]`
5. **Losing the bake.** The baked image lives in memory (`is_dirty` True; the log says "Baking map saved to internal
   image, save it externally or pack it"). Set `filepath_raw` and `file_format`, then `image.save()`.
   `[exp: experiments/export/cycles_bake.py]` `[exp: experiments/export/bake_procedural_for_gltf.py]`
6. **OBJ round trips that change the scene.** On re-import each object came back rotated (90, 0, 0) with its own
   rotation and scale baked into the vertices, colour attributes were dropped (`export_colors` False by default), and an
   object with no material picked up the previous object's material ("Red"). `[exp: experiments/export/formats_roundtrip.py]`
7. **STL and PLY merge everything.** Both imported as one object named after the file (`scene`), holding both meshes.
   `[exp: experiments/export/formats_roundtrip.py]`

## glTF 2.0

```python
bpy.ops.export_scene.gltf(filepath=path, export_format="GLB")    # or 'GLTF_SEPARATE' (.gltf + .bin + images)
bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", export_apply=True)   # apply modifiers
bpy.ops.import_scene.gltf(filepath=path)
```

`export_format` accepts only `GLB` and `GLTF_SEPARATE` here (a dynamic enum; the TypeError for a bad value lists them).
`[exp: experiments/export/gltf_materials.py]` Other defaults worth knowing: `export_yup` True, `use_selection` False,
`export_materials` EXPORT, `export_image_format` AUTO, `export_cameras` False, `export_lights` False,
`export_animations` True, `export_draco_mesh_compression_enable` False. `[inv]` (`kb.py op export_scene.gltf`)

What a Principled BSDF becomes (read from the GLB's JSON):

| Blender | glTF | came back on import |
|---|---|---|
| Base Color (0.8, 0.2, 0.1) | `baseColorFactor` [0.8, 0.2, 0.1, alpha] (linear) | (0.8, 0.2, 0.1) |
| Metallic 0.3, Roughness 0.6 | `metallicFactor`, `roughnessFactor` | yes |
| Alpha 0.5 | `alphaMode` BLEND, alpha in `baseColorFactor` | `surface_render_method` BLENDED |
| Emission Color (0, 1, 0), Strength 2 | `emissiveFactor` [0, 1, 0] + `KHR_materials_emissive_strength` 2 | strength 2.0 |
| Coat Weight 0.7 | `KHR_materials_clearcoat` 0.7 | 0.7 |
| Transmission Weight 0.2 | `KHR_materials_transmission` 0.2 | 0.2 |
| IOR 1.7 | `KHR_materials_ior` 1.7 | |
| Specular IOR Level 0.8 | `KHR_materials_specular` `specularColorFactor` [1.6, 1.6, 1.6] (2x) | |
| Sheen Weight 0.4 | `KHR_materials_sheen` `sheenColorFactor` [1, 1, 1]: the weight is lost | Sheen Weight 1.0 |
| Image Texture -> Base Color | `baseColorTexture`, image embedded as PNG | Image Texture node |
| Normal Map node + image | `normalTexture` | Normal Map node |
| Noise Texture -> Base Color | nothing | Base Color white (1, 1, 1) |

Every material was written `doubleSided` true. `[exp: experiments/export/gltf_materials.py]` The glTF add-on's manual
lists what it can export: "Base Color, Metallic, Roughness, Baked Ambient Occlusion, Normal Map (tangent space, +Y up),
Emissive" and extension materials. `[doc: https://docs.blender.org/manual/en/4.5/addons/import_export/scene_gltf2.html]`

Geometry and transforms: an object at Blender (9, 0, 3) sat at glTF (9, 3, 0) (Y up). glTF mesh names are the mesh
datablock names (`Cube.003`), and an applied mesh was renamed `Mesh`. `[exp: experiments/export/gltf_materials.py]` On
import, rotations come back as quaternions (`rotation_euler` stays 0; read `matrix_world`), meshes are triangulated and
split at seams (an 8-vertex box came back with 24 vertices, 12 triangles), and a colour attribute comes back as
`Color` (plus a `Color.001`) with Base Color fed from a MIX node that multiplies the factor by it.
`[exp: experiments/export/formats_roundtrip.py]`

## Bake a procedural material so a glTF keeps it

```python
def bake_to(name, kind, colorspace, **kw):
    img = bpy.data.images.new(name, 256, 256)
    img.colorspace_settings.name = colorspace
    node = nt.nodes.new("ShaderNodeTexImage")
    node.image = img
    nt.nodes.active = node                       # the bake target
    r = bpy.ops.object.bake(type=kind, margin=8, **kw)
    img.filepath_raw = E.out(f"{name}.png")     # E.out(): a file path in the experiment's results folder
    img.file_format = "PNG"
    img.save()
    return node, r

col_node, r1 = bake_to("basecolor", "DIFFUSE", "sRGB", pass_filter={"COLOR"})
rough_node, r2 = bake_to("roughness", "ROUGHNESS", "Non-Color")
nt.links.new(col_node.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(rough_node.outputs["Color"], bsdf.inputs["Roughness"])
for n in (noise, ramp):
    nt.nodes.remove(n)
bpy.ops.export_scene.gltf(filepath=path, export_format="GLB")
```

Before this, the scene needs Cycles (`scene.render.engine = "CYCLES"`), the object selected and active, and a UV map
(a UV sphere has one). Both bakes returned `{'FINISHED'}`; the GLB then carried `baseColorTexture` and
`metallicRoughnessTexture`, both embedded PNGs (183 kB for two 256 px images). One sample is enough for a colour-only
bake. `[exp: experiments/export/bake_procedural_for_gltf.py]` The glTF manual recommends the same for normals: bake
type Normal with the default space settings (Tangent, +X, +Y, +Z).
`[doc: https://docs.blender.org/manual/en/4.5/addons/import_export/scene_gltf2.html]`

## Cycles baking

```python
scene.render.engine = "CYCLES"
img = bpy.data.images.new("baked", 128, 128, float_buffer=True)
node = nt.nodes.new("ShaderNodeTexImage")
node.image = img
nt.nodes.active = node
bpy.ops.object.select_all(action="DESELECT")
plane.select_set(True)
bpy.context.view_layer.objects.active = plane
r = bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"}, margin=4)
```

`[exp: experiments/export/cycles_bake.py]` "Baking requires a mesh to have a UV map, and either a Color Attribute or an
Image Texture node with an image to be baked to. The Active Image Texture node or Color Attribute is used as the baking
target." `[doc: https://docs.blender.org/manual/en/4.5/render/cycles/baking.html]`

What each bake wrote, on a plane with Base Color (0.8, 0.2, 0.1) and a cube floating above it, sun 3 W/m2, world 0.2
grey, 32 samples on Metal at 128 px:

| type | pass_filter | texel | time |
|---|---|---|---|
| DIFFUSE | {'COLOR'} | (0.77, 0.19, 0.10): albedo after the specular layer's share; (0.8, 0.2, 0.1) with Specular IOR Level 0 | 0.3-0.5 s |
| DIFFUSE | {'DIRECT', 'INDIRECT', 'COLOR'} | open (0.91, 0.22, 0.11), under the cube (0.29, 0.02, 0.01) | 0.5 s |
| NORMAL | (normal_space TANGENT) | (0.5, 0.5, 1.0) on a flat face | 0.2 s |
| AO | | 0.97 open, 0.47 next to the cube | 0.3 s |
| COMBINED | | | 0.5 s |

`[exp: experiments/export/cycles_bake.py]` Bake types in 4.5: COMBINED, AO, SHADOW, POSITION, NORMAL, UV, ROUGHNESS,
EMIT, ENVIRONMENT, DIFFUSE, GLOSSY, TRANSMISSION. `[inv]` "If only Color is selected you get the pass color, which is
a property of the surface and independent of sampling refinement." `[doc: https://docs.blender.org/manual/en/4.5/render/cycles/baking.html]`

Settings: `bpy.ops.object.bake(type=...)` overrides `scene.cycles.bake_type` (default COMBINED); margin and the rest live
on `scene.render.bake` (margin 16 px, margin_type ADJACENT_FACES, use_clear True, target IMAGE_TEXTURES, normal_space
TANGENT). Samples come from `scene.cycles.samples`. `[exp: experiments/export/cycles_bake.py]`

## Other formats: what survives a round trip

Source: a box (2 x 2 x 2 m cube at (1, 2, 3), rotated 30 degrees about Z, scale (1, 1, 0.5)) with UVs, a material
"Red" (base colour 0.8, 0.05, 0.05) and a byte colour attribute "Col"; and a UV sphere "Ball" with no material.
`[exp: experiments/export/formats_roundtrip.py]`

| format (operators) | objects back | transforms | UVs | material, base colour | colour attribute | geometry |
|---|---|---|---|---|---|---|
| OBJ (`wm.obj_export`, `wm.obj_import`) | Box, Ball | positions kept; each object rotated (90, 0, 0), own rotation and scale baked into vertices | UVMap | Red (0.8, 0.05, 0.05) via MTL; Ball also got Red | dropped | quads kept |
| STL (`wm.stl_export`, `wm.stl_import`) | one object "scene" | baked | none | none | none | triangles, shared vertices merged (122 v, 236 tris) |
| PLY (`wm.ply_export`, `wm.ply_import`) | one object "scene" | baked | UVMap | none | Col | quads kept; vertices split at UV seams (165) |
| FBX (`export_scene.fbx`, `import_scene.fbx`) | Box, Ball | kept as transforms (rotation 30, scale 0.5) | UVMap | Red (0.8, 0.05, 0.05) | Col | unchanged (8 v, 6 faces) |
| USD .usdc (`wm.usd_export`, `wm.usd_import`) | BoxMesh, Sphere (mesh data names) + an empty | kept | renamed `st` | Red (0.8, 0.05, 0.05) | Col | unchanged |
| glTF .glb (`export_scene.gltf`, `import_scene.gltf`) | Box, Ball | kept (as quaternions) | UVMap | Red, Base Color linked from a MIX with the colour attribute | `Color`, `Color.001` | triangulated, split (Box 24 v) |

`[exp: experiments/export/formats_roundtrip.py]`

## Reference: exporter defaults that bite

| operator | parameter | default | `[inv]` |
|---|---|---|---|
| `export_scene.gltf` | `export_apply` | False | modifiers not applied |
| `export_scene.gltf` | `export_yup` | True | |
| `export_scene.gltf` | `use_selection` | False | whole scene |
| `export_scene.gltf` | `export_cameras`, `export_lights` | False, False | |
| `wm.obj_export` | `forward_axis`, `up_axis` | NEGATIVE_Z, Y | |
| `wm.obj_export` | `apply_modifiers`, `export_selected_objects` | True, False | |
| `wm.obj_export` | `export_colors`, `export_materials`, `path_mode` | False, True, AUTO | |
| `wm.stl_export` | `ascii_format`, `use_batch`, `global_scale` | False, False, 1.0 | `forward_axis` Y, `up_axis` Z |
| `wm.ply_export` | `export_normals`, `export_colors`, `ascii_format` | False, SRGB, False | |
| `wm.usd_export` | `export_materials`, `generate_preview_surface`, `export_textures` | True, True, False | |
| `wm.usd_export` | `rename_uvmaps`, `evaluation_mode`, `root_prim_path` | True, RENDER, /root | |
| `wm.usd_export` | `convert_orientation` | False | |
| `export_scene.fbx` | parameters | `kb.py op export_scene.fbx` | |

Full parameter lists: `kb.py op wm.obj_export` and so on. `[inv]` Format pages in the manual:
`[doc: https://docs.blender.org/manual/en/4.5/files/import_export/obj.html]`,
`[doc: https://docs.blender.org/manual/en/4.5/files/import_export/usd.html]`,
`[doc: https://docs.blender.org/manual/en/4.5/files/import_export/stl.html]`,
`[doc: https://docs.blender.org/manual/en/4.5/files/import_export/ply.html]`,
`[doc: https://docs.blender.org/manual/en/4.5/addons/import_export/scene_fbx.html]`.
