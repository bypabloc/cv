"""Validacion de flags del comando `e2e` (monocommand).

Flags:
  --module=api|admin|app   modulo a correr (ausente -> los 3 en orden)
  --env=dev|stage          entorno de DEPLOY (NUNCA prod; default dev)
  --samples=N              muestras por endpoint read-safe (modulo api; >=1)
  --aws-profile=<X>        perfil AWS CLI para SSM/Neon (default: shell)
  --keep-data              NO limpiar los datos sinteticos creados en Neon
  --lambda=<name>          sub-filtro del modulo api (cv|contact_form|
                           tracking_pixel|auth|users); default todos
  --headed                 browser visible (admin/app, debug local sin container)
  --verbose / --quiet
"""

from __future__ import annotations

import os
import sys
from typing import Any


sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.describe import ScriptDescribe
from utils.flags_to_dict import set_default_values
from utils.flags_to_dict import validate_allowed_flags


# Entornos de DEPLOY soportados (NUNCA prod: el harness muta el entorno y
# lee Neon). Duplicado intencional de tests.shared.config.VALID_ENVS para
# no acoplar la validacion de flags (devtools) al portador E2E (tests/).
VALID_ENVS = ('dev', 'stage')

# Modulos first-class del harness E2E.
VALID_MODULES = ('api', 'admin', 'app')

# Sub-filtro del modulo api (los 5 Lambdas HTTP).
VALID_LAMBDAS = ('cv', 'contact_form', 'tracking_pixel', 'auth', 'users')

ALLOWED_FLAGS = [
    'module',
    'env',
    'samples',
    'aws_profile',
    'keep_data',
    'lambda',
    'headed',
    'verbose',
    'quiet',
    'help',
]

DEFAULTS: dict[str, Any] = {
    'module': None,
    'env': 'dev',
    'samples': 5,
    'aws_profile': None,
    'keep_data': False,
    'lambda': None,
    'headed': False,
    'verbose': False,
    'quiet': False,
}


def flag(flags_dict: dict[str, Any]) -> dict[str, Any]:
    """Valida y normaliza las flags del comando `e2e`."""
    validate_allowed_flags(flags_dict, ALLOWED_FLAGS)
    flags_dict = set_default_values(flags_dict, DEFAULTS)

    module = flags_dict.get('module')
    if module is not None and module not in VALID_MODULES:
        raise ValueError(
            f"--module invalido: '{module}'. "
            f'Validos: {", ".join(VALID_MODULES)} (o ausente -> los 3).',
        )

    env = flags_dict.get('env')
    if env not in VALID_ENVS:
        raise ValueError(
            f"--env invalido: '{env}'. e2e MUTA el entorno y lee Neon: "
            f'solo {", ".join(VALID_ENVS)} (NUNCA prod).',
        )

    lam = flags_dict.get('lambda')
    if lam is not None and lam not in VALID_LAMBDAS:
        raise ValueError(
            f"--lambda invalido: '{lam}'. Validos: {', '.join(VALID_LAMBDAS)}",
        )

    samples = flags_dict.get('samples')
    if not isinstance(samples, bool) and not isinstance(samples, int):
        try:
            flags_dict['samples'] = int(samples)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f'--samples debe ser un entero. Recibido: {samples!r}',
            ) from exc
    if flags_dict['samples'] < 1:
        raise ValueError('--samples debe ser >= 1')

    return flags_dict


def describe() -> ScriptDescribe:
    """Inventario machine-readable de las flags del comando `e2e`."""
    return {
        'name': 'e2e',
        'kind': 'monocommand',
        'summary': (
            'E2E unificado (Python 3.14) contra el backend desplegado '
            '(dev|stage): modulos api (HTTP), admin (browser) y app '
            '(las 6 apps Astro). NUNCA prod'
        ),
        'commands': [],
        'flags': {
            'module': {
                'type': 'choice',
                'choices': list(VALID_MODULES),
                'summary': 'Modulo a correr (ausente -> los 3 en orden)',
            },
            'env': {
                'type': 'choice',
                'choices': list(VALID_ENVS),
                'default': 'dev',
                'summary': 'Entorno de deploy (NUNCA prod)',
            },
            'samples': {
                'type': 'int',
                'default': 5,
                'summary': 'Muestras por endpoint read-safe (modulo api)',
            },
            'aws_profile': {
                'type': 'string',
                'summary': 'Perfil AWS CLI para SSM/Neon (ej. tfs-dev)',
            },
            'keep_data': {
                'type': 'bool',
                'default': False,
                'summary': 'No limpiar los datos sinteticos creados',
            },
            'lambda': {
                'type': 'choice',
                'choices': list(VALID_LAMBDAS),
                'summary': 'Sub-filtro del modulo api (default: todos)',
            },
            'headed': {
                'type': 'bool',
                'default': False,
                'summary': 'Browser visible (admin/app, debug local)',
            },
            'verbose': {'type': 'bool', 'default': False, 'summary': 'Detalle'},
            'quiet': {'type': 'bool', 'default': False, 'summary': 'Silencia'},
        },
    }
