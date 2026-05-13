"""Project-structure assembler for the scan script.

Walks files (filesystem or git output), runs them through ``ignore`` and
``files`` helpers and produces the nested ``structure`` dict that
``display.py`` later renders. This is the single piece that ties git
queries, ignore rules and on-disk reads together.
"""

from __future__ import annotations

import os
from typing import Any

from scan.files import get_file_content
from scan.files import get_file_dates
from scan.git_query import get_deleted_files
from scan.git_query import get_file_content_from_git
from scan.git_query import get_file_deleted_date
from scan.git_query import get_git_files_by_mode
from scan.git_query import get_git_tracked_directories
from scan.git_query import get_git_tracked_files
from scan.git_query import get_uncommitted_files
from scan.ignore import should_exclude_file


def build_structure_dict(
    folders: list[str],
    files: list[str],
) -> dict[str, Any]:
    """Build a nested dict that mirrors the folder hierarchy."""
    structure: dict[str, Any] = {}

    for folder in folders:
        parts = folder.split('/')
        current = structure
        for part in parts:
            if part not in current:
                current[part] = {}
            current = current[part]

    for file_path in files:
        parts = file_path.split('/')
        if len(parts) == 1:
            structure[parts[0]] = file_path
        else:
            folder_parts = parts[:-1]
            file_name = parts[-1]

            current = structure
            for part in folder_parts:
                if part not in current:
                    current[part] = {}
                current = current[part]

            current[file_name] = file_path

    return structure


def build_folders_structure(folders: list[str]) -> dict[str, Any]:
    """Build a nested dict of folders only (no files)."""
    structure: dict[str, Any] = {}

    for folder in folders:
        parts = folder.split('/')
        current = structure

        for part in parts:
            if part not in current:
                current[part] = {}
            current = current[part]

    return structure


def _process_files_for_mode(
    file_list: list[str],
    flags: dict[str, Any],
) -> tuple[dict[str, Any], set[str]]:
    """Read content+dates for a list of files, plus collect parent folders."""
    processed_files: dict[str, Any] = {}
    processed_folders: set[str] = set()

    for file_path in file_list:
        if not should_exclude_file(file_path, flags):
            exclude_empty = flags.get('exclude_empty', False)
            content = get_file_content(file_path, exclude_empty)

            if exclude_empty and content is None:
                continue

            created_date, modified_date = get_file_dates(file_path)

            processed_files[file_path] = {
                'path': file_path,
                'content': content,
                'created_date': (
                    created_date.isoformat() if created_date else None
                ),
                'modified_date': (
                    modified_date.isoformat() if modified_date else None
                ),
            }

            dir_path = os.path.dirname(file_path)
            while dir_path and dir_path != '.':
                processed_folders.add(dir_path)
                parent_dir = os.path.dirname(dir_path)
                if parent_dir == dir_path:
                    break
                dir_path = parent_dir

    return processed_files, processed_folders


def _init_structure(flags: dict[str, Any]) -> dict[str, Any]:
    """Initialize the base structure shape from flags."""
    structure: dict[str, Any] = {'folders': [], 'files': {}}

    if flags.get('include_deleted'):
        structure['deleted'] = {
            'folders': [],
            'files': {},
            'structure': {},
            'structure_folders': {},
        }

    git_mode = flags.get('git_mode')
    if git_mode and git_mode != 'all':
        structure['git_modes'] = {
            git_mode: {
                'folders': [],
                'files': {},
                'structure': {},
                'structure_folders': {},
            },
        }
    elif git_mode == 'all':
        structure['git_modes'] = {
            mode: {
                'folders': [],
                'files': {},
                'structure': {},
                'structure_folders': {},
            }
            for mode in [
                'staged',
                'unstaged',
                'untracked',
                'stash',
                'unmerged',
                'changed',
            ]
        }

    return structure


