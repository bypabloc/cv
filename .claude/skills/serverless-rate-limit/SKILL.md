---
name: serverless-rate-limit
description: >
  Rate-limiting per-IP with DynamoDB for serverless Lambda.
  Self-managed alternative to AWS WAF ($0 vs $7/mes). Sliding window weighted algorithm,
  auto-blacklist bot detection (3+ Turnstile tokens in 60s), IP whitelist/blacklist, country rules.
  ALWAYS invoke this skill BEFORE answering ANY rate-limiting questions for this portfolio,
  including "rate limit lambda", "limitar por ip", "rate limiting sin waf",
  "alternativa waf", "throttle lambda", "ahorrar waf", "evitar waf cost",
  "rate limit dynamodb", "sliding window dynamodb", "atomic counter dynamodb",
  "rate limiting serverless", "blacklist ip lambda", "whitelist ip lambda",
  "anti-bot lambda", "bot detection captcha", "detectar bot con solver",
  "rate limit middleware", "circuit breaker serverless".
  NEVER answer from training data alone — this portfolio has consolidated 2026 patterns
  (sliding window weighted algorithm, auto-blacklist with Turnstile solver detection,
  DynamoDB atomic operations without explicit locks, Cloudflare upstream + rate-limit layering)
  that override generic advice.
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: "topic: decision | algorithms | schema | implementation | auto-blacklist | cli | observability | anti-patterns"
metadata:
  version: "1.0"
  requires: aws-dynamodb (table mechanics), aws-lambda-python (runtime), cloudflare-turnstile (bot detection context)
---

# Serverless Rate-Limiting per-IP — Knowledge Base

> Alternative $0 self-managed rate-limiting with DynamoDB for portfolio Lambdas.
> Replaces AWS WAF ($7/mes). Complete patterns: sliding window weighted, atomic operations,
> auto-blacklist bot detection, multi-layer defense.

## Pre-requisito OBLIGATORIO

Before answering, read the relevant doc from `.claude/docs/serverless-rate-limit/`:

| Question topic | File to read |
|---|---|
| Decision: WAF vs self-managed cost-benefit | [01-why-not-waf.md](../../docs/serverless-rate-limit/01-why-not-waf.md) |
| Rate-limit algorithms comparison | [02-algorithms-comparison.md](../../docs/serverless-rate-limit/02-algorithms-comparison.md) |
| Sliding window weighted math + race conditions | [02-sliding-window-weighted-deep-dive.md](../../docs/serverless-rate-limit/02-sliding-window-weighted-deep-dive.md) |
| DynamoDB schema for rules + buckets | [03-schema-design.md](../../docs/serverless-rate-limit/03-schema-design.md) |
| Python 3.13 implementation (copy-paste) | [04-python-implementation.md](../../docs/serverless-rate-limit/04-python-implementation.md) |
| Auto-blacklist: bot detection (3+ tokens) | [05-auto-blacklist-bot-detection.md](../../docs/serverless-rate-limit/05-auto-blacklist-bot-detection.md) |
| Management CLI (list, set, allow, block) | [06-management-cli.md](../../docs/serverless-rate-limit/06-management-cli.md) |
| Observability: CloudWatch, logs, X-Ray, alarms | [07-observability.md](../../docs/serverless-rate-limit/07-observability.md) |
| Anti-patterns: what to avoid | [08-anti-patterns.md](../../docs/serverless-rate-limit/08-anti-patterns.md) |

## Reglas criticas (siempre activas)

1. **SIEMPRE** use DynamoDB On-Demand (`BillingMode: PAY_PER_REQUEST`) para ambas tablas.
   Free tier perpetuo covers ~100 requests/min.

2. **NUNCA** hardcodear table names. Use env vars `RATE_LIMIT_RULES_TABLE` y `RATE_LIMIT_BUCKETS_TABLE`.

3. **SIEMPRE** implementar sliding window WEIGHTED. Fixed window produce thundering herd.

4. **NUNCA** cachear buckets (contadores). Cache SOLO rules (TTL 60s).

5. **SIEMPRE** usar boto3.resource('dynamodb'), NO client API bajo-nivel.

