"""C-004, the photographic finish 9 of the 17 artists added in another program (kb/research/realism-breakdowns.md),
done in Blender 4.5's compositor headless: glow (Glare, Bloom and Fog Glow), chromatic aberration (Lens Distortion's
Dispersion), a vignette (Ellipse Mask, Blur, Multiply), grain (a Texture node with a Noise texture), and a warm
grade (Color Balance gain). Each is measured on a test frame made of emission planes: a flat grey field, and a dark
field with one very bright dot and a vertical white-to-black edge."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import numpy as np
import OpenImageIO as oiio
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
scene.view_settings.view_transform = "Standard"
scene.render.engine = "CYCLES"
scene.cycles.samples = 4
scene.cycles.use_denoising = False
S = 256
scene.render.resolution_x = scene.render.resolution_y = S
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"


def emitter(name, value, size, loc, strength=1.0):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = (size[0], size[1], 1)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (value, value, value, 1)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    ob.data.materials.append(m)
    return ob


cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 2
cam.location = (0, 0, 5)
scene.collection.objects.link(cam)
scene.camera = cam
scene.world = bpy.data.worlds.new("Black")
scene.world.use_nodes = True
next(n for n in scene.world.node_tree.nodes if n.type == "BACKGROUND").inputs["Color"].default_value = (0, 0, 0, 1)

flat = emitter("Grey", 0.18, (2.2, 2.2), (0, 0, 0))          # fills the frame
dark = [emitter("Dark", 0.02, (2.2, 2.2), (0, 0, 0.001)),
        emitter("White", 1.0, (0.5, 1.0), (0.85, -0.5, 0.002)),  # an edge at x = 0.6, off-centre (dispersion is radial)
        emitter("Dot", 1.0, (0.03, 0.03), (-0.5, 0.5, 0.003), strength=60)]


def use(test):
    for ob in dark:
        ob.hide_render = test != "dark"
    flat.hide_render = test != "flat"


def chain(build):
    """Render Layers -> build(tree, image socket) -> Composite; build=None leaves the compositor off."""
    scene.use_nodes = build is not None
    if build is None:
        return
    tree = scene.node_tree
    for n in list(tree.nodes):
        tree.nodes.remove(n)
    rl = tree.nodes.new("CompositorNodeRLayers")
    comp = tree.nodes.new("CompositorNodeComposite")
    tree.links.new(build(tree, rl.outputs["Image"]), comp.inputs["Image"])


def render(frame=1):
    scene.frame_set(frame)
    scene.render.filepath = E.out("tmp.exr")
    bpy.ops.render.render(write_still=True)
    px = oiio.ImageBuf(scene.render.filepath).get_pixels(oiio.FLOAT)
    os.remove(scene.render.filepath)
    return px[:, :, :3]


lum = lambda px: px @ np.array([0.2126, 0.7152, 0.0722])
DOT = (int(S * 0.25), int(S * 0.25))                          # row, column of the dot (top-left quarter)


def rings(px):
    L = lum(px)
    yy, xx = np.mgrid[0:S, 0:S]
    d = np.hypot(yy - DOT[0], xx - DOT[1])
    return {f"r{r}": round(float(L[(d >= r - 0.5) & (d < r + 0.5)].mean()), 4) for r in (4, 8, 16, 32, 64)}


def edge(px, row=int(S * 0.75)):
    """Where each channel crosses half-way along a row through the white-to-black edge (column, sub-pixel)."""
    out = {}
    for i, ch in enumerate("RGB"):
        line = px[row, :, i]
        half = (line.min() + line.max()) / 2
        c = int(np.argmax(line > half))
        out[ch] = round(float(c - 1 + (half - line[c - 1]) / (line[c] - line[c - 1])), 2) if c > 0 else None
    return out


rows = {}
# glow
use("dark")
chain(None)
rows["none"] = dict(rings=rings(render()))
for kind in ("BLOOM", "FOG_GLOW"):
    def glare(tree, img, kind=kind):
        g = tree.nodes.new("CompositorNodeGlare")
        g.glare_type = kind
        g.quality = "HIGH"
        tree.links.new(img, g.inputs["Image"])
        return g.outputs["Image"]
    chain(glare)
    rows[f"Glare {kind}, threshold 1"] = dict(rings=rings(render()))
new_glare = scene.node_tree.nodes.new("CompositorNodeGlare")
E.fact("luminance at 4, 8, 16, 32 and 64 px from a dot of strength 60 on a dark field, with no glare and with Glare's "
       "Bloom and Fog Glow (each set explicitly: a new Glare node starts as this type)", new_glare_type=new_glare.glare_type,
       rows=rows)

# chromatic aberration
rows = {}
chain(None)
rows["none"] = edge(render())
for disp in (0.02, 0.05, 0.1):
    def lens(tree, img, disp=disp):
        n = tree.nodes.new("CompositorNodeLensdist")
        n.inputs["Dispersion"].default_value = disp
        tree.links.new(img, n.inputs["Image"])
        return n.outputs["Image"]
    chain(lens)
    rows[f"Lens Distortion, dispersion {disp}"] = edge(render())
E.fact("where red, green and blue cross half-way along a row through a black-to-white edge 0.8 of the way across "
       "and a quarter up from the bottom (column, 256 px frame): Lens Distortion's Dispersion splits them", rows=rows)

# vignette, grain, grade on the flat field
use("flat")
rows = {}
chain(None)
base = render()
corner = lambda px: float(lum(px)[4:20, 4:20].mean())
centre = lambda px: float(lum(px)[120:136, 120:136].mean())
rows["none"] = dict(centre=round(centre(base), 4), corner=round(corner(base), 4), std=round(float(lum(base)[100:156, 100:156].std()), 5),
                    r_over_b=round(float(base[..., 0].mean() / base[..., 2].mean()), 4))


def vignette(tree, img):
    m = tree.nodes.new("CompositorNodeEllipseMask")
    m.inputs["Size"].default_value = (0.95, 0.95)
    b = tree.nodes.new("CompositorNodeBlur")
    b.filter_type = "GAUSS"
    b.inputs["Size"].default_value = (60, 60)
    mul = tree.nodes.new("CompositorNodeMixRGB")
    mul.blend_type = "MULTIPLY"
    tree.links.new(m.outputs["Mask"], b.inputs["Image"])
    tree.links.new(img, mul.inputs[1])
    tree.links.new(b.outputs["Image"], mul.inputs[2])
    return mul.outputs["Image"]


chain(vignette)
px = render()
rows["vignette: Ellipse Mask 0.95, Gaussian Blur 60 px, Multiply"] = dict(centre=round(centre(px), 4), corner=round(corner(px), 4))


def soft_vignette(tree, img):
    out = vignette(tree, img)
    out.node.inputs["Fac"].default_value = 0.3
    return out


chain(soft_vignette)
px = render()
rows["vignette as above, Multiply at Fac 0.3"] = dict(centre=round(centre(px), 4), corner=round(corner(px), 4))

tex = bpy.data.textures.new("Grain", "NOISE")


def grain(tree, img):
    t = tree.nodes.new("CompositorNodeTexture")
    t.texture = tex
    mix = tree.nodes.new("CompositorNodeMixRGB")
    mix.blend_type = "OVERLAY"
    mix.inputs["Fac"].default_value = 0.15
    tree.links.new(img, mix.inputs[1])
    tree.links.new(t.outputs["Color"], mix.inputs[2])
    return mix.outputs["Image"]


chain(grain)
g1, g2 = render(1), render(2)
p1, p2 = lum(g1)[100:156, 100:156], lum(g2)[100:156, 100:156]
rows["grain: Texture node (Noise texture), Overlay at 0.15"] = dict(
    mean=round(float(p1.mean()), 4), std=round(float(p1.std()), 5),
    frame1_vs_frame2_correlation=round(float(np.corrcoef(p1.ravel(), p2.ravel())[0, 1]), 3))


def grade(tree, img):
    cb = tree.nodes.new("CompositorNodeColorBalance")
    cb.correction_method = "LIFT_GAMMA_GAIN"
    next(s for s in cb.inputs if s.identifier == "Color Gain").default_value = (1.1, 1.0, 0.9, 1)
    tree.links.new(img, next(s for s in cb.inputs if s.identifier == "Image"))
    return cb.outputs["Image"]


chain(grade)
px = render()
rows["grade: Color Balance, gain colour (1.1, 1.0, 0.9)"] = dict(r_over_b=round(float(px[..., 0].mean() / px[..., 2].mean()), 4),
                                                                  centre=round(centre(px), 4))
E.fact("on a flat 0.18 grey frame: centre and corner luminance, noise (standard deviation) and red over blue, with no "
       "compositing and with each effect; for grain, also how alike its pattern is on frames 1 and 2", rows=rows)
E.save()
