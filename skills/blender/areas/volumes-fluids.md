# Volumes and fluids

Blender 4.5.14 LTS on Apple Silicon (16 GB, Metal). Tags: `[inv]` read from Blender (`scripts/kb.py`), `[exp: path]`
measured here (paths relative to the source repository; results next to each script in `results/`), `[doc: link]`
Blender's documentation. A volume here is a Volume object (OpenVDB grids) or a mesh whose material has a Volume
output; fluids are Mantaflow smoke and liquid domains. Other simulations and their caches: `simulation.md`.

## What goes wrong most often

1. **Trusting `kb.py`'s defaults for the volume modifiers.** A new Mesh to Volume modifier starts at `VOXEL_AMOUNT` 32,
   density 1.0 and interior band 0.2, where the registered defaults `kb.py` prints read 0 for all of them. The
   geometry-nodes Mesh to Volume node starts at amount 64 instead. Read the values from the modifier or node you made.
   `[exp: experiments/volumes/mesh_volume_convert.py]` `[inv]`
2. **Looking for the result on the Volume data-block.** The Mesh to Volume modifier's grids exist only on the
   evaluated object: the Volume data-block itself had 0 grids, `obj.evaluated_get(depsgraph).data` had 1
   (`density`, FLOAT). `VolumeGrids.save` on the data-block returned True and wrote a `.vdb` with no grids in it.
   `[exp: experiments/volumes/mesh_volume_convert.py]` `[exp: experiments/volumes/vdb_roundtrip.py]`
3. **Moving the Volume object to move the volume.** Mesh to Volume places the volume where the source mesh is in the
   world: with the source at x = -1.2, the volume's centre was at x = -1.326 with the Volume object at 0 and -1.306
   with it at 5. Move the source mesh. `[exp: experiments/volumes/volume_render.py]`
4. **Volume to Mesh returning nothing from a file.** It reads the grid named in `grid_name`, `density` by default; a
   level set written as `surface` gave 0 points until `grid_name = "surface"`. `[exp: experiments/volumes/vdb_roundtrip.py]`
5. **Principled Volume wired to Surface.** A mesh cube with Principled Volume on the material's Surface socket rendered
   black (0, 0, 0) in Cycles and EEVEE. It goes on the Volume socket. `[exp: experiments/volumes/volume_render.py]`
6. **Calling `fluid.bake_all` with nothing active.** It fails its poll ("Context missing active object"). With
   `bpy.context.temp_override(object=domain, active_object=domain)` it baked headless and returned when done.
   `[exp: experiments/volumes/fluid_bake.py]`
7. **Baking an unsaved file.** A new domain's cache directory is `cache_fluid_<hash>` inside `bpy.app.tempdir`,
   Blender's session temp folder, when the file has not been saved; in a saved file it is `//cache_fluid_<hash>` next
   to the `.blend`. Set `domain_settings.cache_directory` to a folder of your own before baking.
   `[exp: experiments/volumes/fluid_bake.py]` (That Blender deletes its session temp folder on exit was not checked
   here.)
8. **Changing a domain setting after a bake.** Setting `vorticity` or `resolution_max` from Python after an ALL bake
   cleared `has_cache_baked_data` and deleted all 20 cache files. Moving the flow object, changing its density or the
   domain's `cache_frame_end` kept the bake. `[exp: experiments/volumes/fluid_bake.py]`
9. **Re-baking a baked domain.** `bake_all` on a domain that already has a bake returned FINISHED without baking again,
   even after pointing `cache_directory` at a new folder (it wrote 2 files there). `free_all` returned at once while
   `has_cache_baked_data` still read True and the files were still on disk; after a `scene.frame_set` both had settled
   (False, 0 files) and the next `bake_all` baked all 20 files again. `[exp: experiments/volumes/fluid_free.py]`

## Mesh to volume and back

**Modifiers.** Mesh to Volume goes on a Volume object; Volume to Mesh on a mesh object.

