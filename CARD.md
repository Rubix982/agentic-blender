# CARD

The live card is below the template. One card open at a time; a card closes with a number, or a sentence that could
have come out the other way.

```
### C-xxx · title
**Opened / Closed:**
1. WHERE WE ARE      the last thing established, as a number or a fact
2. WHAT WE ARE DOING one action a second person could carry out
3. WHY               what is not known now that will be known after
4. WHAT IS AFFECTED  which claims, files or numbers change either way (written before the work)
5. CONCLUSION        if X, we claim A; if not-X, we claim B
6. CONSEQUENCE OF NOT DOING IT
**Result:**
```

---

### C-001 · A field guide to Blender 4.5, read from Blender itself, and a skill made from it

**Opened:** 2026-11-23 · **Closed:** 2026-11-23

1. **WHERE WE ARE.** Blender has come up in two projects. What we learned is spread over one 371-line feature map and
   dozens of lessons scattered through another project's logs, and none of it reaches an agent working somewhere else.
   This machine runs Blender 4.5.14 LTS (Apple Silicon, 16 GB).
2. **WHAT WE ARE DOING.** Build a knowledge base of Blender 4.5 from three sources: an inventory read from Blender
   itself (every type, property, operator and node, with node sockets), experiments run headless on this machine, and
   lessons from earlier projects, rewritten as general lessons. Document it by area, and package it as a skill
   (`skills/blender/`) with a lookup tool over the inventory.
3. **WHY.** Unknown now: whether a written guide changes how often an agent's Blender script does the right thing the
   first time. After: a count, on ten tasks set aside before any of the guide was written (`evals/tasks.md`), done by a
   fresh agent with the skill and without it.
4. **WHAT IS AFFECTED.** Nothing that exists yet; this repository is new. The earlier projects' own Blender notes stay
   where they are; they may later point here.
5. **CONCLUSION.** If the agent with the skill gets at least 3 more of the 10 tasks right first time than without it, the
   skill is where Blender work starts in every project, and new Blender lessons are written here. If not, the guide is
   reference only, and the failures say what the gap is instead (knowledge, or checking the result).
6. **CONSEQUENCE OF NOT DOING IT.** Each project rediscovers Blender from an agent's memory, which mixes versions 2.7 to
   4.x; the next one (a pierced stone screen to be lit and rendered) starts from zero.

**Amendment (2026-11-23, before any run):** the ten tasks in `evals/tasks.md` were written by the guide's writer, who
then briefed the guide's workers knowing them, so the guide's coverage leans toward them (details in `evals/tasks.md`).
The claim in field 5 is tested on an independent set of ten tasks written by a fresh agent that had not seen the guide
(`evals/independent/`); the writer's set is reported beside it.

**Status (2026-11-23, end of the build):** the guide is frozen as git tag `v1`: 22 area pages, a generated reference
(every node, modifier, constraint and setting of 4.5), 121 experiments with 884 recorded facts, 168 lessons, and the
audit finding 1,812 of 1,859 cited numbers in the results they cite. Both task sets and the harness are validated
(`evals/harness_check.md`: right solutions 10 of 10 and wrong ones 0 of 10, in each set). Not run yet: the with and
without comparison itself, 20 Claude sessions per set on the user's account, which waits for the user's yes.

**Result:** with the skill, 10 of the 10 independent tasks were right the first time; without it, 6 of 10 (one
session per task and arm, claude-opus-5-5; `evals/results.md`). The gap of 4 meets the bar of 3 in field 5, so the
first branch holds: Blender work starts from this skill, and new Blender lessons are written here.

What the 4 is made of: every script without the skill that ran was right (6 of 6), and all four failures crashed
before saving anything. Three hit one trap the guide does not describe (deleting the default objects with
`bpy.data.objects.remove` leaves `None` in `view_layer.objects` until `view_layer.update()`); the skill's sessions
avoided it by starting from the empty file in its skeleton (9 of 10). The fourth guessed a light-linking name that
the skill's session looked up with `kb.py`. Limits: one session per task and arm (the four differing tasks all going
one way would happen about one time in 16 if the skill made no difference); the agents wrote blind, so this measures
first attempts, not finished work; the skill's sessions took 12.5 turns on average against 2.8 and cost about a
quarter more; the writer's set was not run.
