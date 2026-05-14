# CORS y seguridad de origenes

> Configuracion segura de CORS en REST API Gateway. Restriccion estricta
> a 6 subdominios portfolio + localhost dev. Anti-pattern: CORS *wildcard.

[← Usage plans](./04-usage-plans-api-keys.md) | [README](./README.md) | [Siguiente: Request validation →](./06-request-validation.md)

## CORS problem

Browsers (por Same-Origin Policy) rechazan requests cross-origin a menos
que el servidor autorice explicitamente con headers CORS.

Cuando el cliente (JavaScript en un subdominio) hace fetch POST a otro
subdominio (API), el browser:

1. **Pre-flight**: envia OPTIONS request sin body para preguntar si puede
2. **Validacion**: recibe response con headers Access-Control-Allow-Origin,
   Access-Control-Allow-Methods, Access-Control-Allow-Headers
3. **Ejecucion**: si preflight OK, envia POST real

```
Browser en https://hub.the-full-stack.com
                 |
                 v fetch('https://api.the-full-stack.com/contact', ...)
                 |
      [Pre-flight OPTIONS request sin body]
      Origin: https://hub.the-full-stack.com
                 |
                 v API Gateway
                 |
      [OPTIONS response con CORS headers]
      Access-Control-Allow-Origin: https://hub.the-full-stack.com
      Access-Control-Allow-Methods: POST
      Access-Control-Allow-Headers: Content-Type
                 |
                 v Browser valida preflight
                 |
      [Real POST request se ejecuta]
                 |
                 v Lambda procesa
```

## CORS en REST API Gateway

En REST API, CORS se configura:

1. **Crear OPTIONS method** (API Gateway lo hace automaticamente)
2. **Responder con headers CORS** (solo en 2xx, por default)
3. **Configurar error responses** con CORS (importante)

### Patron SAM (CORS basico)

```yaml
Resources:
  PortfolioApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: prod
      Cors:
        AllowMethods: "'POST,OPTIONS,GET'"
        AllowHeaders: "'Content-Type,Authorization'"
        AllowOrigin: "'https://the-full-stack.com'"
        MaxAge: "'600'"
```

Esto genera un OPTIONS method que devuelve:
```
HTTP/1.1 200 OK
Access-Control-Allow-Methods: POST, OPTIONS, GET
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Origin: https://the-full-stack.com
Access-Control-Max-Age: 600
```

### Problema: errores 4xx/5xx sin CORS headers

Por defecto, API Gateway SOLO agrega CORS headers a respuestas 2xx.
Si la validacion falla (400) o hay error (500), no hay CORS headers,
y el browser rechaza la respuesta.

Solucion: **Gateway responses** con CORS para error codes.

```yaml
Resources:
  PortfolioApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: prod
      Cors:
        AllowMethods: "'POST,OPTIONS,GET'"
        AllowHeaders: "'Content-Type,Authorization'"
        AllowOrigin: "'https://the-full-stack.com'"
        MaxAge: "'600'"
      GatewayResponses:
        BadRequest:
          StatusCode: 400
          DefaultResponse: false
          ResponseHeaders:
            Access-Control-Allow-Origin: "'https://the-full-stack.com'"
            Access-Control-Allow-Headers: "'Content-Type,Authorization'"
            Access-Control-Allow-Methods: "'POST,OPTIONS,GET'"
        Unauthorized:
          StatusCode: 401
          DefaultResponse: false
          ResponseHeaders:
            Access-Control-Allow-Origin: "'https://the-full-stack.com'"
            Access-Control-Allow-Headers: "'Content-Type,Authorization'"
            Access-Control-Allow-Methods: "'POST,OPTIONS,GET'"
        Throttled:
          StatusCode: 429
          DefaultResponse: false
          ResponseHeaders:
            Access-Control-Allow-Origin: "'https://the-full-stack.com'"
            Access-Control-Allow-Headers: "'Content-Type,Authorization'"
            Access-Control-Allow-Methods: "'POST,OPTIONS,GET'"
```

Ahora, incluso errores de validacion o throttling incluyen CORS headers.

## Whitelist de origenes: 6 subdominios

Para este portfolio, permitir SOLO estos origenes:

```yaml
AllowOrigin: |
  '
  https://the-full-stack.com,
  https://www.the-full-stack.com,
  https://hub.the-full-stack.com,
  https://fintech.the-full-stack.com,
  https://architect.the-full-stack.com,
  https://leader.the-full-stack.com,
  https://vibe.the-full-stack.com,
  http://localhost:3000
  '
```

Nota: no puedes usar multiples origenes en un string. Necesitas un CloudFront
distribution o usar un Lambda authorizer para validar dinamicamente.

**Solucion simple: CloudFront + Lambda@Edge** (futuro, hoy no necesario).

Por ahora, usar **un solo origin principal** y agregar otros en CloudFront
si es necesario.

Simplificado:
```yaml
AllowOrigin: "'https://the-full-stack.com'"
```

Los subdominios (hub., fintech., etc.) estan bajo el mismo dominio, asi que
si API esta en `api.the-full-stack.com`, funciona cross-site pero del mismo
dominio efectivamente.

