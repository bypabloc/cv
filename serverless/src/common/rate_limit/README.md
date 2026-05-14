# common.rate_limit - Sliding window weighted per-IP

> Alternativa `$0/mes` a AWS WAF Web ACL (`$7/mes`). Self-managed con
> DynamoDB. Patron consolidado en `.claude/docs/serverless-rate-limit/`.

## Quick start

```python
from common.rate_limit import check_or_raise
from common.ip_extractor import extract_ip, extract_country

def lambda_handler(event, context):
    ip = extract_ip(event)
    country = extract_country(event)

    # Levanta IPBlacklistedError, CountryBlockedError o RateLimitExceededError
    check_or_raise(
        ip=ip,
        endpoint='/contact',
        country=country,
        turnstile_validated=False,
    )

    # ... resto del handler
```

## Algoritmo sliding window weighted

Para una window de N segundos:

```
effective_count = current_bucket.count + previous_bucket.count * (1 - elapsed_fraction)

donde:
  elapsed_fraction = (now - current_window_start) / N
```

Esto evita el bug del fixed window:
- 10 req en los ultimos 30s del bucket 1 + 10 req en los primeros 30s del bucket 2 = 20 req en 60s real, pero con fixed window cuenta como "10 cada uno".
- Con sliding window weighted, justo en la transicion, los 20 cuentan correctamente.

## Tablas (SAM template)

### `portfolio-rate-limit-rules-{stage}`

| Key | Tipo | Notas |
|-----|------|-------|
| `rule_key` | S (PK) | `endpoint#/contact` \| `ip#1.2.3.4` \| `country#CN` |
| `kind` | S (SK) | `endpoint` \| `ip_whitelist` \| `ip_blacklist` \| `country` |
| `limit` | N | requests max por window |
| `window_seconds` | N | longitud de la ventana |
| `action` | S | `throttle` \| `block` |
| `expires_at` | N (TTL) | Unix epoch; auto-borrar (para auto-blacklist con TTL) |
| `reason` | S | texto humano |
| `metadata` | M | context opcional (auto_created, etc.) |

### `portfolio-rate-limit-buckets-{stage}`

| Key | Tipo | Notas |
|-----|------|-------|
| `bucket_key` | S (PK) | `ip#1.2.3.4#endpoint#/contact#window#1715000000` |
| `count` | N | atomic ADD :inc |
| `turnstile_tokens` | N | counter separado para auto-blacklist |
| `expires_at` | N (TTL) | `window_start + window_seconds * 2` (mantener prev) |

## Reglas iniciales (cargar post-deploy)

```bash
serverless rate-limit set --endpoint=/contact --limit=3 --window=300 --action=throttle
serverless rate-limit set --endpoint=/track --limit=30 --window=300 --action=throttle
serverless rate-limit set --endpoint=/validate-turnstile --limit=5 --window=60 --action=throttle
```

## Auto-blacklist por bot detection

Si una IP genera 3+ tokens Turnstile validos en 60s, asumimos Turnstile
solver (bot). Crear rule ip_blacklist con TTL 24h.

```python
# Dentro del flow:
bucket = increment_bucket(..., turnstile_validated=True)
if should_auto_blacklist(bucket['turnstile_tokens']):
    create_blacklist_rule(ip)  # TTL 24h
```

## Cache de rules

Las rules se cachean con `@cached(ttl=60, stale_for=300, tags=['rate-limit-rules'])`.
Para invalidar manualmente despues de cambiar una rule:

```python
from common.cache import DynamoDBCache

cache = DynamoDBCache()
cache.invalidate(tag='rate-limit-rules')
```

## NUNCA cachear buckets

Los buckets DEBEN ser fresh: si cache stale, podriamos permitir mas
requests del limite real (race condition logica). Solo `get_item` directo.

## Trade-off vs AWS WAF

| Aspecto | Con WAF | Sin WAF (este) |
|---------|---------|----------------|
| Costo | `$7/mes` | `$0` |
| Latencia agregada | `<5ms` (edge) | `~10-20ms` (warm, 2 GetItem + 1 UpdateItem) |
| Defense edge (rechaza antes de Lambda) | Si | No (siempre invoca, mitigado por reserved concurrency) |
| Algoritmo | fixed window | sliding window weighted |
| Auto-blacklist | No | Si (3+ tokens en 60s) |
| Country rules dinamicas | manual | YAML/CLI |
| OWASP managed rules | bundle gratis | No (mitigado por Turnstile + JSON Schema) |
