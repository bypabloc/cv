"""Parsers para manifestos Python (pyproject.toml) y npm (package.json).

Extraen los paquetes y sus versiones declaradas, conservando el prefijo (^, ~,
==, >=) para poder reaplicarlo al escribir.

Para Python soportamos pyproject.toml con secciones:
  - [project.dependencies]   (PEP 621)
  - [dependency-groups.<name>]  (PEP 735)
"""

import json
from pathlib import Path
import re
import tomllib


# Operadores PEP 440 soportados en requirements.txt. Los escribimos del mas
# largo al mas corto para que el regex haga el match correcto.
_PYPI_OPERATORS = ('===', '~=', '==', '!=', '<=', '>=', '<', '>')

# Linea de package PEP 508 simplificada: name[extras]<op><version>
_PYPI_LINE_RE = re.compile(
    r'^\s*'
    r'(?P<name>[A-Za-z0-9_.\-]+)'
    r'(?P<extras>\[[^\]]+\])?'
    r'\s*(?P<op>===|~=|==|!=|<=|>=|<|>)\s*'
    r'(?P<version>[A-Za-z0-9_.\-+!]+)'
    r'\s*$',
)


# Specs npm que NO deben consultarse al registry (son refs locales/git/url).
_NPM_NON_REGISTRY_PREFIXES = (
    'workspace:',
    'file:',
    'link:',
    'git+',
    'git:',
    'http:',
    'https:',
    'github:',
    'npm:',
)


def parse_requirements_txt(path: Path) -> list[dict]:
    """Parse a Python requirements.txt file.

    Returns:
        Lista de dicts con keys: name, operator, version, extras, line_no.
        Solo extrae lineas que matchean ``name[extras]<op>version``. Saltea
        comentarios, lineas en blanco, lineas con marcadores como ``-r``,
        ``-e``, ``--`` (no son packages directos).
    """
    if not path.exists():
        return []

    packages: list[dict] = []
    for line_no, raw in enumerate(path.read_text().splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith(('#', '-')):
            continue

        match = _PYPI_LINE_RE.match(stripped)
        if not match:
            continue

        packages.append(
            {
                'name': match.group('name'),
                'operator': match.group('op'),
                'version': match.group('version'),
                'extras': match.group('extras') or '',
                'line_no': line_no,
            }
        )

    return packages


def _find_dep_line(src_lines: list[str], dep_str: str) -> int:
    """Find the 1-based line containing the quoted dependency spec.

    Returns 0 if not found (caller will skip rewriting that entry).
    """
    for line_no, line in enumerate(src_lines, start=1):
        if f'"{dep_str}"' in line or f"'{dep_str}'" in line:
            return line_no
    return 0


def _parse_dep_entry(
    dep: str,
    section: str,
    src_lines: list[str],
) -> dict | None:
    """Parse a single PEP 508 dependency string from a pyproject.toml list.

    Returns None if the dep is not a pinned spec (no version operator, or
    points to a URL/path). Strips environment markers (`; python_version<X`).
    """
    if not isinstance(dep, str):
        return None

    base = dep.split(';', 1)[0].strip()
    match = _PYPI_LINE_RE.match(base)
    if not match:
        return None

    return {
        'name': match.group('name'),
        'operator': match.group('op'),
        'version': match.group('version'),
        'extras': match.group('extras') or '',
        'line_no': _find_dep_line(src_lines, dep),
        'section': section,
        'original': dep,
    }


def _collect_pyproject_section(
    deps: list[str],
    section: str,
    src_lines: list[str],
) -> list[dict]:
    """Filter+parse a list of PEP 508 specs into upgrade_deps records."""
    parsed: list[dict] = []
    for dep in deps:
        entry = _parse_dep_entry(dep, section, src_lines)
        if entry is not None:
            parsed.append(entry)
    return parsed


def parse_pyproject_toml(path: Path) -> list[dict]:
    """Parse a pyproject.toml extracting dependencies pinned with `==`, `>=`...

    Reads:
      - `[project].dependencies`   (PEP 621, list of PEP 508 strings)
      - `[dependency-groups]`      (PEP 735, dict of group -> list)

    Each item must match the same `name[extras]<op>version` pattern as
    `requirements.txt`. Items with markers (`; python_version<'3.10'`) or
    no version pin (e.g. `pkg ; sys_platform == 'linux'`) are SKIPPED —
    we only upgrade explicitly pinned packages, leaving floating ones untouched.

    `line_no` is the 1-based line in the source file where the package string
    appears, allowing line-based rewriting that preserves comments/formatting.

    Returns: list of dicts with keys: name, operator, version, extras,
    line_no, section ('project.dependencies' or 'dependency-groups.<group>').
    Empty list if the file does not exist or has no parseable entries.
    """
    if not path.exists():
        return []

    text = path.read_text()
    data = tomllib.loads(text)
    src_lines = text.splitlines()

    packages: list[dict] = []

    project_deps = data.get('project', {}).get('dependencies', [])
    if isinstance(project_deps, list):
        packages.extend(
            _collect_pyproject_section(
                project_deps,
                'project.dependencies',
                src_lines,
            ),
        )

    groups = data.get('dependency-groups', {})
    if isinstance(groups, dict):
        for group_name, group_deps in groups.items():
            if isinstance(group_deps, list):
                packages.extend(
                    _collect_pyproject_section(
                        group_deps,
                        f'dependency-groups.{group_name}',
                        src_lines,
                    ),
                )

    return packages


def _split_npm_constraint(spec: str) -> tuple[str, str] | None:
    """Split an npm version spec into (prefix, version).

    Returns None if ``spec`` is not a registry version (e.g. ``workspace:*``,
    ``file:../foo``, ``git+https://...``).
    """
    if not spec:
        return None

    if spec.startswith(_NPM_NON_REGISTRY_PREFIXES):
        return None

    # Strip whitespace
    spec = spec.strip()

    # Common npm prefixes for version ranges
    for prefix in ('^', '~', '>=', '<=', '>', '<', '='):
        if spec.startswith(prefix):
            return prefix, spec[len(prefix) :].strip()

    # Wildcard or "latest" or ranges with whitespace ("1.0 - 2.0", "*")
    # Solo consideramos un version literal si parece una version (digito al inicio).
    if not spec or not spec[0].isdigit():
        return None

    return '', spec


def _collect_npm_section(
    deps: dict | None,
    section: str,
) -> list[dict]:
    """Convert an npm-style dict {name: spec} into upgrade_deps records."""
    if not deps:
        return []

    out: list[dict] = []
    for name, spec in deps.items():
        if not isinstance(spec, str):
            continue
        parsed = _split_npm_constraint(spec)
        if parsed is None:
            continue
        prefix, version = parsed
        out.append(
            {
                'name': name,
                'prefix': prefix,
                'version': version,
                'section': section,
            }
        )
    return out


def parse_package_json(path: Path) -> list[dict]:
    """Parse an npm package.json file.

    Extrae ``dependencies``, ``devDependencies`` y ``pnpm.overrides``.
    Saltea protocolos no-registry (workspace:, file:, link:, git+, http(s):).

    Returns:
        Lista de dicts con keys: name, prefix, version, section.
    """
    if not path.exists():
        return []

    data = json.loads(path.read_text())

    packages: list[dict] = []
    packages.extend(
        _collect_npm_section(data.get('dependencies'), 'dependencies'),
    )
    packages.extend(
        _collect_npm_section(data.get('devDependencies'), 'devDependencies'),
    )
    packages.extend(
        _collect_npm_section(
            data.get('pnpm', {}).get('overrides'),
            'pnpm.overrides',
        ),
    )

    return packages
