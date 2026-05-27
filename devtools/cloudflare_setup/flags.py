"""Flag validation for cloudflare_setup script.

Subcommand-style: ``phase`` is a positional argument
(``projects|domains|dns|status|trigger|all``, default ``all``). The
optional ``--env=dev|stage|prod`` flag selects the target environment
(default ``prod``).
"""

import sys
from typing import Any

from devtools.cloudflare_setup.config import VALID_ENVS

from utils.describe import ScriptDescribe
from utils.flags_to_dict import set_default_values
from utils.flags_to_dict import validate_allowed_flags


VALID_PHASES = [
    'projects',
    'domains',
    'dns',
    'status',
    'trigger',
    'all',
]


ALLOWED_FLAGS = [
    'phase',
    'env',
    'help',
    'verbose',
]


_DEFAULTS = {
    'phase': 'all',
    'env': 'prod',
    'verbose': False,
}


_PHASE_SUMMARIES = {
    'projects': 'Crea o actualiza los 6 Pages projects para el env elegido',
    'domains': 'Adjunta el dominio personalizado a cada project',
    'dns': 'Crea/actualiza records CNAME apuntando a pages.dev',
    'status': 'Muestra el ultimo deployment de cada project',
    'trigger': 'Dispara un build fresco en cada project (sin push a GitHub)',
    'all': 'Ejecuta projects -> domains -> dns -> status en orden',
}


def _extract_positionals(flags_dict: dict[str, Any]) -> None:
    """
    Pull the positional ``phase`` arg from sys.argv into ``flags_dict``.

    ``flags_to_dict`` only parses ``--key=value``; positionals
    (``cloudflare_setup trigger``) would be lost otherwise. Only the
    first positional is taken — this script has a single subcommand
    level.
    """
    raw_args = sys.argv[2:]
    for arg in raw_args:
        if arg == '--':
            break
        if not arg.startswith('--'):
            flags_dict.setdefault('phase', arg)
            break


def _validate_phase(flags_dict: dict) -> str:
    phase = flags_dict.get('phase', 'all')
    if phase not in VALID_PHASES:
        msg = f'phase invalido: {phase!r}. Validos: {", ".join(VALID_PHASES)}.'
        raise ValueError(msg)
    return phase


def _validate_env(flags_dict: dict) -> str:
    env = flags_dict.get('env', 'prod')
    if env not in VALID_ENVS:
        msg = f'env invalido: {env!r}. Validos: {", ".join(VALID_ENVS)}.'
        raise ValueError(msg)
    return env


def flag(flags_dict: dict) -> dict:
    """Validate and normalize flags for cloudflare_setup script."""
    _extract_positionals(flags_dict)
    validate_allowed_flags(flags_dict, ALLOWED_FLAGS)
    flags_dict = set_default_values(flags_dict, _DEFAULTS)
    _validate_phase(flags_dict)
    _validate_env(flags_dict)
    return flags_dict


def describe() -> ScriptDescribe:
    """Machine-readable inventory of cloudflare_setup commands and flags."""
    return {
        'name': 'cloudflare_setup',
        'kind': 'subcommand',
        'summary': (
            'Orquestador idempotente de Cloudflare Pages: crea/patchea los '
            'projects, adjunta dominios, configura DNS, triggerea deploys '
            'y muestra el status. Soporta los 3 envs (dev|stage|prod).'
        ),
        'commands': [
            {
                'name': phase,
                'summary': _PHASE_SUMMARIES.get(phase, ''),
                'flags': ['env'],
                'destructive': False,
            }
            for phase in VALID_PHASES
        ],
        'flags': {
            'env': {
                'type': 'string',
                'default': 'prod',
                'summary': (
                    'Entorno objetivo (dev|stage|prod). Selecciona el '
                    'sufijo de project_name, la branch GitHub y los env '
                    'vars per env.'
                ),
            },
            'verbose': {
                'type': 'bool',
                'default': False,
                'summary': 'Logs adicionales (no usado todavia)',
            },
        },
    }
