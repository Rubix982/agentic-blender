"""Two things an animation task needs and v1 did not show (found by the C-001 comparison, evals/results.md):
repeating keys forever with the Cycles F-modifier, and keyframing values that are not object properties: a material's
node input and a Geometry Nodes modifier input. Where does each action live, and does a render see the animated value?"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import math
import bpy
import OpenImageIO as oiio
from bpy_extras import anim_utils
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
vl = bpy.context.view_layer
scene.frame_start, scene.frame_end = 1, 96


def fcurve(id_block, path, index=0):
    ad = id_block.animation_data
    return anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot).fcurves.find(path, index=index)


def value_at(frame, get):
    scene.frame_set(frame)
    return round(get(), 4)


# 1. a back-and-forth slide, repeated by a Cycles modifier
ob = bpy.data.objects.new("Slider", bpy.data.meshes.new("Slider"))
scene.collection.objects.link(ob)
for f, x in ((1, 0.0), (25, 2.0), (49, 0.0)):
    ob.location.x = x
    ob.keyframe_insert("location", index=0, frame=f)
fc = fcurve(ob, "location", 0)
x = lambda: ob.location.x
before = dict(f13=value_at(13, x), f61=value_at(61, x), f73=value_at(73, x))
E.fact("without a modifier the curve holds its last key after frame 49 (extrapolation CONSTANT)",
       extrapolation=fc.extrapolation, **before)
mod = fc.modifiers.new("CYCLES")
E.fact("a new Cycles F-modifier starts at mode REPEAT both ways with 0 cycles (0 = forever), though the registered "
       "default of the modes is NONE", type=mod.type, mode_before=mod.mode_before, mode_after=mod.mode_after,
       cycles_before=mod.cycles_before, cycles_after=mod.cycles_after)
stale = dict(f61=value_at(61, x), f73=value_at(73, x), evaluate_f61=round(fc.evaluate(61), 4))
E.fact("a modifier added after the scene was evaluated (frame_set above) is ignored by frame_set: frame 61 still reads "
       "the held last key, though fcurve.evaluate(61) already gives the repeat", **stale)
ob.animation_data.action.update_tag()
after = dict(f13=value_at(13, x), f61=value_at(61, x), f73=value_at(73, x), f97=value_at(97, x), f_minus_11=value_at(-11, x))
E.fact("after action.update_tag() the 48-frame cycle repeats: frame 61 equals frame 13 and frame 73 equals frame 25 "
       "(x = 2), and frames before the first key repeat too", **after)

# 2. a material's node input, keyed
mat = bpy.data.materials.new("Glow")
mat.use_nodes = True
nt = mat.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
em = nt.nodes.new("ShaderNodeEmission")
em.name = "Emission"
nt.links.new(em.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
strength = em.inputs["Strength"]
for f, v in ((1, 0.0), (25, 10.0)):
    strength.default_value = v
    strength.keyframe_insert("default_value", frame=f)
ntfc = fcurve(nt, 'nodes["Emission"].inputs[1].default_value')
E.fact("keyframing a node input puts the action on the material's node tree, not on the material: "
       "mat.animation_data stays None", material_anim=mat.animation_data is not None,
       tree_action=nt.animation_data.action.name if nt.animation_data and nt.animation_data.action else None,
       slot=nt.animation_data.action_slot.identifier, data_path=ntfc.data_path if ntfc else None,
       in_bpy_data_actions=nt.animation_data.action.name in bpy.data.actions)
E.fact("while the material is on no object it is not evaluated: after frame_set the input still reads the last value "
       "set (10), and only fcurve.evaluate gives the keyed value (Bezier: halfway in time is halfway in value)",
       users=mat.users, f1=value_at(1, lambda: strength.default_value), f13=value_at(13, lambda: strength.default_value),
       evaluate_f1=round(ntfc.evaluate(1), 4), evaluate_f13=round(ntfc.evaluate(13), 4))

# does a render see it? an emissive plane filling an orthographic camera, rendered at frames 1, 13 and 25
bpy.ops.mesh.primitive_plane_add(size=2)
plane = bpy.context.object
plane.data.materials.append(mat)
vl.update()
dg = bpy.context.evaluated_depsgraph_get()
ev = lambda: mat.evaluated_get(bpy.context.evaluated_depsgraph_get()).node_tree.nodes["Emission"].inputs[1].default_value
E.fact("once the material is on an object in the scene, frame_set animates it: the original input and the evaluated "
       "copy both read the keyed value", f13_original=value_at(13, lambda: strength.default_value), f13_evaluated=round(ev(), 4),
       f1_original=value_at(1, lambda: strength.default_value))
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 1
cam.location = (0, 0, 5)
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.engine = "CYCLES"
scene.cycles.samples = 4
scene.cycles.use_denoising = False
scene.render.resolution_x = scene.render.resolution_y = 16
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"
scene.view_settings.view_transform = "Standard"
renders = {}
for f in (1, 13, 25):
    scene.frame_set(f)
    scene.render.filepath = E.out("tmp.exr")
    bpy.ops.render.render(write_still=True)
    renders[f"f{f}"] = round(float(oiio.ImageBuf(scene.render.filepath).get_pixels(oiio.FLOAT)[:, :, 0].mean()), 3)
    os.remove(scene.render.filepath)
E.fact("a render at each frame shows the keyed strength (linear pixel value = strength for an emission plane)", **renders)

# 3. a Geometry Nodes modifier input, keyed
ng = bpy.data.node_groups.new("Scaler", "GeometryNodeTree")
ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
sock = ng.interface.new_socket(name="Scale", in_out="INPUT", socket_type="NodeSocketFloat")
gi, go = ng.nodes.new("NodeGroupInput"), ng.nodes.new("NodeGroupOutput")
tr = ng.nodes.new("GeometryNodeTransform")
ng.links.new(gi.outputs["Geometry"], tr.inputs["Geometry"])
ng.links.new(tr.outputs["Geometry"], go.inputs["Geometry"])
bpy.ops.mesh.primitive_cube_add(size=1)
cube = bpy.context.object
gn = cube.modifiers.new("GN", "NODES")
gn.node_group = ng
ident = sock.identifier
path = f'modifiers["GN"]["{ident}"]'
for f, v in ((1, 1.0), (25, 3.0)):
    gn[ident] = v
    cube.keyframe_insert(data_path=path, frame=f)
gfc = fcurve(cube, path)
E.fact("a Geometry Nodes input is keyed on the object with data path modifiers[\"GN\"][\"<identifier>\"]; the curve "
       "lives in the object's action", identifier=ident, data_path=gfc.data_path if gfc else None,
       f13=value_at(13, lambda: gn[ident]))
try:
    gn.keyframe_insert(f'["{ident}"]', frame=49)
    via_mod = "ok"
except Exception as e:
    via_mod = f"{type(e).__name__}: {e}"
E.fact("keying through the modifier itself (mod.keyframe_insert('[\"<identifier>\"]')) gives this", result=via_mod,
       keys=len(gfc.keyframe_points))
E.save()
