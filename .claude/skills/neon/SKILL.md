---
name: neon-serverless-postgres
description: >
  Neon serverless PostgreSQL reference for portfolio backend.
  Use when the user asks about "neon postgres", "serverless database",
  "scale-to-zero database", "database branching", "neon pricing free tier",
  "lambda postgres connection", "psycopg3 lambda", "connection pooling lambda",
  "compare neon vs supabase", "neon vs rds", "test database per PR",
  "point-in-time recovery postgres", "que postgres usar", "serverless pg",
  "branching database", "instant database clone", "copy-on-write database",
  or any comparison of Neon with RDS, Supabase, PlanetScale, Aurora.
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: "topic (pricing|lambda|branching|comparison|architecture)"
---

# Neon Serverless PostgreSQL Skill

> Reference for Neon integration in this portfolio (Lambdas + DynamoDB Streams + tracking analytics).
> Verified 2026-05-14. DO NOT answer Neon questions from training data—ALWAYS consult the docs in this skill.

## Cuando invocar

- Usuario pregunta sobre Neon, serverless Postgres, branching, scale-to-zero
- Usuario compara providers (Neon vs RDS vs Supabase vs PlanetScale)
- Usuario pregunta sobre Lambda + PostgreSQL integration
- Usuario necesita pricing, regions, features de Neon 2026
- Usuario pregunta sobre free tier, compute hours, storage costs
- Usuario pregunta sobre psycopg3, connection pooling, cold start

## Cuando NO invocar

- Usuario pregunta sobre PostgreSQL en general (sin mencionar Neon) → use `postgresql-18` skill si existe
- Usuario pregunta sobre Django ORM (sin DB) → usar `django-6` skill
- Usuario pregunta sobre AWS Lambda sin DB context → usar `aws-lambda-*` si existe
- Usuario pregunta sobre Vercel (no Neon) → usar deployment skill

## Knowledge base

Documentacion de referencia en `.claude/docs/neon/`:

1. **README.md** — Quick start, pricing 2026, reglas criticas, entorno actual
2. **01-architecture-pricing.md** — Que es Neon, scale-to-zero, planes Free/Launch/Scale, regiones
3. **02-aws-lambda-integration-python.md** — psycopg3 + pooling + SSM + codigo real + cold start analysis
4. **03-branching-workflow.md** — Git-style branching, testing per PR, data recovery, CLI commands
5. **04-vs-rds-supabase-planetscale.md** — Comparativa honesta, decision tree, performance, pricing

Gestion operativa concreta del proyecto: `.claude/rules/neon-management.md`
— connection string en SSM, runner de migrations versionado
(`serverless/scripts/migrate.py` + `serverless/migrations/`), comandos
`python devtools/run.py serverless db-*`, branches Neon, rollback, seguridad.
Para CUALQUIER pregunta de "como gestiono / como aplico migration / como
roleo back / como creo un branch" en este portfolio, esa rule es la fuente
de verdad operativa; los docs cubren el "que es / por que / cuanto cuesta".

## Reglas criticas SIEMPRE/NUNCA

- **SIEMPRE** usar pooled connection string (`-pooler` endpoint) en Lambda
- **SIEMPRE** guardar DATABASE_URL en AWS SSM Parameter Store (SecureString type)
- **SIEMPRE** inicializar cliente Neon en module scope (no dentro de handler) para reutilizar conexion
- **SIEMPRE** agregar `sslmode=require&channel_binding=require` a connection string
- **SIEMPRE** usar psycopg3 (NO psycopg2 deprecated)
- **NUNCA** usar Vercel Postgres (ya no existe, migrado a Neon 2024)
- **NUNCA** preocuparte por suspensión auto (5 min inactivity) — es normal y sin costo
- **NUNCA** esperar costo en portfolio Free tier (<100 MB, volumen bajo)

## Tabla de docstrings

| Seccion | Archivo | Linea aprox |
|---------|---------|-----------|
| Pricing 2026 | 01-architecture-pricing.md | "Planes 2026" |
| Scale-to-zero | 01-architecture-pricing.md | "Scale-to-zero" |
| Lambda integration | 02-aws-lambda-integration-python.md | "Setup (5 pasos)" |
| psycopg3 handler | 02-aws-lambda-integration-python.md | "Codigo Lambda" |
| Connection pooling | 02-aws-lambda-integration-python.md | "Pooling: dos opciones" |
| Cold start analysis | 02-aws-lambda-integration-python.md | "Performance: cold start analysis" |
| Branching intro | 03-branching-workflow.md | "Que es un branch en Neon" |
| Per-PR databases | 03-branching-workflow.md | "Use cases: Per-PR databases" |
| CLI commands | 03-branching-workflow.md | "CLI commands basicos" |
| Vs RDS | 04-vs-rds-supabase-planetscale.md | "RDS Postgres (NO recomendado)" |
| Vs Supabase | 04-vs-rds-supabase-planetscale.md | "Supabase (ALTERNATIVA)" |
| Decision tree | 04-vs-rds-supabase-planetscale.md | "Decision tree" |