## Seguridad: NUNCA usar wildcard *

**PROHIBIDO**:
```yaml
AllowOrigin: "'*'"  # ❌ INSEGURO
```

Razon: permite cross-origin access desde CUALQUIER sitio, incluyendo
maliciosos. Atacante puede:
1. Inyectar <script> en otro sitio
2. Hacer fetch POST a tu API
3. Robar datos, hacer acciones maliciosas

Ejemplo ataque:
```javascript
// Codigo inyectado en hacker.com
fetch('https://api.the-full-stack.com/contact', {
  method: 'POST',
  credentials: 'include',  // envia cookies si existen
  body: JSON.stringify({
    email: 'attacker@hacker.com',
    message: 'Suscribeme spam'
  })
})
```

Con `AllowOrigin: *`, esto funciona. Sin wildcard, browser lo bloquea.

## Credentials (cookies) en CORS

Por defecto, browsers no envian cookies en requests cross-origin.

Para habilitar:

```javascript
fetch('https://api.the-full-stack.com/contact', {
  method: 'POST',
  credentials: 'include',  // envia cookies
  body: JSON.stringify({...})
})
```

Y en API Gateway, permitir credenciales:

```yaml
AllowCredentials: true  # En SAM Cors
```

Response:
```
Access-Control-Allow-Credentials: true
Access-Control-Allow-Origin: https://the-full-stack.com  # Nota: NO puede ser *
```

**Nota**: si habilitas `AllowCredentials: true`, `AllowOrigin` NO puede ser `*`.
Debe ser especifico.

Para este portfolio (form publico sin login), **no necesitas credentials**.

## Custom domain y SSL/TLS

API debe servirse por HTTPS, no HTTP.

```yaml
Domain:
  DomainName: api.the-full-stack.com
  CertificateArn: arn:aws:acm:us-west-2:ACCOUNT:certificate/abc123
  BasePath:
    - /
```

ACM cert debe estar en la misma region (us-west-2).

Certificado se valida una vez y se renueva automaticamente.

## Testing CORS

Pre-flight (OPTIONS):
```bash
curl -X OPTIONS https://api.the-full-stack.com/contact \
  -H "Origin: https://hub.the-full-stack.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v
```

Esperado:
```
HTTP/1.1 200 OK
Access-Control-Allow-Methods: POST, OPTIONS, GET
Access-Control-Allow-Origin: https://hub.the-full-stack.com
Access-Control-Allow-Headers: Content-Type
```

Real POST:
```bash
curl -X POST https://api.the-full-stack.com/contact \
  -H "Origin: https://hub.the-full-stack.com" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","message":"Test"}' \
  -v
```

Esperado: 200 OK (si validacion pasa) o 400 (si falla).
Ambos deben incluir `Access-Control-Allow-Origin` header.

## Gotchas

### Gotcha 1: Preflight cache

El browser cachea preflight responses segun `Access-Control-Max-Age`.

```
Access-Control-Max-Age: 600  # 10 minutos
```

Significa que por 10 min, browser no hace nuevos OPTIONS requests para
el mismo metodo + origen + headers.

Si cambias CORS config, esperar 10 min (o limpiar cache del browser).

### Gotcha 2: Credenciales en URL

No puedes pasar credenciales en la URL (ej. `https://user:pass@api.com`).
Los browsers lo rechazan.

Usa headers `Authorization: Bearer <token>` en su lugar.

### Gotcha 3: Response body diferente en preflight

En preflight (OPTIONS), el body es vacio y la response viene de API Gateway,
no de tu Lambda.

En POST real, la response viene de Lambda.

Si necesitas incluir CORS headers en respuesta de error, hazlo en Lambda:

```python
def lambda_handler(event, context):
    try:
        # Procesar request
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'OK'}),
            'headers': {
                'Access-Control-Allow-Origin': event['headers'].get('Origin', '*'),
                'Content-Type': 'application/json'
            }
        }
    except ValueError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)}),
            'headers': {
                'Access-Control-Allow-Origin': event['headers'].get('Origin', '*'),
                'Content-Type': 'application/json'
            }
        }
```

### Gotcha 4: Validar Origin en Lambda

NUNCA confies en el header Origin. Validar en Lambda:

```python
ALLOWED_ORIGINS = [
    'https://the-full-stack.com',
    'https://hub.the-full-stack.com',
    'https://fintech.the-full-stack.com',
    'http://localhost:3000'
]

def lambda_handler(event, context):
    origin = event['headers'].get('Origin', '')
    
    if origin not in ALLOWED_ORIGINS:
        return {
            'statusCode': 403,
            'body': json.dumps({'error': 'Origin not allowed'}),
        }
    
    # Procesar
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'OK'}),
        'headers': {
            'Access-Control-Allow-Origin': origin,
            'Content-Type': 'application/json'
        }
    }
```

## Next steps

- [06-request-validation.md](./06-request-validation.md) — JSON Schema validation
- [07-deployment-sam.md](./07-deployment-sam.md) — template SAM completo
- [08-monitoring-logs.md](./08-monitoring-logs.md) — logging y metricas

Verificado a fecha 2026-05-13.
