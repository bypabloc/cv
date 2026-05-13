"""scan entry point: orchestrates the project structure walk and display.

The heavy lifting lives in submodules:
- ``ignore.py``    — gitignore + glob/regex pattern matching
- ``git_query.py`` — git ls-files, diff, deleted/uncommitted helpers
- ``files.py``     — filesystem reads (content + dates)
- ``structure.py`` — assembles the nested structure dict
- ``display.py``   — pretty/list output

This file just wires the flags through, picks the printable header text
for the active mode, and either returns the dict (Python invocation) or
prints it (CLI invocation).
"""

from __future__ import annotations

import os
from typing import Any

from scan.display import display_structure
from scan.git_query import get_git_base_branch
from scan.structure import get_project_structure


def main(flags: dict[str, Any]) -> dict[str, Any] | None:
    """Print or return the project structure depending on the invoker.

    When ``flags['_invoked_from'] == 'python'`` we return the structure so
    callers can keep working with it; otherwise we print the human-readable
    view.
    """
    invoked_from = flags.get('_invoked_from', 'python')
    only_list = flags.get('only_list', False)

    structure = get_project_structure(flags)

    if invoked_from == 'python':
        return structure

    if not only_list:
        print(f'Estructura del proyecto - Directorio: {os.getcwd()}')
        _print_mode_header(flags)
        print('=' * 60)

    display_structure(structure, flags)
    return None


def _print_mode_header(flags: dict[str, Any]) -> None:
    """Print the one-line description of the active mode."""
    git_mode = flags.get('git_mode')
    if git_mode == 'unmerged':
        base_branch = get_git_base_branch()
        mode_text = f"Modo: Archivos no mergeados a rama '{base_branch}'"
        if flags.get('include_deleted'):
            mode_text += ' (incluye eliminados)'
        print(mode_text)
        return

    if git_mode:
        mode_descriptions = {
            'staged': 'Archivos en staging area (listos para commit)',
            'unstaged': 'Archivos con cambios no staged',
            'untracked': 'Archivos nuevos no rastreados por git',
            'changed': (
                'Archivos con cualquier cambio (staged + unstaged + untracked)'
            ),
            'stash': 'Archivos del stash mas reciente',
            'unmerged': 'Archivos no mergeados a rama base',
            'all': 'Todos los archivos separados por categoria',
        }
        description = mode_descriptions.get(git_mode, f'Modo git: {git_mode}')
        print(f'Modo: {description}')
        return

    if flags.get('include_ignored'):
        print('Modo: Incluye archivos ignorados por git')
    else:
        print('Modo: Solo archivos rastreados por git (por defecto)')


if __name__ == '__main__':
    test_flags: dict[str, Any] = {
        'include_ignored': False,
        'excludes_extension': [],
        'only_folders_root': False,
        'include_deleted': False,
        'exclude_empty': False,
        'git_mode': None,
    }
    main(test_flags)
