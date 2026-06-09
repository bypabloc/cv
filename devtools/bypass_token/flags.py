"""Validacion de flags del script bypass_token.

Subcommand-style:
  python devtools/run.py bypass_token keygen [--envs=dev] [--dry-run]
  python devtools/run.py bypass_token mint --env=dev [--private-key=...]
                                                      [--ttl=300]

keygen: genera un par Ed25519 por env, escribe la PRIVADA en
        docker/env/dev-cli/.{env} (local-only) y la PUBLICA en
        docker/env/server/.{env} (para sync a SSM).
mint:   firma un token efimero y lo imprime (para curl). La privada se
        pasa con --private-key (extraida con grep, ver env-files.md) o se
        resuelve de docker/env/dev-cli/.{env}.
"""

from __future__ import annotations

import sys
from typing import Any

from utils.describe import ScriptDescribe
from utils.flags_to_dict import set_default_values
from utils.flags_to_dict import validate_allowed_flags


VALID_COMMANDS = ('keygen', 'mint')

# Envs validos para generar/firmar. NUNCA prod: el bypass no existe en prod.
VALID_ENVS = ('dev',)

ALLOWED_FLAGS = [
    'command',
    'envs',
    'env',
    'private_key',
    'ttl',
    'dry_run',
    'help',
    'verbose',
]

_DEFAULTS: dict[str, Any] = {
    'envs': 'dev',
    'env': 'dev',
    'private_key': None,
    'ttl': 300,
    'dry_run': False,
    'verbose': False,
}

_COMMAND_SUMMARIES = {
    'keygen': (
        'Genera un par Ed25519 por env: PRIVADA -> dev-cli/.{env} '
        '(local-only), PUBLICA -> server/.{env} (sync SSM)'
    ),
    'mint': (
        'Firma un token de bypass efimero y lo imprime (uso en curl: '
        '-H "X-Turnstile-Bypass-Token: <token>")'
    ),
}

_COMMAND_FLAGS = {
    'keygen': ['envs', 'dry_run'],
    'mint': ['env', 'private_key', 'ttl'],
}


def _extract_positionals(flags_dict: dict[str, Any]) -> None:
    """Reconstruye el comando posicional desde sys.argv[2:].

    `flags_to_dict` solo parsea `--key=value`; el positional
    (`bypass_token keygen`) se pierde. Se toma el primero.
    """
    for arg in sys.argv[2:]:
        if arg == '--':
            break
        if not arg.startswith('--'):
            flags_dict.setdefault('command', arg)
            break


def _validate_command(flags_dict: dict[str, Any]) -> str:
    command = flags_dict.get('command')
    if not command:
        msg = (
            'Falta el comando posicional. Comandos validos: '
            f'{", ".join(VALID_COMMANDS)}.\n'
            'Ejemplo: python devtools/run.py bypass_token keygen '
            '--envs=dev'
        )
        raise ValueError(msg)
    if command not in VALID_COMMANDS:
        msg = (
            f'Comando invalido: {command!r}. '
            f'Validos: {", ".join(VALID_COMMANDS)}.'
        )
        raise ValueError(msg)
    return command


def _parse_envs(flags_dict: dict[str, Any]) -> list[str]:
    raw = flags_dict.get('envs')
    if not raw:
        return list(VALID_ENVS)
    items = (
        raw
        if isinstance(raw, list)
        else [e.strip() for e in str(raw).split(',') if e.strip()]
    )
    bad = [e for e in items if e not in VALID_ENVS]
    if bad:
        msg = (
            f'--envs invalido: {bad}. Validos: {", ".join(VALID_ENVS)} '
            '(NUNCA prod: el bypass no existe en prod).'
        )
        raise ValueError(msg)
    return items


def flag(flags_dict: dict[str, Any]) -> dict[str, Any]:
    """Valida y normaliza las flags de bypass_token."""
    _extract_positionals(flags_dict)
    validate_allowed_flags(flags_dict, ALLOWED_FLAGS)

    command = _validate_command(flags_dict)
    flags_dict = set_default_values(flags_dict, _DEFAULTS)
    flags_dict['command'] = command
    flags_dict['envs'] = _parse_envs(flags_dict)

    if command == 'mint':
        env = flags_dict.get('env')
        if env not in VALID_ENVS:
            msg = (
                f'mint: --env invalido {env!r}. '
                f'Validos: {", ".join(VALID_ENVS)}.'
            )
            raise ValueError(msg)
        flags_dict['ttl'] = int(flags_dict.get('ttl', 300))

    return flags_dict


def describe() -> ScriptDescribe:
    """Inventario machine-readable de comandos y flags de bypass_token."""
    return {
        'name': 'bypass_token',
        'kind': 'subcommand',
        'summary': (
            'Keygen + mint del token de bypass de Turnstile (Ed25519). '
            'keygen genera pares por env (privada local-only, publica a SSM); '
            'mint firma un token efimero para curl. NUNCA prod.'
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
            'envs': {
                'type': 'string',
                'summary': 'CSV de envs para keygen (default dev)',
                'required': False,
            },
            'env': {
                'type': 'string',
                'summary': 'Env para mint (dev; default dev)',
                'required': False,
            },
            'private_key': {
                'type': 'string',
                'summary': (
                    'Clave privada Ed25519 (base64) para mint. Si se omite, '
                    'se extrae de docker/env/dev-cli/.{env}.'
                ),
                'required': False,
            },
            'ttl': {
                'type': 'int',
                'summary': 'TTL del token en segundos (default 300)',
                'required': False,
            },
            'dry_run': {
                'type': 'bool',
                'summary': 'keygen: no escribe en disco',
                'required': False,
            },
        },
    }
