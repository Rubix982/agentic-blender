# blender-field-guide

A field guide to Blender 4.5 for coding agents, packaged as a Claude Code skill.

An agent's memory of Blender mixes every version from 2.7 to 4.x, so it writes property names that were renamed years
ago, operators that need a window it doesn't have, and scripts that fail while reporting success. This guide replaces
memory with three things that can be checked:

- **What Blender says about itself.** `skills/blender/scripts/inventory.py` asks Blender 4.5.14 LTS for every type, property, operator,
  node and Python function it has: 3,944 types, 10,477 properties, 2,482 operators, 523 node types with their 2,246
  sockets, and 611 members of `bmesh`, `mathutils` and the other modules around `bpy`. `kb.py` searches it.
- **What happens when you try.** Small headless experiments, one question each, whose results are kept
  (`experiments/<area>/results/*.json`) and can be run again on another version to see which facts changed.
- **What real projects learned.** Lessons from weeks of building cloth garments on animated figures in Blender, with
  the numbers that were measured, rewritten without the project's specifics (`kb/lessons/`).

Blender's own manual and Python reference (4,120 pages) can be searched offline with `docs.py`; they are downloaded on
first use, not bundled.

## Use

The skill is `skills/blender/`. Its front page (`SKILL.md`) is the way of working and a map; `areas/*.md` are the
guides by area; `scripts/` holds the tools:

```bash
python3 skills/blender/scripts/kb.py find smooth angle            # search everything Blender reports about itself
python3 skills/blender/scripts/kb.py node "Principled BSDF"       # every socket: name, identifier, type, default
python3 skills/blender/scripts/kb.py path ClothSettings           # -> bpy.data.objects[...].modifiers[...]<ClothModifier>.settings
python3 skills/blender/scripts/kb.py op export_scene.gltf         # every parameter with its default
python3 skills/blender/scripts/docs.py fetch                      # once: the 4.5 manual and Python reference
python3 skills/blender/scripts/docs.py search shadow catcher      # passages with their public URLs
python3 skills/blender/scripts/run.py my_script.py -- --out x.png # run a script in Blender, headless, the safe way
```

Install as a plugin (this repository is its own marketplace):

```
/plugin marketplace add /path/to/blender-field-guide
/plugin install blender-field-guide@blender-field-guide
```

## How it is built

`METHOD.md` sets the rules: every fact carries its evidence (`[inv]` read from Blender, `[exp: path]` measured here,
`[lesson]` from a project, `[doc: link]` from Blender's documentation), experiments record facts as sentences that
could come out false, and no project, client or person is named. `CARD.md` holds the open question: whether the guide
makes an agent's Blender scripts right the first time more often, tested on ten tasks written before the guide
(`evals/tasks.md`).

Requirements: Blender 4.5 (found at `$BLENDER`, `~/Applications/Blender.app`, `/Applications/Blender.app` or on
`PATH`) and Python 3.9 or later. Everything here was read and measured on Blender 4.5.14 LTS, Apple Silicon (M2 Pro,
16 GB).
