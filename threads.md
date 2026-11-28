# Threads

Open questions that surfaced while C-001 is open. One card at a time: these wait until C-001 closes.

### T-001 · Which free remote asset sources can a headless script pull from, and how?

**Status:** answered
**Parent:** C-001
**Opened:** 2026-11-23
**Question:** v1 knows only the assets bundled with Blender; it names no remote source. Candidates: Poly Haven and
ambientCG (CC0, no account), Megascans (reported free again in November 2026, needs an Epic account: the user's call).
**Answer:** C-002 (CARD.md): Poly Haven and ambientCG through `scripts/assets.py` and `scripts/asset_import.py`, 10 of
10 test assets right (`areas/remote-assets.md`). Megascans not used (account).

### T-002 · What do the most-used community extensions add, read in a throwaway profile?

**Status:** answered
**Parent:** C-001
**Opened:** 2026-11-23
**Question:** v1 inventoried the 14 bundled add-ons only; 4.5's `BLENDER_USER_RESOURCES` and `BLENDER_USER_EXTENSIONS`
(listed in `--help`) let extensions be installed and inventoried without changing the user's own Blender.
**Answer:** C-003 (CARD.md): the top 20 by downloads, sandboxed; 13 have an operator that works headless with default
settings (`areas/extensions.md`); 15 once four were given the input they are made for (targeted_addons.py).

### T-003 · What separates a contest-level realistic environment from a merely correct one, and can an agent reach it?

**Status:** open
**Parent:** C-001
**Opened:** 2026-11-23
**Question:** the guide checks that a script did what was asked, never whether the image looks real. Proposed test: a
photo match (one real photograph rebuilt in Blender, compared in the same frame, then shuffled pairs judged blind).
**Answer:** in part, C-004 (CARD.md): from 17 published breakdowns, every setting-level technique 4 or more used runs
headless with a measured effect (`areas/realism.md`). Still open: the photo match, which tests the judgement left over.

### T-004 · v2: the lessons the comparison found

**Parent:** C-001
**Opened:** 2026-11-23
**Question:** add to the guide the view-layer trap (`None` in `view_layer.objects` after `bpy.data.objects.remove`,
until `view_layer.update()`; `evals/results/stale_view_layer.py`), which crashed 3 of the 10 scripts written without
it, and the sun-elevation rule held back from v1.
**Answer:** in v2 (git tag `v2`): the view-layer trap (`data-model.md`, `errors.md`), the sun from elevation and
bearing with the sky's `sun_rotation` (`light-world-camera.md`), light and shadow linking, and looping keys and keyed
node inputs (`animation-video.md`), each from a new experiment.
**Status:** answered

### T-005 · Blender competitions over the years: techniques as settings, procedures (operator steps) and judgement

**Status:** active
**Parent:** T-003
**Opened:** 2026-11-23
**Question:** the user's idea: study winners across years (Best of Blender Artists, Suzanne Awards, CG Boost, Pwnisher,
Blender Studio's open movies) far deeper than click-by-click tutorials, writing each technique so an agent can run it.
A research agent is gathering it (scratchpad competitions_study.md, to become kb/research/).
**Answer:** —

### T-006 · Turning a click-path tutorial into operator calls

**Status:** open
**Parent:** T-005
**Opened:** 2026-11-23
**Question:** YouTube teaches by clicks and hotkeys. Ways in: the user pastes Blender's Info editor log (every click as
its Python call); or a lookup from Blender's own keymap and menu labels to operators (`kb.py keys`), built from the
running Blender like the inventory.
**Answer:** —

### T-007 · How much frame-to-frame change does the compositor grain add to a moving shot?

**Status:** open
**Parent:** T-005
**Opened:** 2026-11-24
**Question:** C-006 found the render's noise adds 0.00018 to a forest dolly's flicker at 128 samples; C-005's grain
(Overlay 0.06, a new pattern every frame) was measured only as graded against clean on one frame (0.0088), so its own
flicker is unknown.
**Answer:** —

### T-008 · Which enums read from `bl_rna` list only a placeholder, like the view's `look`?

**Status:** open
**Parent:** T-005
**Opened:** 2026-11-24
**Question:** C-008 found `ColorManagedViewSettings.bl_rna.properties["look"].enum_items` lists only NONE, while the
Standard view takes eight looks; the guide's enum lookups (`kb.py enums`) may miss every enum filled in at run time.
**Answer:** —


