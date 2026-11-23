"""C-005: build the brief's shot (CARD.md) and save it as out/scene.blend. Run from the repository root:
    python3 skills/blender/scripts/run.py shots/morning-clearing/build.py -- shots/morning-clearing/out/scene.blend
Every step comes from the guide's pages (named in the comments); assets come through scripts/assets.py (Poly Haven,
CC0; run `assets.py get` for each id in ASSETS first)."""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.stdout.reconfigure(line_buffering=True)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "blender", "scripts"))
import asset_import as ai  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0]) if argv else os.path.join(HERE, "out", "scene.blend")
ASSETS = dict(hdri="autumn_forest_04", ground="forest_leaves_04", boulder="boulder_01", fern="fern_02",
              stump="tree_stump_01", trunk="dead_tree_trunk_02", rock="rock_09", sorrel="shrub_sorrel_01")
SUN_BEARING = 30.0          # where the sun should stand: ahead and to the right of a camera looking north (+Y)

bpy.ops.wm.read_factory_settings(use_empty=True)                     # SKILL.md: the skeleton
scene = bpy.context.scene
scene.render.fps, scene.frame_start, scene.frame_end = 24, 1, 240
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 1280, 720, 100
report = {}

# ---------------------------------------------------------------- light: HDRI turned so its sun is where we want it
sky = ai.manifest("polyhaven", ASSETS["hdri"], "4k")
e0, b0 = ai.hdri_sun(sky, 0)                                          # remote-assets.md: where the HDRI's sun is
rot = SUN_BEARING - b0
ai.world_from_hdri(sky, strength=0.7, rotation_deg=rot)
elev, bear = ai.hdri_sun(sky, rot)
report["hdri_sun"] = dict(elevation=round(elev, 1), bearing=round(bear, 1), rotation=round(rot, 1))
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))    # a Sun light on the HDRI's sun (7 of 17)
sun.rotation_euler = (math.radians(90 - elev), 0, math.radians(180 - bear))   # light-world-camera.md
sun.data.energy = 4.0
sun.data.angle = math.radians(1.5)
sun.data.use_temperature, sun.data.temperature = True, 4300           # realism.md: a warm morning sun
scene.collection.objects.link(sun)
to_sun = (sun.matrix_basis.to_3x3() @ Vector((0, 0, 1))).normalized()

# ---------------------------------------------------------------- the floor: leaf litter at real size, gently uneven
bpy.ops.mesh.primitive_grid_add(x_subdivisions=240, y_subdivisions=240, size=36)
ground = bpy.context.object
ground.name = "Ground"
gm = ai.manifest("polyhaven", ASSETS["ground"])
ground.data.materials.append(ai.material_from_maps(gm, displacement_m=0.03))
ai.uvs_to_real_size(ground, gm["size_m"])                             # remote-assets.md
tex = bpy.data.textures.new("Undulate", "CLOUDS")
tex.noise_scale = 3.0
disp = ground.modifiers.new("Undulate", "DISPLACE")
disp.texture, disp.strength, disp.mid_level = tex, 0.35, 0.5
disp.texture_coords = "GLOBAL"


