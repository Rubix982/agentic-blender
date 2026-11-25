"""C-007, step 3: the render against the photograph, by the one rule in common.py, and the sheet for the user.

    python3 skills/blender/scripts/run.py shots/jali-match/compare.py
Reads photo/agra-jali.jpg (at half size) and out/render.png. Measures, inside the photo's screen box:
  openings_iou     pixels that are opening in both, over pixels that are opening in either
  stone_iou        the same for stone
  stone_y          the stone's luminance, 10th / 50th / 90th percentiles (the 50th was fitted by the lights)
  stone_spread     90th minus 10th percentile: the stone's contrast, which nothing was fitted to
  stone_y_bands    the stone's median luminance in ten bands from top to bottom
  detail           (C-011) the carving's light and dark against the photo's, in a fine and a forms band
  light_map        (C-012) where the light pools: the stone's median in 6 x 7 cells, render against photo
Writes shots/jali-match/sheet.jpg (the two side by side, and the same detail of each at full size) and
results/compare.json."""
import json
import os
import sys

import blf
import imbuf
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common as C  # noqa: E402
import shot  # noqa: E402  (C-022: which photo, and where the outputs go)
from read_photo import stats  # noqa: E402

W, H = C.size()
photo = C.load(shot.PHOTO, (W, H))
render = C.load(os.path.join(shot.OUT, "render.png"), (W, H))
from read_photo import photo_normals, field  # noqa: E402
FIELD = field()                                                        # C-014: no openings in the frame, either image
kp, sp = stats(photo, photo_normals(), FIELD)                          # the photo's rule with the normals' veto (C-012)
# C-018: the render shares the photo's geometry and camera, so the normals' veto (C-012) applies to its rule too:
# once its lit faces were desaturated like the photo's, the colour rule took some of them for wall, as it had the
# photo's before the veto.
kr, sr = stats(render, photo_normals(), FIELD)
x0, y0, x1, y1 = sp["box"]
box = (slice(y0, y1 + 1), slice(x0, x1 + 1))


def iou(a, b):
    a, b = a[box], b[box]
    return round(float((a & b).sum() / max((a | b).sum(), 1)), 4)


res = dict(openings_iou=iou(kp["opening"], kr["opening"]), stone_iou=iou(kp["stone"], kr["stone"]),
           photo=dict(stone_y=sp["stone_y"], stone_y_p99=sp["stone_y_p99"], stone_rgb_median=sp["stone_rgb_median"],
                      stone_spread=round(sp["stone_y"][2] - sp["stone_y"][0], 4),
                      opening_y=sp["opening_y"], opening_share=sp["opening_share"], stone_y_bands=sp["stone_y_bands"]),
           render=dict(stone_y=sr["stone_y"], stone_y_p99=sr["stone_y_p99"], stone_rgb_median=sr["stone_rgb_median"],
                       stone_spread=round(sr["stone_y"][2] - sr["stone_y"][0], 4),
                       opening_y=sr["opening_y"], opening_share=sr["opening_share"], stone_y_bands=sr["stone_y_bands"]))
res["spread_ratio"] = round(res["render"]["stone_spread"] / res["photo"]["stone_spread"], 4)
# C-008's measures. Lines: each image's cut lines found within 2 px of the other's, inside the screen's box.
lp, lr = C.cut_lines(kp)[box], C.cut_lines(kr)[box]
res["lines"] = dict(photo_share=round(float(lp.mean()), 4), render_share=round(float(lr.mean()), 4),
                    render_near_photo=round(float((lr & C.dilate(lp, 2)).sum() / max(lr.sum(), 1)), 4),
                    photo_near_render=round(float((lp & C.dilate(lr, 2)).sum() / max(lp.sum(), 1)), 4))
# The photo's thin stone (strips about 4 px wide or less): how much of it the render shows as stone, not opening.
stone_ph = ~kp["opening"] & ~kp["outside"]
thin = (stone_ph & ~C.dilate(C.erode(stone_ph, 2), 2))[box]
res["thin_stone_shown"] = round(float((thin & ~kr["opening"][box]).sum() / max(thin.sum(), 1)), 4)
# Edge softness: the luminance gradient's mean on each image's own opening edges (a pixel either side of the mask's
# boundary). The photo's edges are soft over about two pixels (lens and phone processing); a crisper render reads rough.
def edge_gradient(kk):
    yy = kk["y"]
    g = np.hypot(np.gradient(yy, axis=0), np.gradient(yy, axis=1))
    e = (C.dilate(kk["opening"], 1) & ~C.erode(kk["opening"], 1))[box]
    return float(g[box][e].mean())
