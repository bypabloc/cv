"""Unit tests for npc_pipeline.main (dispatch).

Path mirroring: devtools/npc_pipeline/main.py -> this file.

Mockea npc_pipeline.blender_runner (no invoca Blender real).
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


class TestDispatchStatus:
    def test_when_blender_available_returns_zero(self, monkeypatch, capsys):
        from npc_pipeline.main import main

        monkeypatch.setattr(
            'npc_pipeline.blender_runner.check_blender_available',
            lambda **_k: (True, 'Blender 4.2.0 OK'),
        )

        exit_code = main({'command': 'status', 'blender_bin': 'blender'})

        assert exit_code == 0
        assert 'Blender 4.2.0 OK' in capsys.readouterr().out

    def test_when_blender_missing_returns_one(self, monkeypatch, capsys):
        from npc_pipeline.main import main

        monkeypatch.setattr(
            'npc_pipeline.blender_runner.check_blender_available',
            lambda **_k: (False, 'Blender no encontrado en PATH'),
        )

        exit_code = main({'command': 'status', 'blender_bin': 'blender'})

        assert exit_code == 1
        assert 'no encontrado' in capsys.readouterr().out


class TestDispatchInstallAddons:
    def test_passes_mpfb2_zip_flag_to_script(self, monkeypatch):
        from npc_pipeline.main import main

        captured = {}

        def _fake_run(*, script_name, script_args, blender_bin):
            captured['script_name'] = script_name
            captured['script_args'] = script_args
            return _completed(stdout='MPFB2 instalado')

        monkeypatch.setattr(
            'npc_pipeline.blender_runner.run_blender_script',
            _fake_run,
        )

        exit_code = main(
            {
                'command': 'install-addons',
                'mpfb2_zip': 'devtools/npc_pipeline/vendor/mpfb2.zip',
                'blender_bin': 'blender',
            },
        )

        assert exit_code == 0
        assert captured['script_name'] == 'install_addons.py'
        assert captured['script_args'] == [
            '--mpfb2-zip=devtools/npc_pipeline/vendor/mpfb2.zip',
        ]

    def test_without_mpfb2_zip_still_runs_script(self, monkeypatch):
        from npc_pipeline.main import main

        captured = {}

        def _fake_run(*, script_name, script_args, blender_bin):
            captured['script_args'] = script_args
            return _completed(stdout='solo Rigify habilitado')

        monkeypatch.setattr(
            'npc_pipeline.blender_runner.run_blender_script',
            _fake_run,
        )

        exit_code = main(
            {'command': 'install-addons', 'blender_bin': 'blender'}
        )

        assert exit_code == 0
        assert captured['script_args'] == []


class TestDispatchRig:
    def test_builds_input_and_output_args(self, monkeypatch):
        from npc_pipeline.main import main

        captured = {}

        def _fake_run(*, script_name, script_args, blender_bin):
            captured['script_name'] = script_name
            captured['script_args'] = script_args
            return _completed(stdout='Rig guardado')

        monkeypatch.setattr(
            'npc_pipeline.blender_runner.run_blender_script',
            _fake_run,
        )

        exit_code = main(
            {
                'command': 'rig',
                'input': 'npc-base.blend',
                'output': 'npc-rigged.blend',
                'blender_bin': 'blender',
            },
        )

        assert exit_code == 0
        assert captured['script_name'] == 'rig_mesh.py'
        assert captured['script_args'] == [
            '--input=npc-base.blend',
            '--output=npc-rigged.blend',
        ]


class TestDispatchAnimate:
    def test_builds_input_and_output_args(self, monkeypatch):
        from npc_pipeline.main import main

        captured = {}

        def _fake_run(*, script_name, script_args, blender_bin):
            captured['script_name'] = script_name
            captured['script_args'] = script_args
            return _completed(stdout='Animaciones guardadas')

        monkeypatch.setattr(
            'npc_pipeline.blender_runner.run_blender_script',
            _fake_run,
        )

        exit_code = main(
            {
                'command': 'animate',
                'input': 'npc-rigged.blend',
                'output': 'npc-animated.blend',
                'blender_bin': 'blender',
            },
        )

        assert exit_code == 0
        assert captured['script_name'] == 'animate.py'
        assert captured['script_args'] == [
            '--input=npc-rigged.blend',
            '--output=npc-animated.blend',
        ]


class TestDispatchGenerateMesh:
    def test_builds_output_and_preview_dir_args(self, monkeypatch):
        from npc_pipeline.main import main

        captured = {}

        def _fake_run(*, script_name, script_args, blender_bin):
            captured['script_name'] = script_name
            captured['script_args'] = script_args
            return _completed(stdout='ok')

        monkeypatch.setattr(
            'npc_pipeline.blender_runner.run_blender_script',
            _fake_run,
        )

        exit_code = main(
            {
                'command': 'generate-mesh',
                'output': 'npc-base.blend',
                'preview_dir': 'tmp/npc-pipeline',
                'blender_bin': 'blender',
            },
        )

        assert exit_code == 0
        assert captured['script_name'] == 'generate_mesh.py'
        assert '--output=npc-base.blend' in captured['script_args']
        assert '--preview-dir=tmp/npc-pipeline' in captured['script_args']


class TestDispatchExport:
    def test_compresses_with_gltf_transform_by_default(
        self,
        monkeypatch,
        tmp_path,
    ):
        from npc_pipeline.main import main

        monkeypatch.setattr(
            'npc_pipeline.blender_runner.run_blender_script',
            lambda **_k: _completed(stdout='raw export ok'),
        )
        captured_cmd = {}

        def _fake_subprocess_run(cmd, **_k):
            captured_cmd['cmd'] = cmd
            return _completed(returncode=0)

        monkeypatch.setattr('subprocess.run', _fake_subprocess_run)

        output = tmp_path / 'npc-base.glb'
        exit_code = main(
            {
                'command': 'export',
                'input': str(tmp_path / 'npc-rigged.blend'),
                'output': str(output),
                'skip_compress': False,
                'blender_bin': 'blender',
            },
        )

        assert exit_code == 0
        assert captured_cmd['cmd'][:3] == [
            'npx',
            '--yes',
            '@gltf-transform/cli',
        ]
        assert captured_cmd['cmd'][3] == 'meshopt'
        assert captured_cmd['cmd'][-1] == str(output)

    def test_deletes_raw_glb_after_successful_compress(
        self,
        monkeypatch,
        tmp_path,
    ):
        from npc_pipeline.main import main

        monkeypatch.setattr(
            'npc_pipeline.blender_runner.run_blender_script',
            lambda **_k: _completed(stdout='raw export ok'),
        )
        monkeypatch.setattr(
            'subprocess.run',
            lambda *_a, **_k: _completed(returncode=0),
        )

        output = tmp_path / 'npc-base.glb'
        raw_glb = output.with_suffix('.raw.glb')
        raw_glb.write_bytes(b'fake-raw-glb-bytes')

        exit_code = main(
            {
                'command': 'export',
                'input': str(tmp_path / 'npc-rigged.blend'),
                'output': str(output),
                'skip_compress': False,
                'blender_bin': 'blender',
            },
        )

        assert exit_code == 0
        assert raw_glb.exists() is False

    def test_keeps_raw_glb_when_compress_fails(self, monkeypatch, tmp_path):
        from npc_pipeline.main import main

        monkeypatch.setattr(
            'npc_pipeline.blender_runner.run_blender_script',
            lambda **_k: _completed(stdout='raw export ok'),
        )
        monkeypatch.setattr(
            'subprocess.run',
            lambda *_a, **_k: _completed(returncode=1),
        )

        output = tmp_path / 'npc-base.glb'
        raw_glb = output.with_suffix('.raw.glb')
        raw_glb.write_bytes(b'fake-raw-glb-bytes')

        exit_code = main(
            {
                'command': 'export',
                'input': str(tmp_path / 'npc-rigged.blend'),
                'output': str(output),
                'skip_compress': False,
                'blender_bin': 'blender',
            },
        )

        assert exit_code == 1
        assert raw_glb.exists() is True

    def test_skip_compress_renames_raw_glb_without_gltf_transform(
        self,
        monkeypatch,
        tmp_path,
    ):
        from npc_pipeline.main import main

        monkeypatch.setattr(
            'npc_pipeline.blender_runner.run_blender_script',
            lambda **_k: _completed(stdout='raw export ok'),
        )
        subprocess_calls = []
        monkeypatch.setattr(
            'subprocess.run',
            lambda *a, **k: subprocess_calls.append(a) or _completed(),
        )

        output = tmp_path / 'npc-base.glb'
        raw_glb = output.with_suffix('.raw.glb')
        raw_glb.write_bytes(b'fake-glb-bytes')

        exit_code = main(
            {
                'command': 'export',
                'input': str(tmp_path / 'npc-rigged.blend'),
                'output': str(output),
                'skip_compress': True,
                'blender_bin': 'blender',
            },
        )

        assert exit_code == 0
        assert output.read_bytes() == b'fake-glb-bytes'
        assert subprocess_calls == []  # glTF-Transform NUNCA se invoca


class TestMainErrorHandling:
    def test_when_blender_runner_raises_returns_one(self, monkeypatch, capsys):
        from npc_pipeline.blender_runner import NpcPipelineError
        from npc_pipeline.main import main

        def _raise(**_k):
            raise NpcPipelineError('Blender no encontrado en PATH')

        monkeypatch.setattr(
            'npc_pipeline.blender_runner.run_blender_script',
            _raise,
        )

        exit_code = main(
            {
                'command': 'rig',
                'input': 'a.blend',
                'output': 'b.blend',
                'blender_bin': 'blender',
            },
        )

        assert exit_code == 1
        assert 'no encontrado en PATH' in capsys.readouterr().out

    def test_when_command_unimplemented_returns_one(self, capsys):
        from npc_pipeline.main import main

        exit_code = main({'command': 'not-a-real-command'})

        assert exit_code == 1
        assert 'no implementado' in capsys.readouterr().out
