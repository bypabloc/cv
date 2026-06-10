# 07 — Seccion 8: descomposicion para paralelizacion

> Tareas atomicas con file exclusivity. Cap de orquestacion: <=4 agentes,
> 1 workflow a la vez ([orchestration.md](../../../.claude/rules/orchestration.md)).
> [Volver al README](README.md).

| # | Tarea | Archivos (raiz) | AC | Depende de | Paralelizable con | Verify | Done |
|---|-------|-----------------|----|------------|-------------------|--------|------|
| T1 | Fase 0: secret PAT + bucket S3 + rol OIDC (declarativos + provision) | `serverless/lambda/resources/**`, `.claude/rules/serverless-secrets.md` | AC-7, AC-8 | — | T2 | `validate-catalog` + `provision-infra` idempotente | recursos en SSM/S3 |
| T2 | Fase 0: aislamiento Neon dev (branch + rotar SSM) | operativo (sin codigo) | AC-12 | — | T1 | escritura de prueba en dev no toca prod | branches verificados |
| T3 | Refactor `cv_write` en shared.db + seed lo consume | `shared/db/repositories/cv_write.py`, `services/db/core/services/seed_service.py`, `shared/tests/**` | AC-1, AC-4 | — | T1, T2 | `tests --shared` + `--lambda=db` | verde + lint-deps |
| T4 | Scaffold `cv_admin` + auth + handler + operation publish | `services/cv_admin/**` (base) | AC-2, AC-7 | T3 | T7 | `tests --lambda=cv_admin` | base verde |
| T5 | `content`: profile + experiences (models/controllers/services) | `services/cv_admin/core/**` (archivos propios) | AC-1, AC-3 | T4 | T6 | unit + coverage | verde |
| T6 | `content`: projects + entidades simples + skill-categories + reorder + catalogs | `services/cv_admin/core/**` (archivos propios) | AC-4, AC-5 | T4 | T5 | unit + coverage | verde |
| T7 | devtools `db_export` + workflow `db-backup.yml` | `devtools/db_export/**`, `.github/workflows/db-backup.yml` | AC-8 | T1 | T4-T6 | devtools unit + dispatch manual | snapshot en S3 |
| T8 | Seed desde S3 + guard + eliminar `seeds/data/` | `services/db/**`, docs/rules | AC-9, AC-10 | T7 (snapshots verificados) | T9-T11 | gate 2.4 + unit db | `rg seeds/data` limpio |
| T9 | Admin: clients + hooks + types + validation + MSW | `admin/src/features/cv-management/{api,hooks}/**`, `admin/tests/mocks/**` | AC-6 | contrato de T4-T6 (tipos) | T10 | admin test | verde |
| T10 | Admin: componentes base (bilang, niche-picker, section-list, publish-card) | `admin/src/features/cv-management/components/**` | AC-5, AC-6, AC-7 | T9 (tipos) | T9 parcial | admin test | verde |
| T11 | Admin: forms por entidad + sub-rutas + overview | `admin/src/app/(admin)/cv/**`, components restantes | AC-6 | T10 | — | test + build | rutas en `out/` |
| T12 | E2E api + admin browser: implementar TODOS los specs de [11-specs-e2e-api.md](11-specs-e2e-api.md) (~19) y [12-specs-e2e-admin.md](12-specs-e2e-admin.md) (~14) | `tests/api/**`, `tests/admin/**` | todos | T5, T6, T11 + deploy dev | — | `e2e --module=api/admin --env=dev` | todos los specs de los docs 11-12 verdes |
| T13 | Verificacion final + limpieza spec | bateria completa | todos | T1-T12 | — | seccion 11 | PR verde |

Checks de paralelizabilidad: T5/T6 comparten carpeta pero archivos
disjuntos (un controller/model por action) — asignar listas de archivos
explicitas si se paraleliza con worktrees. T9/T10 tocan la misma feature:
secuencial dentro de un mismo worktree, paralelo respecto del backend.
