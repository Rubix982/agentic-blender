# Results

## Independent set, guide v1 (2026-11-23)

`python3 evals/run_eval.py --set independent`: one session per task and arm, model claude-opus-5-5, each session in
an empty folder outside the repository with no MCP servers, the agent writing `task.py` without running Blender and
the harness running it once. Records: `results/independent-20261123-202046.jsonl` (transcripts stay in the
git-ignored `runs/20261123-202046-independent/`).

| Task | With the skill | Without | Why the one without failed |
|---|---|---|---|
| 1. Terrain from a height table | right | crashed | `None` in `view_layer.objects` after deleting the default objects |
| 2. Weighted bevel and array | right | crashed | the same |
| 3. Coated car paint | right | right | |
| 4. Light linking | right | crashed | `CollectionObject.object`, a name that does not exist |
| 5. 360° panorama | right | right | |
| 6. Looping slide, spin and glow | right | right | |
| 7. Baked rigid-body drop | right | right | |
| 8. Sphere grid with an exposed Scale | right | right | |
| 9. STL for a 3D printer | right | crashed | `None` in `view_layer.objects` after deleting the default objects |
| 10. Composite over a brand colour | right | right | |
| **Right first time** | **10** | **6** | |

Every script written without the skill that ran was right (6 of 6); all four failures crashed before saving anything.

**The view-layer trap (tasks 1, 2, 9).** All ten scripts written without the skill started from the factory scene and
deleted its cube, light and camera with `bpy.data.objects.remove`. Three then looped over `view_layer.objects` to
deselect everything and met `None`. A separate run (`results/stale_view_layer.py`) shows why: after the removal the
view layer listed `[None, None, None]`, still so after a new object was linked, and `['New']` only after
`view_layer.update()`. The guide does not describe this trap. Nine of the ten scripts written with the skill avoided
it by starting from an empty file, as the skill's skeleton does (`read_factory_settings(use_empty=True)`); the tenth
deleted the objects and never looped over the view layer.

**The light-linking name (task 4).** The session with the skill ran `kb.py find light linking`,
`kb.py struct LightLinking` and `kb.py prop Object.light_linking`, and set
`collection_objects[...].light_linking.link_state`. The session without it guessed `.object` on a `CollectionObject`.

**Cost.** With the skill the sessions took 12.5 turns on average against 2.8, and the ten cost 7.43 dollars against
5.98 (the cost Claude Code reports); time per session was the same (155 s against 156 s).

**What this does not show.** One session per task and arm: the four tasks where the arms differed all went the
skill's way, which, if the skill made no difference, would happen about one time in 16. The agents were not allowed
to run Blender, so this measures first attempts; an agent that may run its script would see these crashes and fix
them, and how many rounds the skill saves there is not measured. The writer's set (`tasks.md`) was not run.

**False flag in the records.** `agent_ran_blender` is true for task 1 with the skill: the pattern matched a command
run inside the folder `skills/blender` (`kb.py`). No session ran Blender; a strict pattern (the Blender binary, or
`blender -` as a command) finds none in the 20 transcripts.
