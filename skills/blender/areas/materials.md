# Materials and shader nodes

Blender 4.5.14 LTS on Apple Silicon. Tags: `[inv]` read from Blender (`scripts/kb.py`), `[exp: path]` measured here
(paths relative to the source repository), `[lesson]` from a real project, `[doc: link]` Blender's documentation.
Shader values were measured by rendering them as emission with the Raw view transform into a float EXR, so the number
read back is the number the shader saw.

## What goes wrong most often

1. **Principled BSDF input names from 3.x.** These raise `KeyError` in 4.5: `Subsurface`, `Subsurface Color`,
   `Specular`, `Sheen`, `Clearcoat`, `Clearcoat Roughness`, `Clearcoat Normal`, `Transmission`,
   `Transmission Roughness`, `Emission`. Their 4.5 names: `Subsurface Weight`, `Specular IOR Level`, `Sheen Weight`,
   `Coat Weight`, `Coat Roughness`, `Coat Normal`, `Transmission Weight`, `Emission Color`. `Specular Tint` and
   `Sheen Tint` still exist but are now colours, not floats. `[exp: experiments/materials/principled_bsdf.py]`
2. **Principled inputs by index.** The order changed: `inputs[6]` is now a hidden `Weight` socket, `inputs[9]` is
   `Subsurface Radius` (was Roughness in 3.x), `inputs[21]` is `Coat IOR` (was Alpha). Use names.
   `[exp: experiments/materials/principled_bsdf.py]`
3. **A material that should glow and doesn't.** `Emission Strength` defaults to 0.0, so setting only `Emission Color`
   gives nothing: the render read (0, 0, 0); with strength 5 it read (5.0, 1.0, 0.25) for colour (1, 0.2, 0.05).
   `[exp: experiments/materials/principled_bsdf.py]`
4. **Finding the shader by name.** Node names follow the UI language. Look up by type:
   `next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")`. `[exp: experiments/materials/principled_bsdf.py]`
5. **Expecting a node tree on a new material.** `bpy.data.materials.new()` gives `use_nodes` False and `node_tree`
   None; `use_nodes = True` creates Principled BSDF -> Material Output. `[exp: experiments/materials/principled_bsdf.py]`
6. **Colour on `material.diffuse_color`.** That is the viewport colour, drawn by Workbench; Cycles and EEVEE use the
   node tree. `[exp: experiments/rendering/workbench.py]`
7. **Musgrave Texture.** `nodes.new("ShaderNodeTexMusgrave")` raises `RuntimeError: Node type ShaderNodeTexMusgrave
   undefined`. Its types live in Noise Texture's `noise_type` (FBM, MULTIFRACTAL, RIDGED_MULTIFRACTAL,
   HYBRID_MULTIFRACTAL, HETERO_TERRAIN). `[exp: experiments/materials/procedural_textures.py]` "The Dimension input was
   replaced by a Roughness input, where Roughness = Lacunarity^(-Dimension). The Detail input value must be subtracted
   by 1 compared to the old Musgrave Texture node."
   `[doc: https://docs.blender.org/manual/en/4.5/render/shader_nodes/textures/musgrave.html]`
8. **Data maps left in sRGB.** An 8-bit PNG loads as `sRGB`, so byte 128 reaches the shader as 0.218; under
   `Non-Color` it is 0.502. Normal, roughness, metallic, height and mask maps need
   `image.colorspace_settings.name = "Non-Color"`. The old name `"Linear"` raises TypeError; it is
   `"Linear Rec.709"`. `[exp: experiments/materials/image_textures.py]`
9. **`material.cycles.displacement_method`.** In 4.5 it is `material.displacement_method` (BUMP, DISPLACEMENT, BOTH;
   default BUMP); `material.cycles` has no such attribute. With BUMP a displacement output only shades: the silhouette
   stays flat. `[exp: experiments/materials/displacement.py]`
10. **Textures on Object or Generated coordinates with unapplied scale.** Generated runs 0..1 over the bounding box
    and Object gives local coordinates, so both ignore object scale: a texture stretches with it. UV does too, unless
    the UVs match the scaled shape. `[exp: experiments/materials/texture_coordinates.py]`

## Make a material and set the Principled BSDF

```python
m = bpy.data.materials.new(name)
m.use_nodes = True
b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
b.inputs["Base Color"].default_value = (*color, 1)      # RGBA, scene-linear
b.inputs["Roughness"].default_value = rough
b.inputs["Metallic"].default_value = metal
obj.data.materials.append(m)                             # a slot on the mesh data
```

