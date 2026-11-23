# Wrong (single-layer EXR): Passes: a Cycles render to a multilayer OpenEXR holding depth and normal passes besides the image.
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from _common import OUT
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.samples = 8
sc.render.resolution_x = sc.render.resolution_y = 64
vl = sc.view_layers[0]; vl.use_pass_z = True; vl.use_pass_normal = True
sc.render.image_settings.file_format = "OPEN_EXR"   # wrong: single-layer EXR keeps only the image
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