def ground_height(x, y, r=0.7):
    """The displaced ground's median height within r of (x, y), read from the evaluated mesh."""
    bpy.context.view_layer.update()
    me = ground.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    zs = sorted(v.co.z for v in me.vertices if (v.co.x - x) ** 2 + (v.co.y - y) ** 2 < r * r)
    return zs[len(zs) // 2] if zs else 0.0


def place(key, loc, rot_z=0.0, scale=1.0, sink=0.06):
    """Import a Poly Haven model and seat it on the displaced ground at (x, y), its lowest point sink metres below
    the ground's median height there (the floor is displaced, so a flat z would leave it floating or buried)."""
    loc = (loc[0], loc[1], ground_height(loc[0], loc[1]) - sink)
    objs, size = ai.import_model(ai.manifest("polyhaven", ASSETS[key]))
    meshes = [o for o in objs if o.type == "MESH"]
    root = next((o for o in objs if o.parent is None), objs[0])
    bpy.context.view_layer.update()
    lo = min((o.matrix_world @ v.co).z for o in meshes for v in o.data.vertices)
    root.location = (loc[0], loc[1], root.location.z - lo + loc[2])
    root.rotation_euler.z += math.radians(rot_z)
    root.scale = [s * scale for s in root.scale]
    return objs, size


# ---------------------------------------------------------------- the boulder, with moss on what faces the sky
objs, size = place("boulder", (0, 0), sink=0.1)
boulder = next(o for o in objs if o.type == "MESH")
report["boulder_size_m"] = [round(s, 4) for s in size]
report["boulder_stated_m"] = ai.manifest("polyhaven", ASSETS["boulder"])["size_m"]
mat = boulder.active_material
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
base_link = bsdf.inputs["Base Color"].links[0] if bsdf.inputs["Base Color"].is_linked else None
geo = nt.nodes.new("ShaderNodeNewGeometry")
up = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(geo.outputs["Normal"], up.inputs["Vector"])
r_up = nt.nodes.new("ShaderNodeValToRGB")                             # realism.md: facing up through a ColorRamp
r_up.color_ramp.elements[0].position, r_up.color_ramp.elements[1].position = 0.55, 0.85
nt.links.new(up.outputs["Z"], r_up.inputs["Fac"])
nz = nt.nodes.new("ShaderNodeTexNoise")
nz.inputs["Scale"].default_value = 3.0
nz.inputs["Detail"].default_value = 6.0
nt.links.new(nt.nodes.new("ShaderNodeTexCoord").outputs["Object"], nz.inputs["Vector"])   # realism.md: Object coords
r_nz = nt.nodes.new("ShaderNodeValToRGB")
r_nz.color_ramp.elements[0].position, r_nz.color_ramp.elements[1].position = 0.42, 0.58
nt.links.new(nz.outputs["Fac"], r_nz.inputs["Fac"])
mask = nt.nodes.new("ShaderNodeMath")
mask.operation = "MULTIPLY"
nt.links.new(r_up.outputs["Color"], mask.inputs[0])
nt.links.new(r_nz.outputs["Color"], mask.inputs[1])
moss = nt.nodes.new("ShaderNodeMix")
moss.data_type = "RGBA"
moss.inputs["B"].default_value = (0.09, 0.16, 0.03, 1)
nt.links.new(mask.outputs[0], moss.inputs["Factor"])
if base_link:
    nt.links.new(base_link.from_socket, moss.inputs["A"])
nt.links.new(moss.outputs["Result"], bsdf.inputs["Base Color"])
rough = nt.nodes.new("ShaderNodeMix")                                # moss is rougher than stone
rough.data_type = "FLOAT"
rough.inputs["B"].default_value = 0.95
nt.links.new(mask.outputs[0], rough.inputs["Factor"])
if bsdf.inputs["Roughness"].is_linked:
    nt.links.new(bsdf.inputs["Roughness"].links[0].from_socket, rough.inputs["A"])
else:
    rough.inputs["A"].default_value = bsdf.inputs["Roughness"].default_value
nt.links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])

# ---------------------------------------------------------------- the fallen trunk and the stump
place("trunk", (1.6, 1.1), rot_z=28, sink=0.05)
place("stump", (-2.6, 2.4), rot_z=-15, sink=0.05)

# ---------------------------------------------------------------- scattering by painted density (realism.md)
lib = bpy.data.collections.new("Library")
scene.collection.children.link(lib)
sources = {}
for key in ("fern", "rock", "sorrel"):
    objs, _ = ai.import_model(ai.manifest("polyhaven", ASSETS[key]))
    bpy.context.view_layer.update()
    src = next(o for o in objs if o.type == "MESH")
    # glTF's Y-up turn sits on the object (or its parent), not the mesh, and Object Info in ORIGINAL space instances
    # the bare mesh: bake the world transform into the mesh first, or the instances lie on their side
    src.data.transform(src.matrix_world)
    src.parent = None
    src.matrix_world = __import__("mathutils").Matrix.Identity(4)
    for o in objs:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        lib.objects.link(o)
    src.location.z = -50                                              # out of sight; instanced below
    sources[key] = src
