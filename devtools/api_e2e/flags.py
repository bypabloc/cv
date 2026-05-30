"""Validacion de flags del script api_e2e (monocommand).

Flags:
  --env=dev|stage      entorno de DEPLOY (NUNCA prod; default dev)
  --lambda=<name>      filtra a un Lambda (cv|contact_form|tracking_pixel|
                       auth|users); default todos
  --samples=N          muestras por endpoint read-safe (default 5)
  --aws-profile=<X>    perfil AWS CLI para SSM/Neon (default: shell)
  --keep-data          NO limpiar los datos sinteticos creados en Neon
  --verbose / --quiet
"""

from __future__ import annotations

import os
import sys
from typing import Any


sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config import VALID_ENVS
from utils.describe import ScriptDescribe
from utils.flags_to_dict import set_default_values
from utils.flags_to_dict import validate_allowed_flags


VALID_LAMBDAS = ('cv', 'contact_form', 'tracking_pixel', 'auth', 'users')

ALLOWED_FLAGS = [
    'env',
    'lambda',
    'samples',
    'aws_profile',
    'keep_data',
    'verbose',
    'quiet',
    'help',
]

DEFAULTS: dict[str, Any] = {
    'env': 'dev',
    'lambda': None,
    'samples': 5,
    'aws_profile': None,
    'keep_data': False,
    'verbose': False,
    'quiet': False,
}


def flag(flags_dict: dict[str, Any]) -> dict[str, Any]:
    """Valida y normaliza las flags de api_e2e."""
    validate_allowed_flags(flags_dict, ALLOWED_FLAGS)
    flags_dict = set_default_values(flags_dict, DEFAULTS)

    env = flags_dict.get('env')
    if env not in VALID_ENVS:
        raise ValueError(
            f"--env invalido: '{env}'. api_e2e MUTA el entorno y lee Neon: "
            f'solo {", ".join(VALID_ENVS)} (NUNCA prod).',
        )

    lam = flags_dict.get('lambda')
    if lam is not None and lam not in VALID_LAMBDAS:
        raise ValueError(
            f"--lambda invalido: '{lam}'. "
            f'Validos: {", ".join(VALID_LAMBDAS)}',
        )

    samples = flags_dict.get('samples')
    if not isinstance(samples, int):
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
    """Inventario machine-readable de las flags de api_e2e."""
    return {
        'name': 'api_e2e',
        'kind': 'monocommand',
        'summary': (
            'Tests E2E reales (HTTP) contra el backend desplegado '
            '(dev|stage): flujos de exito + errores por Lambda, con '
            'tiempos de respuesta'
        ),
        'commands': [],
        'flags': {
            'env': {
                'type': 'choice',
                'choices': list(VALID_ENVS),
                'default': 'dev',
                'summary': 'Entorno de deploy (NUNCA prod)',
            },
            'lambda': {
                'type': 'choice',
                'choices': list(VALID_LAMBDAS),
                'summary': 'Filtra a un Lambda (default: todos)',
            },
            'samples': {
                'type': 'int',
                'default': 5,
                'summary': 'Muestras por endpoint read-safe',
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
            'verbose': {'type': 'bool', 'default': False, 'summary': 'Detalle'},
            'quiet': {'type': 'bool', 'default': False, 'summary': 'Silencia'},
        },
    }
