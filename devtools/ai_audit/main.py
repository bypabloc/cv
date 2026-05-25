"""ai_audit main: router de subcomandos.

Entry point invocado por devtools/run.py. Recibe el dict de flags ya
validado por flags.py.

Subcomandos:
- audit   (default): scrapea targets x tools y produce snapshot+report
- setup:  abre browser interactivo para guardar storageState
- report: re-renderiza Markdown desde un snapshot.json existente

Exit codes:
  0 -> exito (puede incluir PARTIAL / SKIPPED)
  1 -> >= 50% de los audits BLOCKED/ERROR
  2 -> error interno (config invalida, playwright no instalado)
"""

import asyncio
from pathlib import Path
import sys

from ai_audit import auth
from ai_audit import report


def main(flags: dict) -> int:
    """Router de subcomandos. flags ya validado por flags.py."""
    sub = flags['subcommand']
    if sub == 'setup':
        return _run_setup(flags)
    if sub == 'report':
        return _run_report(flags)
    return _run_audit(flags)


def _run_setup(flags: dict) -> int:
    """Setup interactivo o check-only de storageState."""
    tool = flags['tool']
    if flags.get('check_only', False):
        state = auth.check(tool)
        print(state.value)
        return 0 if state == auth.AuthState.VALID else 1

    login_url = auth.LOGIN_URLS.get(tool)
    if not login_url:
        print(
            f"setup: tool '{tool}' no requiere auth "
            '(isitagentready y aibotchecker son anonimas)',
        )
        return 2
    asyncio.run(auth.setup_interactive(tool, login_url))
    return 0


def _run_report(flags: dict) -> int:
    """Re-renderiza Markdown desde un snapshot existente."""
    snapshot_path = Path(flags['snapshot'])
    if not snapshot_path.exists():
        print(
            f'report: snapshot no existe: {snapshot_path}',
            file=sys.stderr,
        )
        return 2
    output_path = snapshot_path.parent / 'report.md'
    report.render_markdown(
        snapshot_path=snapshot_path,
        output_path=output_path,
    )
    print(f'rendered: {output_path}')
    return 0


def _run_audit(_flags: dict) -> int:
    """Pendiente: implementado en C9 (fase cli)."""
    msg = 'audit subcommand: pendiente — ver docs/specs/ai-audit-tool/06-fase-cli.md'
    raise NotImplementedError(msg)