`[exp: experiments/rendering/cycles_metal_vs_cpu.py]` A new Principled BSDF, whether made by `use_nodes` or by
`nodes.new("ShaderNodeBsdfPrincipled")`, uses `distribution` MULTI_GGX and `subsurface_method` RANDOM_WALK, though the
inventory's RNA defaults read GGX and BURLEY. `[exp: experiments/materials/principled_bsdf.py]` `[inv]`

Base Color is not the diffuse albedo you get back: a Base Color of (0.8, 0.2, 0.1) baked as a diffuse colour pass read
(0.77, 0.19, 0.10) because the specular layer takes its share; with `Specular IOR Level` 0 it read (0.8, 0.2, 0.1).
`[exp: experiments/export/cycles_bake.py]`

## Procedural textures

Texture node types in 4.5: Brick, Checker, Coord (Texture Coordinate), Environment, Gabor (new in 4.3), Gradient, IES,
Image, Magic, Noise, PointDensity, Sky, Voronoi, Wave, WhiteNoise, all `ShaderNodeTex*`.
`[exp: experiments/materials/procedural_textures.py]`

```python
noise = nt.nodes.new("ShaderNodeTexNoise")
noise.noise_type = "RIDGED_MULTIFRACTAL"     # FBM is the default
tc = nt.nodes.new("ShaderNodeTexCoord")
nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
nt.links.new(noise.outputs["Fac"], em.inputs["Color"])
```

What each texture's scalar output covers over a 2 m plane, Object coordinates, default settings
(`[exp: experiments/materials/procedural_textures.py]`, contact sheet `results/procedural_textures-sheet.png`):

| texture | output | min | mean | max |
|---|---|---|---|---|
| Noise FBM | Fac | 0.25 | 0.50 | 0.74 |
| Noise RIDGED_MULTIFRACTAL | Fac | 0.00 | 0.06 | 0.58 |
| Noise HETERO_TERRAIN | Fac | -0.73 | -0.01 | 0.73 |
| Voronoi F1 | Distance | 0.04 | 0.53 | 1.12 |
| Wave (bands, sine) | Fac | 0.01 | 0.50 | 0.99 |
| Gabor | Value | 0.11 | 0.50 | 0.89 |
| Magic | Fac | 0.10 | 0.50 | 0.93 |
| Brick | Fac | 0 | 0.21 | 1 |
| Checker | Fac | 0 | 0.50 | 1 |
| Gradient (linear) | Fac | 0 | 0.25 | 0.99 (clamped below 0 on the -x half) |
| White Noise | Value | 0.02 | 0.50 | 0.96 |

Feed a Color Ramp (`ShaderNodeValToRGB`) when a texture's range is narrow (Noise FBM spans only about 0.25-0.75).

Modes and sockets in 4.5 (`[exp: experiments/materials/procedural_textures.py]`):

| node | modes | inputs (shown by default) | outputs |
|---|---|---|---|
| Noise | `noise_dimensions` 1D-4D (3D); `noise_type` (FBM); `normalize` (True) | Vector, Scale, Detail, Roughness, Lacunarity, Distortion; W, Offset, Gain appear when used | Fac, Color |
| Voronoi | `voronoi_dimensions` (3D); `feature` F1, F2, SMOOTH_F1, DISTANCE_TO_EDGE, N_SPHERE_RADIUS; `distance` EUCLIDEAN, MANHATTAN, CHEBYCHEV, MINKOWSKI; `normalize` (False) | Vector, Scale, Detail, Roughness, Lacunarity, Randomness | Distance, Color, Position |
| Wave | `wave_type` BANDS, RINGS; `bands_direction` X, Y, Z, DIAGONAL; `wave_profile` SIN, SAW, TRI | Vector, Scale, Distortion, Detail, Detail Scale, Detail Roughness, Phase Offset | Color, Fac |
| Gabor | `gabor_type` 2D, 3D | Vector, Scale, Frequency, Anisotropy, Orientation | Value, Phase, Intensity |
| Gradient | `gradient_type` LINEAR, QUADRATIC, EASING, DIAGONAL, SPHERICAL, QUADRATIC_SPHERE, RADIAL | Vector | Color, Fac |
| Brick | | Vector, Color1, Color2, Mortar, Scale, Mortar Size, Mortar Smooth, Bias, Brick Width, Row Height | Color, Fac |
| Checker | | Vector, Color1, Color2, Scale | Color, Fac |
| Magic | | Vector, Scale, Distortion | Color, Fac |
| White Noise | `noise_dimensions` | Vector | Value, Color |

A Checker with Scale 1 on Generated coordinates (0..1) is one square: the whole surface was Color2. Scale 2 gives the
first edge at the middle. `[exp: experiments/camera/camera_aim_dof.py]`

## Texture coordinates and mapping

