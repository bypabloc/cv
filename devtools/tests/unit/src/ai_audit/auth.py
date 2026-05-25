"""Unit tests for ai_audit.auth.

Path mirroring: devtools/ai_audit/auth.py -> this file.
"""

import json
from pathlib import Path
import stat

import pytest

from ai_audit import auth


pytestmark = pytest.mark.unit


@pytest.fixture
def tmp_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Apunta auth.STORAGE_DIR a un directorio temporal por test."""
    storage_dir = tmp_path / 'ai-audit'
    monkeypatch.setattr(auth, 'STORAGE_DIR', storage_dir)
    return storage_dir


def test_check_when_file_missing_then_missing(tmp_storage: Path) -> None:
    """
    Given no existe el archivo,
    When auth.check,
    Then retorna AuthState.MISSING.
    """
    assert auth.check('ahrefs') == auth.AuthState.MISSING


def test_check_when_valid_file_then_valid(tmp_storage: Path) -> None:
    """
    Given archivo con cookies no-vacias,
    When auth.check,
    Then retorna AuthState.VALID.
    """
    tmp_storage.mkdir(parents=True)
    (tmp_storage / 'ahrefs.json').write_text(
        json.dumps({'cookies': [{'name': 'x', 'value': 'y'}], 'origins': []}),
    )

    assert auth.check('ahrefs') == auth.AuthState.VALID


def test_check_when_cookies_empty_then_expired(tmp_storage: Path) -> None:
    """
    Given archivo con cookies=[],
    When auth.check,
    Then retorna AuthState.EXPIRED.
    """
    tmp_storage.mkdir(parents=True)
    (tmp_storage / 'ahrefs.json').write_text(
        json.dumps({'cookies': [], 'origins': []}),
    )

    assert auth.check('ahrefs') == auth.AuthState.EXPIRED


def test_check_when_corrupted_json_then_expired(tmp_storage: Path) -> None:
    """
    Given archivo con JSON invalido,
    When auth.check,
    Then retorna AuthState.EXPIRED (no crashea).
    """
    tmp_storage.mkdir(parents=True)
    (tmp_storage / 'ahrefs.json').write_text('not json {{{')

    assert auth.check('ahrefs') == auth.AuthState.EXPIRED


def test_save_when_called_then_writes_with_0600(tmp_storage: Path) -> None:
    """
    Given un dict valido,
    When auth.save,
    Then el archivo se crea con perms 0600 y dir 0700.
    """
    state = {'cookies': [{'name': 'a', 'value': 'b'}], 'origins': []}

    auth.save('ahrefs', state)

    path = tmp_storage / 'ahrefs.json'
    assert path.exists()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(tmp_storage.stat().st_mode) == 0o700
    assert json.loads(path.read_text()) == state


def test_load_when_exists_then_returns_dict(tmp_storage: Path) -> None:
    """
    Given un archivo guardado previamente,
    When auth.load,
    Then retorna el dict parseado.
    """
    tmp_storage.mkdir(parents=True)
    state = {'cookies': [{'a': 1}], 'origins': []}
    (tmp_storage / 'ahrefs.json').write_text(json.dumps(state))

    assert auth.load('ahrefs') == state


def test_load_when_missing_then_returns_none(tmp_storage: Path) -> None:
    """
    Given no existe el archivo,
    When auth.load,
    Then retorna None.
    """
    assert auth.load('ahrefs') is None


def test_storage_path_when_called_then_includes_tool_name(
    tmp_storage: Path,
) -> None:
    """
    Given un tool name,
    When auth.storage_path,
    Then retorna <STORAGE_DIR>/<tool>.json.
    """
    assert auth.storage_path('semrush') == tmp_storage / 'semrush.json'


def test_login_urls_when_inspected_then_only_ahrefs_and_semrush() -> None:
    """
    Given el dict LOGIN_URLS,
    When se inspecciona,
    Then contiene solo ahrefs y semrush (las 2 tools con auth).
    """
    assert set(auth.LOGIN_URLS.keys()) == {'ahrefs', 'semrush'}
