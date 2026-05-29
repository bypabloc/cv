"""
Given un TableMeta y una tabla real,
When se llama .check_schema(),
Then el SchemaDiff reporta exactamente las diferencias (AC-11).
"""

from __future__ import annotations

import boto3
import pytest
from shared.dynamodb.models import ContactItem, TrackingEventItem


@pytest.mark.usefixtures('dynamodb_tables')
def test_check_schema_in_sync_when_meta_matches_table() -> None:
    """check_schema() reporta in_sync cuando la tabla coincide con Meta."""
    # Act
    diff = TrackingEventItem.check_schema()

    # Assert
    assert diff.exists is True
    assert diff.keys_match is True
    assert diff.ttl_match is True
    assert diff.gsi_missing == []
    assert diff.gsi_unexpected == []
    assert diff.in_sync is True


@pytest.mark.usefixtures('mock_aws_no_tables')
def test_check_schema_reports_table_absent() -> None:
    """check_schema() reporta exists=False si la tabla no existe."""
    # Act
    diff = ContactItem.check_schema()

    # Assert
    assert diff.exists is False
    assert diff.in_sync is False


@pytest.mark.usefixtures('mock_aws_no_tables')
def test_check_schema_detects_key_and_ttl_drift() -> None:
    """check_schema() detecta KeySchema y TTL divergentes."""
    # Arrange: crear la tabla contacts con un KeySchema distinto al Meta
    # (PK 'wrong_key' en vez de 'id') y sin TTL.
    client = boto3.client('dynamodb', region_name='us-east-1')
    client.create_table(
        TableName='portfolio-contacts-test',
        AttributeDefinitions=[
            {'AttributeName': 'wrong_key', 'AttributeType': 'S'},
        ],
        KeySchema=[{'AttributeName': 'wrong_key', 'KeyType': 'HASH'}],
        BillingMode='PAY_PER_REQUEST',
    )

    # Act
    diff = ContactItem.check_schema()

    # Assert
    assert diff.exists is True
    assert diff.keys_match is False
    # ContactItem.Meta no declara ttl_attr y la tabla tampoco lo tiene:
    # eso SI coincide.
    assert diff.ttl_match is True
    assert diff.in_sync is False
    assert any('KeySchema' in note for note in diff.notes)


@pytest.mark.usefixtures('mock_aws_no_tables')
def test_check_schema_detects_missing_gsi() -> None:
    """check_schema() detecta un GSI declarado pero ausente en la tabla."""
    # Arrange: crear tracking SIN el GSI niche-created_at-index.
    client = boto3.client('dynamodb', region_name='us-east-1')
    client.create_table(
        TableName='portfolio-tracking-test',
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
        TableName='portfolio-tracking-test',
        TimeToLiveSpecification={
            'Enabled': True,
            'AttributeName': 'expires_at',
        },
    )

    # Act
    diff = TrackingEventItem.check_schema()

    # Assert
    assert diff.keys_match is True
    assert diff.ttl_match is True
    assert diff.gsi_missing == ['niche-created_at-index']
    assert diff.in_sync is False
