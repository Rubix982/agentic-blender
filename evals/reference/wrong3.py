# Wrong (smooth everywhere, no angle rule): Heightfield: 100 x 100 vertices, 2 m across, z = 0.1 sin(3x) cos(3y), from arrays; smooth except edges sharper than 30 deg.
import math, os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
from _common import OUT, link
bpy.ops.wm.read_factory_settings(use_empty=True)
n = 100
xs, ys = np.meshgrid(np.linspace(-1, 1, n), np.linspace(-1, 1, n))
co = np.c_[xs.ravel(), ys.ravel(), 0.1 * np.sin(3 * xs.ravel()) * np.cos(3 * ys.ravel())].astype(np.float32)
quads = np.array([(j * n + i, j * n + i + 1, (j + 1) * n + i + 1, (j + 1) * n + i) for j in range(n - 1) for i in range(n - 1)], np.int32)
me = bpy.data.meshes.new("Height")
me.vertices.add(len(co)); me.vertices.foreach_set("co", co.ravel())
me.loops.add(quads.size); me.loops.foreach_set("vertex_index", quads.ravel())
me.polygons.add(len(quads)); me.polygons.foreach_set("loop_start", np.arange(0, quads.size, 4, dtype=np.int32))
me.update(calc_edges=True); me.validate()
me.shade_smooth()
ob = link(bpy.data.objects.new("Height", me))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