res["edge_gradient"] = dict(photo=round(edge_gradient(kp), 4), render=round(edge_gradient(kr), 4))
res["edge_gradient"]["render_over_photo"] = round(res["edge_gradient"]["render"] / res["edge_gradient"]["photo"], 3)
# C-011: the carving's detail. On stone in both images, at least 3 px from any opening (so the openings' edges do not
# count), each image's luminance split into two bands: fine (minus its own blur over 5 px) and forms (blur over 5 px
# minus blur over 21 px). For each band, the correlation between photo and render (1 when every light and dark falls
# where the photo's does) and the render's amplitude over the photo's (its standard deviation, render over photo).
def bands(yy):
    b5, b21 = C.blur(yy, 5), C.blur(yy, 21)
    return dict(fine=yy - b5, forms=b5 - b21)
both = (C.erode(kp["stone"], 3) & C.erode(kr["stone"], 3))[box]
bp, br = bands(kp["y"]), bands(kr["y"])
res["detail"] = {}
for name in ("fine", "forms"):
    a, b = bp[name][box][both], br[name][box][both]
    res["detail"][name] = dict(correlation=round(float(np.corrcoef(a, b)[0, 1]), 4),
                               amplitude_ratio=round(float(b.std() / max(a.std(), 1e-9)), 4))
res["detail"]["pixels"] = int(both.sum())
# What the measure gives the photo against itself shifted diagonally by 1 and 2 px: a render that lands a pixel or two
# off the photo cannot score more, so these are its ceilings.
res["detail"]["photo_vs_itself_shifted"] = {}
for dpx in (1, 2):
    ys = np.roll(np.roll(kp["y"], dpx, 0), dpx, 1)
    ks = np.roll(np.roll(kp["stone"], dpx, 0), dpx, 1)
    sb = (C.erode(kp["stone"], 3) & C.erode(ks, 3))[box]
    bs = bands(ys)
    res["detail"]["photo_vs_itself_shifted"][f"{dpx}px"] = {
        n: round(float(np.corrcoef(bp[n][box][sb], bs[n][box][sb])[0, 1]), 4) for n in ("fine", "forms")}
# C-011, the user's second look: the frame's weathering. On stone in both images in the frame (the screen's box less
# the carved field, as read_photo.py's dark_in_field draws it), each band's standard deviation, render over photo.
inner = np.zeros(kp["y"].shape, bool)
inner[y0 + 110:y1 - 95, x0 + 130:x1 - 110] = True
fr = (C.erode(kp["stone"], 3) & C.erode(kr["stone"], 3) & ~inner)[box]
res["frame_texture"] = {name: dict(photo=round(float(bp[name][box][fr].std()), 4), render=round(float(br[name][box][fr].std()), 4),
                                   ratio=round(float(br[name][box][fr].std() / max(bp[name][box][fr].std(), 1e-9)), 4))
                        for name in ("fine", "forms")}
# C-012: the light map. The stone's median luminance (on stone in both, 3 px from any opening) in 6 x 7 cells over the
# screen's box, each over its image's median cell: where the light pools. Its error is the RMS of log(render / photo)
# over the cells.
def light_map(yy, mask, gx=6, gy=7):
    xs = np.linspace(x0, x1 + 1, gx + 1).astype(int)
    ys = np.linspace(y0, y1 + 1, gy + 1).astype(int)
    out = np.full((gy, gx), np.nan)
    for j in range(gy):
        for i in range(gx):
            mm = mask[ys[j]:ys[j + 1], xs[i]:xs[i + 1]]
            if mm.sum() > 50:
                out[j, i] = np.median(yy[ys[j]:ys[j + 1], xs[i]:xs[i + 1]][mm])
    return out / np.nanmedian(out)
