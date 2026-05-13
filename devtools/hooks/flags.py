"""Flags for the ``hooks`` devtools script.

Usage:
    python devtools/run.py hooks --type=pre-commit
    python devtools/run.py hooks --type=pre-push

This script orchestrates git hook validations. The .git-hooks/pre-commit and
.git-hooks/pre-push files are thin wrappers that simply delegate here.
"""

from typing import Any

from utils.describe import ScriptDescribe


_VALID_TYPES = ('pre-commit', 'pre-push')


def flag(flags_dict: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize flags for the ``hooks`` script.

    Required:
        --type=<pre-commit|pre-push>
    """
    hook_type = flags_dict.get('type')
    if hook_type not in _VALID_TYPES:
        msg = (
            f'--type es requerido y debe ser uno de {_VALID_TYPES}. '
            f'Recibido: {hook_type!r}'
        )
        raise ValueError(msg)

    return {'type': hook_type}


def describe() -> ScriptDescribe:
    """Machine-readable inventory of hooks flags."""
    return {
        'name': 'hooks',
        'kind': 'monocommand',
        'summary': 'Orquesta validaciones de git hooks (delegado por .git-hooks/)',
        'commands': [],
        'flags': {
            'type': {
                'type': 'choice',
                'choices': list(_VALID_TYPES),
                'required': True,
                'summary': 'Tipo de hook a ejecutar',
            },
        },
    }
