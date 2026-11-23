#!/usr/bin/env python3
"""The repository's runner is the skill's: skills/blender/scripts/run.py. This file forwards to it, so experiments can
keep calling `python3 tools/run.py ...` and importing `from run import blender`."""
import importlib.util
import os

_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills", "blender", "scripts", "run.py")
_spec = importlib.util.spec_from_file_location("_skill_run", _path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
blender, main = _mod.blender, _mod.main

if __name__ == "__main__":
    main()
