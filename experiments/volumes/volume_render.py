"""Rendering volumes at small sizes in 4.5: a Volume object (Mesh to Volume) and a mesh cube, each with Principled
Volume, in Cycles (CPU and Metal) and EEVEE. Is the volume visible (how much light it scatters or blocks), how long a
128 px frame takes, what Cycles' step rate does to time, and what happens with no material or with Principled Volume
wired to the Surface output by mistake."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import time

import bmesh
import bpy
import numpy as np
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
S = 128


def mesh(name, build):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new(); build(bm); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob


src = mesh("Src", lambda bm: bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0))
src.hide_render = True
vol = bpy.data.volumes.new("Vol")
vo = bpy.data.objects.new("Vol", vol); scene.collection.objects.link(vo)
m2v = vo.modifiers.new("M2V", "MESH_TO_VOLUME"); m2v.object = src; m2v.voxel_amount = 64
cube = mesh("Cube", lambda bm: bmesh.ops.create_cube(bm, size=1.6))
cube.location.x = 2.2
src.location.x = -1.2


def world_centre(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    oe = ob.evaluated_get(dg)
    from mathutils import Vector
    c = sum((Vector(b) for b in oe.bound_box), Vector()) / 8
    return [round(v, 3) for v in (oe.matrix_world @ c)]


at_origin = world_centre(vo)
vo.location.x = 5.0
moved = world_centre(vo)
vo.location.x = 0.0
E.fact("the Mesh to Volume modifier puts the volume where the source mesh is in the world: moving the Volume object "
       "(to x = 5) does not move the volume", source_x=src.location.x, volume_centre_vol_at_0=at_origin,
       volume_centre_vol_at_5=moved)

backdrop = mesh("Back", lambda bm: bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=4))
backdrop.location = (0, 3, 0); backdrop.rotation_euler = (1.5708, 0, 0)
wm = bpy.data.materials.new("White"); wm.use_nodes = True
wm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1)
backdrop.data.materials.append(wm)


def volume_material(name, socket="Volume", density=5.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Density"].default_value = density
    pv.inputs["Color"].default_value = (0.9, 0.5, 0.2, 1)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(pv.outputs["Volume"], out.inputs[socket])
    return m


vmat = volume_material("Smoke")
vol.materials.append(vmat)
cube.data.materials.append(volume_material("Fog", density=2.0))

sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 4.0; sun.rotation_euler = (0.9, 0.0, 0.6)
scene.collection.objects.link(sun)
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.location = (0.5, -9, 0.5); cam.rotation_euler = (1.5708, 0, 0)
scene.collection.objects.link(cam); scene.camera = cam
scene.world = bpy.data.worlds.new("W")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.2
scene.render.resolution_x = scene.render.resolution_y = S
scene.view_settings.view_transform = "Standard"
scene.render.image_settings.file_format = "PNG"
path = E.out("v.png")


def col(x):   # world x -> image column, for this camera (sensor 36 mm, lens 50 mm, distance 9 m)
    half = 9 * 18 / 50
    return int((x - 0.5 + half) / (2 * half) * S)


def render():
    scene.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t
    img = bpy.data.images.load(path, check_existing=False)
    px = np.array(img.pixels[:], dtype=np.float32).reshape(S, S, 4)[..., :3]
    bpy.data.images.remove(img)
    row = S // 2      # image row 0 is the bottom; row S // 2 the centre line, row S - 12 near the top
    pick = lambda x, r=row: [round(float(v), 3) for v in px[r - 3: r + 3, col(x) - 3: col(x) + 3].mean(axis=(0, 1))]  # noqa
    return dict(seconds=round(dt, 3), volume_obj=pick(-1.2), cube=pick(2.2), backdrop=pick(0.5, S - 12))


res = {}
scene.render.engine = "CYCLES"
scene.cycles.samples = 32
scene.cycles.use_denoising = False
scene.cycles.device = "CPU"
res["Cycles CPU"] = render()
dev = exp.metal(scene)
res[f"Cycles {dev}"] = render()
for rate in (0.25, 4.0):
    scene.cycles.volume_step_rate = rate
    res[f"Cycles {dev} step_rate {rate}"] = render()
scene.cycles.volume_step_rate = 1.0
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.eevee.taa_render_samples = 32
res["EEVEE"] = render()
E.fact("a Volume object (Mesh to Volume, amount 64) and a mesh cube with Principled Volume (density 5 and 2, orange) "
       "render in Cycles and EEVEE: both differ from the bare backdrop; seconds per 128 px frame at 32 samples",
       **{k: v for k, v in res.items() if "step_rate" not in k})
E.fact("Cycles' volume_step_rate (default 1) at 128 px on Metal: 0.25 was the slowest, 4 about as fast as 1, and the "
       "volume's colour moved by under 0.01",
       base=res[f"Cycles {dev}"], **{k: v for k, v in res.items() if "step_rate" in k})

# No material on the Volume object; Principled Volume into Surface by mistake.
scene.render.engine = "CYCLES"
vol.materials.clear()
nomat = render()
vol.materials.append(vmat)
cube.data.materials.clear()
cube.data.materials.append(volume_material("Wrong", socket="Surface", density=2.0))
wrong = render()
scene.render.engine = "BLENDER_EEVEE_NEXT"
wrong_eevee = render()
E.fact("a Volume object with no material still renders in Cycles (a default grey volume); Principled Volume wired to "
       "the Surface output renders the cube black in Cycles instead of as a volume",
       no_material=nomat, volume_into_surface=wrong, volume_into_surface_eevee=wrong_eevee,
       for_reference=res[f"Cycles {dev}"])
os.remove(path)
E.save(results=res, device=dev, size=S, voxel_amount=64, samples=32, densities=[5.0, 2.0])
