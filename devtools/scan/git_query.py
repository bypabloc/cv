"""Git introspection helpers for the scan script.

All git interaction lives here: tracked files, base branch detection, mode
collectors (staged/unstaged/untracked/stash/unmerged), deleted files. The
rest of scan only consumes plain Python data structures from this module.
"""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
import os
import sys

import git

from scan.ignore import get_ignored_files_from_gitignore
from scan.ignore import is_ignored_by_pattern


def get_git_ignored_files() -> list[str]:
    """Files ignored by git that aren't already covered by ``.gitignore`` lines."""
    try:
        repo = git.Repo('.')
        ignored_patterns = get_ignored_files_from_gitignore()

        git_ignored_files_output = repo.git.ls_files(
            '--others',
            '--ignored',
            '--exclude-standard',
        ).splitlines()

        unique_ignored_files = [
            os.path.normpath(file_path)
            for file_path in git_ignored_files_output
            if not is_ignored_by_pattern(
                os.path.normpath(file_path), ignored_patterns
            )
        ]
    except git.InvalidGitRepositoryError:
        print('Advertencia: No es un repositorio Git válido')
        return []
    else:
        return unique_ignored_files


def get_git_tracked_files() -> set[str]:
    """Set of files tracked by git in the current repo (empty on errors)."""
    try:
        repo = git.Repo('.')
        tracked_files = repo.git.ls_files().splitlines()
        return set(tracked_files)
    except git.InvalidGitRepositoryError, git.GitCommandError, OSError:
        return set()


def get_git_tracked_directories() -> set[str]:
    """Directories that contain at least one git-tracked file."""
    tracked_files = get_git_tracked_files()
    tracked_dirs: set[str] = set()

    for file_path in tracked_files:
        dir_path = os.path.dirname(file_path)
        while dir_path:
            tracked_dirs.add(dir_path)
            parent_dir = os.path.dirname(dir_path)
            if parent_dir == dir_path:
                break
            dir_path = parent_dir

    return tracked_dirs


def _get_available_base_branches(repo: git.Repo) -> list[str]:
    """Candidate base branches that exist in remote or local refs."""
    candidates = ['main', 'master', 'dev', 'develop']
    remote_refs = {ref.name for ref in repo.refs if 'origin/' in ref.name}
    available = [b for b in candidates if f'origin/{b}' in remote_refs]
    if available:
        return available
    local_refs = {ref.name for ref in repo.heads}
    return [b for b in candidates if b in local_refs]


def _resolve_base_for_current(
    current: str | None,
    available: list[str],
) -> str | None:
    """If current branch IS a base branch, return its upstream target."""
    if current not in available:
        return None
    if current in ('dev', 'develop'):
        for b in ('master', 'main'):
            if b in available:
                return b
    return available[0] if available else 'main'


def _commit_distance(repo: git.Repo, ref: str) -> int | None:
    """Count commits ahead of ref, or None on error."""
    try:
        return int(repo.git.rev_list('--count', f'{ref}..HEAD'))
    except git.GitCommandError:
        return None


def _find_closest_branch(
    repo: git.Repo,
    available: list[str],
) -> str:
    """Branch with the fewest commits ahead (closest ancestor)."""
    best_branch = available[0]
    best_distance: float = float('inf')
    for branch in available:
        distance = _commit_distance(repo, f'origin/{branch}')
        if distance is not None and distance < best_distance:
            best_distance = distance
            best_branch = branch
    return best_branch


def get_git_base_branch() -> str:
    """Detect the parent branch from which the current branch was created.

    Hierarchy: feature/* -> dev -> master/main. Falls back to ``main`` on
    any git error.
    """
    try:
        repo = git.Repo('.')
        try:
            current = repo.active_branch.name
        except TypeError:
            current = None

        available = _get_available_base_branches(repo)
        if not available:
            return 'main'

        upstream = _resolve_base_for_current(current, available)
        if upstream is not None:
            return upstream

        return _find_closest_branch(repo, available)
    except git.InvalidGitRepositoryError, git.GitCommandError, OSError:
        return 'main'


def _resolve_base_ref(repo: git.Repo, base_branch: str) -> str:
    """Resolve to ``origin/<branch>`` if it exists, else local branch name."""
    base_ref = base_branch
    try:
        repo.commit(f'origin/{base_branch}')
        base_ref = f'origin/{base_branch}'
    except git.BadName, git.GitCommandError:
        try:
            repo.commit(base_branch)
        except git.BadName, git.GitCommandError:
            print(
                f'Advertencia: No se encontro rama base {base_branch}',
                file=sys.stderr,
            )
    return base_ref


