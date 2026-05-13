"""TypeScript-purity check for frontend modules (portfolio Astro 6).

Forbids `.js`, `.jsx`, `.mjs`, `.cjs` files inside `apps/<APP>/` and
`packages/<PKG>/`.

Allowlist (config files at module root only):
    {anything}.config.{js,mjs,cjs}
    vitest.config.{js,mjs,cjs}
    postcss.config.{js,mjs,cjs}

Excluded directories (never reported):
    node_modules/, dist/, .astro/, coverage/
"""

from pathlib import Path
import re


_FORBIDDEN_EXTENSIONS = ('.js', '.jsx', '.mjs', '.cjs')

_ALLOWLIST_FILENAME_RE = re.compile(
    r'^([A-Za-z0-9_.\-]+\.config|vitest\.config|postcss\.config)\.(js|mjs|cjs)$',
)

_DEFAULT_EXCLUDED = ('node_modules/', '.astro/', 'dist/', 'coverage/')

_PORTFOLIO_APPS = ('hub', 'generic', 'fintech', 'architect', 'leader', 'vibe')
_PORTFOLIO_PACKAGES = ('app-shared', 'content', 'cv-pdf', 'seo', 'ui')

# Mapeo modulo -> (path prefix, depth-of-module-root).
# Depth-of-module-root es la cantidad de path parts ANTES del primer archivo.
# Para apps/X/foo.ts: depth=2 -> 'apps','X','foo.ts' -> parts[0:2] = module root.
# Para packages/X/foo.ts: depth=2 igual.
_MODULE_MAP: dict[str, dict] = {}
for _app in _PORTFOLIO_APPS:
    _MODULE_MAP[_app] = {
        'prefix': f'apps/{_app}/',
        'root_depth': 2,
        'excluded': _DEFAULT_EXCLUDED,
    }
for _pkg in _PORTFOLIO_PACKAGES:
    _MODULE_MAP[f'pkg-{_pkg}'] = {
        'prefix': f'packages/{_pkg}/',
        'root_depth': 2,
        'excluded': _DEFAULT_EXCLUDED,
    }

_VALID_MODULES = tuple(_MODULE_MAP.keys())


def _is_allowlisted_at_root(rel_path: str, module_info: dict) -> bool:
    """True if rel_path is a config file directly at <module-root>/<file>."""
    p = Path(rel_path)
    parts = p.parts
    root_depth = module_info['root_depth']
    # Para apps/<X>/foo.config.mjs: parts = ('apps', '<X>', 'foo.config.mjs')
    # len(parts) debe ser root_depth + 1 (root + filename).
    if len(parts) != root_depth + 1:
        return False
    if not rel_path.startswith(module_info['prefix']):
        return False
    return bool(_ALLOWLIST_FILENAME_RE.match(parts[-1]))


def find_forbidden_js_files(
    module: str,
    files: list[str],
    *,
    project_root: Path,
) -> list[str]:
    """Return forbidden .js/.jsx/.mjs/.cjs files inside the given module.

    Files outside the module prefix are ignored. Files inside excluded
    directories (node_modules, dist, etc.) are ignored. Allowlisted config
    files at the module root are ignored.

    Module names:
      - apps Astro: 'hub', 'generic', 'fintech', 'architect', 'leader', 'vibe'
      - packages: 'pkg-app-shared', 'pkg-content', 'pkg-cv-pdf', 'pkg-seo', 'pkg-ui'
    """
    if module not in _VALID_MODULES:
        msg = f'Unknown frontend module: {module}'
        raise ValueError(msg)

    info = _MODULE_MAP[module]
    prefix = info['prefix']
    excluded = info['excluded']

    violations: list[str] = []
    for f in files:
        if not f.startswith(prefix):
            continue
        if any(part in f for part in excluded):
            continue
        if not f.endswith(_FORBIDDEN_EXTENSIONS):
            continue
        if _is_allowlisted_at_root(f, info):
            continue
        violations.append(f)

    return violations
