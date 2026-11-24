"""C-006's bar, applied to the run's numbers, so the verdict can be checked rather than read from prose.

    python3 experiments/animation/flicker_verdict.py
Reads results/flicker.json (flicker, detail, difference from the baseline) and results/flicker_times.json (seconds per
frame from the log, battery-throttled frames excluded). "Excess" is a variant's mean flicker minus the floor's (1,024
samples). The three clauses, as the card wrote them before the run:
  a fix that works   at most 1.5x the baseline's time, at most half the baseline's excess, at least 90 % of the
                     floor's detail
  denoise_animation  per-frame if its frames differ from the baseline's by less than a tenth of the baseline's excess;
                     temporal if its flicker is at least a quarter below the baseline's
  C-005's figure     mostly motion if the floor's flicker is at least half the baseline's
Writes results/flicker_verdict.json, with each variant's change in flicker against the baseline's and its cut in
excess, both in per cent."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "results", "flicker.json")))["data"]["rows"]
T = json.load(open(os.path.join(HERE, "results", "flicker_times.json")))["variants"]
FLOOR = "1024 samples (floor)"

floor, base = R[FLOOR], R["baseline"]
base_s = T["baseline"]["median_seconds"]
base_excess = base["mean"] - floor["mean"]
rows = {}
for name, r in R.items():
    if name == "denoise_animation":
        s = T["raw with passes"]["median_seconds"] + r["operator_seconds"] / r["frames"]
    else:
        s = T[name]["median_seconds"]
    excess = r["mean"] - floor["mean"]
    rows[name] = dict(flicker=r["mean"], excess=round(excess, 5), seconds=s, time_ratio=round(s / base_s, 2),
                      excess_ratio=round(excess / base_excess, 2) if base_excess else None,
                      detail_ratio=round(r["detail"] / floor["detail"], 3), plants=r["plants"],
                      difference_from_baseline=r.get("difference_from_baseline"),
                      flicker_change_pct=round((r["mean"] / base["mean"] - 1) * 100, 2),
                      excess_cut_pct=round((1 - excess / base_excess) * 100, 1) if base_excess else None,
                      fix_that_works=(s <= 1.5 * base_s and excess <= 0.5 * base_excess
                                      and r["detail"] >= 0.9 * floor["detail"] and name not in ("baseline", FLOOR)))
da = R["denoise_animation"]
verdict = dict(
    floor_flicker=floor["mean"], baseline_flicker=base["mean"], baseline_excess=round(base_excess, 5),
    floor_over_baseline=round(floor["mean"] / base["mean"], 3),
    noise_share_of_baseline_pct=round(base_excess / base["mean"] * 100, 1),
    c005_mostly_motion=floor["mean"] >= 0.5 * base["mean"],
    fixes_that_work=[n for n, r in rows.items() if r["fix_that_works"]],
    denoise_animation=dict(difference_from_baseline=da["difference_from_baseline"],
                           tenth_of_baseline_excess=round(base_excess / 10, 6),
                           per_frame_by_the_card=da["difference_from_baseline"] < base_excess / 10,
                           flicker_change=round(da["mean"] / base["mean"] - 1, 4),
                           temporal_by_the_card=da["mean"] <= 0.75 * base["mean"]),
    rows=rows)
with open(os.path.join(HERE, "results", "flicker_verdict.json"), "w") as f:
    json.dump(verdict, f, indent=1)
print(json.dumps({k: v for k, v in verdict.items() if k != "rows"}, indent=1))
for n, r in rows.items():
    print(f"{n:32s} flicker {r['flicker']:.5f} excess {r['excess']:+.5f} ({r['excess_ratio']}x) "
          f"time {r['seconds']:.1f}s ({r['time_ratio']}x) detail {r['detail_ratio']} plants {r['plants']}")