```python
vol = bpy.data.volumes.new("Vol")
vo = bpy.data.objects.new("Vol", vol); scene.collection.objects.link(vo)
m2v = vo.modifiers.new("M2V", "MESH_TO_VOLUME"); m2v.object = src        # starts at VOXEL_AMOUNT 32
back = bpy.data.objects.new("Back", bpy.data.meshes.new("Back")); scene.collection.objects.link(back)
v2m = back.modifiers.new("V2M", "VOLUME_TO_MESH"); v2m.object = vo        # GRID resolution, threshold 0.1

dg = bpy.context.evaluated_depsgraph_get()
[(g.name, g.data_type) for g in vo.evaluated_get(dg).data.grids]           # [('density', 'FLOAT')]
len(back.evaluated_get(dg).data.vertices)
```

`[exp: experiments/volumes/mesh_volume_convert.py]` A new Volume to Mesh starts at resolution `GRID` (the volume's own
voxels), threshold 0.1, adaptivity 0. `[exp: experiments/volumes/mesh_volume_convert.py]`

Round trip of a radius-1 UV sphere (64 x 32) through both modifiers, interior band 0.2, threshold 0.1.
`[exp: experiments/volumes/mesh_volume_convert.py]`

| `voxel_amount` | voxel | points out | radius out (min / mean / max) | time |
|---|---|---|---|---|
| 16 | 0.21651 m | 362 | 0.9647 / 0.9945 / 1.029 | 0.012 s |
| 32 | 0.10825 m | 1538 | 0.9759 / 0.9857 / 1.0072 | 0.012 s |
| 64 | 0.05413 m | 6138 | 0.9773 / 0.9793 / 0.9856 | 0.018 s |
| 128 | 0.02706 m | 24674 | 0.9776 / 0.9785 / 0.9799 | 0.034 s |

`[exp: experiments/volumes/mesh_volume_convert.py]` The voxel is the bounding box's diagonal (3.46 m here) divided by
the amount, not its side; points out grow about four times per doubling.

**Where the surface comes back.** A fog volume made from a mesh is 0 outside and ramps to the density across the
interior band, so Volume to Mesh finds the threshold about threshold x band width inside the original surface: band 0.2
gave mean radius 0.979, 0.898 and 0.817 at thresholds 0.1, 0.5 and 0.9; band 0.05 at threshold 0.1 gave 1.000.
`[exp: experiments/volumes/mesh_volume_convert.py]`

**Geometry nodes.** Mesh to Volume -> Volume to Mesh with node defaults gave the same 6138 points and mean radius 0.9793
as the modifiers at amount 64. The SDF grid nodes are there in 4.5 and run headless: Mesh to SDF Grid (voxel 2/64 m)
-> Grid to Mesh at threshold 0 returned a surface at mean radius 0.9984 (min 0.9976), much closer to the mesh than
the fog-volume route. `[exp: experiments/volumes/mesh_volume_convert.py]`

```python
a = ng.nodes.new("GeometryNodeMeshToSDFGrid"); a.inputs["Voxel Size"].default_value = 2 / 64
b = ng.nodes.new("GeometryNodeGridToMesh");    b.inputs["Threshold"].default_value = 0.0
ng.links.new(geo, a.inputs["Mesh"]); ng.links.new(a.outputs["SDF Grid"], b.inputs["Grid"])
```

A Volume object whose geometry nodes output a Volume Cube (resolution 32 over -1..1) evaluated to one FLOAT grid,
`density`, voxel 0.06452 m (2/31). `[exp: experiments/volumes/mesh_volume_convert.py]`

**Voxel values from Python.** `bpy` gives only grid metadata (`name`, `data_type`, `channels`, `matrix_object`,
`is_loaded`) `[inv]`. Blender 4.5 bundles the OpenVDB module as `import openvdb` (version 12.0.0; `pyopenvdb` does not
exist), with `read` and `write`. `[exp: experiments/volumes/mesh_volume_convert.py]`

## OpenVDB files out and in

```python
dg = bpy.context.evaluated_depsgraph_get()
vo.evaluated_get(dg).data.grids.save(path)          # the evaluated volume, not vol.grids

grids, meta = openvdb.readAll(path)                  # read it outside Blender's API
g = grids[0]; g.activeVoxelCount(), g.evalMinMax(), g.transform.voxelSize()

bpy.ops.object.volume_import(filepath=path, directory=folder + os.sep, files=[{"name": "sphere.vdb"}])

v = bpy.data.volumes.new("ByPath"); v.filepath = path
v.grids.load()                                       # grids are listed only after this
```

