"""Build structured JSON reports from ruff check --output-format=json.

Categorizes violations by ruff code prefix and generates a summary
with per-file and per-category breakdowns.
"""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
import json
from typing import Any


# Ruff code prefix -> human-readable category
CATEGORY_MAP: dict[str, str] = {
    'E': 'style_errors',
    'W': 'style_warnings',
    'F': 'pyflakes_issues',
    'I': 'import_sorting',
    'UP': 'python_upgrade',
    'B': 'bugbear_issues',
    'C4': 'comprehensions',
    'SIM': 'simplifications',
    'PIE': 'pie_issues',
    'RET': 'return_issues',
    'N': 'naming_issues',
    'S': 'security_issues',
    'BLE': 'blind_except',
    'A': 'builtins_issues',
    'COM': 'comma_issues',
    'DJ': 'django_issues',
    'PT': 'pytest_issues',
    'ERA': 'commented_code',
    'T20': 'debug_prints',
    'FIX': 'fixme_comments',
    'G': 'logging_issues',
    'T10': 'debugger_issues',
    'ANN': 'annotation_issues',
    'Q': 'quote_issues',
    'RUF': 'ruff_specific',
    'SLF': 'private_access',
    'DTZ': 'datetime_issues',
    'PERF': 'performance_issues',
    'C90': 'complexity_issues',
    'TRY': 'exception_issues',
    'PLE': 'pylint_errors',
    'ISC': 'string_concat',
    'LOG': 'logging_issues',
    'ASYNC': 'async_issues',
    'FURB': 'refurb_issues',
    'RSE': 'raise_issues',
    'TC': 'type_checking',
    'FLY': 'flynt_issues',
}


def categorize_violation(code: str) -> str:
    """Map a ruff error code to its category.

    Matches longest prefix first (e.g. 'C90' before 'C4').
    """
    for prefix in sorted(CATEGORY_MAP, key=len, reverse=True):
        if code.startswith(prefix):
            return CATEGORY_MAP[prefix]
    return 'unknown_issues'


def build_report(
    ruff_json: list[dict[str, Any]],
    *,
    files_checked: list[str],
    strip_prefix: str = '',
) -> dict[str, Any]:
    """Build a categorized report from ruff JSON output.

    Parameters
    ----------
    ruff_json : list[dict]
        Raw ruff check --output-format=json output (list of violations).
    files_checked : list[str]
        Files that were checked (for total_files count).
    strip_prefix : str
        Prefix to strip from filenames (e.g. '/app/server/').

    Returns
    -------
    dict
        Structured report with summary, files, and categories.
    """
    files: dict[str, dict[str, Any]] = {}
    categories: dict[str, dict[str, Any]] = {}

    for violation in ruff_json:
        filename = violation.get('filename', '')
        if strip_prefix and filename.startswith(strip_prefix):
            filename = filename[len(strip_prefix) :]

        code = violation.get('code', '')
        category = categorize_violation(code)

        entry = {
            'code': code,
            'message': violation.get('message', ''),
            'line': violation.get('location', {}).get('row'),
            'column': violation.get('location', {}).get('column'),
            'category': category,
            'url': violation.get('url', ''),
        }

        if filename not in files:
            files[filename] = {'violations': [], 'violation_count': 0}
        files[filename]['violations'].append(entry)
        files[filename]['violation_count'] += 1

        if category not in categories:
            categories[category] = {'count': 0, 'files': set()}
        categories[category]['count'] += 1
        categories[category]['files'].add(filename)

    # Convert sets to sorted lists for JSON serialization
    for cat_data in categories.values():
        cat_data['files'] = sorted(cat_data['files'])

    total_violations = sum(f['violation_count'] for f in files.values())

    return {
        'summary': {
            'total_files': len(files_checked),
            'files_with_errors': len(files),
            'total_violations': total_violations,
        },
        'files': files,
        'categories': categories,
        'metadata': {
            'timestamp': datetime.now(tz=UTC).isoformat(),
        },
    }


def format_report(report: dict[str, Any]) -> str:
    """Serialize report to indented JSON string."""
    return json.dumps(report, indent=2, ensure_ascii=False)
