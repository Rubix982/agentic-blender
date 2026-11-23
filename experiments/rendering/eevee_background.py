"""Does EEVEE (4.2+ "EEVEE Next") render in background mode (-b) on this Mac, how fast, and which 4.1 settings are gone?"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import time
import bpy
import numpy as np
from mathutils import Vector
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene

# --- the engine's name
names = {}
for name in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "CYCLES", "BLENDER_WORKBENCH", "HYDRA_STORM"):
    try:
        scene.render.engine = name
        names[name] = "ok"
    except TypeError as e:
        names[name] = str(e)
E.fact("in 4.5 the EEVEE engine id is BLENDER_EEVEE_NEXT; assigning the 2.8-4.1 id BLENDER_EEVEE raises TypeError, "
       "whose message lists the valid engines; with --factory-startup in -b, HYDRA_STORM is not among them",
       results=names)

# --- which 4.1 EEVEE ("Legacy") settings still exist
old = ["use_soft_shadows", "shadow_cube_size", "shadow_cascade_size", "use_shadow_high_bitdepth", "use_ssr",
       "use_ssr_refraction", "ssr_quality", "use_bloom", "bloom_intensity", "bloom_threshold", "use_motion_blur",
       "gi_auto_bake", "use_volumetric_lights", "sss_samples", "use_gtao", "gtao_distance", "taa_render_samples",
       "gi_diffuse_bounces", "use_shadows", "shadow_ray_count", "shadow_step_count", "use_raytracing",
       "ray_tracing_method", "shadow_resolution_scale", "use_fast_gi"]
present = {k: hasattr(scene.eevee, k) for k in old}
E.fact("SceneEEVEE attributes from 4.1 that are gone in 4.5 (hasattr False)",
       gone=[k for k, v in present.items() if not v], kept=[k for k, v in present.items() if v])
m = bpy.data.materials.new("probe")
light = bpy.data.lights.new("probe", "POINT")
E.fact("material and light attributes: which 4.1 EEVEE ones remain in 4.5",
       material={k: hasattr(m, k) for k in ("blend_method", "shadow_method", "surface_render_method", "use_screen_refraction",
                                            "show_transparent_back", "use_backface_culling_shadow", "use_transparency_overlap")},
       light={k: hasattr(light, k) for k in ("use_contact_shadow", "contact_shadow_distance", "shadow_buffer_bias",
                                             "shadow_soft_size", "use_shadow_jitter", "shadow_jitter_overblur",
                                             "shadow_filter_radius", "shadow_maximum_resolution")},
       render_use_motion_blur=hasattr(scene.render, "use_motion_blur"))
m.blend_method = "BLEND"
E.fact("material.blend_method still accepts 'BLEND' in 4.5 and maps onto surface_render_method",
       blend_method=m.blend_method, surface_render_method=m.surface_render_method,
       surface_render_method_items=[i.identifier for i in type(m).bl_rna.properties["surface_render_method"].enum_items])
bpy.data.materials.remove(m)
bpy.data.lights.remove(light)

# --- a scene: floor, glossy sphere, diffuse cube, sun, camera
def material(name, color, rough=0.5, metal=0.0):
    mt = bpy.data.materials.new(name)
    mt.use_nodes = True
    b = next(n for n in mt.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return mt


bpy.ops.mesh.primitive_plane_add(size=12)
bpy.context.object.data.materials.append(material("floor", (0.8, 0.8, 0.8), rough=0.1))
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1), segments=48, ring_count=24)
bpy.ops.object.shade_smooth()
bpy.context.object.data.materials.append(material("chrome", (0.9, 0.9, 0.9), rough=0.05, metal=1.0))
bpy.ops.mesh.primitive_cube_add(size=1.2, location=(1.8, 0.6, 0.6))
bpy.context.object.data.materials.append(material("red", (0.8, 0.1, 0.1)))
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3.0
sun.data.angle = 0.1
sun.rotation_euler = (0.7, 0.2, 0.5)
scene.collection.objects.link(sun)
world = bpy.data.worlds.new("World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.4, 0.5, 0.7, 1)
scene.world = world
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.location = (5, -6, 3.5)
cam.rotation_euler = (Vector((0.5, 0, 0.8)) - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = scene.render.resolution_y = 256
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"


def render(tag=None):
    scene.render.filepath = E.out((tag or "tmp") + ".exr")
    t = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t
    img = bpy.data.images.load(scene.render.filepath)
    px = np.array(img.pixels[:], dtype=np.float32).reshape(256, 256, 4)[..., :3]
    bpy.data.images.remove(img)
    if not tag:
        os.remove(scene.render.filepath)
    return round(dt, 2), px


first, px_first = render()
rows = {}
for spp in (1, 16, 64):
    scene.eevee.taa_render_samples = spp
    rows[spp] = render()[0]
E.fact("EEVEE renders in background mode on macOS (Metal); the first render of a session pays shader compilation",
       first_render_s=first, mean=round(float(px_first.mean()), 4), seconds_by_taa_render_samples=rows)

scene.eevee.taa_render_samples = 16
_, px_on = render()
scene.eevee.use_shadows = False
t_noshadow, px_off = render()
scene.eevee.use_shadows = True
# the floor right under the sphere is in its shadow: compare that patch
E.fact("scene.eevee.use_shadows=False turns off all shadows: the image brightens (by little here: the shadowed area is small)",
       mean_with=round(float(px_on.mean()), 4), mean_without=round(float(px_off.mean()), 4))

scene.eevee.use_raytracing = True
t_rt, px_rt = render()
scene.eevee.ray_tracing_method = "PROBE"
t_probe, px_probe = render()
E.fact("turning on scene.eevee.use_raytracing (off by default) changes the image (reflections now traced in screen space) "
       "and costs time",
       seconds_off=rows[16], seconds_on=t_rt, mean_abs_change=round(float(np.abs(px_rt - px_on).mean()), 4),
       ray_tracing_method_items=[i.identifier for i in type(scene.eevee).bl_rna.properties["ray_tracing_method"].enum_items])
scene.eevee.use_raytracing = False

E.save(engines=names, present=present)
