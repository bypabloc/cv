"""Tests de validacion de flags del script bypass_token (logica pura).

El conftest de devtools agrega devtools/ al sys.path, asi que
`bypass_token` resuelve como paquete.
"""

import sys

from bypass_token.flags import flag
import pytest


def _argv(*args: str) -> list[str]:
    return ['run.py', 'bypass_token', *args]


def test_flag_keygen_defaults(monkeypatch) -> None:
    """
    Given el comando keygen sin flags,
    When flag(),
    Then command=keygen + envs=[dev] (default).
    """
    monkeypatch.setattr(sys, 'argv', _argv('keygen'))

    result = flag({})

    assert result['command'] == 'keygen'
    assert result['envs'] == ['dev']
    assert result['dry_run'] is False


def test_flag_mint_env_dev(monkeypatch) -> None:
    """
    Given el comando mint --env=dev,
    When flag(),
    Then command=mint + env=dev + ttl=300 (default int).
    """
    monkeypatch.setattr(sys, 'argv', _argv('mint'))

    result = flag({'env': 'dev'})

    assert result['command'] == 'mint'
    assert result['env'] == 'dev'
    assert result['ttl'] == 300


def test_flag_missing_command_raises(monkeypatch) -> None:
    """Given sin comando posicional, When flag(), Then ValueError."""
    monkeypatch.setattr(sys, 'argv', _argv())

    with pytest.raises(ValueError, match='Falta el comando'):
        flag({})


def test_flag_invalid_command_raises(monkeypatch) -> None:
    """Given un comando invalido, When flag(), Then ValueError."""
    monkeypatch.setattr(sys, 'argv', _argv('nope'))

    with pytest.raises(ValueError, match='Comando invalido'):
        flag({})


def test_flag_keygen_rejects_prod_env(monkeypatch) -> None:
    """Given --envs incluye prod, When flag(), Then ValueError (nunca prod)."""
    monkeypatch.setattr(sys, 'argv', _argv('keygen'))

    with pytest.raises(ValueError, match='NUNCA prod'):
        flag({'envs': 'dev,prod'})


def test_flag_mint_rejects_prod_env(monkeypatch) -> None:
    """Given mint --env=prod, When flag(), Then ValueError."""
    monkeypatch.setattr(sys, 'argv', _argv('mint'))

    with pytest.raises(ValueError, match='--env invalido'):
        flag({'env': 'prod'})
