---
title: Rate-Limiting per-IP con DynamoDB en Serverless Lambda
description: Alternativa de costo cero a AWS WAF para el portfolio. Implementacion self-managed con DynamoDB On-Demand + algoritmo sliding window weighted.
status: stable
last-reviewed: 2026-05-14
---

# Rate-Limiting per-IP con DynamoDB en Serverless Lambda

> Patron completo de rate-limiting per-IP implementado con DynamoDB On-Demand
> en 5 Lambdas Python 3.13 del backend del portfolio. Alternativa $0 a AWS WAF
> ($7/mes). Costo: gratis perpetuo (free tier DynamoDB), defensa en Lambda.

## Contexto del portfolio

- **Stack**: 5 Lambdas Python 3.13 arm64 en us-west-2 (contact_form, tracking_pixel, turnstile_validator, stream_processor, aggregator)
- **Upstream CDN**: Cloudflare Pages (gratis, defensa edge basica)
- **Antes**: AWS WAF con rate-based rules = $7/mes
- **Ahora**: Rate-limit self-managed con DynamoDB = $0/mes
- **Trigger**: Ahorrar costo WAF sin sacrificar defensa robusta
- **Alcance**: Limitar por IP + endpoint + pais + auto-blacklist bots

## Tabla de contenidos

| Capitulo | Tema | Cuando leer |
|----------|------|-----------|
| [01-why-not-waf.md](./01-why-not-waf.md) | Decision: WAF vs self-managed | Si dudas si reemplazar WAF con DynamoDB |
| [02-algorithms-comparison.md](./02-algorithms-comparison.md) | Algoritmos: fixed window, sliding window log, **sliding window weighted**, token bucket, leaky bucket | Antes de elegir algoritmo |
| [02-sliding-window-weighted-deep-dive.md](./02-sliding-window-weighted-deep-dive.md) | Deep dive del algoritmo recomendado: math, race conditions, edge cases | Antes de implementar check |
| [03-schema-design.md](./03-schema-design.md) | Schema de las 2 tablas: `rate_limit_rules` y `rate_limit_buckets` | Antes de crear infra (SAM template incluido) |
| [04-python-implementation.md](./04-python-implementation.md) | Codigo Python COMPLETO: check.py, rules.py, buckets.py, auto_blacklist.py, exceptions.py | Para copy-paste a `serverless/src/common/rate_limit/` |
| [05-auto-blacklist-bot-detection.md](./05-auto-blacklist-bot-detection.md) | Auto-blacklist: deteccion de bots con 3+ tokens Turnstile validos en 60s | Antes de habilitar auto-blacklist |
| [06-management-cli.md](./06-management-cli.md) | CLI para gestionar reglas (list, set, allow, block, unblock, stats) | Para integrar en devtools |
| [07-observability.md](./07-observability.md) | CloudWatch metrics, structured logs, X-Ray, dashboards, alarms | Antes de deploy a produccion |
| [08-anti-patterns.md](./08-anti-patterns.md) | Anti-patterns evitados (Lambda Authorizer, fixed window, sin TTL, etc.) | Para entender la arquitectura |

## Comparacion rapida: $7/mes WAF vs $0 self-managed

| Aspecto | AWS WAF | DynamoDB self-managed | Ganador |
|---------|---------|----------------------|---------|
| **Costo** | $7/mes (Web ACL $5 + 2 rules $1.20 + requests ~$0.80) | $0/mes (free tier perpetuo) | DynamoDB ✓ |
| **Defensa** | Edge (rechaza antes de Lambda) | En Lambda (paga invocacion siempre) | WAF ✓ |
| **Control** | Managed rules OWASP predefinidas | Control total del algoritmo | DynamoDB ✓ |
| **Latencia** | ~10ms WAF check | ~10-20ms (warm Lambda) | Similar |
| **Personalizacion** | Limitada (scope-down statements) | Completa (whitelist, blacklist, pais, auto-blacklist) | DynamoDB ✓ |
| **Escalabilidad** | Infinita (managed) | Free tier DynamoDB (25 GB storage, ilimitado RCU/WCU On-Demand) | WAF ✓ |
| **Cuando gana WAF** | DDoS sostenido >10k req/s, compliance regulatorio, scale masivo | — | — |
| **Cuando gana self-managed** | Portfolio personal, costo cero objetivo, Cloudflare upstream | ✓ | ✓ |

