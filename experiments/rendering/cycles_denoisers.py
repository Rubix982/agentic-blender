"""Which denoisers does Cycles 4.5 offer on this Mac, does OpenImageDenoise run on the GPU, and what does denoising
buy at low samples? Noise = RMSE against a 4096-sample un-denoised reference."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import time
import bpy
import numpy as np
from mathutils import Vector
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene


def material(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


bpy.ops.mesh.primitive_plane_add(size=12)
bpy.context.object.data.materials.append(material("floor", (0.8, 0.8, 0.8)))
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1), segments=48, ring_count=24)
bpy.ops.object.shade_smooth()
bpy.context.object.data.materials.append(material("gold", (1.0, 0.77, 0.34), rough=0.25, metal=1.0))
bpy.ops.mesh.primitive_cube_add(size=1.2, location=(1.8, 0.6, 0.6))
bpy.context.object.data.materials.append(material("red", (0.8, 0.1, 0.1)))
area = bpy.data.objects.new("Area", bpy.data.lights.new("Area", "AREA"))
area.data.energy = 500
area.data.size = 1
area.location = (-3, -2, 4)
area.rotation_euler = (Vector((0, 0, 1)) - area.location).to_track_quat("-Z", "Y").to_euler()
scene.collection.objects.link(area)
world = bpy.data.worlds.new("World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.3
scene.world = world
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.location = (5, -6, 3.5)
cam.rotation_euler = (Vector((0.5, 0, 0.8)) - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.engine = "CYCLES"
exp.metal()
scene.render.resolution_x = scene.render.resolution_y = 256
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"
scene.cycles.use_adaptive_sampling = False


def valid_items(owner, prop):
    """A dynamic enum lists only its static items through bl_rna; assigning a bad value makes the TypeError list the real ones."""
    try:
        setattr(owner, prop, "__nope__")
    except TypeError as e:
        msg = str(e)
        return msg[msg.index("("):] if "(" in msg else msg


den_static = [i.identifier for i in type(scene.cycles).bl_rna.properties["denoiser"].enum_items]
den_valid = valid_items(scene.cycles, "denoiser")
E.fact("cycles.denoiser is a dynamic enum: bl_rna enum_items lists nothing, while a bad assignment's TypeError lists the valid ones",
       static_items=den_static, type_error=den_valid)
E.fact("Cycles denoiser defaults in 4.5", denoiser=scene.cycles.denoiser, use_gpu=scene.cycles.denoising_use_gpu,
       input_passes=scene.cycles.denoising_input_passes, prefilter=scene.cycles.denoising_prefilter,
       quality=scene.cycles.denoising_quality,
       input_passes_items=[i.identifier for i in type(scene.cycles).bl_rna.properties["denoising_input_passes"].enum_items],
       prefilter_items=[i.identifier for i in type(scene.cycles).bl_rna.properties["denoising_prefilter"].enum_items],
       quality_items=[i.identifier for i in type(scene.cycles).bl_rna.properties["denoising_quality"].enum_items])
try:
    scene.cycles.denoiser = "OPTIX"
    optix = "accepted"
except TypeError as e:
    optix = str(e)
E.fact("assigning denoiser OPTIX on this Mac", result=optix)
scene.cycles.denoiser = "OPENIMAGEDENOISE"


def render(samples, denoise, gpu=True, quality="HIGH", res=256):
    scene.render.resolution_x = scene.render.resolution_y = res
    scene.cycles.samples = samples
    scene.cycles.use_denoising = denoise
    scene.cycles.denoising_use_gpu = gpu
    scene.cycles.denoising_quality = quality
    scene.render.filepath = E.out("tmp.exr")
    t = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t
    img = bpy.data.images.load(scene.render.filepath)
    px = np.array(img.pixels[:], dtype=np.float32).reshape(res, res, 4)[..., :3]
    bpy.data.images.remove(img)
    return dt, px


def err(px, ref):
    """Linear RMSE (dominated by fireflies) and display RMSE (clipped to 0..1, gamma 2.2: closer to what is seen)."""
    lin = float(np.sqrt(((px - ref) ** 2).mean()))
    d = lambda x: np.clip(x, 0, 1) ** (1 / 2.2)
    disp = float(np.sqrt(((d(px) - d(ref)) ** 2).mean()))
    return round(lin, 5), round(disp, 5)


configs = [(False, True, "HIGH"), (True, True, "HIGH"), (True, False, "HIGH"), (True, True, "FAST"), (True, True, "BALANCED")]
for den, gpu, q in configs[1:]:
    render(8, den, gpu, q)  # warm-up: kernels and each denoiser model load once
_, ref = render(4096, False)
rows = []
for s in (16, 64, 1024):
    for den, gpu, q in (configs if s < 1024 else configs[:1]):
        dt = min(render(s, den, gpu, q)[0] for _ in range(2))
        _, px = render(s, den, gpu, q)
        lin, disp = err(px, ref)
        rows.append(dict(samples=s, denoise=den, oidn_gpu=gpu if den else None, quality=q if den else None,
                         seconds=round(dt, 2), rmse_linear=lin, rmse_display=disp))
for r in rows:
    print(r)
big = {}
for gpu in (True, False):
    render(16, True, gpu, "HIGH", res=512)
    big[gpu] = round(min(render(16, True, gpu, "HIGH", res=512)[0] for _ in range(2)), 2)
big_raw = round(min(render(16, False, True, "HIGH", res=512)[0] for _ in range(2)), 2)
os.remove(E.out("tmp.exr"))
get = lambda s, den, gpu=True, q="HIGH": next(r for r in rows if r["samples"] == s and r["denoise"] == den
                                             and (not den or (r["oidn_gpu"] == gpu and r["quality"] == q)))
raw16, d16, raw1024 = get(16, False), get(16, True), get(1024, False)
beats = d16["rmse_display"] < raw1024["rmse_display"]
E.fact(f"in display terms, OIDN at 16 samples {'beats' if beats else 'does not beat'} 1024 un-denoised samples "
       f"({d16['rmse_display']} vs {raw1024['rmse_display']}), in {d16['seconds']} s vs {raw1024['seconds']} s; "
       "in linear RMSE the fireflies it smears keep it behind",
       raw16=raw16, denoised16=d16, raw1024=raw1024)
E.fact("OIDN on the GPU (denoising_use_gpu=True) vs on the CPU, and its quality settings, at 256 px",
       rows=[r for r in rows if r["denoise"]])
E.fact("at 512 px, 16 samples: seconds with OIDN on GPU, with OIDN on CPU, and without denoising",
       oidn_gpu_s=big[True], oidn_cpu_s=big[False], no_denoise_s=big_raw)
E.save(rows=rows, res512=dict(oidn_gpu=big[True], oidn_cpu=big[False], none=big_raw))
