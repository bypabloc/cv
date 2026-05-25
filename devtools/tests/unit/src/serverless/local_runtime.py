"""Unit tests for serverless.local_runtime - run-local sin SAM.

Path mirroring: devtools/serverless/local_runtime.py -> this file.

Cubre los dos modos de ejecucion local (RIE via Docker / directo via
subprocess con el .venv del backend), el fallback a directo cuando Docker
no esta, el manejo de un event JSON inexistente y el `_FakeContext`.
`subprocess`, `shutil.which`, `package_lambda` y `vendored_shared` estan
mockeados: ningun test levanta Docker ni empaqueta de verdad.
"""

import contextlib
import subprocess
import textwrap

import pytest


pytestmark = pytest.mark.unit


def _make_direct_lambda(tmp_path):
    """Crea un lambda de prueba con un core/handler.py importable.

    El handler devuelve un dict fijo para verificar que se ejecuto.
    Incluye un `pyproject.toml` minimo: `_run_direct` prepara el `.venv`
    aislado del lambda con `ensure_lambda_venv`, que lo exige.
    """
    core = tmp_path / 'core'
    core.mkdir()
    (core / '__init__.py').write_text('', encoding='utf-8')
    (core / 'handler.py').write_text(
        textwrap.dedent(
            """
            def lambda_handler(event, context):
                return {
                    'ok': True,
                    'event': event,
                    'fn': context.function_name,
                }
            """,
        ),
        encoding='utf-8',
    )
    (tmp_path / 'pyproject.toml').write_text(
        '[project]\nname = "probe"\nversion = "0.1.0"\n',
        encoding='utf-8',
    )
    return tmp_path


def _stub_venv(monkeypatch):
    """Mockea ensure_lambda_venv: no corre `uv`, devuelve un python fijo.

    `_run_direct` prepara el `.venv` aislado del lambda; en los tests no
    queremos correr `uv sync` de verdad.
    """
    from serverless import venv

    # `_run_direct` hace `from serverless.venv import ensure_lambda_venv`
    # (import local): se parchea en el modulo origen.
    monkeypatch.setattr(
        venv,
        'ensure_lambda_venv',
        lambda root: root / '.venv' / 'bin' / 'python',
    )


def _resolved(root, *, name='probe', runtime='python3.13', memory=256):
    """Construye un ResolvedLambda apuntando a `root`."""
    from serverless.resolve import ResolvedLambda

    return ResolvedLambda(
        mode='lambda-controller',
        root=root,
        manifest={
            'name': name,
            'runtime': runtime,
            'handler': 'core.handler.lambda_handler',
            'memory': memory,
        },
    )


@contextlib.contextmanager
def _noop_vendor(_root):
    """Context manager que reemplaza a vendored_shared sin copiar nada."""
    yield _root


class TestRunLocalDirect:
    """run_local con mode=DIRECT ejecuta el handler en un subproceso."""

    def test_run_local_direct_invokes_handler(self, tmp_path, monkeypatch):
        from serverless import local_runtime

        root = _make_direct_lambda(tmp_path)
        _stub_venv(monkeypatch)
        monkeypatch.setattr(
            local_runtime,
            'vendored_shared',
            _noop_vendor,
        )
        captured = {}

        def _fake_run(cmd, **_kwargs):
            captured['cmd'] = cmd
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout='{"ok": true}',
                stderr='',
            )

        monkeypatch.setattr(local_runtime.subprocess, 'run', _fake_run)

        rc = local_runtime.run_local(
            _resolved(root),
            event_path=None,
            mode=local_runtime.RuntimeMode.DIRECT,
        )

        assert rc == 0
        # El subproceso recibe el script runner + la raiz del lambda.
        assert local_runtime._DIRECT_RUNNER in captured['cmd']
        assert str(root) in captured['cmd']

    def test_run_local_direct_when_handler_raises_returns_error(
        self,
        tmp_path,
        monkeypatch,
    ):
        from serverless import local_runtime

        root = _make_direct_lambda(tmp_path)
        _stub_venv(monkeypatch)
        monkeypatch.setattr(
            local_runtime,
            'vendored_shared',
            _noop_vendor,
        )

        def _fake_run(cmd, **_kwargs):
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=1,
                stdout='',
                stderr='ValueError: boom',
            )

        monkeypatch.setattr(local_runtime.subprocess, 'run', _fake_run)

        rc = local_runtime.run_local(
            _resolved(root),
            event_path=None,
            mode=local_runtime.RuntimeMode.DIRECT,
        )

        assert rc == 1


