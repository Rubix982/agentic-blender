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
call_errors = {}
for name, f in (("export_scene.obj", lambda: bpy.ops.export_scene.obj(filepath=E.out("x.obj"))),
                ("export_mesh.stl", lambda: bpy.ops.export_mesh.stl(filepath=E.out("x.stl")))):
    try:
        f()
        call_errors[name] = "ran"
    except AttributeError as e:
        call_errors[name] = str(e)
E.fact("calling a removed exporter raises AttributeError 'Calling operator ... error, could not be found'", errors=call_errors)


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
                bc = b.inputs["Base Color"] if b else None
                if bc is not None and bc.is_linked:
                    mats.append((s.material.name, "linked from " + bc.links[0].from_node.type))
                else:
                    mats.append((s.material.name, [round(v, 3) for v in bc.default_value[:3]] if bc else None))
            elif s.material:
                mats.append((s.material.name, [round(v, 3) for v in s.material.diffuse_color[:3]]))
        out[o.name] = dict(verts=len(me.vertices), faces=len(me.polygons), centre=[round(v, 3) for v in centre],
                           size=[round(v, 3) for v in o.dimensions], scale=[round(v, 3) for v in o.scale],
                           rot_deg=[round(math.degrees(v), 1) for v in o.matrix_world.to_euler()],
                           parent=o.parent.name if o.parent else None, mesh_name=me.name,
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

E.fact("OBJ (wm.obj_export defaults) writes .obj + .mtl. On import: names kept; world positions kept; each object gets "
       "rotation (90, 0, 0) with its own rotation and scale baked into the vertices (Box reads scale 1); UVs kept; base colour "
       "kept through MTL Kd; colour attributes are dropped (export_colors defaults False); and Ball, which had no material, "
       "comes back with Box's material 'Red' (the last usemtl carries over)", obj=results["obj"])
E.fact("STL import gives one object named after the file, holding both meshes as triangles with shared vertices merged "
       "(122 vertices, 236 triangles); no UVs, materials or colours", stl=results["stl"])
E.fact("PLY (defaults) also merges everything into one object named after the file; it keeps quads (134 faces), UVs (with "
       "vertices split at UV seams: 165) and the colour attribute; materials are dropped", ply=results["ply"])
E.fact("FBX (export_scene.fbx / import_scene.fbx defaults) keeps object names, rotation and scale as transforms, UVs, the "
       "material with its base colour, and the colour attribute; nothing is triangulated", fbx=results["fbx"])
E.fact("USD (.usdc defaults) keeps transforms, UVs (renamed 'st'), the material with base colour and the colour attribute, "
       "but objects come back named after their mesh data (BoxMesh, Sphere), and an extra empty object appears",
       usd=results["usdc"])
E.fact("glTF (GLB defaults) keeps names and transforms (as quaternions), triangulates and splits vertices (Box 24 vertices, "
       "12 triangles), keeps UVs; the material's base colour comes back linked from a MIX node that multiplies the factor by "
       "the imported colour attribute (now 'Color' plus 'Color.001')", gltf=results["glb"])
E.save(original=orig, results=results)
