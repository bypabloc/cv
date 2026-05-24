"""Flag validation for github_sync command."""

from utils.describe import ScriptDescribe
from utils.flags_to_dict import set_default_values
from utils.flags_to_dict import validate_allowed_flags


VALID_ENVS = ('dev', 'stage', 'prod')

ALLOWED_FLAGS = [
    'env',
    'dry_run',
    'keys',
    'create_env',
    'help',
]


def flag(flags_dict: dict) -> dict:
    """Validate and normalize flags for github_sync command."""
    validate_allowed_flags(flags_dict, ALLOWED_FLAGS)

    normalized = set_default_values(
        flags_dict,
        {
            'dry_run': False,
            'keys': '',
            'create_env': False,
        },
    )

    env = normalized.get('env')
    if not env:
        raise ValueError(
            '--env requerido. Valores validos: ' + ', '.join(VALID_ENVS),
        )
    if env not in VALID_ENVS:
        raise ValueError(
            f'--env="{env}" invalido. Valores validos: '
            + ', '.join(VALID_ENVS),
        )
    return normalized


def describe() -> ScriptDescribe:
    """Machine-readable inventory of github_sync flags."""
    return {
        'name': 'github_sync',
        'kind': 'monocommand',
        'summary': (
            'Sincroniza docker/env/client/.{env} a GitHub Environment Variables'
        ),
        'commands': [],
        'flags': {
            'env': {
                'type': 'string',
                'default': None,
                'summary': 'Env destino: dev | stage | prod',
            },
            'dry_run': {
                'type': 'bool',
                'default': False,
                'summary': 'Reporta SKIP/PUSH/CREATE/MISSING sin ejecutar set',
            },
            'keys': {
                'type': 'string',
                'default': '',
                'summary': 'Subset de keys a sincronizar (csv). Vacio = todas',
            },
            'create_env': {
                'type': 'bool',
                'default': False,
                'summary': 'Si el GH Environment no existe, lo crea',
            },
        },
    }