class TestRunLocalRie:
    """run_local con mode=RIE construye y levanta el contenedor Docker."""

    def test_run_local_rie_builds_docker_command(
        self,
        tmp_path,
        monkeypatch,
    ):
        from serverless import local_runtime

        root = _make_direct_lambda(tmp_path)
        _stub_venv(monkeypatch)
        build_path = tmp_path / 'build'
        build_path.mkdir()

        monkeypatch.setattr(
            local_runtime.shutil,
            'which',
            lambda _name: '/usr/bin/docker',
        )
        monkeypatch.setattr(
            local_runtime,
            'package_lambda',
            lambda _root, *, runtime: (build_path, set(), []),
        )
        monkeypatch.setattr(local_runtime.time, 'sleep', lambda _s: None)

        captured = {}

        class _FakePopen:
            def __init__(self, cmd, *_args, **_kwargs):
                captured['popen_cmd'] = cmd

            def terminate(self):
                captured['terminated'] = True

            def wait(self):
                return 0

        def _fake_run(cmd, **_kwargs):
            captured['run_cmd'] = cmd
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout='{"statusCode": 200}',
                stderr='',
            )

        monkeypatch.setattr(local_runtime.subprocess, 'Popen', _FakePopen)
        monkeypatch.setattr(local_runtime.subprocess, 'run', _fake_run)

        rc = local_runtime.run_local(
            _resolved(root),
            event_path=None,
            mode=local_runtime.RuntimeMode.RIE,
        )

        assert rc == 0
        # El comando incluye env vars del modo local antes del -v. Tras
        # filtrar los pares `-e KEY=VALUE`, debe quedar el comando base.
        popen_cmd = captured['popen_cmd']
        # docker, run, --rm al inicio
        assert popen_cmd[:3] == ['docker', 'run', '--rm']
        # Las ultimas posiciones son la imagen + handler
        assert popen_cmd[-2:] == [
            'public.ecr.aws/lambda/python:3.13',
            'core.handler.lambda_handler',
        ]
        # Y debe estar el mount + port (en algun lugar antes de la imagen)
        assert '-v' in popen_cmd
        assert f'{build_path}:/var/task:ro' in popen_cmd
        assert '-p' in popen_cmd
        assert '9000:8080' in popen_cmd
        assert captured['run_cmd'][0] == 'curl'
        assert captured['terminated'] is True

    def test_run_local_rie_falls_back_to_direct_when_no_docker(
        self,
        tmp_path,
        monkeypatch,
    ):
        from serverless import local_runtime

        root = _make_direct_lambda(tmp_path)
        _stub_venv(monkeypatch)
        monkeypatch.setattr(
            local_runtime.shutil,
            'which',
            lambda _name: None,
        )
        monkeypatch.setattr(
            local_runtime,
            'vendored_shared',
            _noop_vendor,
        )

        def _explode(*_args, **_kwargs):
            raise AssertionError('no debe empaquetar sin Docker')

        monkeypatch.setattr(local_runtime, 'package_lambda', _explode)
        monkeypatch.setattr(
            local_runtime.subprocess,
            'run',
            lambda cmd, **_k: subprocess.CompletedProcess(
                args=cmd, returncode=0, stdout='{"ok": true}', stderr=''
            ),
        )

        rc = local_runtime.run_local(
            _resolved(root),
            event_path=None,
            mode=local_runtime.RuntimeMode.RIE,
        )

        assert rc == 0


