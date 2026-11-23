# Stone material: two hex colours mixed by noise through a ramp, roughness 0.7, bump from the same noise.
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from _common import OUT
def lin(h, i):
    c = int(h[i:i + 2], 16) / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4   # hex is sRGB; Blender stores linear
def hexcol(h):
    h = h.lstrip("#"); return (lin(h, 0), lin(h, 2), lin(h, 4), 1.0)
m = bpy.data.materials.new("Stone"); m.use_nodes = True
t = m.node_tree; bsdf = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
noise = t.nodes.new("ShaderNodeTexNoise"); ramp = t.nodes.new("ShaderNodeValToRGB"); bump = t.nodes.new("ShaderNodeBump")
ramp.color_ramp.elements[0].color = hexcol("#8a5a44"); ramp.color_ramp.elements[1].color = hexcol("#b07a5c")
t.links.new(noise.outputs["Fac"], ramp.inputs["Fac"]); t.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
t.links.new(noise.outputs["Fac"], bump.inputs["Height"]); t.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
bsdf.inputs["Roughness"].default_value = 0.7
bpy.data.objects["Cube"].data.materials.clear(); bpy.data.objects["Cube"].data.materials.append(m)   # a user, so it is saved
bpy.ops.wm.save_as_mainfile(filepath=OUT)
