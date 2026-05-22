"""E2E — forma exacta del contrato `batchItemFailures` de salida.

Given un batch con un record valido entre dos invalidos (fallan al
  parsear),
When `lambda_handler` procesa el batch end-to-end,
Then la respuesta tiene EXACTAMENTE la forma del contrato
  `ReportBatchItemFailures` de AWS: una sola clave `batchItemFailures`,
  cuyo valor es una lista de dicts `{'itemIdentifier': <eventID>}`, uno
  por record fallido y solo por los fallidos.
"""

from __future__ import annotations

import pytest
from sqlalchemy import Engine

from tests.integration._fixtures.events import (
    contact_record,
    invalid_contact_record,
    stream_event,
)
from tests.integration._fixtures.runner import invoke_handler

pytestmark = pytest.mark.integration


def test_batch_item_failures_contract_shape_e2e(
    sqlite_db: Engine,
) -> None:
    # Arrange
    event = stream_event(
        invalid_contact_record('bad-a'),
        contact_record('good-b'),
        invalid_contact_record('bad-c'),
    )

    # Act
    result = invoke_handler(event, sqlite_db)

    # Assert — el contrato exacto de AWS ReportBatchItemFailures.
    assert list(result.keys()) == ['batchItemFailures']
    failures = result['batchItemFailures']
    assert failures == [
        {'itemIdentifier': 'bad-a'},
        {'itemIdentifier': 'bad-c'},
    ]
    for item in failures:
        assert list(item.keys()) == ['itemIdentifier']
