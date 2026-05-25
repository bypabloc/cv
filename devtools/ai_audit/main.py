"""ai_audit main: router de subcomandos.

Entry point invocado por devtools/run.py. Recibe el dict de flags ya
validado por flags.py.

Subcomandos:
- audit   (default): scrapea targets x tools y produce snapshot+report
- report: re-renderiza Markdown desde un snapshot.json existente

Nota: el subcomando `setup` fue eliminado cuando se descontinuo el
soporte de storageState (las tools activas son anonimas o usan API
key gratuita resuelta directo desde docker/env/dev-cli/.{env}).

Exit codes:
  0 -> exito (puede incluir PARTIAL / SKIPPED)
  1 -> >= 50% de los audits BLOCKED/ERROR
  2 -> error interno (config invalida, playwright no instalado)
"""

import asyncio
from datetime import UTC
from datetime import datetime
import os
from pathlib import Path
import sys

from ai_audit import catalog
from ai_audit import report
from ai_audit import scraper
from ai_audit.tools.base import Status
from shared.paths import PROJECT_ROOT


def main(flags: dict) -> int:
    """Router de subcomandos. flags ya validado por flags.py."""
    sub = flags['subcommand']
    if sub == 'report':
        return _run_report(flags)
    return _run_audit(flags)


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


def _run_audit(flags: dict) -> int:
    """Comando default: scrapea targets x tools y produce snapshot+report."""
    scraper.auto_install_chromium()

    # PSI_ENV permite que LighthousePsi resuelva PSI_API_KEY desde
    # docker/env/dev-cli/.{env} correcto en runtime.
    os.environ['PSI_ENV'] = flags['env']

    targets = catalog.resolve_targets(
        env=flags['env'],
        niches=flags['niches'],
        targets_override=flags.get('targets') or None,
    )
    tool_names: list[str] = flags['tools']

    if not targets or not tool_names:
        print(
            'ERROR: no targets o tools resueltos',
            file=sys.stderr,
        )
        return 2

    ran_at = datetime.now(UTC)
    run_dir = (
        PROJECT_ROOT / 'tmp' / 'ai-audit' / ran_at.strftime('%Y-%m-%dT%H-%M-%S')
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = run_dir / 'snapshot.json'
    report_path = run_dir / 'report.md'

    print(
        f'[ai_audit] env={flags["env"]} '
        f'targets={len(targets)} x tools={len(tool_names)} '
        f'= {len(targets) * len(tool_names)} audits',
    )

    results = asyncio.run(
        scraper.run_audit(
            targets=targets,
            tool_names=tool_names,
            headless=flags.get('headless', True),
        ),
    )

    report.write_snapshot(
        results=results,
        env=flags['env'],
        ran_at=ran_at,
        path=snapshot_path,
    )
    report.render_markdown(
        snapshot_path=snapshot_path,
        output_path=report_path,
    )

    _print_summary(results, report_path)
    return scraper.resolve_exit_code(results)


def _print_summary(results: list, report_path: Path) -> None:
    """Imprime tabla resumen + path al reporte."""
    by_status: dict[str, int] = {s.value: 0 for s in Status}
    for r in results:
        by_status[r.status.value] += 1
    summary = '  '.join(f'{k}: {v}' for k, v in by_status.items())
    print(f'[ai_audit] {summary}')
    print(f'[ai_audit] report: {report_path}')