- The saved sphere was 88,845 bytes: one `FloatGrid` named `density`, class fog volume, 3240 active voxels, values
  0.0037 to 1.0, 1.0 at the centre, voxel 0.10825 m. `[exp: experiments/volumes/vdb_roundtrip.py]`
- `volume_import` ran headless with no override and added one Volume object; its grids loaded from the file.
  `[exp: experiments/volumes/vdb_roundtrip.py]`
- Through the data API, the grids were listed (one, `density`) only after `grids.load()`. `grids[0].load()` returned
  True, yet that grid's `is_loaded` still read False on the original data-block; why was not traced.
  `[exp: experiments/volumes/vdb_roundtrip.py]`
- A missing file does not raise: `grids.load()` returned False and `grids.error_message` read "missing.vdb not found".
  `[exp: experiments/volumes/vdb_roundtrip.py]`
- **A VDB written from scratch:** `openvdb.createLevelSetSphere(radius=0.8, center=(0, 0, 0), voxelSize=0.04,
  halfWidth=3.0)` saved with `openvdb.write(path, grids=[ls])` loaded in Blender. Volume to Mesh, with `grid_name` set,
  put the surface at radius 0.800 at threshold 0 and 0.900 at the default 0.1. `[exp: experiments/volumes/vdb_roundtrip.py]`
- **Sequences:** importing `seq_0001.vdb` to `seq_0003.vdb` in one call (all three in `files`) made one Volume object
  with `is_sequence` True and `frame_duration` 3; frames 1, 2, 3 loaded their own files, frame 5 loaded none
  (`sequence_mode` CLIP). `[exp: experiments/volumes/vdb_roundtrip.py]`

## Rendering a volume

```python
m = bpy.data.materials.new("Smoke"); m.use_nodes = True
nt = m.node_tree; nt.nodes.clear()
pv = nt.nodes.new("ShaderNodeVolumePrincipled")
pv.inputs["Density"].default_value = 5.0            # multiplies the grid named in "Density Attribute" ("density")
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(pv.outputs["Volume"], out.inputs["Volume"])    # Volume, not Surface
vol.materials.append(m)                              # a Volume object; or a mesh's material for a box of fog
```

Principled Volume's inputs in 4.5: Color, Color Attribute, Density (1.0), Density Attribute (`density`), Anisotropy,
Absorption Color, Emission Strength, Emission Color, Blackbody Intensity, Blackbody Tint, Temperature, Temperature
Attribute (`temperature`). `[inv]` (`kb.py node "Principled Volume"`) `[doc: https://docs.blender.org/manual/en/4.5/render/shader_nodes/shader/volume_principled.html]`

A Volume object (Mesh to Volume, amount 64, density 5, orange) and a mesh cube of fog (density 2) in front of a grey
backdrop, sun-lit, 128 x 128, 32 samples. `[exp: experiments/volumes/volume_render.py]`

| Engine | seconds | volume object (RGB) | fog cube | bare backdrop |
|---|---|---|---|---|
| Cycles CPU | 0.156 | (0.438, 0.332, 0.211) | (0.458, 0.365, 0.27) | (0.482, 0.482, 0.482) |
| Cycles Metal | 0.468 | same | same | same |
| EEVEE | 0.298 | (0.577, 0.451, 0.313) | (0.614, 0.511, 0.412) | (0.478, 0.478, 0.478) |

`[exp: experiments/volumes/volume_render.py]` At this size the CPU was faster than Metal, as in
`animation-video.md`. Cycles' `volume_step_rate` (default 1.0): 0.25 took 0.792 s, 1.0 took 0.468 s, 4.0 took 0.431 s, and the volume's
colour moved by less than 0.01. A Volume object with no material still rendered in Cycles, as a grey volume
(0.531, 0.531, 0.531). `[exp: experiments/volumes/volume_render.py]`

Volume settings that exist in 4.5: Cycles
`volume_step_rate`, `volume_max_steps` (1024), `volume_bounces` (0); EEVEE `volumetric_tile_size` ("8"),
`volumetric_samples` (64), `volumetric_start` / `volumetric_end` (0.1 / 100 m), `volumetric_shadow_samples` (16). `[inv]`

