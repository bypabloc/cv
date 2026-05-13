"""Display helpers for the scan script.

Renders the structure dict as either a separator-joined list (CI/scripts)
or a human-readable tree (terminal). All output behaviour lives here so
that the data layer (``structure.py``) stays free of presentation
concerns.
"""

from __future__ import annotations

from typing import Any


def _display_list_mode(
    structure: dict[str, Any],
    flags: dict[str, Any],
) -> None:
    """Print a single line of paths separated by ``;`` (machine-readable)."""
    separator = ';'
    if flags.get('only_folders_root'):
        print(separator.join(structure['folders']))
    else:
        file_paths = list(structure['files'].keys())
        all_items = structure['folders'] + file_paths
        print(separator.join(all_items) if all_items else '')


def _display_files_section(files: dict[str, Any]) -> None:
    """Print the ``Archivos:`` block with date metadata."""
    print('Archivos:')
    print('-' * 20)
    for file_path, file_info in files.items():
        dates_info = ''
        if file_info.get('created_date') and file_info.get('modified_date'):
            dates_info = (
                f' (Creado: {file_info["created_date"][:10]}, '
                f'Modificado: {file_info["modified_date"][:10]})'
            )
        print(f'  {file_path}{dates_info}')
    print()


def _display_deleted_section(deleted_files: dict[str, Any]) -> None:
    """Print the ``Archivos eliminados:`` block."""
    print('\nArchivos eliminados:')
    print('-' * 20)
    for file_path, file_info in deleted_files.items():
        dates_info = ''
        if file_info.get('deleted_date'):
            dates_info = f' (Eliminado: {file_info["deleted_date"][:10]})'
        print(f'  [deleted] {file_path}{dates_info}')
    print()


def _display_detailed_mode(
    structure: dict[str, Any],
    flags: dict[str, Any],
) -> None:
    """Print the full human-readable view of the structure."""
    if flags.get('only_folders_root'):
        print('Carpetas raiz del proyecto:')
        print('-' * 30)
        for folder in structure['folders']:
            print(f'  {folder}')
        print(f'\nTotal: {len(structure["folders"])} carpetas')
        return

    if structure['folders']:
        print('Carpetas:')
        print('-' * 20)
        for folder in structure['folders']:
            print(f'  {folder}')
        print()

    if structure['files']:
        _display_files_section(structure['files'])

    if 'deleted' in structure and structure['deleted']['files']:
        _display_deleted_section(structure['deleted']['files'])

    deleted_count = len(structure.get('deleted', {}).get('files', {}))
    summary_text = (
        f'Resumen: {len(structure["folders"])} carpetas, '
        f'{len(structure["files"])} archivos'
    )
    if deleted_count > 0:
        summary_text += f', {deleted_count} eliminados'
    print(summary_text)


def display_structure(
    structure: dict[str, Any],
    flags: dict[str, Any],
) -> None:
    """Public entry point: choose list vs detailed mode and print."""
    if flags.get('only_list', False):
        _display_list_mode(structure, flags)
    else:
        _display_detailed_mode(structure, flags)
