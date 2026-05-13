"""Reporter para validate_versions: tabla legible + JSON estructurado.

Color codes ANSI (mismos que ``upgrade_deps.reporter`` para consistencia):
    - verde   = ok (current == latest)
    - amarillo = outdated (current < latest)
    - rojo    = error/unknown / compat issue 'error'
    - cyan    = headers
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
import json

from validate_versions.compat_rules import CompatIssue
from validate_versions.resolver import ResolvedPackage


_GREEN = '\033[0;32m'
_YELLOW = '\033[1;33m'
_RED = '\033[0;31m'
_CYAN = '\033[0;36m'
_DIM = '\033[2m'
_RESET = '\033[0m'

_STATUS_COLORS = {
    'ok': _GREEN,
    'outdated': _YELLOW,
    'unknown': _RED,
    'ahead': _CYAN,
}


def _color(text: str, color: str) -> str:
    return f'{color}{text}{_RESET}'


def _group_by_workspace(
    packages: Iterable[ResolvedPackage],
) -> dict[str, list[ResolvedPackage]]:
    grouped: dict[str, list[ResolvedPackage]] = defaultdict(list)
    for p in packages:
        grouped[p.relpath].append(p)
    # Sort each group by name for deterministic output.
    for k in grouped:
        grouped[k].sort(key=lambda p: p.name.lower())
    return dict(grouped)


def _print_workspace_table(
    relpath: str, packages: list[ResolvedPackage]
) -> None:
    name_width = max((len(p.name) for p in packages), default=20)
    name_width = max(name_width, 30)
    version_width = 12

    print()
    print(_color(f'=== {relpath} ===', _CYAN))
    header = (
        f'  {"package":<{name_width}}  '
        f'{"current":<{version_width}}  '
        f'{"latest":<{version_width}}  status'
    )
    print(header)
    print('  ' + '-' * (len(header) - 2))

    for p in packages:
        latest_str = p.latest if p.latest is not None else '?'
        status_colored = _color(
            f'{p.status:>8}', _STATUS_COLORS.get(p.status, '')
        )
        print(
            f'  {p.name:<{name_width}}  '
            f'{p.current:<{version_width}}  '
            f'{latest_str:<{version_width}}  '
            f'{status_colored}'
        )


def _print_compat_issues(issues: list[CompatIssue]) -> None:
    print()
    print(_color('=' * 70, _CYAN))
    if not issues:
        print(_color('  Compatibilidad cross-package: 0 issues', _GREEN))
        print(_color('=' * 70, _CYAN))
        return

    print(
        _color(
            f'  Compatibilidad cross-package: {len(issues)} issue(s)', _YELLOW
        )
    )
    print(_color('=' * 70, _CYAN))
    for issue in issues:
        sev_color = _RED if issue.severity == 'error' else _YELLOW
        print()
        print(
            f'  [{_color(issue.severity.upper(), sev_color)}] '
            f'{_color(issue.rule, _CYAN)}'
        )
        print(f'    {issue.message}')
        for entity in issue.affected:
            print(f'    {_DIM}- {entity}{_RESET}')


def _print_summary(
    packages: list[ResolvedPackage], issues: list[CompatIssue]
) -> None:
    by_status: dict[str, int] = defaultdict(int)
    for p in packages:
        by_status[p.status] += 1

    errors = sum(1 for i in issues if i.severity == 'error')
    warnings = sum(1 for i in issues if i.severity == 'warning')

    print()
    print(_color('=' * 70, _CYAN))
    print('  Resumen')
    print(_color('=' * 70, _CYAN))
    print(
        f'  packages: {len(packages)} total | '
        f'{_color(str(by_status["ok"]), _GREEN)} ok | '
        f'{_color(str(by_status["outdated"]), _YELLOW)} outdated | '
        f'{_color(str(by_status["unknown"]), _RED)} unknown | '
        f'{_color(str(by_status["ahead"]), _CYAN)} ahead'
    )
    print(
        f'  compat: {_color(str(errors), _RED)} error(s) | '
        f'{_color(str(warnings), _YELLOW)} warning(s)'
    )


def print_human(
    packages: list[ResolvedPackage], issues: list[CompatIssue]
) -> None:
    """Imprime un reporte legible (tabla por workspace + compat)."""
    print()
    print(_color('=' * 70, _CYAN))
    print('  validate_versions [read-only]')
    print(_color('=' * 70, _CYAN))

    grouped = _group_by_workspace(packages)
    for relpath in sorted(grouped.keys()):
        _print_workspace_table(relpath, grouped[relpath])

    _print_compat_issues(issues)
    _print_summary(packages, issues)
    print()


def print_json(
    packages: list[ResolvedPackage], issues: list[CompatIssue]
) -> None:
    """Imprime el reporte como JSON estructurado (para CI/scripting)."""
    output = {
        'packages': [
            {
                'kind': p.kind,
                'workspace': p.workspace,
                'manifest': p.relpath,
                'name': p.name,
                'section': p.section,
                'current': p.current,
                'latest': p.latest,
                'status': p.status,
            }
            for p in packages
        ],
        'compat_issues': [
            {
                'rule': i.rule,
                'severity': i.severity,
                'message': i.message,
                'affected': i.affected,
            }
            for i in issues
        ],
        'summary': {
            'total_packages': len(packages),
            'ok': sum(1 for p in packages if p.status == 'ok'),
            'outdated': sum(1 for p in packages if p.status == 'outdated'),
            'unknown': sum(1 for p in packages if p.status == 'unknown'),
            'ahead': sum(1 for p in packages if p.status == 'ahead'),
            'compat_errors': sum(1 for i in issues if i.severity == 'error'),
            'compat_warnings': sum(
                1 for i in issues if i.severity == 'warning'
            ),
        },
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
