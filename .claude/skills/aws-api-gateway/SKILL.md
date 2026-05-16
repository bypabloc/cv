---
name: aws-api-gateway
description: >
  AWS API Gateway reference for this portfolio (us-west-2, REST API with
  3 endpoints: POST /contact 3 req/min/IP, POST /track 30 req/min/IP,
  POST /validate-turnstile internal). Covers REST API vs HTTP API
  decision (REST chosen for usage plans + request validators despite
  3.5x cost), the CRITICAL gotcha that API Gateway throttling is GLOBAL
  not per-IP (per-IP rate limiting REQUIRES AWS WAF rate-based rules,
  $5/Web ACL/mo + $1/M req + $0.60/rule/mo), token bucket throttling
  algorithm (steady-state rate + burst), throttling hierarchy (per-client
  > per-method > account-level > regional), JSON Schema request
  validators (reject invalid before Lambda invoke saves cost), CORS for
  REST API (gateway responses manual for 4XX/5XX, whitelist 6
  subdomains the-full-stack.com + niches), custom domain with ACM cert,
  SAM template with AWS::Serverless::Api + AWS::WAFv2::WebACL +
  WebACLAssociation, CloudWatch access logs in JSON
  ($context.identity.sourceIp), X-Ray tracing, alarms for 429 anomalies,
  pricing 2026 us-west-2 (REST $3.50/M, HTTP $1.00/M, total stack
  ~$7/mo dominated by WAF fixed cost), and defense-in-depth strategy
  (5 layers: WAF > API GW throttle > request validator > Lambda logic >
  CloudWatch alarms). ALWAYS invoke this skill BEFORE answering ANY
  question about API Gateway, rate limiting per IP in AWS, throttling
  AWS, WAF rate-based rules, or AWS REST API setup for this project.
  NEVER answer from training data alone — this project has consolidated
  2026 knowledge (REST vs HTTP API decision, WAF as the ONLY native
  way to do per-IP rate limiting in API Gateway, exact pricing
  us-west-2) that overrides generic advice.
  Use when the user says "api gateway", "aws api gateway", "rest api
  aws", "http api aws", "api gateway throttle", "throttling aws",
  "rate limit aws", "rate limit por ip", "rate limit per ip",
  "limitar peticiones por ip", "bloquear ip aws", "waf aws",
  "aws waf", "waf rate-based", "rate-based rule", "ddos protection
  aws", "anti-spam api", "anti-bot api gateway", "usage plan aws",
  "api key aws", "throttle 429", "429 too many requests",
  "request validator aws", "json schema api gateway", "cors api
  gateway", "preflight aws", "options method aws", "custom domain api
  gateway", "acm api gateway", "api custom domain", "cloudwatch access
  logs", "$context.identity.sourceIp", "x-ray api gateway",
  "como expongo una lambda", "como hago un endpoint en aws", "como
  protejo mi api de spam", "endpoint http aws", "endpoint serverless",
  "que diferencia entre rest y http api", "rest vs http api",
  "precio api gateway", "costo api gateway", "api gateway free tier".
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash(sam:*), Bash(aws:*), Bash(curl:*)
argument-hint: "tema: architecture | throttle | rate-limit-ip | usage-plan | cors | validation | deploy | monitor | cost"
metadata:
  version: "1.0"
---

# AWS API Gateway — knowledge reference

> Conocimiento consolidado sobre API Gateway para el portfolio (REST API
> en us-west-2 con 3 endpoints + WAF rate-based rules por IP). Todo
> decision, gotcha y precio en `.claude/docs/aws-api-gateway/`.

## Pre-requisito OBLIGATORIO

Antes de responder, leer la doc relevante de `.claude/docs/aws-api-gateway/`:

