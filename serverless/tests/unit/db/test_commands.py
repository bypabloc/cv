"""Unit tests de los comandos de la Lambda db (migrate/current/etc.)."""

from __future__ import annotations

from typing import Any

import pytest

from db.commands import COMMANDS
from db.commands import current as current_cmd
from db.commands import downgrade as downgrade_cmd
from db.commands import migrate as migrate_cmd
from db.commands import show_migrations as show_cmd
from db.commands import stamp as stamp_cmd

pytestmark = pytest.mark.unit


class TestRegistry:
    """COMMANDS - registry factory de comandos."""

    def test_when_inspected_then_has_the_five_commands(self) -> None:
        """
        Given el registry COMMANDS,
        When se inspecciona,
        Then expone exactamente los 5 comandos de gestion de schema.
        """
        assert sorted(COMMANDS) == [
            'current',
            'downgrade',
            'migrate',
            'show-migrations',
            'stamp',
        ]


class TestCurrent:
    """current - revision de Alembic aplicada en la DB."""

    def test_when_db_has_revision_then_returns_it(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given una DB con una revision aplicada,
        When current.run,
        Then devuelve status ok y la revision capturada.
        """
        monkeypatch.setattr(
            current_cmd, 'capture', lambda _fn: 'abc123 (head)'
        )

        result = current_cmd.run({})

        assert result == {
            'command': 'current',
            'status': 'ok',
            'current': 'abc123 (head)',
        }

    def test_when_db_unmigrated_then_current_is_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given una DB sin migraciones aplicadas (capture devuelve vacio),
        When current.run,
        Then 'current' es None.
        """
        monkeypatch.setattr(current_cmd, 'capture', lambda _fn: '')

        result = current_cmd.run({})

        assert result['current'] is None


class TestShowMigrations:
    """show-migrations - historial + revision actual."""

    def test_when_run_then_returns_history_lines_and_current(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un historial de migraciones,
        When show_migrations.run,
        Then devuelve el historial como lista de lineas y la revision actual.
        """
        outputs = iter(['rev1 -> rev2\nrev0 -> rev1', 'rev2 (head)'])
        monkeypatch.setattr(show_cmd, 'capture', lambda _fn: next(outputs))

        result = show_cmd.run({})

        assert result['command'] == 'show-migrations'
        assert result['status'] == 'ok'
        assert result['history'] == ['rev1 -> rev2', 'rev0 -> rev1']
        assert result['current'] == 'rev2 (head)'


class TestMigrate:
    """migrate - aplica las migraciones pendientes."""

    def test_when_run_then_calls_upgrade_with_target(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un payload con target,
        When migrate.run,
        Then invoca alembic upgrade con ese target y reporta la revision.
        """
        calls: list[Any] = []
        monkeypatch.setattr(migrate_cmd, 'build_config', lambda: 'CFG')
        monkeypatch.setattr(
            'alembic.command.upgrade',
            lambda cfg, target: calls.append((cfg, target)),
        )
        monkeypatch.setattr(
            'db.commands.current.run',
            lambda _args: {'current': 'rev9 (head)'},
        )

        result = migrate_cmd.run({'target': 'rev9'})

        assert calls == [('CFG', 'rev9')]
        assert result == {
            'command': 'migrate',
            'status': 'ok',
            'target': 'rev9',
            'current': 'rev9 (head)',
        }

    def test_when_no_target_then_defaults_to_head(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un payload sin target,
        When migrate.run,
        Then usa 'head' como target.
        """
        calls: list[Any] = []
        monkeypatch.setattr(migrate_cmd, 'build_config', lambda: 'CFG')
        monkeypatch.setattr(
            'alembic.command.upgrade',
            lambda cfg, target: calls.append(target),
        )
        monkeypatch.setattr(
            'db.commands.current.run', lambda _args: {'current': 'h'}
        )

        result = migrate_cmd.run({})

        assert calls == ['head']
        assert result['target'] == 'head'


class TestStamp:
    """stamp - marca una revision sin ejecutar el SQL."""

    def test_when_run_then_calls_stamp_with_target(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un payload con target,
        When stamp.run,
        Then invoca alembic stamp con ese target (adopcion en una DB con
        schema preexistente).
        """
        calls: list[Any] = []
        monkeypatch.setattr(stamp_cmd, 'build_config', lambda: 'CFG')
        monkeypatch.setattr(
            'alembic.command.stamp',
            lambda cfg, target: calls.append((cfg, target)),
        )
        monkeypatch.setattr(
            'db.commands.current.run', lambda _args: {'current': 'h (head)'}
        )

        result = stamp_cmd.run({'target': 'head'})

        assert calls == [('CFG', 'head')]
        assert result == {
            'command': 'stamp',
            'status': 'ok',
            'target': 'head',
            'current': 'h (head)',
        }


class TestDowngrade:
    """downgrade - revierte migraciones (operacion destructiva)."""

    def test_when_no_target_then_error(self) -> None:
        """
        Given un payload sin target,
        When downgrade.run,
        Then devuelve error (target es obligatorio).
        """
        result = downgrade_cmd.run({'confirm': True})

        assert result['status'] == 'error'
        assert "Falta 'target'" in result['error']

    def test_when_no_confirm_then_rejected(self) -> None:
        """
        Given un payload con target pero sin confirm: true,
        When downgrade.run,
        Then se rechaza sin ejecutar nada (salvaguarda anti-accidente).
        """
        result = downgrade_cmd.run({'target': '-1'})

        assert result['status'] == 'rejected'
        assert "'confirm': true" in result['error']

    def test_when_confirmed_then_calls_downgrade(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un payload con target y confirm: true,
        When downgrade.run,
        Then invoca alembic downgrade con ese target.
        """
        calls: list[Any] = []
        monkeypatch.setattr(downgrade_cmd, 'build_config', lambda: 'CFG')
        monkeypatch.setattr(
            'alembic.command.downgrade',
            lambda cfg, target: calls.append((cfg, target)),
        )
        monkeypatch.setattr(
            'db.commands.current.run', lambda _args: {'current': None}
        )

        result = downgrade_cmd.run({'target': 'base', 'confirm': True})

        assert calls == [('CFG', 'base')]
        assert result == {
            'command': 'downgrade',
            'status': 'ok',
            'target': 'base',
            'current': None,
        }
