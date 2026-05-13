"""Ignore-pattern matching for the scan script.

Reads ``.gitignore`` patterns and supports a richer glob syntax for the
``--ignore-patterns`` flag (``**/__pycache__/**``, ``**/*.pyc``, etc).
``should_exclude_file`` is the canonical predicate consumed by the rest of
the scan pipeline.
"""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path
import re
from typing import Any


def get_ignored_files_from_gitignore() -> set[str]:
    """Read ``.gitignore`` and return the raw line patterns it declares."""
    patterns: set[str] = set()
    gitignore_path = '.gitignore'
    if not os.path.exists(gitignore_path):
        return patterns

    with open(gitignore_path) as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                patterns.add(stripped)
    return patterns


def is_ignored_by_pattern(file_path: str, patterns: set[str]) -> bool:
    """Match a path against gitignore-style patterns (directory-aware)."""
    for pattern in patterns:
        pattern = pattern.removeprefix('/')

        if pattern.endswith('/'):
            if os.path.isdir(file_path):
                file_path += '/'
            if fnmatch.fnmatch(file_path, pattern + '*'):
                return True
        elif fnmatch.fnmatch(file_path, pattern):
            return True

    return False


def matches_ignore_pattern(file_path: str, pattern: str) -> bool:
    r"""Match ``file_path`` against a regex/glob pattern.

    Supports patterns like ``**/*/__init__``, ``.*\.pyc$``, ``tests/.*\.py$``.
    Falls back to substring search if the regex is invalid.
    """
    try:
        normalized_path = os.path.normpath(file_path).replace('\\', '/')

        if '**/' in pattern or '*' in pattern:
            regex_pattern = pattern.replace('**/', '.*/')
            regex_pattern = regex_pattern.replace('*', '[^/]*')
            regex_pattern = regex_pattern.replace('/.*/', '/.*/')

            if not regex_pattern.startswith('^'):
                regex_pattern = '.*' + regex_pattern

            if not regex_pattern.endswith('$') and '\\.' not in regex_pattern:
                regex_pattern += '(\\..*)?$'
            elif not regex_pattern.endswith('$'):
                regex_pattern += '$'
        else:
            regex_pattern = pattern

        compiled_pattern = re.compile(regex_pattern, re.IGNORECASE)
        return bool(compiled_pattern.search(normalized_path))

    except re.error:
        return pattern in file_path
    except ValueError, TypeError, AttributeError:
        return False


def _matches_path_pattern(file_path: str, pattern: str) -> bool:
    """Match a file path against a glob-like pattern.

    Common shortcuts handled directly:
    - ``prefix/**``: any file under prefix/
    - ``**/segment/**``: segment appears anywhere as a directory
    - ``**/*.ext``: files with extensión at any depth
    - ``**/__init__.py``: file at any depth
    Other patterns delegate to ``matches_ignore_pattern``.
    """
    normalized = os.path.normpath(file_path).replace('\\', '/')

    # Directory segment anywhere — must check before the prefix/** shortcut.
    if pattern.startswith('**/') and pattern.endswith('/**'):
        segment = pattern[3:-3]
        return f'/{segment}/' in f'/{normalized}/'

    if pattern.endswith('/**'):
        prefix = pattern[:-3]
        return normalized.startswith(prefix + '/') or normalized == prefix

    if pattern.startswith('**/'):
        suffix = pattern[3:]
        if '*' not in suffix:
            return normalized.endswith('/' + suffix) or normalized == suffix
        if suffix.startswith('*.'):
            ext = suffix[1:]
            return normalized.endswith(ext)

    return matches_ignore_pattern(file_path, pattern)


def should_exclude_empty_file(file_path: str) -> bool:
    """Return True if the file is missing or contains only whitespace."""
    try:
        if not os.path.exists(file_path):
            return True

        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
                return not content or content.strip() == ''
        except UnicodeDecodeError:
            try:
                with open(file_path, encoding='latin1') as f:
                    content = f.read()
                    return not content or content.strip() == ''
            except OSError, UnicodeDecodeError, PermissionError:
                return False
    except OSError, PermissionError:
        return True


def should_exclude_file(file_path: str, flags: dict[str, Any]) -> bool:
    """Decide whether a file is filtered out by the active flags.

    Honours: ``_module_config['root']`` (module scope), ``only_extension``,
    ``excludes_extension``, ``exclude_empty``, ``ignore_patterns``.
    """
    module_config = flags.get('_module_config')
    if module_config:
        module_root = module_config.get('root', '')
        if module_root and not file_path.startswith(module_root):
            return True

    file_ext = Path(file_path).suffix.lower()
    file_ext = file_ext.removeprefix('.')

    only_extension = flags.get('only_extension', [])
    if only_extension and file_ext not in only_extension:
        return True

    excludes_extension = flags.get('excludes_extension', [])
    if (
        excludes_extension
        and not only_extension
        and file_ext in excludes_extension
    ):
        return True

    exclude_empty = flags.get('exclude_empty', False)
    if exclude_empty and should_exclude_empty_file(file_path):
        return True

    ignore_patterns = flags.get('ignore_patterns', [])
    if ignore_patterns:
        for pattern in ignore_patterns:
            if _matches_path_pattern(file_path, pattern):
                return True

    return False
