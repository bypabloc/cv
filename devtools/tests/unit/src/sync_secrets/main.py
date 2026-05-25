"""Unit tests for sync_secrets.main (router + targets).

Cubre el orquestador y los 3 targets:
- client routing (con mocks de gh_client)
- dev-cli validation (sin mocks — no toca remoto)
- server routing (con mocks de serverless.secrets_sync.sync_secrets_to_ssm)

Hermeticidad verificada con canary SECRET_VALUE en stdout capturado.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from sync_secrets.main import main


pytestmark = pytest.mark.unit


SECRET_VALUE = '__do_not_log_me_123abc__'


def _write_env(tmp_path: Path, category: str, env: str, contents: str) -> Path:
    cat_dir = tmp_path / 'docker' / 'env' / category
    cat_dir.mkdir(parents=True, exist_ok=True)
    p = cat_dir / f'.{env}'
    p.write_text(contents, encoding='utf-8')
    return p


def _catalog_dir(tmp_path: Path) -> Path:
    """Crea un catalog_dir vacio (sin YAMLs) — el target server tolera
    catalogo vacio y reporta SKIP.
    """
    d = tmp_path / 'serverless' / 'lambda' / 'resources' / 'secrets'
    d.mkdir(parents=True, exist_ok=True)
    # Placeholder YAML para que ServerCatalog.load() no falle
    (d / 'README.md').write_text('placeholder', encoding='utf-8')
    return d


@pytest.fixture
def patched_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr('sync_secrets.main.PROJECT_ROOT', tmp_path)
    return tmp_path


def test_main_client_only_skip_when_remote_matches(
    patched_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    Given category=client + remoto matchea local,
    When main,
    Then reporta SKIP y NO llama a set_variable. Valor NUNCA en stdout.
    """
    _write_env(
        patched_root,
        'client',
        'dev',
        f'PUBLIC_API_ENDPOINT={SECRET_VALUE}\n',
    )
    with (
        patch('sync_secrets.targets.gh_check_auth', return_value=None),
        patch('sync_secrets.targets.get_variable', return_value=SECRET_VALUE),
        patch('sync_secrets.targets.set_variable') as mock_set,
    ):
        rc = main(
            {
                'env': 'dev',
                'category': 'client',
                'dry_run': False,
                'keys': 'PUBLIC_API_ENDPOINT',
                'create_env': False,
                'aws_profile': '',
            }
        )
    assert rc == 0
    mock_set.assert_not_called()
    out = capsys.readouterr().out
    assert '[SKIP] PUBLIC_API_ENDPOINT' in out
    assert SECRET_VALUE not in out


