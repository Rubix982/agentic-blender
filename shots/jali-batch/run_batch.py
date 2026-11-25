"""C-022: make.py's chain on every shot folder in shots/, its method unchanged.

    python3 shots/jali-batch/run_batch.py [--workers N] [--only SLUG ...] [--force]
The learned steps (normals.py, then intrinsics.py, in the repo's .venv) run one shot at a time, since they share the
GPU; as each shot's are done, it joins a queue that N workers (default 2: the machine's limit is 4 Blender jobs, and
the learned steps use memory too) take through read_photo.py, build.py and compare.py in Blender. Each step runs with
JALI_SHOT=<the shot's folder> (shots/jali-match/shot.py), its log in <folder>/log/<step>.log. A step that fails stops
that shot, not the batch. A step already done (status.json says ok) is skipped unless --force. Writes status.json:
for each shot and step, ok or the exit code, the seconds, and the log's last lines when it failed."""
import json
import os
import queue
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CHAIN = os.path.join(ROOT, "shots", "jali-match")
RUN = os.path.join(ROOT, "skills", "blender", "scripts", "run.py")
VENV_PY = os.path.join(ROOT, ".venv", "bin", "python")
STATUS = os.path.join(HERE, "status.json")
argv = sys.argv[1:]
WORKERS = int(argv[argv.index("--workers") + 1]) if "--workers" in argv else 2
ONLY = argv[argv.index("--only") + 1:] if "--only" in argv else None
FORCE = "--force" in argv
LOCK = threading.Lock()
status = json.load(open(STATUS)) if os.path.exists(STATUS) else {}

STEPS_A = [("normals", [VENV_PY, os.path.join(CHAIN, "normals.py")]),
           ("intrinsics", [VENV_PY, os.path.join(CHAIN, "intrinsics.py")])]
STEPS_B = [(name, [sys.executable, RUN, os.path.join(CHAIN, f"{name}.py"), "--timeout", str(t)])
           for name, t in (("read_photo", 300), ("build", 1800), ("compare", 300))]


def save():
    with LOCK:
        with open(STATUS, "w") as f:
            json.dump(status, f, indent=1)


def step(slug, name, cmd):
    """Run one step for one shot; True when it succeeded (or was done already)."""
    st = status.setdefault(slug, {})
    if not FORCE and st.get(name, {}).get("ok"):
        return True
    folder = os.path.join(HERE, "shots", slug)
    os.makedirs(os.path.join(folder, "log"), exist_ok=True)
    log = os.path.join(folder, "log", f"{name}.log")
    t = time.time()
    with open(log, "w") as f:
        r = subprocess.run(cmd, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, env=dict(os.environ, JALI_SHOT=folder))
    tail = [ln.replace(ROOT + os.sep, "").replace(os.path.expanduser("~"), "~")   # no home folder in the record
            for ln in open(log, errors="ignore").read().strip().splitlines()[-6:]]
    st[name] = dict(ok=r.returncode == 0, exit=r.returncode, seconds=round(time.time() - t, 1),
                    **({} if r.returncode == 0 else dict(tail=tail)))
    save()
    print(f"{time.strftime('%H:%M:%S')} {slug} {name}: {'ok' if r.returncode == 0 else 'FAILED ' + str(r.returncode)} "
          f"({st[name]['seconds']} s)", flush=True)
    return r.returncode == 0


def worker(q):
    while True:
        slug = q.get()
        if slug is None:
            return
        try:
            for name, cmd in STEPS_B:
                if not step(slug, name, cmd):
                    break
        finally:
            q.task_done()


if __name__ == "__main__":
    slugs = sorted(d for d in os.listdir(os.path.join(HERE, "shots")) if os.path.isdir(os.path.join(HERE, "shots", d)))
    if ONLY:
        slugs = [s for s in slugs if s in ONLY]
    q = queue.Queue()
    threads = [threading.Thread(target=worker, args=(q,)) for _ in range(WORKERS)]
    for th in threads:
        th.start()
    for slug in slugs:
        if all(step(slug, name, cmd) for name, cmd in STEPS_A):
            q.put(slug)
    q.join()
    for _ in threads:
        q.put(None)
    for th in threads:
        th.join()
    done = sum(1 for s in slugs if status.get(s, {}).get("compare", {}).get("ok"))
    print(f"BATCH {done} of {len(slugs)} shots through compare", flush=True)
