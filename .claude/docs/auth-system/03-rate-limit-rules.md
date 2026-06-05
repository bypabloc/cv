# Reglas de rate-limit del Lambda `auth`

> Seed manual via `serverless rate-limit set` 1 vez por stage. Reusa
> `shared.rate_limit` (sliding window weighted) + tabla
> `portfolio-rate-limit-rules-${stage}`.

## Endpoint key

Formato: `<operation>.<action>` literal. El controller llama
`shared.rate_limit.check_or_raise(endpoint=f'{operation}.{action}')`.
Matching exacto (NO prefix). Cada operation.action tiene su key propia.

## Tabla de reglas activas

| Endpoint | Limit | Window | Hard cap | Hard-cap action | Justificacion |
|---|---|---|---|---|---|
| `login.check-email` | 3 | 3600s | 10/h | blacklist-24h | Unico punto con Turnstile; anti spam masivo de altas |
| `login.start` | 5 | 60s | 20/min | blacklist-1h | Anti brute force email enumeration |
| `login.verify-magic-link` | 10 | 60s | — | — | Generoso (un user normal hace 1) |
| `login.verify-code` | 10 | 60s | — | — | Idem |
| `verify.set-password` | 5 | 60s | — | — | Operacion sensible |
| `verify.resend-code` | 3 | 300s | — | — | Anti-spam de emails (5 min ventana) |
| `session.refresh` | 30 | 60s | — | — | Token rotation frecuente OK |
| `session.logout` | 30 | 60s | — | — | Idem |

## Throttle adicional aplicado en el controller

Independiente del rate-limit por IP:

- `verify.resend-code`: 60s desde la ultima emision PARA EL MISMO user
  (AC-21). Si NO paso, devuelve `429 RESEND_THROTTLED`.

## Comandos seed (1 vez por stage)

```bash
# dev
python devtools/run.py serverless rate-limit set --stage=dev \
  --endpoint='login.check-email' --limit=3 --window=3600 \
  --hard-cap=10 --hard-cap-action=blacklist-24h --aws-profile=tfs-dev
python devtools/run.py serverless rate-limit set --stage=dev \
  --endpoint='login.start' --limit=5 --window=60 \
  --hard-cap=20 --hard-cap-action=blacklist-1h --aws-profile=tfs-dev
python devtools/run.py serverless rate-limit set --stage=dev \
  --endpoint='login.verify-magic-link' --limit=10 --window=60 --aws-profile=tfs-dev
python devtools/run.py serverless rate-limit set --stage=dev \
  --endpoint='login.verify-code' --limit=10 --window=60 --aws-profile=tfs-dev
python devtools/run.py serverless rate-limit set --stage=dev \
  --endpoint='verify.set-password' --limit=5 --window=60 --aws-profile=tfs-dev
python devtools/run.py serverless rate-limit set --stage=dev \
  --endpoint='verify.resend-code' --limit=3 --window=300 --aws-profile=tfs-dev
python devtools/run.py serverless rate-limit set --stage=dev \
  --endpoint='session.refresh' --limit=30 --window=60 --aws-profile=tfs-dev
python devtools/run.py serverless rate-limit set --stage=dev \
  --endpoint='session.logout' --limit=30 --window=60 --aws-profile=tfs-dev

# Repetir 1 a 1 con --stage=stage y --stage=prod
```

Idempotente: ejecutar de nuevo sobrescribe los valores.

Verificar:

```bash
python devtools/run.py serverless rate-limit list --stage=dev
# debe mostrar las 8 reglas
```

## Response al exceder

```jsonc
HTTP/1.1 429 Too Many Requests
{
  "error": "RATE_LIMITED",
  "retry_after": 42        // segundos hasta que el window se libere
}
```

El header `Retry-After: 42` tambien se setea para clientes que lo
respeten.
