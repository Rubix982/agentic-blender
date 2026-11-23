"""Shared by the reference solutions: the output path, and an object linked into the scene."""
import sys

import bpy

OUT = sys.argv[sys.argv.index("--") + 1]


def link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj
