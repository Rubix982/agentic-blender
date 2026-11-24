"""C-007, step 1: read the photograph with the rule in common.py, before anything is built.

    python3 skills/blender/scripts/run.py shots/jali-match/read_photo.py
Writes shots/jali-match/out/classes.png (surround black, openings white, stone orange) to check the rule by eye, and
out/photo.json (also results/read_photo.json, with the first rule's openings beside the rule's and the colour of the
dark pixels in the carved field): the screen's extent in pixels, the openings' share of it, and the stone's luminance (10th, 50th and
90th percentiles, and by ten horizontal bands from top to bottom)."""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common as C  # noqa: E402

OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)


NORMALS_NPY = os.path.join(HERE, "out", "normals.npy")


def field():
    """The carved field's box, as read_photo.py found it (C-014), or None before it has run."""
    path = os.path.join(HERE, "results", "read_photo.json")
    if not os.path.exists(path):
        return None
    d = json.load(open(path))
    return dict(field=d["field_box"], box=d["screen_box_for_field"]) if "field_box" in d else None


def photo_normals():
    """Marigold's normals for the photo (normals.py), if they have been made: common.classify's veto uses them."""
    return np.load(NORMALS_NPY) if os.path.exists(NORMALS_NPY) else None


def stats(rgb, normals=None, field=None):
    k = C.classify(rgb, normals)
    if field is not None:                                               # C-014: the frame has no openings
        C.keep_field(k, field["field"], field["box"])
    rows = np.nonzero(k["stone"].mean(axis=1) > 0.2)[0]
    cols = np.nonzero(k["stone"].mean(axis=0) > 0.2)[0]
    y0, y1, x0, x1 = int(rows[0]), int(rows[-1]), int(cols[0]), int(cols[-1])
    box = (slice(y0, y1 + 1), slice(x0, x1 + 1))
    s = k["y"][box][k["stone"][box]]
    bands = [float(np.median(k["y"][y0 + i * (y1 - y0) // 10: y0 + (i + 1) * (y1 - y0) // 10, x0:x1][
        k["stone"][y0 + i * (y1 - y0) // 10: y0 + (i + 1) * (y1 - y0) // 10, x0:x1]])) for i in range(10)]
    return k, dict(box=[x0, y0, x1, y1], width_px=x1 - x0 + 1, height_px=y1 - y0 + 1,
                   opening_share=round(float(k["opening"][box].mean()), 4),
                   outside_share=round(float(k["outside"][box].mean()), 4),
                   stone_y=[round(float(np.percentile(s, q)), 4) for q in (10, 50, 90)],
                   stone_y_p99=round(float(np.percentile(s, 99)), 4),
                   stone_rgb_median=[round(float(c), 4) for c in np.median(rgb[box][k["stone"][box]], axis=0)],
                   opening_y=round(float(np.median(k["y"][box][k["opening"][box]])), 4),
                   stone_y_bands=[round(b, 4) for b in bands])


if __name__ == "__main__":
    rgb = C.load(os.path.join(HERE, "photo", "agra-jali.jpg"), C.size())
    NM = photo_normals()
    k0, st0 = stats(rgb, NM)
    FIELD = dict(field=C.field_box(k0["opening"], st0["box"]), box=st0["box"])   # C-014: the carved field
    k, st = stats(rgb, NM, FIELD)
    st["field_box"] = FIELD["field"]
    st["screen_box_for_field"] = FIELD["box"]
    st["frame_openings_removed_px"] = int(k["frame_openings"].sum())
    img = np.zeros(rgb.shape, np.float32)
    img[k["opening"]] = 1.0
    img[k["stone"]] = (0.85, 0.45, 0.2)
    C.write_png(os.path.join(OUT, "classes.png"), img)
    lines = C.cut_lines(k)
    ov = rgb.copy()
    ov[lines] = (0.1, 0.9, 1.0)
    C.write_png(os.path.join(OUT, "lines.png"), ov)                   # the cut lines over the photo, to check by eye
    st.update(size=list(C.size()), rule=dict(dark=C.DARK, green_red=C.GREEN_RED, wall_dist=C.WALL_DIST, wall_tex=C.WALL_TEX,
                                              wall_green_red_min=C.WALL_GR_MIN, lit=C.LIT, lit_abs=C.LIT_ABS, dim=C.DIM, dim_abs=C.DIM_ABS))
    # The first rule, kept as a measurement: openings where saturation is below 0.22 and luminance at least 0.30.
    x0, y0, x1, y1 = st["box"]
    mid = (y0 + y1) // 2
    mx, mn = rgb.max(axis=2), rgb.min(axis=2)
    sat_rule = ~k["outside"] & ((mx - mn) / np.maximum(mx, 1e-6) < 0.22) & (k["y"] >= 0.30)
    halves = dict(top=(slice(y0, mid), slice(x0, x1 + 1)), bottom=(slice(mid, y1 + 1), slice(x0, x1 + 1)))
    st["cut_lines"] = dict(share_of_box=round(float(lines[y0:y1 + 1, x0:x1 + 1].mean()), 4),
                           rule=dict(darker_by=C.LINE_T, thin=C.LINE_THIN, neighbours=C.LINE_NEIGHBOURS, run=C.LINE_RUN))
    st["rules_compared"] = {
        "saturation below 0.22, luminance at least 0.30": {h: round(float(sat_rule[b].mean()), 4) for h, b in halves.items()},
        "green over red above 0.86": {h: round(float((~k["outside"] & (k["gr"] > C.GREEN_RED))[b].mean()), 4)
                                      for h, b in halves.items()},
        "either that or near the wall's local colour (C-008)": {h: round(float((k["opening"] | k["lit"] | k["dim"])[b].mean()), 4)
                                                                 for h, b in halves.items()},
        "the same, less what is brighter than the wall (C-009)": {h: round(float((k["opening"] | k["dim"])[b].mean()), 4)
                                                                  for h, b in halves.items()},
        "the same, less what is darker than the wall too (C-011)": {h: round(float(k["opening"][b].mean()), 4)
                                                                    for h, b in halves.items()}}
    st["rules_compared"]["saturation below 0.22, luminance at least 0.30"]["whole"] = round(
        float(sat_rule[y0:y1 + 1, x0:x1 + 1].mean()), 4)
    # C-009: the pixels the cut was sure were wall, by their luminance over the local wall's; and what the lit test takes.
    box = (slice(y0, y1 + 1), slice(x0, x1 + 1))
    ratio = (k["y"] / np.maximum(k["wall_y"], 1e-3))[box][k["sure"][box]]
    st["lit_stone"] = dict(rule=dict(brighter_than_wall_by=C.LIT, plus=C.LIT_ABS),
                           sure_over_wall_p10_p25_p50_p75_p90=[round(float(np.percentile(ratio, q)), 3)
                                                               for q in (10, 25, 50, 75, 90)],
                           share_of_box=round(float(k["lit"][box].mean()), 4),
                           share_of_c008_openings=round(float(k["lit"][box].sum() / (k["opening"] | k["lit"] | k["dim"])[box].sum()), 4),
                           share_of_c008_openings_by_half={h: round(float(k["lit"][b].sum() / (k["opening"] | k["lit"] | k["dim"])[b].sum()), 4)
                                                           for h, b in halves.items()})
    # C-011: what the dim test takes, of what C-009's rule called opening, by thirds of the box's height.
    was = k["opening"] | k["dim"]
    thirds = np.array_split(np.arange(y0, y1 + 1), 3)
    st["dim_stone"] = dict(rule=dict(darker_than_wall_by=C.DIM, less=C.DIM_ABS),
                           share_of_box=round(float(k["dim"][box].mean()), 4),
                           share_of_c009_openings=round(float(k["dim"][box].sum() / was[box].sum()), 4),
                           share_of_c009_openings_by_third=[round(float(k["dim"][t[0]:t[-1] + 1, x0:x1 + 1].sum()
                                                                        / max(was[t[0]:t[-1] + 1, x0:x1 + 1].sum(), 1)), 4)
                                                            for t in thirds])
    # C-012: what the normals' veto takes (none if the normals are not made yet).
    st["veto_stone"] = dict(rule=dict(area_below_px=C.VETO_AREA, lean_above_deg=C.VETO_DEG), normals=NM is not None,
                            share_of_box=round(float(k["veto"][box].mean()), 4),
                            share_of_openings_before=round(float(k["veto"][box].sum() / max((k["opening"] | k["veto"])[box].sum(), 1)), 4))
    # Dark pixels inside the screen: is their colour the stone's or the wall's?
    inner = (slice(y0 + 110, y1 - 95), slice(x0 + 130, x1 - 110))     # the carved field, inside the frame
    d = k["outside"][inner]
    st["dark_in_field"] = dict(share=round(float(d.mean()), 4),
                               green_red_p50_p90=[round(float(np.percentile(k["gr"][inner][d], q)), 4) for q in (50, 90)])
    with open(os.path.join(OUT, "photo.json"), "w") as f:
        json.dump(st, f, indent=1)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    with open(os.path.join(HERE, "results", "read_photo.json"), "w") as f:
        json.dump(st, f, indent=1)
    print("PHOTO", json.dumps(st), flush=True)