| Tema de la pregunta | Archivo a leer |
|---------------------|----------------|
| REST vs HTTP vs WebSocket API | [01-architecture.md](../../docs/aws-api-gateway/01-architecture.md) |
| Throttling: token bucket, jerarquia, 429 | [02-throttling-fundamentals.md](../../docs/aws-api-gateway/02-throttling-fundamentals.md) |
| Rate limit per-IP (WAF requerido) | [03-rate-limit-per-ip.md](../../docs/aws-api-gateway/03-rate-limit-per-ip.md) |
| Usage plans + API keys (B2B futuro) | [04-usage-plans-api-keys.md](../../docs/aws-api-gateway/04-usage-plans-api-keys.md) |
| CORS, preflight, multi-origin whitelist | [05-cors-security.md](../../docs/aws-api-gateway/05-cors-security.md) |
| Request validators (JSON Schema) | [06-request-validation.md](../../docs/aws-api-gateway/06-request-validation.md) |
| SAM template + ACM + WAF deployment | [07-deployment-sam.md](../../docs/aws-api-gateway/07-deployment-sam.md) |
| CloudWatch logs, X-Ray, alarms | [08-monitoring-logs.md](../../docs/aws-api-gateway/08-monitoring-logs.md) |
| Pricing 2026 + defense in depth | [09-cost-throttling-strategy.md](../../docs/aws-api-gateway/09-cost-throttling-strategy.md) |

## Reglas criticas (siempre activas)

1. **SIEMPRE** REST API para este portfolio. HTTP API es 3.5x mas barato
   pero NO soporta usage plans ni request validators. La diferencia de
   precio (<$0.04/mes) NO justifica perder esos features.

2. **SIEMPRE** AWS WAF con rate-based rule para rate-limit per-IP. API
   Gateway throttling nativo es GLOBAL (suma todas las IPs), NO per-IP.
   Sin WAF, un solo atacante consume el throttle bucket entero.
   Costo: $7/mes fijo. NO hay alternativa nativa.

3. **NUNCA** confiar en una sola capa de proteccion. Defense in depth:
   - Capa 1: WAF rate-based (per-IP)
   - Capa 2: API Gateway throttle (global por metodo)
   - Capa 3: Request validator (JSON Schema, rechaza antes de Lambda)
   - Capa 4: Lambda business logic (Turnstile validation)
   - Capa 5: CloudWatch alarms (deteccion anomalias)

4. **SIEMPRE** request validator con JSON Schema. Invalid requests se
   rechazan en API Gateway antes de invocar Lambda = ahorra cost +
   reduce attack surface.

5. **NUNCA** CORS con `AllowOrigin: '*'` para endpoints que reciben
   datos sensibles (form contacto). Whitelist explicito de los 6
   subdominios bajo `the-full-stack.com`. Y agregar Gateway Responses
   para CORS en error codes 4XX/5XX (default no los incluye).

6. **NUNCA** mezclar usage plans + WAF en la misma capa. Usage plans
   funcionan con API keys (clientes identificados). WAF funciona con
   IPs (anonimo publico). Para form publico = WAF. Para futuro B2B con
   API keys = usage plans.

7. **SIEMPRE** verificar la skill antes de modificarla con
   `claude --permission-mode bypassPermissions -p` (regla
   [.claude/rules/claude-config-testing.md](../../rules/claude-config-testing.md)).

## Workflow tipico de respuesta

1. Identificar el tema (throttle / rate-limit / cors / deploy / etc.)
2. Leer doc relevante de `.claude/docs/aws-api-gateway/`
3. Responder con:
   - SAM YAML snippet ejecutable
   - Comando AWS CLI para verificar
   - Costo estimado us-west-2 Mayo 2026
4. Si la pregunta cae fuera de scope: derivar a otra skill

## Atajos rapidos

### "Como protejo mi API de spam desde una IP?"

Solo WAF rate-based rule lo hace nativamente. API Gateway throttle es
global. Detalle + SAM completo en
[03-rate-limit-per-ip.md](../../docs/aws-api-gateway/03-rate-limit-per-ip.md).

