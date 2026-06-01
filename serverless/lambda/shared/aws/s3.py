"""@module shared.aws.s3 — cliente S3 compartido (lectura de objetos).

Portador del cliente boto3 S3. El `core/` de los services NUNCA importa
`boto3` directo: usa `from shared.aws.s3 import get_object_text`.

El cliente se crea LAZY (PEP 562) y se cachea a nivel de modulo: el primer
acceso lo materializa, las invocaciones warm de la Lambda lo reusan. NO se
crea al importar (un Lambda que importa shared.aws por otra razon no paga
la creacion del cliente S3 en su cold start). Lo usa `send_email` para bajar
los templates de email del bucket portfolio-email-templates-${stage}.
"""

from __future__ import annotations

from typing import Any

from shared.core.config import settings

_client_cache: dict[str, Any] = {}


def get_client() -> Any:
    """Devuelve el cliente S3 (lazy singleton)."""
    if 'c' not in _client_cache:
        import boto3

        _client_cache['c'] = boto3.client('s3', region_name=settings.aws_region)
    return _client_cache['c']


def get_object_text(bucket: str, key: str, *, encoding: str = 'utf-8') -> str:
    """Descarga un objeto S3 y lo devuelve decodificado como texto.

    Args:
        bucket: nombre del bucket.
        key: clave del objeto (path dentro del bucket).
        encoding: encoding para decodificar los bytes (default utf-8).

    Returns:
        El contenido del objeto como str.
    """
    response = get_client().get_object(Bucket=bucket, Key=key)
    return response['Body'].read().decode(encoding)


def reset_client_cache() -> None:
    """Resetea el cache del cliente (para tests con moto)."""
    _client_cache.clear()
