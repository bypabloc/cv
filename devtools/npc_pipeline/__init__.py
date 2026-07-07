"""Orchestrates the journey-npc-realism Blender headless pipeline.

Subcommand-style script. Each subcommand shells out to
`blender --background --python <script.py> -- <args>` — the actual bpy
logic lives in `npc_pipeline/scripts/*.py`, run by Blender's own embedded
Python interpreter, NOT by devtools/.venv. See
.claude/docs/journey-npc-realism/ for the full pipeline reference.
"""