def _collect_staged_files(repo: git.Repo) -> list[str]:
    """Files in the staging area (added/copied/modified/renamed)."""
    staged_output = repo.git.diff(
        '--cached',
        '--name-only',
        '--diff-filter=ACMR',
        'HEAD',
    )
    if not staged_output:
        return []
    return [f.strip() for f in staged_output.splitlines() if f.strip()]


def _collect_unstaged_files(repo: git.Repo) -> list[str]:
    """Files with unstaged changes in the working tree."""
    return [item.a_path for item in repo.index.diff(None) if item.a_path]


def _collect_stash_files(repo: git.Repo) -> list[str]:
    """Files modified in the most recent stash entry.

    Includes untracked files captured via ``git stash push -u`` by inspecting
    the third parent commit (``stash@{0}^3``) when present.
    """
    try:
        stash_list = repo.git.stash('list').splitlines()
        if not stash_list:
            return []
        files: set[str] = set()
        # Tracked changes (staged + unstaged) live in stash@{0}.
        tracked = repo.git.stash(
            'show',
            '--name-only',
            'stash@{0}',
        ).splitlines()
        files.update(f.strip() for f in tracked if f.strip())
        # Untracked files (when stashed with -u) live in stash@{0}^3.
        # Sin -u no existe ese commit y git lanza un error que es esperado.
        try:
            untracked = repo.git.show(
                '--name-only',
                '--pretty=format:',
                'stash@{0}^3',
            ).splitlines()
        except git.GitCommandError:
            untracked = []
        files.update(f.strip() for f in untracked if f.strip())
        return sorted(files)
    except (git.GitCommandError, git.GitCommandNotFound, OSError) as e:
        print(f'No se pudo obtener archivos del stash: {e}')
    return []


def _collect_unmerged_files(repo: git.Repo) -> list[str]:
    """Files diff'd between current branch and the resolved base ref."""
    try:
        base_branch = get_git_base_branch()

        try:
            current_branch = repo.active_branch.name
        except TypeError:
            current_branch = None

        if current_branch is not None and current_branch == base_branch:
            return []

        base_ref = _resolve_base_ref(repo, base_branch)
        diff_output = repo.git.diff('--name-only', f'{base_ref}...HEAD')
        if not diff_output:
            return []
        return [f.strip() for f in diff_output.splitlines() if f.strip()]
    except (
        git.InvalidGitRepositoryError,
        git.GitCommandError,
        OSError,
    ) as e:
        print(f'Error obteniendo archivos no mergeados: {e}')
        return []


def get_git_files_by_mode(mode: str = 'changed') -> dict[str, list[str]]:
    """Collect files for the requested git mode.

    Modes: ``changed``, ``staged``, ``unstaged``, ``stash``, ``unmerged``,
    ``all``. Returns a dict with all categories so the caller can pick
    whichever it needs.
    """
    try:
        repo = git.Repo('.')
        result: dict[str, list[str]] = {
            'staged': [],
            'unstaged': [],
            'untracked': [],
            'stash': [],
            'unmerged': [],
            'changed': [],
        }

        if mode in ('changed', 'staged', 'unmerged', 'all'):
            result['staged'] = _collect_staged_files(repo)

        if mode in ('changed', 'unstaged', 'unmerged', 'all'):
            result['unstaged'] = _collect_unstaged_files(repo)

        if mode in ('changed', 'unmerged', 'all'):
            result['untracked'] = list(repo.untracked_files)

        if mode in ('stash', 'all'):
            result['stash'] = _collect_stash_files(repo)

        if mode in ('unmerged', 'all'):
            result['unmerged'] = _collect_unmerged_files(repo)

        result['changed'] = list(
            set(result['staged'] + result['unstaged'] + result['untracked']),
        )
    except (
        git.InvalidGitRepositoryError,
        git.GitCommandError,
        OSError,
    ) as e:
        print(f"Error obteniendo archivos por modo '{mode}': {e}")
        return {
            'staged': [],
            'unstaged': [],
            'untracked': [],
            'stash': [],
            'changed': [],
        }
    else:
        return result


def _get_uncommitted_diff_files(
    repo: git.Repo,
    base_branch: str,
) -> list[str]:
    """Diff files vs base branch, with sane fallbacks."""
    try:
        base_ref = _resolve_base_ref(repo, base_branch)

        unmerged_files: set[str] = set()
        diff_output = repo.git.diff('--name-only', f'{base_ref}...HEAD')
        if diff_output:
            unmerged_files = {
                f.strip() for f in diff_output.splitlines() if f.strip()
            }

        git_files = get_git_files_by_mode('changed')
        unmerged_files.update(git_files['changed'])
        return list(unmerged_files)
    except (
        git.InvalidGitRepositoryError,
        git.GitCommandError,
        OSError,
    ):
        return _get_uncommitted_fallback(repo, base_branch)


