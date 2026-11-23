"""Render time per frame of a short animation at small sizes: Workbench, EEVEE (16 and 64 samples), Cycles on the CPU
and on Metal (16 and 64 samples, no denoising). Per-frame times come from the render_pre / render_post handlers inside
one render(animation=True), so the first frame (EEVEE's shader compile, Cycles' scene upload) shows apart from the rest.
A sphere on a plane under an area light, the sphere moving; 256 x 256, 5 frames each."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import shutil
import statistics
import time

import bmesh
import bpy
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
d = E.out("frames")
shutil.rmtree(d, ignore_errors=True)
os.makedirs(d)


def mesh(name, build):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new(); build(bm); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob


sphere = mesh("Sphere", lambda bm: bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=0.5))
for p in sphere.data.polygons:
    p.use_smooth = True
plane = mesh("Plane", lambda bm: bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=3))
mat = bpy.data.materials.new("Red"); mat.use_nodes = True
mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.8, 0.1, 0.1, 1)
sphere.data.materials.append(mat)
sphere.location = (-1, 0, 0.5); sphere.keyframe_insert("location", frame=1)
sphere.location = (1, 0, 0.5); sphere.keyframe_insert("location", frame=5)
light = bpy.data.objects.new("Area", bpy.data.lights.new("Area", "AREA"))
light.data.energy = 300; light.data.size = 1.0; light.location = (1, -1, 3)
scene.collection.objects.link(light)
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.location = (0, -5, 2.5); cam.rotation_euler = (1.15, 0, 0)
scene.collection.objects.link(cam); scene.camera = cam
scene.world = bpy.data.worlds.new("W")
scene.render.resolution_x = scene.render.resolution_y = 256
scene.frame_start, scene.frame_end = 1, 5
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = os.path.join(d, "f_####")

stamps = []
pre = lambda *a: stamps.append(("pre", time.time()))      # noqa: E731
post = lambda *a: stamps.append(("post", time.time()))    # noqa: E731
bpy.app.handlers.render_pre.append(pre)
bpy.app.handlers.render_post.append(post)


def run(label):
    stamps.clear()
    t = time.time()
    bpy.ops.render.render(animation=True)
    total = time.time() - t
    per = [round(stamps[i + 1][1] - stamps[i][1], 3) for i in range(0, len(stamps) - 1, 2)
           if stamps[i][0] == "pre" and stamps[i + 1][0] == "post"]
    r = dict(first_s=per[0], rest_median_s=round(statistics.median(per[1:]), 3), total_s=round(total, 2), frames=len(per))
    print(label, r, flush=True)
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
    return r


res = {}
scene.render.engine = "BLENDER_WORKBENCH"
res["Workbench"] = run("Workbench")
scene.render.engine = "BLENDER_EEVEE_NEXT"
for n in (16, 64):
    scene.eevee.taa_render_samples = n
    res[f"EEVEE {n}"] = run(f"EEVEE {n}")
scene.render.engine = "CYCLES"
scene.cycles.use_denoising = False
scene.cycles.use_adaptive_sampling = False
scene.cycles.device = "CPU"
for n in (16, 64):
    scene.cycles.samples = n
    res[f"Cycles CPU {n}"] = run(f"Cycles CPU {n}")
dev = exp.metal(scene)
for n in (16, 64):
    scene.cycles.samples = n
    res[f"Cycles {dev} {n}"] = run(f"Cycles {dev} {n}")
scene.render.use_persistent_data = True
res[f"Cycles {dev} 64 persistent"] = run("persistent")
scene.render.use_persistent_data = False

E.fact("per-frame render time at 256 x 256 (first frame, then the median of frames 2-5), measured between the "
       "render_pre and render_post handlers inside one render(animation=True)", **res)
E.fact("EEVEE's first frame cost more than the later ones in the first EEVEE run (16 samples) and not in the second "
       "(64 samples); that this is shader compilation is not checked",
       eevee16_first=res["EEVEE 16"]["first_s"], eevee16_rest=res["EEVEE 16"]["rest_median_s"],
       eevee64_first=res["EEVEE 64"]["first_s"], eevee64_rest=res["EEVEE 64"]["rest_median_s"])
E.fact("at 256 px Cycles on the CPU was faster per frame than on Metal at 16 samples and level with it at 64; Metal's "
       "time barely changed from 16 to 64 samples (a fixed cost per frame), and persistent data cut most of that cost",
       cpu16=res["Cycles CPU 16"]["rest_median_s"], gpu16=res[f"Cycles {dev} 16"]["rest_median_s"],
       cpu64=res["Cycles CPU 64"]["rest_median_s"], gpu64=res[f"Cycles {dev} 64"]["rest_median_s"],
       gpu64_persistent=res[f"Cycles {dev} 64 persistent"]["rest_median_s"], device=dev)
shutil.rmtree(d)
E.save(results=res, device=dev, size=256)
