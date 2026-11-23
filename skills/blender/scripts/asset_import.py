"""Inside Blender: turn what assets.py fetched into a world, a material at real-world size, or imported objects.

    import sys; sys.path.insert(0, "<this folder>")
    import asset_import as ai
    m = ai.manifest("polyhaven", "red_brick")          # the cached manifest; run `assets.py get` first
    sky = ai.manifest("polyhaven", "kloofendal_48d_partly_cloudy_puresky")
    ai.world_from_hdri(sky, rotation_deg=90)
    elevation, bearing = ai.hdri_sun(sky, rotation_deg=90)   # to put a Sun light on the HDRI's sun
    mat = ai.material_from_maps(m)                      # Principled BSDF, each map in its colour space
    ai.uvs_to_real_size(plane, m["size_m"])             # one texture tile = its real width and height
    objs, size = ai.import_model(ai.manifest("polyhaven", "ArmChair_01"))

Files are only read, never executed: a model is imported from glTF, OBJ, FBX or USD, never from a downloaded .blend
(which can carry scripts). Measured on Blender 4.5: experiments/assets/remote_assets.py in the source repository.
"""
import glob
import json
import math
import os

import bpy

CACHE = os.path.expanduser(os.environ.get("AGENTIC_BLENDER_ASSET_CACHE", "~/.cache/agentic-blender/assets"))
DATA_MAPS = ("roughness", "metallic", "normal", "displacement", "opacity", "arm", "ao")


def manifest(source, asset_id, res=None):
    """The manifest assets.py saved for this asset (the given resolution folder, or the only/first one)."""
    found = sorted(glob.glob(os.path.join(CACHE, source, asset_id, res or "*", "manifest.json")))
    if not found:
        raise FileNotFoundError(f"no cached {source}/{asset_id}: run  python3 assets.py get {source} {asset_id}")
    return json.load(open(found[0]))


def world_from_hdri(m, scene=None, strength=1.0, rotation_deg=0.0):
    """A world lit by the HDRI; rotation_deg turns it about Z (see the page for which way)."""
    scene = scene or bpy.context.scene
    w = bpy.data.worlds.new(m["id"])
    w.use_nodes = True
    nt = w.node_tree
    bg = next(n for n in nt.nodes if n.type == "BACKGROUND")
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(m["hdri"], check_existing=True)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value[2] = math.radians(rotation_deg)
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    w["source"] = m.get("credit", "")
    scene.world = w
    return w


def hdri_sun(m, rotation_deg=0.0):
    """(elevation, bearing) in degrees of the HDRI's brightest pixel (outdoors, its sun) once world_from_hdri has turned
    it by rotation_deg; bearing clockwise from +Y. Pixel (u, v) of the image sits at bearing 360 u - 90 + rotation and
    elevation 180 (v - 0.5). A Sun light goes there with rotation_euler = (radians(90 - elevation), 0,
    radians(180 - bearing)) (light-world-camera.md)."""
    import numpy as np
    img = bpy.data.images.load(m["hdri"], check_existing=True)
    w, h = img.size
    a = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(a)
    lum = a.reshape(h, w, 4)[:, :, :3].sum(axis=2)          # rows bottom to top
    r, c = np.unravel_index(np.argmax(lum), lum.shape)
    u, v = (c + 0.5) / w, (r + 0.5) / h
    return 180 * (v - 0.5), (360 * u - 90 + rotation_deg) % 360


