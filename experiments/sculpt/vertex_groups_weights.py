"""Weights by data in 4.5: vertex groups from Python (add, weight, remove), how fast many weights can be written and
read, what a weight outside 0..1 does, whether a vertex group reaches a render through the shader's Attribute node,
whether it shows in mesh.attributes, and two operators that use weights (normalize) or are driven by them (Displace)."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import time

import bmesh
import bpy
import numpy as np
import OpenImageIO as oiio
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene


def err(fn):
    try:
        return "ok", fn()
    except Exception as e:  # noqa: BLE001
        return "error", f"{type(e).__name__}: {str(e).strip()[:200]}"


me = bpy.data.meshes.new("Grid")
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=316, y_segments=316, size=1.0)      # 317 x 317 = 100,489 points
bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("Grid", me)
scene.collection.objects.link(ob)
n = len(me.vertices)
co = np.empty(n * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
w = np.clip((co[:, 0] + 1) / 2, 0, 1)                     # 0 at x = -1 to 1 at x = +1

vg = ob.vertex_groups.new(name="ramp")
t = time.time()
vg.add(list(range(n)), 1.0, "REPLACE")
one_call = time.time() - t
t = time.time()
for i in range(n):
    vg.add([i], float(w[i]), "REPLACE")
per_vertex = time.time() - t
E.fact("vertex_groups[...].add(indices, weight, 'REPLACE') writes one weight to many points in one call; a different "
       "weight per point needs one call per point (no foreach_set for vertex groups): times for 100,489 points",
       points=n, one_call_s=round(one_call, 3), per_point_calls_s=round(per_vertex, 2))

t = time.time()
read = np.array([vg.weight(i) for i in range(n)])
read_s = time.time() - t
t = time.time()
gi = vg.index
read2 = np.zeros(n)
for v in me.vertices:
    for g in v.groups:
        if g.group == gi:
            read2[v.index] = g.weight
read2_s = time.time() - t
E.fact("reading weights back: vg.weight(i) per point, or a loop over mesh.vertices[i].groups; both match what was "
       "written", weight_calls_s=round(read_s, 2), groups_loop_s=round(read2_s, 2),
       max_err=round(float(np.abs(read - w).max()), 6), max_err_loop=round(float(np.abs(read2 - w).max()), 6))

vg2 = ob.vertex_groups.new(name="partial")
vg2.add([0, 1, 2], 0.5, "REPLACE")
vg2.add([3], 1.7, "REPLACE")
vg2.add([4], -0.3, "REPLACE")
vg2.add([1], 0.25, "ADD")
vg2.add([2], 0.25, "SUBTRACT")
E.fact("a weight outside 0..1 is clamped on add (1.7 -> 1, -0.3 -> 0, the point still a member); ADD and SUBTRACT "
       "change an existing weight; weight() of a point not in the group raises RuntimeError",
       w3=vg2.weight(3), w4=vg2.weight(4), w1_after_add=vg2.weight(1), w2_after_subtract=vg2.weight(2),
       not_member=err(lambda: vg2.weight(10)))
vg2.remove([0])
E.fact("vg.remove([i]) takes a point out of the group", after_remove=err(lambda: vg2.weight(0)))
E.fact("vertex groups are not listed in mesh.attributes in 4.5 (they live in the mesh's deform layer)",
       in_attributes="ramp" in me.attributes, attribute_names=[a.name for a in me.attributes if not a.name.startswith(".")])

# Does the shader's Attribute node read a vertex group by name?
mat = bpy.data.materials.new("W"); mat.use_nodes = True
nt = mat.node_tree; nt.nodes.clear()
em = nt.nodes.new("ShaderNodeEmission"); out = nt.nodes.new("ShaderNodeOutputMaterial")
at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "ramp"
nt.links.new(at.outputs["Fac"], em.inputs["Strength"]); nt.links.new(em.outputs[0], out.inputs["Surface"])
me.materials.append(mat)
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.data.type = "ORTHO"; cam.data.ortho_scale = 2.0; cam.location = (0, 0, 3)
scene.collection.objects.link(cam); scene.camera = cam
scene.world = bpy.data.worlds.new("W")
scene.render.resolution_x = scene.render.resolution_y = 64
scene.view_settings.view_transform = "Standard"
scene.render.image_settings.file_format = "OPEN_EXR"
path = E.out("w.exr")
rows = {}
for eng in ("CYCLES", "BLENDER_EEVEE_NEXT"):
    scene.render.engine = eng
    if eng == "CYCLES":
        scene.cycles.samples = 4; scene.cycles.use_denoising = False
    else:
        scene.eevee.taa_render_samples = 4
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    px = oiio.ImageBuf(path).get_pixels(oiio.FLOAT)
    rows[eng] = [round(float(px[32, x, 0]), 3) for x in (4, 16, 32, 48, 60)]
E.fact("the shader's Attribute node with attribute_name set to a vertex group's name renders its weight in Cycles "
       "(a 0 -> 1 ramp across x reads as one) but reads 0 everywhere in EEVEE", sample_x_px=[4, 16, 32, 48, 60],
       expected=[round((x + 0.5) / 64, 3) for x in (4, 16, 32, 48, 60)], **rows)
# The same weights copied into a FLOAT POINT attribute, read by the same node in EEVEE.
fa = me.attributes.new("ramp_f", "FLOAT", "POINT")
fa.data.foreach_set("value", w.astype(np.float32))
at.attribute_name = "ramp_f"
scene.render.filepath = path
bpy.ops.render.render(write_still=True)
px = oiio.ImageBuf(path).get_pixels(oiio.FLOAT)
E.fact("copied into a FLOAT POINT attribute, the same weights render in EEVEE through the Attribute node",
       eevee=[round(float(px[32, x, 0]), 3) for x in (4, 16, 32, 48, 60)], engine=scene.render.engine)
at.attribute_name = "ramp"
os.remove(path)

# A modifier driven by a weight: Displace along Z by the ramp.
dm = ob.modifiers.new("D", "DISPLACE")
dm.direction = "Z"; dm.strength = 1.0; dm.mid_level = 0.0; dm.vertex_group = "ramp"
dg = bpy.context.evaluated_depsgraph_get()
ev = ob.evaluated_get(dg).data
z = np.empty(len(ev.vertices) * 3, np.float32); ev.vertices.foreach_get("co", z); z = z.reshape(-1, 3)[:, 2]
E.fact("a Displace modifier with vertex_group set moves each point by its weight (no texture: displacement 1 x weight)",
       max_err=round(float(np.abs(z - w).max()), 5))
ob.modifiers.remove(dm)

# An operator that works on weights: normalize all.
vga = ob.vertex_groups.new(name="a"); vgb = ob.vertex_groups.new(name="b")
vga.add([0], 0.6, "REPLACE"); vgb.add([0], 0.6, "REPLACE")
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
r = err(lambda: bpy.ops.object.vertex_group_normalize_all(lock_active=False))
E.fact("object.vertex_group_normalize_all runs headless with the object active; a point in several groups then sums "
       "to 1", result=r, point0_sum=round(sum(g.weight for g in me.vertices[0].groups), 4))
E.save(points=n)
