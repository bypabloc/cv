"""Unit tests for npc_pipeline.flags.

Path mirroring: devtools/npc_pipeline/flags.py -> this file.
"""

import pytest


pytestmark = pytest.mark.unit


class TestFlagCommandValidation:
    def test_when_command_missing_raises(self, monkeypatch):
        from npc_pipeline.flags import flag

        monkeypatch.setattr('sys.argv', ['run.py', 'npc_pipeline'])

        with pytest.raises(ValueError, match='Falta el subcomando'):
            flag({})

    def test_when_command_invalid_raises(self, monkeypatch):
        from npc_pipeline.flags import flag

        monkeypatch.setattr(
            'sys.argv',
            ['run.py', 'npc_pipeline', 'not-a-command'],
        )

        with pytest.raises(ValueError, match='Comando invalido'):
            flag({})

    def test_when_status_command_valid_returns_flags(self, monkeypatch):
        from npc_pipeline.flags import flag

        monkeypatch.setattr('sys.argv', ['run.py', 'npc_pipeline', 'status'])

        result = flag({})

        assert result['command'] == 'status'
        assert result['blender_bin'] == 'blender'


class TestRequiredFlagsPerCommand:
    def test_when_generate_mesh_missing_output_raises(self, monkeypatch):
        from npc_pipeline.flags import flag

        monkeypatch.setattr(
            'sys.argv',
            ['run.py', 'npc_pipeline', 'generate-mesh'],
        )

        with pytest.raises(ValueError, match='--output'):
            flag({})

    def test_when_generate_mesh_has_output_passes(self, monkeypatch):
        from npc_pipeline.flags import flag

        monkeypatch.setattr(
            'sys.argv',
            ['run.py', 'npc_pipeline', 'generate-mesh'],
        )

        result = flag({'output': 'npc-base.blend'})

        assert result['output'] == 'npc-base.blend'

    def test_when_rig_missing_input_and_output_raises(self, monkeypatch):
        from npc_pipeline.flags import flag

        monkeypatch.setattr('sys.argv', ['run.py', 'npc_pipeline', 'rig'])

        with pytest.raises(ValueError, match='--input, --output'):
            flag({})

    def test_when_export_missing_output_raises(self, monkeypatch):
        from npc_pipeline.flags import flag

        monkeypatch.setattr('sys.argv', ['run.py', 'npc_pipeline', 'export'])

        with pytest.raises(ValueError, match='--output'):
            flag({'input': 'npc-rigged.blend'})

    def test_when_install_addons_without_mpfb2_zip_passes(self, monkeypatch):
        """mpfb2_zip es opcional: Rigify ya viene con Blender."""
        from npc_pipeline.flags import flag

        monkeypatch.setattr(
            'sys.argv',
            ['run.py', 'npc_pipeline', 'install-addons'],
        )

        result = flag({})

        assert result['command'] == 'install-addons'


class TestDefaults:
    def test_skip_compress_defaults_false(self, monkeypatch):
        from npc_pipeline.flags import flag

        monkeypatch.setattr(
            'sys.argv',
            ['run.py', 'npc_pipeline', 'export'],
        )

        result = flag({'input': 'a.blend', 'output': 'b.glb'})

        assert result['skip_compress'] is False

    def test_blender_bin_defaults_to_blender(self, monkeypatch):
        from npc_pipeline.flags import flag

        monkeypatch.setattr('sys.argv', ['run.py', 'npc_pipeline', 'status'])

        result = flag({})

        assert result['blender_bin'] == 'blender'

    def test_explicit_blender_bin_is_preserved(self, monkeypatch):
        from npc_pipeline.flags import flag

        monkeypatch.setattr('sys.argv', ['run.py', 'npc_pipeline', 'status'])

        result = flag({'blender_bin': '/opt/blender/blender'})

        assert result['blender_bin'] == '/opt/blender/blender'


class TestDescribe:
    def test_lists_all_valid_commands(self):
        from npc_pipeline.flags import VALID_COMMANDS
        from npc_pipeline.flags import describe

        described_names = {c['name'] for c in describe()['commands']}

        assert described_names == set(VALID_COMMANDS)
