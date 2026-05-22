"""Conversion de tipos entre DynamoDB y Python.

DynamoDB (via boto3 Resource) representa TODO numero como `Decimal`. El
codigo de dominio espera `int`/`float`. Y al escribir, DynamoDB rechaza
`float` nativo y los empty strings. Este modulo centraliza esa
conversion, antes triplicada en `cache/client`, `rate_limit/rules` y
`stream_service`.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any


def from_dynamodb(value: Any) -> Any:
    """Convierte un valor leido de DynamoDB a su tipo Python natural.

    `Decimal` entero -> `int`; `Decimal` con fraccion -> `float`. Aplica
    recursivamente sobre dicts y lists (atributos Map / List de DynamoDB).

    Parameters
    ----------
    value : Any
        Valor crudo devuelto por boto3 (puede anidar `Decimal`).

    Returns
    -------
    Any
        Mismo valor con los `Decimal` bajados a `int`/`float`.
    """
    if isinstance(value, Decimal):
        return (
            int(value)
            if value == value.to_integral_value()
            else float(value)
        )
    if isinstance(value, dict):
        return {k: from_dynamodb(v) for k, v in value.items()}
    if isinstance(value, list):
        return [from_dynamodb(v) for v in value]
    return value


def to_dynamodb(value: Any) -> Any:
    """Convierte un valor Python a uno que DynamoDB (Resource API) acepta.

    `float` -> `Decimal` (DynamoDB rechaza `float` nativo). Aplica
    recursivamente. `int`, `str`, `bool`, `None` pasan sin cambio: boto3
    los serializa directo.

    Parameters
    ----------
    value : Any
        Valor Python a escribir.

    Returns
    -------
    Any
        Valor apto para `put_item`/`update_item`.
    """
    if isinstance(value, bool):
        # bool es subclase de int: tratarlo antes para no convertirlo.
        return value
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: to_dynamodb(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_dynamodb(v) for v in value]
    return value


def is_empty(value: Any) -> bool:
    """`True` si el valor no debe persistirse como atributo DynamoDB.

    DynamoDB no acepta strings vacios. Un campo `None` o `''` se omite del
    Item (paridad con los for-loop de campos opcionales del codigo viejo).
    El `0`, el `False` y las colecciones vacias SI se persisten: son
    valores significativos.

    Parameters
    ----------
    value : Any
        Valor candidato a atributo.

    Returns
    -------
    bool
        `True` si debe omitirse.
    """
    return value is None or value == ''
