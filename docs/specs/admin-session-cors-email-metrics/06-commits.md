# 06 — Commits

[<- 05](05-bug-metrics-navitem.md) | [Verificacion E2E ->](07-verificacion-e2e.md)

Rama `fix/admin-session-cors-email-metrics` desde `dev`. Cada commit deja el
repo verde (lint + typecheck + tests del scope). Orden por riesgo creciente.

1. `docs(specs): plan 4 bug-fixes admin + backend`
   - Crea `docs/specs/admin-session-cors-email-metrics/`.

2. `fix(admin): oculta el nav-item metrics hasta b-analytics-api`
   - Bug 4: `nav-items.ts` + `nav-items.test.ts`. [AC-12]
   - Verificar: `pnpm --filter @portfolio/admin test` + `build`.

3. `fix(admin): retiene el redirect durante el bootstrap de sesion`
   - Bug 1: store + use-auth-timer + use-auth-bootstrap + use-protected-route
     + auth-guard + tests. [AC-1..AC-4]
   - Verificar: `pnpm --filter @portfolio/admin test` + `typecheck`.

4. `fix(cors): permite el header Authorization en el preflight y respuestas`
   - Bug 2: `cors.py` + `provisioner.py` + tests (mismo commit, sincronizados).
     [AC-5/6]
   - Verificar: `serverless tests --type=unit --shared` +
     `test_runner --module=devtools --type=unit`.

5. `feat(auth): unifica magic-link + code en un solo email`
   - Bug 3: email_dispatch_service + 3 controllers + email_config + 4 templates
     + tests. [AC-7..AC-11]
   - Verificar: `serverless tests --type=coverage --lambda=auth` (>=80%).

6. `test(specs): verificacion E2E + limpieza del plan`
   - Fase 07 + `git rm -r docs/specs/admin-session-cors-email-metrics/`.

Un solo PR `fix/admin-session-cors-email-metrics -> dev` (merge commit).

## PR (body, 4 secciones)

- **Problema**: los 4 bugs (1 sesion, 2 CORS, 3 email, 4 /metrics).
- **Solucion**: paralela a Problema (D1..D4 de
  [01-contexto-y-decision.md](01-contexto-y-decision.md)).
- **Como probar**: la bateria de [07-verificacion-e2e.md](07-verificacion-e2e.md)
  (Partes A/B local + Parte C post-deploy).
- **TODO**: vacio (o lo que escape del scope).
