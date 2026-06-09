"""Flag validation for rotate_secrets script.

Subcommand-style script: each service (turnstile, ...) is one subcommand
and declares the credentials it requires as explicit flags. Credentials
are NEVER read from env files automatically — the user passes them via
flags so the script remains agnostic to where they live.
"""

import sys
from typing import Any

from utils.describe import ScriptDescribe
from utils.flags_to_dict import set_default_values
from utils.flags_to_dict import validate_allowed_flags


VALID_SERVICES = [
    'turnstile',
]

# Credenciales requeridas por cada servicio. Validacion enforced en flag().
_REQUIRED_CREDS = {
    'turnstile': ['cloudflare_api_token', 'cloudflare_account_id'],
}

ALLOWED_FLAGS = [
    # Comando posicional (resuelto en _extract_positionals)
    'command',
    'subcommands',
    # Comportamiento general
    'dry_run',
    'force',  # crear widget aunque ya exista uno con el mismo nombre
    'rotate',  # rotar secret aunque el widget ya exista
    'envs',  # subset de envs a escribir (default: todos)
    # Credenciales por servicio (cada subcommand consume las suyas)
    'cloudflare_api_token',
    'cloudflare_account_id',
    # Cross-cutting
    'help',
    'verbose',
]

_DEFAULTS = {
    'dry_run': False,
    'force': False,
    'rotate': False,
    'verbose': False,
}


_COMMAND_SUMMARIES = {
    'turnstile': (
        'Configura y/o rota Cloudflare Turnstile widgets por entorno y '
        'escribe sitekey + secret en docker/env/{server,client}/.{env}'
    ),
}

_COMMAND_FLAGS = {
    'turnstile': [
        'cloudflare_api_token',
        'cloudflare_account_id',
        'dry_run',
        'force',
        'rotate',
        'envs',
    ],
}


def _validate_command(flags_dict: dict) -> str:
    command = flags_dict.get('command')
    if not command:
        msg = (
            'Falta el subcomando posicional. Servicios validos: '
            f'{", ".join(VALID_SERVICES)}.\n'
            'Ejemplo: python devtools/run.py rotate_secrets turnstile \\\n'
            '  --cloudflare-api-token=$(grep -m1 ^CLOUDFLARE_API_TOKEN= '
            'docker/env/dev-cli/.prod | cut -d= -f2-) \\\n'
            '  --cloudflare-account-id=$(grep -m1 ^CLOUDFLARE_ACCOUNT_ID= '
            'docker/env/dev-cli/.prod | cut -d= -f2-)'
        )
        raise ValueError(msg)
    if command not in VALID_SERVICES:
        msg = (
            f'Servicio invalido: {command!r}. '
            f'Validos: {", ".join(VALID_SERVICES)}.'
        )
        raise ValueError(msg)
    return command


def _validate_required_creds(command: str, flags_dict: dict) -> None:
    required = _REQUIRED_CREDS.get(command, [])
    missing = [f for f in required if not flags_dict.get(f)]
    if missing:
        flag_args = ', '.join(f'--{f.replace("_", "-")}' for f in missing)
        msg = (
            f'Credenciales faltantes para {command}: {flag_args}.\n'
            f'Pasa cada credencial como flag (NO leas el .env completo, '
            f'extrae solo la key con bash: '
            f'`grep -m1 ^KEY= docker/env/dev-cli/.prod | cut -d= -f2-`).'
        )
        raise ValueError(msg)


def _parse_envs(flags_dict: dict) -> list[str]:
    valid_envs = ['local', 'test', 'dev', 'prod']
    raw = flags_dict.get('envs')
    if not raw:
        return valid_envs
    if isinstance(raw, list):
        items = raw
    else:
        items = [e.strip() for e in str(raw).split(',') if e.strip()]
    bad = [e for e in items if e not in valid_envs]
    if bad:
        msg = f'--envs invalido: {bad}. Validos: {", ".join(valid_envs)}.'
        raise ValueError(msg)
    return items


def _extract_positionals(flags_dict: dict[str, Any]) -> None:
    """Extract positional args from sys.argv into flags_dict['command'].

    `flags_to_dict` solo parsea `--key=value`; los positionals
    (`rotate_secrets turnstile`) se pierden. Este helper los reconstruye
    desde `sys.argv[2:]` saltando el nombre del script. Solo se toma el
    primer positional (el resto es ignorado: este script es de un solo
    nivel de subcomando).
    """
    raw_args = sys.argv[2:]
    for arg in raw_args:
        if arg == '--':
            break
        if not arg.startswith('--'):
            flags_dict.setdefault('command', arg)
            break


def flag(flags_dict: dict) -> dict:
    """Validate and normalize flags for rotate_secrets script."""
    _extract_positionals(flags_dict)
    validate_allowed_flags(flags_dict, ALLOWED_FLAGS)

    command = _validate_command(flags_dict)
    _validate_required_creds(command, flags_dict)

    flags_dict = set_default_values(flags_dict, _DEFAULTS)
    flags_dict['envs'] = _parse_envs(flags_dict)

    return flags_dict


def describe() -> ScriptDescribe:
    """Machine-readable inventory of rotate_secrets commands and flags."""
    return {
        'name': 'rotate_secrets',
        'kind': 'subcommand',
        'summary': (
            'Rota o configura credenciales de servicios externos (Cloudflare '
            'Turnstile, ...) y las escribe en docker/env/*/.{env}. Cada '
            'servicio exige sus credenciales por flags explicitas.'
        ),
        'commands': [
            {
                'name': cmd,
                'summary': _COMMAND_SUMMARIES.get(cmd, ''),
                'flags': _COMMAND_FLAGS.get(cmd, []),
                'destructive': False,
            }
            for cmd in VALID_SERVICES
        ],
        'flags': {
            'cloudflare_api_token': {
                'type': 'string',
                'summary': (
                    'API token de Cloudflare con scopes Turnstile:Edit '
                    '(requerido por subcomando `turnstile`)'
                ),
                'required': False,
            },
            'cloudflare_account_id': {
                'type': 'string',
                'summary': (
                    'Account ID de Cloudflare '
                    '(requerido por subcomando `turnstile`)'
                ),
                'required': False,
            },
            'envs': {
                'type': 'list',
                'summary': (
                    'Subset de envs a actualizar '
                    '(local,test,dev,prod). Default: todos.'
                ),
            },
            'dry_run': {
                'type': 'bool',
                'default': False,
                'summary': (
                    'No escribe en disco ni hace cambios en Cloudflare; '
                    'solo imprime lo que haria'
                ),
            },
            'force': {
                'type': 'bool',
                'default': False,
                'summary': (
                    'Crear widget nuevo aunque ya exista uno con el mismo '
                    'nombre (subcomando `turnstile`)'
                ),
            },
            'rotate': {
                'type': 'bool',
                'default': False,
                'summary': (
                    'Rotar el secret de un widget existente '
                    '(subcomando `turnstile`)'
                ),
            },
        },
    }