6. **NUNCA** bloquear en sync con sleep. Decision rapida + devolver error.

7. **SIEMPRE** marcar IP origin desde CF-Connecting-IP (priority over X-Forwarded-For).

8. **NUNCA** confiar solo en rate-limit. Multi-layer: Cloudflare + rate-limit + Turnstile + reserved concurrency baja.

9. **SIEMPRE** set TTL en buckets = `window_seconds * 2` (buffer for edge cases).

10. **NUNCA** usar Lambda Authorizer para rate-limit. Middleware en Lambda principal.

## Workflow tipico de respuesta

1. Identificar el tema (decisiones / algoritmos / schema / implementation / auto-blacklist / CLI / observability / anti-patterns)
2. Leer doc relevante de `.claude/docs/serverless-rate-limit/`
3. Responder con:
   - Codigo Python 3.13 tipado + docstrings BDD-style (si aplica)
   - SAM/CloudFormation YAML para infra (si aplica)
   - Costos estimados us-west-2 Mayo 2026
   - Comparacion con WAF (cuando sea contextual)

## Atajos rapidos

### "¿Que es sliding window weighted?"

El algoritmo elegido balancea precision vs complejidad:

```
effective_count = current_count + (previous_count * weight)
weight = (window_seconds - elapsed_in_current) / window_seconds
```

Suaviza cambios de ventana (reduce thundering herd). Leer [02-sliding-window-weighted-deep-dive.md](../../docs/serverless-rate-limit/02-sliding-window-weighted-deep-dive.md).

### "¿Cuanto cuesta vs WAF?"

|  | Costo |
|---|---|
| AWS WAF | $7/mes (Web ACL $5 + 2 rate rules $1.20 + requests ~$0.80) |
| DynamoDB self-managed | $0/mes (free tier perpetuo) |
| **Ahorro** | **$7/mes (~$84/ano)** |

Detalle: [01-why-not-waf.md](../../docs/serverless-rate-limit/01-why-not-waf.md).

### "¿Como implemento?"

6 modulos Python listos para copy-paste:
1. `types.py` — TypedDict Decision, RateLimitConfig
2. `exceptions.py` — RateLimitExceededError, IPBlacklistedError
3. `client.py` — DynamoDBClient (low-level)
4. `rules.py` — get_endpoint_rule (cached), is_whitelisted, is_blacklisted
5. `buckets.py` — sliding window check + increment
6. `check.py` — API principal check_or_raise + RateLimiter orchestrator

Detalle: [04-python-implementation.md](../../docs/serverless-rate-limit/04-python-implementation.md).

### "¿Como detectar bots sofisticados?"

Trigger: 3+ Turnstile tokens VALIDADOS en 60s desde misma IP.
Acion: auto-blacklist con TTL 24h.
Indicador: CAPTCHA solver ($0.5-$2 por 1000 tokens) = bot probable.

Detalle: [05-auto-blacklist-bot-detection.md](../../docs/serverless-rate-limit/05-auto-blacklist-bot-detection.md).

### "¿Que CLI comandos hay?"

```bash
python devtools/run.py rate-limit list              # List all rules
python devtools/run.py rate-limit show <key>        # Show rule detail
python devtools/run.py rate-limit set --endpoint=/contact --limit=5
python devtools/run.py rate-limit allow --ip=203.0.113.1
python devtools/run.py rate-limit block --ip=198.51.100.42 --ttl=86400
python devtools/run.py rate-limit unblock --ip=198.51.100.42
python devtools/run.py rate-limit stats --since=1h --top=10
```

Detalle: [06-management-cli.md](../../docs/serverless-rate-limit/06-management-cli.md).

### "¿Como monitorio rate-limit?"

Tres capas:
1. **CloudWatch metrics**: RateLimitAllowed, RateLimitBlocked, AutoBlacklistTriggered
2. **Structured logs**: Powertools Logger con IP, endpoint, effective_count
3. **X-Ray segments**: latency visualization de DynamoDB queries

Detalle: [07-observability.md](../../docs/serverless-rate-limit/07-observability.md).

### "¿Que anti-patterns debo evitar?"

