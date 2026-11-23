"""Does the experiment harness work: an empty scene, Cycles' GPU device found, a fact saved."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import exp
E = exp.Experiment(__file__)
n = len(bpy.data.objects)
dev = exp.metal()
E.fact("an empty scene after read_factory_settings(use_empty=True) has no objects", objects=n)
E.fact("Cycles' GPU device type on this machine", device=dev, devices=[d.name for d in bpy.context.preferences.addons['cycles'].preferences.devices])
E.save(args_after_dashdash=sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
