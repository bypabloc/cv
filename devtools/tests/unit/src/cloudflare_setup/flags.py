"""Unit tests for cloudflare_setup.flags.

Path mirroring: devtools/cloudflare_setup/flags.py -> this file.

Cubre:
- phase posicional valido / invalido / default
- --env=dev|prod aceptado; otros rechazados
- flag() rellena defaults y normaliza
"""

from cloudflare_setup.flags import VALID_PHASES
from cloudflare_setup.flags import flag
import pytest


pytestmark = pytest.mark.unit


def _argv(monkeypatch, *args):
    """Setea sys.argv como `run.py cloudflare_setup <args>`."""
    monkeypatch.setattr('sys.argv', ['run.py', 'cloudflare_setup', *args])


# ---- positional phase + defaults ---------------------------------------


class TestPhasePositional:
    """phase es posicional. Default = all si no se pasa."""

    @pytest.mark.parametrize('phase', sorted(VALID_PHASES))
    def test_valid_phase_accepted(self, monkeypatch, phase):
        _argv(monkeypatch, phase)
        result = flag({})
        assert result['phase'] == phase

    def test_default_phase_is_all(self, monkeypatch):
        _argv(monkeypatch)
        result = flag({})
        assert result['phase'] == 'all'

    def test_invalid_phase_raises(self, monkeypatch):
        _argv(monkeypatch, 'nope')
        with pytest.raises(ValueError, match='phase invalido'):
            flag({})


# ---- --env flag --------------------------------------------------------


class TestEnvFlag:
    """--env=dev|prod. Default = prod."""

    @pytest.mark.parametrize('env', ['dev', 'prod'])
    def test_valid_env_accepted(self, monkeypatch, env):
        _argv(monkeypatch, 'trigger')
        result = flag({'env': env})
        assert result['env'] == env

    def test_default_env_is_prod(self, monkeypatch):
        _argv(monkeypatch, 'trigger')
        result = flag({})
        assert result['env'] == 'prod'

    def test_invalid_env_raises(self, monkeypatch):
        _argv(monkeypatch, 'trigger')
        with pytest.raises(ValueError, match='env invalido'):
            flag({'env': 'local'})


# ---- combinations -----------------------------------------------------


class TestCombinations:
    def test_trigger_dev_passes(self, monkeypatch):
        _argv(monkeypatch, 'trigger')
        result = flag({'env': 'dev'})
        assert result['phase'] == 'trigger'
        assert result['env'] == 'dev'

    def test_all_dev_passes(self, monkeypatch):
        _argv(monkeypatch, 'all')
        result = flag({'env': 'dev'})
        assert result['phase'] == 'all'
        assert result['env'] == 'dev'

    def test_status_default_env_is_prod(self, monkeypatch):
        _argv(monkeypatch, 'status')
        result = flag({})
        assert result['phase'] == 'status'
        assert result['env'] == 'prod'
