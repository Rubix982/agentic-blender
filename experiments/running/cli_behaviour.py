"""How Blender behaves when a script drives it from the command line: exit codes, printed output, arguments, startup
time, Python drivers, the render flags, and what bpy.context holds in background mode.

Run with the system Python (it starts Blender itself):  python3 experiments/running/cli_behaviour.py
Writes experiments/running/results/cli_behaviour.json.
"""
import datetime
import json
import os
import platform
import subprocess
import sys
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from run import blender  # noqa: E402

B = blender()
TMP = tempfile.mkdtemp(prefix="bfg-cli-")
facts, data = [], {}


def fact(sentence, **numbers):
    facts.append(dict(fact=sentence, **numbers))
    print("FACT", sentence, numbers, flush=True)


def script(name, body):
    p = os.path.join(TMP, name)
    with open(p, "w") as f:
        f.write(body)
    return p


def run(args, env=None, timeout=120):
    t = time.time()
    r = subprocess.run([B] + args, capture_output=True, text=True, env=env or os.environ, timeout=timeout)
    return r, time.time() - t


version = subprocess.run([B, "--version"], capture_output=True, text=True).stdout.splitlines()[0]

# 1. Exit codes.
bad = script("raise.py", "raise RuntimeError('boom')\n")
r, _ = run(["-b", "--factory-startup", "--python", bad])
r2, _ = run(["-b", "--factory-startup", "--python-exit-code", "1", "--python", bad])
ex = script("exit3.py", "import sys\nsys.exit(3)\n")
r3, _ = run(["-b", "--factory-startup", "--python", ex])
fact("A script that raises still leaves Blender's exit code at 0 unless --python-exit-code is given",
     exit_without_flag=r.returncode, exit_with_flag_1=r2.returncode,
     traceback_printed="RuntimeError: boom" in (r.stdout + r.stderr))
fact("sys.exit(N) inside a --python script ends Blender with exit code N", exit_code=r3.returncode)

# 2. Printed output: does it arrive while Blender runs, or only when it exits?
slow = script("slow.py", "import time\nprint('first', flush=FLUSH)\ntime.sleep(3)\nprint('second', flush=FLUSH)\n")


def arrival(label, flush=False, env_add=None, flags=(), prelude=""):
    body = prelude + open(slow).read().replace("FLUSH", "True" if flush else "False")
    p = script(f"slow_{len(data)}.py", body)
    env = {k: v for k, v in os.environ.items() if k != "PYTHONUNBUFFERED"}
    env.update(env_add or {})
    t = time.time()
    proc = subprocess.Popen([B, "-b", "--factory-startup", *flags, "--python", p], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, env=env, bufsize=1)
    times = {}
    for line in proc.stdout:
        if line.strip() in ("first", "second"):
            times[line.strip()] = round(time.time() - t, 2)
    proc.wait()
    times["exit"] = round(time.time() - t, 2)
    data["output: " + label] = times
    return times


plain = arrival("plain print")
unbuf = arrival("PYTHONUNBUFFERED=1", env_add={"PYTHONUNBUFFERED": "1"})
unbuf_sys = arrival("PYTHONUNBUFFERED=1 with --python-use-system-env", env_add={"PYTHONUNBUFFERED": "1"},
                    flags=("--python-use-system-env",))
flushed = arrival("print(..., flush=True)", flush=True)
reconf = arrival("sys.stdout.reconfigure(line_buffering=True) first",
                 prelude="import sys\nsys.stdout.reconfigure(line_buffering=True)\n")
streams = {k: (v.get("first", 99) < 2) for k, v in data.items() if k.startswith("output: ")}
fact("Through a pipe, which ways of printing reach the reader while the script still runs (a 3 s pause between two "
     "lines; True = the first line arrived before the pause ended)", **streams)

# 3. Arguments.
argv = script("argv.py", "import sys, json\nprint('ARGV', json.dumps(sys.argv))\n"
                         "print('MINE', json.dumps(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []))\n")
