#!/usr/bin/env python3
"""Run a Python script inside Blender, headless, the same way every time.

  python3 tools/run.py SCRIPT.py [--blend FILE.blend] [--keep-prefs] [--timeout S] [-- ARGS...]

Blender runs in the background (-b) with factory settings (--factory-startup, so no user add-ons or preferences leak in),
exits with code 1 if the script raises (--python-exit-code 1; without it a failed script exits 0), and prints each line
as it is printed (stdout line-buffered inside Blender). ARGS reach the script after '--' in sys.argv.
Which Blender: $BLENDER, else ~/Applications/Blender.app, /Applications/Blender.app, or `blender` on PATH.
`python3 tools/run.py --which` prints the binary and its version.
"""
import os
import shutil
import subprocess
import sys
import time

CANDIDATES = [os.environ.get("BLENDER"), "~/Applications/Blender.app/Contents/MacOS/Blender",
              "/Applications/Blender.app/Contents/MacOS/Blender", shutil.which("blender")]


def blender():
    for c in CANDIDATES:
        if c and os.path.exists(os.path.expanduser(c)):
            return os.path.expanduser(c)
    sys.exit("Blender not found: set $BLENDER to the Blender binary")


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(2)
    if argv[0] == "--which":
        b = blender()
        print(b)
        print(subprocess.run([b, "--version"], capture_output=True, text=True).stdout.splitlines()[0])
        return
    rest = []
    if "--" in argv:
        i = argv.index("--")
        argv, rest = argv[:i], argv[i + 1:]
    script, blend, factory, timeout = None, None, True, None
    while argv:
        a = argv.pop(0)
        if a == "--blend":
            blend = argv.pop(0)
        elif a == "--keep-prefs":
            factory = False
        elif a == "--timeout":
            timeout = float(argv.pop(0))
        else:
            script = a
    if not script:
        sys.exit("no script given")
    cmd = [blender(), "-b"] + ([blend] if blend else []) + (["--factory-startup"] if factory else [])
    # Blender's Python ignores PYTHON* environment variables (PYTHONUNBUFFERED included) unless --python-use-system-env
    # is given, so a plain print() is held until the script ends when read through a pipe. Line buffering is switched on
    # inside Blender instead (experiments/running/cli_behaviour.py).
    cmd += ["--python-exit-code", "1", "--python-expr", "import sys; sys.stdout.reconfigure(line_buffering=True)",
            "--python", script, "--"] + rest
    env = dict(os.environ)
    t = time.time()
    try:
        code = subprocess.run(cmd, env=env, timeout=timeout).returncode
    except subprocess.TimeoutExpired:
        print(f"[run.py] timed out after {timeout} s", file=sys.stderr)
        code = 124
    print(f"[run.py] exit {code} in {time.time() - t:.1f} s", file=sys.stderr)
    sys.exit(code)


if __name__ == "__main__":
    main()
