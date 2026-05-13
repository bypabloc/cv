"""Flag parser for the ``weak_assertion`` script."""

from __future__ import annotations

import os
import sys
from typing import Any


# Permite importar utils del paquete devtools/
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.describe import ScriptDescribe
from utils.flags_to_dict import set_default_values
from utils.flags_to_dict import validate_allowed_flags


ALLOWED_FLAGS = [
    'files',
    'git_mode',
    'quiet',
    'help',
]

DEFAULTS: dict[str, Any] = {
    'files': [],
    'git_mode': None,  # None | 'staged' | 'unmerged' | 'modified' | 'changed'
    'quiet': False,
    'help': False,
}

VALID_GIT_MODES = ('staged', 'unmerged', 'modified', 'changed')


def flag(flags_dict: dict[str, Any]) -> dict[str, Any]:
    """Procesa y válida las flags para el script weak_assertion.

    Args:
        flags_dict: Dict de flags ya procesado por ``run.py`` (parser hace
            ``--foo=bar`` -> ``{'foo': 'bar'}``).

    Returns:
        Dict con flags validadas y defaults aplicados.

    Raises:
        ValueError: si hay flags no permitidas o valores inválidos.
    """
    validate_allowed_flags(flags_dict, ALLOWED_FLAGS)
    flags_dict = set_default_values(flags_dict, DEFAULTS)

    _normalize_files(flags_dict)
    _validate_git_mode(flags_dict)

    return flags_dict


def _normalize_files(flags_dict: dict[str, Any]) -> None:
    """Convierte ``--files=a,b,c`` (string) a lista, o respeta lista existente."""
    raw = flags_dict.get('files')
    if isinstance(raw, str):
        flags_dict['files'] = [v for v in raw.split(',') if v]
    elif raw is None:
        flags_dict['files'] = []


def _validate_git_mode(flags_dict: dict[str, Any]) -> None:
    """Verifica que ``git_mode`` sea uno de los valores aceptados."""
    value = flags_dict.get('git_mode')
    if value is None:
        return
    if value not in VALID_GIT_MODES:
        msg = (
            f'--git-mode={value} inválido. '
            f'Valores aceptados: {", ".join(VALID_GIT_MODES)}.'
        )
        raise ValueError(msg)


def describe() -> ScriptDescribe:
    """Machine-readable inventory of weak_assertion flags."""
    return {
        'name': 'weak_assertion',
        'kind': 'monocommand',
        'summary': (
            'Detecta asserts vagos en archivos de test Python (política '
            'AI-testing independence). Falla con exit 1 si encuentra '
            'asserts vagos en archivos staged/unmerged.'
        ),
        'commands': [],
        'flags': {
            'files': {
                'type': 'list',
                'summary': (
                    'Paths separados por coma. Solo se procesan los que '
                    'están bajo un directorio tests/ y existen en disco.'
                ),
            },
            'git_mode': {
                'type': 'choice',
                'choices': list(VALID_GIT_MODES),
                'summary': (
                    'Toma archivos de git en lugar de --files. '
                    "'staged' (pre-commit), 'unmerged' (pre-push), "
                    "'modified' (working tree), 'changed' (todos)."
                ),
            },
            'quiet': {
                'type': 'bool',
                'default': False,
                'summary': 'Solo imprime el conteo, no el detalle.',
            },
        },
    }
