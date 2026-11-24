# Light, world and camera

Blender 4.5.14 LTS on Apple Silicon. Tags: `[inv]` read from Blender (`scripts/kb.py`), `[exp: path]` measured here
(paths relative to the source repository), `[lesson]` from a real project, `[doc: link]` Blender's documentation.
Light measurements read the radiance of a white Lambertian floor (Diffuse BSDF, albedo 0.8) in a scene-linear EXR and
convert it to irradiance, E = pi x radiance / 0.8.

## What goes wrong most often

1. **Light power from memory, or the sun as bright as a lamp.** A sun's strength is irradiance in W/m2: strength 3 put
   exactly 3.0 on a floor facing it, in both engines. Point, spot and area power is radiant watts: a 1000 W point light
   gave 19.8 at 2 m (P / (4 pi d^2) = 19.9) and a quarter of that at 4 m. An area light of the same power is four times
   brighter on its axis (about P / (pi d^2)), because it emits from one side like a panel.
   `[exp: experiments/light/light_units.py]` "It is Radiant Flux or Radiant Power which is also measured in Watts".
   `[doc: https://docs.blender.org/manual/en/4.5/render/lights/light_object.html]`
2. **Default energies that depend on how the light was made.** `bpy.data.lights.new` gives energy 10 for every type,
   a sun included (10 W/m2: a white floor reads 2.5, far past white under Standard). `bpy.ops.object.light_add` gave a
   sun of 1 W/m2 and a point light of 10 W, radius 0, in background mode with factory settings. Set `energy`
   explicitly. `[exp: experiments/light/light_units.py]` `[exp: experiments/light/sun_angle_soft_shadow.py]`
3. **A Nishita sky treated like a 0..1 colour.** At strength 1 with the sun at 45 degrees it put irradiance of about
   94 (green channel) on the floor in Cycles, 90 % of it from the sun disc. Scale the Background Strength down or lower
   exposure; from that number, a strength of about 0.02 brings a white floor near 0.5 under Standard (derived, not
   rendered). The manual says as much: "this sky type is quite
   bright and makes the image look overexposed with the default scene settings".
   `[exp: experiments/light/world_sky.py]` `[doc: https://docs.blender.org/manual/en/4.5/render/shader_nodes/textures/sky.html]`
