# Arquitectura: REST API vs HTTP API vs WebSocket

> Comparacion de tipos de API Gateway en AWS 2026. Decision: REST API es
> correcta para este portfolio. Justificacion de features y precios.

[← README](./README.md) | [Siguiente: Throttling fundamentals →](./02-throttling-fundamentals.md)

## Decision: REST API (no HTTP API)

Para este portfolio con 3 endpoints (contact, track, validate-turnstile) que
requieren throttling granular por-IP y validacion de request, **REST API es
la eleccion correcta**, aunque sea mas cara que HTTP API.

### Por que REST API

1. **Usage Plans + API Keys**: REST API soporta usage plans (cuotas, throttling
   per-cliente). HTTP API no. Aunque en este caso no usaremos API keys publicas
   (es form publico), los usage plans nos dan throttling global por endpoint.
2. **Request Validators**: REST API permite validar request body, headers, query
   strings ANTES de invocar Lambda via JSON Schema. HTTP API no tiene esto.
   Invalida el request en API Gateway = $0 Lambda invocation.
3. **WAF Integration**: Ambos soportan WAF, pero REST API combina mejor con
   usage plans (una capa de throttling global + WAF para per-IP).
4. **Caching per-method**: REST API permite cache por metodo. HTTP API caching
   es mas limitado. Util para /track (telemetria) que es idempotente.
5. **Gateway Responses personalizadas**: REST API permite customizar respuestas
   de error (4xx, 5xx) incluyendo CORS headers. Necesario para pre-flight
   failing gracefully.

### Tradeoff: REST API es 3.5x mas caro que HTTP API

- **REST API**: $3.50 / 1M requests
- **HTTP API**: $1.00 / 1M requests
- **Estimado mensual (10K requests)**: $0.035 REST vs $0.010 HTTP

Pero para este volumen, la diferencia es $0.02-0.03/mes. Negligible.
Las features valen la pena.

## Comparacion completa (2026)

| Feature | REST API | HTTP API | WebSocket |
|---------|----------|----------|-----------|
| **Pricing** | $3.50/M | $1.00/M | $3.50/M + $0.25/M msgs |
| **Usage Plans** | Si | No | N/A |
| **API Keys** | Si | Si (simple) | No |
| **Request Validators** | Si (JSON Schema) | No | N/A |
| **Response Mapping** | Si (templates) | Limitado | N/A |
| **WAF Integration** | Si | Si | Si |
| **Gateway Responses** | Si | Si | Si |
| **Caching per-method** | Si | No (stage-level) | N/A |
| **CORS** | Manual (OPTIONS) | Declarativo | N/A |
| **Authorizers** | Lambda, Cognito, OAuth | Lambda, JWT | N/A |
| **VPC Endpoint** | Si | Si | Si |
| **CloudTrail logging** | Si | Si | Si |
| **X-Ray tracing** | Si | Si | Si |
| **Custom domains** | Si | Si | Si |
| **TLS 1.2+** | Si | Si | Si |

## Topologia del API (arquitectura recomendada)

```
                    the-full-stack.com
                            |
                    api.the-full-stack.com (custom domain)
                            |
                      [ACM Certificate]
                            |
                   [REST API Gateway]
                    (us-west-2, prod)
                            |
          +-------------------+-------------------+
          |                   |                   |
      [WAF Web ACL]     [Usage Plans]      [Request Validators]
    (rate-based rule   (global throttle)  (JSON Schema per route)
     per IP)               
          |                   |                   |
    Bloquea IPs         Throttle 429      Rechaza bad
    >3 req/5min         responses con     request 400
    desde una IP        Retry-After
          |                   |                   |
          +-------------------+-------------------+
                            |
                      [3 Lambda Functions]
                            |
          +-------------------+-------------------+
          |                   |                   |
      [Lambda]            [Lambda]            [Lambda]
      /contact            /track          /validate-turnstile
      (strict)            (moderate)       (moderate)
```

## Endpoints y limites de throttling

| Endpoint | Rate limit | Burst | Quota diaria | Backend |
|----------|-----------|-------|-------------|---------|
| `POST /contact` | 3 req/min per IP | 5 requests | 50/dia per IP | contact.py |
| `POST /track` | 30 req/min per IP | 60 requests | 1000/dia per IP | track.py |
| `POST /validate-turnstile` | 30 req/min per IP | 60 requests | 1000/dia per IP | validate.py |

## Configuracion de dominios

- **Apex**: no. API en subdominio `api.the-full-stack.com`.
- **Certificate**: ACM en us-west-2, validacion DNS via Route 53.
- **Registrar**: AWS Route 53 (donde esta registrado el dominio).
- **DNS**: Usar Route 53 (mismo registrar) o CF DNS si migras zona.
- **Hotlinks permitidos**: solo 6 subdominios portfolio + localhost dev.

CORS whitelist:
```
- https://the-full-stack.com
- https://hub.the-full-stack.com
- https://fintech.the-full-stack.com
- https://architect.the-full-stack.com
- https://leader.the-full-stack.com
- https://vibe.the-full-stack.com
- http://localhost:3000 (dev local)
```

## Region y multi-region (futuro)

**Region actual**: us-west-2 (Oregon). Decisiones:

1. **Una region es suficiente**: el portfolio es estatico en Cloudflare Pages
   (edge worldwide). El API es backend de bajo volumen. No necesita multi-region.
2. **Si el volumen crece**: agregar region adicional (us-east-1) y usar Route 53
   geolocation routing. Pero hoy no justificado.
3. **DynamoDB (futuro)**: si agregas DB para logging de tracking, usar DynamoDB
   global tables (multi-region replication). Hoy no necesario.

## SSL/TLS

- **ACM Certificate**: Universal SSL generado por AWS. Renovacion automatica.
- **TLS version**: Minimo TLS 1.2 (default REST API). Puede configurarse a 1.3.
- **Ciphers**: Default AWS managed (fuerte, FIPS compatible).
- **API endpoint**: solo HTTPS. No permitir HTTP.

## API Key management

**Decision**: NO usar API keys publicas en el frontend.

Razon: las API keys en el cliente JavaScript son comprometibles. Para formularios
publicos sin autenticacion, confiar en:

1. **WAF rate-based rule per IP** (primera defensa contra volumetria)
2. **API Gateway throttling** (segunda defensa per endpoint)
3. **CORS restriction** (tercera defensa: solo origenes permitidos)

Si en el futuro tienes clientes B2B con cuotas distintas, entonces:
- Crear API key para cada cliente (en AWS, no en el codigo)
- Pasar API key via header `x-api-key`
- Usage plan con throttle/quota distinct por cliente
- Rotar keys mensualmente via AWS Secrets Manager

## Next steps

1. Leer [02-throttling-fundamentals.md](./02-throttling-fundamentals.md)
   para entender token bucket algorithm y niveles de throttling.
2. Leer [03-rate-limit-per-ip.md](./03-rate-limit-per-ip.md) para WAF
   rate-based rules (el mecanismo de per-IP rate-limiting).
3. Leer [07-deployment-sam.md](./07-deployment-sam.md) para template SAM
   completo.

Verificado a fecha 2026-05-13.
