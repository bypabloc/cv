"""File system helpers for the scan script.

Tiny wrappers that read on-disk files and stat metadata. Kept apart from
the git side (``git_query.py``) so it is obvious which functions touch
the filesystem vs the git ref database.
"""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
import os


def get_file_dates(
    file_path: str,
) -> tuple[datetime | None, datetime | None]:
    """Return (created, modified) datetimes from filesystem stat info."""
    try:
        if not os.path.exists(file_path):
            return None, None

        stat_info = os.stat(file_path)
        modified_time = datetime.fromtimestamp(
            stat_info.st_mtime,
            tz=UTC,
        )

        if hasattr(stat_info, 'st_birthtime'):
            created_time = datetime.fromtimestamp(
                stat_info.st_birthtime,
                tz=UTC,
            )
        else:
            created_time = datetime.fromtimestamp(
                stat_info.st_ctime,
                tz=UTC,
            )
    except OSError, PermissionError:
        return None, None
    else:
        return created_time, modified_time


def get_file_content(
    file_path: str,
    exclude_empty: bool = False,
) -> str | bool | None:
    """Read a file safely with utf-8/latin-1 fallbacks.

    Returns:
        - The text content (str)
        - ``False`` for empty files when ``exclude_empty=False``
        - ``None`` when the file does not exist or is empty under
          ``exclude_empty=True``
        - A placeholder string for binary files
    """
    try:
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

                if exclude_empty and (not content or content.strip() == ''):
                    return None
                if not exclude_empty and (not content or content.strip() == ''):
                    return False

                return content
        except UnicodeDecodeError:
            try:
                with open(file_path, encoding='latin1') as f:
                    content = f.read()

                    if exclude_empty and (not content or content.strip() == ''):
                        return None
                    if not exclude_empty and (
                        not content or content.strip() == ''
                    ):
                        return False

                    return content
            except UnicodeDecodeError, PermissionError:
                file_size = os.path.getsize(file_path)
                return f'<Archivo binario - {file_size} bytes>'
    except OSError, PermissionError:
        return None
