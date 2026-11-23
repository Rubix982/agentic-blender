"""Automatic checks for the ten tasks in tasks.md.

Run inside Blender 4.5:
    "$BLENDER" -b --factory-startup --python-exit-code 1 --python checks.py -- TASK PATH

Prints one line `CHECK {json}` with task, passed, reasons, numbers; exits 0 on pass, 1 on fail.
Every check reads only the output file named by PATH.
"""
import json
import math
import os
import struct
import sys
import traceback
import zlib

import bpy
from mathutils import Vector


# ----------------------------------------------------------------------------- helpers

class Result:
    def __init__(self, task):
        self.task = task
        self.reasons = []
        self.numbers = {}

    def fail(self, msg):
        self.reasons.append(msg)

    def num(self, key, value):
        if isinstance(value, float):
            value = round(value, 5)
        elif isinstance(value, (list, tuple)):
            value = [round(v, 5) if isinstance(v, float) else v for v in value]
        self.numbers[key] = value

    def expect(self, cond, msg):
        if not cond:
            self.fail(msg)
        return cond


def open_blend(path, r):
    if not os.path.isfile(path):
        r.fail("output file does not exist: %s" % path)
        return False
    with open(path, "rb") as f:
        magic = f.read(7)
    # Uncompressed .blend starts with BLENDER; compressed ones with the zstd/gzip magic.
    if not (magic.startswith(b"BLENDER") or magic[:4] == b"\x28\xb5\x2f\xfd" or magic[:2] == b"\x1f\x8b"):
        r.fail("output is not a .blend file")
        return False
    bpy.ops.wm.open_mainfile(filepath=path, load_ui=False)
    return True


