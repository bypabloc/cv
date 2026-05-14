---
title: Decision - WAF vs DynamoDB self-managed rate-limiting
description: Por que NO usar AWS WAF para rate-limiting en el portfolio. Comparacion detallada de costos, control, defensa, y latencia.
status: stable
last-reviewed: 2026-05-14
---

# 01. Decision: WAF vs DynamoDB self-managed

> Por que decidimos reemplazar AWS WAF ($7/mes) con rate-limiting self-managed
> en DynamoDB ($0/mes). Comparacion tecnica y de costo.

[README](./README.md) | [Siguiente: Algoritmos →](./02-algorithms-comparison.md)

## Contexto de la decision

Portfolio personal de Pablo Contreras con 5 Lambdas Python 3.13 en us-west-2:
- `contact_form`: contacto del site
- `tracking_pixel`: analittica
- `turnstile_validator`: validacion de tokens CAPTCHA
- `stream_processor`: procesamiento async
- `aggregator`: agregacion de datos

**Anterior arquitectura**: API Gateway + AWS WAF con 2 rate-based rules = $7/mes.

**Nueva arquitectura**: API Gateway + DynamoDB self-managed rate-limit middleware = $0/mes.

## Opcion 1: AWS WAF (lo que reemplazamos)

### Ventajas WAF

| Ventaja | Explicacion |
|---------|-------------|
| **Defensa en la edge** | WAF rechaza requests antes de llegar a Lambda. Ahorra invocaciones. |
| **Managed service** | AWS gestiona availability, patching, escala. Zero operational burden. |
| **Reglas OWASP predefinidas** | Proteccion contra SQL injection, XSS, travesial, etc. |
| **10M requests/mes gratis** (aprox) | Bajo volumen es cheaper que pagar por invocaciones Lambda extra. |
| **IP tracking >10k** | WAF puede trackear >10k IPs simultaneamente sin degradacion. |
| **Soporte regulatorio** | Algunos compliance frameworks requieren WAF (PCI-DSS nivel estricto). |

### Desventajas WAF para este caso

| Desventaja | Impacto |
|-----------|--------|
| **Costo fijo $5/mes** | Web ACL cuesta $5, + $1.20 por rate rule (2 rules = $7 total). Para portfolio con bajo volumen, es desperdicio. |
| **Reglas rigidas** | No puedes cambiar limites sin re-deploying stack. Custom logic limitada. |
| **No ve logica de negocio** | WAF no sabe si token Turnstile fue validado. No puede auto-blacklist bots sofisticados. |
| **5 minutos ventana fija** | Los rate limits se aplican en ventanas de 5 min. No hay granularidad menor. |
| **Minimo 10 req/5min** | No podes limitar por debajo de 0.033 req/s (10 req en 5 min). |
| **IP spoofing posible** | Si confias en X-Forwarded-For sin validacion, atacantes pueden spoof IPs. |
| **Scope-down complexity** | Custom logic dentro de WAF requiere statement trees complejos (JSON nesting profundo). |

### Costo desglosado WAF

```
Web ACL:                     $5.00/mes
Rate-based rule #1:          $1.00/mes
Rate-based rule #2:          $0.20/mes
Requests (10M @ $0.60/M):    $6.00/mes  (aprox, bajo volumen)
---
Total:                       $12.20/mes (case pesimista)
Minimo realista:             $7.00/mes  (si <1M requests)
```

**Para este portfolio**: Bajo volumen (~100 req/min = 150k/mes),
costo es principalmente el $5 ACL fijo.

## Opcion 2: API Gateway throttling (rechazado)

API Gateway nativo permite throttle global:
- `ThrottleSettings: RateLimit=3 per-method` → **pero aplica a TODAS las IPs juntas**.

No hay forma de limitar **per-IP** en API Gateway solo.

Por eso WAF fue la opcion historica (o construir custom en Lambda).

## Opcion 3: DynamoDB self-managed (ELEGIDA)

### Ventajas

| Ventaja | Explicacion |
|---------|-------------|
| **Costo $0** | Free tier DynamoDB perpetuo: 25 GB + 25 RCU + 25 WCU = gratis siempre. |
| **Control total** | Logica 100% custom: whitelist, blacklist, auto-blacklist, country rules, etc. |
| **Entiende negocio** | Rate-limit DESPUES de Turnstile check. Puede auto-blacklist bots. |
| **Latencia rapida** | DynamoDB ~10-20ms warm Lambda. Comparable a WAF. |
| **Granularidad minuto** | Puedes limitar a 1 req/min si quieres. Sliding window, no ventanas fijas. |
| **Escalable perpetuo** | On-Demand significa: baja volumen = $0, volumen alto = paga por lo que usa (sin WAF overscaling). |
| **Sin costo fijo** | Cero overhead si el site esta down o trafico cae. |