```yaml
# WAF rate-based rule en SAM
ContactRateLimitRule:
  Type: AWS::WAFv2::WebACL
  Properties:
    Scope: REGIONAL
    Rules:
      - Name: ContactPerIPRateLimit
        Priority: 1
        Statement:
          RateBasedStatement:
            Limit: 30     # min 10 max 20M, ventana 5 min
            AggregateKeyType: IP
        Action: { Block: {} }
        VisibilityConfig: { ... }
```

### "REST API o HTTP API?"

REST. La diferencia de $0.04/mes no compensa perder usage plans +
request validators + WAF. Decision en
[01-architecture.md](../../docs/aws-api-gateway/01-architecture.md).

### "Cuanto va a costar el API?"

~$7.06/mes total a 10k req/mes:
- REST API GW: <$0.01
- WAF (Web ACL fijo): $7.00
- Lambda: $0 (free tier)
- CloudWatch: <$0.01

WAF es el dominador del costo. Escala excelente: a 1M req/mes sube a
~$15.95. Tabla completa en
[09-cost-throttling-strategy.md](../../docs/aws-api-gateway/09-cost-throttling-strategy.md).

### "El navegador rechaza con CORS error"

Causa tipica: status 4XX o 5XX sin CORS headers. API Gateway por
default solo agrega CORS headers a 2XX. Fix: configurar Gateway
Responses para DEFAULT_4XX y DEFAULT_5XX. Codigo en
[05-cors-security.md](../../docs/aws-api-gateway/05-cors-security.md).

### "Quiero validar el JSON antes de Lambda"

Request validator con JSON Schema model. Define el shape esperado,
API Gateway lo rechaza con 400 si no matchea. Ejemplo completo en
[06-request-validation.md](../../docs/aws-api-gateway/06-request-validation.md).

## Anti-patrones a evitar

- Responder "usa API Gateway throttle para rate-limit por IP" — NO funciona
- Recomendar `AllowOrigin: '*'` para evitar problemas CORS
- Sugerir HTTP API para ahorrar $0.04/mes a costa de perder features
- Omitir WAF "porque cuesta $7/mes" — sin el, no hay anti-spam
- Hardcodear URLs en CORS headers (usar AllowOrigin con whitelist)
- Olvidar Gateway Responses para error codes
- Pedir aumentar account-level throttle ANTES de tener WAF (no soluciona el problema)
- Cobrar Lambda invocations innecesarias por no usar request validator

## Comandos utiles

```bash
# Verificar API Gateway desplegado
aws apigateway get-rest-apis --region us-west-2

# Test endpoint contacto
curl -X POST https://api.the-full-stack.com/contact \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","message":"hola"}'

# Ver WAF metrics
aws wafv2 get-sampled-requests \
  --web-acl-arn <arn> \
  --rule-metric-name ContactPerIPRateLimit \
  --scope REGIONAL --region us-west-2 \
  --time-window StartTime=...,EndTime=... \
  --max-items 100

# CloudWatch Logs Insights query (top IPs throttled)
fields @timestamp, $context.identity.sourceIp, $context.status
| filter $context.status = 429
| stats count() by $context.identity.sourceIp
| sort by count desc
| limit 20
```

## Relacion con otras skills/rules

- `aws-lambda-python` — los 3 handlers detras de cada endpoint
- `cloudflare-turnstile` — primera capa de proteccion bot, antes que API Gateway
- `aws-dynamodb` — storage que Lambda escribe
- [.claude/rules/security.md](../../rules/security.md) — CORS, CSP, headers
- [.claude/rules/verify-before-done.md](../../rules/verify-before-done.md) — smoke test post-deploy

## Cuando NO invocar esta skill

- Pregunta sobre API REST framework (FastAPI, Flask, Express) — esos son backends, no API Gateway
- Pregunta sobre Cloudflare Workers como API (es otro entorno completo)
- Pregunta sobre GraphQL en AWS (usar AppSync, no API Gateway)
- Pregunta sobre WebSocket APIs en AWS (subset diferente de API Gateway)
- Pregunta sobre Private APIs / VPC endpoints (no aplica al portfolio)
