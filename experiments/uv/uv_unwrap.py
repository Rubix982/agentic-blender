"""UV maps from Python in 4.5: which unwrap operators run headless and what they need, the angle unit of Smart UV
Project, seams and the unwrap methods, packing, and setting or reading UVs through the data API and bmesh."""
import math
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402

import exp  # noqa: E402

E = exp.Experiment(__file__)


def make(kind, name):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    if kind == "sphere":
        bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0)
    elif kind == "cylinder":
        bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.5, radius2=0.5, depth=2.0)
    else:
        bmesh.ops.create_cube(bm, size=2.0)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def activate(ob):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def uvs(ob, layer=None):
    me = ob.data
    lay = me.uv_layers[layer] if layer else me.uv_layers.active
    a = np.zeros(len(me.loops) * 2, dtype=np.float32)
    lay.uv.foreach_get("vector", a)
    return a.reshape(-1, 2)


def islands_and_area(ob):
    """UV islands (corners joined where they share a vertex and the same UV) and total UV area."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    uvl = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    parent = list(range(len(bm.faces)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for e in bm.edges:
        fs = e.link_faces
        if len(fs) != 2:
            continue
        a, b = fs
        def uv_at(f, v):
            return next(l[uvl].uv for l in f.loops if l.vert == v)
        if all((uv_at(a, v) - uv_at(b, v)).length < 1e-5 for v in e.verts):
            parent[find(a.index)] = find(b.index)
    n = len({find(i) for i in range(len(bm.faces))})
    area = 0.0
    for f in bm.faces:
        pts = [l[uvl].uv for l in f.loops]
        area += 0.5 * abs(sum(pts[i].x * pts[i - 1].y - pts[i - 1].x * pts[i].y for i in range(len(pts))))
    bm.free()
    return n, area


# 1. A new UV layer on a mesh that had none.
sph = make("sphere", "Sphere")
lay = sph.data.uv_layers.new(name="UVMap")
a = uvs(sph)
vals = sorted({(round(float(x), 4), round(float(y), 4)) for x, y in a})
quads = sum(1 for p in sph.data.polygons if p.loop_total == 4)
E.fact("A new UV layer on a mesh without UVs is not empty: each face gets the whole unit square (its corners at the "
       "square's corners; triangles use three of them)", corners=len(a), distinct_uvs=vals[:8], quads=quads,
       triangles=len(sph.data.polygons) - quads)
E.fact("A UV map is an attribute: a FLOAT2 on the CORNER domain, under the UV map's name",
       attribute=[(at.name, at.data_type, at.domain) for at in sph.data.attributes if at.name == "UVMap"])

# 2. Smart UV Project: needs edit mode and a selection; its angle is in radians.
activate(sph)
try:
    r = bpy.ops.uv.smart_project()
    obj_mode = str(r)
except RuntimeError as e:
    obj_mode = "ERROR " + str(e).splitlines()[0]
E.fact("uv.smart_project in object mode", result=obj_mode)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
def smart_islands(angle):
    bpy.ops.uv.smart_project(angle_limit=angle, island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    n, _ = islands_and_area(sph)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    return n


try:
    by_angle = {"66 (meant as degrees)": smart_islands(66), "radians(89) (the soft maximum)": smart_islands(math.radians(89)),
                "radians(90) (the hard maximum)": smart_islands(math.radians(90)),
                "radians(66)": smart_islands(math.radians(66)), "radians(30)": smart_islands(math.radians(30))}
except (TypeError, ValueError, RuntimeError) as e:
    by_angle = "ERROR " + str(e).splitlines()[0][:200]
E.fact("Smart UV Project's angle_limit is in radians (default 1.1519 = 66 degrees; soft range to 1.5533 = 89 "
       "degrees, hard limit 1.5708 = 90). Passing 66, meaning degrees, raises nothing: it is clamped to the hard limit, "
       "and the islands match 90 degrees, not 66", islands=by_angle)
t = time.time()
r = bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
dt = time.time() - t
bpy.ops.object.mode_set(mode="OBJECT")
a = uvs(sph)
n, area = islands_and_area(sph)
E.fact("uv.smart_project works headless once the object is active, in edit mode with its faces selected; on a 32 x 16 "
       "UV sphere it gives these islands, inside the unit square", result=str(r), seconds=round(dt, 3), islands=n,
       uv_min=[round(float(x), 4) for x in a.min(0)], uv_max=[round(float(x), 4) for x in a.max(0)],
       uv_area_used=round(area, 4))

# 3. Seams and the unwrap methods.
method_items = [i.identifier for i in bpy.ops.uv.unwrap.get_rna_type().properties["method"].enum_items]
cyl = make("cylinder", "Cylinder")
cyl.data.uv_layers.new(name="UVMap")
bm = bmesh.new()
bm.from_mesh(cyl.data)
for e in bm.edges:   # seams: both cap rims, and one vertical edge
    f = e.link_faces
    if len(f) == 2 and abs(f[0].normal.z) != abs(f[1].normal.z):
        e.seam = True
vert = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1.5]
vert[0].seam = True
bm.to_mesh(cyl.data)
bm.free()
seams = sum(1 for e in cyl.data.edges if e.use_seam)
res = {}
for m in method_items:
    activate(cyl)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    t = time.time()
    try:
        bpy.ops.uv.unwrap(method=m, margin=0.02)
        bpy.ops.object.mode_set(mode="OBJECT")
        n, area = islands_and_area(cyl)
        res[m] = dict(islands=n, uv_area=round(area, 4), seconds=round(time.time() - t, 3))
    except RuntimeError as e:
        bpy.ops.object.mode_set(mode="OBJECT")
        res[m] = "ERROR " + str(e).splitlines()[0][:120]
E.fact("uv.unwrap splits along seams (edge.use_seam, set here through bmesh's edge.seam): a cylinder with seams around "
       "both caps and down one side unwraps into 3 islands with each method 4.5 offers", seams=seams, methods=res)

# 4. Packing, and lightmap pack.
activate(sph)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
props = sorted(p.identifier for p in bpy.ops.uv.pack_islands.get_rna_type().properties if p.identifier != "rna_type")
r1 = bpy.ops.uv.pack_islands(margin=0.01, rotate=True)
ts = bpy.context.scene.tool_settings
sync_before = ts.use_uv_select_sync
ts.use_uv_select_sync = True
t = time.time()
r2 = bpy.ops.uv.pack_islands(margin=0.01, rotate=True)
dt = time.time() - t
bpy.ops.object.mode_set(mode="OBJECT")
n, area = islands_and_area(sph)
E.fact("uv.pack_islands acts on islands selected in the UV editor's own selection, not the mesh's: after Smart UV "
       "Project, with the faces selected, it returned CANCELLED; with tool_settings.use_uv_select_sync = True (UV "
       "selection follows the mesh) it packed", default_result=str(r1), use_uv_select_sync_default=sync_before,
       with_sync=str(r2), seconds=round(dt, 3), uv_area_used_after=round(area, 4), options=props)
cube = make("cube", "Cube")
cube.data.uv_layers.new(name="UVMap")
activate(cube)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
r = bpy.ops.uv.lightmap_pack(PREF_MARGIN_DIV=0.2)
bpy.ops.object.mode_set(mode="OBJECT")
n, area = islands_and_area(cube)
E.fact("uv.lightmap_pack gives every face of a cube its own island", result=str(r), islands=n, uv_area=round(area, 4))

# 5. Setting UVs without operators.
grid = bpy.data.meshes.new("Grid")
N = 200
xs, ys = np.meshgrid(np.linspace(0, 1, N + 1), np.linspace(0, 1, N + 1))
verts = np.c_[xs.ravel(), ys.ravel(), np.zeros(xs.size)]
quads = [(j * (N + 1) + i, j * (N + 1) + i + 1, (j + 1) * (N + 1) + i + 1, (j + 1) * (N + 1) + i)
         for j in range(N) for i in range(N)]
grid.from_pydata(verts.tolist(), [], quads)
grid.update()
lay = grid.uv_layers.new(name="UVMap")
loop_verts = np.zeros(len(grid.loops), dtype=np.int32)
grid.loops.foreach_get("vertex_index", loop_verts)
uv = verts[loop_verts, :2].astype(np.float32)
t = time.time()
lay.uv.foreach_set("vector", uv.ravel())
fast = time.time() - t
t = time.time()
for i, d in enumerate(lay.data):
    d.uv = uv[i]
slow = time.time() - t
back = np.zeros(len(grid.loops) * 2, dtype=np.float32)
lay.uv.foreach_get("vector", back)
E.fact("UVs from arrays: uv_layer.uv.foreach_set('vector', flat_array) per corner is far faster than a loop over "
       "uv_layer.data (marked deprecated in 4.5, still working); corners map to vertices through loops.vertex_index",
       corners=len(grid.loops), foreach_set_s=round(fast, 4), python_loop_s=round(slow, 3),
       round_trip_max_error=float(np.abs(back - uv.ravel()).max()))

# 6. UVs through bmesh.
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=4, y_segments=4, size=1.0)
uvl = bm.loops.layers.uv.verify()   # the active UV layer, created if missing
for f in bm.faces:
    for loop in f.loops:
        loop[uvl].uv = (loop.vert.co.x * 0.5 + 0.5, loop.vert.co.y * 0.5 + 0.5)
me = bpy.data.meshes.new("BmGrid")
bm.to_mesh(me)
bm.free()
bm2 = bmesh.new()
named = bm2.loops.layers.uv.new("UVMap").name
bm2.free()
E.fact("bmesh: bm.loops.layers.uv.verify() returns the active UV layer, creating one if there is none, and that new "
       "layer is named 'Float2', not 'UVMap'; bm.loops.layers.uv.new('UVMap') names it. loop[layer].uv sets a corner's "
       "UV", verify_created=[l.name for l in me.uv_layers], new_named=named,
       uv_range=[round(float(x), 3) for x in (lambda a: (a.min(), a.max()))(
           (lambda m: (lambda arr: (m.uv_layers[0].uv.foreach_get("vector", arr), arr)[1])(np.zeros(len(m.loops) * 2)))(me))])

E.save(unwrap_methods=method_items)