### Desventajas

| Desventaja | Mitigacion |
|-----------|-----------|
| **Defensa en Lambda** | Lambda siempre se invoca (costo). Pero: free tier Lambda (1M/mes gratis) cubre esto. |
| **DDoS sostenido >10k req/s** | DynamoDB On-Demand se satura. Solucion: reactive WAF o escalar con write sharding. |
| **Espacio de nombres global** | Si buckets key-name colisiona entre Lambdas, puede haber race. Mitigacion: prefijos claros. |
| **Operational overhead** | Mantienes codigo, monitoreo, debugging. AWS no lo cuida. Pero: codigo completo en this knowledge base. |
| **TTL eventual** | Items del bucket NO se borran exactamente al vencer. Pueden quedar 48h. Storage crece. Pero: DynamoDB On-Demand no cobra storage si <25GB. |

### Costo desglosado (self-managed)

```
DynamoDB reads (rules fetch ~1/invocacion):  ~100k/mes @ $0.25/M = $0.025/mes
DynamoDB writes (bucket increment):           ~100k/mes @ $1.25/M = $0.125/mes
DynamoDB storage (100 MB buckets vivos):      <25 GB (free tier)
CloudWatch logs (structured):                 ~5 GB/mes @ $0.50/GB = $2.50/mes
Lambda invocations (rate-limit check):        ~100k/mes (included in Lambda free tier 1M/mes)
---
Total:                                        ~$2.65/mes (realista)
Con free tier TTL + storage:                  ~$0/mes (si logs minimales)
```

**Ahorro vs WAF**: $7 - $0 = **$7/mes** (~84 USD/ano).

## Decision matrix (para otros casos)

Si tu portfolio / API es:

| Caso | Recomendacion |
|------|---|
| **Personal portfolio, <1k req/dia, costo es prioridad** | DynamoDB self-managed (este patrón) ✓ |
| **Produccion, compliance regulatorio, 100k+ req/dia** | WAF + DynamoDB (multi-layer) |
| **API publica masiva >1M req/dia, DDoS target** | WAF + Shield Advanced + DynamoDB |
| **Prototype, no hay defensa activa** | API Gateway throttle solo (muy debil) |
| **Fintech/Pagos, PCI DSS** | WAF obligatorio (compliance) |

## Comparacion side-by-side

| Caracteristica | WAF | Self-managed DynamoDB |
|---|---|---|
| **Costo mensual** | $7-12 | $0-3 |
| **Defensa ubicacion** | Edge (Cloudflare → WAF → Lambda) | En Lambda (despues de Cloudflare) |
| **Invocaciones Lambda pagadas** | Menos (WAF rechaza antes) | Mas (siempre se invoca) |
| **Control de reglas** | Limitado (scope-down statements) | Completo (codigo Python) |
| **Auto-blacklist bots** | No (no ve Turnstile) | Si (3+ tokens = blacklist 24h) |
| **Whitelist/Blacklist manual** | Posible (IP set referencias) | Facil (DynamoDB items) |
| **Country-based block** | Si (via GeoIP) | Si (CF-IPCountry header) |
| **Latencia rate-check** | ~10ms | ~10-20ms |
| **Granularidad ventana** | 5 min fijo | Configurable (60s, 300s, etc.) |
| **Max IPs trackeadas** | 10k simultaneous | Ilimitadas (On-Demand) |
| **Escala DDoS >10k req/s** | Excelente | Degradacion posible |
| **Compliance WAF-explicit** | Cumple (algunos frameworks) | No (requiere justificacion) |
| **Operacional burden** | Bajo (managed) | Medio (codigo custom) |

## Conclusion

**Para este portfolio**: DynamoDB self-managed es la opcion correcta porque:

1. **Costo**: $7 es justificable, pero $0 es mejor para proyecto personal.
2. **Control**: Necesitamos auto-blacklist bots (requiere logica custom).
3. **Volumen bajo**: Free tier DynamoDB cubre perpetuo.
4. **Cloudflare upstream**: CDN gratis ya cubre defensa edge basica.
5. **Flexibility**: Si trafico crece, podemos agregar WAF sin remover self-managed.

**Riesgo aceptado**: Si trafico crece >10k req/s, reactivar WAF. Pero hoy eso es improbable.

---

**Verificado a**: 2026-05-14 (AWS WAF pricing, DynamoDB On-Demand free tier perpetuo confirmados en console AWS)
