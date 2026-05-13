"""Shared helper that wraps ``scan`` for consumers that need a list of files.

This is the single entry point for any devtools or git-hooks code that needs
to know "which files are in state X (staged/unstaged/changed/...)" without
re-implementing git plumbing. It exists because:

- ``test_runner`` shells out to ``python devtools/run.py scan ...`` (subprocess)
- ``.git-hooks/_common.py`` imports ``scan.main.get_project_structure`` directly
- ``verify`` used to call ``git`` itself, which diverged from the canonical
  detection (no .gitignore respect, no deleted-file filtering, no support for
  ``unmerged``/``stash`` modes)

This helper unifies the second pattern (direct import, no subprocess) so
that any in-process Python caller goes through the same code path.

Two modes:

- ``files_for_module(module, git_mode, ...)`` — filtered by the module's
  ``root`` and ``extensions`` config. Use when you need files for a specific
  module (e.g., conformance for ``server/*.py``).
- ``files_changed(git_mode)`` — every changed file, no module/extension
  filter. Use when you need a transversal view (e.g., ``verify`` classifying
  any path).
"""

from __future__ import annotations

from typing import Any


def files_for_module(
    *,
    module: str,
    git_mode: str,
    purpose: str | None = None,
) -> list[str]:
    """Files for ``module`` filtered by its ``root`` and ``extensions``.

    Mirrors the historical ``.git-hooks/_common.py:scan_files`` behaviour:
    only paths under ``module_config['root']`` whose suffix is in
    ``module_config['extensions']`` are returned. Optional ``purpose``
    layers on the per-purpose excludes from ``scan.modules``.
    """
    from scan.main import get_project_structure
    from scan.modules import get_module
    from scan.modules import get_purpose_excludes

    module_config = get_module(module)
    extensions = module_config.get('extensions', ['py'])

    flags: dict[str, Any] = {
        'module': module,
        'git_mode': git_mode,
        'only_list': True,
        'only_extension': extensions,
        'include_ignored': False,
        'include_deleted': False,
        'exclude_empty': False,
        'only_folders_root': False,
        'ignore_patterns': list(module_config.get('exclude_patterns', [])),
        '_invoked_from': 'python',
        '_module_config': module_config,
    }

    if purpose:
        flags['ignore_patterns'] += get_purpose_excludes(module, purpose)

    structure = get_project_structure(flags)
    if not structure:
        return []

    suffixes = tuple(f'.{ext}' for ext in extensions)
    return [
        path for path in structure.get('files', {}) if path.endswith(suffixes)
    ]


def files_changed(*, git_mode: str = 'changed') -> list[str]:
    """Every changed file for ``git_mode``, no module/extension filter.

    Use this when you need to classify arbitrary paths (``verify`` checks
    server/dashboard/landing/devtools/.claude in one pass). Defaults to
    ``changed`` (staged + unstaged + untracked) to mirror the previous
    ``verify --all-changed`` semantics.

    Filters that ``scan`` always applies: project ``.gitignore`` rules and
    deleted files (``include_deleted=False``). That's the value-add over
    raw ``git diff --name-only``.
    """
    from scan.main import get_project_structure

    flags: dict[str, Any] = {
        'git_mode': git_mode,
        'only_list': True,
        'include_ignored': False,
        'include_deleted': False,
        'exclude_empty': False,
        'only_folders_root': False,
        'ignore_patterns': [],
        '_invoked_from': 'python',
    }

    structure = get_project_structure(flags)
    if not structure:
        return []

    return sorted(structure.get('files', {}).keys())
