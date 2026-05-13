"""``weak_assertion`` script entry point.

Detecta asserts vagos en archivos de test Python via AST. Política:
``.claude/rules/ai-testing-independence.md``.

Modos:
- ``--files=path1,path2`` - lista explicita
- ``--git-mode=staged|unmerged|modified`` - toma archivos de git

Exit codes:
    0 - sin findings
    1 - al menos un weak assertion (bloqueante)
"""
from __future__ import annotations

from pathlib import Path
import sys
from typing import Any


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def main(flags: dict[str, Any]) -> int:
    """CLI entry point. Llamado desde ``devtools/run.py``.

    Args:
        flags: dict de flags ya validados por ``flags.py``.

    Returns:
        Exit code (0 = ok, 1 = findings).
    """
    sys.path.insert(0, str(_PROJECT_ROOT / 'devtools'))
    from shared.weak_assertion import format_findings
    from shared.weak_assertion import scan_files

    files = _resolve_files(flags)
    if not files:
        return 0

    findings = scan_files(files, project_root=_PROJECT_ROOT)
    if not findings:
        return 0

    if flags.get('quiet'):
        n = len(findings)
        plural = 's' if n != 1 else ''
        print(
            f'[weak_assertion] {n} weak assert{plural} detectado{plural}',
            file=sys.stderr,
        )
    else:
        print(format_findings(findings), file=sys.stderr)

    return 1


def _resolve_files(flags: dict[str, Any]) -> list[str]:
    """Resuelve la lista de archivos a escanear (--files vs --git-mode)."""
    git_mode = flags.get('git_mode')
    explicit = flags.get('files') or []

    if git_mode:
        sys.path.insert(0, str(_PROJECT_ROOT / 'devtools'))
        from shared.scan_helper import files_changed

        return files_changed(git_mode=git_mode)

    return explicit


if __name__ == '__main__':
    # Permite ejecución directa: python devtools/weak_assertion/main.py ...
    sys.path.insert(0, str(_PROJECT_ROOT / 'devtools'))
    from weak_assertion.flags import get_flags

    raw_flags = get_flags(sys.argv[1:])
    if raw_flags.get('help'):
        print(__doc__)
        sys.exit(0)
    sys.exit(main(raw_flags))
