"""
TypedDicts compartidos entre Lambdas.

Tipos:
- LambdaEvent: shape generico del event de API Gateway REST proxy
- LambdaContext: shape del context de runtime Lambda
- JsonResponse: shape de respuesta esperada por API Gateway REST proxy
"""

from typing import Any, NotRequired, TypedDict


class RequestContextIdentity(TypedDict, total=False):
    """Identity del context API GW (subset relevante)."""

    sourceIp: str
    userAgent: NotRequired[str]


class RequestContext(TypedDict, total=False):
    """RequestContext de API GW REST proxy (subset)."""

    identity: RequestContextIdentity
    requestId: str
    stage: str


class LambdaEvent(TypedDict, total=False):
    """Event de API Gateway REST proxy integration."""

    httpMethod: str
    path: str
    headers: dict[str, str]
    queryStringParameters: dict[str, str] | None
    pathParameters: dict[str, str] | None
    body: str | None
    isBase64Encoded: bool
    requestContext: RequestContext


class JsonResponse(TypedDict, total=False):
    """Shape de respuesta para API GW REST proxy."""

    statusCode: int
    headers: dict[str, str]
    body: str
    isBase64Encoded: NotRequired[bool]


class ErrorPayload(TypedDict):
    """Body de respuestas de error: shape JSON consistente."""

    error: str
    code: str
    extra: NotRequired[dict[str, Any]]
