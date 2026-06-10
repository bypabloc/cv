# 08 — Seccion 9: commits

> Rama `feature/c-cv-management` desde `dev`. Un PR a `dev`. Cada commit
> deja el repo verde y ejecuta su verificacion ANTES de commitear.
> [Volver al README](README.md).

| # | Mensaje (Conventional Commits, espanol) | AC | Verificacion incremental |
|---|------------------------------------------|----|--------------------------|
| 1 | `docs(specs): agrega plan c-cv-management` | — | lint markdown implicito (pre-commit) |
| 2 | `chore(serverless): declara secret github-deploy-token y bucket db-backups` | AC-7, AC-8 | `validate-catalog`; `provision-infra --stage=dev` idempotente |
| 3 | `refactor(serverless): extrae helpers de escritura del seed a shared.db cv_write` | AC-1 | `tests --shared` + `tests --lambda=db` + `lint-deps` |
| 4 | `feat(serverless): agrega Lambda cv_admin con auth admin y operation publish` | AC-2, AC-7 | `tests --lambda=cv_admin` + `lint-deps --lambda=cv_admin` |
| 5 | `feat(serverless): cv_admin content para profile y experiencias` | AC-1, AC-3 | unit + coverage cv_admin |
| 6 | `feat(serverless): cv_admin content para proyectos, entidades simples, reorder y catalogs` | AC-4, AC-5 | unit + coverage cv_admin |
| 7 | `feat(devtools): agrega db_export con snapshot YAML seed-compatible a S3` | AC-8 | `test_runner --module=devtools --type=unit` + ruff |
| 8 | `ci(github): agrega workflow db-backup semanal por OIDC` | AC-8 | `act -n` o dispatch manual en dev tras push |
| 9 | `refactor(serverless): seed lee desde S3 con guard confirm_overwrite` | AC-9 | `tests --lambda=db` |
| 10 | `chore(serverless): elimina seeds/data tras snapshot verificado en S3` | AC-10 | gate 2.4 completo + `rg -l "seeds/data"` limpio |
| 11 | `feat(admin): agrega feature cv-management con clients, hooks y mocks` | AC-6 | `pnpm --filter @portfolio/admin test` + typecheck |
| 12 | `feat(admin): componentes base de edicion bilang, niches y publicar` | AC-5, AC-6, AC-7 | admin test + coverage |
| 13 | `feat(admin): sub-rutas por seccion del cv con forms y overview` | AC-6 | admin test + `pnpm --filter @portfolio/admin build` |
| 14 | `test(e2e): specs api de cv_admin con lifecycle completo por entidad` (los ~19 specs de [11-specs-e2e-api.md](11-specs-e2e-api.md)) | AC-1..5, 7, 11 | `e2e --module=api --env=dev` |
| 15 | `test(e2e): specs browser del editor cv con flujos completos por seccion` (los ~14 specs de [12-specs-e2e-admin.md](12-specs-e2e-admin.md)) | AC-5..7, 13 | `e2e --module=admin --env=dev` |
| 16 | `docs(rules): actualiza neon-management y serverless-backend al modelo DB-fuente-de-verdad` | — | lectura cruzada sin referencias muertas |
| 17 | `chore(specs): elimina la carpeta del plan c-cv-management` (`git rm -r docs/specs/c-cv-management/`) | — | bateria seccion 11 completa en verde |

Notas:

- El deploy a dev de `cv_admin` y `db` ocurre entre los commits 6 y 14
  (necesario para E2E); el deploy NO es un commit, es operacion devtools.
- Los commits 5-6 pueden subdividirse si el diff supera lo revisable.
- Gate de cierre: push + PR SOLO con la bateria de
  [10-verificacion-e2e.md](10-verificacion-e2e.md) en verde.
