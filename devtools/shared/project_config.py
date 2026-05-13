"""Project identity loader.

Reads project.yml from repo root and exposes name variants as module-level
constants. All devtools scripts import from here instead of hardcoding names.

Uses PyYAML if available, falls back to simple regex parsing otherwise.
This ensures the module never crashes even if pyyaml is not installed yet
(e.g. during git hooks before venv setup).
"""

from pathlib import Path
import re


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CONFIG_PATH = _PROJECT_ROOT / 'project.yml'

_DEFAULTS = {
    'name': 'my-project',
    'name_snake': 'my_project',
    'name_display': 'My Project',
    'container_prefix': 'mp',
}

_GENERIC_NAME = 'my-project'

# Simple regex for "key: value" lines in YAML (no nested structures needed)
_YAML_LINE_RE = re.compile(r'^(\w+)\s*:\s*(.+)$', re.MULTILINE)


def _parse_simple_yaml(text: str) -> dict[str, str]:
    """Parse flat key-value YAML without external dependencies."""
    result = {}
    for match in _YAML_LINE_RE.finditer(text):
        key = match.group(1)
        value = match.group(2).strip().strip('\'"')
        result[key] = value
    return result


def _load_config() -> dict[str, str]:
    if not _CONFIG_PATH.exists():
        return dict(_DEFAULTS)
    raw = _CONFIG_PATH.read_text(encoding='utf-8')
    data = _parse_simple_yaml(raw)
    result = {}
    for key, default in _DEFAULTS.items():
        result[key] = str(data.get(key, default))
    return result


_config = _load_config()

PROJECT_NAME: str = _config['name']
PROJECT_NAME_SNAKE: str = _config['name_snake']
PROJECT_NAME_DISPLAY: str = _config['name_display']
CONTAINER_PREFIX: str = _config['container_prefix']


def is_generic() -> bool:
    """Return True if project.yml still has the default boilerplate name."""
    return PROJECT_NAME == _GENERIC_NAME
