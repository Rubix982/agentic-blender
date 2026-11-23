"""The depsgraph a final render evaluates against the viewport one, measured from renders: a Subdivision modifier's
render_levels against levels (and show_render), and the hide flags (hide_render, hide_viewport, the view layer's
hide_set, a collection excluded or hidden from render) in Cycles, EEVEE and Workbench.

Subdivision: a 2 m cube with levels 1 and render_levels 3, seen from above (orthographic). The covered area of the
render (alpha summed, in m2) is compared with the area of the cube's outline evaluated at each level."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy  # noqa: E402
import numpy as np  # noqa: E402
import OpenImageIO as oiio  # noqa: E402

import exp  # noqa: E402

E = exp.Experiment(__file__)
scene = bpy.context.scene
device = exp.metal()
scene.cycles.samples = 16
scene.cycles.use_denoising = False
scene.eevee.taa_render_samples = 16
scene.render.film_transparent = True
R = 256
scene.render.resolution_x = scene.render.resolution_y = R
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"
TMP = tempfile.mkdtemp(prefix="bfg-rvv-")

bpy.ops.mesh.primitive_cube_add(size=2)
cube = bpy.context.object
mod = cube.modifiers.new("Subdivision", "SUBSURF")
mod.levels, mod.render_levels = 1, 3
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 2.4
cam.location = (0, 0, 5)
scene.collection.objects.link(cam)
scene.camera = cam
PIX_M2 = (cam.data.ortho_scale / R) ** 2


def hull_area(xy):
    pts = sorted(set(map(tuple, np.round(xy, 6))))
    def half(points):
        h = []
        for p in points:
            while len(h) >= 2 and ((h[-1][0] - h[-2][0]) * (p[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0])) <= 0:
                h.pop()
            h.append(p)
        return h
    hull = half(pts)[:-1] + half(pts[::-1])[:-1]
    x, y = np.array(hull).T
    return 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


outline = {}
for lv in (0, 1, 2, 3):
    mod.levels = lv
    dg = bpy.context.evaluated_depsgraph_get()
    me = cube.evaluated_get(dg).data
    co = np.zeros(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    outline[lv] = dict(vertices=len(me.vertices), area_m2=round(float(hull_area(co.reshape(-1, 3)[:, :2])), 4))
mod.levels = 1
dg = bpy.context.evaluated_depsgraph_get()
viewport = dict(mode=dg.mode, vertices=len(cube.evaluated_get(dg).data.vertices))


def covered(engine):
    scene.render.engine = engine
    p = os.path.join(TMP, "r.exr")
    scene.render.filepath = p
    bpy.ops.render.render(write_still=True)
    px = oiio.ImageBuf(p).get_pixels(oiio.FLOAT)
    os.remove(p)
    return px


def area(engine):
    a = covered(engine)[..., 3]
    m2 = float(a.sum() * PIX_M2)
    best = min(outline, key=lambda lv: abs(outline[lv]["area_m2"] - m2))
    return dict(area_m2=round(m2, 4), matches_level=best)


rows = {e: area(e) for e in ("CYCLES", "BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH")}
E.fact("A final render evaluates modifiers at their render settings: a Subdivision modifier with levels 1 and "
       "render_levels 3 rendered with the outline of level 3 in Cycles, EEVEE and Workbench, while the viewport "
       "depsgraph that Python gets (context.evaluated_depsgraph_get(), mode VIEWPORT) holds level 1",
       outline_by_level=outline, viewport_depsgraph=viewport, render=rows)

mod.show_render = False
off = {e: area(e) for e in ("CYCLES", "BLENDER_EEVEE_NEXT")}
mod.show_render = True
mod.show_viewport = False
dg = bpy.context.evaluated_depsgraph_get()
vp_off = len(cube.evaluated_get(dg).data.vertices)
vp_off_render = area("CYCLES")
mod.show_viewport = True
E.fact("modifier.show_render = False leaves the modifier out of renders (the plain cube's outline) while the viewport "
       "keeps it; show_viewport = False is the reverse: the viewport depsgraph lost it and the render kept level 3",
       show_render_false=off, show_viewport_false=dict(viewport_vertices=vp_off, cycles=vp_off_render))

# a render-mode depsgraph from Python: the handlers that receive one
seen = []


def handler(scn, depsgraph=None):
    if depsgraph is not None:
        ob = cube.evaluated_get(depsgraph)
        seen.append(dict(mode=depsgraph.mode, vertices=len(ob.data.vertices)))
    else:
        seen.append(dict(mode=None))


bpy.app.handlers.frame_change_post.append(handler)
scene.frame_start = scene.frame_end = 1
scene.render.engine = "CYCLES"
scene.render.filepath = os.path.join(TMP, "anim_")
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_x = scene.render.resolution_y = 16
bpy.ops.render.render(animation=True)
anim_seen = list(seen)
seen.clear()
bpy.ops.render.render(write_still=True)
still_seen = list(seen)
bpy.app.handlers.frame_change_post.remove(handler)
E.fact("A frame_change_post handler that takes a depsgraph argument was called with the render's own depsgraph (mode "
       "RENDER, the cube at render_levels) during render(animation=True) and during a still render too, then once more "
       "with the viewport depsgraph (mode VIEWPORT, levels) after each render",
       animation_render=anim_seen, still_render=still_seen)
for f in os.listdir(TMP):
    os.remove(os.path.join(TMP, f))
scene.render.resolution_x = scene.render.resolution_y = R
scene.render.image_settings.file_format = "OPEN_EXR"

# hide flags: five emissive squares in a row, the cube out of the way
cube.hide_render = True
cube.hide_set(True)
cam.data.ortho_scale = 6
labels = ["control", "hide_viewport", "hide_render", "hide_set (view layer)", "collection excluded",
          "collection hide_render", "collection hide_viewport"]
obs = {}
for i, lab in enumerate(labels):
    me = bpy.data.meshes.new(lab)
    me.from_pydata([(-0.3, -0.3, 0), (0.3, -0.3, 0), (0.3, 0.3, 0), (-0.3, 0.3, 0)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new(lab, me)
    ob.location = (-2.4 + i * 0.8, 0, 0)
    if lab.startswith("collection"):
        col = bpy.data.collections.new(lab)
        scene.collection.children.link(col)
        col.objects.link(ob)
    else:
        scene.collection.objects.link(ob)
    obs[lab] = ob
obs["hide_viewport"].hide_viewport = True
obs["hide_render"].hide_render = True
obs["hide_set (view layer)"].hide_set(True)
vl = bpy.context.view_layer
vl.layer_collection.children["collection excluded"].exclude = True
bpy.data.collections["collection hide_render"].hide_render = True
bpy.data.collections["collection hide_viewport"].hide_viewport = True
dg = bpy.context.evaluated_depsgraph_get()
in_viewport = {lab: any(o.original == ob for o in dg.objects) for lab, ob in obs.items()}
visible_get = {lab: ob.visible_get() for lab, ob in obs.items()}


def present(engine):
    a = covered(engine)[..., 3]
    out = {}
    for lab, ob in obs.items():
        col = int((ob.location.x + cam.data.ortho_scale / 2) / cam.data.ortho_scale * R)
        out[lab] = bool(a[R // 2, col] > 0.5)
    return out


rendered = {e: present(e) for e in ("CYCLES", "BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH")}
E.fact("What each hide flag does to a final render (True = the object rendered) and to the viewport depsgraph: "
       "hide_render and a collection's hide_render or exclude keep an object out of renders; hide_viewport (the "
       "monitor icon) and the view layer's hide_set (the eye) do not, they only take it out of the viewport",
       rendered=rendered, in_viewport_depsgraph=in_viewport, visible_get=visible_get)

os.rmdir(TMP)
E.save(device=device, resolution=R)
