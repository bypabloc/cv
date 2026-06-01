"""@module shared.aws.dynamodb_types — re-export de boto3.dynamodb.types.

Aisla a los `core/` de los services del import directo a boto3.
`TypeDeserializer`/`TypeSerializer` parsean el formato low-level de
DynamoDB (NewImage/OldImage de Streams, items crudos); si hace falta
algun helper de conversion Decimal -> str, vive aqui.

NO se exporta el cliente `boto3` ni el resource — esos los aporta
`shared.aws.dynamodb` con un wrapper especifico (`get_table`, ...).
"""

from __future__ import annotations

from boto3.dynamodb.types import TypeDeserializer, TypeSerializer

__all__ = ['TypeDeserializer', 'TypeSerializer']
