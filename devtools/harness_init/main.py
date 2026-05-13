"""Wrapper Python sobre ``.claude/hooks/harness-init.sh``.

Permite invocar el gate de inicio de sesion via la API unificada de devtools::

    python devtools/run.py harness_init
    python devtools/run.py harness_init --quiet

Internamente delega al script bash en ``.claude/hooks/harness-init.sh`` (la
fuente de verdad de la logica del gate). Este wrapper existe para que el gate
sea descubrible via ``python devtools/run.py --list-scripts`` y siga la misma
convencion que ``test_runner``, ``scan``, ``verify``, ``upgrade_deps``.

Salida del shell hook va a stderr (mensajes coloreados [OK]/[WARN]/[FAIL]).
Exit code 0 si todo OK; 1 si hay errores criticos.
"""

import logging
from pathlib import Path
import subprocess
from typing import Any


logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_HOOK_SCRIPT = _PROJECT_ROOT / '.claude' / 'hooks' / 'harness-init.sh'


def main(flags: dict[str, Any]) -> int:
    """Entry point invoked by ``devtools/run.py``.

    Parameters
    ----------
    flags : dict
        Validated flags dict (see ``flags.py``).

    Returns
    -------
    int
        Exit code from the shell hook (0 = OK, 1 = critical failure).
    """
    if not _HOOK_SCRIPT.exists():
        logger.error('No se encontro %s', _HOOK_SCRIPT)
        return 1

    if not _HOOK_SCRIPT.stat().st_mode & 0o111:
        logger.error('%s no es ejecutable (chmod +x falta)', _HOOK_SCRIPT)
        return 1

    env = None
    if flags.get('quiet'):
        import os

        env = os.environ.copy()
        env['HARNESS_INIT_QUIET'] = '1'

    try:
        result = subprocess.run(  # noqa: S603
            [str(_HOOK_SCRIPT)],
            check=False,
            cwd=_PROJECT_ROOT,
            env=env,
        )
    except OSError:
        logger.exception('No se pudo ejecutar %s', _HOOK_SCRIPT)
        return 1

    return result.returncode
