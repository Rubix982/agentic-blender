"""Export the same two objects to OBJ, STL, PLY, FBX, USD and glTF with each exporter's defaults, import each file into an
empty scene, and record what came back: objects, names, vertex counts, world position, size, UVs, materials and their
base colour, colour attributes. Also: which pre-4.x operator names are gone."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import math
import bpy
from mathutils import Vector
import exp

E = exp.Experiment(__file__)
old_ops = {}
for mod, op in (("export_scene", "obj"), ("import_scene", "obj"), ("export_mesh", "stl"), ("import_mesh", "stl"),
                ("export_mesh", "ply"), ("import_mesh", "ply"), ("wm", "obj_export"), ("wm", "stl_export"),
                ("wm", "ply_export"), ("wm", "usd_export"), ("export_scene", "fbx"), ("export_scene", "gltf"),
                ("wm", "fbx_import"), ("import_scene", "fbx"), ("wm", "collada_export")):
    old_ops[f"{mod}.{op}"] = op in dir(getattr(bpy.ops, mod))
E.fact("exporter/importer operators present in 4.5: the C++ wm.obj_*, wm.stl_*, wm.ply_*, wm.usd_* and the add-on "
       "export_scene.fbx/gltf; the old Python export_scene.obj, export_mesh.stl/ply are gone (AttributeError on call); "
       "4.5 also has wm.fbx_import (new C++ FBX importer) and still wm.collada_export",
       present=old_ops)


def build():
    exp.empty()
    scene = bpy.context.scene
    bpy.ops.mesh.primitive_cube_add(size=2, location=(1, 2, 3), rotation=(0, 0, math.radians(30)))
    box = bpy.context.object
    box.name = "Box"
    box.data.name = "BoxMesh"
    box.scale = (1, 1, 0.5)
    m = bpy.data.materials.new("Red")
    m.use_nodes = True
    next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.8, 0.05, 0.05, 1)
    box.data.materials.append(m)
    col = box.data.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    for d in col.data:
        d.color = (0, 0, 1, 1)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(-2, 0, 0.5), segments=16, ring_count=8)
    bpy.context.object.name = "Ball"
    return scene


def summary():
    out = {}
    dg = bpy.context.evaluated_depsgraph_get()
    for o in sorted(bpy.data.objects, key=lambda o: o.name):
        if o.type != "MESH":
            continue
        me = o.data
        corners = [o.matrix_world @ Vector(c) for c in o.bound_box]
        centre = sum(corners, Vector()) / 8
        mats = []
        for s in o.material_slots:
            if s.material and s.material.node_tree:
                b = next((n for n in s.material.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
                mats.append((s.material.name, [round(v, 3) for v in b.inputs["Base Color"].default_value[:3]] if b else None))
            elif s.material:
                mats.append((s.material.name, [round(v, 3) for v in s.material.diffuse_color[:3]]))
        out[o.name] = dict(verts=len(me.vertices), faces=len(me.polygons), centre=[round(v, 3) for v in centre],
                           size=[round(v, 3) for v in o.dimensions], scale=[round(v, 3) for v in o.scale],
                           uv=[u.name for u in me.uv_layers], materials=mats,
                           colors=[c.name for c in me.color_attributes])
    return out


build()
orig = summary()
E.fact("the source objects", objects=orig)
d = E.out("rt")
os.makedirs(d, exist_ok=True)
fmts = {
    "obj": (lambda p: bpy.ops.wm.obj_export(filepath=p), lambda p: bpy.ops.wm.obj_import(filepath=p)),
    "stl": (lambda p: bpy.ops.wm.stl_export(filepath=p), lambda p: bpy.ops.wm.stl_import(filepath=p)),
    "ply": (lambda p: bpy.ops.wm.ply_export(filepath=p), lambda p: bpy.ops.wm.ply_import(filepath=p)),
    "fbx": (lambda p: bpy.ops.export_scene.fbx(filepath=p), lambda p: bpy.ops.import_scene.fbx(filepath=p)),
    "usdc": (lambda p: bpy.ops.wm.usd_export(filepath=p), lambda p: bpy.ops.wm.usd_import(filepath=p)),
    "glb": (lambda p: bpy.ops.export_scene.gltf(filepath=p), lambda p: bpy.ops.import_scene.gltf(filepath=p)),
}
results = {}
for ext, (ex, im) in fmts.items():
    build()
    p = os.path.join(d, f"scene.{ext}")
    try:
        ex(p)
        files = sorted(os.listdir(d))
        exp.empty()
        im(p)
        results[ext] = dict(files=files, objects=summary(), types=sorted({o.type for o in bpy.data.objects}))
    except Exception as e:
        results[ext] = dict(error=str(e)[:300])
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
    print(ext, results[ext])
os.rmdir(d)

E.fact("OBJ (wm.obj_export defaults) writes .obj + .mtl; on import: names kept (Box, Ball), world positions and sizes kept, "
       "but the object's rotation and scale are baked into the vertices (scale reads 1), UVs kept, material and its base "
       "colour kept through MTL Kd; colour attributes are not exported (export_colors False)", obj=results["obj"])
E.fact("STL keeps only triangles: one object per file by default (both merged), no UVs, no materials, no colours, and the "
       "vertex count is per-triangle-corner unless merged", stl=results["stl"])
E.fact("PLY (wm.ply_export defaults) merges everything into one object, keeps UVs and colour attributes, drops materials",
       ply=results["ply"])
E.fact("FBX (export_scene.fbx defaults) keeps names, transforms (rotation and scale stay on the object), UVs, material and "
       "base colour, colour attribute", fbx=results["fbx"])
E.fact("USD (wm.usd_export defaults, .usdc) keeps names, transforms, UVs, material with base colour (UsdPreviewSurface), "
       "colour attribute", usd=results["usdc"])
E.fact("glTF (GLB defaults) keeps names, transforms, UVs, material and base colour; the colour attribute comes back as "
       "'Color' (glTF COLOR_0)", gltf=results["glb"])
E.save(original=orig, results=results)
