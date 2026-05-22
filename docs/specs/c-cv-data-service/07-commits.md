# 07 — Commits

[<- 06 Archivos](06-archivos-afectados.md) | [Siguiente: worktrees ->](08-paralelizacion-worktrees.md)

## 9. Commits

Cada commit deja el repo verde (lint + typecheck + tests del scope) y ejecuta
su verificacion incremental ANTES de commitear. Conventional Commits espanol.
Un solo PR `feature/cv-data-service -> dev`.

| # | Commit | Cubre | Verificacion incremental |
|---|--------|-------|--------------------------|
| 1 | `docs(specs): plan del servicio cv y handler HTTP generico` | la carpeta del plan | `markdownlint` / lectura |
| 2 | `feat(shared): handler HTTP generico en lambda_kit` | T1, T2 / AC-1,2,3 | `serverless tests --type=coverage --shared` |
| 3 | `refactor(contact-form): delega el handler en http_handler` | T3 / AC-7 | `serverless tests --type=unit --lambda=contact_form` |
| 4 | `refactor(tracking-pixel): delega el handler en http_handler` | T4 | `serverless tests --type=unit --lambda=tracking_pixel` |
| 5 | `feat(content): el frontend envia operation y action` | T5 / AC-7 | `pnpm run build` + E2E form/tracking |
| 6 | `feat(db): cv_repository con las queries de lectura del CV` | T6 / AC-4,5,9 | `serverless tests --type=coverage --shared` |
| 7 | `feat(cv): scaffold del Lambda cv (manifest, settings)` | T7 | `python -m compileall -q core` |
| 8 | `feat(cv): modelo Pydantic CvQueryModel` | T8 / AC-6 | `serverless tests --type=unit --lambda=cv` |
| 9 | `feat(cv): cv_service con cache sobre cv_repository` | T9 / AC-4,5,9 | `serverless tests --type=unit --lambda=cv` |
| 10 | `feat(cv): handler delega en http_handler + events` | T10 / AC-10 | `serverless run --stage=local --lambda=cv` |
| 11 | `feat(cv): controllers de las 10 actions del CV` | T11 / AC-4,5,6 | `serverless tests --type=coverage --lambda=cv` |
| 12 | `test(cv): suite de integration E2E contra Neon` | T12 / AC-4,5,6,9 | `serverless tests --type=integration --lambda=cv` |
| 13 | `feat(content): cliente cv-api-client con validacion Zod` | T13 / AC-8 | `pnpm --filter @portfolio/content exec vitest run` |
| 14 | `feat(apps): el prebuild de las 6 apps consume el API cv` | T14 / AC-8 | `pnpm run build` |
| 15 | `test(cv-data-service): verificacion E2E del plan` | seccion 11 + `git rm -r docs/specs/c-cv-data-service` | bateria completa seccion 11 |

## Secuencia

```text
1 (plan)
  -> 2 (base: http_handler — todos dependen de esto)
       -> 3, 4, 5    (migracion handlers — paralelizable)
       -> 6 (cv_repository — paralelo a 3/4/5)
            -> 7 (scaffold cv)
                 -> 8, 9, 10   (paralelizable tras scaffold)
                      -> 11 (controllers)
                           -> 12 (E2E cv)
                                -> 13 (cliente TS)
                                     -> 14 (prebuild apps)
                                          -> 15 (verificacion E2E + limpieza)
```

## PR

Un solo PR `feature/cv-data-service -> dev`, merge commit. El body sigue el
template (`.claude/rules/git-workflow.md`): Problema / Solucion / Como probar
(reusa la bateria de la seccion 11) / TODO (eliminar YAML, custom domain API).

El commit 15 incluye `git rm -r docs/specs/c-cv-data-service/` — la carpeta del
plan es efimera (`.claude/rules/plan-format.md`). Las decisiones que deban
sobrevivir (el contrato `http_handler`) se promueven a
`.claude/rules/lambda-controller.md` ANTES de borrar la carpeta.

`git push` + crear PR SOLO cuando la bateria de la seccion 11 pase completa en
verde.

Continua en [08-paralelizacion-worktrees.md](08-paralelizacion-worktrees.md).
