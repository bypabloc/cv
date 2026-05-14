# Neon Serverless PostgreSQL

> Guia pragmatica para usar Neon como base de datos para el portfolio.
> Serverless PostgreSQL con scale-to-zero, branching git-style, y PG18 compatible.
> Verificado 2026-05-14.

## Indice

| Tema | Cuando leer |
|------|------------|
| Quick start + pricing | Antes de crear proyecto Neon |
| Arquitectura y precios 2026 | Decisiones de plan (Free/Launch/Scale) |
| Lambda + psycopg3 integration | Implementar handlers Python que escriben a Neon |
| Branching workflow | Testing, preview deployments, per-PR databases |
| Vs RDS, Supabase, PlanetScale | Justificar la eleccion por este portfolio |

## Reglas criticas

- SIEMPRE usar pooled connection string (`neon_connection_pooler=true`) en Lambda
- SIEMPRE guardar DATABASE_URL en SSM Parameter Store (mismo patron que secrets)
- NUNCA usar Vercel Postgres — ya no existe (migrado a Neon 2024). Usar Neon directo
- SIEMPRE leer en module scope en Lambda: `db = psycopg3.connect(...)` FUERA del handler
- NUNCA crear branch main a mano — main es inmutable en produccion
- SIEMPRE usar `sslmode=require&channel_binding=require` en Lambda
- Scale-to-zero auto-suspend despues de 5 min inactivity en Free/Launch (es normal, no es problema)

## Quick start (5 min)

```bash
# 1. Crear proyecto (free tier indefinido)
# Acceso a https://console.neon.tech → create project → us-west-2 (Oregon)

# 2. DB URL llega como: postgresql://user:pass@host/dbname
# Guardar en SSM Parameter Store (AWS Secrets Manager alternativa):
aws ssm put-parameter \
  --name /portfolio/neon-database-url \
  --value "postgresql://..." \
  --type SecureString

# 3. Lambda handler consume desde SSM
# Ver archivo 02-aws-lambda-integration-python.md
```

## Entorno actual (mayo 2026)

- **Free tier**: $0/mes. 100 CU-hours/mes (91.25 horas). 0.5 GB storage. PERPETUO.
- **Launch tier**: $0.106/CU-hour. 100 GB transfer incluido. Autoscale a 16 CU.
- **Scale tier**: $0.222/CU-hour. Hasta 56 CU. Private networking. HIPAA/SOC2.
- **Storage**: $0.35/GB-mes (post-free tier)
- **Compute**: 1 CU = 1 vCPU + 4 GB RAM
- **Regions**: us-west-2 (Oregon) disponible. Migrar de Azure deprecado Aug 2026.
- **PG version**: 14, 15, 16, 17, 18 GA (asynchronous I/O enabled)

## Para este portfolio

- **Plan recomendado**: Free tier (perpetuo, nunca expira)
- **Compute**: 0.25 CU default (suficiente para 200 contacts/mes + 15k events tracking)
- **Storage**: <100 MB probable (dentro de 0.5 GB free)
- **Branching**: 10 branches free tier (para testing, preview deploy per PR)
- **Suspension**: Auto-suspend despues 5 min inactivity (sin costo CU cuando suspendido)

## Arquitectura blockchain

```
DynamoDB Streams → Lambda processor → Neon PostgreSQL (us-west-2)
                                     ↓
                            CRM queries (analytics)
                            
Lambda cron (daily) → tracking events → Neon (append-only log)
```

- Neon FREE tier soporta este volumen indefinidamente
- Branching para testing: `neon branch create --name test-feature-X`
- Instant clone de main sin costo de storage (copy-on-write)

## Archivos de referencia

1. **01-architecture-pricing.md** — Detalles de planes, scale-to-zero, regiones
2. **02-aws-lambda-integration-python.md** — psycopg3 + pooling + SSM + codigo real
3. **03-branching-workflow.md** — Git branches para testing/preview
4. **04-vs-rds-supabase-planetscale.md** — Comparativa con alternativas
5. **../skills/neon/SKILL.md** — Skill para invocacion via `/neon` en Claude

## Referencias

- [Neon Docs](https://neon.com/docs)
- [Neon Pricing](https://neon.com/pricing)
- [Lambda Integration Guide](https://neon.com/docs/guides/aws-lambda)
- [Branching Primer](https://neon.com/docs/get-started/workflow-primer)
- [PG18 Features](https://neon.com/postgresql/18-new-features)
