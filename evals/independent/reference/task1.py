# Reference solution, task 1: terrain mesh from a height table, smooth by angle 30 deg.
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

# Blender 4.1+: auto smooth is gone; smooth faces + sharp edges from angle.
me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
me.set_sharp_from_angle(angle=math.radians(30.0))
me.update()

bpy.ops.wm.save_as_mainfile(filepath=out)
