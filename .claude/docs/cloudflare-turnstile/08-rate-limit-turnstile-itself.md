# Rate limits y free tier de Turnstile

> Limites de la plataforma Turnstile, free tier, enterprise, y
> consideraciones de rate limit para siteverify API.

[← CSP/Multi-domain](./07-cors-multidomain.md) | [Siguiente: Alternativas →](./09-alternatives-comparison.md)

## Free plan

| Limite | Valor | Notas |
|--------|-------|-------|
| Widgets por account | 20 | Si necesitas mas, upgrade a Enterprise |
| Hostnames por widget | 10 | Cubre apex + 9 subdominios |
| Challenges mensuales | **Ilimitados** | Puedes hacer 1000 desafios/hora sin problema |
| Analytics retention | 7 dias | Mas viejo se borra |
| Support | Community | Cloudflare Community Forums |

### Para este portfolio

- Widgets needed: 1 (compartido en 6 apps)
- Hostnames needed: 6 (the-full-stack.com + 5 subdominios)
- Challenges/mes estimated: ~200 contactos + ~15,000 tracking pixels = 15,200
- **Estamos bien dentro del free tier** (mucho margen)

## Enterprise plan

| Limite | Valor | Notas |
|--------|-------|-------|
| Widgets por account | **Ilimitados** | Para grandes deployments |
| Hostnames por widget | 200 | Si tienes 100+ subdominios |
| Challenges mensuales | Ilimitados | Mismo que free |
| Analytics retention | 30 dias | Mas historico |
| Custom branding | Si | Remover badge de Cloudflare |
| Ephemeral IDs | Si | No persistencia de user tracking |
| Support | Dedicated | Account manager |
| Precio | $2,000/mes | Solo opcion entre free y $2k (no tier intermedio) |

**Para este portfolio:** Free plan es suficiente.

## Rate limiting de siteverify (no documentado publicamente)

Cloudflare NO documenta publicamente rate limits para siteverify, pero
basado en community reports y arquitectura tipica:

### Estimaciones

- **Limite blando:** ~1000 validaciones/minuto/account (undocumented)
- **Limite duro:** ~10,000 validaciones/minuto/account (estimado)
- **Ventana:** Por minuto (rolling)

**Comportamiento:** Si excedes, comenzaras a recibir:

```json
{
  "success": false,
  "error_codes": ["internal-error"]
}
```

(O posibles 429 Too Many Requests en el futuro)

### Para este portfolio

Portfolio tiene:

- ~200 contactos/mes = ~6/dia ≈ 0.004/segundo
- ~15,000 tracking pixels/mes = ~500/dia ≈ 0.006/segundo
- **Total: ~0.01/segundo = 600/minuto**

**Conclusion:** MUCHO margen incluso si suben 10x la traffic.

## Estimaciones de escalado

| Caso | Validaciones/mes | Validaciones/minuto pico | Rate limit concern? |
|------|------------------|-------------------------|---------------------|
| Este portfolio (actual) | 15,200 | ~0.5 | No |
| 10x traffic | 152,000 | ~5 | No |
| 100x traffic | 1,520,000 | ~50 | No |
| 1000x traffic | 15,200,000 | ~500 | Posible, contactar soporte |

## Monitoring rate limit

En Lambda, loguear:

```python
def check_rate_limit_health(
    error_code: str,
    error_count: int,
    time_window_minutes: int = 5,
) -> None:
    """Monitor para detectar rate limit problems."""
    if error_code == "internal-error":
        # Podria ser rate limit
        if error_count > 10:  # 10+ errores en 5 min
            logger.critical(
                f"Possible rate limit: {error_count} internal-errors "
                f"in {time_window_minutes}min"
            )
            # Alert: escalate to devops

        logger.warning(f"internal-error #{error_count}")
```

CloudWatch metrics:

```python
import boto3

cloudwatch = boto3.client("cloudwatch")

def log_turnstile_metric(success: bool, error_code: str | None = None):
    cloudwatch.put_metric_data(
        Namespace="Portfolio/Turnstile",
        MetricData=[
            {
                "MetricName": "ValidationAttempts",
                "Value": 1,
                "Unit": "Count",
                "Dimensions": [
                    {"Name": "Status", "Value": "success" if success else "failure"},
                    {"Name": "ErrorCode", "Value": error_code or "none"},
                ],
            }
        ],
    )
```

Dashboard en CloudWatch:

```
ValidationAttempts[Status=success] / ValidationAttempts[ErrorCode=internal-error]
```

Si `internal-error` rate sube de 0 a >1%, investigar.

## Estrategia si alcanzas limites (unlikely)

1. **Bajo rate limit:** Implementar caching/memoization de tokens
   (validar una sola vez, cachear resultado por 10 min)
   
2. **Medio rate limit:** Contactar Cloudflare soporte con metrics,
   pedir whitelist para account
   
3. **Alto rate limit:** Upgrade a Enterprise (pero $2,000/mes)

4. **Alternativa:** Migrar a ALTCHA o FriendlyCaptcha (PoW-based,
   sin servidor externo para validar)

## Free tier pricing drop

En Sept 2022, Cloudflare anuncio que Turnstile es gratis **para todos**.
No hay deprecation plan para free tier. Considerar que:

- Free tier es "good enough" indefinidamente
- Enterprise es para casos edge (1000+ subdominios, custom branding)
- Portfolio debe quedarse en Free (20 widgets, 10 hostnames = plenty)
