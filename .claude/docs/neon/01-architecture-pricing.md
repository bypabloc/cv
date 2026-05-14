# Arquitectura y Pricing de Neon 2026

> Que es Neon, como funciona scale-to-zero, y planes 2026 comparados.
> Verificado 2026-05-14 via neon.com/pricing.

## Que es Neon (arquitectura 10.000 pies)

Neon es **PostgreSQL serverless**: separacion de compute y storage via arquitectura custom.

- **Storage layer**: multi-tenant, COW (copy-on-write), soporta time-travel queries
- **Compute layer**: PostgreSQL estandar (PG14-PG18), efimero, scale-up/down bajo demanda
- **Control plane**: API Neon para crear branches, modificar compute, recuperar snapshots

### Diferencia clave vs RDS / self-hosted

```
Traditional PostgreSQL:       Neon:
┌─────────────────────┐      ┌──────────────────────────────┐
│ Compute + Storage   │      │ Ephemeral Compute (PostgreSQL)│
│  (acoplado, caro)   │      │          +                    │
└─────────────────────┘      │ Persistent Shared Storage     │
                             │  (multi-tenant, copy-on-write)│
                             └──────────────────────────────┘
```

Ventaja: compute desaparece cuando no se usa (scale-to-zero). Storage persiste. Costo minimo en idle.

## Scale-to-zero (autosuspend)

Neon suspende compute automaticamente despues de **5 minutos inactivity**:

- **Suspended**: no consume CU-hours, ~200-500ms resume time, data intacta
- **Active**: consume CU-hours, queries corren en vivo
- Resume es transparente: conexion se reconnecta automaticamente

Para este portfolio:
- 95% del tiempo suspendido (sin costo)
- 5% tiempo activo (consumo CU-hours)
- **Calculo**: 100 CU-hours/mes ÷ 730 horas = ~0.137 CU-hours media. Bajo.

## Planes 2026 (pricing post-Databricks Q2 2025)

| Aspecto | Free | Launch | Scale |
|--------|------|--------|-------|
| **Costo** | $0 | $0.106/CU-h | $0.222/CU-h |
| **Storage** | 0.5 GB | $0.35/GB-mes | $0.35/GB-mes |
| **Compute** | 0.25-2 CU (100 CU-h/mes) | autoscale 0-16 CU | fixed 0-56 CU |
| **Transfer** | 5 GB/mes | 100 GB/mes | 500 GB/mes |
| **Branches** | 10 | 10 | unlimited |
| **Retention** | 7 dias | 7 dias | 30 dias |
| **Cron jobs** | ❌ | 1 | 5 |
| **IP allowlist** | ❌ | ❌ | ✓ |
| **Private networking** | ❌ | ❌ | ✓ + $0.01/GB |
| **HIPAA/SOC2** | ❌ | ❌ | ✓ |
| **Support** | community | standard | priority |

### Detalles Free tier

- **100 CU-hours/mes**: si usas 1 CU (full compute 2.0), son ~100 horas/mes activas
- **0.5 GB storage**: para 200 contacts + 15k events/mes ~ 50-100 MB. OK.
- **5 GB transfer/mes**: tracking events + CRM queries. OK.
- **10 branches**: suficiente para 10 features en paralelo
- **Scale-to-zero**: suspends after 5 min inactivity (no costo)
- **No expira**: free tier es perpetuo (cambio post-Databricks 2025)

### Ejemplo de costo real

Portfolio con stats actuales:

```
Volumen:
- 200 contacts/mes
- 15,000 tracking events/mes
- 3 Lambda handlers (100ms cada uno, 5 requests/dia)

Calculo aproximado:
- Handler 1 (DynamoDB processor): 5 req/dia * 30 dias * 100ms = 15k ms = 4 seg/mes
- Handler 2 (tracking events): 5 req/dia * 30 dias * 50ms = 2 seg/mes
- Handler 3 (analytics query): 1 req/dia * 30 dias * 200ms = 6 seg/mes
- Total: ~12 seg/mes = 0.0033 CU-hours/mes

CU-hours budget 100/mes >> 0.0033 usado → FREE TIER FOREVER
```

## Regiones disponibles 2026

Neon soporta (principal en us-east-1, Oregon para este portfolio):

| Region | AWS equiv | Neon name | Disponibilidad |
|--------|-----------|-----------|----------------|
| us-east-1 | Oregon | us-east-1 | ✓ (recomendado) |
| us-east-1 | N. Virginia | us-east-1 | ✓ |
| us-east-2 | Ohio | us-east-2 | ✓ |
| eu-west-1 | Ireland | eu-west-1 | ✓ |
| ap-southeast-1 | Singapore | ap-southeast-1 | ✓ |
| azure-eastus2 | ❌ deprecated | — | ❌ migrar antes Aug 2026 |

Portfolio esta en us-east-1 (Lambdas) → Neon us-east-1 (mismo region, min latency).

## PostgreSQL version support

Neon soporta PG14-18. Status 2026-05-14:

- **PG18**: GA (septiembre 2025). Asynchronous I/O enabled. 2-3x perf gain en algunos casos.
- **PG17**: GA. No mas cambios.
- **PG16**: GA. Estable.
- **PG15, PG14**: GA. Legacy pero soportados.

Recomendacion: usar **PG18** (nuevo, performance + features, fully GA en 2026).

## Databricks ownership (May 2025)

Cambio importante:

- **Adquisicion**: Databricks compro Neon por ~$1 billion (May 2025)
- **Pricing impact**: compute drop 15-25%, storage drop 80% ($1.75 → $0.35/GB)
- **Free tier**: duplico CU-hours (50 → 100)
- **Future**: potencial integracion con Databricks Lakehouse (aun TBD)

**Conclusion**: post-Databricks pricing es aun mas competitivo.

## Performance baselines

Cold start Lambda con psycopg3:

- **Init (module scope)**: ~150-250ms primera ejecucion
- **Connect (pooled)**: ~10-30ms warm
- **Suspended resume**: ~200-500ms (transparente)
- **Query execution**: estandar Postgres (typically <50ms para queries simples)

Para este portfolio, idle 95% del tiempo, asi que mostly re-resuming (200-500ms cada 5 min, acceptable).

## Summary para este proyecto

✓ Free tier indefinido (cambio post-Databricks)
✓ us-east-1 disponible
✓ PG18 GA + asynchronous I/O
✓ Scale-to-zero ahorra costo en idle
✓ Branching para testing (10 branches incluidas)
✗ NUNCA pagara nada para este volumen (Free tier)

Siguiente: ver Lambda + psycopg3 integration.

## Referencias

- [Neon Pricing Official](https://neon.com/pricing)
- [Plans Documentation](https://neon.com/docs/introduction/plans)
- [Regions Documentation](https://neon.com/docs/introduction/regions)
- [PG18 Features](https://neon.com/postgresql/18-new-features)
- [Databricks Acquisition News](https://neon.com/blog/neon-databricks)
