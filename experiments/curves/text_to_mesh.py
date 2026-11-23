"""Text objects from Python: body, size, extrude/bevel, alignment, and conversion to a mesh."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy, bmesh
import exp
E = exp.Experiment(__file__)


def ev(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    e = ob.evaluated_get(dg); me = e.to_mesh()
    xs = [v.co.x for v in me.vertices]; zs = [v.co.z for v in me.vertices]
    bm = bmesh.new(); bm.from_mesh(me); man = all(x.is_manifold for x in bm.edges) if bm.edges else None; bm.free()
    r = dict(verts=len(me.vertices), faces=len(me.polygons), width=round(max(xs) - min(xs), 4) if xs else 0,
             depth=round(max(zs) - min(zs), 4) if zs else 0, manifold=man)
    e.to_mesh_clear()
    return r

cu = bpy.data.curves.new("txt", "FONT")
cu.body = "Hello"
ob = bpy.data.objects.new("txt", cu); bpy.context.scene.collection.objects.link(ob)
E.fact("bpy.data.curves.new(name, 'FONT') gives a TextCurve; the default font is the built-in Bfont", type=type(cu).__name__, font=cu.font.name if cu.font else None,
       size=cu.size, align_x=cu.align_x, align_y=cu.align_y, fonts=[f.name for f in bpy.data.fonts])
E.fact("flat text 'Hello' evaluates to filled faces, no depth", **ev(ob))
cu.extrude = 0.05
E.fact("extrude 0.05 gives depth 0.1 (extrude goes both ways)", **ev(ob))
cu.bevel_depth = 0.01; cu.bevel_resolution = 2
E.fact("bevel_depth 0.01 rounds the edges and adds to the size", **ev(ob))
cu.bevel_depth = 0; cu.extrude = 0
cu.size = 2.0
E.fact("size 2 doubles the width", **ev(ob))
cu.size = 1.0
cu.align_x = "CENTER"
dg = bpy.context.evaluated_depsgraph_get(); me = ob.evaluated_get(dg).to_mesh(); xs = [v.co.x for v in me.vertices]; ob.evaluated_get(dg).to_mesh_clear()
E.fact("align_x CENTER centres the text on the origin", x_min=round(min(xs), 4), x_max=round(max(xs), 4),
       aligns=[e.identifier for e in cu.bl_rna.properties["align_x"].enum_items])
cu.body = "A\nB"
E.fact("a newline in body makes a second line", **ev(ob))
cu.body = "Héllo ✓"
E.fact("non-ASCII characters missing from Bfont produce no geometry for that glyph (no error)", **ev(ob))
# load a font file from the Blender install
fdir = os.path.join(bpy.utils.system_resource("DATAFILES"), "fonts")
fonts_avail = sorted(os.listdir(fdir)) if os.path.isdir(fdir) else []
E.fact("font files shipped in datafiles/fonts", files=fonts_avail)
cu.body = "Hello"
cu.extrude = 0.05
# to mesh
me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
bm = bmesh.new(); bm.from_mesh(me)
before = (len(bm.verts), all(e.is_manifold for e in bm.edges))
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
after = (len(bm.verts), all(e.is_manifold for e in bm.edges), sum(1 for f in bm.faces if len(f.verts) > 4))
bm.free()
E.fact("extruded text converted with new_from_object: (verts, manifold) before and after remove_doubles, and the number of n-gons",
       before=before, after_remove_doubles=after[:2], ngons=after[2])
E.save()