## A small Mantaflow smoke or liquid, baked headless

```python
dom = ...                                            # a 2 m cube mesh
md = dom.modifiers.new("Fluid", "FLUID"); md.fluid_type = "DOMAIN"
ds = md.domain_settings
ds.domain_type = "GAS"                               # or "LIQUID"
ds.resolution_max = 32
ds.cache_frame_start, ds.cache_frame_end = 1, 10
ds.cache_type = "ALL"                                # default REPLAY
ds.cache_directory = "/abs/path/cache"               # default: bpy.app.tempdir when the file is unsaved
fm = flow.modifiers.new("Fluid", "FLUID"); fm.fluid_type = "FLOW"
fm.flow_settings.flow_type = "SMOKE"; fm.flow_settings.flow_behavior = "INFLOW"
# liquid: flow_type = "LIQUID", flow_behavior = "GEOMETRY"
with bpy.context.temp_override(object=dom, active_object=dom):
    bpy.ops.fluid.bake_all()                         # blocks until done
```

`[exp: experiments/volumes/fluid_bake.py]` A new domain is GAS, cache type REPLAY, data as OpenVDB, mesh as
`BOBJECT`, resolution 32, frames 1-250, `use_mesh` on. `[exp: experiments/volumes/fluid_bake.py]` REPLAY bakes "as
the simulation is being played", MODULAR step by step with separate bake operators, ALL with one tool.
`[doc: https://docs.blender.org/manual/en/4.5/physics/fluid/type/domain/cache.html]`

Bake time and cache size for 10 frames, ALL. `[exp: experiments/volumes/fluid_bake.py]`

| `resolution_max` | smoke: seconds | smoke: bytes | liquid: seconds | liquid: bytes | liquid surface points, frame 10 |
|---|---|---|---|---|---|
| 16 | 0.15 | 548,556 | 0.14 | 663,575 | 862 |
| 32 | 0.29 | 728,803 | 0.35 | 2,062,018 | 3236 |
| 48 | 0.56 | 1,011,012 | 0.76 | 4,330,894 | 6998 |
| 96 | 5.3 | 2,550,835 | 5.27 | 17,414,102 | 27012 |

`[exp: experiments/volumes/fluid_bake.py]`

- **What a bake writes.** Smoke: one `config/config_####.uni` and one `data/fluid_data_####.vdb` per frame (20 files
  for 10 frames). Liquid adds 10 mesh files (30 in all). `[exp: experiments/volumes/fluid_bake.py]`
- **Reading the smoke back.** The last frame's `.vdb` held the grids `density`, `flame`, `shadow`, `temperature` and
  `velocity`; density had 691 active voxels and a maximum of 0.9575 (at resolution 16). `volume_import` on that file
  made a Volume object with the same five grids, so a bake can be rendered or reprocessed as an ordinary volume.
  `[exp: experiments/volumes/fluid_bake.py]`
- **Liquid surface.** After an ALL bake, the domain's evaluated mesh at frame 10 was the liquid surface (3236 points at
  resolution 32), not the domain cube. `[exp: experiments/volumes/fluid_bake.py]`
- **REPLAY without a bake.** With the default cache type, stepping frames 1 to 10 with `frame_set` simulated and wrote
  20 cache files in 0.11 s, with `has_cache_baked_data` False. `[exp: experiments/volumes/fluid_bake.py]`

What clears a baked (ALL) cache, each change made after a fresh bake of 20 files.
`[exp: experiments/volumes/fluid_bake.py]`

| Change | `has_cache_baked_data`, files after |
|---|---|
| move the flow object | True, 20 |
| flow `density` halved | True, 20 |
| domain `cache_frame_end` + 1 | True, 20 |
| domain `vorticity` + 0.1 | False, 0 |
| domain `resolution_max` + 2 | False, 0 |
| `fluid.free_all`, then a `frame_set` | False, 0 |

`[exp: experiments/volumes/fluid_bake.py]` A moved flow object does not show in the baked result until the domain is
freed and baked again (that the old bake keeps playing was not checked frame by frame here).