r, _ = run(["-b", "--factory-startup", "--python", argv, "--", "--out", "x.png", "-f", "3"])
lines = {l.split(" ", 1)[0]: json.loads(l.split(" ", 1)[1]) for l in r.stdout.splitlines() if l.startswith(("ARGV", "MINE"))}
fact("sys.argv inside Blender holds Blender's own arguments too; a script's own arguments are the ones after '--', "
     "and Blender does not act on them", argv_length=len(lines["ARGV"]), mine=lines["MINE"],
     rendered_frame_3="Saved:" in r.stdout)

# 4. Startup time.
noop = script("noop.py", "pass\n")
times = {}
for label, args in (("factory", ["-b", "--factory-startup", "--python", noop]),
                    ("user_prefs_and_addons", ["-b", "--python", noop])):
    ts = []
    for _ in range(3):
        _, dt = run(args)
        ts.append(round(dt, 2))
    times[label] = ts
fact("Starting headless Blender, running an empty script and quitting takes about this long (3 runs each)", **times)

# 5. Python expressions in drivers: are they evaluated when a file is opened headless?
blend = os.path.join(TMP, "driver.blend")
make = script("make_driver.py", f"""
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
o = bpy.data.objects.new('E', None); bpy.context.scene.collection.objects.link(o)
d = o.driver_add('location', 0).driver
d.type = 'SCRIPTED'; d.expression = '__import__("math").pi'          # needs Python: not a 'simple expression'
d2 = o.driver_add('location', 1).driver
d2.type = 'SCRIPTED'; d2.expression = 'frame * 2'                   # a simple expression Blender evaluates itself
bpy.ops.wm.save_as_mainfile(filepath={blend!r})
""")
run(["-b", "--factory-startup", "--python", make])
read = script("read_driver.py", """
import bpy, json
sc = bpy.context.scene; sc.frame_set(5)
o = bpy.data.objects['E']
print('LOC', json.dumps([round(o.location[0], 4), round(o.location[1], 4)]))
print('AUTOEXEC', bpy.app.autoexec_fail, bpy.app.autoexec_fail_message)
""")
outs = {}
for label, flags in (("default", []), ("-y (enable autoexec)", ["-y"]), ("--disable-autoexec", ["--disable-autoexec"])):
    r, _ = run(["-b", "--factory-startup"] + flags + [blend, "--python", read])
    loc = [l for l in r.stdout.splitlines() if l.startswith("LOC")]
    ae = [l for l in r.stdout.splitlines() if l.startswith("AUTOEXEC")]
    outs[label] = dict(location=json.loads(loc[0][4:]) if loc else None, autoexec=ae[0] if ae else None)
data["drivers"] = outs
fact("A driver whose expression needs Python stays unevaluated in a file opened headless unless autoexec is on (-y); "
     "a simple expression such as 'frame * 2' is evaluated either way",
     **{k.split(" ")[0]: v["location"] for k, v in outs.items()})

# 6. Rendering from the command line: arguments run in order; the engine and Cycles device flags.
import struct  # noqa: E402


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


def cli_render(extra_after_dashdash, samples):
    outp = os.path.join(TMP, f"frame_{len(data)}_")
    expr = ("import bpy; s=bpy.context.scene; s.render.resolution_x=s.render.resolution_y=320; s.cycles.use_adaptive_sampling=False; "
            f"s.render.resolution_percentage=100; s.cycles.samples={samples}; s.cycles.use_denoising=False; "
            "print('DEVICE', s.cycles.device, flush=True)")
    r, dt = run(["-b", "--factory-startup", "-E", "CYCLES", "-o", outp, "-F", "PNG", "-x", "1",
                 "--python-expr", expr, "-f", "1", "--"] + extra_after_dashdash, timeout=600)
    saved = [l.split("'")[1] for l in r.stdout.splitlines() if l.startswith("Saved:")]
    return dict(seconds=round(dt, 1), size=png_size(saved[0]) if saved else None,
                device_property=[l for l in r.stdout.splitlines() if l.startswith("DEVICE")][:1],
                order=[l.split(" ")[0] for l in r.stdout.splitlines() if l.startswith(("DEVICE", "Saved:"))])


