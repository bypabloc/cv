"""Unit tests for serverless.secrets_sync - sync .env -> SSM.

Path mirroring: devtools/serverless/secrets_sync.py -> this file.

Cubre AC-4..AC-7 y AC-10 (no-leaking) del plan
docs/specs/serverless-secrets-catalog/.

Mockea subprocess.run para emular aws-cli sin tocar AWS.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import textwrap

import pytest


pytestmark = pytest.mark.unit


_CANARY = 'CANARY_NEVER_LOG_THIS_b8a7c2e3f9d1'


def _write_yaml(directory, name, content):
    yaml_path = directory / f'{name}.yaml'
    yaml_path.write_text(content, encoding='utf-8')
    return yaml_path


def _write_catalog_dir(tmp_path):
    """Crea un catalogo minimo con turnstile-secret + owner-email."""
    catalog_dir = tmp_path / 'catalog'
    catalog_dir.mkdir()
    _write_yaml(
        catalog_dir,
        'turnstile-secret',
        textwrap.dedent(
            """
            kind: ssm-parameter
            name: turnstile-secret
            description: cf turnstile
            path: /portfolio/${stage}/turnstile-secret
            ssm_type: SecureString
            source_env_var: TURNSTILE_SECRET_KEY
            target_env_var: SSM_TURNSTILE_SECRET_PATH
            stages: [dev, stage, prod]
            required: true
            """,
        ).strip(),
    )
    _write_yaml(
        catalog_dir,
        'owner-email',
        textwrap.dedent(
            """
            kind: ssm-parameter
            name: owner-email
            description: owner email
            path: /portfolio/owner-email
            ssm_type: String
            source_env_var: OWNER_EMAIL
            target_env_var: SSM_OWNER_EMAIL_PATH
            stages: [dev, stage, prod]
            required: true
            """,
        ).strip(),
    )
    return catalog_dir


def _write_env(tmp_path, content):
    env_file = tmp_path / '.dev'
    env_file.write_text(content, encoding='utf-8')
    return env_file


class _SubprocessStub:
    """Captura las llamadas a subprocess.run y emula aws-cli."""

    def __init__(self, *, get_responses, put_returns=0):
        self.calls: list[list[str]] = []
        self.get_responses = list(get_responses)
        self.put_returns = put_returns

    def __call__(self, cmd, *args, **kwargs):
        self.calls.append(list(cmd))
        if 'get-parameter' in cmd:
            response = self.get_responses.pop(0)
            if response is None:
                return subprocess.CompletedProcess(
                    cmd,
                    returncode=255,
                    stdout='',
                    stderr='ParameterNotFound',
                )
            return subprocess.CompletedProcess(
                cmd,
                returncode=0,
                stdout=json.dumps({'Parameter': {'Value': response}}),
                stderr='',
            )
        if 'put-parameter' in cmd:
            return subprocess.CompletedProcess(
                cmd,
                returncode=self.put_returns,
                stdout='',
                stderr='',
            )
        return subprocess.CompletedProcess(
            cmd, returncode=0, stdout='', stderr=''
        )


class TestLoadEnvFile:
    def test_when_file_does_not_exist_raises(self, tmp_path):
        from serverless.secrets_sync import SyncError
        from serverless.secrets_sync import load_env_file

        with pytest.raises(SyncError, match='no existe'):
            load_env_file(tmp_path / '.dev')

    def test_when_file_valid_returns_dict(self, tmp_path):
        from serverless.secrets_sync import load_env_file

        env = _write_env(tmp_path, 'KEY1=value1\nKEY2=value2\n')

        result = load_env_file(env)

        assert result == {'KEY1': 'value1', 'KEY2': 'value2'}

    def test_ignores_comments_and_empty_lines(self, tmp_path):
        from serverless.secrets_sync import load_env_file

        env = _write_env(
            tmp_path,
            '# comment\n\nKEY=value\n# another\n',
        )

        result = load_env_file(env)

        assert result == {'KEY': 'value'}


class TestSyncFlow:
    def test_when_value_matches_ssm_returns_skip(self, tmp_path, monkeypatch):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_sync import SyncAction
        from serverless.secrets_sync import sync_secrets_to_ssm

        catalog_dir = _write_catalog_dir(tmp_path)
        env = _write_env(
            tmp_path,
            'TURNSTILE_SECRET_KEY=mysecret\nOWNER_EMAIL=test@example.com\n',
        )
        # Orden alfabetico: owner-email primero, turnstile-secret despues
        stub = _SubprocessStub(get_responses=['test@example.com', 'mysecret'])
        monkeypatch.setattr('subprocess.run', stub)

        results = sync_secrets_to_ssm(
            stage='dev',
            env_file=env,
            catalog=Catalog.load(catalog_dir),
        )

        assert {r.action for r in results} == {SyncAction.SKIP}

    def test_when_value_differs_returns_push(self, tmp_path, monkeypatch):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_sync import SyncAction
        from serverless.secrets_sync import sync_secrets_to_ssm

        catalog_dir = _write_catalog_dir(tmp_path)
        env = _write_env(
            tmp_path,
            'TURNSTILE_SECRET_KEY=newvalue\nOWNER_EMAIL=test@example.com\n',
        )
        # Orden alfabetico: owner-email primero, turnstile-secret despues
        stub = _SubprocessStub(
            get_responses=['test@example.com', 'oldvalue'],
        )
        monkeypatch.setattr('subprocess.run', stub)

        results = sync_secrets_to_ssm(
            stage='dev',
            env_file=env,
            catalog=Catalog.load(catalog_dir),
        )

        actions = {r.name: r.action for r in results}
        assert actions['turnstile-secret'] == SyncAction.PUSH
        assert actions['owner-email'] == SyncAction.SKIP

    def test_when_ssm_param_not_exists_returns_push(
        self,
        tmp_path,
        monkeypatch,
    ):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_sync import SyncAction
        from serverless.secrets_sync import sync_secrets_to_ssm

        catalog_dir = _write_catalog_dir(tmp_path)
        env = _write_env(
            tmp_path,
            'TURNSTILE_SECRET_KEY=brandnew\nOWNER_EMAIL=test@example.com\n',
        )
        # Orden alfabetico: owner-email primero, turnstile-secret despues
        stub = _SubprocessStub(get_responses=['test@example.com', None])
        monkeypatch.setattr('subprocess.run', stub)

        results = sync_secrets_to_ssm(
            stage='dev',
            env_file=env,
            catalog=Catalog.load(catalog_dir),
        )

        actions = {r.name: r.action for r in results}
        assert actions['turnstile-secret'] == SyncAction.PUSH

    def test_when_required_env_missing_raises(self, tmp_path, monkeypatch):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_sync import SyncError
        from serverless.secrets_sync import sync_secrets_to_ssm

        catalog_dir = _write_catalog_dir(tmp_path)
        env = _write_env(tmp_path, 'OWNER_EMAIL=test@example.com\n')
        stub = _SubprocessStub(get_responses=[None])
        monkeypatch.setattr('subprocess.run', stub)

        with pytest.raises(SyncError, match='TURNSTILE_SECRET_KEY ausente'):
            sync_secrets_to_ssm(
                stage='dev',
                env_file=env,
                catalog=Catalog.load(catalog_dir),
            )

    def test_when_stage_local_raises(self, tmp_path):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_sync import SyncError
        from serverless.secrets_sync import sync_secrets_to_ssm

        catalog_dir = _write_catalog_dir(tmp_path)
        env = _write_env(tmp_path, 'KEY=value\n')

        with pytest.raises(SyncError, match='`local`'):
            sync_secrets_to_ssm(
                stage='local',
                env_file=env,
                catalog=Catalog.load(catalog_dir),
            )

    def test_dry_run_does_not_call_put_parameter(self, tmp_path, monkeypatch):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_sync import sync_secrets_to_ssm

        catalog_dir = _write_catalog_dir(tmp_path)
        env = _write_env(
            tmp_path,
            'TURNSTILE_SECRET_KEY=new\nOWNER_EMAIL=test@example.com\n',
        )
        stub = _SubprocessStub(get_responses=['old', 'test@example.com'])
        monkeypatch.setattr('subprocess.run', stub)

        sync_secrets_to_ssm(
            stage='dev',
            env_file=env,
            catalog=Catalog.load(catalog_dir),
            dry_run=True,
        )

        put_calls = [c for c in stub.calls if 'put-parameter' in c]
        assert put_calls == []

    def test_only_filters_secrets(self, tmp_path, monkeypatch):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_sync import sync_secrets_to_ssm

        catalog_dir = _write_catalog_dir(tmp_path)
        env = _write_env(
            tmp_path,
            'TURNSTILE_SECRET_KEY=v\nOWNER_EMAIL=test@example.com\n',
        )
        stub = _SubprocessStub(get_responses=['v'])
        monkeypatch.setattr('subprocess.run', stub)

        results = sync_secrets_to_ssm(
            stage='dev',
            env_file=env,
            catalog=Catalog.load(catalog_dir),
            only=('turnstile-secret',),
        )

        assert [r.name for r in results] == ['turnstile-secret']


class TestNoLeaking:
    """AC-10: el valor nunca aparece en stdout, args ni traceback."""

    def test_canary_never_in_subprocess_args(self, tmp_path, monkeypatch):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_sync import sync_secrets_to_ssm

        catalog_dir = _write_catalog_dir(tmp_path)
        env = _write_env(
            tmp_path,
            f'TURNSTILE_SECRET_KEY={_CANARY}\nOWNER_EMAIL=test@example.com\n',
        )
        stub = _SubprocessStub(get_responses=[None, None])
        monkeypatch.setattr('subprocess.run', stub)

        sync_secrets_to_ssm(
            stage='dev',
            env_file=env,
            catalog=Catalog.load(catalog_dir),
        )

        for call in stub.calls:
            joined = ' '.join(str(x) for x in call)
            assert _CANARY not in joined, (
                f'canary leaked en aws-cli args: {call}'
            )

    def test_canary_never_in_stdout(self, tmp_path, monkeypatch, capsys):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_sync import sync_secrets_to_ssm

        catalog_dir = _write_catalog_dir(tmp_path)
        env = _write_env(
            tmp_path,
            f'TURNSTILE_SECRET_KEY={_CANARY}\nOWNER_EMAIL=test@example.com\n',
        )
        stub = _SubprocessStub(get_responses=[None, None])
        monkeypatch.setattr('subprocess.run', stub)

        sync_secrets_to_ssm(
            stage='dev',
            env_file=env,
            catalog=Catalog.load(catalog_dir),
        )

        captured = capsys.readouterr()
        assert _CANARY not in captured.out
        assert _CANARY not in captured.err

    def test_canary_never_in_exception_message(
        self,
        tmp_path,
        monkeypatch,
    ):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_sync import SyncError
        from serverless.secrets_sync import sync_secrets_to_ssm

        catalog_dir = _write_catalog_dir(tmp_path)
        env = _write_env(
            tmp_path,
            f'TURNSTILE_SECRET_KEY={_CANARY}\nOWNER_EMAIL=test@example.com\n',
        )

        # Forzar fallo del get-parameter
        def _fail(cmd, *a, **k):
            if 'get-parameter' in cmd:
                return subprocess.CompletedProcess(
                    cmd,
                    returncode=1,
                    stdout='',
                    stderr='SomeAwsError',
                )
            return subprocess.CompletedProcess(
                cmd,
                returncode=0,
                stdout='',
                stderr='',
            )

        monkeypatch.setattr('subprocess.run', _fail)

        try:
            sync_secrets_to_ssm(
                stage='dev',
                env_file=env,
                catalog=Catalog.load(catalog_dir),
            )
        except SyncError as exc:
            assert _CANARY not in str(exc)
        else:
            pytest.fail('expected SyncError')

    def test_secret_spec_repr_no_value(self, tmp_path):
        """SecretSpec.repr nunca incluye el valor (porque no lo guarda)."""
        from serverless.secrets_catalog import Catalog

        catalog_dir = _write_catalog_dir(tmp_path)
        catalog = Catalog.load(catalog_dir)
        for spec in catalog.by_name.values():
            assert _CANARY not in repr(spec)


class TestPutSsmTempfile:
    """put_ssm_value pasa el valor via tempfile, no como argumento."""

    def test_put_uses_file_protocol_not_arg(self, tmp_path, monkeypatch):
        from serverless.secrets_catalog import Catalog
        from serverless.secrets_sync import put_ssm_value

        catalog_dir = _write_catalog_dir(tmp_path)
        catalog = Catalog.load(catalog_dir)
        spec = catalog.get('turnstile-secret')

        captured_cmds: list[list[str]] = []

        def _capture(cmd, *a, **k):
            captured_cmds.append(list(cmd))
            return subprocess.CompletedProcess(
                cmd,
                returncode=0,
                stdout='',
                stderr='',
            )

        monkeypatch.setattr('subprocess.run', _capture)

        put_ssm_value(
            spec,
            'dev',
            _CANARY,
            profile=None,
            region='us-east-1',
        )

        assert len(captured_cmds) == 1
        cmd = captured_cmds[0]
        # El valor NUNCA debe aparecer como arg
        for arg in cmd:
            assert _CANARY not in str(arg), f'canary leaked in arg: {arg!r}'
        # Debe haber un --value file://...
        assert any(str(arg).startswith('file://') for arg in cmd), (
            f'no file:// in cmd: {cmd}'
        )