lm_mask = C.erode(kp["stone"], 3) & C.erode(kr["stone"], 3)
lmp, lmr = light_map(kp["y"], lm_mask), light_map(kr["y"], lm_mask)
res["light_map"] = dict(photo=[[round(float(v), 3) for v in row] for row in lmp],
                        render=[[round(float(v), 3) for v in row] for row in lmr],
                        log_rms=round(float(np.sqrt(np.nanmean(np.log(lmr / lmp) ** 2))), 4))
# C-018: the frame's crispness. On the frame's top band (inside the box, the top 34 to 72 rows of the image, x 200 to
# 1000), each image's fine band (less its blur over 1 sigma) over its forms band (1 to 3.5 sigma): the photo's fine
# grain and small sharp specks against soft blobs (the user's "bluriness": Marigold's albedo blobs, C-018).
def crisp(yy):
    f = yy - C.blur(yy, 5)
    m = C.blur(yy, 5) - C.blur(yy, 21)
    band_ = (slice(34, 72), slice(200, 1000))
    return round(float(f[band_].std() / max(m[band_].std(), 1e-9)), 4)
res["frame_crispness"] = dict(photo=crisp(kp["y"].astype(np.float32)), render=crisp(kr["y"].astype(np.float32)))
# C-019: grime in the hollows, and the openings' edges. Recesses from heights integrated from the photo's normals
# (screened at 30 px, as the build does), each pixel's height below its masked mean over 11 and 21 px; on stone in both
# 6 px from any opening, inside the carved field: the median log(render / photo) on the deepest 3 % of the recesses
# against the stone's median. And the same on the stone's band 1 to 4 px from an opening against 6 px or more inside.
NMc = photo_normals()
if NMc is not None and FIELD is not None:
    skin_c = C.erode(kp["stone"], 2)
    hgt, _ = C.heights_from_normals(NMc, skin_c, screen_px=30)
    stc = skin_c.astype(np.float32)
    fx0, fy0, fx1, fy1 = FIELD["field"]
    infield = np.zeros_like(skin_c); infield[fy0:fy1 + 1, fx0:fx1 + 1] = True
    deep_m = infield & C.erode(kp["stone"], 6) & C.erode(kr["stone"], 6)
    lr_all = np.log(np.maximum(kr["y"], 1e-3) / np.maximum(kp["y"], 1e-3))
    res["recesses"] = {}
    for w_ in ((11, 21) if deep_m.any() else ()):                    # C-022: none when no stone is 6 px from an opening in both
        rec = np.clip(C.blur(hgt * stc, w_) / np.maximum(C.blur(stc, w_), 1e-3) - hgt, 0, None)
        q97 = np.percentile(rec[deep_m], 97)
        res["recesses"][f"window_{w_}px"] = dict(
            deepest_3pct=round(float(np.median(lr_all[deep_m & (rec >= q97)])), 4),
            all_stone=round(float(np.median(lr_all[deep_m])), 4))
    edge_band = infield & kp["stone"] & kr["stone"] & ~C.erode(kp["stone"], 4) & C.erode(kp["stone"], 1)
    res["opening_edges"] = dict(edge_band=round(float(np.median(lr_all[edge_band])), 4),
                                inside=round(float(np.median(lr_all[deep_m])), 4)) if edge_band.any() and deep_m.any() else None
# C-015: the stone's colour variation (the photo's stains, grime and darker frame, against an even albedo): on stone in
# both (3 px from any opening), each image blurred over 5 px, the chromaticity log(R / G) and log(B / G); their spread
# (the two standard deviations combined), render over photo; and the frame's median luminance over the field's.
def chroma(img, mask):
    b = np.stack([C.blur(img[:, :, c].astype(np.float32), 5) for c in range(3)], -1)
    a = np.log(np.maximum(b[:, :, 0], 1e-3) / np.maximum(b[:, :, 1], 1e-3))[mask]
    bb = np.log(np.maximum(b[:, :, 2], 1e-3) / np.maximum(b[:, :, 1], 1e-3))[mask]
    return float(np.sqrt(a.var() + bb.var()))