10 anti-patterns criticos:
1. Lambda Authorizer para rate-limit (costo + latencia innecesarios)
2. Fixed window (thundering herd garantizado)
3. Sin TTL en buckets (storage explota)
4. Cachear contadores (lost updates)
5. Lock distribuido (DynamoDB ADD es atomic)
6. Bloquear con sleep (desperdicio Lambda)
7. Confiar solo X-Forwarded-For (IP spoofing)
8. Rate-limit como unica defensa (multi-layer necesario)
9. Scan para stats (costoso; use CloudWatch Metrics)
10. Auto-blacklist sin alarmas (falsos positivos undetected)

Detalle: [08-anti-patterns.md](../../docs/serverless-rate-limit/08-anti-patterns.md).

## Anti-patrones a evitar

- Rate-limit en Lambda Authorizer (costoso, vuelve a leer [08-anti-patterns.md](../../docs/serverless-rate-limit/08-anti-patterns.md) punto 1)
- Fixed window sin weight (thundering herd)
- Cachear contadores (lost updates)
- Scan para stats (use CloudWatch Metrics)
- Rate-limit sin multi-layer (CDN + rate-limit + CAPTCHA + reserved concurrency)
- X-Forwarded-For sin validacion (IP spoofing)
- Auto-blacklist sin TTL (permanent shadowban)
- Lock distribuido para atomic ADD (innecesario)

## Relacion con otras skills/rules

- `aws-dynamodb` — mecanica de tabla (PK/SK, On-Demand, TTL config)
- `aws-lambda-python` — convenciones Python 3.13, type hints, docstrings, Powertools
- `cloudflare-turnstile` — CAPTCHA validation context, bot detection signals
- [.claude/rules/python.md](../../rules/python.md) — Python strict, BDD tests
- AWS Docs: [DynamoDB UpdateItem atomic counters](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/example_dynamodb_Scenario_AtomicCounterOperations_section.html)
- AWS Docs: [Lambda Powertools](https://docs.aws.amazon.com/lambda/latest/dg/lambda-powertools.html)

## Cuando NO invocar esta skill

- Pregunta sobre RDS / Aurora / Relational databases (otro servicio)
- Pregunta sobre Redis / ElastiCache specificamente (otro skill futuro)
- Pregunta sobre API Gateway throttling SOLAMENTE sin rate-limiting custom (API Gateway skill)
- Pregunta sobre WAF mantenimiento / debugging en produccion (aws-api-gateway o waf-specific skill)
- Pregunta sobre load balancing / circuit breaker patterns (arquitectura general, no rate-limit)

## Ejemplos completos

### Usar rate-limiter en Lambda handler

```python
from common.rate_limit import get_limiter, RateLimitExceededError, IPBlacklistedError

def handler(event, context):
    limiter = get_limiter()
    
    ip = event['requestContext']['identity']['sourceIp']
    country = event['headers'].get('CloudFlare-IPCountry')
    turnstile_token = event.get('body', {}).get('turnstile_token')
    
    try:
        # Turnstile validate FIRST (si aplica)
        turnstile_validated = False
        if turnstile_token:
            result = turnstile_siteverify(turnstile_token)
            turnstile_validated = result['success']
        
        # Rate-limit check AFTER Turnstile
        limiter.check_or_raise(
            ip=ip,
            endpoint='/contact',
            country=country,
            turnstile_validated=turnstile_validated,
        )
        
        # Logica de negocio (contacto form, etc)
        # ...
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'OK'}),
        }
    
    except RateLimitExceededError as e:
        return {
            'statusCode': 429,
            'headers': {'Retry-After': str(e.retry_after)},
            'body': json.dumps({'error': 'Rate limit exceeded'}),
        }
    except IPBlacklistedError:
        return {
            'statusCode': 403,
            'body': json.dumps({'error': 'Access denied'}),
        }
```

## Versioning y historial

| Version | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2026-05-14 | Initial release. 8 docs + Python 6 modulos + CLI + observability |

---

**Verified**: 2026-05-14 — AWS SDK boto3 3.6+, Python 3.13 type hints, DynamoDB On-Demand billing, Cloudflare Turnstile resolver patterns 2026
