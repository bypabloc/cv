# Error codes de Turnstile siteverify

> Significado de cada error code que devuelve el endpoint siteverify.
> Util para debugging y logging.

[← Backend Python](./04-backend-validation-python.md) | [Siguiente: Anti-replay →](./06-anti-replay-best-practices.md)

## Tabla completa de error codes

| Error code | Causa | HTTP respuesta | Accion cliente |
|-----------|-------|---------|-----------------|
| `missing-input-secret` | No enviaste secret en request | 400 Bad Request (bug backend) | Ninguna (es bug nuestro) |
| `invalid-input-secret` | Secret key es invalida o expirada | 401 Unauthorized | Verificar dashboard Cloudflare |
| `missing-input-response` | No enviaste response token | 400 Bad Request | Mostrar "resuelve captcha nuevamente" |
| `invalid-input-response` | Token es invalido o corrupto | 403 Forbidden | Regenerar token (`turnstile.reset()`) |
| `bad-request` | Request malformada (params en query?) | 400 Bad Request | Verificar formato POST (body JSON) |
| `timeout-or-duplicate` | Token expiro (>5 min) O ya fue validado | 403 Forbidden | Regenerar token |
| `internal-error` | Error interno de Cloudflare | 500 Internal Server | Reintentar en 30s |

## Mapeo a respuestas HTTP

### 400 Bad Request

- `missing-input-secret` — ERROR: secret no en request (bug nuestro)
- `missing-input-response` — usuario no completo captcha
- `bad-request` — request POST malformada

Accion: Si cliente ve 400, regenerar token y reintentar form.

### 401 Unauthorized

- `invalid-input-secret` — secret key roto (no valido)

Accion: Verificar que `TURNSTILE_SECRET_KEY` en Lambda es correcto.

### 403 Forbidden

- `invalid-input-response` — token corrupto
- `timeout-or-duplicate` — token expiro o ya usado

Accion: Regenerar token en cliente; no reintentar con mismo token.

### 500 Internal Server

- `internal-error` — problema en Cloudflare

Accion: Reintentar con exponential backoff (1s, 2s, 4s, max 10s).

## Debugging: como loguear errores

```python
from datetime import datetime

def log_turnstile_error(
    error_code: str,
    token: str,
    hostname: str,
    remote_ip: str | None = None,
    extra: dict | None = None,
) -> None:
    """Log estructurado de errores Turnstile."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "turnstile_validation_error",
        "error_code": error_code,
        "token_sample": token[:20] + "..." if token else None,
        "hostname": hostname,
        "remote_ip": remote_ip,
        "extra": extra or {},
    }
    logger.warning(json.dumps(log_entry))

# Uso en handler
try:
    validate_turnstile_token(token, remote_ip, expected_hostname)
except TurnstileValidationError as e:
    log_turnstile_error(
        error_code=e.error_code,
        token=token,
        hostname=expected_hostname,
        remote_ip=remote_ip,
        extra=e.details,
    )
    return {
        "statusCode": 403,
        "body": json.dumps({"error": "Validation failed"}),
    }
```

## Patrones comun y soluciones

### Problema: siempre "timeout-or-duplicate"

**Causa 1:** Intentando validar el mismo token 2 veces

```python
# ❌ MAL: validas dos veces
validate_turnstile_token(token)  # OK
validate_turnstile_token(token)  # timeout-or-duplicate
```

**Solucion:** Validar una sola vez. Si necesitas retry, usar `idempotency_key`
(ver seccion 06-anti-replay).

**Causa 2:** Token expiro (>5 minutos desde generacion)

**Solucion:** Verificar timestamp en cliente antes de submit.

### Problema: "bad-request" consistentemente

**Causa:** Enviando parametros en query string en lugar de JSON body

```python
# ❌ MAL
requests.post(
    "https://challenges.cloudflare.com/turnstile/v0/siteverify?secret=...&response=..."
)

# ✅ BIEN
requests.post(
    "https://challenges.cloudflare.com/turnstile/v0/siteverify",
    json={"secret": "...", "response": "..."},
)
```

### Problema: "invalid-input-secret"

**Causa:** Secret key es invalida (copiada mal, expirada, etc.)

**Solucion:**
1. Ir a dashboard Cloudflare
2. Copiar secret key nuevamente
3. Actualizar `TURNSTILE_SECRET_KEY` en Lambda env
4. Re-deploy

### Problema: "internal-error" ocasional

**Causa:** Cloudflare tiene problema temporal

**Solucion:** Implementar retry con exponential backoff

```python
import time

def validate_with_retry(token: str, max_retries: int = 3) -> TurnstileResponse:
    for attempt in range(max_retries):
        try:
            return validate_turnstile_token(token)
        except TurnstileValidationError as e:
            if e.error_code == "internal_error" and attempt < max_retries - 1:
                wait_time = (2 ** attempt)  # 1s, 2s, 4s
                logger.warning(
                    f"Turnstile internal error, retrying in {wait_time}s"
                )
                time.sleep(wait_time)
            else:
                raise
```

## Monitoreo y alertas

Configurar alertas en Lambda CloudWatch para:

```
ERROR
  error_code = "invalid-input-secret" → Problema con credenciales
  error_code = "internal-error" (persistente) → Posible outage Cloudflare
  statusCode = 403 (spike) → Posible ataque

WARNING
  error_code = "timeout-or-duplicate" (alto rate) → Usuarios retryando
```