## Reglas criticas (siempre activas)

1. **SIEMPRE** usar DynamoDB On-Demand (`BillingMode: PAY_PER_REQUEST`) para ambas tablas.
   Volumen bajo + spiky = free tier perpetuo.

2. **NUNCA** hardcodear table names. Usar env vars `RATE_LIMIT_RULES_TABLE` y `RATE_LIMIT_BUCKETS_TABLE`.

3. **SIEMPRE** implementar sliding window WEIGHTED. Fixed window produce thundering herd.

4. **NUNCA** cachear el contador (buckets). Cache SOLO las rules (TTL 60s).

5. **SIEMPRE** usar boto3.resource('dynamodb'), NO client API bajo-nivel.

6. **NUNCA** bloquear en sync con sleep. Decision rapida + devolver error si lock no adquirido.

7. **SIEMPRE** marcar IP origin desde CF-Connecting-IP (prioridad sobre X-Forwarded-For).

8. **NUNCA** confiar solo en rate-limit. Siempre: Turnstile PRIMERO, rate-limit DESPUES, reserved concurrency BAJO.

9. **SIEMPRE** habilitar auto-blacklist solo si Cloudflare upstream activo. Evita falsos positivos.

10. **NUNCA** exponenciar metricas internas a logs publicos (leakear patrones de ataque).

## Flujo de una request (orden CRITICO)

```
1. Request llega a Cloudflare Pages
2. Cloudflare mitiga DDoS basico (gratis)
3. Request a Lambda via API Gateway
4. Lambda middleware:
   a) Extraer IP desde CF-Connecting-IP (o X-Forwarded-For fallback)
   b) Obtener reglas para endpoint (cached 60s)
   c) Chequear IP whitelist (permitir)
   d) Chequear IP blacklist (bloquear)
   e) Chequear country rules (bloquear si necesario)
   f) Chequear rate-limit sliding window weighted (allow/throttle)
   g) Si Turnstile required: verificar + (si valido) increment turnstile counter
   h) Si 3+ tokens validos en 60s: auto-blacklist esta IP 24h
5. Si todas las checks pasan: handler ejecuta logica de negocio
```

## Costo real (Mayo 2026)

Para ~100 requests/min (10k/dia) con rate-limit ON-DEMAND:

- **DynamoDB reads** (rules fetch + bucket get): ~15k/dia @ $0.25/M = ~$0.004/dia
- **DynamoDB writes** (bucket increment): ~10k/dia @ $1.25/M = ~$0.013/dia
- **DynamoDB storage**: ~100 MB buckets vivos @ free tier = $0
- **TTL deletion**: gratis
- **Total**: ~$0.5/mes (en free tier perpetuo)

**Comparacion con WAF**: Ahorro $6.50/mes + control total.

## Cuando REACTIVAR WAF

Si observas:
- DDoS sostenido >10k req/s (DynamoDB On-Demand se satura)
- Requerimiento regulatorio de WAF (compliance)
- Hotspot en una sola IP que rompe partition key (write sharding necesario)

→ Vuelve a WAF. Este patron es para portfolios personales + bajo volumen.

## Navegacion

Empezar por [01-why-not-waf.md](./01-why-not-waf.md) para entender la decision.

Luego leer [02-algorithms-comparison.md](./02-algorithms-comparison.md) + [02-sliding-window-weighted-deep-dive.md](./02-sliding-window-weighted-deep-dive.md).

Implementacion: [03-schema-design.md](./03-schema-design.md) → [04-python-implementation.md](./04-python-implementation.md) → [07-observability.md](./07-observability.md).

---

**Verificado a**: 2026-05-14
**Fuentes**: AWS docs (DynamoDB UpdateItem atomic), lifeomic rate-limiter, Arpit Bhayani sliding window blog, AWS database blog resource counters