## Workflow tipico de respuesta

1. **User pregunta sobre Neon** → leer el archivo relevante de `.claude/docs/neon/`
2. **Verificar contexto** → pricing, architecture, Lambda, branching, comparison?
3. **Dar respuesta CONCRETA** con codigo/comandos/URLs de los docs
4. **Incluir reglas criticas SIEMPRE/NUNCA** que apliquen
5. **Citar fuentes** — "Ver .claude/docs/neon/XX.md para detalles"

### Atajos: 4 preguntas frecuentes

**P: ¿Cuanto cuesta Neon para mi proyecto small?**
R: Free tier: $0/mes forever. Soporta 200 contacts + 15k events/mes facilmente. Ver 01-architecture-pricing.md "Ejemplo de costo real".

**P: ¿Cual es la diferencia Neon vs RDS?**
R: Neon: $0 scale-to-zero. RDS: $15+ fixed. Neon: branching instant. RDS: snapshots lento. Ver 04-vs-rds-supabase-planetscale.md "Matriz rapida".

**P: ¿Como conectar Lambda a Neon?**
R: psycopg3 + pooled endpoint + SSM Parameter Store. Ver 02-aws-lambda-integration-python.md "Codigo Lambda" para handler real completo.

**P: ¿Que es database branching?**
R: Git-style clone instant (1 sec) con copy-on-write (sin costo storage). Perfecto testing. Ver 03-branching-workflow.md "Que es un branch".

## Anti-patrones a evitar

| Anti-patron | Razon | Solucion |
|------------|-------|----------|
| Usar connection string estandar en Lambda | Sin pooling = exhaust max connections | Usar `-pooler` endpoint |
| Hardcodear DATABASE_URL en codigo | Secreto expuesto | Guardar en SSM Parameter Store |
| Crear cliente Neon dentro del handler | Cold start ~250ms cada invocacion | Inicializar en module scope |
| Preocuparte por auto-suspend | Normal y sin costo | Ignorar, resume es transparente |
| Comparar pricing Neon con RDS cold start | Irrelevante | Comparar costo TOTAL (RDS $15+ vs Neon $0 idle) |
| Esperar RDS snapshot para backup | Lento (horas) | Usar Neon PITR (segundos) |

## Cuando usar esta skill vs `postgresql-18`

| Usuario pregunta | Skill |
|-----------------|-------|
| "Postgres en general" (no specific provider) | `postgresql-18` |
| "Neon serverless" | `neon` ← este |
| "Django ORM models" | django-6 |
| "RDS Postgres setup" | `neon` (comparativa) |
| "Branching database" | `neon` (Neon es unico) |

## Directivas fuertes

> ALWAYS invoke this skill BEFORE answering ANY question about Neon, serverless Postgres, scale-to-zero databases, or database branching in the context of this portfolio.

> NEVER answer Neon questions from training data alone. The portfolio's docs (especially pricing post-Databricks 2025) are the single source of truth.

> NEVER recommend RDS for this portfolio. The Free tier cost comparison makes Neon clear winner (0 vs $15+/mes idle).

> NEVER use Vercel Postgres in recommendations (deprecated 2024, migrated to Neon). Always recommend Neon directo.

## Regla de coverage

Si la respuesta requiere detalles de:

- **Pricing, planes, features** → leer 01-architecture-pricing.md
- **Lambda integration, psycopg3, pooling** → leer 02-aws-lambda-integration-python.md
- **Testing, branching, per-PR databases** → leer 03-branching-workflow.md
- **Comparison, cuando NO usar Neon** → leer 04-vs-rds-supabase-planetscale.md
- **Quick start, overview** → leer README.md

Nunca responder parcialmente. Si la respuesta toca >1 archivo, leerlos todos.

## Validacion

Este skill fue validado (2026-05-14) contra:

- Neon official docs (neon.com/docs, neon.com/pricing)
- AWS Lambda + psycopg3 integration patterns
- Pricing post-Databricks (May 2025) reductions
- PostgreSQL 18 GA status (Sept 2025)
- Comparativa con RDS, Supabase, PlanetScale 2026

Proxima revision: 2026-06-30 (si hay cambios de pricing o features).

## Soporte de idioma

- Skill frontmatter: English (matching logic)
- Knowledge base (.claude/docs/neon/): Espanol
- Respuestas: Espanol, terminos tecnicos en ingles
