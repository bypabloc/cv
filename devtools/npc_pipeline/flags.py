"""Flag validation for the npc_pipeline script.

Subcommand-style script (same convention as ``serverless``/``docker``/
``rotate_secrets``): one positional subcommand + explicit flags. See
``main.py`` module docstring for the full command reference.
"""

import sys
from typing import Any

from utils.describe import ScriptDescribe
from utils.flags_to_dict import set_default_values
from utils.flags_to_dict import validate_allowed_flags


VALID_COMMANDS = [
    'status',
    'install-addons',
    'generate-mesh',
    'rig',
    'animate',
    'export',
]

ALLOWED_FLAGS = [
    # Comando posicional (resuelto en _extract_positionals)
    'command',
    'subcommands',
    # Flags de las etapas
    'mpfb2_zip',
    'input',
    'output',
    'preview_dir',
    'skip_compress',
    'blender_bin',
    # Cross-cutting
    'help',
    'verbose',
]

_DEFAULTS = {
    'skip_compress': False,
    'verbose': False,
    'blender_bin': 'blender',
}

_REQUIRED_BY_COMMAND: dict[str, list[str]] = {
    'status': [],
    'install-addons': [],  # mpfb2_zip es opcional: Rigify ya viene con Blender
    'generate-mesh': ['output'],
    'rig': ['input', 'output'],
    'animate': ['input', 'output'],
    'export': ['input', 'output'],
}

_COMMAND_SUMMARIES = {
    'status': 'Verifica que Blender (>=4.2) este disponible en PATH',
    'install-addons': 'Instala MPFB2 (zip local) + habilita Rigify, headless',
    'generate-mesh': 'Genera la malla humanoide base con MPFB2, headless',
    'rig': 'Riggea la malla con Rigify (metarig + generate), headless',
    'animate': 'Crea los clips idle/walk (keyframes FK) sobre el rig, headless',
    'export': 'Exporta a .glb (nativo Blender + glTF-Transform Meshopt)',
}

_COMMAND_FLAGS = {
    'status': ['blender_bin'],
    'install-addons': ['mpfb2_zip', 'blender_bin'],
    'generate-mesh': ['output', 'preview_dir', 'blender_bin'],
    'rig': ['input', 'output', 'blender_bin'],
    'animate': ['input', 'output', 'blender_bin'],
    'export': ['input', 'output', 'skip_compress', 'blender_bin'],
}


def _extract_positionals(flags_dict: dict[str, Any]) -> None:
    """Extract the subcommand positional (e.g. ``npc_pipeline status``).

    ``flags_to_dict`` solo parsea ``--key=value``; el positional se
    reconstruye desde ``sys.argv[2:]`` saltando el nombre del script.
    """
    raw_args = sys.argv[2:]
    for arg in raw_args:
        if arg == '--':
            break
        if not arg.startswith('--'):
            flags_dict.setdefault('command', arg)
            break


def _validate_command(flags_dict: dict) -> str:
    command = flags_dict.get('command')
    if not command:
        msg = (
            'Falta el subcomando posicional. Comandos validos: '
            f'{", ".join(VALID_COMMANDS)}.\n'
            'Ejemplo: python devtools/run.py npc_pipeline status'
        )
        raise ValueError(msg)
    if command not in VALID_COMMANDS:
        msg = (
            f'Comando invalido: {command!r}. '
            f'Validos: {", ".join(VALID_COMMANDS)}.'
        )
        raise ValueError(msg)
    return command


def _validate_required_flags(command: str, flags_dict: dict) -> None:
    required = _REQUIRED_BY_COMMAND.get(command, [])
    missing = [f for f in required if not flags_dict.get(f)]
    if missing:
        flag_args = ', '.join(f'--{f.replace("_", "-")}' for f in missing)
        msg = f'Flags faltantes para {command!r}: {flag_args}.'
        raise ValueError(msg)


def flag(flags_dict: dict) -> dict:
    """Validate and normalize flags for the npc_pipeline script."""
    _extract_positionals(flags_dict)
    validate_allowed_flags(flags_dict, ALLOWED_FLAGS)

    command = _validate_command(flags_dict)
    _validate_required_flags(command, flags_dict)

    return set_default_values(flags_dict, _DEFAULTS)


def describe() -> ScriptDescribe:
    """Machine-readable inventory of npc_pipeline commands and flags."""
    return {
        'name': 'npc_pipeline',
        'kind': 'subcommand',
        'summary': (
            'Orquesta el pipeline Blender headless (MPFB2 -> Rigify -> '
            'export) del plan journey-npc-realism. Ver '
            '.claude/docs/journey-npc-realism/.'
        ),
        'commands': [
            {
                'name': cmd,
                'summary': _COMMAND_SUMMARIES.get(cmd, ''),
                'flags': _COMMAND_FLAGS.get(cmd, []),
                'destructive': False,
            }
            for cmd in VALID_COMMANDS
        ],
        'flags': {
            'mpfb2_zip': {
                'type': 'string',
                'summary': (
                    'Path al zip de MPFB2 descargado manualmente '
                    '(static.makehumancommunity.org, sin cuenta)'
                ),
                'required': False,
            },
            'input': {
                'type': 'string',
                'summary': 'Path al .blend de entrada de la etapa',
                'required': False,
            },
            'output': {
                'type': 'string',
                'summary': 'Path de salida (.blend o .glb segun la etapa)',
                'required': False,
            },
            'preview_dir': {
                'type': 'string',
                'summary': 'Directorio para los PNG de verificacion visual',
                'required': False,
            },
            'skip_compress': {
                'type': 'bool',
                'default': False,
                'summary': (
                    'En `export`: omitir la compresion Meshopt de '
                    'glTF-Transform (deja el .glb crudo de Blender)'
                ),
            },
            'blender_bin': {
                'type': 'string',
                'default': 'blender',
                'summary': 'Binario de Blender a invocar (default: PATH)',
            },
        },
    }
