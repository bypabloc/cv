"""@module shared.aws.dynamodb_types — re-export de boto3.dynamodb.types.

Aisla a los `core/` de los services del import directo a boto3. El
stream_processor consume `TypeDeserializer` para parsear el formato
NewImage/OldImage de DynamoDB Streams; si en el futuro hace falta
`TypeSerializer` o helpers de conversion Decimal -> str, viven aqui.

NO se exporta el cliente `boto3` ni el resource — esos los aporta
`shared.aws.dynamodb` con un wrapper especifico (`get_table`, ...).
"""

from __future__ import annotations

from boto3.dynamodb.types import TypeDeserializer, TypeSerializer

__all__ = ['TypeDeserializer', 'TypeSerializer']
