"""Flag validation for sync_secrets command."""

from utils.describe import ScriptDescribe
from utils.flags_to_dict import set_default_values
from utils.flags_to_dict import validate_allowed_flags


VALID_ENVS = ('local', 'dev', 'stage', 'prod')
VALID_CATEGORIES = ('all', 'client', 'server', 'dev-cli')

ALLOWED_FLAGS = [
    'env',
    'category',
    'dry_run',
    'keys',
    'create_env',
    'aws_profile',
    'help',
]


def flag(flags_dict: dict) -> dict:
    """Validate and normalize flags for sync_secrets command."""
    validate_allowed_flags(flags_dict, ALLOWED_FLAGS)

    normalized = set_default_values(
        flags_dict,
        {
            'category': 'all',
            'dry_run': False,
            'keys': '',
            'create_env': False,
            'aws_profile': '',
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

    category = normalized['category']
    if category not in VALID_CATEGORIES:
        raise ValueError(
            f'--category="{category}" invalido. Valores validos: '
            + ', '.join(VALID_CATEGORIES),
        )

    return normalized


def describe() -> ScriptDescribe:
    """Machine-readable inventory of sync_secrets flags."""
    return {
        'name': 'sync_secrets',
        'kind': 'monocommand',
        'summary': (
            'Sincroniza docker/env/{client,server,dev-cli}/.{env} a sus '
            'destinos (GH Variables / AWS SSM / local-only)'
        ),
        'commands': [],
        'flags': {
            'env': {
                'type': 'string',
                'default': None,
                'summary': 'Env destino: local | dev | stage | prod',
            },
            'category': {
                'type': 'string',
                'default': 'all',
                'summary': 'Subset: all | client | server | dev-cli',
            },
            'dry_run': {
                'type': 'bool',
                'default': False,
                'summary': 'Reporta acciones sin ejecutar',
            },
            'keys': {
                'type': 'string',
                'default': '',
                'summary': 'Subset de keys a sincronizar (csv)',
            },
            'create_env': {
                'type': 'bool',
                'default': False,
                'summary': 'Crea GH Environment si no existe (solo client)',
            },
            'aws_profile': {
                'type': 'string',
                'default': '',
                'summary': 'AWS profile para server (--aws-profile=tfs-dev)',
            },
        },
    }