bpy.context.view_layer.update()
me = ground.data
weights = {k: me.attributes.new(f"density_{k}", "FLOAT", "POINT") for k in sources}
for i, v in enumerate(me.vertices):
    x, y = v.co.x, v.co.y
    d = math.hypot(x, y)
    corridor = abs(x) < 0.9 and -9 < y < -1.3                          # keep the camera's way clear
    near = math.exp(-((d - 1.6) ** 2) / 2.0)                          # a ring round the boulder
    sides = math.exp(-((abs(x) - 1.5) ** 2) / 0.15) if -6.5 < y < -2.0 else 0.0  # foreground, inside the 35 mm view
    weights["fern"].data[i].value = 0.0 if corridor else min(1.0, 0.4 + 0.6 * near + sides)
    weights["sorrel"].data[i].value = 0.15 if corridor else 0.5 + 0.5 * near
    weights["rock"].data[i].value = 0.06 + 0.94 * math.exp(-(d ** 2) / 1.5)

ng = bpy.data.node_groups.new("Scatter", "GeometryNodeTree")
ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
N, L = ng.nodes, ng.links
gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
join = N.new("GeometryNodeJoinGeometry")
L.new(gi.outputs["Geometry"], join.inputs["Geometry"])                # keep the ground itself
DENS = dict(fern=1.4, sorrel=2.0, rock=2.5)
SCALE = dict(fern=(0.35, 0.7), sorrel=(1.5, 3.0), rock=(0.5, 1.4))
for seed, key in enumerate(sources):
    dist = N.new("GeometryNodeDistributePointsOnFaces")
    dist.inputs["Seed"].default_value = seed
    w = N.new("GeometryNodeInputNamedAttribute")
    w.data_type = "FLOAT"
    w.inputs["Name"].default_value = f"density_{key}"
    mul = N.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = DENS[key]
    L.new(w.outputs["Attribute"], mul.inputs[0])
    L.new(mul.outputs[0], dist.inputs["Density"])
    L.new(gi.outputs["Geometry"], dist.inputs["Mesh"])
    info = N.new("GeometryNodeObjectInfo")
    info.inputs["Object"].default_value = sources[key]
    info.inputs["As Instance"].default_value = True
    info.transform_space = "ORIGINAL"
    rz = N.new("FunctionNodeRandomValue")
    rz.data_type = "FLOAT"
    rz.inputs["Max"].default_value = 2 * math.pi
    rz.inputs["Seed"].default_value = seed + 10
    comb = N.new("ShaderNodeCombineXYZ")
    L.new(rz.outputs["Value"], comb.inputs["Z"])
    rs = N.new("FunctionNodeRandomValue")
    rs.data_type = "FLOAT"
    rs.inputs["Min"].default_value, rs.inputs["Max"].default_value = SCALE[key]
    rs.inputs["Seed"].default_value = seed + 20
    inst = N.new("GeometryNodeInstanceOnPoints")
    L.new(dist.outputs["Points"], inst.inputs["Points"])
    L.new(info.outputs["Geometry"], inst.inputs["Instance"])
    L.new(comb.outputs["Vector"], inst.inputs["Rotation"])
    L.new(rs.outputs["Value"], inst.inputs["Scale"])
    L.new(inst.outputs["Instances"], join.inputs["Geometry"])
L.new(join.outputs["Geometry"], go.inputs["Geometry"])
gn = ground.modifiers.new("Scatter", "NODES")                         # after Undulate: points land on the bumps
gn.node_group = ng

