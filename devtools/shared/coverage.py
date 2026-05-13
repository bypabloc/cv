"""Per-file coverage verification for server (pytest-cov) and frontend (v8).

Returns structured results so callers (hooks, test_runner) can format output
according to their own conventions.

Exclusiones globales: archivos sin valor para coverage 80% (no contienen
lógica de negocio que requiera tests unitarios).
"""

import json
from pathlib import Path


COVERAGE_THRESHOLD = 80


# Path patterns excluidos del enforcement de coverage 80% (server-side).
# Estos archivos no contienen lógica de negocio que requiera tests unitarios.
SERVER_COVERAGE_EXCLUDES: tuple[str, ...] = (
    '__init__.py',  # Re-exports
    '/enums/',  # TextChoices/IntegerChoices declarativas
    '/enums.py',
    '/constants.py',  # UPPER_SNAKE_CASE constantes estáticas
    '/migrations/',  # Auto-generadas por Django
    '/apps.py',  # AppConfig declarativa (1-2 lineas utiles)
    '/admin/',  # Admin classes (testeadas via integration)
    '/serializers/',  # Serializers DRF (testeados via integration views)
    '/urls.py',  # URL patterns declarativos
    '/views/',  # Views thin (testeados via integration)
    '/config/settings/',  # Django settings (declarativas)
    '/config/urls.py',
    '/config/wsgi.py',
    '/config/asgi.py',
    'manage.py',
    '/exceptions.py',  # Definición de excepciones de dominio (sin lógica)
)

# Frontend (portfolio Astro 6 + packages): exclusiones equivalentes a server.
# Pages, layouts, .astro y components son JSX-heavy / template-only y se
# cubren via E2E (Playwright). La lógica testeable real esta en src/lib/,
# packages/<X>/src/, validators y formatters.
FRONTEND_COVERAGE_EXCLUDES: tuple[str, ...] = (
    '/types/',  # Solo type definitions
    '/constants.ts',
    '/config.ts',
    'env.d.ts',
    '.astro',  # Componentes Astro (template-only, testeados via E2E)
    '/layouts/',  # Layouts/templates (estructura JSX, sin lógica testeable)
    '/pages/',  # Pages Astro (file-based routing, testeadas via E2E)
    '/public/',  # Assets estáticos
    # Astro config files in apps/<APP> y packages/<PKG>
    '/astro.config.ts',
    '/vitest.config.ts',
    '/uno.config.ts',
    '/tailwind.config.ts',
    # Scripts auxiliares (build-time, no lógica testeable crítica)
    '/scripts/',
)


def is_excluded_from_coverage(source: str) -> bool:
    """True si el source esta excluido del coverage 80% per-file.

    Aplica patrones SERVER_COVERAGE_EXCLUDES y FRONTEND_COVERAGE_EXCLUDES.
    Centralizado aquí para que hooks, test_runner y CI usen el mismo criterio.
    """
    for pattern in SERVER_COVERAGE_EXCLUDES + FRONTEND_COVERAGE_EXCLUDES:
        if pattern in source:
            return True
    return False


# Layout for frontend coverage:
#   <module>/coverage/coverage-summary.json (Vitest v8 reporter='json-summary')
#
# Keys in the summary are absolute paths to source files. We match by suffix
# against the source's path-from-module-root, so the comparison is independent
# of the host filesystem.
_PORTFOLIO_APPS = ('hub', 'generic', 'fintech', 'architect', 'leader', 'vibe')
_PORTFOLIO_PACKAGES = ('app-shared', 'content', 'cv-pdf', 'seo', 'ui')

_FRONTEND_COVERAGE_LAYOUT: dict[str, dict] = {}
for _app in _PORTFOLIO_APPS:
    _FRONTEND_COVERAGE_LAYOUT[_app] = {
        'summary_path': f'apps/{_app}/coverage/coverage-summary.json',
        'strip_for_match': f'apps/{_app}/',
    }
