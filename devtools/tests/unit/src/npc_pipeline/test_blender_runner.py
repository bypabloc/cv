"""Unit tests for npc_pipeline.blender_runner.

Path mirroring: devtools/npc_pipeline/blender_runner.py -> this file.

Mockea subprocess.run para no requerir Blender instalado (el pipeline
real corre headless contra un binario que el dev instala localmente,
ver .claude/docs/journey-npc-realism/01-pipeline-blender-headless.md).
"""

import subprocess

import pytest


pytestmark = pytest.mark.unit


def _completed(*, returncode=0, stdout='', stderr=''):
    return subprocess.CompletedProcess(
        args=[],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


class TestFindBlenderVersion:
    def test_when_blender_not_in_path_returns_none(self, monkeypatch):
        from npc_pipeline.blender_runner import find_blender_version

        def _raise(*_a, **_k):
            raise FileNotFoundError

        monkeypatch.setattr('subprocess.run', _raise)

        assert find_blender_version() is None

    def test_when_output_matches_returns_version_tuple(self, monkeypatch):
        from npc_pipeline.blender_runner import find_blender_version

        monkeypatch.setattr(
            'subprocess.run',
            lambda *a, **k: _completed(stdout='Blender 4.2.3\n'),
        )

        assert find_blender_version() == (4, 2, 3)

    def test_when_output_unparseable_returns_none(self, monkeypatch):
        from npc_pipeline.blender_runner import find_blender_version

        monkeypatch.setattr(
            'subprocess.run',
            lambda *a, **k: _completed(stdout='not a version string'),
        )

        assert find_blender_version() is None

    def test_when_returncode_nonzero_returns_none(self, monkeypatch):
        from npc_pipeline.blender_runner import find_blender_version

        monkeypatch.setattr(
            'subprocess.run',
            lambda *a, **k: _completed(returncode=1),
        )

        assert find_blender_version() is None


class TestCheckBlenderAvailable:
    def test_when_not_found_returns_false_with_hint(self, monkeypatch):
        from npc_pipeline.blender_runner import check_blender_available

        monkeypatch.setattr(
            'npc_pipeline.blender_runner.find_blender_version',
            lambda **_k: None,
        )

        ok, message = check_blender_available()

        assert ok is False
        assert 'no encontrado en PATH' in message

    def test_when_version_below_minimum_returns_false(self, monkeypatch):
        from npc_pipeline.blender_runner import check_blender_available

        monkeypatch.setattr(
            'npc_pipeline.blender_runner.find_blender_version',
            lambda **_k: (3, 6, 0),
        )

        ok, message = check_blender_available()

        assert ok is False
        assert '>= 4.2' in message

    def test_when_version_meets_minimum_returns_true(self, monkeypatch):
        from npc_pipeline.blender_runner import check_blender_available

        monkeypatch.setattr(
            'npc_pipeline.blender_runner.find_blender_version',
            lambda **_k: (4, 2, 0),
        )

        ok, message = check_blender_available()

        assert ok is True
        assert 'Blender 4.2.0 OK' in message


class TestScriptPath:
    def test_when_script_exists_returns_path(self):
        from npc_pipeline.blender_runner import script_path

        path = script_path('generate_mesh.py')

        assert path.name == 'generate_mesh.py'
        assert path.exists()

    def test_when_script_missing_raises(self):
        from npc_pipeline.blender_runner import NpcPipelineError
        from npc_pipeline.blender_runner import script_path

        with pytest.raises(NpcPipelineError, match='no encontrado'):
            script_path('does_not_exist.py')


class TestBuildBlenderCommand:
    def test_builds_expected_argv(self):
        from npc_pipeline.blender_runner import build_blender_command

        command = build_blender_command(
            script_name='export_glb.py',
            script_args=['--input=a.blend', '--output=b.glb'],
        )

        assert command[0] == 'blender'
        assert command[1] == '--background'
        assert command[2] == '--python-exit-code'
        assert command[3] == '1'
        assert command[4] == '--python'
        assert command[5].endswith('export_glb.py')
        assert command[6] == '--'
        assert command[7:] == ['--input=a.blend', '--output=b.glb']

    def test_uses_custom_blender_bin(self):
        from npc_pipeline.blender_runner import build_blender_command

        command = build_blender_command(
            script_name='export_glb.py',
            script_args=[],
            blender_bin='/opt/blender/blender',
        )

        assert command[0] == '/opt/blender/blender'


class TestRunBlenderScript:
    def test_when_blender_unavailable_raises(self, monkeypatch):
        from npc_pipeline.blender_runner import NpcPipelineError
        from npc_pipeline.blender_runner import run_blender_script

        monkeypatch.setattr(
            'npc_pipeline.blender_runner.check_blender_available',
            lambda **_k: (False, 'Blender no encontrado en PATH'),
        )

        with pytest.raises(NpcPipelineError, match='no encontrado en PATH'):
            run_blender_script(script_name='export_glb.py', script_args=[])

    def test_when_script_exits_nonzero_raises_with_output(self, monkeypatch):
        from npc_pipeline.blender_runner import NpcPipelineError
        from npc_pipeline.blender_runner import run_blender_script

        monkeypatch.setattr(
            'npc_pipeline.blender_runner.check_blender_available',
            lambda **_k: (True, 'Blender 4.2.0 OK'),
        )
        monkeypatch.setattr(
            'subprocess.run',
            lambda *a, **k: _completed(
                returncode=1,
                stdout='algo paso',
                stderr='Traceback...',
            ),
        )

        with pytest.raises(NpcPipelineError, match='fallo'):
            run_blender_script(script_name='export_glb.py', script_args=[])

    def test_when_script_succeeds_returns_completed_process(self, monkeypatch):
        from npc_pipeline.blender_runner import run_blender_script

        monkeypatch.setattr(
            'npc_pipeline.blender_runner.check_blender_available',
            lambda **_k: (True, 'Blender 4.2.0 OK'),
        )
        monkeypatch.setattr(
            'subprocess.run',
            lambda *a, **k: _completed(stdout='Malla guardada en x.blend'),
        )

        result = run_blender_script(
            script_name='generate_mesh.py', script_args=[]
        )

        assert result.returncode == 0
        assert 'Malla guardada' in result.stdout