# ---------------------------------------------------------------- a canopy the camera cannot see: dappled light
bpy.ops.mesh.primitive_plane_add(size=1)
canopy = bpy.context.object
canopy.name = "Canopy"
canopy.scale = (40, 40, 1)
canopy.location = Vector((0, 0, 0.5)) + to_sun * 14
canopy.rotation_euler = to_sun.to_track_quat("Z", "Y").to_euler()
canopy.visible_camera = False                                         # realism.md: hidden shadow casters
cm = bpy.data.materials.new("Canopy")
cm.use_nodes = True
ct = cm.node_tree
for n in list(ct.nodes):
    ct.nodes.remove(n)
leaf_noise = ct.nodes.new("ShaderNodeTexNoise")
leaf_noise.inputs["Scale"].default_value = 0.35
leaf_noise.inputs["Detail"].default_value = 8.0
leaf_noise.inputs["Roughness"].default_value = 0.65
ct.links.new(ct.nodes.new("ShaderNodeTexCoord").outputs["Object"], leaf_noise.inputs["Vector"])
holes = ct.nodes.new("ShaderNodeValToRGB")
holes.color_ramp.elements[0].position, holes.color_ramp.elements[1].position = 0.47, 0.53
ct.links.new(leaf_noise.outputs["Fac"], holes.inputs["Fac"])
mix = ct.nodes.new("ShaderNodeMixShader")
ct.links.new(holes.outputs["Color"], mix.inputs["Fac"])
dark = ct.nodes.new("ShaderNodeBsdfDiffuse")
dark.inputs["Color"].default_value = (0.02, 0.03, 0.01, 1)
ct.links.new(dark.outputs[0], mix.inputs[1])
ct.links.new(ct.nodes.new("ShaderNodeBsdfTransparent").outputs[0], mix.inputs[2])
ct.links.new(mix.outputs[0], ct.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
canopy.data.materials.append(cm)

# ---------------------------------------------------------------- haze: a ground layer, drifting (realism.md)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 4, 2.5))
fog = bpy.context.object
fog.name = "Haze"
fog.scale = (44, 44, 5)
fm = bpy.data.materials.new("Haze")
fm.use_nodes = True
ft = fm.node_tree
for n in list(ft.nodes):
    ft.nodes.remove(n)
vol = ft.nodes.new("ShaderNodeVolumePrincipled")
vol.inputs["Anisotropy"].default_value = 0.55                         # forward scattering: glow towards the sun
coord = ft.nodes.new("ShaderNodeTexCoord")
mp = ft.nodes.new("ShaderNodeMapping")
ft.links.new(coord.outputs["Object"], mp.inputs["Vector"])
wisp = ft.nodes.new("ShaderNodeTexNoise")
wisp.inputs["Scale"].default_value = 2.5
ft.links.new(mp.outputs["Vector"], wisp.inputs["Vector"])
dens = ft.nodes.new("ShaderNodeMath")
dens.operation = "MULTIPLY_ADD"                                        # 0.03 x noise + 0.004
dens.inputs[1].default_value, dens.inputs[2].default_value = 0.03, 0.004
ft.links.new(wisp.outputs["Fac"], dens.inputs[0])
ft.links.new(dens.outputs[0], vol.inputs["Density"])
ft.links.new(vol.outputs["Volume"], ft.nodes.new("ShaderNodeOutputMaterial").inputs["Volume"])
fog.data.materials.append(fm)
loc = mp.inputs["Location"]
loc.default_value = (0, 0, 0)
loc.keyframe_insert("default_value", frame=1)                         # animation-video.md: a node input's action
loc.default_value = (0.06, 0.02, 0)                                    # lives on the node tree; object coords of a
loc.keyframe_insert("default_value", frame=240)                       # 44 m cube: 0.06 is about 2.6 m of drift
from bpy_extras import anim_utils  # noqa: E402
ad = ft.animation_data
for fc in anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot).fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = "LINEAR"                                   # animation-video.md: keys are BEZIER by default