def _get_uncommitted_fallback(
    repo: git.Repo,
    base_branch: str,
) -> list[str]:
    """Fallback for retrieving uncommitted files when full diff fails."""
    try:
        diff_output = repo.git.diff('--name-only', base_branch)
        return [f.strip() for f in diff_output.splitlines() if f.strip()]
    except git.GitCommandError, OSError:
        git_files = get_git_files_by_mode('changed')
        return git_files['changed']


def get_uncommitted_files() -> list[str]:
    """Files with uncommitted changes vs the resolved base branch."""
    try:
        repo = git.Repo('.')
        base_branch = get_git_base_branch()

        try:
            current_branch = repo.active_branch.name
        except TypeError:
            current_branch = None

        if current_branch == base_branch:
            git_files = get_git_files_by_mode('changed')
            return git_files['changed']

        return _get_uncommitted_diff_files(repo, base_branch)

    except (
        git.InvalidGitRepositoryError,
        git.GitCommandError,
        OSError,
    ) as e:
        print(f'Error obteniendo archivos no mergeados: {e}')
        return []


def _collect_deleted_from_index(repo: git.Repo) -> list[str]:
    """Files marked as deleted in the index (working tree + HEAD)."""
    deleted = [
        item.a_path for item in repo.index.diff(None) if item.deleted_file
    ]
    deleted.extend(
        item.a_path for item in repo.index.diff('HEAD') if item.deleted_file
    )
    return deleted


def _collect_deleted_from_branch(
    repo: git.Repo,
    base_branch: str,
) -> list[str]:
    """Files deleted vs base branch, falling back to index-only."""
    try:
        base_ref = f'origin/{base_branch}'
        if base_ref not in [ref.name for ref in repo.refs]:
            base_ref = base_branch

        deleted_output = repo.git.diff(
            '--name-only',
            '--diff-filter=D',
            base_ref,
        )
        deleted = (
            [
                item.strip()
                for item in deleted_output.splitlines()
                if item.strip()
            ]
            if deleted_output
            else []
        )

        deleted.extend(_collect_deleted_from_index(repo))
    except (
        git.InvalidGitRepositoryError,
        git.GitCommandError,
        OSError,
    ):
        return _collect_deleted_from_index(repo)
    else:
        return deleted


def get_deleted_files() -> list[str]:
    """Files deleted vs the base branch."""
    try:
        repo = git.Repo('.')
        base_branch = get_git_base_branch()

        try:
            current_branch = repo.active_branch.name
        except TypeError:
            current_branch = None

        if current_branch == base_branch:
            deleted_files = _collect_deleted_from_index(repo)
        else:
            deleted_files = _collect_deleted_from_branch(repo, base_branch)

        return list(set(deleted_files))

    except (
        git.InvalidGitRepositoryError,
        git.GitCommandError,
        OSError,
    ) as e:
        print(f'Error obteniendo archivos eliminados: {e}')
        return []


def get_file_deleted_date(file_path: str) -> datetime | None:
    """Best-effort deletion date for ``file_path`` from git history."""
    try:
        repo = git.Repo('.')
        commits = list(repo.iter_commits(paths=file_path, max_count=10))

        for commit in commits:
            for item in commit.diff(
                commit.parents[0] if commit.parents else None,
            ):
                if item.deleted_file and item.a_path == file_path:
                    return datetime.fromtimestamp(
                        commit.committed_date,
                        tz=UTC,
                    )

        if commits:
            result = datetime.fromtimestamp(
                commits[0].committed_date,
                tz=UTC,
            )
        else:
            result = None
    except git.InvalidGitRepositoryError, git.GitCommandError, OSError:
        return None
    else:
        return result


def _get_file_content_from_commits(
    repo: git.Repo,
    file_path: str,
) -> str | None:
    """Recover file content from the most recent commit that touched it."""
    try:
        commits = list(repo.iter_commits(paths=file_path, max_count=1))
        if commits:
            commit = commits[0]
            return repo.git.show(f'{commit.hexsha}:{file_path}')
    except git.GitCommandError, git.BadName:
        print(
            f'No se pudo obtener contenido de {file_path} desde commits',
        )
    return None


def get_file_content_from_git(
    file_path: str,
    base_branch: str | None = None,
) -> str | None:
    """Recover the content of a deleted file from git history."""
    try:
        repo = git.Repo('.')

        if base_branch is None:
            base_branch = get_git_base_branch()

        try:
            base_ref = f'origin/{base_branch}'
            if base_ref not in [ref.name for ref in repo.refs]:
                base_ref = base_branch

            content = repo.git.show(f'{base_ref}:{file_path}')
        except git.GitCommandError, git.BadName:
            content = _get_file_content_from_commits(repo, file_path)
    except git.InvalidGitRepositoryError, git.GitCommandError, OSError:
        return None
    else:
        return content
