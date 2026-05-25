"""Unit tests for ai_audit.auth (stub).

Path mirroring: devtools/ai_audit/auth.py -> este archivo.

Desde mayo 2026 ninguna tool activa usa storageState — auth.py es un
stub que devuelve valores seguros (VALID + None) para compat con
scraper.py. Estos tests verifican que el stub no falla y reporta lo
esperado.
"""

import pytest

from ai_audit import auth


pytestmark = pytest.mark.unit


def test_check_always_returns_valid() -> None:
    """
    Given el stub auth.check,
    When se invoca con cualquier tool name,
    Then retorna AuthState.VALID (ninguna tool usa storageState hoy).
    """
    assert auth.check('isitagentready') == auth.AuthState.VALID
    assert auth.check('validators') == auth.AuthState.VALID
    assert auth.check('lighthouse_psi') == auth.AuthState.VALID


def test_load_always_returns_none() -> None:
    """
    Given el stub auth.load,
    When se invoca con cualquier tool name,
    Then retorna None (no hay state que cargar).
    """
    assert auth.load('isitagentready') is None
    assert auth.load('validators') is None


def test_login_urls_is_empty() -> None:
    """
    Given LOGIN_URLS,
    When se inspecciona,
    Then esta vacio (ninguna tool requiere login).
    """
    assert auth.LOGIN_URLS == {}


def test_storage_path_compat_keeps_dir_layout() -> None:
    """
    Given un tool name,
    When auth.storage_path,
    Then retorna <STORAGE_DIR>/<tool>.json (compat con scripts viejos).
    """
    result = auth.storage_path('isitagentready')

    assert result.name == 'isitagentready.json'
    assert result.parent == auth.STORAGE_DIR


def test_auth_state_enum_keeps_three_values() -> None:
    """
    Given AuthState,
    When se inspecciona,
    Then mantiene VALID, EXPIRED, MISSING (compat con consumers).
    """
    assert auth.AuthState.VALID.value == 'VALID'
    assert auth.AuthState.EXPIRED.value == 'EXPIRED'
    assert auth.AuthState.MISSING.value == 'MISSING'
