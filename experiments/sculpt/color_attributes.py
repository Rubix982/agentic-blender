"""Painting by data with colour attributes in 4.5: the four kinds (BYTE_COLOR or FLOAT_COLOR, on POINT or CORNER),
what a new one holds, whether each reaches a Cycles and an EEVEE render through the Color Attribute node at the value
written (linear), what happens to values above 1, which attribute an empty layer_name reads, the Attribute node as an
alternative, and how fast the colours can be written."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import time

import bmesh
import bpy
import numpy as np
import OpenImageIO as oiio
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
KINDS = [("BYTE_COLOR", "POINT"), ("BYTE_COLOR", "CORNER"), ("FLOAT_COLOR", "POINT"), ("FLOAT_COLOR", "CORNER")]


def quad(name, x):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=0.4)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location.x = x
    scene.collection.objects.link(ob)
    return ob


def emit_material(name, node_kind, layer):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    if node_kind == "color":
        n = nt.nodes.new("ShaderNodeVertexColor"); n.layer_name = layer
        nt.links.new(n.outputs["Color"], em.inputs["Color"])
    else:
        n = nt.nodes.new("ShaderNodeAttribute"); n.attribute_name = layer
        nt.links.new(n.outputs["Color"], em.inputs["Color"])
    return m


# What a new attribute of each kind holds.
probe = quad("probe", 100)
starts = {}
for t, dmn in KINDS:
    a = probe.data.color_attributes.new(f"{t}_{dmn}", t, dmn)
    starts[f"{t} {dmn}"] = [round(x, 4) for x in a.data[0].color]
E.fact("a new colour attribute of any of the four kinds starts white and opaque, (1, 1, 1, 1)", **starts)
bpy.data.objects.remove(probe)

value = (0.5, 0.25, 0.1, 1.0)
hdr = (2.0, 0.5, 0.05, 1.0)
obs = []
for i, (t, dmn) in enumerate(KINDS):
    ob = quad(f"{t}_{dmn}", i * 1.0 - 1.5)
    a = ob.data.color_attributes.new("paint", t, dmn)
    a.data.foreach_set("color", np.tile(np.array(value, np.float32), len(a.data)))
    ob.data.materials.append(emit_material(f"m{i}", "color", "paint"))
    obs.append(ob)
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.data.type = "ORTHO"; cam.data.ortho_scale = 4.0
cam.location = (0, 0, 5)
scene.collection.objects.link(cam); scene.camera = cam
scene.world = bpy.data.worlds.new("W")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
scene.render.resolution_x, scene.render.resolution_y = 256, 64
scene.view_settings.view_transform = "Standard"
scene.render.image_settings.file_format = "OPEN_EXR"
path = E.out("ca.exr")


def render(engine):
    scene.render.engine = engine
    if engine == "CYCLES":
        scene.cycles.samples = 4
        scene.cycles.use_denoising = False
    else:
        scene.eevee.taa_render_samples = 4
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    px = oiio.ImageBuf(path).get_pixels(oiio.FLOAT)       # (h, w, c), top row first
    out = []
    for i in range(4):
        x = int((i * 1.0 - 1.5 + 2.0) / 4.0 * 256)
        out.append([round(float(v), 4) for v in px[32, x, :3]])
    return out


cyc = render("CYCLES")
eev = render("BLENDER_EEVEE_NEXT")
E.fact("all four kinds render at the linear value written, (0.5, 0.25, 0.1), in Cycles and in EEVEE, through the Color "
       "Attribute node (BYTE_COLOR to within its 8-bit sRGB step)",
       kinds=[f"{t} {d}" for t, d in KINDS], cycles=cyc, eevee=eev)

for ob in obs:
    a = ob.data.color_attributes["paint"]
    a.data.foreach_set("color", np.tile(np.array(hdr, np.float32), len(a.data)))
read_back = {f"{t} {d}": [round(x, 4) for x in ob.data.color_attributes["paint"].data[0].color]
             for (t, d), ob in zip(KINDS, obs)}
hdr_cyc = render("CYCLES")
E.fact("a value above 1 (2.0, 0.5, 0.05): FLOAT_COLOR keeps it; BYTE_COLOR clamps it to 1",
       read_back=read_back, cycles=hdr_cyc)

# Which attribute does an empty layer_name read: the active one or the render (default) one?
for ob in obs:
    ob.hide_render = True
ob = quad("two", 0.0)
me = ob.data
a1 = me.color_attributes.new("first", "FLOAT_COLOR", "POINT")
a1.data.foreach_set("color", np.tile(np.array((1, 0, 0, 1), np.float32), len(a1.data)))
a2 = me.color_attributes.new("second", "FLOAT_COLOR", "POINT")
a2.data.foreach_set("color", np.tile(np.array((0, 0, 1, 1), np.float32), len(a2.data)))
idx = dict(active_color_name=me.color_attributes.active_color_name, default_color_name=me.color_attributes.default_color_name,
           render_color_index=me.color_attributes.render_color_index, active_color_index=me.color_attributes.active_color_index)
me.materials.append(emit_material("empty", "color", ""))


def at_origin():
    scene.render.engine = "CYCLES"
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    px = oiio.ImageBuf(path).get_pixels(oiio.FLOAT)
    return [round(float(v), 3) for v in px[32, 128, :3]]


start = at_origin()
me.color_attributes.active_color = a2
after_active = at_origin()
me.color_attributes.render_color_index = me.color_attributes.find("second")
after_render = at_origin()
E.fact("an empty layer_name on the Color Attribute node reads the render (default) colour attribute, which is the "
       "first one made; changing the active one does not change the render",
       indices_at_start=idx, first_is_red_second_blue=True, empty_name_at_start=start,
       after_setting_active_to_second=after_active, after_setting_render_to_second=after_render,
       default_color_name_now=me.color_attributes.default_color_name)

me.materials.clear()
me.materials.append(emit_material("attr", "attr", "second"))
via_attr = at_origin()
me.materials.clear()
me.materials.append(emit_material("missing", "color", "nosuch"))
missing = at_origin()
E.fact("the Attribute node with attribute_name set to a colour attribute's name reads it too; a misspelled name on "
       "the Color Attribute node renders black, with no error", attribute_node=via_attr, misspelled=missing)

# Writing speed: per-element loop vs foreach_set, 100k points.
big = bpy.data.meshes.new("big")
big.vertices.add(100_000)
ca = big.color_attributes.new("c", "FLOAT_COLOR", "POINT")
cols = np.random.default_rng(0).random((100_000, 4), dtype=np.float32)
t = time.time()
for i, c in enumerate(cols):
    ca.data[i].color = c
loop_s = time.time() - t
t = time.time()
ca.data.foreach_set("color", cols.ravel())
bulk_s = time.time() - t
cb = big.color_attributes.new("b", "BYTE_COLOR", "POINT")
cb.data.foreach_set("color", cols.ravel())
back = np.empty(400_000, np.float32); cb.data.foreach_get("color", back)
srgb = np.empty(400_000, np.float32); cb.data.foreach_get("color_srgb", srgb)
E.fact("100,000 point colours: a Python loop over .data[i].color against one foreach_set('color', flat array)",
       loop_s=round(loop_s, 3), foreach_set_s=round(bulk_s, 4))
E.fact("a BYTE_COLOR attribute round-trips a linear value through 8-bit sRGB: foreach_get('color') returns it to "
       "within 0.01; foreach_get('color_srgb') returns the stored sRGB value",
       max_err_color=round(float(np.abs(back - cols.ravel()).max()), 4),
       linear_0_5_reads_srgb=(lambda: (cb.data[0].__setattr__("color", (0.5, 0.5, 0.5, 1)),
                                       round(cb.data[0].color_srgb[0], 4))[1])())
os.remove(path)
E.save(value=value, hdr=hdr)
