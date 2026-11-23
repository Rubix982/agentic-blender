# Wrong solution, task 1: uses the pre-4.1 auto-smooth API, which no longer exists, and carries on.
import bpy, sys, math

out = sys.argv[sys.argv.index("--") + 1]

CSV = """0.0,0.1,0.2,0.2,2.2,2.3,2.3
0.0,0.1,0.2,0.3,2.3,2.4,2.4
0.1,0.2,0.3,0.3,2.3,2.4,2.5
0.1,0.2,0.3,0.4,2.4,2.5,2.5
0.2,0.3,0.4,0.4,2.4,2.5,2.6"""

rows = [[float(v) for v in line.split(",")] for line in CSV.strip().splitlines()]
ny, nx = len(rows), len(rows[0])

bpy.ops.wm.read_factory_settings(use_empty=True)

verts = [(x, y, rows[y][x]) for y in range(ny) for x in range(nx)]
faces = []
for y in range(ny - 1):
    for x in range(nx - 1):
        a = y * nx + x
        faces.append((a, a + 1, a + 1 + nx, a + nx))

me = bpy.data.meshes.new("Terrain")
me.from_pydata(verts, [], faces)
me.update()
ob = bpy.data.objects.new("Terrain", me)
bpy.context.scene.collection.objects.link(ob)

me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
try:
    me.use_auto_smooth = True                  # Blender <= 4.0 API
    me.auto_smooth_angle = math.radians(30.0)
except AttributeError:
    print("auto smooth not available; faces are smooth anyway")
me.update()

bpy.ops.wm.save_as_mainfile(filepath=out)