4. **Expecting EEVEE to be lit by the Nishita sun disc.** It is not: EEVEE's floor irradiance stayed near Cycles'
   no-disc value at every elevation (about 10 at 45 degrees against Cycles' 94 with the disc). Lowering
   `world.sun_threshold` from 10 to 1 only raised it to 18. Add a Sun light for the sun in EEVEE.
   `[exp: experiments/light/world_sky.py]` "In Nishita mode, the Sun Disc property is not supported".
   `[doc: https://docs.blender.org/manual/en/4.5/render/eevee/limitations/nodes_support.html]`
5. **Soft shadows in EEVEE from 4.1 settings.** `scene.eevee.use_soft_shadows` and `light.use_contact_shadow` are gone.
   Shadow softness comes from the light's size (`sun.angle`, `light.shadow_soft_size`), and EEVEE reaches the right
   penumbra width only with `light.use_shadow_jitter = True` (default False): without it a 10-degree sun's soft edge was
   98 mm wide against 131 mm in Cycles; with it, 136 mm. `[exp: experiments/light/sun_angle_soft_shadow.py]`
   `[exp: experiments/rendering/eevee_background.py]`
6. **A shadow catcher pass that removes the shadow.** In Cycles, with film transparent, the shadow is in the Combined
   pass's alpha (0.77 under the cube) *only while the Shadow Catcher pass is off*. Turning on
   `view_layer.cycles.use_pass_shadow_catcher` moved it out of Combined (alpha 0 there) into the "Shadow Catcher" pass
   (0.23 in shadow, 1.0 on open floor) to be multiplied over the backplate. EEVEE has no shadow catcher: the floor
   rendered as an ordinary opaque floor. `[exp: experiments/light/shadow_catcher.py]`
7. **`is_shadow_catcher` on `object.cycles`.** It is `Object.is_shadow_catcher` (and `Object.is_holdout`);
   `object.cycles` has no such attribute. `[exp: experiments/light/shadow_catcher.py]`
8. **Aiming with the wrong axes.** A camera or light looks down its local -Z with +Y up:
   `direction.to_track_quat("-Z", "Y")`. With `"Z"` the camera faced away (target depth -10.9).
   `[exp: experiments/camera/camera_aim_dof.py]`
9. **Reading a constrained camera's matrix before an update.** After moving a Track To target, `matrix_world` was
   stale (target projected to x = -0.05) until `bpy.context.view_layer.update()` (then 0.5).
   `[exp: experiments/camera/camera_aim_dof.py]`
10. **Tilting a sun by its elevation.** A sun shines down its local -Z, so `rotation_euler.x = radians(30)` put it 60
    degrees up, not 30. For elevation e and compass bearing b (+Y north, +X east, clockwise from north):
    `rotation_euler = (radians(90 - e), 0, radians(180 - b))`. `[exp: experiments/light/sun_elevation.py]`
11. **Looking for the object in a light-linking entry.** `collection.collection_objects[i]` has only
    `light_linking.link_state`; `.object` raises `AttributeError`. The object is `collection.objects[i]`, in the same
    order. `[exp: experiments/light/light_linking.py]`

## Lights

```python
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3.0                       # W/m2 on a surface facing the sun
sun.data.angle = math.radians(2)            # angular diameter: shadow softness (sun_angle_soft_shadow.py)
sun.rotation_euler = (0.7, 0.2, 0.5)        # only direction matters for a sun
scene.collection.objects.link(sun)

area = bpy.data.objects.new("Area", bpy.data.lights.new("Area", "AREA"))
area.data.energy = 300                      # W, total
area.data.size = 2
area.location = (-3, -2, 4)
area.rotation_euler = (Vector((0, 0, 1)) - area.location).to_track_quat("-Z", "Y").to_euler()   # aim at a point
scene.collection.objects.link(area)
```

(Code from `experiments/rendering/cycles_metal_vs_cpu.py`.) Measured irradiance on a floor facing the light, Cycles and
EEVEE within 0.3 % of each other `[exp: experiments/light/light_units.py]`:

| light | setting | measured E | law |
|---|---|---|---|
| sun | strength 1 / 3 | 1.00 / 3.00 | E = strength |
| sun, tilted 60 degrees | strength 3 | 1.50 | strength x cos(tilt) |
| point, radius 0 | 1000 W at 2 m / 4 m | 19.82 / 4.97 | P / (4 pi d^2) = 19.89 / 4.97 |
| spot 45 degrees, on axis | 1000 W at 2 m | 19.82 | same as a point light: the cone masks, it does not focus |
| area 1 m square, on axis | 1000 W at 4 m | 19.46 | about P / (pi d^2) = 19.89 |
| area 2 m square, on axis | 1000 W at 4 m | 18.35 | total power fixed (`normalize` True by default) |
| sun with `light.exposure = 1` | strength 1 | 2.00 | power x 2^exposure |

`[exp: experiments/light/light_units.py]`

A spot's pool can be stretched by scaling its object, since the scale applies to the cone. A spot 2 m above a floor,
cone 40 degrees, hard edge: the pool (half the peak) is 1.438 m across, where the cone says 1.456; scaled (2, 1, 1) it is
2.688 m along x (1.869 times) and still 1.438 m along y; scaled 3 along the beam (local z) it narrows to 0.5 m both ways
(2.876 times). An oval museum spot is one spot scaled sideways (`production.md`, item 19).
`[exp: experiments/light/spot_scale.py]`

Soft shadows. A 2 m plate 1 m above the floor, sun straight down, the shadow edge's 5-95 % width (2.3 mm per pixel; a
uniform disc predicts 0.805 of the full penumbra 2 h tan(angle / 2)):

| sun.angle | predicted | Cycles | EEVEE, jitter off | EEVEE, jitter on |
|---|---|---|---|---|
| 0 | 0 | 4.7 mm (pixel filter) | 4.7 | 4.7 |
| 2 degrees | 28 mm | 23 | 19 | 28 |
| 10 degrees | 141 mm | 131 | 98 | 136 |

`[exp: experiments/light/sun_angle_soft_shadow.py]` A new sun's angle is 0.526 degrees. `[exp: experiments/light/light_units.py]`

## A sun at a given elevation and bearing

