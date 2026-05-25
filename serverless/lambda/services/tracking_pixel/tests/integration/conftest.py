"""Configuracion pytest de los tests de integracion del `tracking_pixel`.

A diferencia de los tests unitarios (que mockean E/S puntual con
`unittest.mock`), los tests de integracion ejercitan el flujo COMPLETO
end-to-end: invocan el `lambda_handler` real con un evento API Gateway
crudo y verifican el efecto observable (respuesta HTTP + estado en
DynamoDB), recorriendo handler -> controller -> service -> persistencia.

Fidelidad vs AWS real: la suite usa `moto` (`mock_aws`) para emular las
4 tablas DynamoDB que el Lambda toca (tracking, cache, rate-limit-rules,
rate-limit-buckets). moto reproduce con alta fidelidad la semantica de
DynamoDB (PK/SK, `UpdateItem` atomico, TTL como atributo, condiciones),
asi que el flujo se ejercita igual que contra AWS — pero sin red, sin
credenciales y sin costo, lo que hace la suite ejecutable en CI.

Las fixtures de este conftest:
  - `aws_credentials` (autouse): credenciales AWS fake (heredado del
    conftest unit) para que moto intercepte boto3.
  - `tracking_env` (autouse): monta moto, crea las 4 tablas, siembra la
    regla de rate-limit del endpoint `/track` (30 req/min) y resetea los
    singletons boto3 entre tests para que no quede estado cruzado.

`_fixtures/` aloja builders compartidos (prefijo `_` para que pytest no
los recolecte como tests).
"""

from __future__ import annotations

from collections.abc import Generator

import pytest

# El conftest raiz del Lambda (tests/conftest.py) ya agrega `core/` al
# sys.path, setea las env vars minimas y define la fixture autouse
# `aws_credentials`. Este conftest solo agrega la fixture de moto E2E.


@pytest.fixture(autouse=True)
def tracking_env() -> Generator[None]:
    """Monta moto, crea las 4 tablas y siembra la regla de `/track`.

    Es `autouse`: cada test de integracion corre con el entorno AWS
    emulado ya preparado, sin declarar la fixture explicitamente.

    Pasos:
      1. Abre `mock_aws()` (intercepta todo boto3).
      2. Resetea el resource singleton de DynamoDB y el cache singleton
         para que no apunten a un mock de un test anterior.
      3. Crea `tracking`, `cache`, `rate-limit-rules`, `rate-limit-buckets`.
      4. Siembra la regla de endpoint `/track` con `limit=30`,
         `window_seconds=60` (lo que el Lambda usa en produccion). Sin
         esta regla el rate-limit caeria al default global (10/min).

    El `mock_aws()` se cierra al terminar el test: las tablas y su
    contenido se descartan, garantizando aislamiento entre tests.
    """
    import boto3
    from moto import mock_aws
    from shared.aws.dynamodb import reset_resource_cache

    with mock_aws():
        reset_resource_cache()
        ddb = boto3.client('dynamodb', region_name='us-east-1')

        ddb.create_table(
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
        ddb.create_table(
            TableName='portfolio-cache-test',
            AttributeDefinitions=[
                {'AttributeName': 'cache_key', 'AttributeType': 'S'},
            ],
            KeySchema=[{'AttributeName': 'cache_key', 'KeyType': 'HASH'}],
            BillingMode='PAY_PER_REQUEST',
        )
        ddb.create_table(
            TableName='portfolio-rate-limit-rules-test',
            AttributeDefinitions=[
                {'AttributeName': 'rule_key', 'AttributeType': 'S'},
                {'AttributeName': 'kind', 'AttributeType': 'S'},
            ],
            KeySchema=[
                {'AttributeName': 'rule_key', 'KeyType': 'HASH'},
                {'AttributeName': 'kind', 'KeyType': 'RANGE'},
            ],
            BillingMode='PAY_PER_REQUEST',
        )
        ddb.create_table(
            TableName='portfolio-rate-limit-buckets-test',
            AttributeDefinitions=[
                {'AttributeName': 'bucket_key', 'AttributeType': 'S'},
            ],
            KeySchema=[
                {'AttributeName': 'bucket_key', 'KeyType': 'HASH'},
            ],
            BillingMode='PAY_PER_REQUEST',
        )

        # Regla del endpoint /track: 30 requests por ventana de 60s.
        # El Lambda invoca check_or_raise(endpoint='/track'), que la lee
        # de esta tabla. Sin la regla, check.py cae al DEFAULT_LIMIT (10).
        boto3.resource('dynamodb', region_name='us-east-1').Table(
            'portfolio-rate-limit-rules-test'
        ).put_item(
            Item={
                'rule_key': 'endpoint#/track',
                'kind': 'endpoint',
                'limit': 30,
                'window_seconds': 60,
                'action': 'throttle',
                'reason': 'tracking pixel endpoint limit',
            }
        )

        yield