def test_main_client_push_when_value_changes(
    patched_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    Given valor local difiere del remoto,
    When main,
    Then PUSH + set_variable llamado UNA vez. Valor NO en stdout.
    """
    _write_env(
        patched_root,
        'client',
        'dev',
        f'PUBLIC_API_ENDPOINT={SECRET_VALUE}\n',
    )
    with (
        patch('sync_secrets.targets.gh_check_auth', return_value=None),
        patch(
            'sync_secrets.targets.get_variable',
            return_value='https://api.old.example',
        ),
        patch('sync_secrets.targets.set_variable') as mock_set,
    ):
        rc = main(
            {
                'env': 'dev',
                'category': 'client',
                'dry_run': False,
                'keys': 'PUBLIC_API_ENDPOINT',
                'create_env': False,
                'aws_profile': '',
            }
        )
    assert rc == 0
    mock_set.assert_called_once_with('dev', 'PUBLIC_API_ENDPOINT', SECRET_VALUE)
    out = capsys.readouterr().out
    assert '[PUSH] PUBLIC_API_ENDPOINT' in out
    assert SECRET_VALUE not in out


def test_main_devcli_reports_local_only_no_remote(
    patched_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    Given category=dev-cli + .env tiene las keys requeridas,
    When main,
    Then reporta LOCAL-ONLY para cada una y NO sincroniza nada.
    """
    contents = (
        f'AWS_ACCESS_KEY_ID={SECRET_VALUE}\n'
        f'AWS_SECRET_ACCESS_KEY={SECRET_VALUE}\n'
        'NEON_DB_API_KEY=x\n'
        'CLOUDFLARE_API_TOKEN=y\n'
        'CLOUDFLARE_ACCOUNT_ID=z\n'
        'ACCOUNT_ID=637423614564\n'
    )
    _write_env(patched_root, 'dev-cli', 'dev', contents)
    with (
        patch('sync_secrets.targets.set_variable') as mock_set,
        patch('sync_secrets.targets.sync_secrets_to_ssm') as mock_ssm,
    ):
        rc = main(
            {
                'env': 'dev',
                'category': 'dev-cli',
                'dry_run': False,
                'keys': '',
                'create_env': False,
                'aws_profile': '',
            }
        )
    assert rc == 0
    mock_set.assert_not_called()
    mock_ssm.assert_not_called()
    out = capsys.readouterr().out
    assert '[LOCAL-ONLY] AWS_ACCESS_KEY_ID' in out
    assert '[LOCAL-ONLY] AWS_SECRET_ACCESS_KEY' in out
    # CRITICAL: NUNCA imprimir el valor real
    assert SECRET_VALUE not in out


def test_main_devcli_reports_missing_when_required_key_absent(
    patched_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    Given dev-cli .env sin AWS_SECRET_ACCESS_KEY,
    When main,
    Then reporta MISSING para esa key.
    """
    _write_env(
        patched_root,
        'dev-cli',
        'dev',
        'AWS_ACCESS_KEY_ID=AKIA...\n',  # solo una de las requeridas
    )
    rc = main(
        {
            'env': 'dev',
            'category': 'dev-cli',
            'dry_run': False,
            'keys': '',
            'create_env': False,
            'aws_profile': '',
        }
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert '[MISSING] AWS_SECRET_ACCESS_KEY' in out
    assert '[LOCAL-ONLY] AWS_ACCESS_KEY_ID' in out


def test_main_routes_only_requested_category(
    patched_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    Given category=client + sin .env de server,
    When main,
    Then NO ejecuta el target server (no print de server header).
    """
    _write_env(patched_root, 'client', 'dev', 'BASE_DOMAIN=x.example\n')
    with (
        patch('sync_secrets.targets.gh_check_auth', return_value=None),
        patch('sync_secrets.targets.get_variable', return_value=None),
        patch('sync_secrets.targets.set_variable'),
    ):
        main(
            {
                'env': 'dev',
                'category': 'client',
                'dry_run': True,
                'keys': 'BASE_DOMAIN',
                'create_env': False,
                'aws_profile': '',
            }
        )
    out = capsys.readouterr().out
    assert '[client]' in out
    assert '[server]' not in out
    assert '[dev-cli]' not in out


def test_main_category_all_runs_3_targets_in_order(
    patched_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    Given category=all + los 3 .env existen,
    When main,
    Then imprime los 3 headers en orden client -> server -> dev-cli.
    """
    _write_env(patched_root, 'client', 'dev', 'BASE_DOMAIN=x.example\n')
    _write_env(patched_root, 'server', 'dev', 'OWNER_EMAIL=u@x.com\n')
    _write_env(patched_root, 'dev-cli', 'dev', 'AWS_ACCESS_KEY_ID=AKIA...\n')
    _catalog_dir(patched_root)
    with (
        patch('sync_secrets.targets.gh_check_auth', return_value=None),
        patch('sync_secrets.targets.get_variable', return_value=None),
        patch('sync_secrets.targets.set_variable'),
        patch('sync_secrets.targets.sync_secrets_to_ssm', return_value=[]),
        patch(
            'sync_secrets.targets.ServerCatalog.load',
            return_value=type('C', (), {'for_stage': lambda self, s: ()})(),
        ),
    ):
        main(
            {
                'env': 'dev',
                'category': 'all',
                'dry_run': True,
                'keys': '',
                'create_env': False,
                'aws_profile': 'tfs-dev',
            }
        )
    out = capsys.readouterr().out
    client_idx = out.index('[client]')
    server_idx = out.index('[server]')
    devcli_idx = out.index('[dev-cli]')
    assert client_idx < server_idx < devcli_idx


def test_main_exit_2_on_error(
    patched_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    Given gh auth falla,
    When main category=client,
    Then exit 2 (error interno).
    """
    _write_env(patched_root, 'client', 'dev', 'BASE_DOMAIN=x.example\n')
    from sync_secrets.gh_client import GhClientError

    with patch(
        'sync_secrets.targets.gh_check_auth',
        side_effect=GhClientError('gh no auth'),
    ):
        rc = main(
            {
                'env': 'dev',
                'category': 'client',
                'dry_run': False,
                'keys': '',
                'create_env': False,
                'aws_profile': '',
            }
        )
    assert rc == 2
    assert 'gh no auth' in capsys.readouterr().out