### T-009 · How can one photograph give a carving's fine relief: crisp edges, incised rims, raised forms?

**Status:** answered
**Parent:** T-005
**Opened:** 2026-11-24
**Question:** C-007 to C-009 got the jali's openings and symmetry from its photo but not its relief: one top-lit photo
gives only the up-down slope of the surface, and our shading-to-height step rounds every step into a soft slope.
**Answer:** C-011 (CARD.md; `areas/production.md`, items 13 to 18): a learned normal map of the photo, used as the
front's normals with heights from it for the shadows, and the photo's own light and dark for the weathering; judged
"at a glance, yes". The light is still off (T-015).

### T-010 · Does a free, local normal-map model, run on the averaged motif, give crisp carving?

**Status:** answered
**Parent:** T-009
**Opened:** 2026-11-24
**Question:** Models trained on many images (Marigold, DSINE, Depth Anything V2) predict which way each bit of surface
faces; which runs on this laptop, under a licence we can use, and keeps the rims and edges?
**Answer:** yes, for Marigold normals v1.1 (CreativeML OpenRAIL++-M; diffusers, in the repo's .venv), run on the photo
itself, not the averaged motif: 8.3 s a 768 px tile on this laptop's GPU, and the forms band 0.549 against C-009's
0.399 once used as a normal map (C-011). DSINE and Depth Anything V2 were not tried. It flattens plain weathered stone.

### T-011 · Can the relief be fitted so that its render matches the photo (inverse rendering)?

**Status:** open
**Parent:** T-009
**Opened:** 2026-11-24
**Question:** Adjust the height map until a render of it under the fitted light matches the averaged motif, with the
symmetry and "edges are steps" as constraints (SIRFS-style, or Mitsuba 3's differentiable renderer).
**Answer:** —

### T-012 · Are there other photos of the same screen, from other angles or under other light?

**Status:** answered
**Parent:** T-009
**Opened:** 2026-11-24
**Question:** Two or more views give real depth (photogrammetry: COLMAP, Meshroom); one view can only give what looks
right under its own light.
**Answer:** no, not where we could look (C-021). The photographer's three photos in that gallery are three different
screens, each from the front; nobody else's on Flickr; Commons and the museum's archive could not be read from here.

### T-013 · What number says "the detail is there", so the bar is not the judge's eye alone?

**Status:** answered
**Parent:** T-009
**Opened:** 2026-11-24
**Question:** The lines measure fell from C-008 to C-009 while the forms got better; a measure that rewards crisp,
correctly placed relief (the render's local structure against the photo's, under the same light) is missing.
**Answer:** — (C-011 tried a forms band, luminance blurred over 5 px less over 21 px, on stone: it rose as the user's
judgement did, 0.399 to 0.549, with a ceiling of 0.557 at a 2 px misregistration; once the photo's own detail went into
the normals it partly measures the photo against itself, so it is a candidate, not an answer.)
C-016: over all eight judged sheets, SSIM, the openings' IoU (full size), the bright end and the render's cut lines
near the photo's follow the verdicts (Spearman 0.8 or more on the patch and the whole screen); the forms band and the
colour spread in one view only. `compare.py` prints them as a scorecard; `areas/production.md` has the standard.

### T-014 · Why does a 2D curve's fill break at 0.92 mm a point, when the same outlines in pixels fill?

**Status:** answered
**Parent:** T-005
**Opened:** 2026-11-24
**Question:** C-009's trace (420 outlines) filled 0.3116 m2 of front face built in metres and 1.0485 m2 built in pixels;
one smoothed 15 x 4 px island did it. Is it the fill merging points closer than a fixed distance (Blender's scanfill),
and at what spacing does it start? C-011 found it is not the scale alone: at 15 mm the same island (about 981, 141),
smoothed, broke the fill in pixels too, and filled unsmoothed; at 5 mm several holes near (884, 440) and (922, 441)
broke it either way. The build now finds and repairs such a loop by halving; the cause is still open.
**Answer:** C-020: not a tolerance (the scan-fill's only tolerance does not touch closed outlines) but its exact
arithmetic: a scale, a 0.0005 px shift or rounding to 1e-5 px turns the break on and off
(`experiments/curves/curve_fill_knife_edge.py`). Geometry Nodes' Fill Curve never broke; the build's repair uses it.
C-023 (2026-11-26): the batch's later "failed fills" were not the fill. The outlines' turning (`common.contours`
samples one pixel) disagreed with their nesting, so the check's signed area was wrong; both fills gave the even-odd
area exactly. The build now turns each outline by its nesting depth.

### T-015 · What light does the museum's photo have, and can the render's be fitted to it?

**Status:** answered
**Parent:** T-009
**Opened:** 2026-11-24
**Question:** C-011 closed "yes, at a glance" with the light named as what would make it better: the photo's spot pools
on the centre and leaves the frame dark, and lights the rims cream; the render's is even and dim (the stone's bright
end 0.478 against 0.669, the forms band's amplitude 0.53 of the photo's). Fit the spot's direction, cone and falloff,
not only its power, to the photo, now that the normals make the shading comparable.
**Answer:** for the pool, C-012: one spot 4.69 m out, a 13.1 degree cone slightly wider than round, fitted to a light
map of the photo, takes the map's error from 0.443 to 0.198; judged "it reads better". What is left inside the pool
(the bright end, the contrast) is T-016.

### T-016 · What tone curve did the photo's processing apply, and can the render go through the same one?

**Status:** answered
**Parent:** T-015
**Opened:** 2026-11-24
**Question:** After C-012's fitted pool the stone's dark end is close (0.159 against 0.129) but the bright end is short
(0.514 against 0.674) about the same median, the shape an S-curve gives; the photo was edited in Polarr. C-008 found
Blender's contrast looks brighten the wall too, which is set exactly; a curve with the wall set through its inverse
would not.
**Answer:** C-013: an S-curve on luminance through the stone's median (exponents 1.020 below, 2.374 above), the wall set
through its inverse and iterated with it; the bright end and contrast met, the openings unchanged; "almost very
realistic in a passing glance". What gives it away now: the stone looks new (T-017), the borders vanish (C-014).

### T-017 · What makes carved stone look centuries old, and can the photo give the render its age?

**Status:** answered
**Parent:** T-009
**Opened:** 2026-11-24
**Question:** After C-013 the user found the render "VERY fresh, like it was just created": its stone is one procedural
sandstone, even in colour, clean in its hollows; the photo's has stains, darker patches, grime in the recesses and a
darker frame. Marigold's lighting model (`marigold-iid-lighting-v1-1`, cached) splits a photo into albedo and
shading: is its albedo the stone's age, used as the base colour?
**Answer:** for this photo, yes by the judge ("this looks so real!"; C-015): the albedo as a projected base colour,
the photo's pale specks put back into it and taken out of the relief. The colour spread reached 0.49 of the photo's,
a measure that is partly the light's colour and noise. Untried: the light's colour (lit faces paler, shadows redder in
the photo), grime in the hollows.

### T-018 · What of the jali recipe holds for another asset (another screen, or carving that is not pierced)?

**Status:** active (C-022, on the user's word 2026-11-25)
**Parent:** T-009
**Opened:** 2026-11-24
**Question:** C-007 to C-015 built one jali from one photo to "this looks so real!", through 23 findings in
`areas/production.md`. Which of them are about pierced carved stone in general and which about this photo? Run
`make.py`'s chain on a second photo and see what breaks. Parked on the user's word (2026-11-24) until the remaining
jali threads have set a standard: T-013, T-019, T-014, T-012, T-011. Candidates found by C-021, same phone, gallery
and licence as ours: Flickr 51973919577 (a near sibling) and 51975487525 (another design).
**Answer:** —

### T-019 · The light's colour, and grime in the hollows: what is left of the stone's age?

**Status:** answered
**Parent:** T-017
**Opened:** 2026-11-24
**Question:** C-015 found a third of the photo's colour variation goes with brightness (lit faces paler, shadows
redder, at three times the render's slope): the spot's colour and a cooler fill, or the phone's processing. And dirt
gathers in a carving's hollows, which the albedo projected from the front may not carry. Do either move the render
nearer the photo, by the colour measures and the judge?
**Answer:** — (the colour half: not the light's colour, C-017; the photo's processing, a saturation curve on
luminance, C-018: the slopes within 6 %, the colour spread 0.48 to 0.75, "so realistic". Grime in the hollows: not
measurably missing, C-019: the render's deepest recesses at most 4.8 % lighter than the photo's against its stone
overall, so none was added.)

### T-020 · Does this guide's method add anything when the vendor ships its own agent skills?

**Status:** answered
**Parent:** C-001
**Opened:** 2026-11-24
**Question:** Blender had no official skill to compare against. Mapbox publishes 27 (MIT), with evals that grade prose
answers rather than run code. Test case: `~/code/agentic-mapbox`, C-001 (ten blind GL JS tasks, run in headless
Chromium, with and without Mapbox's skills).
**Answer:** for that test case, the eval said not to build. C-001 in `~/code/agentic-mapbox` (2026-11-24): on ten
blind GL JS tasks the model got 10 of 10 alone and 10 of 10 with Mapbox's 27 skills, which it never opened. The
method's eval was still the useful part, because it found no gap for a guide to fill before one was written. Open
behind it: the newer GL JS surface (agentic-mapbox T-004).

### T-021 · Can the read step tell an opening from a shadow without our photo's colours?

**Status:** parked
**Parent:** T-018 (C-022)
**Opened:** 2026-11-25
**Question:** The colour rule expects red stone in front of a lit grey wall, and C-022 found four ways photos break
it. Four probes on the 19 photos (2026-11-25, scratch code, not kept) found no reading to replace it. First, a light
or dark split, its side chosen by structure (the stone one piece, the openings many enclosed pieces): the score ranked
it above the colour rule on our photo (0.78 against 0.62), where the colour rule is plainly better, so the score
cannot choose between readings. Second, Depth Anything V2 Small (Apache-2.0, in the local cache, under a second a
photo at 1,400 px) shows our holes clearly, but a local depth split takes every step in depth for an opening: 0.39 to
0.41 agreement (IoU) with the approved reading. Third, brightness to draw the outline with depth to decide: 0.23.
Fourth, depth's surest pixels as seeds for the colour fields: 0.24, with 39 % of the image called opening against
13 %. To resume: depth looks usable for telling which side is the opening, not for drawing its outline.
**Answer:** —

### T-022 · How can the read step find a screen that is only part of a larger scene?

**Status:** open
**Parent:** T-021 (C-023)
**Opened:** 2026-11-26
**Question:** In 06 and 07 the screen sits inside a porch or a hall. In 06 the colour rule takes the pale sunlit columns
and the arch's lit rim for openings (grey, like the wall it expects behind red stone), the carved field's box is placed
by those large "openings" and spans the picture, and the render cuts them out and shows the backdrop through them, its
colour at that height the jali's dark blue-green holes (the user: "a strange blueish affect"). A lead: place the field
where openings are many and packed (fix 8's density, a count of pieces), not where they are large.
**Answer:** —

### T-023 · Can the rebuilt screens, taken together, be a library from which new jali designs are generated?

**Status:** open
**Parent:** T-018
**Opened:** 2026-11-27
**Question:** The user, during C-023: going over each piece until it reads as its photo builds a library of assets, "to
the point that we might generatively create new assets based on past renders, completely new designs not seen before."
What each rebuild holds now is a traced outline mask, a relief from normals and an albedo, matched to one photo; it
does not hold the design's own structure (motif, repeat, symmetry, grid), which C-009's averaging and `symmetry.py`
touched once. Open: what representation of a screen a generator would need, and how many rebuilt screens make a library.
**Progress:** C-024 (2026-11-27): as traced, no screen's openings give a motif; one repeat away they match at most 47 %
of themselves over a field and 64 % in one hand-cut panel (bar 0.70). The unit is the panel, not the field.
C-025 (2026-11-27): from the mean of a panel's copies, each moved by one shift, 13's motif (a star and its ring
of holes) rebuilds 83 % of its panel, 18's 80 %, 12's 67 %; 1 of 7 clears the bar, and two failures are the measure's.
C-026 (2026-11-27): the measure fixed (a repeat its lattice agrees on, stone and openings scored alike), still 1 of
7 (13: 0.87 balanced); 18 0.81, short of the margin by 0.008; 08 and 10 unmeasurable on panels that small.
**Answer:** —

### T-024 · How is a design of two levels found, a fine net with larger shapes laid over it?

**Status:** open
**Parent:** T-023 (C-026)
**Opened:** 2026-11-27
**Question:** 16's central panel is a fine net of small diamonds that repeats about every 54 px, and over it larger
shapes that do not repeat at that step (`shots/jali-batch/c026_motifs.jpg`, its motif's mean blotched where the
copies disagree). One motif on one lattice cannot hold it. Is the larger level a second lattice (a supertile) found
the same way at a longer step, or a different kind of structure?
**Answer:** —