# ---------------------------------------------------------------- the camera: a slow dolly, focused on the boulder
target = bpy.data.objects.new("Focus", None)
target.location = (0, 0, 0.55)
scene.collection.objects.link(target)
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
scene.collection.objects.link(cam)
scene.camera = cam
cam.data.lens = 35
cam.data.dof.use_dof = True                                           # light-world-camera.md
cam.data.dof.focus_object = target
cam.data.dof.aperture_fstop = 4.0
tt = cam.constraints.new("TRACK_TO")
tt.target, tt.track_axis, tt.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"
cam.location = (0.7, -7.2, 1.45)
cam.keyframe_insert("location", frame=1)
cam.location = (0.25, -4.4, 1.2)
cam.keyframe_insert("location", frame=240)                            # Bezier keys: it eases in and out

# ---------------------------------------------------------------- render settings (rendering.md)
scene.render.engine = "CYCLES"
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
report["device"] = scene.cycles.device
scene.cycles.samples = 128
scene.cycles.adaptive_threshold = 0.03
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPENIMAGEDENOISE"
scene.render.use_persistent_data = True                               # animation-video.md: far faster per frame
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.view_settings.exposure = 0.3
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_depth = "8"
scene.render.use_overwrite = False                                    # resume: skip frames already written
scene.render.use_placeholder = True
scene.render.filepath = os.path.join(os.path.dirname(OUT), "frames", "")

# ---------------------------------------------------------------- the finish, in the compositor (realism.md)
scene.use_nodes = True
tree = scene.node_tree
for n in list(tree.nodes):
    tree.nodes.remove(n)
rl = tree.nodes.new("CompositorNodeRLayers")
glare = tree.nodes.new("CompositorNodeGlare")
glare.glare_type = "FOG_GLOW"                                          # a new Glare node starts as STREAKS
glare.quality = "HIGH"
glare.inputs["Threshold"].default_value = 1.2
glare.inputs["Strength"].default_value = 0.35
tree.links.new(rl.outputs["Image"], glare.inputs["Image"])
grade = tree.nodes.new("CompositorNodeColorBalance")
grade.correction_method = "LIFT_GAMMA_GAIN"
next(s for s in grade.inputs if s.identifier == "Color Gain").default_value = (1.04, 1.0, 0.95, 1)
tree.links.new(glare.outputs["Image"], next(s for s in grade.inputs if s.identifier == "Image"))
ell = tree.nodes.new("CompositorNodeEllipseMask")
ell.inputs["Size"].default_value = (1.0, 1.0)
blur = tree.nodes.new("CompositorNodeBlur")
blur.filter_type = "GAUSS"
blur.inputs["Size"].default_value = (240, 240)
tree.links.new(ell.outputs["Mask"], blur.inputs["Image"])
vig = tree.nodes.new("CompositorNodeMixRGB")
vig.blend_type = "MULTIPLY"
vig.inputs["Fac"].default_value = 0.3                                 # realism.md: Fac 1 blackens the corners
tree.links.new(grade.outputs["Image"], vig.inputs[1])
tree.links.new(blur.outputs["Image"], vig.inputs[2])
clean = tree.nodes.new("CompositorNodeOutputFile")                    # compositing.md: the frame before grain,
clean.base_path = os.path.join(os.path.dirname(OUT), "clean", "")     # for the flicker check
clean.format.file_format = "PNG"
clean.file_slots[0].path = ""
tree.links.new(vig.outputs["Image"], clean.inputs[0])
gtex = bpy.data.textures.new("Grain", "NOISE")
gnode = tree.nodes.new("CompositorNodeTexture")
gnode.texture = gtex
grain = tree.nodes.new("CompositorNodeMixRGB")
grain.blend_type = "OVERLAY"
grain.inputs["Fac"].default_value = 0.06                              # realism.md: a new pattern every frame
tree.links.new(vig.outputs["Image"], grain.inputs[1])
tree.links.new(gnode.outputs["Color"], grain.inputs[2])
comp = tree.nodes.new("CompositorNodeComposite")
tree.links.new(grain.outputs["Image"], comp.inputs["Image"])

bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
report["instances"] = sum(1 for i in dg.object_instances if i.is_instance)
report["objects"] = len(bpy.data.objects)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("BUILD", report, flush=True)
