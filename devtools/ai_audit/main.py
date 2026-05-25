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


def main(flags: dict) -> int:
    """Router de subcomandos. flags ya validado por flags.py."""
    sub = flags['subcommand']
    if sub == 'setup':
        return _run_setup(flags)
    if sub == 'report':
        return _run_report(flags)
    return _run_audit(flags)


def _run_setup(_flags: dict) -> int:
    """Pendiente: implementado en C3 (fase auth)."""
    msg = 'setup subcommand: pendiente — ver docs/specs/ai-audit-tool/03-fase-auth.md'
    raise NotImplementedError(msg)


def _run_report(_flags: dict) -> int:
    """Pendiente: implementado en C8 (fase report)."""
    msg = 'report subcommand: pendiente — ver docs/specs/ai-audit-tool/05-fase-report.md'
    raise NotImplementedError(msg)


def _run_audit(_flags: dict) -> int:
    """Pendiente: implementado en C9 (fase cli)."""
    msg = 'audit subcommand: pendiente — ver docs/specs/ai-audit-tool/06-fase-cli.md'
    raise NotImplementedError(msg)
