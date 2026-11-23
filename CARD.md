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

**Opened:** 2026-11-23

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

**Result:** —