```python
def sun_rotation(elevation_deg, bearing_deg):        # +Y north, +X east, bearing clockwise from north
    return (math.radians(90 - elevation_deg), 0.0, math.radians(180 - bearing_deg))

sun.rotation_euler = sun_rotation(30, 135)           # 30 degrees up, in the south-east
sky.sun_elevation = math.radians(30)                 # a Nishita sky's sun in the same place:
sky.sun_rotation = math.radians(135)                 # its sun_rotation is the bearing
```

Checked three ways `[exp: experiments/light/sun_elevation.py]`:

- Five pairs of elevation and bearing, from (10, 135) to (60, 225): the light's +Z axis came out at the asked elevation
  and bearing, error 0.0 degrees. `[exp: experiments/light/sun_elevation.py]`
- A 1 m pole's shadow, found by ray casts in 5 mm steps: 1.75 m at elevation 30 (1 / tan 30° = 1.732), 1.015 m at 45
  (1.0) and 2.76 m at 20 (2.747), the excess being the pole's 0.02 m radius; each pointed away from the sun's bearing.
  `[exp: experiments/light/sun_elevation.py]`
- A Nishita sky rendered as an equirectangular panorama at 1 degree a pixel, its orientation fixed by a control lamp
  due east: `sun_rotation` 0, 90, 180 and 270 put the sun disc at bearings 1, 91, 181 and 270, at elevation 30 within
  3 degrees. `[exp: experiments/light/sun_elevation.py]`

In an equirectangular render from a camera at rotation (90, 0, 0) degrees, column = bearing + 180 degrees: north,
where the camera looks, is the image centre, and east is right of centre. `[exp: experiments/light/sun_elevation.py]`

## Light and shadow linking

```python
recv = bpy.data.collections.new("LitBySun")          # need not be linked into the scene
recv.objects.link(ground); recv.objects.link(left)   # each entry starts at link_state INCLUDE
sun.light_linking.receiver_collection = recv         # on the light's object: the sun now lights only these

block = bpy.data.collections.new("NoSunShadow")
block.objects.link(right)
block.collection_objects[0].light_linking.link_state = "EXCLUDE"   # entries pair with block.objects by position
sun.light_linking.blocker_collection = block         # the right sphere casts no shadow from this sun
```

Two spheres on a floor under a sun, a black world, seen from above; linear brightness, the mean of 3 x 3 pixels
`[exp: experiments/light/light_linking.py]`:

| Setup | Engine | Left top | Right top | Left's shadow | Right's shadow | Lit floor |
|---|---|---|---|---|---|---|
| no linking | Cycles | 0.6 | 0.602 | 0.016 | 0.017 | 0.593 |
| receivers: floor and left, INCLUDE | Cycles | 0.6 | 0.0 | 0.016 | 0.017 | 0.591 |
| receivers: right only, EXCLUDE | Cycles | 0.6 | 0.0 | 0.016 | 0.017 | 0.591 |
| blockers: right only, EXCLUDE | Cycles | 0.6 | 0.602 | 0.016 | 0.619 | 0.593 |
| no linking | EEVEE | 0.61 | 0.61 | 0.0 | 0.0 | 0.583 |
| receivers: floor and left, INCLUDE | EEVEE | 0.61 | 0.0 | 0.0 | 0.0 | 0.583 |
| receivers: right only, EXCLUDE | EEVEE | 0.61 | 0.0 | 0.0 | 0.0 | 0.583 |
| blockers: right only, EXCLUDE | EEVEE | 0.61 | 0.61 | 0.0 | 0.583 | 0.583 |

Both engines honour both kinds. A receiver collection of INCLUDE entries lights only them; one of EXCLUDE entries
lights everything else. An object the sun does not light still casts the sun's shadow: only the blocker collection
removes it.

## World

```python
world = bpy.data.worlds.new("World")        # use_nodes False, node_tree None, color (0.05, 0.05, 0.05)
world.use_nodes = True                      # creates Background (Color, Strength, Weight) -> World Output
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")   # by type: node names follow the UI language
bg.inputs["Color"].default_value = (0.5, 0.5, 0.5, 1)
bg.inputs["Strength"].default_value = 1.0
scene.world = world
```

