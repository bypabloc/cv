"""Flag parser for the ``mutation_testing`` script."""

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
    'paths',
    'category',
    'all',
    'dry_run',
    'help',
]

VALID_CATEGORIES = ('critical', 'standard', 'experimental')

DEFAULTS: dict[str, Any] = {
    'paths': [],
    'category': None,
    'all': False,
    'dry_run': False,
    'help': False,
}


def flag(flags_dict: dict[str, Any]) -> dict[str, Any]:
    """Procesa y válida las flags para el script mutation_testing.

    Args:
        flags_dict: Dict de flags ya procesado por ``run.py``.

    Returns:
        Dict con flags validadas y defaults aplicados.

    Raises:
        ValueError: si hay flags no permitidas o combinaciones inválidas.
    """
    validate_allowed_flags(flags_dict, ALLOWED_FLAGS)
    flags_dict = set_default_values(flags_dict, DEFAULTS)

    _normalize_paths(flags_dict)
    _validate_category(flags_dict)
    _validate_combination(flags_dict)

    return flags_dict


def _normalize_paths(flags_dict: dict[str, Any]) -> None:
    """Convierte ``--paths=a,b,c`` (string) a lista."""
    raw = flags_dict.get('paths')
    if isinstance(raw, str):
        flags_dict['paths'] = [v for v in raw.split(',') if v]
    elif raw is None:
        flags_dict['paths'] = []


def _validate_category(flags_dict: dict[str, Any]) -> None:
    """Verifica que ``category`` sea un valor aceptado."""
    value = flags_dict.get('category')
    if value is None:
        return
    if value not in VALID_CATEGORIES:
        msg = (
            f'--category={value} inválido. '
            f'Valores aceptados: {", ".join(VALID_CATEGORIES)}.'
        )
        raise ValueError(msg)


def _validate_combination(flags_dict: dict[str, Any]) -> None:
    """Al menos uno de --paths / --category / --all debe especificarse."""
    has_paths = bool(flags_dict.get('paths'))
    has_category = flags_dict.get('category') is not None
    has_all = bool(flags_dict.get('all'))

    if not (has_paths or has_category or has_all):
        msg = (
            'Especifica al menos uno: --paths=<comma-separated>, '
            '--category=<critical|standard|experimental>, o --all.'
        )
        raise ValueError(msg)

    if has_all and (has_paths or has_category):
        msg = '--all es excluyente con --paths y --category.'
        raise ValueError(msg)


def describe() -> ScriptDescribe:
    """Machine-readable inventory of mutation_testing flags."""
    return {
        'name': 'mutation_testing',
        'kind': 'monocommand',
        'summary': (
            'Mutation testing del server (mutmut) con thresholds por '
            'criticidad. Lee devtools/mutation_testing/config.py.'
        ),
        'commands': [],
        'flags': {
            'paths': {
                'type': 'list',
                'summary': (
                    'Paths bajo server/ separados por coma '
                    '(ej. apps/payments,apps/auth).'
                ),
            },
            'category': {
                'type': 'choice',
                'choices': list(VALID_CATEGORIES),
                'summary': (
                    'Corre todos los paths de una categoria del config.'
                ),
            },
            'all': {
                'type': 'bool',
                'default': False,
                'summary': 'Corre todas las categorias (critical+standard+experimental).',
            },
            'dry_run': {
                'type': 'bool',
                'default': False,
                'summary': (
                    'Imprime que paths se mutarian con que threshold, sin '
                    'ejecutar mutmut.'
                ),
            },
        },
    }