cm = C.erode(kp["stone"], 3) & C.erode(kr["stone"], 3)
cm_box = np.zeros_like(cm); cm_box[box] = cm[box]
fld = np.zeros_like(cm); fld[y0 + 110:y1 - 95, x0 + 130:x1 - 110] = True
res["stone_colour"] = dict(photo_spread=round(chroma(photo, cm_box), 4), render_spread=round(chroma(render, cm_box), 4))
res["stone_colour"]["ratio"] = round(res["stone_colour"]["render_spread"] / max(res["stone_colour"]["photo_spread"], 1e-9), 4)
# C-017: colour against brightness. On the same stone, each blurred over 5 px: log(R/G) and log(B/G) regressed on
# log(luminance); the slopes, and the share of each one's variance a straight line explains. In the photo the lit
# faces are paler and the shadows redder.
def colour_slopes(img, mask):
    b = np.stack([C.blur(img[:, :, c].astype(np.float32), 5) for c in range(3)], -1)
    ly = np.log(np.maximum(b @ np.array([0.2126, 0.7152, 0.0722], np.float32), 1e-3))[mask]
    out = {}
    for name, (i, j) in (("r_over_g", (0, 1)), ("b_over_g", (2, 1))):
        c = np.log(np.maximum(b[:, :, i], 1e-3) / np.maximum(b[:, :, j], 1e-3))[mask]
        k, c0 = np.polyfit(ly, c, 1)
        out[name] = dict(slope=round(float(k), 4), explained=round(float(1 - (c - (k * ly + c0)).var() / c.var()), 4))
    return out
res["colour_vs_brightness"] = dict(photo=colour_slopes(photo, cm_box), render=colour_slopes(render, cm_box))
res["frame_over_field"] = dict(photo=round(float(np.median(kp["y"][cm_box & ~fld]) / np.median(kp["y"][cm_box & fld])), 4),
                               render=round(float(np.median(kr["y"][cm_box & ~fld]) / np.median(kr["y"][cm_box & fld])), 4))
# C-016: SSIM (a standard structural similarity of luminance, an 11 px Gaussian window), over the screen's box and over
# the detail patch. It followed the judge's verdicts best of every measure over C-007 to C-015 (measure_history.py).
def ssim_map(a, b):
    c1, c2 = 0.01 ** 2, 0.03 ** 2
    ma, mb = C.blur(a, 11), C.blur(b, 11)
    va, vb = C.blur(a * a, 11) - ma * ma, C.blur(b * b, 11) - mb * mb
    cov = C.blur(a * b, 11) - ma * mb
    return ((2 * ma * mb + c1) * (2 * cov + c2)) / ((ma * ma + mb * mb + c1) * (va + vb + c2))
