# Specs del backend serverless

> Descomposicion atomica del backend del portfolio (5 Lambdas + API GW +
> 5 tablas DynamoDB + Neon PG + SES + Turnstile) en specs ejecutables
> independientemente.

## Indice

| Spec | Titulo | Estado | Estimacion | Dependencias |
|------|--------|--------|------------|--------------|
| [SPEC-000](SPEC-000-setup-inicial.md) | Setup inicial (AWS account, SSM secrets, Cloudflare Turnstile widget) | done | 0.5 dia | — |
| [SPEC-001](SPEC-001-sam-template-base.md) | SAM template base + 3 tablas DynamoDB hot path | done | 1 dia | SPEC-000 |
| [SPEC-002](SPEC-002-common-module.md) | Modulo `src/common/` compartido (config, logger, types, clients) | done | 0.5 dia | SPEC-001 |
| [SPEC-003](SPEC-003-cache-module.md) | Cache module en `common/cache/` + tabla cache | done | 1 dia | SPEC-002 |
| [SPEC-004](SPEC-004-rate-limit-module.md) | Rate-limit module en `common/rate_limit/` + 2 tablas | done | 1 dia | SPEC-002, SPEC-003 |
| [SPEC-005](SPEC-005-contact-form-lambda.md) | Lambda `contact_form` (POST /contact + Turnstile + SES + rate-limit) | done | 1 dia | SPEC-002, SPEC-003, SPEC-004 |
| [SPEC-006](SPEC-006-tracking-pixel-lambda.md) | Lambda `tracking_pixel` (POST /track + enrichment + rate-limit) | draft | 0.5 dia | SPEC-002, SPEC-003, SPEC-004 |
| [SPEC-007](SPEC-007-turnstile-validator-lambda.md) | Lambda `turnstile_validator` (POST /validate-turnstile) | draft | 0.5 dia | SPEC-002, SPEC-003 |
| [SPEC-008](SPEC-008-neon-setup-migrations.md) | Neon project + migrations SQL 001-005 + psycopg3 layer | draft | 1 dia | SPEC-001 |
| [SPEC-009](SPEC-009-stream-processor-lambda.md) | Lambda `stream_processor` (Streams -> Neon) + DLQ | draft | 1-2 dias | SPEC-005, SPEC-006, SPEC-008 |
| [SPEC-010](SPEC-010-aggregator-lambda.md) | Lambda `aggregator` (cron 03:00 UTC) + materialized views | draft | 1-2 dias | SPEC-008, SPEC-009 |
| [SPEC-011](SPEC-011-ses-dns-production.md) | SES domain verification (DKIM/SPF/DMARC) + production access | draft | 0.5 dia + 24-48h espera | SPEC-000 |
| [SPEC-012](SPEC-012-frontend-contact-form.md) | Componente `ContactForm.astro` en `packages/ui` + integracion 6 apps | draft | 1 dia | SPEC-005 |
| [SPEC-013](SPEC-013-frontend-tracking-pixel.md) | Componentes `TrackingPixel.astro` + `CookieBanner.astro` + GDPR opt-in | draft | 1 dia | SPEC-006, SPEC-012 |
| [SPEC-014](SPEC-014-dashboard-analytics.md) | Dashboard Astro protegido que consulta Neon (basic auth) | draft | 2-3 dias | SPEC-010 |
| [SPEC-015](SPEC-015-observability-runbook.md) | RUNBOOK + DEPLOYMENT + smoke tests + AWS Billing Alarm | draft | 0.5 dia | TODAS |

**Total estimado**: 12-18 dias de trabajo no full-time (depende de paralelizacion).

## Grafo de dependencias

```text
SPEC-000 (setup)
    |
    +--> SPEC-001 (SAM base)
    |       |
    |       +--> SPEC-002 (common module)
    |       |       |
    |       |       +--> SPEC-003 (cache)
    |       |       |       |
    |       |       |       +--> SPEC-004 (rate-limit)
    |       |       |       |       |
    |       |       |       |       +--> SPEC-005 (contact_form)
    |       |       |       |       +--> SPEC-006 (tracking_pixel)
    |       |       |       |
    |       |       |       +--> SPEC-007 (turnstile_validator)
    |       |       |
    |       |       +-------------------> SPEC-008 (Neon + migrations)
    |       |                                 |
    |       |                                 +--> SPEC-009 (stream_processor)
    |       |                                 |        |
    |       |                                 |        +--> SPEC-010 (aggregator)
    |       |                                 |                   |
    |       |                                 |                   +--> SPEC-014 (dashboard)
    |       |                                 |
    |       |   SPEC-005 ----------------------+
    |       |   SPEC-006 ----------------------+ (escriben a Dynamo, alimentan Stream)
    |       |
    |       +--> SPEC-005 ----+
    |                         |
    |                         +--> SPEC-012 (ContactForm.astro frontend)
    |                         |
    |       +--> SPEC-006 ----+
    |                         |
    |                         +--> SPEC-013 (TrackingPixel.astro + Cookie banner)
    |
    +--> SPEC-011 (SES DKIM + DNS + production access)

SPEC-015 (RUNBOOK + smoke) depende de todas, ejecuta al final
```

## Paralelizables

| Grupo | Specs que se pueden ejecutar en paralelo | Razon |
|-------|------------------------------------------|-------|
| Grupo A | SPEC-000, SPEC-011 (DNS) | DNS de SES no bloquea setup AWS |
| Grupo B | SPEC-003, SPEC-007 | Cache no depende del Turnstile validator y viceversa |
| Grupo C | SPEC-005, SPEC-006, SPEC-007 | Las 3 Lambdas hot path despues de common + cache + rate-limit |
| Grupo D | SPEC-012, SPEC-013 | Frontends de form y tracking se pueden hacer en paralelo |

## Definition of Done (transversal a TODAS las specs)

- [ ] Tests pytest con coverage >= 80% per-file
- [ ] `serverless lint` + `serverless format` + `serverless typecheck` pasan
- [ ] `serverless validate` (sam validate) pasa
- [ ] `serverless invoke` con event JSON ejemplar pasa local
- [ ] `serverless deploy --stage=dev` exitoso
- [ ] `serverless smoke --stage=dev` pasa
- [ ] CloudWatch Logs limpios primeras 10 invocaciones (sin ERROR)
- [ ] Documentacion actualizada (ARCHITECTURE.md, RUNBOOK.md si aplica)
- [ ] Commit con conventional commits espanol (sin atribucion IA)

## Convenciones criticas (recordatorio)

Todas las specs deben respetar:

- Python 3.13 + arm64 (Graviton2)
- AWS Powertools v3 (`@logger @tracer @metrics`)
- boto3 clients en module scope (no en handler)
- Secrets via SSM Parameter Store + KMS (NUNCA env vars)
- IAM least privilege (acciones y ARNs especificos)
- Conventional commits en espanol
- Tests path mirror src/X -> tests/unit/X
- BDD-style en docstring + AAA en cuerpo + asserts EXACTOS

## Workflow de ejecucion

1. Leer la spec completa antes de empezar
2. Verificar dependencias estan `done`
3. Crear branch `feature/spec-NNN-<short-name>` desde `dev`
4. Implementar tasks en orden (cada task tiene verify command)
5. Pasar Definition of Done de la spec + transversal
6. Commit + push + PR contra `dev`
7. Una vez merged, marcar spec como `done` en este README
