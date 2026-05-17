"""Flags for the ``harness_init`` devtools script.

Usage:
    python devtools/run.py harness_init
    python devtools/run.py harness_init --quiet

Wrapper sobre `.claude/hooks/harness-init.sh`. Verifica que el entorno del
arnes (Harness Engineering) este listo para empezar a trabajar:

  1. Archivos base existen (docs/CHECKPOINTS.md, docs/progress/...)
  2. Cualquier docs/<módulo>/feature_list.json existente es JSON válido y
     respeta `one_feature_at_a_time` (por módulo)
  3. Docker daemon corriendo + containers principales up
  4. Branch actual no es protegida (master/main/dev/stage)
  5. docs/progress/ esta limpio (sin temporales viejos)

Exit code 0 si OK, 1 si hay errores críticos.
"""

from typing import Any

from utils.describe import ScriptDescribe
from utils.flags_to_dict import set_default_values
from utils.flags_to_dict import validate_allowed_flags


ALLOWED_FLAGS = [
    'quiet',
    'help',
]


def flag(flags_dict: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize flags for ``harness_init``.

    Parameters
    ----------
    flags_dict : dict
        Raw flags dictionary from flags_to_dict.

    Returns
    -------
    dict
        Validated and normalized flags dictionary.
    """
    validate_allowed_flags(flags_dict, ALLOWED_FLAGS)

    return set_default_values(
        flags_dict,
        {
            'quiet': False,
        },
    )


def describe() -> ScriptDescribe:
    """Machine-readable inventory of harness_init flags."""
    return {
        'name': 'harness_init',
        'kind': 'monocommand',
        'summary': (
            'Gate BLOQUEANTE de inicio de sesión (Harness Engineering): '
            'verifica archivos base (docs/CHECKPOINTS.md, docs/progress/), '
            'feature_list.json por módulo, Docker, branch, docs/progress/ limpio'
        ),
        'commands': [],
        'flags': {
            'quiet': {
                'type': 'bool',
                'default': False,
                'summary': 'Suprime output [OK], solo muestra [WARN] y [FAIL]',
            },
        },
    }
