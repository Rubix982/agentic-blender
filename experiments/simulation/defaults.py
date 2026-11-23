"""What the physics settings default to in 4.5: cloth, cloth collision, collider, rigid body (object and world), soft body.

Read from bl_rna (the defaults a new modifier gets) and from a freshly made modifier/world, so the two can be compared."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import exp
E = exp.Experiment(__file__)


def props(obj, names=None):
    out = {}
    for p in obj.bl_rna.properties:
        if p.identifier in ("rna_type",) or p.type in ("POINTER", "COLLECTION"):
            continue
        if names and p.identifier not in names:
            continue
        try:
            v = getattr(obj, p.identifier)
        except Exception as e:  # noqa
            v = f"<{e}>"
        if hasattr(v, "__len__") and not isinstance(v, str):
            v = list(v)
        out[p.identifier] = v
    return out


bpy.ops.mesh.primitive_plane_add(size=1)
plane = bpy.context.object
cm = plane.modifiers.new("Cloth", "CLOTH")
cloth = props(cm.settings)
ccol = props(cm.collision_settings)
cache = props(cm.point_cache)

bpy.ops.mesh.primitive_cube_add(size=1)
cube = bpy.context.object
col = cube.modifiers.new("Collision", "COLLISION")
collider = props(cube.collision)

# rigid body: world and object
had_world = bpy.context.scene.rigidbody_world is not None
bpy.ops.rigidbody.world_add()
world = props(bpy.context.scene.rigidbody_world)
bpy.context.view_layer.objects.active = cube
cube.select_set(True)
bpy.ops.rigidbody.object_add()
rbo = props(cube.rigid_body)

bpy.ops.mesh.primitive_uv_sphere_add()
sph = bpy.context.object
sm = sph.modifiers.new("Softbody", "SOFT_BODY")
soft = props(sph.soft_body)

E.fact("a new cloth modifier's quality (steps per frame) is 5 and its pin stiffness is 1",
       quality=cloth["quality"], pin_stiffness=cloth["pin_stiffness"], mass_kg=cloth["mass"],
       air_damping=cloth["air_damping"], tension=cloth["tension_stiffness"], bending=cloth["bending_stiffness"],
       bending_model=cloth["bending_model"])
E.fact("a new cloth's collision distance is 15 mm against objects and against itself, and self-collision is off",
       distance_min=ccol["distance_min"], self_distance_min=ccol["self_distance_min"],
       use_self_collision=ccol["use_self_collision"], collision_quality=ccol["collision_quality"])
E.fact("a new cloth's cache runs from frame 1 to 250", frame_start=cache["frame_start"], frame_end=cache["frame_end"])
E.fact("a collider's own thickness_outer defaults to 0.02 (relative units) and its friction (cloth) to 5",
       thickness_outer=collider["thickness_outer"], cloth_friction=collider["cloth_friction"],
       damping=collider["damping"])
E.fact("a new scene has no rigid body world until one is added", had_world=had_world)
E.fact("a new rigid body world steps 10 substeps per frame with 10 solver iterations",
       substeps_per_frame=world["substeps_per_frame"], solver_iterations=world["solver_iterations"],
       point_cache_end=bpy.context.scene.rigidbody_world.point_cache.frame_end)
E.fact("a new rigid body is active, convex hull, mass 1 kg, collision margin 0.04 m with use_margin off",
       type=rbo["type"], shape=rbo["collision_shape"], mass=rbo["mass"], margin=rbo["collision_margin"],
       use_margin=rbo["use_margin"], friction=rbo["friction"], restitution=rbo["restitution"])
E.fact("a new soft body uses a goal (goal_default 0.7) and edge springs",
       use_goal=soft["use_goal"], goal_default=soft["goal_default"], use_edges=soft["use_edges"],
       use_self_collision=soft["use_self_collision"])
E.save(cloth=cloth, cloth_collision=ccol, cloth_cache=cache, collider=collider, rigidbody_world=world,
       rigidbody_object=rbo, soft_body=soft)
