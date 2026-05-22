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
    return tmp_path


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
        assert local_runtime._DIRECT_RUNNER in captured['cmd']  # noqa: SLF001
        assert str(root) in captured['cmd']

    def test_run_local_direct_when_handler_raises_returns_error(
        self,
        tmp_path,
        monkeypatch,
    ):
        from serverless import local_runtime

        root = _make_direct_lambda(tmp_path)
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
        assert captured['popen_cmd'] == [
            'docker',
            'run',
            '--rm',
            '-v',
            f'{build_path}:/var/task:ro',
            '-p',
            '9000:8080',
            'public.ecr.aws/lambda/python:3.13',
            'core.handler.lambda_handler',
        ]
        assert captured['run_cmd'][0] == 'curl'
        assert captured['terminated'] is True

    def test_run_local_rie_falls_back_to_direct_when_no_docker(
        self,
        tmp_path,
        monkeypatch,
    ):
        from serverless import local_runtime

        root = _make_direct_lambda(tmp_path)
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
