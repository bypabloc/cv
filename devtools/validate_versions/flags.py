"""Flag validation for validate_versions command."""

from utils.describe import ScriptDescribe
from utils.flags_to_dict import set_default_values
from utils.flags_to_dict import validate_allowed_flags


ALLOWED_FLAGS = [
    'json',
    'strict',
    'help',
]


def flag(flags_dict: dict) -> dict:
    """Validate and normalize flags for validate_versions command."""
    validate_allowed_flags(flags_dict, ALLOWED_FLAGS)

    return set_default_values(
        flags_dict,
        {
            'json': False,
            'strict': False,
        },
    )


def describe() -> ScriptDescribe:
    """Machine-readable inventory of validate_versions flags."""
    return {
        'name': 'validate_versions',
        'kind': 'monocommand',
        'summary': (
            'Valida que cada dep del monorepo este en latest stable y que las'
            ' versiones cross-package sean compatibles (Astro major uniforme,'
            ' Vite peer coherente, etc). Read-only.'
        ),
        'commands': [],
        'flags': {
            'json': {
                'type': 'bool',
                'default': False,
                'summary': 'Output como JSON estructurado en vez de tabla.',
            },
            'strict': {
                'type': 'bool',
                'default': False,
                'summary': (
                    'Exit 1 si hay packages outdated o incompatibilidades.'
                    ' Util para pre-merge gates.'
                ),
            },
        },
    }
