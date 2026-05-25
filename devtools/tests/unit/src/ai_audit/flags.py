"""Unit tests for ai_audit.flags.

Path mirroring: devtools/ai_audit/flags.py -> this file.
"""

import sys
from unittest import mock

from ai_audit.flags import flag
import pytest


pytestmark = pytest.mark.unit


def _argv(*args: str) -> list[str]:
    """Helper: simula sys.argv para `run.py ai_audit [args...]`."""
    return ['run.py', 'ai_audit', *args]


def test_flag_when_no_args_then_default_audit() -> None:
    """
    Given args vacios,
    When flag,
    Then subcommand='audit', env='prod', niches=los 6, tools=las 3.
    """
    with mock.patch.object(sys, 'argv', _argv()):
        result = flag({})

    assert result['subcommand'] == 'audit'
    assert result['env'] == 'prod'
    assert result['niches'] == [
        'generic',
        'hub',
        'fintech',
        'architect',
        'leader',
        'vibe',
    ]
    assert result['tools'] == [
        'isitagentready',
        'validators',
        'lighthouse_psi',
    ]
    assert result['targets'] == []


def test_flag_when_unknown_tool_then_raises() -> None:
    """
    Given --tools=foo,
    When flag,
    Then raises ValueError con 'unknown tool: foo'.
    """
    with (
        mock.patch.object(sys, 'argv', _argv()),
        pytest.raises(
            ValueError,
            match='unknown tool: foo',
        ),
    ):
        flag({'tools': 'foo'})


def test_flag_when_invalid_env_then_raises() -> None:
    """
    Given --env=qa,
    When flag,
    Then raises ValueError con --env='qa' invalido.
    """
    with (
        mock.patch.object(sys, 'argv', _argv()),
        pytest.raises(
            ValueError,
            match="--env='qa' invalido",
        ),
    ):
        flag({'env': 'qa'})


def test_flag_when_unknown_niche_then_raises() -> None:
    """
    Given --niches=hub,unknown,
    When flag,
    Then raises ValueError con 'unknown niches: unknown'.
    """
    with (
        mock.patch.object(sys, 'argv', _argv()),
        pytest.raises(
            ValueError,
            match='unknown niches: unknown',
        ),
    ):
        flag({'niches': 'hub,unknown'})


def test_flag_when_targets_path_missing_slash_then_raises() -> None:
    """
    Given --targets=hub:projects (sin /),
    When flag,
    Then raises ValueError con 'path must start with /'.
    """
    with (
        mock.patch.object(sys, 'argv', _argv()),
        pytest.raises(
            ValueError,
            match='path must start with /',
        ),
    ):
        flag({'targets': 'hub:projects'})


def test_flag_when_setup_subcommand_then_rejected() -> None:
    """
    Given subcomando 'setup' (eliminado en mayo 2026),
    When flag,
    Then raises ValueError con 'Subcomando desconocido' (solo audit y report).
    """
    with (
        mock.patch.object(sys, 'argv', _argv('setup')),
        pytest.raises(
            ValueError,
            match='Subcomando desconocido',
        ),
    ):
        flag({})


def test_flag_when_report_with_snapshot_then_returns_dict() -> None:
    """
    Given report --snapshot=/x/y.json,
    When flag,
    Then subcommand='report', snapshot='/x/y.json'.
    """
    with mock.patch.object(
        sys,
        'argv',
        _argv('report', '--snapshot=/x/y.json'),
    ):
        result = flag({'snapshot': '/x/y.json'})

    assert result['subcommand'] == 'report'
    assert result['snapshot'] == '/x/y.json'


def test_flag_when_report_without_snapshot_then_raises() -> None:
    """
    Given report sin --snapshot,
    When flag,
    Then raises ValueError con 'report requires --snapshot'.
    """
    with (
        mock.patch.object(sys, 'argv', _argv('report')),
        pytest.raises(
            ValueError,
            match=r'report requires --snapshot',
        ),
    ):
        flag({})


def test_flag_when_unknown_subcommand_then_raises() -> None:
    """
    Given subcomando 'foo' (no en VALID_SUBCOMMANDS),
    When flag,
    Then raises ValueError con 'Subcomando desconocido'.
    """
    with (
        mock.patch.object(sys, 'argv', _argv('foo')),
        pytest.raises(
            ValueError,
            match='Subcomando desconocido',
        ),
    ):
        flag({})


def test_flag_when_targets_valid_then_parses_to_dicts() -> None:
    """
    Given --targets=hub:/projects,fintech:/about,
    When flag,
    Then targets=[{niche, path}, {niche, path}] parseado.
    """
    with mock.patch.object(sys, 'argv', _argv()):
        result = flag({'targets': 'hub:/projects,fintech:/about'})

    assert result['targets'] == [
        {'niche': 'hub', 'path': '/projects'},
        {'niche': 'fintech', 'path': '/about'},
    ]


def test_flag_when_targets_unknown_niche_then_raises() -> None:
    """
    Given --targets=unknown:/x,
    When flag,
    Then raises ValueError con 'niche \\'unknown\\' desconocido'.
    """
    with (
        mock.patch.object(sys, 'argv', _argv()),
        pytest.raises(
            ValueError,
            match=r"niche 'unknown' desconocido",
        ),
    ):
        flag({'targets': 'unknown:/x'})