def material_from_maps(m, name=None, displacement_m=0.01, true_displacement=False):
    """A Principled BSDF material from the manifest's maps. Colour in sRGB, every other map Non-Color; normals through a
    Normal Map node (OpenGL maps); an ARM map (AO, roughness, metal in R, G, B) stands in for missing roughness or metal
    maps. Displacement goes through a Displacement node at displacement_m metres of relief, as bump unless
    true_displacement (which needs a finely subdivided mesh). AO is left out: Cycles and EEVEE compute occlusion."""
    maps = m["maps"]
    mat = bpy.data.materials.new(name or m["id"])
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])

    def tex(role):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(maps[role], check_existing=True)
        n.image.colorspace_settings.name = "Non-Color" if role in DATA_MAPS else "sRGB"
        n.label = role
        nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
        return n

    if "color" in maps:
        nt.links.new(tex("color").outputs["Color"], bsdf.inputs["Base Color"])
    sep = None
    if "arm" in maps and ("roughness" not in maps or "metallic" not in maps):
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(tex("arm").outputs["Color"], sep.inputs["Color"])
    if "roughness" in maps:
        nt.links.new(tex("roughness").outputs["Color"], bsdf.inputs["Roughness"])
    elif sep:
        nt.links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
    if "metallic" in maps:
        nt.links.new(tex("metallic").outputs["Color"], bsdf.inputs["Metallic"])
    elif sep:
        nt.links.new(sep.outputs["Blue"], bsdf.inputs["Metallic"])
    if "normal" in maps:
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(tex("normal").outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    if "opacity" in maps:
        nt.links.new(tex("opacity").outputs["Color"], bsdf.inputs["Alpha"])
    if "displacement" in maps and displacement_m:
        d = nt.nodes.new("ShaderNodeDisplacement")
        nt.links.new(tex("displacement").outputs["Color"], d.inputs["Height"])
        d.inputs["Midlevel"].default_value = 0.5
        d.inputs["Scale"].default_value = displacement_m
        nt.links.new(d.outputs["Displacement"], out.inputs["Displacement"])
        mat.displacement_method = "BOTH" if true_displacement else "BUMP"
    mat["source"] = m.get("credit", "")
    mat["unused_maps"] = [r for r in maps if r == "ao" or (r == "arm" and sep is None)]
    return mat


def uvs_to_real_size(obj, size_m, uv_name=None):
    """Scale obj's UVs so one tile of a texture size_m = (width, height) metres covers that much of the surface, as
    measured on the object in world space. Assumes undistorted UVs (a primitive's, or a clean unwrap). Returns the
    metres per UV unit found before scaling."""
    if not size_m:
        raise ValueError("this asset has no stated size: pass one, e.g. (2, 2)")
    me = obj.data
    uv = me.uv_layers[uv_name] if uv_name else me.uv_layers.active
    if uv is None:
        raise ValueError(f"{obj.name} has no UV map; unwrap it first")
    mw = obj.matrix_world
    world_area = uv_area = 0.0
    for poly in me.polygons:
        co = [mw @ me.vertices[me.loops[i].vertex_index].co for i in poly.loop_indices]
        for k in range(1, len(co) - 1):
            world_area += (co[k] - co[0]).cross(co[k + 1] - co[0]).length / 2
        p = [uv.data[i].uv for i in poly.loop_indices]
        uv_area += abs(sum(p[i].x * p[(i + 1) % len(p)].y - p[(i + 1) % len(p)].x * p[i].y for i in range(len(p)))) / 2
    metres_per_uv = math.sqrt(world_area / uv_area)
    su, sv = metres_per_uv / size_m[0], metres_per_uv / size_m[1]
    for d in uv.data:
        d.uv = (d.uv.x * su, d.uv.y * sv)
    return metres_per_uv


def import_model(m, maps_if_untextured=True):
    """Import the manifest's model (glTF, OBJ, FBX or USD) into the current scene; return (new objects, world size
    (x, y, z) in metres of their combined bounding box). If an OBJ arrives without textures and the asset has maps,
    they are applied with material_from_maps."""
    path = m["model"]
    ext = os.path.splitext(path)[1].lower()
    before = set(bpy.data.objects)
    if ext in (".gltf", ".glb"):
        bpy.ops.import_scene.gltf(filepath=path)
    elif ext == ".obj":
        bpy.ops.wm.obj_import(filepath=path)
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=path)
    elif ext in (".usd", ".usda", ".usdc", ".usdz"):
        bpy.ops.wm.usd_import(filepath=path)
    else:
        raise ValueError(f"not importing {ext}: only glTF, OBJ, FBX and USD")
    new = [o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    meshes = [o for o in new if o.type == "MESH"]
    if maps_if_untextured and m.get("maps") and meshes:
        has_images = any(n.type == "TEX_IMAGE" and n.image for o in meshes for s in o.material_slots
                         if s.material and s.material.use_nodes for n in s.material.node_tree.nodes)
        if not has_images:
            mat = material_from_maps(m)
            for o in meshes:
                o.data.materials.clear()
                o.data.materials.append(mat)
    pts = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
    size = tuple(max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)) if pts else (0, 0, 0)
    for o in new:
        o["source"] = m.get("credit", "")
    return new, size
