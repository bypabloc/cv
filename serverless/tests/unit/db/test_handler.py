"""Unit tests del handler de la Lambda db (factory de comandos)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from db import handler as handler_mod
from db.handler import lambda_handler

pytestmark = pytest.mark.unit


@dataclass
class MockLambdaContext:
    """Context minimo para inject_lambda_context de Powertools."""

    function_name: str = 'portfolio-db-test'
    memory_limit_in_mb: int = 512
    invoked_function_arn: str = (
        'arn:aws:lambda:us-east-1:000000000000:function:db'
    )
    aws_request_id: str = 'test-req-id'

    def get_remaining_time_in_millis(self) -> int:
        return 120000


def _ctx() -> Any:
    return MockLambdaContext()


@pytest.fixture(autouse=True)
def _no_ssm(monkeypatch: pytest.MonkeyPatch) -> None:
    """ensure_database_url es no-op en tests (no resuelve SSM)."""
    monkeypatch.setattr(handler_mod, 'ensure_database_url', lambda: None)


class TestHandlerDispatch:
    """lambda_handler - resuelve el command del payload via COMMANDS."""

    def test_when_known_command_then_invokes_and_returns_result(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un payload con un command registrado,
        When lambda_handler lo procesa,
        Then invoca la funcion del registry con args y devuelve su resultado.
        """
        received: dict[str, Any] = {}

        def _fake_run(args: dict) -> dict:
            received['args'] = args
            return {'command': 'migrate', 'status': 'ok'}

        monkeypatch.setitem(handler_mod.COMMANDS, 'migrate', _fake_run)

        result = lambda_handler(
            {'command': 'migrate', 'args': {'target': 'head'}}, _ctx()
        )

        assert result == {'command': 'migrate', 'status': 'ok'}
        assert received['args'] == {'target': 'head'}

    def test_when_no_args_then_command_receives_empty_dict(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un payload sin la clave 'args',
        When lambda_handler lo procesa,
        Then el command recibe un dict vacio.
        """
        received: dict[str, Any] = {}

        def _fake_run(args: dict) -> dict:
            received['args'] = args
            return {'status': 'ok'}

        monkeypatch.setitem(handler_mod.COMMANDS, 'current', _fake_run)

        lambda_handler({'command': 'current'}, _ctx())

        assert received['args'] == {}


class TestHandlerErrors:
    """lambda_handler - payloads invalidos y fallos de command."""

    def test_when_no_command_then_error_with_available(self) -> None:
        """
        Given un payload sin 'command',
        When lambda_handler lo procesa,
        Then devuelve error con la lista de comandos disponibles.
        """
        result = lambda_handler({}, _ctx())

        assert result['status'] == 'error'
        assert "Falta 'command'" in result['error']
        assert result['available'] == sorted(handler_mod.COMMANDS)

    def test_when_unknown_command_then_error_with_available(self) -> None:
        """
        Given un payload con un command no registrado,
        When lambda_handler lo procesa,
        Then devuelve error nombrando el command y los disponibles.
        """
        result = lambda_handler({'command': 'nope'}, _ctx())

        assert result['status'] == 'error'
        assert "command desconocido: 'nope'" in result['error']
        assert result['available'] == sorted(handler_mod.COMMANDS)

    def test_when_args_not_dict_then_error(self) -> None:
        """
        Given un payload cuyo 'args' no es un objeto,
        When lambda_handler lo procesa,
        Then devuelve error indicandolo.
        """
        result = lambda_handler(
            {'command': 'migrate', 'args': ['not', 'a', 'dict']}, _ctx()
        )

        assert result['status'] == 'error'
        assert "'args' debe ser un objeto" in result['error']

    def test_when_command_raises_then_error_response(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Given un command cuya ejecucion lanza una excepcion,
        When lambda_handler lo procesa,
        Then devuelve un error generico (sin filtrar el traceback al caller).
        """
        def _boom(_args: dict) -> dict:
            raise RuntimeError('fallo interno de alembic')

        monkeypatch.setitem(handler_mod.COMMANDS, 'migrate', _boom)

        result = lambda_handler({'command': 'migrate'}, _ctx())

        assert result['status'] == 'error'
        assert result['command'] == 'migrate'
        assert 'CloudWatch' in result['error']
