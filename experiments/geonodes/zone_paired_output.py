"""Reading `paired_output` on a zone's input node before it is paired: found when the inventory crashed Blender 4.5.14
(segfault in GeometryNodeClosureInput_paired_output_get). Each zone input node is tried in its own Blender process,
unpaired and paired, so a crash is a result rather than the end of the run.

Run with the system Python:  python3 experiments/geonodes/zone_paired_output.py
"""
import datetime
import json
import os
import platform
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from run import blender  # noqa: E402

B = blender()
TMP = tempfile.mkdtemp(prefix="bfg-zone-")
ZONES = {"GeometryNodeRepeatInput": "GeometryNodeRepeatOutput", "GeometryNodeSimulationInput": "GeometryNodeSimulationOutput",
         "GeometryNodeForeachGeometryElementInput": "GeometryNodeForeachGeometryElementOutput",
         "GeometryNodeClosureInput": "GeometryNodeClosureOutput"}
res = {}
for inp, out in ZONES.items():
    for paired in (False, True):
        body = ("import bpy\n"
                "t = bpy.data.node_groups.new('t', 'GeometryNodeTree')\n"
                f"n = t.nodes.new({inp!r})\nprint('STEP made input', flush=True)\n"
                + (f"o = t.nodes.new({out!r})\nprint('STEP made output', flush=True)\n"
                   "print('PAIR', n.pair_with_output(o), flush=True)\n" if paired else "")
                + "p = n.paired_output\nprint('READ', None if p is None else p.bl_idname, flush=True)\n")
        path = os.path.join(TMP, f"{inp}_{paired}.py")
        open(path, "w").write(body)
        r = subprocess.run([B, "-b", "--factory-startup", "--python", path], capture_output=True, text=True, timeout=120)
        read = [l for l in r.stdout.splitlines() if l.startswith("READ")]
        pair = [l for l in r.stdout.splitlines() if l.startswith("PAIR")]
        steps = [l[5:] for l in r.stdout.splitlines() if l.startswith("STEP")]
        err = [l for l in (r.stdout + r.stderr).splitlines() if "Error" in l][:1]
        res[f"{inp} {'paired' if paired else 'unpaired'}"] = dict(exit=r.returncode, read=read[0][5:] if read else None,
                                                                  paired_ok=pair[0][5:] if pair else None, steps_done=steps,
                                                                  error=err[0][:120] if err else None)
        print(inp, paired, res[f"{inp} {'paired' if paired else 'unpaired'}"], flush=True)
fact = dict(fact="Reading node.paired_output on a zone's input node in 4.5.14 (exit -11 is a segfault): for the Repeat, "
                 "Simulation and For Each Element inputs it returns None unpaired and the output node once paired; for "
                 "the Closure Input, Blender crashed in both cases: reading paired_output on an unpaired one (the backtrace "
                 "names GeometryNodeClosureInput_paired_output_get), and calling pair_with_output (both nodes were made, "
                 "then the crash). From Python, leave the Closure zone alone in 4.5.14", **res)
rec = dict(experiment=os.path.relpath(os.path.abspath(__file__), ROOT),
           blender=subprocess.run([B, "--version"], capture_output=True, text=True).stdout.splitlines()[0],
           machine=f"{platform.system()} {platform.machine()}", date=datetime.date.today().isoformat(), facts=[fact])
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"), exist_ok=True)
json.dump(rec, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "zone_paired_output.json"), "w"), indent=1)
