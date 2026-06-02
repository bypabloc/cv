"""Codigo compartido entre hooks pre-commit y pre-push del portfolio.

Provee:
  - Output con colores (info, ok, err, skip, tip, header, section)
  - Configuración de pasos (config.json + SKIP_STEPS env)
  - Deteccion de archivos staged/unmerged via git plumbing
  - Helpers para correr pnpm directamente en host (sin Docker)

Diseño: autocontenido. NO depende de devtools/.venv. Solo requiere pnpm y
node en PATH (corepack ya lo activa). Esto mantiene el hook ejecutable en
cualquier entorno (local, CI) sin bootstrap pesado.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


# =============================================================================
# CONSTANTES
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COVERAGE_THRESHOLD = 80

PORTFOLIO_APPS = ('hub', 'generic', 'fintech', 'architect', 'leader', 'vibe')
PORTFOLIO_PACKAGES = ('app-shared', 'content', 'cv-pdf', 'seo', 'ui')

_FORBIDDEN_JS_EXTS = ('.js', '.jsx', '.mjs', '.cjs')
_ALLOWLIST_CONFIG_RE = re.compile(
    r'^([A-Za-z0-9_.\-]+\.config|vitest\.config|postcss\.config)\.(js|mjs|cjs)$',
)

# Flag para bypass total de hooks (constante centralizada).
BYPASS_FLAG = '--' + 'no' + '-verify'


# =============================================================================
# COLORES Y OUTPUT
# =============================================================================

def _supports_color() -> bool:
    if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
        return False
    if os.environ.get('VSCODE_PID') or os.environ.get('TERM_PROGRAM') == 'vscode':
        return False
    if os.environ.get('TERM') == 'dumb':
        return False
    return True


if _supports_color():
    _RED = '\033[0;31m'
    _GREEN = '\033[0;32m'
    _YELLOW = '\033[1;33m'
    _BLUE = '\033[0;34m'
    _CYAN = '\033[0;36m'
    _PURPLE = '\033[0;35m'
    _NC = '\033[0m'
else:
    _RED = _GREEN = _YELLOW = _BLUE = _CYAN = _PURPLE = _NC = ''


def out(msg: str) -> None:
    print(msg, flush=True)


def info(msg: str) -> None:
    out(f'{_CYAN}[INFO] {msg}{_NC}')


def ok(msg: str) -> None:
    out(f'{_GREEN}[OK] {msg}{_NC}')


def err(msg: str) -> None:
    out(f'{_RED}[FALLO] {msg}{_NC}')


def skip(msg: str) -> None:
    out(f'{_YELLOW}[OMITIDO] {msg}{_NC}')


def tip(msg: str) -> None:
    out(f'{_YELLOW}[CONSEJO] {msg}{_NC}')


def header(title: str) -> None:
    out('')
    out('=' * 80)
    out(f'{_PURPLE}  {title}{_NC}')
    out('=' * 80)
    out('')


def section(title: str) -> None:
    out('-' * 80)
    out(f'{_BLUE}{title}{_NC}')
    out('-' * 80)


def green(msg: str) -> str:
    return f'{_GREEN}{msg}{_NC}'


def yellow(msg: str) -> str:
    return f'{_YELLOW}{msg}{_NC}'


def red(msg: str) -> str:
    return f'{_RED}{msg}{_NC}'


def cyan(msg: str) -> str:
    return f'{_CYAN}{msg}{_NC}'


# =============================================================================
# CONFIGURACIÓN DE PASOS
# =============================================================================

def should_run_step(step_name: str, hook_name: str) -> bool:
    """Verifica si un paso debe ejecutarse (config.json + SKIP_STEPS env)."""
    skip_steps = os.environ.get('SKIP_STEPS', '')
    if step_name in {s.strip() for s in skip_steps.split(',') if s.strip()}:
        return False

    config_file = PROJECT_ROOT / '.git-hooks' / 'config.json'
    if config_file.exists():
        try:
            config = json.loads(config_file.read_text())
            enabled = (
                config
                .get(hook_name, {})
                .get('steps', {})
                .get(step_name, {})
                .get('enabled', True)
            )
            return bool(enabled)
        except (json.JSONDecodeError, KeyError):
            pass

    return True


def fail(step_desc: str, blocked_msg: str, hook_name: str) -> int:
    """Imprime mensaje de fallo y retorna exit code 1."""
    git_cmd = 'git commit' if hook_name == 'pre-commit' else 'git push'

    out('')
    err(step_desc)
    out('')
    out('=' * 80)
    out(red(f'  {blocked_msg}'))
    out('=' * 80)
    out('')
    out(yellow('Bypass total (emergencias, no recomendado):'))
    out(cyan(f'   {git_cmd} {BYPASS_FLAG}'))
    out('')
    out(yellow('Omitir UN paso (no recomendado):'))
    for step in ('conformance', 'frontend_purity', 'mirror_enforcement',
                 'deletion_mirror', 'typecheck', 'unit_tests', 'build'):
        out(cyan(f'   SKIP_STEPS="{step}" {git_cmd} ...'))
    out('')
    return 1


# =============================================================================
# DETECCION DE ARCHIVOS VIA GIT
# =============================================================================

def get_staged_files() -> list[str]:
    """Archivos staged para commit (pre-commit)."""
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR'],
        capture_output=True, text=True, check=False,
        cwd=str(PROJECT_ROOT),
    )
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.splitlines() if f]


def _resolve_base_branch() -> str | None:
    """Devuelve origin/main, origin/master o origin/dev — el que exista."""
    for candidate in ('origin/main', 'origin/master', 'origin/dev'):
        check = subprocess.run(
            ['git', 'rev-parse', '--verify', candidate],
            capture_output=True, text=True, check=False,
            cwd=str(PROJECT_ROOT),
        )
        if check.returncode == 0:
            return candidate
    return None


def get_unmerged_files() -> list[str]:
    """Archivos modificados vs base branch (pre-push)."""
    base = _resolve_base_branch()
    if base:
        diff_args = [f'{base}...HEAD']
    else:
        diff_args = ['HEAD~1...HEAD']

    result = subprocess.run(
        ['git', 'diff', '--name-only', '--diff-filter=ACMR', *diff_args],
        capture_output=True, text=True, check=False,
        cwd=str(PROJECT_ROOT),
    )
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.splitlines() if f]


def filter_lintable_files(files: list[str]) -> list[str]:
    """Filtra archivos lintables (.ts, .astro, .json, .md) en apps/packages."""
    relevant_exts = ('.ts', '.tsx', '.astro', '.json', '.md', '.css')
    result = []
    for f in files:
        if not (f.startswith('apps/') or f.startswith('packages/')):
            continue
        # public/ y .next/ contienen artefactos generados (openapi.json,
        # mockServiceWorker.js, etc.) que biome ignora -> pasarlos a
        # 'biome check' da 'no files processed' y rompe el pre-commit.
        if (
            'node_modules/' in f
            or '/dist/' in f
            or '/.astro/' in f
            or '/.next/' in f
            or '/public/' in f
        ):
            continue
        if any(f.endswith(ext) for ext in relevant_exts):
            result.append(f)
    return result


def detect_modified_apps(files: list[str]) -> list[str]:
    """Lista las apps Astro con archivos modificados (apps/<X>/...)."""
    result = []
    for app in PORTFOLIO_APPS:
        if any(f.startswith(f'apps/{app}/') for f in files):
            result.append(app)
    return result


def detect_modified_packages(files: list[str]) -> list[str]:
    """Lista los packages con archivos modificados (packages/<X>/...)."""
    result = []
    for pkg in PORTFOLIO_PACKAGES:
        if any(f.startswith(f'packages/{pkg}/') for f in files):
            result.append(pkg)
    return result


# =============================================================================
# FRONTEND PURITY (no .js/.jsx/.mjs/.cjs salvo configs en raíz)
# =============================================================================

def find_forbidden_js_files(files: list[str]) -> list[str]:
    """Detecta archivos .js/.jsx/.mjs/.cjs prohibidos en apps/* o packages/*."""
    violations = []
    for f in files:
        if not (f.startswith('apps/') or f.startswith('packages/')):
            continue
        # public/ y .next/ contienen artefactos generados (openapi.json,
        # mockServiceWorker.js, etc.) que biome ignora -> pasarlos a
        # 'biome check' da 'no files processed' y rompe el pre-commit.
        if (
            'node_modules/' in f
            or '/dist/' in f
            or '/.astro/' in f
            or '/.next/' in f
            or '/public/' in f
        ):
            continue
        if not any(f.endswith(ext) for ext in _FORBIDDEN_JS_EXTS):
            continue
        parts = Path(f).parts
        if len(parts) == 3 and _ALLOWLIST_CONFIG_RE.match(parts[2]):
            continue
        violations.append(f)
    return violations


# =============================================================================
# EJECUCIÓN DE COMANDOS (pnpm en host)
# =============================================================================

def run_pnpm(args: list[str], *, cwd: Path | None = None,
             timeout: int = 300) -> int:
    """Ejecuta `pnpm <args>` en el cwd dado y retorna exit code.

    Inyecta ``CI=true`` para evitar prompts interactivos de pnpm 11
    (ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY) cuando el lockfile
    cambia y pnpm intenta auto-purge de node_modules.
    """
    cwd_str = str(cwd) if cwd else str(PROJECT_ROOT)
    info(f'$ pnpm {" ".join(args)}  (cwd: {Path(cwd_str).name or "."})')
    env = os.environ.copy()
    env.setdefault('CI', 'true')
    try:
        result = subprocess.run(
            ['pnpm', *args],
            cwd=cwd_str, check=False, timeout=timeout, env=env,
        )
        return result.returncode
    except FileNotFoundError:
        err('pnpm no esta instalado en PATH')
        tip('Instalar pnpm via corepack: corepack enable && corepack prepare pnpm@latest --activate')
        return 127


def run_pnpm_exec(args: list[str], *, cwd: Path | None = None,
                  timeout: int = 300) -> int:
    """Ejecuta `pnpm exec <args>` en el cwd dado."""
    return run_pnpm(['exec', *args], cwd=cwd, timeout=timeout)
