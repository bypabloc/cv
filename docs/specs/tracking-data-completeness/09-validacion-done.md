# 09. Validacion y Definition of Done

> Seccion 12 del [plan-format](../../../.claude/rules/plan-format.md).
> Dos checklists: pre-implementacion (antes de empezar a codear) y
> Definition of Done (cierre del plan).

[← 08](08-verificacion-e2e.md) · [README](README.md) · [10 →](10-view-transitions-design.md)

## Pre-implementacion

Marcar TODO antes de pasar de la fase "Plan" a "Implement"
([plan-format.md](../../../.claude/rules/plan-format.md), "Workflow").

### Setup local

- [ ] Branch `feature/tracking-data-completeness` creada desde `dev`
      y commit C1 (carpeta del plan) hecho.
- [ ] `git status` working tree limpio (no hay cambios sin commit).
- [ ] `pnpm install` corre sin warnings.
- [ ] `python devtools/run.py docker up --env=local` levanta los 6
      sitios + nginx + db local.
- [ ] AWS auth: `aws sts get-caller-identity --profile tfs-dev`
      retorna account `637423614564`.
- [ ] gh CLI: `gh auth status` ok (necesario para C13+ trigger CI).

### Conocimiento del codigo

- [ ] Leida la rule [lambda-controller.md](../../../.claude/rules/lambda-controller.md)
      (estructura de Lambdas, ciclo `preload->validate->execute`).
- [ ] Leida la rule [neon-management.md](../../../.claude/rules/neon-management.md)
      (operacion DB: migrations via Lambda `db`, branches Neon).
- [ ] Leida la rule [serverless-secrets.md](../../../.claude/rules/serverless-secrets.md)
      (SSM patterns, KMS, IAM scopes).
- [ ] Leida la rule [ci-cd-pipeline.md](../../../.claude/rules/ci-cd-pipeline.md)
      (OIDC + S3 state, queue por env).
- [ ] Auditado el codigo actual:
      - [ ] `packages/ui/src/lib/track-event.ts` (frontend tracking actual)
      - [ ] `serverless/lambda/services/tracking_pixel/core/models/tracking.py`
      - [ ] `serverless/lambda/shared/lambda_kit/http_dispatch.py`
      - [ ] `serverless/lambda/shared/observability/ua_parser.py`
      - [ ] `packages/ui/src/components/NicheDropdown.astro`
      - [ ] `packages/ui/src/components/MobileNavDrawer.astro`

### TDD setup

- [ ] Tests rojos escritos para AC-1 antes de implementar el Pydantic
      required (commit C6). Confirmado que fallan con el codigo actual.
- [ ] Tests rojos escritos para AC-9 (utm parser) antes de implementar
      `build-track-payload.ts` (commit C9).
- [ ] Tests rojos escritos para AC-12 (NicheDropdown AbortController)
      antes de refactorizar (commit C11).

### Fixtures + dependencias

- [ ] `ua-parser` agregado a `serverless/lambda/shared/observability/pyproject.toml`
      y `uv.lock` actualizado.
- [ ] Branch Neon de prueba creada para validar migrations
      (`neon branches create --name test-drop-stream-event-id --parent main`).
- [ ] DNS TTL del CNAME `api.portfolio.*` bajado a 60s en Cloudflare
      ≥10 min antes de Step 7 del [08](08-verificacion-e2e.md) (NO
      antes; solo en la ventana del deploy real, ver C14).

### Coordinacion humana

- [ ] Ventana del deploy a prod confirmada (fuera de hora pico).
- [ ] El usuario aprobo:
      - [x] PK actual `(session_id, page_id, created_at)` se mantiene.
      - [x] Custom domains a Edge-Optimized en los 3 envs.
      - [x] `ua-parser` reemplaza regex custom.
      - [x] Truncate `tracking_events` en dev Y prod.
      - [x] View transitions: fade 300ms + 3 shared elements + stagger
            40ms + strict reduced-motion.
      - [x] Navbar fix incluido (NicheDropdown + MobileNavDrawer).
      - [x] Tests E2E del navbar con breakpoints.

## Definition of Done (cierre del plan)

Marcar TODO para cerrar el PR. Cualquier item sin marcar → no se
mergea.

### Codigo

- [ ] Todos los AC (AC-1 .. AC-14) tienen al menos UN test que los
      cubre y pasa (mapeo en [03](03-tests-requeridos.md) §6.F).
- [ ] Coverage per-file ≥80% en TODOS los archivos
      modificados/creados (frontend + Lambda + shared + devtools).
- [ ] `pnpm exec biome check .` cero errors.
- [ ] `pnpm exec tsc --noEmit` cero errors.
- [ ] `pnpm exec astro check` cero errors.
- [ ] `pnpm run build` exitoso en las 6 apps (Astro static output).
- [ ] `python -m compileall -q serverless/` exit 0.
- [ ] `pnpm exec vitest run` cero rojos.
- [ ] `python devtools/run.py serverless tests --type=coverage --lambda=tracking_pixel`
      verde + coverage ≥80%.
- [ ] `python devtools/run.py serverless tests --type=coverage --shared`
      verde + coverage ≥80%.
- [ ] `python devtools/run.py test_runner --module=devtools --type=unit`
      verde.

### Infra

