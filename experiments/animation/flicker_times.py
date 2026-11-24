"""C-006's frame times, read back from the Blender log, because flicker.py's own mean per variant is not usable here.

The night run was on battery. Near empty, macOS slowed the machine about threefold (from super-res frame 92 on), and
at 1 % it slept from 02:18 to 08:00 inside 384-sample frame 109 (pmset log: 'Low Power Sleep ... Using Batt
(Charge:1%)', then 'Wake ... Using AC'). The images do not depend on time, so flicker and detail are unaffected; only
seconds per frame are. This takes every frame's 'Time:' line from the log, pairs it with the 'Saved:' line before it
(which names the variant's folder and the frame), and gives each variant the median of its frames, with the frames a
reader should not trust named.

    python3 experiments/animation/flicker_times.py LOG [--slow-from N --slow-to M]
--slow-from/--slow-to: the 1-based positions in the log's sequence of frames rendered on a throttled battery; they are
excluded from the medians and listed. Writes experiments/animation/results/flicker_times.json."""
import argparse
import json
import os
import re
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
SAVED = re.compile(r"^Saved: '.*/([^/]+)/(\d{4})\.exr'")
TIME = re.compile(r"^Time: (?:(\d+):)?(\d+):(\d+\.\d+)")

ap = argparse.ArgumentParser()
ap.add_argument("log")
ap.add_argument("--slow-from", type=int, default=0)
ap.add_argument("--slow-to", type=int, default=0)
a = ap.parse_args()

frames, last = [], None
for line in open(a.log, encoding="utf-8", errors="replace"):
    m = SAVED.match(line)
    if m:
        last = (m.group(1), int(m.group(2)))
        continue
    m = TIME.match(line)
    if m and last:
        h, mi, s = m.groups()
        frames.append(dict(n=len(frames) + 1, variant=last[0], frame=last[1],
                           seconds=round(int(h or 0) * 3600 + int(mi) * 60 + float(s), 2)))
        last = None

out = {}
for f in frames:
    v = out.setdefault(f["variant"], dict(frames=0, all_seconds=[], kept_seconds=[], excluded=[]))
    v["frames"] += 1
    v["all_seconds"].append(f["seconds"])
    if a.slow_from and a.slow_from <= f["n"] <= (a.slow_to or 10 ** 9):
        v["excluded"].append(dict(frame=f["frame"], seconds=f["seconds"], why="battery throttle or sleep"))
    else:
        v["kept_seconds"].append(f["seconds"])
for v in out.values():
    v["median_seconds"] = round(statistics.median(v["kept_seconds"]), 2) if v["kept_seconds"] else None
    v["mean_all_seconds"] = round(statistics.mean(v["all_seconds"]), 2)
    del v["all_seconds"]

rec = dict(experiment=os.path.relpath(os.path.abspath(__file__), os.path.join(HERE, "..", "..")),
           source="the Blender log of flicker.py's run (Time: and Saved: lines)",
           excluded_positions=[a.slow_from, a.slow_to], variants=out)
os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
with open(os.path.join(HERE, "results", "flicker_times.json"), "w") as f:
    json.dump(rec, f, indent=1)
for k, v in out.items():
    print(f"{k:34s} n={v['frames']:2d} kept={len(v['kept_seconds']):2d} median={v['median_seconds']} "
          f"mean_all={v['mean_all_seconds']}")
