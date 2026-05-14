# Anti-replay y best practices de idempotency

> Cada token Turnstile se valida una sola vez. Como manejar retries
> sin que el token sea rechazado.

[← Error codes](./05-error-codes.md) | [Siguiente: CORS/CSP →](./07-cors-multidomain.md)

## Principio fundamental

**Cada token Turnstile se valida UNA SOLA VEZ.**

Si intentas validar el mismo token 2 veces (incluso en 2 requests diferentes),
la segunda validacion fallara con `timeout-or-duplicate`.

Esto es una **caracteristica de seguridad** que previene:

1. **Token replay attacks** — un atacante roba un token y lo usa multiples veces
2. **Bot chains** — un bot valida un token, lo guarda, lo usa en 1000 requests

## Escenario problematico

```
1. Cliente hace POST /contact con token T1 + form data
2. Backend valida T1 en siteverify → OK
3. Backend intenta guardar a DB → timeout/error
4. Cliente reintenta (sin saber que backend ya valido T1)
5. Backend intenta validar T1 nuevamente → timeout-or-duplicate
6. Cliente ve 403, piensa "captcha fallo", regenera token
7. Usuario molesto, tuvo que resolver el captcha 2 veces
```

La solucion: **idempotency_key**

## Solucion 1: idempotency_key (RECOMENDADO)

Cloudflare Turnstile soporta `idempotency_key` en siteverify desde 2023.

Si envias la MISMA `idempotency_key` en dos requests, Cloudflare retorna
el MISMO resultado la segunda vez, sin contar como "validacion duplicada".

### Implementacion Python

```python
import uuid
import hashlib
from typing import Optional

def validate_turnstile_token_idempotent(
    token: str,
    remote_ip: str | None = None,
    idempotency_key: str | None = None,
) -> dict:
    """
    Validar token Turnstile con soporte para idempotency.
    
    Args:
        token: Token del cliente
        remote_ip: IP del cliente (opcional)
        idempotency_key: Clave de idempotencia. Si es None,
                         se genera a partir del token + remoteip
    """
    secret_key = os.getenv("TURNSTILE_SECRET_KEY")

    # Generar idempotency_key si no fue proporcionada
    if not idempotency_key:
        key_material = f"{token}{remote_ip or ''}"
        idempotency_key = hashlib.sha256(
            key_material.encode()
        ).hexdigest()

    payload = {
        "secret": secret_key,
        "response": token,
        "idempotency_key": idempotency_key,
    }
    if remote_ip:
        payload["remoteip"] = remote_ip

    with httpx.Client(timeout=10) as client:
        response = client.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            json=payload,
        )
    response.raise_for_status()

    result = response.json()
    logger.info(
        f"Turnstile validation (idempotent): "
        f"success={result['success']}, "
        f"key={idempotency_key[:8]}..."
    )
    return result
```

### Patron: Lambda idempotent handler

```python
def lambda_handler(event: dict, context) -> dict:
    """POST /api/contact con idempotency."""
    try:
        body = json.loads(event.get("body", "{}"))
        token = body.get("cf-token", "")
        name = body.get("name", "")
        email = body.get("email", "")
        message = body.get("message", "")
        remote_ip = event["requestContext"]["identity"]["sourceIp"]

        # Generar idempotency_key a partir del token
        # (garantiza que mismo cliente con mismo token = mismo key)
        idempotency_key = hashlib.sha256(
            f"{token}{remote_ip}".encode()
        ).hexdigest()

        # Validar con idempotency
        try:
            turnstile_result = validate_turnstile_token_idempotent(
                token=token,
                remote_ip=remote_ip,
                idempotency_key=idempotency_key,
            )
            if not turnstile_result["success"]:
                return {
                    "statusCode": 403,
                    "body": json.dumps({"error": "Captcha failed"}),
                }
        except TurnstileValidationError as e:
            return {
                "statusCode": 403,
                "body": json.dumps(
                    {"error": "Validation failed", "code": e.error_code}
                ),
            }

        # Procesar contacto (si pasa Turnstile)
        try:
            # Guardar a DB
            db_client.put_item(
                Item={
                    "id": str(uuid.uuid4()),
                    "email": email,
                    "name": name,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            # Enviar email
            send_email(to=email, subject="Contacto recibido", body=message)
        except Exception as e:
            logger.error(f"Error procesando contacto: {e}")
            # Si DB falla pero Turnstile paso, el cliente PUEDE reintentar
            # con el mismo token y mismo idempotency_key → siteverify devolvera
            # el mismo success=true (cached), DB operacion se re-ejecutara
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Processing error"}),
            }

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Contact received"}),
        }

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal error"}),
        }
```

## Solucion 2: Prevenir retries innecesarios en cliente

No usar idempotency_key pero evitar que el cliente reintente automaticamente:

```javascript
// En el cliente (Astro/JavaScript)
let isSubmitting = false

document.querySelector('form').addEventListener('submit', async (e) => {
  e.preventDefault()

  if (isSubmitting) {
    console.warn('Submit ya en progreso')
    return
  }

  isSubmitting = true
  try {
    const formData = new FormData(e.target)
    const response = await fetch('/api/contact', {
      method: 'POST',
      body: JSON.stringify(Object.fromEntries(formData)),
    })

    if (response.ok) {
      alert('Contacto enviado!')
      e.target.reset()
    } else {
      const error = await response.json()
      if (error.code === 'timeout-or-duplicate') {
        alert('Token expiro. Resuelve el captcha nuevamente.')
        window.turnstile.reset()
      } else {
        alert('Error al enviar contacto. Intenta nuevamente.')
      }
    }
  } finally {
    isSubmitting = false
  }
})
```

## Cuando usar cada solucion

| Solucion | Caso | Recomendacion |
|----------|------|---------------|
| idempotency_key | DB lento, network flaky, errores ocasionales | **USAR ESTA** |
| No retry en cliente | Network ok, backend rapido y confiable | Alternativa simple |

## Anti-patterns

- ❌ Mostrar "Intenta nuevamente" sin regenerar token
- ❌ Validar token 2 veces en un mismo request (split entre servicios)
- ❌ Guardar tokens en cache/Redis para reusar
- ❌ Ignorar `idempotency_key` si backend es flaky

## Verificacion: idempotency en accion

```bash
# Request 1
curl -X POST https://challenges.cloudflare.com/turnstile/v0/siteverify \
  -H "Content-Type: application/json" \
  -d '{
    "secret": "...",
    "response": "TOKEN",
    "idempotency_key": "abc123"
  }'
# Response: {"success": true, ...}

# Request 2 (mismo key)
curl -X POST https://challenges.cloudflare.com/turnstile/v0/siteverify \
  -H "Content-Type: application/json" \
  -d '{
    "secret": "...",
    "response": "TOKEN",
    "idempotency_key": "abc123"
  }'
# Response: {"success": true, ...}  ← MISMO resultado (cached)

# Request 3 (sin idempotency_key, mismo token)
curl -X POST https://challenges.cloudflare.com/turnstile/v0/siteverify \
  -H "Content-Type: application/json" \
  -d '{
    "secret": "...",
    "response": "TOKEN"
  }'
# Response: {"success": false, "error_codes": ["timeout-or-duplicate"]}
```
