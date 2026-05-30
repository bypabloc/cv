"""Unit tests para shared.aws.warm_aws_clients.

Warmup de clientes boto3 en la fase INIT del Lambda: fuerza la
construccion del resource DynamoDB y/o el cliente SQS antes del EXECUTE
para que el cold a baja memoria (128 MB ~ 0.07 vCPU) no pague el costo
CPU de boto3 dentro del handler. Best-effort: nunca propaga excepciones.
"""

from __future__ import annotations

import pytest
from shared.aws.warmup import warm_aws_clients

pytestmark = pytest.mark.unit


def test_when_dynamodb_true_then_calls_get_resource(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Given warm_aws_clients(dynamodb=True),
    When se invoca,
    Then llama get_resource del modulo shared.aws.dynamodb una vez.
    """
    calls = {'dynamodb': 0, 'sqs': 0, 'meta_client': 0}

    class _FakeMeta:
        @property
        def client(self) -> object:
            calls['meta_client'] += 1
            return object()

    class _FakeResource:
        meta = _FakeMeta()

    def _fake_get_resource() -> object:
        calls['dynamodb'] += 1
        return _FakeResource()

    def _fake_get_sqs_client() -> object:
        calls['sqs'] += 1
        return object()

    monkeypatch.setattr(
        'shared.aws.dynamodb.get_resource', _fake_get_resource
    )
    monkeypatch.setattr(
        'shared.queue.client.get_sqs_client', _fake_get_sqs_client
    )

    warm_aws_clients(dynamodb=True, sqs=False)

    # Warmea el resource Y materializa su .meta.client (el cliente
    # low-level que usa el ORM en EXECUTE).
    assert calls == {'dynamodb': 1, 'sqs': 0, 'meta_client': 1}


def test_when_sqs_true_then_calls_get_sqs_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Given warm_aws_clients(sqs=True),
    When se invoca,
    Then llama get_sqs_client del modulo shared.queue.client una vez.
    """
    calls = {'dynamodb': 0, 'sqs': 0}

    monkeypatch.setattr(
        'shared.aws.dynamodb.get_resource',
        lambda: calls.__setitem__('dynamodb', calls['dynamodb'] + 1),
    )
    monkeypatch.setattr(
        'shared.queue.client.get_sqs_client',
        lambda: calls.__setitem__('sqs', calls['sqs'] + 1),
    )

    warm_aws_clients(dynamodb=False, sqs=True)

    assert calls == {'dynamodb': 0, 'sqs': 1}


def test_when_both_false_then_no_client_is_built(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Given warm_aws_clients() sin flags,
    When se invoca,
    Then no construye ningun cliente (no-op).
    """
    calls = {'dynamodb': 0, 'sqs': 0}

    monkeypatch.setattr(
        'shared.aws.dynamodb.get_resource',
        lambda: calls.__setitem__('dynamodb', calls['dynamodb'] + 1),
    )
    monkeypatch.setattr(
        'shared.queue.client.get_sqs_client',
        lambda: calls.__setitem__('sqs', calls['sqs'] + 1),
    )

    warm_aws_clients()

    assert calls == {'dynamodb': 0, 'sqs': 0}


def test_when_get_resource_raises_then_warmup_is_silent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Given get_resource lanza una excepcion (sin red / sin credenciales),
    When warm_aws_clients(dynamodb=True),
    Then NO propaga: el INIT nunca se rompe por el warmup (best-effort).
    """
    def _boom() -> object:
        raise RuntimeError('no network')

    monkeypatch.setattr('shared.aws.dynamodb.get_resource', _boom)

    # No raise -> el test pasa si warm_aws_clients no propaga.
    result = warm_aws_clients(dynamodb=True)

    assert result is None