On a 2 m plane scaled (3, 1.5, 1) without applying, read at its corners `[exp: experiments/materials/texture_coordinates.py]`:

| output | bottom-left | top-right |
|---|---|---|
| Generated | (0.01, 0.03, 0.5) | (0.99, 0.98, 0.5) |
| Object | (-0.97, -0.95, 0) | (0.98, 0.95, 0) |
| UV | (0.01, 0.03, 0) | (0.99, 0.98, 0) |
| UV -> Mapping POINT, Scale 2 | (0.03, 0.05, 0) | (1.98, 1.95, 0) |
| UV -> Mapping TEXTURE, Scale 2 | (0.01, 0.01, 0) | (0.49, 0.49, 0) |

Mapping `POINT` (the default) multiplies by Scale, so the texture repeats more; `TEXTURE` applies the inverse, so the
texture grows. Texture Coordinate outputs: Generated, Normal, UV, Object, Camera, Window, Reflection; Mapping types
POINT, TEXTURE, VECTOR, NORMAL with inputs Vector, Location, Rotation, Scale.
`[exp: experiments/materials/texture_coordinates.py]`

## Image textures and colour space

```python
img = bpy.data.images.load(png)                          # check_existing=True returns an already-loaded one
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = img
nt.links.new(tex.outputs["Color"], em.inputs["Color"])
img.colorspace_settings.name = "Non-Color"               # for data maps
```

`[exp: experiments/materials/image_textures.py]` A PNG pixel (128, 64, 255) reached the shader as (0.218, 0.052, 1.02)
under sRGB and (0.502, 0.249, 1.006) under Non-Color or Linear Rec.709 (within 2 % of the exact sRGB decode and
byte / 255; one sample on an 8 px render). An 8-bit PNG loads as `sRGB`, an EXR as `Linear Rec.709`; `alpha_mode`
defaults to STRAIGHT. Image Texture node defaults: interpolation Linear (also Closest, Cubic, Smart), projection FLAT,
extension REPEAT (also EXTEND, CLIP, MIRROR). `image.pack()` embeds the file in the .blend.
`bpy.data.images.new(name, w, h)` makes a GENERATED image in sRGB; `float_buffer=True` makes it Linear Rec.709.
`[exp: experiments/materials/image_textures.py]` The colour spaces available: `kb.py enums`. `[inv]`

## Bump, normal map and displacement

```python
m.displacement_method = "DISPLACEMENT"      # BUMP (default), DISPLACEMENT, BOTH; on the Material in 4.5
disp = nt.nodes.new("ShaderNodeDisplacement")
disp.inputs["Midlevel"].default_value = 0.0
disp.inputs["Scale"].default_value = 0.2    # height 0..1 -> 0..0.2 m along the normal
nt.links.new(wave.outputs["Fac"], disp.inputs["Height"])
nt.links.new(disp.outputs["Displacement"], out.inputs["Displacement"])
```

On a 2 m grid with 200 x 200 faces, an orthographic side view measured the silhouette's top at 0 mm with BUMP and
200 mm with DISPLACEMENT and BOTH, in Cycles and in EEVEE. Displacement moves existing vertices, so the mesh must be
dense (or subdivided). `[exp: experiments/materials/displacement.py]`

Sockets: Displacement node Height, Midlevel (0.5), Scale (1.0), Normal, `space` OBJECT; Bump node Strength (1.0),
Distance (0.001), Filter Width (0.1), Height, Normal, `invert` False; Normal Map node Strength, Color, `space` TANGENT
(also OBJECT, WORLD, BLENDER_OBJECT, BLENDER_WORLD). Wire Bump's or Normal Map's Normal output into the Principled
BSDF's Normal input; a tangent-space normal map needs a UV map and a Non-Color image.
`[exp: experiments/materials/displacement.py]` The shading difference between bump and normal map was not measured here.

## Attributes into the shader

```python
ca = me.color_attributes.new("paint", "BYTE_COLOR", "CORNER")
for poly in me.polygons:
    for li in poly.loop_indices:
        ca.data[li].color = face_col[poly.index]      # .color is linear; .color_srgb is the stored value
vc = nt.nodes.new("ShaderNodeVertexColor")            # the "Color Attribute" node
vc.layer_name = "paint"
nt.links.new(vc.outputs["Color"], em.inputs["Color"])

at = nt.nodes.new("ShaderNodeAttribute")
at.attribute_name = "height"                          # a generic attribute, through Fac / Color / Vector
at.attribute_type = "OBJECT"                          # GEOMETRY (default), OBJECT, INSTANCER, VIEW_LAYER
at.attribute_name = "tint"                            # with OBJECT: reads ob["tint"], a custom property
```

