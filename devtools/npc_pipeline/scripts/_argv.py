"""Tiny CLI arg parser shared by the npc_pipeline bpy scripts.

Blender scripts run standalone
(``blender --background --python X.py -- --key=value``): Blender keeps
its own args before ``--`` in ``sys.argv``, so this parses only what
comes after the separator. Blender adds each script's own directory to
``sys.path`` when run via ``--python``, so sibling scripts can
``from _argv import parse_args`` directly.
"""

import sys


def parse_args() -> dict[str, str]:
    """Parse ``--key=value`` pairs after the ``--`` separator."""
    if '--' not in sys.argv:
        return {}
    raw = sys.argv[sys.argv.index('--') + 1 :]
    parsed: dict[str, str] = {}
    for arg in raw:
        if arg.startswith('--') and '=' in arg:
            key, value = arg[2:].split('=', 1)
            parsed[key.replace('-', '_')] = value
    return parsed
