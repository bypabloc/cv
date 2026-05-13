"""Flag validation for upgrade_deps command."""

from utils.describe import ScriptDescribe
from utils.flags_to_dict import set_default_values
from utils.flags_to_dict import validate_allowed_flags


ALLOWED_FLAGS = [
    'dry_run',
    'help',
]


def flag(flags_dict: dict) -> dict:
    """Validate and normalize flags for upgrade_deps command."""
    validate_allowed_flags(flags_dict, ALLOWED_FLAGS)

    return set_default_values(
        flags_dict,
        {
            'dry_run': False,
        },
    )


def describe() -> ScriptDescribe:
    """Machine-readable inventory of upgrade_deps flags."""
    return {
        'name': 'upgrade_deps',
        'kind': 'monocommand',
        'summary': 'Bumpea dependencias (Python via uv, JS via pnpm)',
        'commands': [],
        'flags': {
            'dry_run': {
                'type': 'bool',
                'default': False,
                'summary': 'Imprime upgrades disponibles sin escribir',
            },
        },
    }