def _fill_mode_data(
    mode_data: dict[str, Any],
    processed_files: dict[str, Any],
    processed_folders: set[str],
) -> None:
    """Populate a mode_data dict with files+folders+derived structures."""
    mode_data['files'] = processed_files
    mode_data['folders'] = sorted(processed_folders)
    mode_data['structure'] = build_structure_dict(
        mode_data['folders'],
        list(processed_files.keys()),
    )
    mode_data['structure_folders'] = build_folders_structure(
        mode_data['folders'],
    )


def _process_git_mode(
    structure: dict[str, Any],
    flags: dict[str, Any],
) -> dict[str, Any] | None:
    """Process git modes; returns final structure if mode is terminal."""
    git_mode = flags.get('git_mode')
    if not git_mode:
        return None

    git_files_by_mode = get_git_files_by_mode(git_mode)

    if git_mode == 'all':
        for mode_name, file_list in git_files_by_mode.items():
            if mode_name in structure['git_modes']:
                processed_files, processed_folders = _process_files_for_mode(
                    file_list, flags
                )
                _fill_mode_data(
                    structure['git_modes'][mode_name],
                    processed_files,
                    processed_folders,
                )
        return None

    file_list = _resolve_file_list_for_mode(git_mode, git_files_by_mode)
    processed_files, processed_folders = _process_files_for_mode(
        file_list,
        flags,
    )
    _fill_mode_data(structure, processed_files, processed_folders)
    return structure


def _resolve_file_list_for_mode(
    git_mode: str,
    git_files_by_mode: dict[str, list[str]],
) -> list[str]:
    """Resolve file list for a single git_mode terminal output.

    For ``unmerged``, union staged + unstaged + untracked + diff vs base
    (matches the documented contract in git_query.get_git_files_by_mode).
    For other modes, return the corresponding category directly.
    """
    if git_mode == 'unmerged':
        union: set[str] = set()
        for category in ('staged', 'unstaged', 'untracked', 'unmerged'):
            union.update(git_files_by_mode.get(category, []))
        return sorted(union)
    return git_files_by_mode.get(git_mode, [])


def _process_deleted_files(
    structure: dict[str, Any],
    flags: dict[str, Any],
) -> None:
    """Process deleted files (only meaningful for ``--git-mode=unmerged``)."""
    deleted_files = get_deleted_files()
    processed_deleted_files: dict[str, Any] = {}
    deleted_folders: set[str] = set()

    for file_path in deleted_files:
        if should_exclude_file(file_path, flags):
            continue

        content = get_file_content_from_git(file_path)
        exclude_empty = flags.get('exclude_empty', False)

        if not content or content.strip() == '':
            if exclude_empty:
                continue
            content = False

        created_date, _ = (
            get_file_dates(file_path)
            if os.path.exists(file_path)
            else (None, None)
        )
        deleted_date = get_file_deleted_date(file_path)

        processed_deleted_files[file_path] = {
            'path': file_path,
            'content': content,
            'created_date': (
                created_date.isoformat() if created_date else None
            ),
            'deleted_date': (
                deleted_date.isoformat() if deleted_date else None
            ),
        }

        dir_path = os.path.dirname(file_path)
        while dir_path and dir_path != '.':
            deleted_folders.add(dir_path)
            parent_dir = os.path.dirname(dir_path)
            if parent_dir == dir_path:
                break
            dir_path = parent_dir

    _fill_mode_data(
        structure['deleted'],
        processed_deleted_files,
        deleted_folders,
    )


def _process_folders_root(
    structure: dict[str, Any],
    flags: dict[str, Any],
) -> None:
    """Populate ``structure['folders']`` with project root folders only."""
    if flags.get('include_ignored', False):
        for item in os.listdir('.'):
            if (
                os.path.isdir(item)
                and not item.startswith('.')
                and not should_exclude_file(item, flags)
            ):
                structure['folders'].append(item)
    else:
        tracked_dirs = get_git_tracked_directories()
        root_dirs: set[str] = set()
        for tracked_dir in tracked_dirs:
            root_part = (
                tracked_dir.split('/')[0] if '/' in tracked_dir else tracked_dir
            )
            if root_part and not root_part.startswith('.'):
                root_dirs.add(root_part)

        structure['folders'] = sorted(
            [d for d in root_dirs if not should_exclude_file(d, flags)],
        )


