"""Helpers for experiments, imported inside Blender.

At the top of an experiment (experiments/<area>/<name>.py):

    import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
    import exp
    E = exp.Experiment(__file__)          # resets to an empty scene unless keep_scene=True
    ...
    E.fact("Cycles finds the Metal device on this machine", device="METAL")   # one plain sentence, with its numbers
    E.save(timing_s=..., anything_else=...)  # writes experiments/<area>/results/<name>.json

A fact is a sentence that could be checked and come out false. Its keyword arguments are the numbers behind it.
"""
import datetime
import json
import os
import platform
import time

import bpy


class Experiment:
    def __init__(self, path, keep_scene=False):
        self.path = os.path.abspath(path)
        self.name = os.path.splitext(os.path.basename(self.path))[0]
        self.dir = os.path.join(os.path.dirname(self.path), "results")
        os.makedirs(self.dir, exist_ok=True)
        self.facts = []
        self.t0 = time.time()
        if not keep_scene:
            empty()

    def out(self, filename):
        """A path for a small output file (an image at most 512 px, a .blend kept only if small)."""
        return os.path.join(self.dir, f"{self.name}-{filename}")

    def fact(self, sentence, **numbers):
        self.facts.append(dict(fact=sentence, **numbers))
        print("FACT", sentence, numbers if numbers else "", flush=True)

    def save(self, **data):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        rec = dict(experiment=os.path.relpath(self.path, root), blender=bpy.app.version_string,
                   machine=f"{platform.system()} {platform.machine()}", date=datetime.date.today().isoformat(),
                   seconds=round(time.time() - self.t0, 2), facts=self.facts, data=data)
        text = json.dumps(rec, indent=1, default=str).replace(os.path.expanduser("~"), "~")   # no home paths
        with open(os.path.join(self.dir, f"{self.name}.json"), "w") as f:
            f.write(text)
        print("SAVED", os.path.join(self.dir, f"{self.name}.json"), flush=True)


def empty():
    """An empty scene: factory startup's cube, camera and light removed, orphan data purged."""
    bpy.ops.wm.read_factory_settings(use_empty=True)


def metal(scene=None):
    """Point Cycles at the GPU (Metal on Apple Silicon) if there is one; returns the device type used, or 'CPU'."""
    scene = scene or bpy.context.scene
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
        try:
            prefs.compute_device_type = kind
        except TypeError:
            continue
        prefs.get_devices()
        devs = [d for d in prefs.devices if d.type == kind]
        if devs:
            for d in prefs.devices:
                d.use = d.type == kind
            scene.cycles.device = "GPU"
            return kind
    scene.cycles.device = "CPU"
    return "CPU"
