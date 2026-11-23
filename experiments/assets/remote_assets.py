"""C-002: ten free assets (Poly Haven, ambientCG) through scripts/assets.py and scripts/asset_import.py, headless.
Each kind has its check (CARD.md): an HDRI lights a grey sphere and turning it 180 degrees moves the lit side; a
texture's maps are connected in the right colour spaces and its tiles repeat at the stated real-world size (measured
in a render, by autocorrelation); a model's imported size is within 2 % of the stated one. Also: where an HDRI's
brightest point (its sun) lands, so a Sun light can be matched to it. Downloads are cached outside the repository;
a missing one is fetched with the system Python."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import math
import subprocess
import bpy
import numpy as np
import OpenImageIO as oiio
import exp

SCRIPTS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "skills", "blender", "scripts"))
sys.path.insert(0, SCRIPTS)
import asset_import as ai  # noqa: E402

E = exp.Experiment(__file__)
ASSETS = [("polyhaven", "kloofendal_48d_partly_cloudy_puresky"), ("polyhaven", "brown_photostudio_02"),
          ("ambientcg", "DaySkyHDRI072B"), ("polyhaven", "red_brick"), ("polyhaven", "metal_plate"),
          ("ambientcg", "Bricks060"), ("ambientcg", "WoodFloor043"), ("polyhaven", "ArmChair_01"),
          ("polyhaven", "potted_plant_04"), ("ambientcg", "3DTreeStump001")]
TILE = 128
tiles, verdicts = [], []


def get_manifest(source, aid):
    try:
        return ai.manifest(source, aid)
    except FileNotFoundError:
        subprocess.run(["python3", os.path.join(SCRIPTS, "assets.py"), "get", source, aid], check=True,
                       capture_output=True)
        return ai.manifest(source, aid)


def fresh():
    exp.empty()
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.samples = 16
    s.cycles.use_denoising = False
    s.render.image_settings.file_format = "OPEN_EXR"
    s.render.image_settings.color_depth = "32"
    s.view_settings.view_transform = "Standard"
    return s


def camera(s, loc, rot_deg, ortho=None, kind="PERSP"):
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.location = loc
    cam.rotation_euler = [math.radians(a) for a in rot_deg]
    if ortho:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = ortho
    if kind == "PANO":
        cam.data.type = "PANO"
        cam.data.panorama_type = "EQUIRECTANGULAR"
    s.collection.objects.link(cam)
    s.camera = cam
    return cam


def render(s, w, h=None):
    s.render.resolution_x, s.render.resolution_y = w, h or w
    s.render.filepath = E.out("tmp.exr")
    bpy.ops.render.render(write_still=True)
    px = oiio.ImageBuf(s.render.filepath).get_pixels(oiio.FLOAT)
    os.remove(s.render.filepath)
    return px                                   # rows top to bottom, RGBA


def tile(px):
    """A 128 px display tile (Standard view, clipped) from a float render, for the contact sheet."""
    img = np.clip(px[:, :, :3], 0, 1) ** (1 / 2.2)
    ys = np.linspace(0, img.shape[0] - 1, TILE).astype(int)
    xs = np.linspace(0, img.shape[1] - 1, TILE).astype(int)
    tiles.append(img[ys][:, xs])


def grey_sphere(s):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=48, ring_count=24)
    bpy.ops.object.shade_smooth()
    mat = bpy.data.materials.new("Grey")
    mat.use_nodes = True
    b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.5, 0.5, 0.5, 1)
    b.inputs["Roughness"].default_value = 0.6
    bpy.context.object.data.materials.append(mat)


def brightest_direction(s):
    """Elevation and bearing (+Y north, clockwise) of the brightest pixel of the world, from a 360 x 180 panorama."""
    px = render(s, 360, 180)[:, :, :3].sum(axis=2)
    r, c = np.unravel_index(np.argmax(px), px.shape)
    return round(90 - (r + 0.5), 1), round(((c + 0.5) - 180) % 360, 1)   # column = bearing + 180 (sun_elevation.py)


def image_brightest_uv(path):
    img = bpy.data.images.load(path, check_existing=True)
    w, h = img.size
    a = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(a)
    lum = a.reshape(h, w, 4)[:, :, :3].sum(axis=2)          # rows bottom to top
    r, c = np.unravel_index(np.argmax(lum), lum.shape)
    return round((c + 0.5) / w, 4), round((r + 0.5) / h, 4)


def period(profile, lo=8):
    p = profile - profile.mean()
    ac = np.correlate(p, p, "full")[len(p) - 1:]
    ac /= ac[0]
    hi = int(len(p) * 0.6)
    lag = lo + int(np.argmax(ac[lo:hi]))
    if 0 < lag < len(ac) - 1:                       # parabolic refinement of the peak
        y0, y1, y2 = ac[lag - 1], ac[lag], ac[lag + 1]
        lag = lag + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2)
    return round(float(lag), 2), round(float(ac[int(round(lag))]), 3)


for source, aid in ASSETS:
    m = get_manifest(source, aid)
    rec = dict(source=source, id=aid, kind=m["kind"], res=m["res"], credit=m["credit"])
    try:
        if m["kind"] == "hdri":
            s = fresh()
            grey_sphere(s)
            camera(s, (0, -4, 0), (90, 0, 0))
            s.render.film_transparent = True
            sides = {}
            for rot in (0, 180):
                ai.world_from_hdri(m, rotation_deg=rot)
                px = render(s, TILE)
                mask = px[:, :, 3] > 0.99
                lum = px[:, :, :3].mean(axis=2)
                half = px.shape[1] // 2
                sides[rot] = (float(lum[:, :half][mask[:, :half]].mean()), float(lum[:, half:][mask[:, half:]].mean()))
                if rot == 0:
                    s.render.film_transparent = False
                    tile(render(s, TILE))
                    s.render.film_transparent = True
            rec.update(left_right_0=[round(v, 4) for v in sides[0]], left_right_180=[round(v, 4) for v in sides[180]])
            flipped = (sides[0][0] - sides[0][1]) * (sides[180][0] - sides[180][1]) < 0
            lit = min(sides[0] + sides[180]) > 0.02
            # where its brightest point is, and how the rotation moves it
            for o in list(bpy.data.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            bpy.context.view_layer.update()
            camera(s, (0, 0, 0), (90, 0, 0), kind="PANO")
            s.render.film_transparent = False
            s.cycles.samples = 4
            dirs = {}
            for rot in (0, 90):
                ai.world_from_hdri(m, rotation_deg=rot)
                dirs[rot] = brightest_direction(s)
            rec.update(brightest_rot0=dirs[0], brightest_rot90=dirs[90], image_brightest_uv=image_brightest_uv(m["hdri"]))
            pred = {rot: [round(x, 1) for x in ai.hdri_sun(m, rot)] for rot in (0, 90)}
            rec.update(hdri_sun_rot0=pred[0], hdri_sun_rot90=pred[90],
                       hdri_sun_error_deg=max(max(abs(pred[r][0] - dirs[r][0]), abs((pred[r][1] - dirs[r][1] + 180) % 360 - 180))
                                              for r in (0, 90)))
            rec["passed"] = bool(flipped and lit)
            rec["why"] = [] if rec["passed"] else [w for w, ok in (("not lit", lit), ("lit side did not move", flipped)) if not ok]
        elif m["kind"] == "texture":
            s = fresh()
            bpy.ops.mesh.primitive_plane_add(size=4)
            plane = bpy.context.object
            mat = ai.material_from_maps(m)
            plane.data.materials.append(mat)
            ai.uvs_to_real_size(plane, m["size_m"])
            uv = plane.data.uv_layers.active.data
            umax, vmax = max(d.uv.x for d in uv), max(d.uv.y for d in uv)
            imgs = [n for n in mat.node_tree.nodes if n.type == "TEX_IMAGE"]
            unlinked = [n.label for n in imgs if not n.outputs["Color"].is_linked]
            spaces = {n.label: n.image.colorspace_settings.name for n in imgs}
            wrong_space = [r for r, cs in spaces.items() if cs != ("sRGB" if r == "color" else "Non-Color")]
            missing = [r for r in m["maps"] if r not in spaces and r not in mat["unused_maps"]]
            ai.world_from_hdri(get_manifest("polyhaven", "kloofendal_48d_partly_cloudy_puresky"))
            camera(s, (0, 0, 5), (0, 0, 0), ortho=4)
            px = render(s, 512)
            lum = px[:, :, :3].mean(axis=2)
            px_per_m = 512 / 4
            want_x, want_y = m["size_m"][0] * px_per_m, m["size_m"][1] * px_per_m
            got_x, acx = period(lum.mean(axis=0))
            got_y, acy = period(lum.mean(axis=1)[::-1])
            tile(px)
            rec.update(size_m=m["size_m"], maps=sorted(m["maps"]), colour_spaces=spaces, unused=list(mat["unused_maps"]),
                       uv_max=[round(umax, 4), round(vmax, 4)], uv_max_expected=[round(4 / m["size_m"][0], 4),
                                                                                  round(4 / m["size_m"][1], 4)],
                       tile_px_expected=[want_x, want_y], tile_px_measured=[got_x, got_y], autocorr_peak=[acx, acy])
            ok_size = abs(got_x - want_x) / want_x < 0.03 and abs(got_y - want_y) / want_y < 0.03
            rec["passed"] = bool(not unlinked and not wrong_space and not missing and ok_size)
            rec["why"] = [w for w, bad in (("unlinked maps %s" % unlinked, unlinked), ("wrong colour space %s" % wrong_space,
                                                                                       wrong_space),
                                           ("maps not used %s" % missing, missing),
                                           ("tile size off", not ok_size)) if bad]
        else:
            s = fresh()
            objs, size = ai.import_model(m)
            meshes = [o for o in objs if o.type == "MESH"]
            used = {n.image for o in meshes for sl in o.material_slots if sl.material and sl.material.use_nodes
                    for n in sl.material.node_tree.nodes if n.type == "TEX_IMAGE" and n.image}
            before = {i.name: bool(i.has_data) for i in used}          # images load lazily: False until used
            images = {}
            for i in used:
                path = bpy.path.abspath(i.filepath) if i.filepath else ""
                on_disk = bool(i.packed_file) or os.path.exists(path)
                _ = i.pixels[0] if i.size[0] else None                 # touching the pixels loads the image
                images[i.name] = bool(on_disk and i.has_data and i.size[0] > 0)
            rec["has_data_before_use"] = before
            rec["materials"] = sorted({sl.material.name for o in meshes for sl in o.material_slots if sl.material})
            rec["maps_applied_by_import_model"] = bool(m["maps"]) and m["id"] in rec["materials"]
            tris = sum(len(p.vertices) - 2 for o in meshes for p in o.data.polygons)
            rec.update(objects=len(objs), meshes=len(meshes), size_m=[round(v, 4) for v in size],
                       stated_size_m=m["size_m"], images_loaded=images, triangles=tris, stated_polycount=m["polycount"],
                       model_file=os.path.basename(m["model"]))
            if m["size_m"]:
                err = max(abs(a - b) / b for a, b in zip(sorted(size), sorted(m["size_m"])))
                rec["size_error"] = round(err, 4)
                ok_size = err < 0.02
            else:
                ok_size = True                       # no stated size: reported, not judged
            ok_img = bool(images) and all(images.values())
            rec["passed"] = bool(objs and ok_size and ok_img)
            rec["why"] = [w for w, bad in (("size off", not ok_size), ("textures missing", not ok_img)) if bad]
            # a look: on a floor, under the outdoor HDRI, framed by its size
            ai.world_from_hdri(get_manifest("polyhaven", "kloofendal_48d_partly_cloudy_puresky"))
            pts = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
            lo = [min(p[i] for p in pts) for i in range(3)]
            hi = [max(p[i] for p in pts) for i in range(3)]
            c = [(a + b) / 2 for a, b in zip(lo, hi)]
            r = max(hi[i] - lo[i] for i in range(3))
            bpy.ops.mesh.primitive_plane_add(size=r * 6, location=(c[0], c[1], lo[2]))
            camera(s, (c[0], c[1] - 2.2 * r, c[2] + 0.6 * r), (78, 0, 0))
            tile(render(s, TILE))
    except Exception as e:
        rec.update(passed=False, why=[f"{type(e).__name__}: {e}"])
    verdicts.append(rec)
    print("ASSET", rec["id"], rec["passed"], rec.get("why"), flush=True)

E.fact("assets that passed their kind's check (C-002 bar: 9 of 10)", passed=sum(r["passed"] for r in verdicts),
       of=len(verdicts), failed=[(r["id"], r["why"]) for r in verdicts if not r["passed"]])
for r in verdicts:
    E.fact(f"{r['source']} {r['id']} ({r['kind']})", **{k: v for k, v in r.items() if k not in ("source", "id", "kind")})

sheet = np.full((3 * TILE, 4 * TILE, 3), 0.5, np.float32)
for i, t in enumerate(tiles[:12]):
    y, x = divmod(i, 4)
    sheet[y * TILE:(y + 1) * TILE, x * TILE:(x + 1) * TILE] = t
out = oiio.ImageBuf(oiio.ImageSpec(4 * TILE, 3 * TILE, 3, oiio.UINT8))
out.set_pixels(oiio.ROI(0, 4 * TILE, 0, 3 * TILE), (np.clip(sheet, 0, 1) * 255).astype(np.uint8))
out.write(E.out("sheet.png"))
E.save(order=[r["id"] for r in verdicts])
