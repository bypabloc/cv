"""Report: snapshot JSON inmutable + Markdown legible.

write_snapshot escribe el JSON crudo. render_markdown produce el
reporte con tabla comparativa por niche + top 5 fixes priorizados
(severity DESC, reach DESC).

prioritize_fixes ordena fixes para mostrar primero los de mas
impacto. Es pure — testeable sin red.
"""

from dataclasses import asdict
from datetime import UTC
from datetime import datetime
import json
from pathlib import Path

from ai_audit.tools.base import Fix
from ai_audit.tools.base import Severity
from ai_audit.tools.base import Status
from ai_audit.tools.base import ToolResult


# Max score por tool para normalizar a 0-100 en la tabla resumen.
TOOL_SCORE_MAX: dict[str, int] = {
    'isitagentready': 5,
    'aibotchecker': 100,
    'ahrefs': 5,
    'semrush': 100,
}

SEVERITY_WEIGHT: dict[Severity, int] = {
    Severity.HIGH: 3,
    Severity.MEDIUM: 2,
    Severity.LOW: 1,
}


def write_snapshot(
    *,
    results: list[ToolResult],
    env: str,
    ran_at: datetime,
    path: Path,
    interrupted: bool = False,
) -> None:
    """Escribe snapshot.json. Sobrescribe si existe."""
    payload = {
        'ranAt': ran_at.astimezone(UTC).isoformat().replace('+00:00', 'Z'),
        'env': env,
        'targets': sorted({r.target for r in results}),
        'tools': sorted({r.tool for r in results}),
        'interrupted': interrupted,
        'results': [_serialize_result(r) for r in results],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, default=str),
        encoding='utf-8',
    )


def render_markdown(
    *,
    snapshot_path: Path,
    output_path: Path,
) -> None:
    """Renderiza Markdown desde un snapshot.json."""
    snapshot = json.loads(snapshot_path.read_text(encoding='utf-8'))
    results = [_deserialize_result(r) for r in snapshot['results']]

    lines: list[str] = []
    lines.append(
        f'# AI readiness audit — {snapshot["env"]} — {snapshot["ranAt"]}',
    )
    lines.append('')
    lines.append(_render_summary_table(results, snapshot['tools']))
    lines.append('')
    lines.append(_render_top_fixes(results))
    lines.append('')
    lines.append(_render_blocked_section(results))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')


def prioritize_fixes(
    results: list[ToolResult],
    top: int = 5,
) -> list[Fix]:
    """Ordena fixes por severity DESC, luego reach DESC. Top N."""
    all_fixes: list[Fix] = []
    for r in results:
        all_fixes.extend(r.fixes)
    all_fixes.sort(
        key=lambda f: (SEVERITY_WEIGHT[f.severity], f.reach),
        reverse=True,
    )
    return all_fixes[:top]


def _serialize_result(r: ToolResult) -> dict:
    """ToolResult -> dict JSON-safe."""
    data = asdict(r)
    data['status'] = r.status.value
    data['fixes'] = [
        {**asdict(f), 'severity': f.severity.value} for f in r.fixes
    ]
    if r.raw_log_path is not None:
        data['raw_log_path'] = str(r.raw_log_path)
    return data


def _deserialize_result(data: dict) -> ToolResult:
    """dict JSON -> ToolResult."""
    fixes = tuple(
        Fix(
            severity=Severity(f['severity']),
            category=f['category'],
            issue=f['issue'],
            fix=f['fix'],
            file=f.get('file'),
            reach=f.get('reach', 1),
        )
        for f in data.get('fixes', [])
    )
    raw = data.get('raw_log_path')
    return ToolResult(
        tool=data['tool'],
        target=data['target'],
        status=Status(data['status']),
        score=data.get('score'),
        categories=data.get('categories', {}),
        fixes=fixes,
        raw_log_path=Path(raw) if raw else None,
        duration_ms=data.get('duration_ms', 0),
        skipped_reason=data.get('skipped_reason'),
        error_message=data.get('error_message'),
    )


def _render_summary_table(
    results: list[ToolResult],
    tools: list[str],
) -> str:
    by_target: dict[str, dict[str, ToolResult]] = {}
    for r in results:
        by_target.setdefault(r.target, {})[r.tool] = r

    header = ['Target', *tools, 'Avg']
    lines = ['## Resumen por target', '']
    lines.append('| ' + ' | '.join(header) + ' |')
    lines.append('|' + '|'.join(['---'] * len(header)) + '|')

    for target in sorted(by_target):
        row = [target]
        normalized: list[int] = []
        for tool in tools:
            res = by_target[target].get(tool)
            if res is None or res.score is None:
                row.append('—')
                continue
            tool_max = TOOL_SCORE_MAX.get(tool, 100)
            norm = int(res.score / tool_max * 100)
            row.append(f'{res.score}/{tool_max}')
            normalized.append(norm)
        if normalized:
            row.append(str(sum(normalized) // len(normalized)))
        else:
            row.append('—')
        lines.append('| ' + ' | '.join(row) + ' |')

    return '\n'.join(lines)


def _render_top_fixes(results: list[ToolResult]) -> str:
    fixes = prioritize_fixes(results, top=5)
    lines = ['## Top 5 fixes priorizados', '']
    if not fixes:
        lines.append('No hay fixes pendientes.')
        return '\n'.join(lines)

    for i, fix in enumerate(fixes, start=1):
        lines.append(f'### #{i} [{fix.severity.value.upper()}] {fix.issue}')
        lines.append(f'- **Categoria**: {fix.category}')
        lines.append(f'- **Reach**: {fix.reach}')
        lines.append(f'- **Fix**: {fix.fix}')
        if fix.file:
            lines.append(f'- **Archivo sugerido**: {fix.file}')
        lines.append('')

    return '\n'.join(lines).rstrip()


def _render_blocked_section(results: list[ToolResult]) -> str:
    bad = [
        r
        for r in results
        if r.status in (Status.BLOCKED, Status.ERROR, Status.SKIPPED)
    ]
    if not bad:
        return ''
    lines = ['## Audits BLOCKED / ERROR / SKIPPED', '']
    lines.append('| Target | Tool | Status | Razon |')
    lines.append('|---|---|---|---|')
    for r in bad:
        reason = r.skipped_reason or r.error_message or '-'
        lines.append(
            f'| {r.target} | {r.tool} | {r.status.value} | {reason} |',
        )
    return '\n'.join(lines)
