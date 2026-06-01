"""shared.aws.s3.get_object_text descarga y decodifica un objeto S3.

Given un objeto en un bucket S3 (moto),
When se llama get_object_text(bucket, key),
Then devuelve el contenido como texto decodificado.
"""

from __future__ import annotations

import pytest
from moto import mock_aws

from shared.aws.s3 import get_object_text, reset_client_cache

pytestmark = pytest.mark.unit


@mock_aws
def test_get_object_text_returns_decoded_body():
    import boto3

    # Arrange: bucket + objeto con texto
    reset_client_cache()
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='portfolio-email-templates-dev')
    s3.put_object(
        Bucket='portfolio-email-templates-dev',
        Key='contact.html',
        Body='<p>Hola {{ name }}</p>'.encode('utf-8'),
    )

    # Act
    result = get_object_text(
        'portfolio-email-templates-dev', 'contact.html'
    )

    # Assert
    assert result == '<p>Hola {{ name }}</p>'


@mock_aws
def test_get_object_text_missing_key_raises():
    import boto3

    reset_client_cache()
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='portfolio-email-templates-dev')

    with pytest.raises(Exception):  # noqa: B017 -- boto ClientError NoSuchKey
        get_object_text('portfolio-email-templates-dev', 'missing.html')