yp_, yr_ = kp["y"].astype(np.float32), kr["y"].astype(np.float32)
smap = ssim_map(yp_, yr_)
shifted = np.roll(np.roll(yp_, 2, 0), 2, 1)
cmap_ = ssim_map(yp_, shifted)
DXp, DYp, DWp, DHp = 520, 330, 560, 420
if not shot.DEFAULT:                                                   # C-022: another photo: centred on its carved field
    _fb = FIELD["field"] if FIELD else sp["box"]
    DWp, DHp = min(DWp, W), min(DHp, H)
    DXp = int(min(max((_fb[0] + _fb[2]) // 2 - DWp // 2, 0), W - DWp))
    DYp = int(min(max((_fb[1] + _fb[3]) // 2 - DHp // 2, 0), H - DHp))
res["ssim"] = dict(box=round(float(smap[box].mean()), 4), patch=round(float(smap[DYp:DYp + DHp, DXp:DXp + DWp].mean()), 4),
                   photo_vs_itself_2px=round(float(cmap_[box].mean()), 4))
# (Not a ceiling: the render scores above the photo against itself 2 px off, since SSIM weighs the photo's fine grain,
# which a shift destroys and the render never had.)
# C-013's guard: the openings' median luminance in the box's upper and lower halves, photo and render.
mid = (y0 + y1) // 2
res["openings_y_by_half"] = {h: dict(photo=round(float(np.median(kp["y"][rows, x0:x1 + 1][kp["opening"][rows, x0:x1 + 1]])), 4),
                                     render=round(float(np.median(kr["y"][rows, x0:x1 + 1][kr["opening"][rows, x0:x1 + 1]])), 4))
                             for h, rows in (("upper", slice(y0, mid)), ("lower", slice(mid, y1 + 1)))}
p90p, p90r = sp["stone_y"][2], sr["stone_y"][2]
# C-016: the standard. The measures that followed the judge's verdicts over C-007 to C-015 (Spearman with the ladder,
# measure_history.py and the full-size openings history), each with its bar; and the guards, which did not follow the
# verdicts but catch a break. Bars are this asset's accepted state (C-015) or the bars the cards set.
def _within(v, lo, hi):
    return bool(lo <= v <= hi)
# follows_judge: Spearman with the verdicts on the detail patch and on the whole screen (measure_history.py); the
# openings' IoU from the full-size comparisons (the sheets are JPEGs at half size, where the rule's openings drift).
# Core: at least 0.8 in both views. Secondary: in one view only.
card = {
    "ssim": dict(value=res["ssim"]["box"], bar=">= 0.50", ok=res["ssim"]["box"] >= 0.50,
                 follows_judge=dict(patch=0.898, whole=0.922), tier="core"),
    "openings_iou": dict(value=res["openings_iou"], bar=">= 0.75", ok=res["openings_iou"] >= 0.75,
                         follows_judge=dict(full_size=0.922), tier="core"),
    "bright_end": dict(value=round(p90r / p90p, 4), bar="0.85 to 1.15", ok=_within(p90r / p90p, 0.85, 1.15),
                       follows_judge=dict(patch=0.874, whole=0.838), tier="core"),
    "lines_render_near_photo": dict(value=res["lines"]["render_near_photo"], bar=">= 0.60",
                                    ok=res["lines"]["render_near_photo"] >= 0.60,
                                    follows_judge=dict(patch=0.886, whole=0.826), tier="core"),
    "forms_correlation": dict(value=res["detail"]["forms"]["correlation"], bar=">= 0.50",
                              ok=res["detail"]["forms"]["correlation"] >= 0.50,
                              follows_judge=dict(patch=0.731, whole=0.898), tier="secondary"),
    "colour_spread": dict(value=res["stone_colour"]["ratio"], bar=">= 0.45 (provisional, T-019)",
                          ok=res["stone_colour"]["ratio"] >= 0.45, follows_judge=dict(patch=0.527, whole=0.922),
                          tier="secondary"),
}
guards = {
    "contrast": dict(value=res["spread_ratio"], bar="0.8 to 1.2", ok=_within(res["spread_ratio"], 0.8, 1.2)),
    "forms_amplitude": dict(value=res["detail"]["forms"]["amplitude_ratio"], bar="0.8 to 1.2",
                            ok=_within(res["detail"]["forms"]["amplitude_ratio"], 0.8, 1.2)),
    "thin_stone_shown": dict(value=res["thin_stone_shown"], bar=">= 0.90", ok=res["thin_stone_shown"] >= 0.90),
    "openings_y_upper": dict(value=round(abs(res["openings_y_by_half"]["upper"]["render"] - res["openings_y_by_half"]["upper"]["photo"]), 4),
                             bar="<= 0.02 off", ok=abs(res["openings_y_by_half"]["upper"]["render"] - res["openings_y_by_half"]["upper"]["photo"]) <= 0.02),
    "openings_y_lower": dict(value=round(abs(res["openings_y_by_half"]["lower"]["render"] - res["openings_y_by_half"]["lower"]["photo"]), 4),
                             bar="<= 0.02 off", ok=abs(res["openings_y_by_half"]["lower"]["render"] - res["openings_y_by_half"]["lower"]["photo"]) <= 0.02),
    "light_map": dict(value=res["light_map"]["log_rms"], bar="<= 0.20", ok=res["light_map"]["log_rms"] <= 0.20),
    "frame_texture_forms": dict(value=res["frame_texture"]["forms"]["ratio"], bar="0.8 to 1.2",
                                ok=_within(res["frame_texture"]["forms"]["ratio"], 0.8, 1.2)),
}
res["scorecard"] = dict(measures=card, guards=guards, all_met=all(v["ok"] for v in card.values()),
                        guards_held=all(v["ok"] for v in guards.values()))
res["bar"] = dict(lines_near_at_least=0.6, stone_p90_within=[round(0.85 * p90p, 4), round(1.15 * p90p, 4)],
                  spread_ratio_within=[0.8, 1.2], openings_iou_at_least=0.68)
res["measures_pass"] = dict(
    lines=res["lines"]["render_near_photo"] >= 0.6 and res["lines"]["photo_near_render"] >= 0.6,
    light=0.85 * p90p <= p90r <= 1.15 * p90p and 0.8 <= res["spread_ratio"] <= 1.2,
    openings_guard=res["openings_iou"] >= 0.68)
# Where the photo sees the wall, what the render shows there, and the IoU by thirds of the screen's height.
po, ro = kp["opening"][box], kr["opening"][box]
res["photo_openings_in_render"] = dict(opening=round(float((po & ro).sum() / po.sum()), 4),
                                       stone=round(float((po & kr["stone"][box]).sum() / po.sum()), 4),
                                       dark=round(float((po & kr["outside"][box]).sum() / po.sum()), 4))
res["render_openings_on_photo_stone"] = round(float((ro & kp["stone"][box]).sum() / max(ro.sum(), 1)), 4)
thirds = np.array_split(np.arange(y0, y1 + 1), 3)
res["openings_iou_by_third"] = [round(float((kp["opening"][t[0]:t[-1] + 1, x0:x1 + 1] & kr["opening"][t[0]:t[-1] + 1, x0:x1 + 1]).sum()
                                      / max((kp["opening"][t[0]:t[-1] + 1, x0:x1 + 1] | kr["opening"][t[0]:t[-1] + 1, x0:x1 + 1]).sum(), 1)), 4)
                                for t in thirds]
print("COMPARE", json.dumps(res), flush=True)

# The sheet: both whole, then one detail of each at full size, with the openings that disagree marked.
half = (W // 2, H // 2)
a = C.load(shot.PHOTO, half)
b = C.load(os.path.join(shot.OUT, "render.png"), half)
DX, DY, DW, DH = DXp, DYp, DWp, DHp                                    # a detail: ours, two rows of cells and their rosettes
LAB = 30
top = np.concatenate([a, b], axis=1)
det = np.concatenate([photo[DY:DY + DH, DX:DX + DW], render[DY:DY + DH, DX:DX + DW]], axis=1)
miss = np.zeros((H, W, 3), np.float32)
miss[kp["opening"] & ~kr["opening"]] = (1.0, 0.2, 0.2)                 # open in the photo only: red
miss[kr["opening"] & ~kp["opening"]] = (0.2, 0.6, 1.0)                 # open in the render only: blue
diffw = C.load_array_resized(miss, half)
cols = max(top.shape[1], det.shape[1], diffw.shape[1])


def pad(x):
    return np.pad(x, ((0, 0), (0, cols - x.shape[1]), (0, 0)), constant_values=0.08)


band = np.full((LAB, cols, 3), 0.08, np.float32)
sheet = np.concatenate([band, pad(top), band, pad(det), band, pad(diffw)], axis=0)
path = shot.SHEET
C.write_png(path, sheet)
ib = imbuf.load(path)
fid = blf.load("/System/Library/Fonts/Supplemental/Arial.ttf") if os.path.exists(
    "/System/Library/Fonts/Supplemental/Arial.ttf") else 0
labels = [(0, shot.CREDIT), (half[0], "render"),
          (0, None), (0, "detail, photograph"), (DW, "detail, render"),
          (0, f"openings that disagree: red = open only in the photo, blue = open only in the render "
              f"(IoU {res['openings_iou']})")]
ys = [0, 0, None, LAB + top.shape[0], LAB + top.shape[0], 2 * LAB + top.shape[0] + det.shape[0]]
with blf.bind_imbuf(fid, ib):
    blf.size(fid, 20)
    blf.color(fid, 0.95, 0.95, 0.95, 1.0)
    for (x, text), y in zip(labels, ys):
        if text:
            blf.position(fid, x + 8, ib.size[1] - (y + 22), 0)
            blf.draw_buffer(fid, text)
imbuf.write(ib, filepath=path)
os.makedirs(shot.RESULTS, exist_ok=True)
with open(os.path.join(shot.RESULTS, "compare.json"), "w") as f:
    json.dump(res, f, indent=1)
print("SHEET", path, sheet.shape, flush=True)