class TestRunLocalEventErrors:
    """run_local valida la existencia del event JSON antes de ejecutar."""

    def test_run_local_when_event_missing_returns_error(
        self,
        tmp_path,
        monkeypatch,
    ):
        from serverless import local_runtime

        root = _make_direct_lambda(tmp_path)
        _stub_venv(monkeypatch)
        monkeypatch.setattr(
            local_runtime.shutil,
            'which',
            lambda _name: None,
        )

        rc = local_runtime.run_local(
            _resolved(root),
            event_path=tmp_path / 'no-such-event.json',
            mode=local_runtime.RuntimeMode.DIRECT,
        )

        assert rc == 1

    def test_run_local_when_event_invalid_json_returns_error(
        self,
        tmp_path,
        monkeypatch,
    ):
        from serverless import local_runtime

        root = _make_direct_lambda(tmp_path)
        _stub_venv(monkeypatch)
        event_file = tmp_path / 'bad.json'
        event_file.write_text('{not json', encoding='utf-8')
        monkeypatch.setattr(
            local_runtime.shutil,
            'which',
            lambda _name: None,
        )

        rc = local_runtime.run_local(
            _resolved(root),
            event_path=event_file,
            mode=local_runtime.RuntimeMode.DIRECT,
        )

        assert rc == 1


class TestFakeContext:
    """_FakeContext expone los atributos que el handler espera."""

    def test_fake_context_has_required_attributes(self):
        from serverless.local_runtime import _FakeContext

        context = _FakeContext(
            function_name='contact-form',
            memory_limit_in_mb=512,
        )

        assert context.function_name == 'contact-form'
        assert context.memory_limit_in_mb == 512
        assert context.aws_request_id == 'local-invoke'
        assert context.get_remaining_time_in_millis() == 300_000


class TestRuntimeMode:
    """RuntimeMode enum mapea los valores del flag --runtime-mode."""

    def test_runtime_mode_values_match_flag_strings(self):
        from serverless.local_runtime import RuntimeMode

        assert RuntimeMode.RIE.value == 'rie'
        assert RuntimeMode.DIRECT.value == 'direct'


class TestLocalEnvVars:
    """_local_env_vars mezcla defaults + manifest.env + catalogo .env."""

    def test_defaults_include_stage_local(self):
        from serverless.local_runtime import _local_env_vars

        resolved = _resolved(__import__('pathlib').Path('/tmp/probe'))

        env = _local_env_vars(resolved)

        assert env['STAGE'] == 'local'
        assert env['ENVIRONMENT'] == 'local'
        assert env['POWERTOOLS_SERVICE_NAME'] == 'probe'

    def test_manifest_env_default_and_local_merged(self, tmp_path):
        from serverless.local_runtime import _local_env_vars
        from serverless.resolve import ResolvedLambda

        resolved = ResolvedLambda(
            mode='lambda-controller',
            root=tmp_path,
            manifest={
                'name': 'probe',
                'runtime': 'python3.13',
                'handler': 'core.handler.lambda_handler',
                'memory': 256,
                'env': {
                    'default': {'LOG_LEVEL': 'INFO', 'X': 'default'},
                    'local': {'X': 'local-override'},
                },
            },
        )

        env = _local_env_vars(resolved)

        assert env['LOG_LEVEL'] == 'INFO'
        assert env['X'] == 'local-override'

    def test_no_secrets_when_lambda_uses_no_secrets(self, tmp_path):
        from serverless.local_runtime import _local_env_vars
        from serverless.resolve import ResolvedLambda

        resolved = ResolvedLambda(
            mode='lambda-controller',
            root=tmp_path,
            manifest={
                'name': 'no-secrets',
                'runtime': 'python3.13',
                'handler': 'core.handler.lambda_handler',
                'memory': 256,
                'uses': {'secrets': []},
            },
        )

        env = _local_env_vars(resolved)

        # No DB_URL ni TURNSTILE_SECRET_KEY si el lambda no los usa
        assert 'DB_URL' not in env
        assert 'TURNSTILE_SECRET_KEY' not in env