`[exp: experiments/light/world_sky.py]` A uniform world of radiance L lights a horizontal floor with E = pi L (0.5 gave
1.571 in Cycles, 1.557 in EEVEE); Strength multiplies it. `[exp: experiments/light/world_sky.py]` A scene made with
`read_factory_settings(use_empty=True)` has no world and no camera `[exp: experiments/rendering/empty_scene_render.py]`;
with `scene.world = None` the background is black and adds no light. `[exp: experiments/light/light_units.py]`

Sky Texture:

```python
sky = wnt.nodes.new("ShaderNodeTexSky")     # sky_type defaults to NISHITA
wnt.links.new(sky.outputs["Color"], bg.inputs["Color"])
sky.sky_type = "NISHITA"
sky.sun_elevation = math.radians(elev)      # radians; sun_rotation turns it about Z
# PREETHAM / HOSEK_WILKIE take a direction vector instead:
sky.sun_direction = (0, -math.cos(math.radians(45)), math.sin(math.radians(45)))
```

| sky_type | parameters (default) | floor E at sun 45 degrees, Cycles (R, G, B) |
|---|---|---|
| `NISHITA` (default) | `sun_elevation` (15 deg), `sun_rotation` (0), `sun_size` (0.545 deg), `sun_intensity` (1), `sun_disc` (True, Cycles only), `altitude` (0 m), `air_density`, `dust_density`, `ozone_density` (1 each) | 111, 94, 78 with the disc; 7.3, 9.1, 13.1 without |
| `PREETHAM` | `sun_direction` ((0, 0, 1)), `turbidity` (2.2) | 1.0, 1.5, 2.7 |
| `HOSEK_WILKIE` | `sun_direction`, `turbidity`, `ground_albedo` (0.3) | 0.13, 0.22, 0.39 |

Nishita in Cycles by elevation (green channel): 5 degrees 7.2, 15 degrees 30, 45 degrees 94, 90 degrees 136.
`[exp: experiments/light/world_sky.py]` In 4.5 the sky types are `PREETHAM`, `HOSEK_WILKIE`, `NISHITA`. `[inv]`

Environment texture (HDRI):

```python
env = wnt.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(path)      # an EXR/HDR loads as 'Linear Rec.709'
wnt.links.new(env.outputs["Color"], bg.inputs["Color"])
```

A uniform 0.25 equirectangular EXR lit the floor with 0.786 (pi x 0.25 = 0.785). `[exp: experiments/light/world_sky.py]`
To rotate an HDRI, put a Texture Coordinate (Generated) -> Mapping (Rotation Z) in front of the Vector input; the
Mapping node and the direction it turns the lighting are measured in `materials.md` (Rotating an HDRI).

## Shadow catcher (Cycles)

```python
floor.is_shadow_catcher = True              # Object property
scene.render.film_transparent = True
# leave view_layer.cycles.use_pass_shadow_catcher off to get the shadow in Combined's alpha
```

With the pass off, Combined under the shadow read RGBA (0, 0, 0, 0.77), open floor (0, 0, 0, 0.001), the cube itself
(0.82, 0.82, 0.82, 1). With the pass on, Combined read alpha 0 under the shadow and the "Shadow Catcher" pass read 0.23
there and 1.0 on open floor. `[exp: experiments/light/shadow_catcher.py]` With the pass on "all indirect light
interactions are captured. With it disabled, a simple approximation is used instead."
`[doc: https://docs.blender.org/manual/en/4.5/render/cycles/object_settings/object_data.html]`

## Camera

A new camera: lens 50 mm, sensor 36 x 24 mm, `sensor_fit` AUTO, clip 0.1 to 1000 m, perspective, `ortho_scale` 6,
depth of field off at f/2.8. `camera.angle` = 2 atan(sensor_width / 2 / lens) = 39.6 degrees.
`[exp: experiments/camera/camera_projection.py]`

```python
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.location = (5, -6, 3.5)
cam.rotation_euler = (Vector((0.5, 0, 0.8)) - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.collection.objects.link(cam)
scene.camera = cam
```

`[exp: experiments/rendering/cycles_metal_vs_cpu.py]` Without `scene.camera`, `bpy.ops.render.render()` raises
`RuntimeError: Error: Cannot render, no camera` in every engine, and the Blender process then exits 1 even when the
script catches the error. `[exp: experiments/rendering/empty_scene_render.py]`

