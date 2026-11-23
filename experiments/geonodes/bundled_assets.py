"""The node-group assets bundled with Blender 4.5 (datafiles/assets/geometry_nodes): what is there, and how to use one headless."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import exp
E = exp.Experiment(__file__)

root = os.path.join(bpy.utils.system_resource("DATAFILES"), "assets", "geometry_nodes")
files = sorted(f for f in os.listdir(root) if f.endswith(".blend"))
E.fact("the bundled geometry-node asset files in 4.5", dir="datafiles/assets/geometry_nodes", files=files)
catalog = {}
for f in files:
    with bpy.data.libraries.load(os.path.join(root, f), link=False, assets_only=True) as (src, dst):
        catalog[f] = list(src.node_groups)
E.fact("node groups marked as assets in each file", groups={k: len(v) for k, v in catalog.items()}, names=catalog)

# append everything from the hair file, check types
with bpy.data.libraries.load(os.path.join(root, "procedural_hair_node_assets.blend"), link=False, assets_only=True) as (src, dst):
    dst.node_groups = list(src.node_groups)
kinds = {}
for g in bpy.data.node_groups:
    kinds.setdefault(g.bl_idname, 0); kinds[g.bl_idname] += 1
E.fact("appending all asset node groups from procedural_hair_node_assets.blend brings in their dependencies too",
       node_groups_in_file=len(bpy.data.node_groups), by_type=kinds,
       asset_marked=sum(1 for g in bpy.data.node_groups if g.asset_data), modifier_groups=sum(1 for g in bpy.data.node_groups if g.is_modifier),
       tool_groups=sum(1 for g in bpy.data.node_groups if getattr(g, "is_tool", False)))

# link instead of append
exp.empty()
p = os.path.join(root, "smooth_by_angle.blend")
with bpy.data.libraries.load(p, link=True) as (src, dst):
    dst.node_groups = ["Smooth by Angle"]
g = bpy.data.node_groups["Smooth by Angle"]
E.fact("linking (link=True) gives a library node group that cannot be edited but can be assigned to a modifier",
       library=bpy.path.basename(g.library.filepath) if g.library else None, is_editable=g.is_editable if hasattr(g, "is_editable") else None,
       libraries=[l.name for l in bpy.data.libraries])
bpy.ops.mesh.primitive_cylinder_add(); ob = bpy.context.object
m = ob.modifiers.new("Smooth by Angle", "NODES"); m.node_group = g
ob.data.shade_smooth()
dg = bpy.context.evaluated_depsgraph_get()
sharp = ob.evaluated_get(dg).data.attributes.get("sharp_edge")
import numpy as np
n = None
if sharp:
    v = np.empty(len(sharp.data), bool); sharp.data.foreach_get("value", v); n = int(v.sum())
E.fact("the linked Smooth by Angle evaluates (default 30 deg) on a 32-sided cylinder: 64 rim edges sharp", sharp_edges=n)
# asset-based operator, headless
r = list(bpy.ops.object.modifier_add_node_group(asset_library_type="ESSENTIALS", relative_asset_identifier="geometry_nodes/smooth_by_angle.blend/NodeTree/Smooth by Angle"))
E.fact("bpy.ops.object.modifier_add_node_group (asset operator) in -b mode", result=r, modifiers=[x.name for x in ob.modifiers])
E.save()
