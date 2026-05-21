"""Mapeo de operaciones del Lambda `stream_processor`.

El Lambda `stream_processor` no esta detras de API Gateway: lo dispara
el Event Source Mapping de los DynamoDB Streams. El handler sintetiza
un unico evento `{operation: 'stream', action: 'process', data: ...}`
a partir del batch de Records del Stream.

Cada codename mapea a:
  - controller : carpeta dentro de controllers/
  - arn_key    : campo de AppConfig con el ARN de un Lambda downstream
                 (vacio: stream_processor no invoca otros Lambdas).
"""

OPERATIONS = {
    'stream': {
        'controller': 'stream',
        'arn_key': '',
    },
}
