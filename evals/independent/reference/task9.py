# Reference solution, task 9: a torus exported as a binary STL in millimetres.
import bpy, sys

out = sys.argv[sys.argv.index("--") + 1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_torus_add(
    major_segments=48, minor_segments=12,
    major_radius=0.04, minor_radius=0.01,
    location=(0, 0, 0),
)
ob = bpy.context.active_object
ob.select_set(True)

# Blender 4.2+: the C++ STL exporter (the old export_mesh.stl add-on is gone).
bpy.ops.wm.stl_export(
    filepath=out,
    export_selected_objects=True,
    ascii_format=False,
    global_scale=1000.0,       # metres in the scene -> millimetres in the file
    use_scene_unit=False,
    forward_axis='Y',
    up_axis='Z',
    apply_modifiers=True,
)