for _pkg in _PORTFOLIO_PACKAGES:
    _FRONTEND_COVERAGE_LAYOUT[f'pkg-{_pkg}'] = {
        'summary_path': f'packages/{_pkg}/coverage/coverage-summary.json',
        'strip_for_match': f'packages/{_pkg}/',
    }


def verify_server_coverage(
    unit_pairs: list[tuple[str, str]],
    *,
    project_root: Path,
    threshold: int = COVERAGE_THRESHOLD,
) -> tuple[list[dict], list[dict]]:
    """Verify per-file coverage from pytest-cov coverage.json.

    Returns:
        (passed, failed) where each item is a dict with:
            source: str, pct: float | None, status: 'OK' | 'FAIL' | 'SKIP'
    """
    coverage_json = project_root / 'server' / 'coverage.json'
    if not coverage_json.exists():
        return [], [
            {'source': 'coverage.json', 'pct': None, 'status': 'MISSING'}
        ]

    data = json.loads(coverage_json.read_text())
    files_data = data.get('files', {})
    passed: list[dict] = []
    failed: list[dict] = []

    for source, _ in unit_pairs:
        if is_excluded_from_coverage(source):
            passed.append({'source': source, 'pct': None, 'status': 'EXCLUDED'})
            continue

        source_key = source.removeprefix('server/')
        file_info = files_data.get(source_key)

        if file_info is None:
            passed.append({'source': source, 'pct': None, 'status': 'SKIP'})
            continue

        pct = file_info.get('summary', {}).get('percent_covered', 0)
        entry = {'source': source, 'pct': pct}

        if pct >= threshold:
            entry['status'] = 'OK'
            passed.append(entry)
        else:
            entry['status'] = 'FAIL'
            failed.append(entry)

    return passed, failed


def _frontend_pct_from_summary(
    source: str,
    summary: dict,
    layout: dict,
) -> float | None:
    """Return the lines % for a source path, matching by absolute-path suffix."""
    needle = source.removeprefix(layout['strip_for_match'])

    for key, val in summary.items():
        if key == 'total':
            continue
        if key.endswith(needle):
            lines = val.get('lines', {})
            pct = lines.get('pct')
            if pct is not None:
                return float(pct)
            return None

    return None


def verify_frontend_coverage(
    module: str,
    unit_pairs: list[tuple[str, str]],
    *,
    project_root: Path,
    threshold: int = COVERAGE_THRESHOLD,
) -> tuple[list[dict], list[dict]]:
    """Verify per-file coverage from Vitest json-summary reporter.

    Reads <module>/coverage/coverage-summary.json. The summary uses absolute
    paths as keys; matching is suffix-based so it is host-independent.

    Returns:
        (passed, failed) same shape as verify_server_coverage.
    """
    if module not in _FRONTEND_COVERAGE_LAYOUT:
        msg = f'Unknown frontend module: {module}'
        raise ValueError(msg)

    layout = _FRONTEND_COVERAGE_LAYOUT[module]
    summary_path = project_root / layout['summary_path']

    if not summary_path.exists():
        return [], [
            {
                'source': layout['summary_path'].split('/')[-1],
                'pct': None,
                'status': 'MISSING',
            }
        ]

    summary = json.loads(summary_path.read_text())

    passed: list[dict] = []
    failed: list[dict] = []

    for source, _ in unit_pairs:
        if is_excluded_from_coverage(source):
            passed.append({'source': source, 'pct': None, 'status': 'EXCLUDED'})
            continue

        pct = _frontend_pct_from_summary(source, summary, layout)

        if pct is None:
            passed.append({'source': source, 'pct': None, 'status': 'SKIP'})
            continue

        entry = {'source': source, 'pct': pct}
        if pct >= threshold:
            entry['status'] = 'OK'
            passed.append(entry)
        else:
            entry['status'] = 'FAIL'
            failed.append(entry)

    return passed, failed


def format_coverage_line(entry: dict) -> str:
    """Format a single coverage entry as a display line."""
    source = entry['source']
    pct = entry.get('pct')
    status = entry['status']
    if pct is None:
        return f'  {source:60s}    N/A  {status}'
    return f'  {source:60s} {pct:6.1f}%  {status}'
