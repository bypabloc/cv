# 03 — Commits, paralelizacion y verificacion E2E

> [README](README.md) | [01-backend](01-backend.md) | [02-frontend](02-frontend.md)

## 9. Commits

1. `docs(specs): agrega plan d-cv-consolidation` — esta carpeta.
2. `feat(serverless): fase Authorize declarativa y CORS por operation en lambda_kit`
   — required_permission + set_permission_checker + cors dict + tests kit.
   Verify: `serverless tests --type=unit --shared`.
3. `refactor(serverless): cv_repository con sesion compartida + list_publications`
   — session param, get_full_cv 1 sesion, get_full_cv_admin. Verify: idem.
4. `feat(serverless): lambda cv absorbe operations content y publish de cv_admin`
   — controllers/services/models/settings/manifest + get-all + tests
   migrados. Verify: `serverless tests --type=unit --lambda=cv` +
   `lint-deps --lambda=cv`.
5. `chore(devtools): endpoints rate-limit /cv y e2e sin cv_admin` —
   rate_limit_cmds, e2e/flags, tests devtools. Verify:
   `test_runner --module=devtools --type=unit`.
6. `feat(admin): consume /cv con get-all, tab activo y textareas` —
   frontend completo + mocks + tests unit. Verify:
   `pnpm --filter @portfolio/admin test` + build.
7. `test(e2e): specs api y admin contra /cv` — _cv_admin_flows + _cv_ui +
   conftest. Verify: suite api contra dev (post-deploy).
8. `docs(rules): cv absorbe cv_admin (9 lambdas)` — rules + CLAUDE.md +
   README del cv.
9. `feat(admin): mejoras UI del editor CV` — sweep playwright (1+ commits).
10. `docs(specs): elimina carpeta del plan` — ultimo commit del PR.

Post-merge (commit de seguimiento tras destroy):
`chore(serverless): elimina el lambda cv_admin` — git rm carpeta +
referencias residuales.

## 10. Paralelizacion

Base secuencial: commits 1-3 (kit + repository: los toca todo lo demas).
Tras fijar el contrato get-all: frontend (admin/ + packages/ui) en agente
paralelo con worktree NO necesario (arboles disjuntos serverless/ vs
admin/). Cap <=4 agentes; aqui 1 inline + 1 agente.

## 11. Verificacion E2E

### Parte A — refactor de tests
- Cero referencias vivas a `/cv-admin` en src del admin, MSW y E2E
  (`rg -l 'cv-admin'` solo debe matchear docs historicas/plan).
- Tests de cv_admin migrados a `services/cv/tests/` y verdes.

### Parte B — bateria (gate del push/PR)
```bash
python devtools/run.py serverless tests --type=unit --shared
python devtools/run.py serverless tests --type=unit --lambda=cv
python devtools/run.py serverless lint-deps
python devtools/run.py test_runner --module=devtools --type=unit
pnpm run lint && pnpm run typecheck && pnpm run test && pnpm run build
pnpm --filter @portfolio/admin test && pnpm --filter @portfolio/admin build
```

### Parte C — despliegue real (post-merge, gate de "listo")
1. `gh run watch` deploy-backend y deploy-apps (cada job verde).
2. Seed rate-limit `'/cv#...'` en dev y prod.
3. E2E: `e2e --module=api --lambda=cv` + `e2e --module=admin` contra dev.
4. Curl real: GET `https://api.portfolio.dev.../cv?operation=cv&action=get`
   200; POST content.get-all con JWT admin 200; sin JWT 401; flujo
   Publicar desde la UI.
5. `serverless destroy --lambda=cv_admin --stage=dev` + create-deployment
   del stage + curl `/cv-admin` confirmando que NO existe (AC-4).
6. Commit de seguimiento eliminando la carpeta cv_admin + esta carpeta de
   plan ya eliminada en el commit 10.