- [ ] `aws apigateway get-domain-name --domain-name api.portfolio.dev.the-full-stack.com --profile tfs-dev`
      → `endpointConfiguration.types[0] === 'EDGE'`.
- [ ] Idem para `api.portfolio.stage` (cuando aplique).
- [ ] Idem para `api.portfolio` (prod).
- [ ] DNS CNAME apunta a la nueva distribucion CloudFront en los 3
      envs.
- [ ] `https://api.portfolio.dev.the-full-stack.com/track` responde
      HTTP 400 (validation) con payload vacio — NO 502/timeout.
- [ ] `https://api.portfolio.stage.the-full-stack.com/track` idem.
- [ ] `https://api.portfolio.the-full-stack.com/track` idem.

### Backend

- [ ] Migration `b2c3d4e5f6a7_drop_stream_event_id` aplicada en dev,
      stage, prod. `alembic current` retorna esa revision en los 3.
- [ ] `psql -c "SELECT column_name FROM information_schema.columns
      WHERE table_name='tracking_events' AND column_name='stream_event_id';"`
      retorna 0 rows en los 3 envs.
- [ ] `tracking_events` truncado en dev y prod (count = 0 antes del
      smoke E2E).
- [ ] Smoke E2E: 1 navegacion real desde el browser inserta 1 fila en
      Neon con las 11 columnas populadas (page_*, utm_*, viewport_*,
      country, browser_version) en los 3 envs.

### Frontend

- [ ] `<ClientRouter />` presente en `BaseLayout.astro` (las 6 apps lo
      consumen).
- [ ] Audit de `transition:name`: solo `hero-identity` y
      `project-{slug}` (dinamico). Cero colisiones.
- [ ] `prefers-reduced-motion: reduce` desactiva todas las animaciones
      (verificado en DevTools).
- [ ] NicheDropdown: 3 navegaciones consecutivas → toggle sigue
      funcionando, sin listeners fugados.
- [ ] MobileNavDrawer: viewport 375px → `<details>` cerrado por
      default → expande al click → resetea al cerrar drawer.

### Tests E2E (Playwright)

- [ ] `tests/feature/specs/tracking-pageview.spec.ts` verde en las 6 apps.
- [ ] `tests/feature/specs/view-transitions.spec.ts` verde.
- [ ] `tests/feature/specs/navbar.spec.ts` verde (desktop + mobile +
      breakpoint resize) en las 6 apps.

### Documentacion

- [ ] El plan se elimino via `git rm -r docs/specs/tracking-data-completeness/`
      en el commit C15.
- [ ] Decisiones que sobreviven al plan (si las hay) promovidas a
      `.claude/rules/` o `docs/` antes del delete:
      - [ ] Politica de Edge-Optimized: ¿documentar en
            [.claude/rules/serverless-secrets.md](../../../.claude/rules/serverless-secrets.md)?
            (probable NO — es config puntual, vive en
            `api_gateway/portfolio-api.yaml`).
      - [ ] Patron AbortController para listeners en componentes con
            re-mount via ClientRouter: ¿documentar en
            [.claude/rules/astro-landing.md](../../../.claude/rules/astro-landing.md)?
            (recomendado SI — es un patron reusable).
      - [ ] View transitions design + 4 patrones: ¿promover el
            capitulo [10](10-view-transitions-design.md) a
            `docs/design-system/view-transitions.md`? (recomendado SI
            — es referencia permanente).

### PR

- [ ] PR creado: `feature/tracking-data-completeness -> dev`.
- [ ] PR body tiene las 4 secciones del template (Problema, Solucion,
      Como probar, TODO). Sin atribucion IA.
- [ ] Reviewer puede correr el "Como probar" siguiendo Steps 7-12 de
      [08](08-verificacion-e2e.md).
- [ ] CI verde: lint + typecheck + build.
- [ ] Branch flow guard verde (PR target es `dev`).
- [ ] PR mergeado con `--merge` (NUNCA `--squash` ni `--rebase` —
      regla del proyecto, ver
      [git-workflow.md](../../../.claude/rules/git-workflow.md)).
- [ ] Feature branch borrada (`--delete-branch` en `gh pr merge`).

### Post-merge

- [ ] `git checkout dev && git pull` aplica los 15 commits limpios.
- [ ] Promocion `dev -> stage` planificada (PR aparte).
- [ ] Promocion `stage -> main` planificada (PR aparte).
- [ ] En main: re-ejecutar Steps 7-15 de [08](08-verificacion-e2e.md)
      para los envs que aun no se apliquen (si C14 solo cubrio dev por
      bandwidth).

## Riesgos de incumplimiento (que invalidan el cierre)

- ❌ Algun AC sin test que lo cubra → reabrir, escribir test, repetir.
- ❌ Tests rojos en Playwright al cierre → no mergear, debug iterativo.
- ❌ Coverage < 80% en archivo modificado → agregar tests.
- ❌ Custom domain Regional en algun env → recrear, repetir Step 7.
- ❌ `stream_event_id` aun presente en alguna fila o columna → corregir
      migration, repetir.
- ❌ NicheDropdown con bug visible tras navegacion → debug
      AbortController, repetir.
- ❌ Atribucion IA detectada en algun commit/PR → reescribir, history
      rebase (NO en branch publica si ya hubo otros mergers — usar
      revert + nuevo commit).

---

Fin del plan. Volver al [README](README.md).
