"""Flags para el script verify."""

import os
import sys
from typing import Any

from utils.describe import ScriptDescribe
from utils.flags_to_dict import set_default_values
from utils.flags_to_dict import validate_allowed_flags


sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


ALLOWED_FLAGS = [
    'staged',
    'modified',
    'all_changed',
    'execute',
    'json',
    'help',
]

DEFAULTS = {
    'staged': False,
    'modified': False,
    'all_changed': False,
    'execute': False,
    'json': False,
    '_invoked_from': 'python',
}


def _validate_source_flags(flags_dict: dict[str, Any]) -> None:
    """Exige exactamente UNA fuente de archivos (staged/modified/all_changed)."""
    sources = sum(
        1 for k in ('staged', 'modified', 'all_changed') if flags_dict.get(k)
    )

    if sources == 0:
        # Default: all_changed (incluye staged + modified + untracked).
        flags_dict['all_changed'] = True
        return

    if sources > 1:
        raise ValueError(
            'Solo se permite UNA fuente: --staged, --modified o --all-changed.',
        )


def flag(flags_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Procesa y valida las flags para verify.

    Parameters
    ----------
    flags_dict : dict
        Flags ya parseadas por run.py.

    Returns
    -------
    dict
        Flags validadas con defaults aplicados.

    Raises
    ------
    ValueError
        Si se usan flags no permitidas o combinaciones invalidas.
    """
    validate_allowed_flags(flags_dict, ALLOWED_FLAGS)
    flags_dict = set_default_values(flags_dict, DEFAULTS)
    _validate_source_flags(flags_dict)
    return flags_dict


def describe() -> ScriptDescribe:
    """Machine-readable inventory of verify flags."""
    return {
        'name': 'verify',
        'kind': 'monocommand',
        'summary': 'Sugerir/ejecutar verificaciones segun archivos cambiados',
        'commands': [],
        'flags': {
            'staged': {
                'type': 'bool',
                'default': False,
                'summary': 'Solo archivos staged',
            },
            'modified': {
                'type': 'bool',
                'default': False,
                'summary': 'Solo archivos modificados (no staged)',
            },
            'all_changed': {
                'type': 'bool',
                'default': True,
                'summary': 'staged + modified + untracked (default)',
            },
            'execute': {
                'type': 'bool',
                'default': False,
                'summary': 'Ejecutar las verificaciones (sino solo lista)',
            },
            'json': {
                'type': 'bool',
                'default': False,
                'summary': 'Output JSON estructurado',
            },
        },
    }
