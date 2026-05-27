"""
Given un batch SQS con un record cuyo body NO es JSON valido,
When lambda_handler procesa,
Then ese record (y SOLO ese) aparece en batchItemFailures con su
     messageId original.

AC-13: failures llevan SIEMPRE el messageId original, nunca otro id.
"""

from __future__ import annotations

import pytest

from tests.unit._helpers import lambda_context, sqs_batch, sqs_record


@pytest.mark.unit
def test_handler_marks_individual_failures_with_id(
    db_session_calls: list[int],
    session_visit_calls: list[dict],
    insert_tracking_calls: list[dict],
    patch_parse_user_agent: None,
) -> None:
    # Arrange
    _ = (
        db_session_calls,
        session_visit_calls,
        insert_tracking_calls,
        patch_parse_user_agent,
    )
    from handler import lambda_handler

    bad = sqs_record(index=1, raw_body='{not json')
    good = sqs_record(index=2)
    event = sqs_batch([bad, good])

    # Act
    result = lambda_handler(event, lambda_context())

    # Assert: el bad va en failures con SU messageId; el good no aparece.
    assert result == {
        'batchItemFailures': [
            {'itemIdentifier': bad['messageId']},
        ],
    }
