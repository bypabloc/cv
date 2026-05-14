# Validacion del token en backend (Python 3.13 + httpx)

> Como validar el token Turnstile en Lambda/servidor, verificar respuesta,
> y manejar errores. Codigo completo listo para copiar-pegar.

[← Frontend](./03-frontend-integration.md) | [Siguiente: Error codes →](./05-error-codes.md)

## Endpoint siteverify

```
POST https://challenges.cloudflare.com/turnstile/v0/siteverify
```

Request:

```json
{
  "secret": "tu_secret_key_aqui",
  "response": "token_del_cliente",
  "remoteip": "192.0.2.1"
}
```

Response (exito):

```json
{
  "success": true,
  "challenge_ts": "2026-05-13T14:30:45.123Z",
  "hostname": "the-full-stack.com",
  "action": "contactForm",
  "cdata": null,
  "error_codes": []
}
```

Response (error):

```json
{
  "success": false,
  "challenge_ts": null,
  "hostname": null,
  "error_codes": ["timeout-or-duplicate"]
}
```

## Implementacion Python con httpx

```python
"""
Validar token Turnstile en un endpoint Lambda.

Variables de entorno requeridas:
  TURNSTILE_SECRET_KEY — secret key del widget Turnstile
  EXPECTED_HOSTNAME — hostname esperado (ej. the-full-stack.com)
"""

import os
import json
import logging
from typing import TypedDict
from datetime import datetime, timezone

import httpx


logger = logging.getLogger(__name__)


class TurnstileResponse(TypedDict):
    """Estructura de respuesta siteverify."""

    success: bool
    challenge_ts: str | None
    hostname: str | None
    action: str | None
    cdata: str | None
    error_codes: list[str]


class TurnstileValidationError(Exception):
    """Excepcion base para errores de validacion Turnstile."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


def validate_turnstile_token(
    token: str,
    remote_ip: str | None = None,
    expected_hostname: str | None = None,
    timeout_seconds: int = 10,
) -> TurnstileResponse:
    """
    Validar token Turnstile llamando siteverify.

    Args:
        token: Token del cliente (max 2048 chars)
        remote_ip: IP del cliente (opcional pero recomendado)
        expected_hostname: Hostname esperado (ej. the-full-stack.com)
        timeout_seconds: Timeout para la request HTTP

    Returns:
        TurnstileResponse con resultado

    Raises:
        TurnstileValidationError si validacion falla
        httpx.RequestError si hay problema de red
    """
    secret_key = os.getenv("TURNSTILE_SECRET_KEY")
    if not secret_key:
        raise TurnstileValidationError(
            "TURNSTILE_SECRET_KEY not configured",
            error_code="missing_env",
        )

    if not expected_hostname:
        expected_hostname = os.getenv("EXPECTED_HOSTNAME")

    if not token or len(token) > 2048:
        raise TurnstileValidationError(
            f"Invalid token: {token[:20]}...",
            error_code="invalid_input_response",
        )

    # Preparar request body
    payload = {
        "secret": secret_key,
        "response": token,
    }
    if remote_ip:
        payload["remoteip"] = remote_ip

    # POST a siteverify
    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                json=payload,
            )
        response.raise_for_status()
    except httpx.RequestError as e:
        logger.error(f"Network error validating Turnstile: {e}")
        raise TurnstileValidationError(
            f"Network error: {e}",
            error_code="internal_error",
        ) from e

    # Parsear respuesta
    try:
        result: TurnstileResponse = response.json()  # type: ignore
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON from siteverify: {response.text}")
        raise TurnstileValidationError(
            "Invalid response from siteverify",
            error_code="internal_error",
        ) from e

    # Log completo para debugging
    logger.info(
        f"Turnstile validation result: success={result['success']}, "
        f"hostname={result['hostname']}, "
        f"error_codes={result.get('error_codes', [])}"
    )

    # Verificaciones criticas
    if not result["success"]:
        error_codes = result.get("error_codes", [])
        logger.warning(
            f"Turnstile validation failed: {error_codes}"
        )
        raise TurnstileValidationError(
            f"Turnstile failed: {error_codes}",
            error_code=error_codes[0] if error_codes else "unknown_error",
            details={"error_codes": error_codes},
        )

    # Verificar hostname
    if expected_hostname and result["hostname"] != expected_hostname:
        logger.error(
            f"Hostname mismatch: expected={expected_hostname}, "
            f"got={result['hostname']}"
        )
        raise TurnstileValidationError(
            f"Hostname mismatch: {result['hostname']}",
            error_code="invalid_hostname",
        )

    # Verificar timestamp (debe ser reciente: < 5 minutos)
    if result["challenge_ts"]:
        try:
            challenge_ts = datetime.fromisoformat(
                result["challenge_ts"].replace("Z", "+00:00")
            )
            now = datetime.now(timezone.utc)
            age_seconds = (now - challenge_ts).total_seconds()

            if age_seconds > 300:  # 5 minutos
                logger.warning(
                    f"Token too old: {age_seconds}s > 300s"
                )
                raise TurnstileValidationError(
                    f"Token expired: {age_seconds}s old",
                    error_code="timeout_or_duplicate",
                )
        except ValueError as e:
            logger.error(f"Invalid challenge_ts format: {e}")
            raise TurnstileValidationError(
                "Invalid challenge_ts format",
                error_code="internal_error",
            ) from e

    logger.info(
        f"Turnstile validation SUCCESS for hostname={result['hostname']}"
    )
    return result


# ============================================================================
# Ejemplo: Lambda handler para /api/contact
# ============================================================================

def lambda_handler(event: dict, context) -> dict:
    """
    POST /api/contact handler.
    
    Espera body JSON:
      {
        "name": "...",
        "email": "...",
        "message": "...",
        "cf-token": "..."
      }
    """
    try:
        # Parsear body
        body = json.loads(event.get("body", "{}"))
        token = body.get("cf-token", "").strip()
        name = body.get("name", "").strip()
        email = body.get("email", "").strip()
        message = body.get("message", "").strip()

        # Validaciones basicas
        if not all([name, email, message, token]):
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"error": "Missing required fields"}
                ),
            }

        # Validar Turnstile
        remote_ip = event.get("requestContext", {}).get(
            "identity", {}
        ).get("sourceIp")

        try:
            turnstile_result = validate_turnstile_token(
                token=token,
                remote_ip=remote_ip,
                expected_hostname="the-full-stack.com",
            )
        except TurnstileValidationError as e:
            logger.warning(f"Turnstile validation failed: {e}")
            return {
                "statusCode": 403,
                "body": json.dumps(
                    {
                        "error": "Captcha validation failed",
                        "code": e.error_code,
                    }
                ),
            }

        # Aqui: procesar el contacto (guardar a DB, enviar email, etc.)
        logger.info(
            f"Contact form received from {email}: {name}"
        )

        # Placeholder: enviar email
        # send_email(to=email, subject="...", body=message)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {"message": "Contact received successfully"}
            ),
        }

    except Exception as e:
        logger.error(f"Unexpected error in /api/contact: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"error": "Internal server error"}
            ),
        }
```

## Checklist antes de deploy

- [ ] Variable `TURNSTILE_SECRET_KEY` configurada en Lambda env
- [ ] Variable `EXPECTED_HOSTNAME` configurada (the-full-stack.com)
- [ ] httpx instalado (`pip install httpx`)
- [ ] Timeout HTTP minimo 10 segundos (siteverify puede ser lento)
- [ ] Logging estructurado habilitado
- [ ] Tests unitarios con mock de siteverify
- [ ] Error handling para network errors, timeouts, invalid JSON
