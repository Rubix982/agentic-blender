# Lessons: materials and images

From a project that textured draped garments with photo-derived maps, embroidery, sequins and sheer fabrics in Blender
4.5.14, rendered in Cycles, EEVEE and Workbench.

---

### Image.pixels of an 8-bit sRGB image gives the stored (encoded) values, not linear ones
**What happens:** for a byte image whose colour space is sRGB, `image.pixels` returns the stored values (bytes / 255).
Float images give linear values.
**Evidence:** on an 8-bit PNG, the median of Blender's pixels (0.8392, 0.8000, 0.7922) equalled the median of PIL's
bytes / 255 to four places. Code that treated them as linear and encoded them to sRGB again lifted a median #d6ccca to
#ece7e6: every colour recorded for months was too light. Float (EXR) maps were assumed linear, not tested. (not
re-checked here)
**What to do:** if `img.colorspace_settings.name == 'sRGB' and not img.is_float`, linearise before averaging, then encode
once.
**How it was found:** comparing Blender's pixels with PIL's.

### Colour inputs are scene-linear: sRGB hex values written raw render pale
**What happens:** Base Color and colour attributes take linear values; a hex colour from a picker or a photo is sRGB.
**Evidence:** a gold #ba9b72 written straight into Base Color rendered near white. (not re-checked here)
**What to do:** convert each channel with `c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4` first.
**How it was found:** a render.

### Workbench draws material.diffuse_color, which node colours do not reach
**What happens:** Workbench (and solid viewport) shading shows each material's `diffuse_color` (grey by default), not its
node tree.
**Evidence:** a skinned tunic rendered in Workbench read as the body in one grey. (not re-checked here)
**What to do:** copy the Principled Base Color into `mat.diffuse_color` and set `scene.display.shading.color_type =
'MATERIAL'`.
**How it was found:** a preview render.

### Changing a simulated mesh's materials frees its cloth cache: re-material a frozen copy
**What happens:** adding or swapping materials on a mesh under an unbaked cloth throws the cache away (`cloth.md`).
**Evidence:** project: materials changed after a simulation rendered unsimulated cloth. Re-checked here
`[exp: experiments/simulation/cloth_cache_invalidation.py]`: adding a material slot to the cloth cut its cache from 40 to
10 frames; editing an existing material's Base Color value did not touch it.
**What to do:** set materials before simulating, or copy the evaluated cloth
(`bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)`) into a new object,
re-create the after-cloth modifiers on it, hide the original from render and change materials on the copy. For flat id
colours, `material_slot.link = 'OBJECT'` changes materials without touching the mesh.
**How it was found:** frozen clips.

### A copied object shares its materials: recolouring the copy recolours the original
**What happens:** `obj.copy()` shares mesh and materials unless they are copied too.
**Evidence:** a check coloured a pressed copy's materials grey through the hidden original, and both sleeves then counted as
missing on 64 frames. (not re-checked here)
**What to do:** copy the materials (`m.copy()`) before changing them on a copy.
**How it was found:** a check that failed on frames that looked fine.

### Nodes inside a node group are not in material.node_tree.nodes
**What happens:** a search for the Principled BSDF in a material's tree misses one kept inside a group node.
**Evidence:** the first search missed it. (not re-checked here)
**What to do:** also search the trees of `GROUP` nodes (`node.node_tree.nodes`).
**How it was found:** a colour change that did nothing.

### The 4.x Mix node has duplicate socket names per data type: address its colour sockets by index
**What happens:** `ShaderNodeMix` carries float, vector and colour versions of A and B under the same names.
**Evidence:** the project set `data_type = 'RGBA'` and used `inputs['Factor']`, `inputs[6]` (A), `inputs[7]` (B) and
`outputs[2]`. (not re-checked here; `kb.py node "Mix"` lists the sockets with identifiers)
**What to do:** set `data_type` first, then link by index or identifier.
**How it was found:** links landing on the float sockets.

### Sheer cloth: a translucent mix, then a transparent mix, and EEVEE's render method
**What happens:** thin cloth should glow when backlit and tint the light that passes; untinted transparency reads grey.
**Evidence:** an untinted sheer fabric lying on the floor read grey instead of pink. Setup used: Principled mixed with
Translucent BSDF (glow), then Transparent BSDF mixed by alpha after it, its colour tinted toward the cloth's;
`mat.surface_render_method = 'DITHERED'` (`'BLENDED'` for partly sheer) and `use_transparency_overlap = True`. (not
re-checked here)
**What to do:** as above.
**How it was found:** backlit swatch tests.

### A metal's colour comes from what it reflects; a photo-sampled colour is too dark for a metal
**What happens:** a colour picked from a photo of gold thread is mostly the metal's shadows; as a metal's base colour it
renders dark olive-grey. A rough metal averages a wide cone of a grey surround and reads as paint.
**Evidence:** gold in a close-up rendered at lightness 57-60 against the photo's 84; the sky was about 58 % of the fitted
light, so camera-facing metal mirrored grey sky. (not re-checked here)
**What to do:** keep the hue and set the brightest channel to a real metal's reflectance (gold about (1.0, 0.78, 0.34)
linear); roughness about 0.25; give metals something bright to mirror (see `rendering.md`).
**How it was found:** measured lightness against photos.

### Smooth-shaded cupped sequins glint at any tilt; flat facets only when aligned
**What happens:** a shallow smooth-shaded dome sweeps a range of normals, so it catches a light from many angles.
**Evidence:** flat 8-facet sequins tilted about 7 degrees gave 0.6-0.8 sparkles per cm² against the photo's 2.1; shallow
cups (depth 0.12 x radius) with smooth shading and a random tilt each came closer. (not re-checked here)
**What to do:** model sequins as shallow smooth cups with a random tilt.
**How it was found:** counting sparkles against a photo.

### A painted metal map is not evidence of sequins
**What happens:** a metallic map read from a photo marks shiny print as metal; turned into geometry it makes sequins where
the cloth has none.
**Evidence:** a digital print became 7,265 sequins. At catalogue resolution 2.4-3.6 % of thread embroidery read as false
metal. (not re-checked here)
**What to do:** gate geometry on a separate reading of what the work is (sequin, thread, print).
**How it was found:** a reviewer's eye on a sequinned print.

### Image.save wrote small generated PNGs black
**What happens:** 8 x 8 plain-colour images created in Blender and saved with `image.save` came out black; the cause was
not found.
**Evidence:** several tiny swatch maps. (not re-checked here)
**What to do:** verify saved images after writing (read them back), or write PNG bytes directly.
**How it was found:** black swatches.
