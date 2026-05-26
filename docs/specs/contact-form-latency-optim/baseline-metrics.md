# Baseline metrics — pre-deploy

Capturado: **2026-05-26 ~18:20 UTC** (post-PR #150-152, pre-deploy del plan latency-optim).

## Smokes capturados

### dev path completo (con bypass Turnstile -> 202)

5 smokes secuenciales:

| Inv | curl time_total | HTTP |
|-----|-----------------|------|
| 1 | 6.241s | 202 |
| 2 | 0.466s | 202 |
| 3 | 0.507s | 202 |
| 4 | 0.480s | 202 |
| 5 | 0.473s | 202 |

- **Cold start p50**: ~6.24s end-to-end (curl)
- **Warm path p50**: ~480ms end-to-end (curl)

### prod path rechazo Turnstile (sin bypass disponible -> 403)

| Inv | curl time_total | HTTP |
|-----|-----------------|------|
| 1 | 5.751s | 403 |
| 2 | 0.408s | 403 |
| 3 | 0.406s | 403 |
| 4 | 0.428s | 403 |
| 5 | 0.420s | 403 |

- **Cold start p50**: ~5.75s end-to-end (curl)
- **Warm path p50**: ~420ms (rechazo rapido en captcha — no entra al execute completo)

## CloudWatch REPORT entries

### dev (durante baseline)

```
Cold: RESTORE_REPORT Restore Duration: 449.89 ms
      REPORT Duration: 5139.08 ms / Billed Duration: 5182 ms
Warm: Duration 134-162 ms
```

### prod (durante baseline)

```
Cold: RESTORE_REPORT Restore Duration: 368.19 ms
      REPORT Duration: 4771.76 ms / Billed Duration: 4834 ms
Warm: Duration 89-98 ms (rechazo rapido por captcha)
```

### stage (datos cache previo, low traffic)

```
Cold: RESTORE_REPORT Restore Duration: 282.12 ms
      REPORT Duration: 5877.67 ms / Billed Duration: 5911 ms
```

## Composicion del cold start (de logs detallados, post PR #146-149)

Tomando como referencia el reporte del usuario hoy (06:30 UTC pre-baseline):

| Fase | dev | prod |
|------|-----|------|
| RESTORE (SnapStart) | 484-1113 ms | 265-1113 ms |
| PRELOAD | 0-51 ms | 0-51 ms |
| VALIDATE (Turnstile HTTP) | 459-513 ms | 459-513 ms |
| EXECUTE (rate_limit 4 DDB + SQS + auto_blacklist) | 2051-3582 ms | 2051-3582 ms |
| **Total** | **~5460-8755 ms** | **~5460-8755 ms** |

## Target post-deploy

| Metrica | Baseline | Target post-deploy | Speedup esperado |
|---------|----------|---------------------|------------------|
| Cold total | ~5500-6240 ms | <= 4400 ms | -20% minimo |
| Warm path (con bypass dev) | ~480 ms | <= 336 ms | -30% minimo |
| EXECUTE phase | ~2050-3580 ms | <= 1400 ms | -50% por paralelizacion |

El gate del commit 10 requiere alcanzar estos targets en al menos 2 de 3
envs (acceptable variabilidad en low-traffic prod).
