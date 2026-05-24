"""Unit tests for github_sync.main.

Path mirroring: devtools/github_sync/main.py -> this file.

Cubre el orquestador completo con mocks de gh_client. NUNCA invoca
gh real. Verifica que ningun valor del .env aparece en stdout
capturado por capsys.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from github_sync.gh_client import GhClientError
from github_sync.main import main


pytestmark = pytest.mark.unit


SECRET_VALUE = '__do_not_log_me_123abc__'


def _write_env(tmp_path: Path, env: str, contents: str) -> Path:
    """Crea docker/env/client/.{env} en tmp + monkeypatch PROJECT_ROOT."""
    client = tmp_path / 'docker' / 'env' / 'client'
    client.mkdir(parents=True, exist_ok=True)
    p = client / f'.{env}'
    p.write_text(contents, encoding='utf-8')
    return p


@pytest.fixture
def patched_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Reemplaza shared.paths.PROJECT_ROOT y github_sync.main.PROJECT_ROOT
    por tmp_path para aislar el test del repo real.
    """
    monkeypatch.setattr('github_sync.main.PROJECT_ROOT', tmp_path)
    return tmp_path


def test_main_exit_1_when_gh_auth_fails(
    patched_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    Given gh auth status falla,
    When main,
    Then exit 1 con mensaje claro.
    """
    _write_env(patched_root, 'dev', '')
    with patch(
        'github_sync.main.check_auth',
        side_effect=GhClientError('gh no autenticado'),
    ):
        rc = main(
            {
                'env': 'dev',
                'dry_run': False,
                'keys': '',
                'create_env': False,
            }
        )
    assert rc == 1
    captured = capsys.readouterr()
    assert 'gh no autenticado' in captured.out
    # NUNCA debe imprimir el valor secreto si el .env lo tuviera
    assert SECRET_VALUE not in captured.out


def test_main_exit_1_when_env_file_missing(
    patched_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    Given docker/env/client/.dev no existe,
    When main,
    Then exit 1 con mensaje claro.
    """
    with patch('github_sync.main.check_auth', return_value=None):
        rc = main(
            {
                'env': 'dev',
                'dry_run': False,
                'keys': '',
                'create_env': False,
            }
        )
    assert rc == 1
    assert 'No existe' in capsys.readouterr().out


def test_main_skip_when_remote_matches(
    patched_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    Given el valor remoto coincide con el local,
    When main,
    Then reporta SKIP y NO llama a set_variable.
    """
    _write_env(
        patched_root,
        'dev',
        f'PUBLIC_API_ENDPOINT={SECRET_VALUE}\n',
    )
    with (
        patch('github_sync.main.check_auth', return_value=None),
        patch(
            'github_sync.main.get_variable',
            return_value=SECRET_VALUE,
        ),
        patch('github_sync.main.set_variable') as mock_set,
    ):
        rc = main(
            {
                'env': 'dev',
                'dry_run': False,
                'keys': 'PUBLIC_API_ENDPOINT',
                'create_env': False,
            }
        )
    assert rc == 0
    mock_set.assert_not_called()
    out = capsys.readouterr().out
    assert '[SKIP] PUBLIC_API_ENDPOINT' in out
    # CRITICAL: el valor NO debe aparecer en stdout
    assert SECRET_VALUE not in out


def test_main_push_when_value_changes(
    patched_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    Given el valor local difiere del remoto,
    When main,
    Then PUSH + llama a set_variable una vez. El valor NO aparece en stdout.
    """
    _write_env(
        patched_root,
        'dev',
        f'PUBLIC_API_ENDPOINT={SECRET_VALUE}\n',
    )
    with (
        patch('github_sync.main.check_auth', return_value=None),
        patch(
            'github_sync.main.get_variable',
            return_value='https://api.old.example',
        ),
        patch('github_sync.main.set_variable') as mock_set,
    ):
        rc = main(
            {
                'env': 'dev',
                'dry_run': False,
                'keys': 'PUBLIC_API_ENDPOINT',
                'create_env': False,
            }
        )
    assert rc == 0
    mock_set.assert_called_once_with('dev', 'PUBLIC_API_ENDPOINT', SECRET_VALUE)
    out = capsys.readouterr().out
    assert '[PUSH] PUBLIC_API_ENDPOINT' in out
    assert SECRET_VALUE not in out


def test_main_create_when_remote_missing(
    patched_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    Given la variable no existe en GH,
    When main,
    Then CREATE + llama a set_variable.
    """
    _write_env(
        patched_root,
        'dev',
        f'PUBLIC_API_ENDPOINT={SECRET_VALUE}\n',
    )
    with (
        patch('github_sync.main.check_auth', return_value=None),
        patch('github_sync.main.get_variable', return_value=None),
        patch('github_sync.main.set_variable') as mock_set,
    ):
        rc = main(
            {
                'env': 'dev',
                'dry_run': False,
                'keys': 'PUBLIC_API_ENDPOINT',
                'create_env': False,
            }
        )
    assert rc == 0
    mock_set.assert_called_once()
    assert '[CREATE] PUBLIC_API_ENDPOINT' in capsys.readouterr().out


def test_main_missing_when_local_empty(
    patched_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    Given el .env tiene PUBLIC_API_ENDPOINT= (vacio),
    When main,
    Then MISSING + NO llama a set_variable.
    """
    _write_env(patched_root, 'dev', 'PUBLIC_API_ENDPOINT=\n')
    with (
        patch('github_sync.main.check_auth', return_value=None),
        patch('github_sync.main.set_variable') as mock_set,
    ):
        rc = main(
            {
                'env': 'dev',
                'dry_run': False,
                'keys': 'PUBLIC_API_ENDPOINT',
                'create_env': False,
            }
        )
    assert rc == 0
    mock_set.assert_not_called()
    assert '[MISSING] PUBLIC_API_ENDPOINT' in capsys.readouterr().out


def test_main_dry_run_does_not_call_set(
    patched_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    Given dry_run=True,
    When main detecta un cambio,
    Then NO llama a set_variable, reporta DRY-RUN.
    """
    _write_env(
        patched_root,
        'dev',
        f'PUBLIC_API_ENDPOINT={SECRET_VALUE}\n',
    )
    with (
        patch('github_sync.main.check_auth', return_value=None),
        patch('github_sync.main.get_variable', return_value=None),
        patch('github_sync.main.set_variable') as mock_set,
    ):
        rc = main(
            {
                'env': 'dev',
                'dry_run': True,
                'keys': 'PUBLIC_API_ENDPOINT',
                'create_env': False,
            }
        )
    assert rc == 0
    mock_set.assert_not_called()
    out = capsys.readouterr().out
    assert '[DRY-RUN CREATE] PUBLIC_API_ENDPOINT' in out
    assert SECRET_VALUE not in out


def test_main_keys_filter_rejects_unknown(
    patched_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    Given --keys con una key fuera del catalogo,
    When main,
    Then exit 1 con mensaje claro.
    """
    _write_env(patched_root, 'dev', 'BASE_DOMAIN=x.example\n')
    with patch('github_sync.main.check_auth', return_value=None):
        rc = main(
            {
                'env': 'dev',
                'dry_run': True,
                'keys': 'NOT_IN_CATALOG',
                'create_env': False,
            }
        )
    assert rc == 1
    assert 'fuera del catalogo' in capsys.readouterr().out
