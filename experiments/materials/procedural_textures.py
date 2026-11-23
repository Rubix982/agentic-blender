"""Which procedural texture nodes exist in 4.5 (Musgrave was merged into Noise in 4.1), what are their modes and inputs,
and what range do their outputs cover? Each texture's Fac/Distance is rendered as emission (Raw view) on a plane
filling the frame; a contact sheet is saved."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import numpy as np
import OpenImageIO as oiio
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
tex_types = sorted(n for n in dir(bpy.types) if n.startswith("ShaderNodeTex"))
E.fact("shader texture node types in 4.5 (Gabor is new in 4.3; there is no ShaderNodeTexMusgrave)", types=tex_types)
m = bpy.data.materials.new("t")
m.use_nodes = True
nt = m.node_tree
try:
    nt.nodes.new("ShaderNodeTexMusgrave")
    musgrave = "created"
except RuntimeError as e:
    musgrave = str(e).strip()
E.fact("nodes.new('ShaderNodeTexMusgrave') raises RuntimeError in 4.5", error=musgrave)


def describe(idname):
    n = nt.nodes.new(idname)
    props = {}
    for p in n.bl_rna.properties:
        if p.type == "ENUM" and p.identifier not in bpy.types.ShaderNode.bl_rna.properties:
            props[p.identifier] = dict(value=getattr(n, p.identifier), items=[i.identifier for i in p.enum_items])
        elif p.type == "BOOLEAN" and p.identifier not in bpy.types.ShaderNode.bl_rna.properties:
            props[p.identifier] = getattr(n, p.identifier)
    d = dict(inputs=[s.name for s in n.inputs if s.enabled], outputs=[s.name for s in n.outputs if s.enabled], props=props)
    nt.nodes.remove(n)
    return d


info = {t: describe(t) for t in ("ShaderNodeTexNoise", "ShaderNodeTexVoronoi", "ShaderNodeTexWave", "ShaderNodeTexGabor",
                                  "ShaderNodeTexMagic", "ShaderNodeTexBrick", "ShaderNodeTexChecker",
                                  "ShaderNodeTexGradient", "ShaderNodeTexWhiteNoise")}
for k, v in info.items():
    print(k, v)
E.fact("Noise Texture in 4.5 carries the old Musgrave types: noise_type FBM (default), MULTIFRACTAL, RIDGED_MULTIFRACTAL, "
       "HYBRID_MULTIFRACTAL, HETERO_TERRAIN, with a Lacunarity input (Offset and Gain appear only for the multifractal "
       "types that use them) and a normalize switch",
       noise=info["ShaderNodeTexNoise"],
       hidden_inputs_fbm=[s.name for s in nt.nodes.new("ShaderNodeTexNoise").inputs if not s.enabled])
E.fact("Voronoi Texture in 4.5 has fractal Detail/Roughness/Lacunarity inputs and a normalize switch", voronoi=info["ShaderNodeTexVoronoi"])
E.fact("Wave, Gabor, Magic, Brick, Checker, Gradient, White Noise: modes and sockets",
       **{k.replace("ShaderNodeTex", "").lower(): v for k, v in info.items()
          if k not in ("ShaderNodeTexNoise", "ShaderNodeTexVoronoi")})

# value ranges: render each texture's scalar output as emission on a plane that fills an orthographic view
bpy.ops.mesh.primitive_plane_add(size=2)
bpy.context.object.data.materials.append(m)
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 2
cam.location = (0, 0, 2)
scene.collection.objects.link(cam)
scene.camera = cam
scene.world = None
scene.render.engine = "CYCLES"
exp.metal()
scene.cycles.samples = 4
scene.cycles.use_denoising = False
scene.render.resolution_x = scene.render.resolution_y = 128
scene.render.image_settings.file_format = "OPEN_EXR"
scene.view_settings.view_transform = "Raw"
nt.nodes.remove(next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"))
em = nt.nodes.new("ShaderNodeEmission")
nt.links.new(em.outputs[0], next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL").inputs["Surface"])
tc = nt.nodes.new("ShaderNodeTexCoord")
cases = [("Noise FBM", "ShaderNodeTexNoise", {}, "Fac"),
         ("Noise RIDGED_MULTIFRACTAL", "ShaderNodeTexNoise", {"noise_type": "RIDGED_MULTIFRACTAL"}, "Fac"),
         ("Noise HETERO_TERRAIN", "ShaderNodeTexNoise", {"noise_type": "HETERO_TERRAIN"}, "Fac"),
         ("Voronoi F1 Distance", "ShaderNodeTexVoronoi", {}, "Distance"),
         ("Wave bands", "ShaderNodeTexWave", {}, "Fac"),
         ("Gabor", "ShaderNodeTexGabor", {}, "Value"),
         ("Magic", "ShaderNodeTexMagic", {}, "Fac"),
         ("Brick", "ShaderNodeTexBrick", {}, "Fac"),
         ("Checker", "ShaderNodeTexChecker", {}, "Fac"),
         ("Gradient linear", "ShaderNodeTexGradient", {}, "Fac"),
         ("White Noise", "ShaderNodeTexWhiteNoise", {}, "Value")]
rows, tiles = [], []
for label, idname, props, out in cases:
    n = nt.nodes.new(idname)
    for k, v in props.items():
        setattr(n, k, v)
    nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    nt.links.new(n.outputs[out], em.inputs["Color"])
    scene.render.filepath = E.out("tmp.exr")
    bpy.ops.render.render(write_still=True)
    a = oiio.ImageBuf(scene.render.filepath).get_pixels(oiio.FLOAT)[..., 0]
    os.remove(scene.render.filepath)
    rows.append(dict(texture=label, output=out, min=round(float(a.min()), 3), mean=round(float(a.mean()), 3),
                     max=round(float(a.max()), 3)))
    tiles.append(np.clip(a, 0, 1))
    nt.nodes.remove(n)
for r in rows:
    print(r)
E.fact("the range each texture's scalar output covers over a 2 m plane (Object coordinates, default settings): Noise FBM Fac "
       "stays in about 0.25-0.75 around 0.5; RIDGED_MULTIFRACTAL sits near 0; HETERO_TERRAIN goes negative (-0.73..0.73); "
       "Voronoi F1 Distance passes 1; the rest stay in 0..1",
       rows=rows)
# contact sheet: 4 columns of 128 px tiles (512 px wide)
while len(tiles) % 4:
    tiles.append(np.zeros((128, 128), np.float32))
sheet = np.vstack([np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles), 4)])
img = np.ascontiguousarray((sheet ** (1 / 2.2) * 255).astype(np.uint8)[:, :, None])  # OIIO wants (H, W, C)
out = oiio.ImageOutput.create(E.out("sheet.png"))
out.open(E.out("sheet.png"), oiio.ImageSpec(img.shape[1], img.shape[0], 1, oiio.UINT8))
out.write_image(img)
out.close()
E.fact("contact sheet saved (row-major, in the order of the rows above)", file="procedural_textures-sheet.png",
       order=[r["texture"] for r in rows])
E.save(info=info, rows=rows)
