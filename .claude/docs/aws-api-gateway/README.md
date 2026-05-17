# AWS API Gateway knowledge base

> Conocimiento consolidado sobre diseño, throttling, rate-limiting y seguridad
> de API Gateway REST para el portfolio stateless. Cada nodo cubre un tema
> especifico; navegar por relevancia, no leer linealmente.

## Cuando leer cada archivo

| Tema | Archivo | Cuando leer |
|------|---------|-------------|
| Arquitectura: REST vs HTTP vs WebSocket | [01-architecture.md](./01-architecture.md) | Entender diferencias 2026, features, precios. Decision recomendada: REST API |
| Throttling fundamentals: token bucket, niveles | [02-throttling-fundamentals.md](./02-throttling-fundamentals.md) | Como funciona throttling nativo de API Gateway, 429 responses, retry |
| Rate-limiting per-IP via AWS WAF | [03-rate-limit-per-ip.md](./03-rate-limit-per-ip.md) | API Gateway no lo soporta nativo. Solucion: WAF rate-based rules por IP |
| Usage plans, API keys, quotas | [04-usage-plans-api-keys.md](./04-usage-plans-api-keys.md) | Cuando usar. Para formularios publicos sin API key, usar WAF para per-IP |
| CORS seguro para Cloudflare Pages | [05-cors-security.md](./05-cors-security.md) | Configurar CORS en REST API restringido a 6 subdominios portfolio |
| Request validation con JSON Schema | [06-request-validation.md](./06-request-validation.md) | Validar request body/headers ANTES de invocar Lambda. Ahorra dinero |
| Deployment con SAM template completo | [07-deployment-sam.md](./07-deployment-sam.md) | Ejemplo SAM: API + Lambdas + WAF + custom domain + samconfig.toml |
| Monitoring: CloudWatch Logs, X-Ray, metricas | [08-monitoring-logs.md](./08-monitoring-logs.md) | Access logs JSON, alertas para 429 anormal, distributed tracing |
| Cost y estrategia de defense in depth | [09-cost-throttling-strategy.md](./09-cost-throttling-strategy.md) | Pricing 2026 us-east-1. Estimado <$20/mes. Capas: WAF → API GW → Lambda |

## Reglas criticas

- **REST API es la decision correcta para este caso**: necesitas usage plans
  (throttling global), request validation (JSON Schema), WAF integration
  para per-IP rate-limiting. HTTP API es mas barato pero carece de estos.
  Justificacion completa en [01-architecture.md](./01-architecture.md).

- **API Gateway nativo NO hace rate-limit per-IP**: solo por API key (cliente).
  Para limitar por IP, SIEMPRE usar AWS WAF con rate-based rule. Obligatorio
  si quieres defense contra volumetria masiva desde una IP maliciosa.

- **WAF rate-based rule minimo 10 req en ventana de 5 min** (cambio May 2025).
  Esto significa que IPs con >10 req en 5 min seran bloqueadas. Ajustar segun
  caso (form contacto: 3 req/min = OK; tracking pixel: 30 req/min = OK).

- **Request validation ahorra dinero**: invalida en API GW ANTES de invocar
  Lambda. Request body malo = 400 de gratis, sin pagar invocacion.

- **CORS en REST API requiere mapeo manual de error responses**: API Gateway
  solo agrega headers CORS a 200. Configurar gateway responses para 4xx/5xx
  para incluir CORS headers, si no el cliente rechaza la respuesta.

- **Custom domain + ACM cert obligatorio para produccion**: nunca exponer
  execute-api endpoint publicamente. Usar ACM cert en us-east-1 (mismo
  region que API Gateway).

## Quick start: desplegar el API

```bash
# 1. Editar template SAM: sam.yaml
#    - Adjustar nombres de Lambdas, rutas, throttling
#    - Configurar CORS origins (6 subdominios del portfolio)
#    - Definir usage plans con limites correctos

# 2. Crear ACM cert para custom domain (one-time)
aws acm request-certificate \
  --domain-name api.the-full-stack.com \
  --validation-method DNS \
  --region us-east-1

# 3. Build + deploy
sam build
sam deploy --guided  # samconfig.toml crea la primera vez

# 4. Verificar
aws apigateway get-rest-apis --region us-east-1
aws wafv2 list-web-acls --scope REGIONAL --region us-east-1

# 5. Test endpoints con curl o Postman
curl -X POST https://api.the-full-stack.com/contact \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","message":"Hola"}'

# Esperar 429 si excedes throttle (verificar Rate-Limit-Limit header)
```

## Estado actual del API (2026-05-13)

- **Endpoints**: 2 (POST /contact, POST /track)
- **Backends**: 2 Lambdas Python 3.13 independientes
- **API Type**: REST API (decision justificada en 01-architecture.md)
- **Region**: us-east-1 (Oregon)
- **CORS**: Restringido a 6 subdominios portfolio + CloudflarePages origin
- **WAF**: Rate-based rule per-IP. /contact: 3 req/min, /track: 30 req/min
- **Monitoring**: CloudWatch Logs (JSON), X-Ray tracing activo, alarmas para 429
- **Cost estimado**: <$20/mes (api calls + data transfer + WAF)

## Archivos criticos del proyecto

- SAM template: `.aws/template.yaml` (IaC completo)
- samconfig.toml: configuracion de regiones, stages, parametros
- `.aws/policies/cors-origins.json`: whitelist de 6 subdominios
- `.aws/waf/rules.yaml`: definicion de rate-based rules per endpoint
- Lambda handlers: `functions/contact.py`, `functions/track.py`

## Verificacion obligatoria pre-deployment

- [ ] SAM template valido (`sam validate`)
- [ ] ACM cert en us-east-1 emitido y validado
- [ ] CORS origins son los 6 subdominios + CloudflarePages
- [ ] Request validators definidos para /contact (/track es telemetria, validacion minima)
- [ ] Usage plans con throttle/quota correctos
- [ ] WAF Web ACL asociada al API Gateway
- [ ] CloudWatch Log Group creado (sam deploy lo hace, verificar)
- [ ] X-Ray tracing habilitado en stage
- [ ] Pre-flight test: `curl -X OPTIONS https://api.../contact` devuelve CORS headers

## Anti-patterns prohibidos

- No usar HTTP API si necesitas usage plans o WAF integration (REST API es obligatorio)
- No exponer el endpoint execute-api publicamente (usar custom domain)
- No confiar SOLO en API Gateway throttling para proteger contra ataques volumetricos (agregar WAF)
- No definir CORS como `*` en produccion (restriccion estricta a 6 subdominios)
- No invocar Lambda si la request falla validacion (usa request validators de API GW)

## Referencias

- AWS API Gateway Pricing 2026: https://aws.amazon.com/api-gateway/pricing/
- AWS WAF Pricing 2026: https://aws.amazon.com/waf/pricing/
- SAM developer guide: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/
- API Gateway Throttling: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html

Verificado a fecha 2026-05-13.
