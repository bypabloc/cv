# 06 — Commits

> Conventional Commits en espanol. Cada commit deja el repo verde
> (lint + typecheck + tests del scope) y es atomico.

Rama: `feature/build-env-vars-per-env` desde `dev`. Un solo PR
`feature/build-env-vars-per-env -> dev`.

| # | Commit | Que toca | Verifica antes de commit |
|---|--------|----------|--------------------------|
| 1 | `docs(specs): plan build-env-vars-per-env` | `docs/specs/build-env-vars-per-env/**` (8 archivos del spec) | repo verde (no toca codigo) |
| 2 | `feat(app-shared): validateApiEndpoint + validateTurnstileSitekey` | `packages/app-shared/src/lib/validate-build-env.ts`, `packages/app-shared/src/index.ts`, test unit | `pnpm --filter @portfolio/app-shared exec vitest run` |
| 3 | `feat(ui): guard PUBLIC_API_ENDPOINT en TrackingPixel` | `packages/ui/src/components/TrackingPixel.astro` | `pnpm exec astro check`, build local hub con env vars OK |
| 4 | `test(ui): build-test del dist verifica data-api-endpoint + hrefs` | `packages/ui/tests/build/tracking-pixel-build.test.ts`, `packages/ui/vitest.config.ts` | `pnpm --filter @portfolio/ui exec vitest run` (incluido build-test) |
| 5 | `chore(hooks): pre-push corre build-tests con RUN_BUILD_TESTS=1` | `.git-hooks/pre-push` (opt-in flag) | `RUN_BUILD_TESTS=1 .git-hooks/pre-push` simulado |
| 6 | `feat(devtools): script github_sync para sincronizar client env a GH Vars` | `devtools/github_sync/**`, `devtools/tests/unit/test_github_sync.py` | `python devtools/run.py test_runner --module=devtools --type=unit`, `ruff check` |
| 7 | `docs(devtools): README de github_sync con ejemplos` | `devtools/github_sync/README.md` | review manual |
| 8 | `feat(astro): astro.config usa buildSiteUrl en vez de hardcode prod` | 6 `apps/*/astro.config.ts` | `pnpm exec astro check` + `pnpm run build` de las 6 apps |
| 9 | `feat(ci): deploy-apps.yml usa environment y env: con GH Variables` | `.github/workflows/deploy-apps.yml`, `.github/workflows/ci.yml` (comentario) | `gh workflow run` dry-run en rama (si soportado) o lint del yaml |
| 10 | `feat(ci): verify-deploy smoke test post-deploy (Capa C)` | `.github/workflows/deploy-apps.yml` (nuevo job) | `actionlint` + yaml lint |
| 11 | `docs(rules): rule client-env-sync + update ci-cd-pipeline + pages-config` | `.claude/rules/client-env-sync.md`, `.claude/rules/ci-cd-pipeline.md`, `cloudflare/pages-config.md`, `CLAUDE.md` (indice) | claude -p valida la rule nueva |
| 12 | `chore(specs): cierra el plan build-env-vars-per-env` | `git rm -r docs/specs/build-env-vars-per-env/` + verificacion E2E final | la bateria de 08-verificacion-e2e.md pasa entera en verde |

Reglas por commit:

- Cada commit pasa su verificacion incremental ANTES de commitear (NO
  se difiere al final). Si el commit 4 deja vitest rojo, no se hace el
  commit 5 — se arregla y se rehace el 4.
- El commit 12 NO es push si la bateria de 08 no esta entera en verde
  (`git push` + PR es el gate de cierre, no un paso intermedio).
- Mensaje exacto del commit 1 sugerido:

  ```
  docs(specs): plan build-env-vars-per-env

  - Plan en docs/specs/build-env-vars-per-env/ (8 archivos)
  - Cubre el bug del /track desactivado en dev + dropdown a prod
  - 3 capas defensivas (guard, build-test, smoke), script de sync de
    client env a GitHub Environment Variables, deploy-apps.yml con
    env vars por stage
  - 9 AC numerados, 12 commits planeados, paralelizacion limitada
  ```

## Secuencia recomendada

```
1 (spec)
  -> 2,3,4 (Fase 1: guards + build-test) [PARALELIZABLE LIMITADO — ver 07]
  -> 5 (pre-push hook)
  -> 6,7 (Fase 2: github_sync) [PARALELIZABLE con 8 — distintos archivos]
  -> 8 (astro.config.ts x6)
  -> 9,10 (Fase 3: deploy-apps.yml) [SECUENCIAL — mismo archivo]
  -> 11 (Fase 4: docs)
  -> 12 (cierre del plan + verificacion E2E)
```