def _process_walk_files(
    structure: dict[str, Any],
    root_display: str,
    files: list[str],
    flags: dict[str, Any],
) -> None:
    """Process files yielded by ``os.walk`` (used by ignored-files mode)."""
    exclude_empty = flags.get('exclude_empty', False)
    for file_name in files:
        if file_name.startswith('.'):
            continue
        full_file_path = (
            os.path.join(root_display, file_name) if root_display else file_name
        )
        if should_exclude_file(full_file_path, flags):
            continue

        content = get_file_content(full_file_path, exclude_empty)
        if exclude_empty and content is None:
            continue

        if full_file_path not in structure['files']:
            created_date, modified_date = get_file_dates(full_file_path)
            structure['files'][full_file_path] = {
                'path': full_file_path,
                'content': content,
                'created_date': (
                    created_date.isoformat() if created_date else None
                ),
                'modified_date': (
                    modified_date.isoformat() if modified_date else None
                ),
            }


def _process_ignored_files(
    structure: dict[str, Any],
    flags: dict[str, Any],
) -> None:
    """Walk the filesystem including git-ignored entries."""
    for root, dirs, files in os.walk('.'):
        root_display = '' if root == '.' else root[2:]

        dirs[:] = [
            d
            for d in dirs
            if not d.startswith('.')
            and not should_exclude_file(os.path.join(root, d), flags)
        ]

        for dir_name in dirs:
            full_dir_path = (
                os.path.join(root_display, dir_name)
                if root_display
                else dir_name
            )
            structure['folders'].append(full_dir_path)

        _process_walk_files(structure, root_display, files, flags)


def _process_tracked_files(
    structure: dict[str, Any],
    flags: dict[str, Any],
) -> None:
    """Walk only files tracked by git (the default mode)."""
    tracked_files = get_git_tracked_files()
    tracked_dirs = get_git_tracked_directories()

    processed_files: dict[str, Any] = {}
    for file_path in tracked_files:
        if should_exclude_file(file_path, flags):
            continue

        exclude_empty = flags.get('exclude_empty', False)
        content = get_file_content(file_path, exclude_empty)
        if exclude_empty and content is None:
            continue

        created_date, modified_date = get_file_dates(file_path)
        processed_files[file_path] = {
            'path': file_path,
            'content': content,
            'created_date': (
                created_date.isoformat() if created_date else None
            ),
            'modified_date': (
                modified_date.isoformat() if modified_date else None
            ),
        }

    structure['files'] = processed_files

    for dir_path in tracked_dirs:
        if not should_exclude_file(dir_path, flags):
            structure['folders'].append(dir_path)


def get_project_structure(flags: dict[str, Any]) -> dict[str, Any]:
    """Top-level dispatcher that produces the structure dict from flags."""
    structure = _init_structure(flags)
    git_mode = flags.get('git_mode')

    if git_mode:
        result = _process_git_mode(structure, flags)
        if result is not None:
            return result

    if git_mode == 'unmerged' and flags.get('include_deleted', False):
        _process_deleted_files(structure, flags)

    if git_mode == 'unmerged':
        unmerged_files = get_uncommitted_files()
        processed_files, processed_folders = _process_files_for_mode(
            unmerged_files,
            flags,
        )
        _fill_mode_data(structure, processed_files, processed_folders)
        return structure

    if flags.get('only_folders_root'):
        _process_folders_root(structure, flags)
        return structure

    if flags.get('include_ignored', False):
        _process_ignored_files(structure, flags)
    else:
        _process_tracked_files(structure, flags)

    structure['folders'].sort()

    file_paths = list(structure['files'].keys())
    structure['structure'] = build_structure_dict(
        structure['folders'],
        file_paths,
    )
    structure['structure_folders'] = build_folders_structure(
        structure['folders'],
    )

    return structure
