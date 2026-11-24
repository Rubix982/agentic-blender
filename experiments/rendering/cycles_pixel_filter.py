"""Which setting sets Cycles' pixel filter: render.filter_size or cycles.filter_width?

C-009 changed render.filter_size from 1.5 to 2.5 and 3.5 px and got the same jali render to four decimals; changing
scene.cycles.filter_width softened it. This renders one hard vertical edge (an emitting plane filling the right half
of an orthographic view, black world) at 64 x 16 px, 64 samples, no denoising, and measures the edge's width as the
spread of its slope (the standard deviation, in pixels, of the step's derivative), for each setting alone."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import numpy as np
import exp
E = exp.Experiment(__file__)

scene = bpy.context.scene
for ob in list(scene.objects):
    bpy.data.objects.remove(ob)
bpy.ops.mesh.primitive_plane_add(size=2.0, location=(1.0, 0, 0))
mat = bpy.data.materials.new("emit")
mat.use_nodes = True
nt = mat.node_tree
for n in list(nt.nodes):
    if n.type != "OUTPUT_MATERIAL":
        nt.nodes.remove(n)
em = nt.nodes.new("ShaderNodeEmission")
nt.links.new(em.outputs["Emission"], next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL").inputs["Surface"])
bpy.context.object.data.materials.append(mat)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 2.0
cam.location = (0.0, 0.0, 5.0)
scene.collection.objects.link(cam)
scene.camera = cam
world = bpy.data.worlds.new("black")
world.use_nodes = True
next(n for n in world.node_tree.nodes if n.type == "BACKGROUND").inputs["Color"].default_value = (0, 0, 0, 1)
scene.world = world
r = scene.render
r.engine = "CYCLES"
r.resolution_x, r.resolution_y, r.resolution_percentage = 64, 16, 100
scene.cycles.samples = 64
scene.cycles.use_denoising = False
scene.cycles.use_adaptive_sampling = False
scene.view_settings.view_transform = "Standard"
exp.metal(scene)
out = E.out("edge.exr")
r.image_settings.file_format = "OPEN_EXR"


def edge_width():
    r.filepath = out
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(out)
    px = np.array(img.pixels[:]).reshape(16, 64, 4)[:, :, 0].mean(axis=0)
    bpy.data.images.remove(img)
    lo, hi = px.min(), px.max()
    t = (px - lo) / max(hi - lo, 1e-9)
    d = np.clip(np.diff(t), 0, None)                                   # the edge's slope, pixel to pixel
    x = np.arange(len(d))
    mu = (d * x).sum() / d.sum()
    return round(float(np.sqrt((d * (x - mu) ** 2).sum() / d.sum())), 3), [round(float(v), 3) for v in t[28:36]]


rows = {}
defaults = dict(filter_size=r.filter_size, filter_width=scene.cycles.filter_width, pixel_filter_type=scene.cycles.pixel_filter_type)
for name, rs, cw in (("both 1.5 (defaults)", 1.5, 1.5), ("render.filter_size 4.0", 4.0, 1.5),
                     ("cycles.filter_width 4.0", 1.5, 4.0)):
    r.filter_size, scene.cycles.filter_width = rs, cw
    w, prof = edge_width()
    rows[name] = dict(render_filter_size=rs, cycles_filter_width=cw, edge_spread_px=w, profile=prof)
    print("ROW", name, rows[name], flush=True)
E.fact("A new scene's pixel filter: render.filter_size, cycles.filter_width, cycles.pixel_filter_type", **defaults)
E.fact("Cycles ignores render.filter_size; cycles.filter_width sets its pixel filter",
       defaults_px=rows["both 1.5 (defaults)"]["edge_spread_px"],
       render_filter_size_4_px=rows["render.filter_size 4.0"]["edge_spread_px"],
       cycles_filter_width_4_px=rows["cycles.filter_width 4.0"]["edge_spread_px"])
E.save(rows=rows, size_px=[64, 16], samples=64)
