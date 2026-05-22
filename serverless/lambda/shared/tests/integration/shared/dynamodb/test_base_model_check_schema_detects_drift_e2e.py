"""
Given la tabla tracking creada a mano SIN el GSI que declara su TableMeta,
When check_schema compara el TableMeta contra esa tabla real,
Then el SchemaDiff reporta el GSI faltante y no esta in_sync.
"""

from __future__ import annotations

import boto3
import pytest
from shared.dynamodb import TrackingEventItem

pytestmark = pytest.mark.integration


def test_base_model_check_schema_detects_drift_e2e(
    mock_aws_no_tables: None,
) -> None:
    """check_schema detecta el GSI declarado y ausente en la tabla real."""
    # Arrange: crear tracking sin el GSI niche-created_at-index.
    client = boto3.client('dynamodb', region_name='us-east-1')
    client.create_table(
        TableName='portfolio-tracking-it',
        AttributeDefinitions=[
            {'AttributeName': 'session_id', 'AttributeType': 'S'},
            {'AttributeName': 'page_id', 'AttributeType': 'S'},
        ],
        KeySchema=[
            {'AttributeName': 'session_id', 'KeyType': 'HASH'},
            {'AttributeName': 'page_id', 'KeyType': 'RANGE'},
        ],
        BillingMode='PAY_PER_REQUEST',
    )
    client.update_time_to_live(
        TableName='portfolio-tracking-it',
        TimeToLiveSpecification={
            'Enabled': True,
            'AttributeName': 'expires_at',
        },
    )

    # Act
    diff = TrackingEventItem.check_schema()

    # Assert
    assert diff.gsi_missing == ['niche-created_at-index']
    assert diff.in_sync is False
