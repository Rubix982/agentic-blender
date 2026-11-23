"""Drawing lines in 4.5: Grease Pencil (the v3 data, rewritten in 4.3) strokes from Python, its material, rendering it
headless with EEVEE and Cycles, Line Art from 3D geometry, and Freestyle lines on a render."""
import math
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy  # noqa: E402
import numpy as np  # noqa: E402

import exp  # noqa: E402

E = exp.Experiment(__file__)
sc = bpy.context.scene


def png_stats(path):
    img = bpy.data.images.load(path, check_existing=False)
    px = np.empty(img.size[0] * img.size[1] * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    px = px.reshape(-1, 4)
    lum = px[:, :3].mean(1)
    return dict(dark_fraction=round(float((lum < 0.2).mean()), 4), mean=round(float(lum.mean()), 4))


def camera_looking_down(z=6.0, ortho=4.0):
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = ortho
    cam.location = (0, 0, z)
    sc.collection.objects.link(cam)
    sc.camera = cam
    return cam


# 1. The old API is gone.
old = dict(data_grease_pencils=hasattr(bpy.data, "grease_pencils"), data_grease_pencils_v3=hasattr(bpy.data, "grease_pencils_v3"),
           type_GPencilStroke=hasattr(bpy.types, "GPencilStroke"), type_GreasePencilDrawing=hasattr(bpy.types, "GreasePencilDrawing"))
probe = bpy.data.grease_pencils_v3.new("probe")
probe_ob = bpy.data.objects.new("probe", probe)
old["object_type"] = probe_ob.type
old["object_data_type"] = type(probe_ob.data).__name__
bpy.data.objects.remove(probe_ob)
bpy.data.grease_pencils_v3.remove(probe)
E.fact("A Grease Pencil object's data in 4.5 is a GreasePencil from bpy.data.grease_pencils_v3 (layers -> frames -> "
       "drawing -> strokes), and the object's type is 'GREASEPENCIL'. The pre-4.3 types (bpy.data.grease_pencils, "
       "GPencilStroke) still exist, for annotations; code written for them does not draw Grease Pencil objects", **old)

# 2. Strokes from Python: a star and a circle.
gp = bpy.data.grease_pencils_v3.new("Lines")
ob = bpy.data.objects.new("Lines", gp)
sc.collection.objects.link(ob)
layer = gp.layers.new("Ink")
frame = layer.frames.new(1)
drawing = frame.drawing
star = [(1.5 * math.cos(math.pi / 2 + i * 4 * math.pi / 5), 1.5 * math.sin(math.pi / 2 + i * 4 * math.pi / 5), 0) for i in range(5)]
circle = [(math.cos(t) * 1.2, math.sin(t) * 1.2, 0) for t in np.linspace(0, 2 * math.pi, 64, endpoint=False)]
drawing.add_strokes([len(star), len(circle)])
pos = np.array(star + circle, dtype=np.float32)
drawing.attributes["position"].data.foreach_set("vector", pos.ravel())
names = sorted(a.name for a in drawing.attributes)
cyclic = drawing.attributes.get("cyclic") or drawing.attributes.new("cyclic", "BOOLEAN", "CURVE")
cyclic.data.foreach_set("value", [True, True])
radius = drawing.attributes.get("radius") or drawing.attributes.new("radius", "FLOAT", "POINT")
radius.data.foreach_set("value", np.full(len(pos), 0.03, dtype=np.float32))
E.fact("Strokes are added with drawing.add_strokes(point_counts) and filled through attributes: 'position' (POINT) and, "
       "added when needed, 'radius' (POINT, in metres) and 'cyclic' (CURVE). A new drawing's attributes before any are "
       "added", attributes_after_add_strokes=names, strokes=len(drawing.strokes),
       points=sum(len(s.points) for s in drawing.strokes))

# 3. A material: Grease Pencil needs its own kind.
mat = bpy.data.materials.new("Ink")
bpy.data.materials.create_gpencil_data(mat)
mat.grease_pencil.color = (0.05, 0.03, 0.02, 1)
ob.data.materials.append(mat)
E.fact("A Grease Pencil material is a normal material given Grease Pencil settings with "
       "bpy.data.materials.create_gpencil_data(mat); its stroke colour is mat.grease_pencil.color",
       is_grease_pencil=mat.is_grease_pencil, show_stroke=mat.grease_pencil.show_stroke, show_fill=mat.grease_pencil.show_fill)

# 4. Rendering it headless.
camera_looking_down()
world = bpy.data.worlds.new("W")
world.color = (1, 1, 1)
sc.world = world
sc.render.resolution_x = sc.render.resolution_y = 256
renders = {}
for engine in ("BLENDER_EEVEE_NEXT", "CYCLES", "BLENDER_WORKBENCH"):
    sc.render.engine = engine
    if engine == "CYCLES":
        sc.cycles.samples = 8
    path = E.out(f"{engine}.png")
    sc.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    renders[engine] = dict(seconds=round(time.time() - t, 2), **png_stats(path))
E.fact("A Grease Pencil drawing renders headless in EEVEE, Cycles and Workbench (Grease Pencil is drawn as its own pass "
       "on top of the render); dark_fraction is the share of the 256 px frame the ink covers", renders=renders)

# 5. Line Art: strokes generated from 3D geometry.
exp.empty()
sc = bpy.context.scene
bpy.ops.mesh.primitive_monkey_add(size=2)
monkey = bpy.context.active_object
cam = camera_looking_down(z=6, ortho=3)
cam.location = (0, -6, 0)
cam.rotation_euler = (math.pi / 2, 0, 0)
try:
    r = bpy.ops.object.grease_pencil_add(type="LINEART_SCENE")
    la = bpy.context.active_object
    mod = next(m for m in la.modifiers if m.type == "LINEART")
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = la.evaluated_get(dg)
    d = ev.data.layers[0].frames[0].drawing if len(ev.data.layers) and len(ev.data.layers[0].frames) else None
    lineart = dict(result=str(r), modifier=mod.type, source_type=mod.source_type,
                   strokes=len(d.strokes) if d else 0, points=sum(len(s.points) for s in d.strokes) if d else 0)
except Exception as e:  # noqa: BLE001
    lineart = "ERROR " + repr(e)[:300]
E.fact("object.grease_pencil_add(type='LINEART_SCENE') works headless and gives a Grease Pencil object with a Line Art "
       "modifier; the strokes it generates are read from the evaluated object", lineart=lineart)

# 6. Freestyle on a normal render.
sc.render.engine = "CYCLES"
sc.cycles.samples = 8
sc.render.resolution_x = sc.render.resolution_y = 256
for o in list(sc.objects):
    if o.type == "GREASEPENCIL":
        bpy.data.objects.remove(o)
light = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sc.collection.objects.link(light)
w = bpy.data.worlds.new("White")
w.color = (1, 1, 1)
sc.world = w
lineset = sc.view_layers[0].freestyle_settings.linesets[0]
style_before = lineset.linestyle
fs = {}
for label in ("off", "on, no line style", "on, with a line style"):
    sc.render.use_freestyle = label != "off"
    if label == "on, with a line style":
        lineset.linestyle = bpy.data.linestyles.new("Ink")
        lineset.linestyle.thickness = 2.0
    path = E.out(f"freestyle_{len(fs)}.png")
    sc.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    fs[label] = dict(seconds=round(time.time() - t, 2), **png_stats(path))
E.fact("Freestyle (render.use_freestyle) draws lines on a Cycles render headless, but in a scene made from an empty "
       "factory file the view layer's line set has no line style: the render printed a Python error "
       "('NoneType' object has no attribute 'use_chaining'), raised nothing, and came out without lines. With "
       "bpy.data.linestyles.new() assigned to the line set, lines appear (dark share of the white frame below)",
       line_style_before=None if style_before is None else style_before.name, freestyle=fs)
for f in os.listdir(E.dir):
    if f.startswith(E.name) and f.endswith(".png"):
        os.remove(os.path.join(E.dir, f))
E.save()