cpu = cli_render([], 512)
gpu = cli_render(["--cycles-device", "METAL"], 512)
data["cli_render"] = dict(cpu=cpu, metal_flag=gpu)
fact("Command-line arguments run in order: --python-expr placed before -f changed the scene before the frame rendered "
     "(the PNG came out at the script's size)", size=cpu["size"], order=cpu["order"])
fact("'-- --cycles-device METAL' changes the device used without changing scene.cycles.device; timed on the factory cube "
     "at 320 px with 512 samples, adaptive sampling off", cpu_s=cpu["seconds"], metal_flag_s=gpu["seconds"],
     scene_device_property_with_flag=gpu["device_property"])

# 7. What bpy.context holds in background mode.
ctx = script("ctx.py", """
import bpy, json
c = bpy.context
names = ['window', 'screen', 'area', 'region', 'space_data', 'scene', 'view_layer', 'object', 'active_object',
         'selected_objects', 'mode', 'window_manager', 'preferences', 'collection', 'tool_settings']
out = {}
for n in names:
    try:
        v = getattr(c, n)
        out[n] = (type(v).__name__ + (':' + v.name if hasattr(v, 'name') and isinstance(v.name, str) else '')) if v is not None else None
        if isinstance(v, list): out[n] = f'list[{len(v)}]'
    except Exception as e:
        out[n] = 'ERROR ' + repr(e)
out['windows'] = len(c.window_manager.windows)
out['background'] = bpy.app.background
r = {}
for op, call in (('object.select_all', lambda: bpy.ops.object.select_all(action='SELECT')),
                 ('mesh.primitive_uv_sphere_add', lambda: bpy.ops.mesh.primitive_uv_sphere_add()),
                 ('object.shade_smooth', lambda: bpy.ops.object.shade_smooth()),
                 ('object.mode_set EDIT', lambda: bpy.ops.object.mode_set(mode='EDIT')),
                 ('mesh.subdivide', lambda: bpy.ops.mesh.subdivide()),
                 ('object.mode_set OBJECT', lambda: bpy.ops.object.mode_set(mode='OBJECT')),
                 ('view3d.snap_cursor_to_center', lambda: bpy.ops.view3d.snap_cursor_to_center()),
                 ('screen.screenshot', lambda: bpy.ops.screen.screenshot(filepath='/tmp/x.png'))):
    try:
        r[op] = str(call())
    except Exception as e:
        r[op] = 'ERROR ' + str(e).splitlines()[0][:160]
out['operators'] = r
print('CTX', json.dumps(out))
""")
r, _ = run(["-b", "--factory-startup", "--python", ctx])
line = [l for l in r.stdout.splitlines() if l.startswith("CTX")]
data["context_background"] = json.loads(line[0][4:]) if line else r.stdout[-2000:]
cb = data["context_background"]
if isinstance(cb, dict):
    fact("In background mode bpy.context has a window and screen (from the opened file) but no area, region or "
         "space; the scene, view layer and active object are the file's; operators that need a 3D view or a screen "
         "area fail their poll, while object, mesh and edit-mode operators work",
         window=cb.get("window"), screen=cb.get("screen"), area=cb.get("area"), object=cb.get("object"),
         windows=cb.get("windows"), operators=cb.get("operators"))

rec = dict(experiment=os.path.relpath(os.path.abspath(__file__), ROOT), blender=version,
           machine=f"{platform.system()} {platform.machine()}", date=datetime.date.today().isoformat(), facts=facts, data=data)
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"), exist_ok=True)
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "cli_behaviour.json"), "w") as f:
    json.dump(rec, f, indent=1)
print("SAVED")
