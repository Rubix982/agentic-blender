# Repeating geometry: copies, instances, particles, hair curves, assets

Blender 4.5.14 LTS. Tags: `[inv]` read from Blender (`scripts/kb.py`), `[exp: path]` measured here, `[doc: link]`
Blender's documentation. Experiment: `experiments/instancing/repeat_geometry.py` in the source repository. Geometry
nodes' own instancing (Instance on Points, Realize Instances) is in `geometry-nodes.md`. Assets from outside
Blender (free HDRIs, textures and models from Poly Haven and ambientCG) are in `remote-assets.md`.

## What goes wrong most often

1. **Copying the mesh when the object is all that needs copying.** 2,000 spheres (32 x 16) as full copies made a
   69.2 MB `.blend` with 2,001 meshes; as linked duplicates (objects sharing one mesh) 2.9 MB with 1 mesh, and quicker
   to create (0.081 s against 0.130 s). `obj.copy()` shares the mesh; `obj.data.copy()` is what duplicates it. `[exp: experiments/instancing/repeat_geometry.py]`
2. **Counting objects to count what is drawn.** Instances are not objects. Vertex instancing and a particle system
   drew 2,000 spheres from 2 objects; count them with `depsgraph.object_instances` (`is_instance`). Collection
   instances need one empty each, so 2,000 empties are 2,000 objects. `[exp: experiments/instancing/repeat_geometry.py]`
3. **Reading a hair particle's `location` as its root.** For hair, `particle.location` is the strand's tip (z = 1.0 on a
   plane at z = 0, hair length 1.0); `hair_keys[0].co` is the root. `[exp: experiments/instancing/repeat_geometry.py]`
4. **Loading from the file that is open.** `save_as_mainfile(filepath=p)` makes `p` the open file, and
   `bpy.data.libraries.load(p)` then fails: "Cannot load from the current blend file." Save with `copy=True` to write a
   copy and stay in the current file. `[exp: experiments/instancing/repeat_geometry.py]`
5. **Using the names list after a library load.** After `with bpy.data.libraries.load(path) as (src, dst):
   dst.node_groups = names`, the list holds the loaded data-blocks, not the names. `[exp: experiments/instancing/repeat_geometry.py]`

## Five ways to repeat 2,000 spheres

| Way | Create | Meshes | `.blend` (MB) | Depsgraph |
|---|---|---|---|---|
| full copies (`objects.new(name, mesh.copy())`) | 0.130 s | 2,001 | 69.23 | 2,000 objects |
| linked duplicates (`objects.new(name, mesh)`) | 0.081 s | 1 | 2.91 | 2,000 objects |
| collection instances (empties, `instance_type = "COLLECTION"`) | 0.068 s | 1 | 2.91 | 2,000 instances + 2,000 empties |
| vertex instancing (`parent.instance_type = "VERTS"`, child parented) | 0.001 s | 2 | 0.42 | 2,000 instances, 2 objects |
| particle system (hair, `render_type = "OBJECT"`) | 0.019 s | 2 | 0.40 | 2,000 instances, 2 objects |

`[exp: experiments/instancing/repeat_geometry.py]` (uncompressed saves; creation from Python, one `view_layer.update()`).
`Object.instance_type` is one of `NONE`, `VERTS`, `FACES`, `COLLECTION`. `[inv]`

```python
coll = bpy.data.collections.new("Ball")        # not linked into the scene, so its objects are not drawn themselves
coll.objects.link(ball)
e = bpy.data.objects.new("inst", None)         # an empty
e.instance_type = "COLLECTION"; e.instance_collection = coll
scene.collection.objects.link(e)
```

**Making instances real, headless:** select the instancers, make one active, `bpy.ops.object.duplicates_make_real()`.
It made 2,000 mesh objects sharing one mesh in 0.27 s. `[exp: experiments/instancing/repeat_geometry.py]`

**A legacy particle system:**

```python
mod = emitter.modifiers.new("Scatter", "PARTICLE_SYSTEM")
ps = mod.particle_system.settings
ps.type = "HAIR"; ps.count = 2000; ps.render_type = "OBJECT"; ps.instance_object = ball
parts = emitter.evaluated_get(bpy.context.evaluated_depsgraph_get()).particle_systems[0].particles
```

Hair particles are placed at once; emitter particles are born over frames, so the frames have to run.
`[exp: experiments/instancing/repeat_geometry.py]`

## Hair curves and point clouds

The `Curves` object type (hair curves, 4.x) builds from Python:

```python
hc = bpy.data.hair_curves.new("Hair")
hc.add_curves([4] * 100)                                   # 100 curves of 4 points
hc.attributes["position"].data.foreach_set("vector", positions.ravel())
obj = bpy.data.objects.new("Hair", hc)                     # obj.type == "CURVES"
```

`[exp: experiments/instancing/repeat_geometry.py]`. `bpy.data.pointclouds.new()` creates an empty point cloud, but
4.5's Python offers no `add_points`; build point clouds with geometry nodes (Mesh to Points, Points).
`[exp: experiments/instancing/repeat_geometry.py]`

## Assets

```python
obj.asset_mark()
obj.asset_data.tags.new("stone"); obj.asset_data.description = "..."
with bpy.data.libraries.load(path, assets_only=True) as (src, dst):   # lists only data-blocks marked as assets
    dst.objects = list(src.objects)
```

Blender's own assets are in `<datafiles>/assets/` (`bpy.utils.system_resource("DATAFILES")`): brushes, and two
node-group files, `geometry_nodes/smooth_by_angle.blend` ("Smooth by Angle": inputs Mesh, Angle, Ignore Sharpness)
and `geometry_nodes/procedural_hair_node_assets.blend`. Append them the same way. `[inv]` `[exp: experiments/instancing/repeat_geometry.py]`