Aiming with a constraint instead (defaults are already right for cameras and lights):

```python
con = b.constraints.new("TRACK_TO")          # track_axis TRACK_NEGATIVE_Z, up_axis UP_Y by default
con.target = target
bpy.context.view_layer.update()              # before reading b.matrix_world
```

Both put the target at (0.5, 0.5) with the same up vector; the constraint leaves `rotation_euler` at (0, 0, 0), so read
`matrix_world`. `[exp: experiments/camera/camera_aim_dof.py]`

### Where a point lands in the image

```python
from bpy_extras.object_utils import world_to_camera_view
bpy.context.view_layer.update()
p = world_to_camera_view(scene, cam, ball.location)     # x, y in 0..1 from the bottom-left; z = depth along the view
W = scene.render.resolution_x * scene.render.resolution_percentage / 100
H = scene.render.resolution_y * scene.render.resolution_percentage / 100
pixel = (p.x * W, (1 - p.y) * H)                        # image row 0 at the top
```

Against the rendered centroid of a small emissive ball, this was within 0.31 px in every case: landscape and portrait,
`sensor_fit` AUTO and HORIZONTAL, 25 and 50 mm, `shift_x` 0.1 / `shift_y` -0.05, `resolution_percentage` 50, and
orthographic. A point is in frame when 0 <= x, y <= 1 and z > 0. `[exp: experiments/camera/camera_projection.py]`

Rules the same check confirmed: with AUTO fit the sensor width spans the longer side of the image (portrait frames
fit it vertically); shift is a fraction of the longer side; `ortho_scale` is the frame's extent in metres along the
longer side (a point 3 m right of centre at `ortho_scale` 6 sits at x = 1.0).
`[exp: experiments/camera/camera_projection.py]`

### Framing objects

`bpy.ops.view3d.camera_to_view_selected()` ran in background mode with no 3D viewport: it moved the active camera,
keeping its rotation, until the selected object filled the frame (ball centred at 0.5, 0.5). It fits the vertices; the
bounding-box corners of a sphere can stick out (y -0.125..1.125). `[exp: experiments/camera/camera_projection.py]`

### Depth of field

```python
cam.data.dof.use_dof = True
cam.data.dof.focus_object = cards[0]         # or focus_distance in metres
cam.data.dof.aperture_fstop = 1.4
```

With 50 mm at f/1.4 and 256 px, the in-focus card stayed as sharp as without DOF (2 px edge) and the other blurred to
3-4 px, near the thin-lens blur circle of 4.3 px. `[exp: experiments/camera/camera_aim_dof.py]`

## Reference: light and camera properties

| property | default | note |
|---|---|---|
| `energy` (on `SunLight`, `PointLight`, `SpotLight`, `AreaLight`) | 10 via `lights.new` | W, or W/m2 for a sun `[exp: experiments/light/light_units.py]` |
| `SunLight.angle` | 0.526 deg | angular diameter |
| `PointLight.shadow_soft_size`, `SpotLight.shadow_soft_size` | 0 via `lights.new` | radius in m `[inv]` |
| `AreaLight.size` | 0.25 m | `shape` SQUARE, RECTANGLE, DISK, ELLIPSE `[inv]` |
| `Light.normalize` | True | power is total output whatever the size |
| `Light.exposure` | 0 | power x 2^exposure |
| `use_shadow_jitter` (on each light type) | False | EEVEE soft shadows from light size |
| `Light.use_temperature`, `temperature` | False, 6500 K | `[inv]` |
| `World.sun_threshold` | 10 | EEVEE: world values above this are extracted as a sun `[inv]` |
| `World.use_sun_shadow` | True | EEVEE `[inv]` |
| `Camera.lens`, `sensor_width`, `sensor_fit` | 50, 36, AUTO | |
| `Camera.shift_x`, `shift_y` | 0 | fraction of the longer side |
| `Camera.type` | PERSP | ORTHO, PANO, CUSTOM `[inv]` |
| `Camera.dof.use_dof`, `aperture_fstop`, `focus_distance` | False, 2.8, 10 m | `[inv]` |
| `Object.is_shadow_catcher`, `is_holdout` | False | Cycles |
