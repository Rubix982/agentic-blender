"""Checks for the ten held-out tasks (evals/tasks.md). Runs inside Blender.

  python3 tools/run.py evals/checks.py -- TASK PATH        TASK is 1..10, PATH the file the task saved
Prints one JSON line (CHECK {...}) with pass and the reasons, and exits 0 on a pass, 1 on a failure.
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
TASK, PATH = int(args[0]), os.path.abspath(args[1])
reasons, numbers = [], {}


def need(ok, why):
    if not ok:
        reasons.append(why)
    return ok


def open_blend(path):
    if not need(os.path.exists(path), f"no file at {path}"):
        return False
    bpy.ops.wm.open_mainfile(filepath=path, load_ui=False)
    return True


def evaluated_mesh(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    return ev, ev.to_mesh()


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_linear(h):
    h = h.lstrip("#")
    return [srgb_to_linear(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)]


def task1():
    if not need(os.path.exists(PATH), f"no file at {PATH}"):
        return
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=PATH)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    numbers["mesh_objects"] = len(meshes)
    if not need(len(meshes) == 1, f"{len(meshes)} mesh objects, not 1"):
        return
    o = meshes[0]
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.transform(o.matrix_world)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)   # glTF splits vertices at seams; weld them back
    dims = sorted((max(v.co[i] for v in bm.verts) - min(v.co[i] for v in bm.verts)) for i in range(3))
    numbers["dims_sorted_m"] = [round(d, 5) for d in dims]
    need(all(abs(a - b) < 0.003 for a, b in zip(dims, [0.06, 0.3, 0.4])), f"size {dims} is not 0.06 x 0.3 x 0.4 m")
    nonmanifold = sum(1 for e in bm.edges if len(e.link_faces) != 2)
    numbers["non_manifold_edges"] = nonmanifold
    need(nonmanifold == 0, f"{nonmanifold} edges without exactly two faces: not watertight")
    vol = abs(bm.calc_volume(signed=True))
    expected = 0.3 * 0.4 * 0.06 - 30 * 0.04 * 0.04 * 0.06
    numbers["volume_m3"], numbers["expected_m3"] = round(vol, 7), round(expected, 7)
    need(abs(vol - expected) <= 0.02 * expected, f"volume {vol:.6f} m3, expected {expected:.6f} +- 2 %")
    chi = len(bm.verts) - len(bm.edges) + len(bm.faces)
    genus = (2 - chi) / 2
    numbers["genus"] = genus
    need(genus == 30, f"genus {genus}, not 30 (Euler characteristic {chi})")


def task2():
    if not open_blend(PATH):
        return
    sc = bpy.context.scene
    lights = [o for o in sc.objects if o.type == "LIGHT"]
    suns = [o for o in lights if o.data.type == "SUN"]
    numbers["lights"] = [(o.name, o.data.type) for o in lights]
    if need(len(suns) == 1 and len(lights) == 1, "not exactly one light, a sun"):
        d = suns[0].matrix_world.to_3x3() @ Vector((0, 0, -1))
        elev = math.degrees(math.asin(max(-1, min(1, -d.normalized().z))))
        numbers["sun_elevation_deg"] = round(elev, 3)
        need(abs(elev - 20) <= 0.5, f"sun elevation {elev:.2f} deg, not 20 +- 0.5")
    w = sc.world
    dark = True
    if w is not None:
        if w.use_nodes and w.node_tree:
            out = [n for n in w.node_tree.nodes if n.type == "OUTPUT_WORLD" and n.is_active_output] or \
                  [n for n in w.node_tree.nodes if n.type == "OUTPUT_WORLD"]
            surf = out[0].inputs["Surface"] if out else None
            if surf is not None and surf.is_linked:
                src = surf.links[0].from_node
                if src.type == "BACKGROUND":
                    strength = src.inputs["Strength"].default_value if not src.inputs["Strength"].is_linked else 1
                    col = src.inputs["Color"].default_value if not src.inputs["Color"].is_linked else (1, 1, 1, 1)
                    dark = strength == 0 or max(col[:3]) == 0
                else:
                    dark = False
        else:
            dark = max(w.color[:3]) == 0
    numbers["world_dark"] = dark
    need(dark, "the world still gives light")
    need(sc.render.engine == "CYCLES", f"engine {sc.render.engine}, not CYCLES")
    need(sc.cycles.samples == 32, f"{sc.cycles.samples} samples, not 32")
    res = (sc.render.resolution_x * sc.render.resolution_percentage // 100,
           sc.render.resolution_y * sc.render.resolution_percentage // 100)
    numbers["resolution"] = res
    need(res == (256, 256), f"render size {res}, not 256 x 256")
    png = os.path.splitext(PATH)[0] + ".png"
    if need(os.path.exists(png), f"no render at {png}"):
        img = bpy.data.images.load(png)
        numbers["png_size"] = list(img.size)
        need(tuple(img.size) == (256, 256), f"PNG is {tuple(img.size)}, not 256 x 256")
        px = list(img.pixels)
        lum = [0.2126 * px[i] + 0.7152 * px[i + 1] + 0.0722 * px[i + 2] for i in range(0, len(px), 4)]
        mean = sum(lum) / len(lum)
        sd = (sum((x - mean) ** 2 for x in lum) / len(lum)) ** 0.5
        numbers["png_mean"], numbers["png_sd"] = round(mean, 4), round(sd, 4)
        need(max(lum) > 0.2 and sd > 0.03, "the render is dark or uniform")


def task3():
    if not open_blend(PATH):
        return
    cands = [o for o in bpy.data.objects if o.type == "MESH" and len(o.data.vertices) == 10000]
    if not need(cands, "no mesh object with 10,000 vertices"):
        numbers["meshes"] = [(o.name, len(o.data.vertices)) for o in bpy.data.objects if o.type == "MESH"]
        return
    o = cands[0]
    me = o.data
    numbers["faces"] = len(me.polygons)
    need(len(me.polygons) == 9801, f"{len(me.polygons)} faces, not 9,801")
    xs = [o.matrix_world @ v.co for v in me.vertices]
    span = (max(p.x for p in xs) - min(p.x for p in xs), max(p.y for p in xs) - min(p.y for p in xs))
    numbers["span"] = [round(s, 4) for s in span]
    need(all(abs(s - 2) < 0.01 for s in span), f"grid spans {span}, not 2 m")
    cx, cy = (max(p.x for p in xs) + min(p.x for p in xs)) / 2, (max(p.y for p in xs) + min(p.y for p in xs)) / 2
    err = max(abs(p.z - 0.1 * math.sin(3 * (p.x - cx)) * math.cos(3 * (p.y - cy))) for p in xs)
    err0 = max(abs(p.z - 0.1 * math.sin(3 * p.x) * math.cos(3 * p.y)) for p in xs)
    numbers["height_error"] = round(min(err, err0), 6)
    need(min(err, err0) < 1e-3, f"heights differ from 0.1 sin(3x) cos(3y) by up to {min(err, err0):.4f}")
    smooth = sum(1 for p in me.polygons if p.use_smooth)
    numbers["smooth_faces"] = smooth
    need(smooth == len(me.polygons), f"{len(me.polygons) - smooth} faces not smooth")
    rule = None
    for m in o.modifiers:
        if m.type == "NODES" and m.node_group and "smooth by angle" in m.node_group.name.lower():
            for item in m.node_group.interface.items_tree:
                if getattr(item, "in_out", "") == "INPUT" and item.name == "Angle":
                    rule = ("modifier", round(math.degrees(m[item.identifier]), 3))
    if rule is None and "sharp_edge" in me.attributes:
        rule = ("sharp_edge attribute", None)
    numbers["angle_rule"] = rule
    if need(rule is not None, "no 30-degree rule: no Smooth by Angle modifier and no sharp-edge data"):
        if rule[1] is not None:
            need(abs(rule[1] - 30) < 0.1, f"Smooth by Angle at {rule[1]} deg, not 30")


def task4():
    if not open_blend(PATH):
        return
    mats = [m for m in bpy.data.materials if m.use_nodes and m.node_tree]
    if not need(mats, "no material with nodes"):
        return
    best = None
    for m in mats:
        t = m.node_tree
        bsdf = [n for n in t.nodes if n.type == "BSDF_PRINCIPLED"]
        if bsdf:
            best = (m, t, bsdf[0])
            break
    if not need(best, "no Principled BSDF"):
        return
    m, t, bsdf = best

    def upstream(sock, kind):
        if not sock.is_linked:
            return None
        n = sock.links[0].from_node
        while n.type == "REROUTE":
            n = n.inputs[0].links[0].from_node if n.inputs[0].is_linked else None
            if n is None:
                return None
        return n if n.type == kind else None

    ramp = upstream(bsdf.inputs["Base Color"], "VALTORGB")
    if need(ramp is not None, "Base Color is not fed by a Color Ramp"):
        noise = upstream(ramp.inputs["Fac"], "TEX_NOISE")
        need(noise is not None, "the Color Ramp is not fed by a Noise Texture")
        els = ramp.color_ramp.elements
        cols = [list(e.color[:3]) for e in els]
        numbers["ramp_colours"] = [[round(c, 4) for c in col] for col in cols]
        want = [hex_linear("#8a5a44"), hex_linear("#b07a5c")]
        raw = [[int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)] for h in ("8a5a44", "b07a5c")]

        def has(target):
            return all(any(max(abs(a - b) for a, b in zip(c, w)) < 0.01 for c in cols) for w in target)
        numbers["colours_linear"], numbers["colours_raw_srgb"] = has(want), has(raw)
        need(has(want), "the ramp's colours are not the two hex colours (hex is sRGB; Blender stores linear)")
    bump = upstream(bsdf.inputs["Normal"], "BUMP")
    if need(bump is not None, "Normal is not fed by a Bump node"):
        bn = upstream(bump.inputs["Height"], "TEX_NOISE")
        need(bn is not None, "the Bump's Height is not fed by a Noise Texture")
        if ramp is not None and bn is not None:
            n1 = upstream(ramp.inputs["Fac"], "TEX_NOISE")
            need(n1 is None or n1 == bn, "the bump and the colour come from different noise textures")
    r = bsdf.inputs["Roughness"]
    numbers["roughness"] = None if r.is_linked else round(r.default_value, 4)
    need(not r.is_linked and abs(r.default_value - 0.7) < 1e-4, "roughness is not 0.7")
    outs = [n for n in t.nodes if n.type == "OUTPUT_MATERIAL"]
    need(any(o.inputs["Surface"].is_linked and o.inputs["Surface"].links[0].from_node == bsdf for o in outs),
         "the Principled BSDF does not reach the Material Output")


def task5():
    if not open_blend(PATH):
        return
    dg = bpy.context.evaluated_depsgraph_get()
    host = [o for o in bpy.data.objects if any(m.type == "NODES" for m in o.modifiers)]
    if not need(host, "no object with a geometry-nodes modifier"):
        return
    o = host[0]
    cubes = 0
    sizes = []
    for inst in dg.object_instances:
        if inst.is_instance and inst.parent and inst.parent.original == o:
            ob = inst.object
            if ob.type == "MESH":
                me = ob.to_mesh() if hasattr(ob, "to_mesh") else ob.data
                mw = inst.matrix_world
                pts = [mw @ v.co for v in me.vertices]
                if len(pts) == 8:
                    size = max(p.x for p in pts) - min(p.x for p in pts)
                    sizes.append(size)
                    cubes += 1
    ev, me = evaluated_mesh(o)
    bm = bmesh.new()
    bm.from_mesh(me)
    seen = set()
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, comp = [v], []
        seen.add(v.index)
        while stack:
            x = stack.pop()
            comp.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen:
                    seen.add(y.index)
                    stack.append(y)
        if len(comp) == 8:
            pts = [ev.matrix_world @ c.co for c in comp]
            sizes.append(max(p.x for p in pts) - min(p.x for p in pts))
            cubes += 1
    numbers["cubes"] = cubes
    numbers["cube_size_range"] = [round(min(sizes), 4), round(max(sizes), 4)] if sizes else None
    need(cubes == 200, f"{cubes} cubes, not 200")
    need(sizes and all(abs(s - 0.05) < 0.002 for s in sizes), "cubes are not 5 cm across")


def corners(points):
    xs = sorted(points, key=lambda p: (p.x + p.y))
    ys = sorted(points, key=lambda p: (p.x - p.y))
    return [xs[0], xs[-1], ys[0], ys[-1]]


def task6():
    if not open_blend(PATH):
        return
    sc = bpy.context.scene
    cl = [(o, m) for o in bpy.data.objects for m in o.modifiers if m.type == "CLOTH"]
    if not need(cl, "no object with a cloth modifier"):
        return
    o, m = cl[0]
    numbers["baked"] = m.point_cache.is_baked
    need(m.point_cache.is_baked, "the cloth cache is not baked")
    n = len(o.data.vertices)
    numbers["vertices"] = n
    need(n in (400, 441), f"{n} vertices: not a 20 x 20 grid")
    sc.frame_set(sc.frame_start)
    ev, me = evaluated_mesh(o)
    p0 = [ev.matrix_world @ v.co for v in me.vertices]
    rest = [o.matrix_world @ v.co for v in o.data.vertices]
    idx = []
    for c in corners(rest):
        idx.append(min(range(n), key=lambda i: (rest[i] - c).length))
    sc.frame_set(60)
    ev, me = evaluated_mesh(o)
    p60 = [ev.matrix_world @ v.co for v in me.vertices]
    moves = [((p60[i] - p0[i]).length, p0[i].z - p60[i].z) for i in idx]
    numbers["corner_moves_m"] = [[round(a, 4), round(b, 4)] for a, b in moves]
    still = [mv for mv in moves if mv[0] <= 0.001]
    fell = [mv for mv in moves if mv[1] >= 0.30]
    need(len(still) == 2, f"{len(still)} corners stayed within 1 mm, not 2")
    need(len(fell) == 2, f"{len(fell)} corners fell 30 cm or more, not 2")


def task7():
    if not open_blend(PATH):
        return
    sc = bpy.context.scene
    rbw = sc.rigidbody_world
    if not need(rbw is not None, "no rigid body world"):
        return
    numbers["baked"] = rbw.point_cache.is_baked
    need(rbw.point_cache.is_baked, "the rigid body cache is not baked")
    active = [o for o in sc.objects if o.rigid_body and o.rigid_body.type == "ACTIVE"]
    passive = [o for o in sc.objects if o.rigid_body and o.rigid_body.type == "PASSIVE"]
    numbers["active"], numbers["passive"] = len(active), len(passive)
    need(len(active) == 10, f"{len(active)} active bodies, not 10")
    if not need(passive, "no passive ground"):
        return
    sc.frame_set(120)
    dg = bpy.context.evaluated_depsgraph_get()
    g = passive[0].evaluated_get(dg)
    top = max((g.matrix_world @ Vector(c)).z for c in g.bound_box)
    hs = []
    for o in active:
        e = o.evaluated_get(dg)
        hs.append(round(e.matrix_world.translation.z - top, 4))
    numbers["centre_heights_m"] = hs
    need(all(abs(h - 0.10) <= 0.01 for h in hs), "not every cube's centre is 10 +- 1 cm above the ground")
    dims = [tuple(round(d, 3) for d in o.dimensions) for o in active]
    need(all(all(abs(d - 0.2) < 0.005 for d in ds) for ds in dims), f"cubes are not 20 cm: {set(dims)}")


def task8():
    if not open_blend(PATH):
        return
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    cam = sc.camera
    if not need(cam is not None, "no scene camera"):
        return
    cube = bpy.data.objects.get("Cube")
    if not need(cube is not None, "no object named Cube"):
        return
    numbers["cube_scale"] = [round(s, 4) for s in cube.scale]
    need(all(abs(a - b) < 1e-4 for a, b in zip(cube.scale, (1, 0.5, 2))), "the cube is not scaled (1, 0.5, 2)")
    numbers["lens"], numbers["sensor_width"] = cam.data.lens, cam.data.sensor_width
    need(abs(cam.data.lens - 50) < 1e-3 and abs(cam.data.sensor_width - 36) < 1e-3, "lens or sensor is not 50 mm / 36 mm")
    need(cam.matrix_world.translation.y > 0, "the camera is not on the +Y side")
    res = (sc.render.resolution_x * sc.render.resolution_percentage // 100,
           sc.render.resolution_y * sc.render.resolution_percentage // 100)
    numbers["resolution"] = res
    need(res == (1080, 1080), f"frame {res}, not 1080 x 1080")
    pts = [world_to_camera_view(sc, cam, cube.matrix_world @ Vector(c)) for c in cube.bound_box]
    h = max(p.y for p in pts) - min(p.y for p in pts)
    numbers["height_fraction"] = round(h, 4)
    need(abs(h - 0.80) <= 0.03, f"the cube fills {h:.3f} of the frame's height, not 0.80 +- 0.03")
    need(all(0 <= p.x <= 1 and 0 <= p.y <= 1 and p.z > 0 for p in pts), "part of the cube is outside the frame")


def task9():
    if not need(os.path.exists(PATH), f"no file at {PATH}"):
        return
    import OpenImageIO as oiio
    inp = oiio.ImageInput.open(PATH)
    if not need(inp is not None, "not readable as an image"):
        return
    names = []
    sub = 0
    while inp.seek_subimage(sub, 0):
        names += list(inp.spec().channelnames)
        sub += 1
    inp.close()
    numbers["channels"] = names
    low = [n.lower() for n in names]
    need(any(n.endswith("depth.z") or n.endswith(".z") and "depth" in n for n in low) or "z" in low,
         "no depth pass channel")
    need(all(any(n.endswith(f"normal.{a}") for n in low) for a in "xyz"), "no normal pass with X, Y and Z")
    need(any(n.endswith("combined.r") or n in ("r",) for n in low), "no image (combined) channels")


def task10():
    if not open_blend(PATH):
        return
    arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    if not need(arms, "no armature"):
        return
    arm = arms[0]
    numbers["bones"] = len(arm.data.bones)
    need(len(arm.data.bones) >= 3, f"{len(arm.data.bones)} bones, not 3")
    skinned = [o for o in bpy.data.objects if o.type == "MESH" and any(m.type == "ARMATURE" and m.object == arm for m in o.modifiers)]
    if not need(skinned, "no mesh with an Armature modifier on the armature"):
        return
    o = skinned[0]
    zero = sum(1 for v in o.data.vertices if sum(g.weight for g in v.groups if o.vertex_groups[g.group].name in arm.data.bones) <= 0)
    numbers["unweighted_vertices"] = zero
    need(zero == 0, f"{zero} vertices with zero total weight")
    rest = [o.matrix_world @ v.co for v in o.data.vertices]
    ztop = max(p.z for p in rest)
    zbot = min(p.z for p in rest)
    numbers["height_m"] = round(ztop - zbot, 4)
    top = [i for i, p in enumerate(rest) if p.z >= ztop - 0.01 * (ztop - zbot)]
    ev, me = evaluated_mesh(o)
    posed = [ev.matrix_world @ v.co for v in me.vertices]
    side = sum(((posed[i].x - rest[i].x) ** 2 + (posed[i].y - rest[i].y) ** 2) ** 0.5 for i in top) / len(top)
    numbers["top_sideways_m"] = round(side, 4)
    need(side >= 0.30, f"the top moved {side:.3f} m sideways, not 0.30 or more")


try:
    globals()[f"task{TASK}"]()
except Exception as e:  # noqa: BLE001
    reasons.append(f"check crashed: {type(e).__name__}: {e}")
ok = not reasons
print("CHECK " + json.dumps(dict(task=TASK, path=PATH, passed=ok, reasons=reasons, numbers=numbers), default=str), flush=True)
sys.exit(0 if ok else 1)