def evaluated_mesh(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ob_eval = ob.evaluated_get(dg)
    me = ob_eval.to_mesh()
    return ob_eval, me


def world_verts(ob_eval, me):
    mw = ob_eval.matrix_world
    return [mw @ v.co for v in me.vertices]


def pick_mesh(name, r, predicate=None):
    """The mesh object the task names (if it names one), else the only scene mesh that fits."""
    fits = lambda o: o.type == 'MESH' and (predicate is None or predicate(o))
    ob = bpy.data.objects.get(name) if name else None
    if ob is not None and fits(ob):
        return ob
    cands = [o for o in bpy.context.scene.objects if fits(o)]
    if len(cands) == 1:
        if name:
            r.num("object_found_by", "no object named %r; the only fitting mesh is %r" % (name, cands[0].name))
        return cands[0]
    r.fail("could not identify the object: %s%d fitting mesh objects"
           % ("no fitting object named %r and " % name if name else "", len(cands)))
    return None


def read_png(path):
    """Minimal PNG decoder (non-interlaced, 8/16-bit gray/RGB/RGBA).
    Returns (width, height, channels, pixels) where pixels[y][x] is a tuple of floats 0..1,
    row 0 being the top of the image. Values are the stored (display-encoded) values."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG file")
    pos = 8
    idat = b""
    width = height = depth = ctype = interlace = None
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            width, height, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat += body
        elif kind == b"IEND":
            break
    if interlace:
        raise ValueError("interlaced PNG not supported")
    channels = {0: 1, 2: 3, 4: 2, 6: 4}.get(ctype)
    if channels is None or depth not in (8, 16):
        raise ValueError("unsupported PNG colour type %s / depth %s" % (ctype, depth))
    bpp = channels * depth // 8
    stride = width * bpp
    raw = zlib.decompress(idat)
    rows = []
    prev = bytearray(stride)
    p = 0
    for _ in range(height):
        ftype = raw[p]
        line = bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        if ftype == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 255
        elif ftype == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif ftype == 3:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif ftype == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        rows.append(line)
        prev = line
    maxv = 255.0 if depth == 8 else 65535.0
    pixels = []
    for line in rows:
        if depth == 8:
            vals = [v / maxv for v in line]
        else:
            vals = [((line[i] << 8) | line[i + 1]) / maxv for i in range(0, stride, 2)]
        pixels.append([tuple(vals[x * channels:(x + 1) * channels]) for x in range(width)])
    return width, height, channels, pixels


def rgb(px, channels):
    if channels in (1, 2):
        return (px[0], px[0], px[0])
    return px[:3]


def patch_mean(pixels, channels, cx, cy, half=2):
    acc = [0.0, 0.0, 0.0]
    n = 0
    for y in range(cy - half, cy + half + 1):
        for x in range(cx - half, cx + half + 1):
            c = rgb(pixels[y][x], channels)
            for i in range(3):
                acc[i] += c[i]
            n += 1
    return [a / n for a in acc]


# ----------------------------------------------------------------------------- task 1

CSV1 = """0.0,0.1,0.2,0.2,2.2,2.3,2.3
0.0,0.1,0.2,0.3,2.3,2.4,2.4
0.1,0.2,0.3,0.3,2.3,2.4,2.5
0.1,0.2,0.3,0.4,2.4,2.5,2.5
0.2,0.3,0.4,0.4,2.4,2.5,2.6"""


def check1(path, r):
    if not open_blend(path, r):
        return
    ob = pick_mesh("Terrain", r)
    if ob is None:
        return
    ob_eval, me = evaluated_mesh(ob)
    rows = [[float(v) for v in line.split(",")] for line in CSV1.splitlines()]
    expected = [Vector((x, y, rows[y][x])) for y in range(5) for x in range(7)]
    wv = world_verts(ob_eval, me)
    r.num("vertices", len(wv))
    r.num("faces", len(me.polygons))
    if not r.expect(len(wv) == 35, "expected 35 vertices, got %d" % len(wv)):
        return
    worst = max(min((w - e).length for w in wv) for e in expected)
    r.num("max_vertex_error_m", worst)
    r.expect(worst < 1e-3, "vertices do not match the height table (worst error %.4f m)" % worst)
    quads = sum(1 for p in me.polygons if p.loop_total == 4)
    r.expect(len(me.polygons) == 24 and quads == 24, "expected 24 quads, got %d faces (%d quads)" % (len(me.polygons), quads))

    mw3 = ob_eval.matrix_world.to_3x3()
    cn = me.corner_normals
    face_corner = {}
    for p in me.polygons:
        for li in p.loop_indices:
            face_corner[(p.index, me.loops[li].vertex_index)] = (mw3 @ Vector(cn[li].vector)).normalized()
    edge_faces = {}
    for p in me.polygons:
        for k in p.edge_keys:
            edge_faces.setdefault(k, []).append(p.index)
    n_sharp = n_smooth = bad_sharp = bad_smooth = 0
    for (a, b), fs in edge_faces.items():
        if len(fs) != 2:
            continue
        f0, f1 = fs
        dihedral = math.degrees(me.polygons[f0].normal.angle(me.polygons[f1].normal))
        split = max(math.degrees(face_corner[(f0, v)].angle(face_corner[(f1, v)])) for v in (a, b))
        joined = min(math.degrees(face_corner[(f0, v)].angle(face_corner[(f1, v)])) for v in (a, b))
        if dihedral > 33.0:
            n_sharp += 1
            if joined < 5.0:          # normals must split at both ends of a sharp edge
                bad_sharp += 1
        elif dihedral < 27.0:
            n_smooth += 1
            if split > 0.5:           # normals must be shared across a smooth edge
                bad_smooth += 1
    r.num("edges_over_30deg", n_sharp)
    r.num("edges_under_30deg", n_smooth)
    r.num("steep_edges_rendered_smooth", bad_sharp)
    r.num("gentle_edges_rendered_sharp", bad_smooth)
    r.expect(n_sharp == 8, "expected 8 edges steeper than 30 deg, found %d" % n_sharp)
    r.expect(bad_sharp == 0, "%d edges over 30 deg are shaded smooth (normals not split)" % bad_sharp)
    r.expect(bad_smooth == 0, "%d edges under 30 deg are shaded sharp/flat (normals split)" % bad_smooth)


# ----------------------------------------------------------------------------- task 2

def check2(path, r):
    if not open_blend(path, r):
        return

    def has_stack(o):
        types = [m.type for m in o.modifiers]
        return 'BEVEL' in types and 'ARRAY' in types

    ob = pick_mesh(None, r, has_stack)
    if ob is None:
        return
    types = [m.type for m in ob.modifiers]
    r.num("modifiers", types)
    if not r.expect(has_stack(ob), "object needs a live Bevel and Array modifier, has %s" % types):
        return
    r.expect(types.index('BEVEL') < len(types) - 1 - types[::-1].index('ARRAY'),
             "Bevel must come before Array in the stack")
    r.num("base_vertices", len(ob.data.vertices))
    r.expect(len(ob.data.vertices) == 8, "base mesh should be the 8-vertex box (modifiers unapplied), has %d"
             % len(ob.data.vertices))
    ob_eval, me = evaluated_mesh(ob)
    wv = world_verts(ob_eval, me)
    r.num("evaluated_vertices", len(wv))
    r.expect(len(wv) == 96, "evaluated mesh should have 96 vertices (3 copies x 32), has %d" % len(wv))
    if not wv:
        return
    xs, ys, zs = [v.x for v in wv], [v.y for v in wv], [v.z for v in wv]
    r.num("x_range", [min(xs), max(xs)])
    r.num("y_range", [min(ys), max(ys)])
    r.num("z_range", [min(zs), max(zs)])
    r.expect(abs(min(xs) + 1.0) < 0.005 and abs(max(xs) - 6.0) < 0.005,
             "X extent should be -1..6 m (three 2 m boxes, 0.5 m gaps)")
    r.expect(abs(min(ys) + 1.0) < 0.005 and abs(max(ys) - 1.0) < 0.005, "Y extent should be -1..1 m")
    off_plane = sum(1 for z in zs if min(abs(z), abs(z - 1.0)) > 1e-4)
    r.num("vertices_off_top_bottom", off_plane)
    r.expect(off_plane == 0, "%d vertices lie between z=0 and z=1: horizontal edges were bevelled" % off_plane)
    # Rounded vertical corners: 4 profile points at 0.1 m from the inset centre, no sharp corner.
    bad_corners = 0
    radii = []
    for k in range(3):
        for sx in (-1, 1):
            for sy in (-1, 1):
                corner = Vector((2.5 * k + sx, sy))
                centre = Vector((2.5 * k + 0.9 * sx, 0.9 * sy))
                pts = {(round(v.x, 4), round(v.y, 4)) for v in wv
                       if (Vector((v.x, v.y)) - corner).length < 0.15}
                d = [(Vector(p) - centre).length for p in pts]
                radii += d
                at_corner = any((Vector(p) - corner).length < 0.01 for p in pts)
                if len(pts) != 4 or at_corner or any(abs(x - 0.1) > 0.005 for x in d):
                    bad_corners += 1
    r.num("bad_vertical_corners", bad_corners)
    if radii:
        r.num("corner_radius_range", [min(radii), max(radii)])
    r.expect(bad_corners == 0, "%d of 12 vertical edges are not rounded with 3 segments of 0.1 m" % bad_corners)


# ----------------------------------------------------------------------------- task 3

def check3(path, r):
    if not open_blend(path, r):
        return

    def unit_sphere(o):
        # A radius-1 sphere at the origin (vertices on the sphere), so a leftover default cube is skipped.
        if not any(s.material for s in o.material_slots) or len(o.data.vertices) < 20:
            return False
        mw = o.matrix_world
        return all(abs((mw @ v.co).length - 1.0) < 0.02 for v in o.data.vertices)

    ob = pick_mesh(None, r, unit_sphere)
    if ob is None:
        return
    mats = [s.material for s in ob.material_slots if s.material]
    if not r.expect(mats, "the sphere has no material"):
        return
    mat = mats[0]
    r.num("material", mat.name)
    if not r.expect(mat.use_nodes and mat.node_tree, "material does not use nodes"):
        return
    outs = [n for n in mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL']
    active = [n for n in outs if n.is_active_output] or outs
    bsdf = None
    for o in active:
        s = o.inputs.get("Surface")
        if s and s.is_linked and s.links[0].from_node.type == 'BSDF_PRINCIPLED':
            bsdf = s.links[0].from_node
            break
    if not r.expect(bsdf is not None, "material output Surface is not fed by a Principled BSDF"):
        return
    want = {
        "Base Color": (0.05, 0.2, 0.6),
        "Metallic": 0.6,
        "Roughness": 0.4,
        "Coat Weight": 1.0,
        "Coat Roughness": 0.08,
        "Sheen Weight": 0.3,
        "Transmission Weight": 0.25,
        "Emission Color": (1.0, 0.5, 0.1),
        "Emission Strength": 0.5,
        "Alpha": 0.9,
    }
    got = {}
    for name, v in want.items():
        sock = bsdf.inputs.get(name)
        if sock is None:
            r.fail("Principled BSDF has no input %r" % name)
            continue
        if sock.is_linked:
            r.fail("input %r is linked; expected a plain value" % name)
            continue
        dv = sock.default_value
        if isinstance(v, tuple):
            g = tuple(dv[:3])
            got[name] = list(g)
            if any(abs(a - b) > 1e-3 for a, b in zip(g, v)):
                r.fail("%s is %s, expected %s" % (name, tuple(round(x, 4) for x in g), v))
        else:
            got[name] = dv
            if abs(dv - v) > 1e-3:
                r.fail("%s is %.4f, expected %s" % (name, dv, v))
    r.num("principled_inputs", got)
    r.num("surface_render_method", mat.surface_render_method)
    r.num("use_transparency_overlap", mat.use_transparency_overlap)
    r.expect(mat.surface_render_method == 'BLENDED', "EEVEE render method is %s, expected BLENDED"
             % mat.surface_render_method)
    r.expect(not mat.use_transparency_overlap, "Transparency Overlap / Show Backface is still on")


# ----------------------------------------------------------------------------- task 4

def check4(path, r):
    if not r.expect(os.path.isfile(path), "output file does not exist"):
        return
    w, h, ch, px = read_png(path)
    r.num("size", [w, h])
    if not r.expect((w, h) == (400, 200), "image is %dx%d, expected 400x200" % (w, h)):
        return

    def lum(cx, cy):
        c = patch_mean(px, ch, cx, cy, 4)
        return sum(c) / 3.0

    left = lum(125, 100)
    right = lum(275, 100)
    ground = [lum(200, 20), lum(30, 100), lum(370, 100), lum(200, 180)]
    r.num("left_sphere_centre", left)
    r.num("right_sphere_centre", right)
    r.num("ground_samples", ground)
    # Relative test, so the view transform (Standard or the default AgX) and a slightly grey world
    # do not decide it: the excluded sphere must be far darker than the lit one.
    r.num("right_to_left_ratio", right / left if left > 0 else None)
    r.expect(left > 0.4, "left sphere is not lit (centre %.3f)" % left)
    r.expect(min(ground) > 0.4, "ground is not lit everywhere (min %.3f)" % min(ground))
    r.expect(right < 0.35 * left, "right sphere receives the sun (centre %.3f vs left %.3f); it must be excluded"
             % (right, left))


# ----------------------------------------------------------------------------- task 5

def check5(path, r):
    if not r.expect(os.path.isfile(path), "output file does not exist"):
        return
    w, h, ch, px = read_png(path)
    r.num("size", [w, h])
    if not r.expect((w, h) == (512, 256), "image is %dx%d, expected 512x256" % (w, h)):
        return
    # Classify by which channels dominate, so the default AgX view transform (which desaturates
    # pure colours, e.g. red -> (0.86, 0.22, 0.12)) does not decide a camera task.
    names = {(1, 0, 0): "red", (0, 1, 0): "green", (0, 0, 1): "blue", (1, 1, 0): "yellow",
             (1, 0, 1): "magenta", (0, 1, 1): "cyan", (1, 1, 1): "white"}

    def classify(c):
        m = max(c)
        if m < 0.15:
            return "black"
        if m < 0.4:
            return "other"
        return names.get(tuple(int(v > 0.7 * m) for v in c), "other")

    probes = {
        "centre (+Y)": ((256, 128), "red"),
        "3/4 width (+X)": ((384, 128), "green"),
        "1/4 width (-X)": ((128, 128), "yellow"),
        "left edge (-Y)": ((2, 128), "blue"),
        "right edge (-Y)": ((509, 128), "blue"),
        "between +Y and +X": ((320, 128), "black"),
        "between -X and +Y": ((192, 128), "black"),
        "below horizon": ((256, 192), "black"),
        "above horizon": ((64, 64), "black"),
    }
    for i, x in enumerate((32, 160, 288, 416)):
        probes["top row %d (+Z)" % i] = ((x, 2), "white")
        probes["bottom row %d (-Z)" % i] = ((x + 64, 253), "magenta")
    seen = {}
    for label, ((x, y), want) in probes.items():
        got = classify(patch_mean(px, ch, x, y, 1))
        seen[label] = got
        if got != want:
            r.fail("%s at (%d,%d) is %s, expected %s" % (label, x, y, got, want))
    r.num("probes", seen)


# ----------------------------------------------------------------------------- task 6

def check6(path, r):
    if not open_blend(path, r):
        return
    sc = bpy.context.scene
    fps = sc.render.fps / sc.render.fps_base
    r.num("fps", fps)
    r.num("frame_range", [sc.frame_start, sc.frame_end])
    r.expect(abs(fps - 24.0) < 1e-6, "scene runs at %.3f fps, expected 24" % fps)
    r.expect((sc.frame_start, sc.frame_end) == (1, 96), "frame range is %d-%d, expected 1-96"
             % (sc.frame_start, sc.frame_end))
    ob = pick_mesh("Hopper", r)
    if ob is None:
        return

    def emission_strength(dg):
        vals = []
        for slot in ob.material_slots:
            if not slot.material or not slot.material.node_tree:
                continue
            m_eval = slot.material.evaluated_get(dg)
            for n in m_eval.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED':
                    vals.append(n.inputs["Emission Strength"].default_value)
                elif n.type == 'EMISSION':
                    vals.append(n.inputs["Strength"].default_value)
        return vals

    # frame: (x in m, z rotation in degrees modulo 360, emission strength)
    expect = {7: (1.0, 45.0, 1.25), 13: (2.0, 90.0, 2.5), 25: (4.0, 180.0, 5.0), 37: (2.0, 270.0, 2.5),
              55: (1.0, 45.0, 1.25), 73: (4.0, 180.0, 5.0), 91: (1.0, 315.0, 1.25)}
    measured = {}
    for f, (ex, erot, eem) in expect.items():
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        mw = ob.evaluated_get(dg).matrix_world
        x = mw.translation.x
        rot = math.degrees(math.atan2(mw[1][0], mw[0][0])) % 360.0
        drot = abs((rot - erot + 180.0) % 360.0 - 180.0)
        ems = emission_strength(dg)
        measured[f] = [round(x, 4), round(rot, 2), [round(e, 4) for e in ems]]
        if abs(x - ex) > 0.02:
            r.fail("frame %d: x = %.3f m, expected %.3f" % (f, x, ex))
        if drot > 1.0:
            r.fail("frame %d: Z rotation = %.1f deg, expected %.1f (mod 360)" % (f, rot, erot))
        if not any(abs(e - eem) < 0.02 for e in ems):
            r.fail("frame %d: emission strength %s, expected %.2f" % (f, [round(e, 3) for e in ems], eem))
    r.num("frames", measured)


# ----------------------------------------------------------------------------- task 7

def check7(path, r):
    if not open_blend(path, r):
        return
    sc = bpy.context.scene
    rbw = sc.rigidbody_world
    if not r.expect(rbw is not None, "scene has no rigid body world"):
        return
    pc = rbw.point_cache
    r.num("is_baked", pc.is_baked)
    r.num("cache_frames", [pc.frame_start, pc.frame_end])
    r.num("substeps_per_frame", rbw.substeps_per_frame)
    r.num("solver_iterations", rbw.solver_iterations)
    r.expect(rbw.enabled, "rigid body world is disabled")
    r.expect(pc.is_baked, "rigid body cache is not baked into the file")
    r.expect(pc.frame_start <= 1 and pc.frame_end >= 120, "cache does not cover frames 1-120")
    r.expect(rbw.substeps_per_frame == 10, "substeps per frame is %d, expected 10" % rbw.substeps_per_frame)
    r.expect(rbw.solver_iterations == 20, "solver iterations is %d, expected 20" % rbw.solver_iterations)
    fps = sc.render.fps / sc.render.fps_base
    r.num("fps", fps)
    r.expect(abs(fps - 24.0) < 1e-6, "scene runs at %.3f fps, expected 24" % fps)
    active = [o for o in sc.objects if o.rigid_body and o.rigid_body.type == 'ACTIVE']
    passive = [o for o in sc.objects if o.rigid_body and o.rigid_body.type == 'PASSIVE']
    r.num("active_bodies", len(active))
    r.num("passive_bodies", len(passive))
    if not r.expect(len(active) == 1, "expected exactly one active rigid body, found %d" % len(active)):
        return
    r.expect(len(passive) >= 1, "no passive rigid body (ground)")
    cube = active[0]
    r.num("mass", cube.rigid_body.mass)
    r.expect(abs(cube.rigid_body.mass - 2.0) < 1e-3, "cube mass is %.3f kg, expected 2" % cube.rigid_body.mass)
    zs = {}
    for f in (1, 25, 120):            # non-consecutive jumps: only a baked cache can answer these
        sc.frame_set(f)
        zs[f] = cube.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation.z
    r.num("z_at_frames", {k: round(v, 4) for k, v in zs.items()})
    r.expect(abs(zs[1] - 10.0) < 0.02, "frame 1: cube centre at z=%.3f, expected 10" % zs[1])
    r.expect(abs(zs[25] - 5.1) < 0.3, "frame 25 (1 s of free fall): z=%.3f, expected about 5.1" % zs[25])
    r.expect(abs(zs[120] - 0.5) < 0.05, "frame 120: z=%.3f, expected the cube resting at 0.5" % zs[120])


# ----------------------------------------------------------------------------- task 8

def check8(path, r):
    if not open_blend(path, r):
        return
    cands = [o for o in bpy.context.scene.objects
             if any(m.type == 'NODES' and m.node_group for m in o.modifiers)]
    r.num("objects_with_gn_modifier", len(cands))
    if not r.expect(len(cands) >= 1, "no object carries a Geometry Nodes modifier with a node group"):
        return
    best = None
    for ob in cands:
        for mod in ob.modifiers:
            if mod.type != 'NODES' or not mod.node_group:
                continue
            items = [it for it in mod.node_group.interface.items_tree
                     if it.item_type == 'SOCKET' and it.in_out == 'INPUT' and it.name == "Scale"]
            if items:
                best = (ob, mod, items[0])
    if not r.expect(best is not None, "no Geometry Nodes modifier has a group input named 'Scale'"):
        return
    ob, mod, item = best
    r.num("scale_socket", [item.identifier, item.socket_type])
    r.expect(item.socket_type == 'NodeSocketFloat', "'Scale' is a %s, expected a float" % item.socket_type)
    default = getattr(item, "default_value", None)
    r.num("scale_default", default)
    r.expect(default is not None and abs(default - 1.0) < 1e-6, "'Scale' default is %s, expected 1.0" % default)
    try:
        value = mod[item.identifier]
    except KeyError:
        value = None
    r.num("scale_on_modifier", value)
    r.expect(isinstance(value, (int, float)) and abs(value - 0.5) < 1e-6,
             "modifier's 'Scale' value is %s, expected 0.5" % value)
    if mod.get(item.identifier + "_use_attribute"):
        r.fail("'Scale' is driven by an attribute, not the value 0.5")
    ob_eval, me = evaluated_mesh(ob)
    wv = world_verts(ob_eval, me)
    r.num("evaluated_vertices", len(wv))
    r.expect(len(wv) == 432, "evaluated mesh has %d vertices; 36 realized 12-vertex icospheres give 432"
             % len(wv))
    if not wv:
        return
    grid = [Vector((-2.5 + i, -2.5 + j, 0.0)) for i in range(6) for j in range(6)]
    counts = [0] * 36
    radii = []
    for v in wv:
        k = min(range(36), key=lambda i: (v - grid[i]).length)
        counts[k] += 1
        radii.append((v - grid[k]).length)
    r.num("radius_range", [min(radii), max(radii)])
    r.num("vertices_per_grid_point", [min(counts), max(counts)])
    r.expect(min(counts) == 12 and max(counts) == 12, "vertices are not 12 per grid point")
    r.expect(all(abs(x - 0.1) < 0.003 for x in radii),
             "sphere radius is %.4f-%.4f m, expected 0.1 (0.2 x Scale 0.5)" % (min(radii), max(radii)))


# ----------------------------------------------------------------------------- task 9

def check9(path, r):
    if not r.expect(os.path.isfile(path), "output file does not exist"):
        return
    with open(path, "rb") as f:
        data = f.read()
    r.num("file_bytes", len(data))
    if len(data) < 84:
        r.fail("file too small to be a binary STL")
        return
    n = struct.unpack("<I", data[80:84])[0]
    r.num("triangles", n)
    if not r.expect(len(data) == 84 + 50 * n, "not a binary STL (size does not match the triangle count)"):
        return
    r.expect(n == 1152, "expected 1152 triangles (48 x 12 quads, triangulated), got %d" % n)
    tris = []
    normals_ok = 0
    for i in range(n):
        vals = struct.unpack("<12f", data[84 + 50 * i:84 + 50 * i + 48])
        nrm = Vector(vals[0:3])
        a, b, c = Vector(vals[3:6]), Vector(vals[6:9]), Vector(vals[9:12])
        tris.append((a, b, c))
        geo = (b - a).cross(c - a)
        if geo.length > 0 and nrm.length > 0 and geo.dot(nrm) > 0:
            normals_ok += 1
    pts = [p for t in tris for p in t]
    mins = [min(p[i] for p in pts) for i in range(3)]
    maxs = [max(p[i] for p in pts) for i in range(3)]
    ext = [maxs[i] - mins[i] for i in range(3)]
    ctr = [(maxs[i] + mins[i]) / 2 for i in range(3)]
    r.num("extent_mm", ext)
    r.num("centre_mm", ctr)
    r.expect(abs(ext[0] - 100) < 0.2 and abs(ext[1] - 100) < 0.2,
             "X/Y extent %.3f x %.3f, expected 100 x 100 mm" % (ext[0], ext[1]))
    r.expect(abs(ext[2] - 20) < 0.1, "Z extent %.3f, expected 20 mm (torus lying flat, Z up)" % ext[2])
    r.expect(all(abs(c) < 0.5 for c in ctr), "torus is not centred on the origin")
    key = lambda p: (round(p.x, 3), round(p.y, 3), round(p.z, 3))
    edges = {}
    for a, b, c in tris:
        ka, kb, kc = key(a), key(b), key(c)
        for e in ((ka, kb), (kb, kc), (kc, ka)):
            edges[tuple(sorted(e))] = edges.get(tuple(sorted(e)), 0) + 1
    non_manifold = sum(1 for v in edges.values() if v != 2)
    r.num("non_manifold_edges", non_manifold)
    r.expect(non_manifold == 0, "%d edges are not shared by exactly two triangles" % non_manifold)
    vol = sum(a.dot(b.cross(c)) for a, b, c in tris) / 6.0
    ideal = 2 * math.pi ** 2 * 40.0 * 10.0 ** 2
    r.num("volume_mm3", vol)
    r.num("volume_ratio_to_ideal_torus", vol / ideal)
    r.expect(0.9 < vol / ideal < 1.01, "enclosed volume %.0f mm^3 (ratio %.3f to a true torus); "
             "wrong size or inward-facing triangles" % (vol, vol / ideal))
    r.num("stored_normals_agreeing", normals_ok)
    r.expect(normals_ok >= 0.95 * n, "stored facet normals disagree with the winding on %d triangles"
             % (n - normals_ok))


# ----------------------------------------------------------------------------- task 10

def check10(path, r):
    if not r.expect(os.path.isfile(path), "output file does not exist"):
        return
    w, h, ch, px = read_png(path)
    r.num("size", [w, h])
    r.num("channels", ch)
    if not r.expect((w, h) == (400, 300), "image is %dx%d, expected 400x300" % (w, h)):
        return
    target = [0x1A / 255.0, 0x2B / 255.0, 0x3C / 255.0]
    bg_probes = [(5, 5), (394, 5), (5, 294), (394, 294), (100, 100), (200, 200), (300, 250)]
    worst = 0.0
    for x, y in bg_probes:
        c = patch_mean(px, ch, x, y, 2)      # 5 x 5 mean: Blender dithers 8-bit output by about 1/255
        worst = max(worst, max(abs(a - b) for a, b in zip(c, target)))
        if ch in (2, 4) and px[y][x][-1] < 0.999:
            r.fail("background at (%d,%d) is not opaque" % (x, y))
    r.num("background_max_error_8bit", worst * 255)
    r.expect(worst * 255 <= 2.0, "background is not #1A2B3C (max channel error %.1f/255)" % (worst * 255))
    red = []
    for y in range(h):
        row = px[y]
        for x in range(w):
            c = rgb(row[x], ch)
            if c[0] > 0.9 and c[1] < 0.1 and c[2] < 0.1:
                red.append((x, y))
    r.num("red_pixels", len(red))
    if not r.expect(red, "no pure red pixels: the square is missing or its colour is altered"):
        return
    cx = sum(p[0] for p in red) / len(red)
    cy = sum(p[1] for p in red) / len(red)
    r.num("red_centroid", [cx, cy])
    r.expect(abs(len(red) - 10000) < 600, "red area is %d px, expected about 10000 (100 x 100)" % len(red))
    r.expect(abs(cx - 299.5) < 3 and abs(cy - 99.5) < 3,
             "red square centred at (%.1f, %.1f); after the horizontal mirror it belongs at (299.5, 99.5)"
             % (cx, cy))


CHECKS = {1: check1, 2: check2, 3: check3, 4: check4, 5: check5,
          6: check6, 7: check7, 8: check8, 9: check9, 10: check10}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) < 2:
        print("usage: blender -b --factory-startup --python checks.py -- TASK PATH")
        sys.exit(2)
    task, path = int(argv[0]), os.path.abspath(argv[1])
    r = Result(task)
    try:
        CHECKS[task](path, r)
    except Exception as e:  # a crash while reading the output is a failed check, not a crashed checker
        r.fail("check raised %s: %s" % (type(e).__name__, e))
        r.num("traceback", traceback.format_exc().splitlines()[-3:])
    passed = not r.reasons
    print("CHECK " + json.dumps({"task": task, "passed": passed, "reasons": r.reasons, "numbers": r.numbers},
                                default=str))
    sys.stdout.flush()
    sys.exit(0 if passed else 1)


main()