`[exp: experiments/materials/attributes_and_slots.py]` The colour attribute reached the shader linear in Cycles and
EEVEE (grey 0.5 read 0.502). A ByteColorAttribute holding 0.5029 linear stores 0.7373 in `.color_srgb`. A float point
attribute set to 0.25 read 0.25 through the Attribute node's Fac. An OBJECT attribute read the custom property
`ob["tint"] = (0.1, 0.2, 0.3)`. A misspelled attribute name rendered 0 with no error. `mesh.vertex_colors` still
exists in 4.5 next to `color_attributes`. `[exp: experiments/materials/attributes_and_slots.py]`

## Materials per face

```python
me.materials.append(m2)                               # slot 1
for p in me.polygons:
    p.material_index = 1 if p.index in (1, 3) else 0
```

Faces 1 and 3 rendered with the second material. Slots added through `mesh.materials` link to the mesh data
(`material_slots[0].link == "DATA"`). `[exp: experiments/materials/attributes_and_slots.py]`

## Reference: Principled BSDF inputs in 4.5

31 inputs; every name equals its identifier. `*` = hidden. `[exp: experiments/materials/principled_bsdf.py]` `[inv]`

| # | name | type | default |
|---|---|---|---|
| 0 | Base Color | Color | (0.8, 0.8, 0.8, 1) |
| 1 | Metallic | Factor | 0 |
| 2 | Roughness | Factor | 0.5 |
| 3 | IOR | Float | 1.5 |
| 4 | Alpha | Factor | 1 |
| 5 | Normal | Vector | (0, 0, 0) |
| 6* | Weight | Float | 0 |
| 7 | Diffuse Roughness | Factor | 0 |
| 8 | Subsurface Weight | Factor | 0 |
| 9 | Subsurface Radius | Vector | (1, 0.2, 0.1) |
| 10 | Subsurface Scale | Distance | 0.05 |
| 11* | Subsurface IOR | Factor | 1.4 |
| 12 | Subsurface Anisotropy | Factor | 0 |
| 13 | Specular IOR Level | Factor | 0.5 |
| 14 | Specular Tint | Color | (1, 1, 1, 1) |
| 15 | Anisotropic | Factor | 0 |
| 16 | Anisotropic Rotation | Factor | 0 |
| 17 | Tangent | Vector | (0, 0, 0) |
| 18 | Transmission Weight | Factor | 0 |
| 19 | Coat Weight | Factor | 0 |
| 20 | Coat Roughness | Factor | 0.03 |
| 21 | Coat IOR | Float | 1.5 |
| 22 | Coat Tint | Color | (1, 1, 1, 1) |
| 23 | Coat Normal | Vector | (0, 0, 0) |
| 24 | Sheen Weight | Factor | 0 |
| 25 | Sheen Roughness | Factor | 0.5 |
| 26 | Sheen Tint | Color | (1, 1, 1, 1) |
| 27 | Emission Color | Color | (1, 1, 1, 1) |
| 28 | Emission Strength | Float | 0 |
| 29 | Thin Film Thickness | Wavelength | 0 |
| 30 | Thin Film IOR | Float | 1.33 |

Output: BSDF. Node properties: `distribution` GGX / MULTI_GGX, `subsurface_method` BURLEY / RANDOM_WALK /
RANDOM_WALK_SKIN. `[inv]`

3.x name -> 4.5 name (the 3.x names raise KeyError, measured; the right column is the 4.5 socket with that role, from
the manual's descriptions):

| 3.x | 4.5 |
|---|---|
| Subsurface | Subsurface Weight |
| Subsurface Color | (no socket of its own in 4.5) |
| Specular | Specular IOR Level |
| Clearcoat, Clearcoat Roughness, Clearcoat Normal | Coat Weight, Coat Roughness, Coat Normal |
| Sheen | Sheen Weight |
| Transmission | Transmission Weight |
| Transmission Roughness | Roughness ("for specular reflection and transmission") |
| Emission | Emission Color |

`[exp: experiments/materials/principled_bsdf.py]`
`[doc: https://docs.blender.org/manual/en/4.5/render/shader_nodes/shader/principled.html]`

## Reference: material settings

| property | default | note |
|---|---|---|
| `Material.use_nodes` | False on `materials.new` | |
| `Material.displacement_method` | BUMP | BUMP, DISPLACEMENT, BOTH |
| `Material.surface_render_method` | DITHERED | EEVEE: DITHERED, BLENDED `[exp: experiments/rendering/eevee_background.py]` |
| `Material.blend_method` | | still accepted; BLEND maps to BLENDED |
| `Material.diffuse_color` | | viewport and Workbench colour only |
| `Material.pass_index` | 0 | for the material index pass `[inv]` |
