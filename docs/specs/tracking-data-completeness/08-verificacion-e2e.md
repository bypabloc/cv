# 08. Verificacion E2E iterativa (fase final)

> Seccion 11 del [plan-format](../../../.claude/rules/plan-format.md).
> SIEMPRE el ultimo commit del plan. Gate del PR.

[← 07](07-paralelizacion-worktrees.md) · [README](README.md) · [09 →](09-validacion-done.md)

## Parte A — Refactor / cleanup de tests

Audit antes de la bateria final:

```bash
# 1. Cero referencias a stream_event_id en el repo
rg "stream_event_id" serverless/ packages/ | wc -l
# Esperado: 0

# 2. Cero referencias al regex parser viejo
rg "_PARSER_REGEX|_UA_REGEX" serverless/lambda/shared/observability/ | wc -l
# Esperado: 0

# 3. Cero data-bound (legacy del NicheDropdown)
rg "data-bound" packages/ui/src/components/NicheDropdown.astro | wc -l
# Esperado: 0

# 4. transition:name auditado (solo hero-identity y project-{slug})
rg "transition:name" apps/ packages/ | awk -F'"' '{print $2}' | sort -u
# Esperado:
#   hero-identity
#   project-{slug}   ← dinamico
#   (sin nombres ajenos al plan)

# 5. Tests nuevos en ruta correcta
ls packages/ui/tests/unit/lib/build-track-payload.test.ts \
   packages/ui/tests/unit/lib/stagger.test.ts \
   packages/ui/tests/unit/components/NicheDropdown.test.ts \
   packages/ui/tests/unit/components/MobileNavDrawer.test.ts \
   tests/feature/specs/tracking-pageview.spec.ts \
   tests/feature/specs/view-transitions.spec.ts \
   tests/feature/specs/navbar.spec.ts

# 6. Tests obsoletos eliminados
rg "test_parse_ua_regex_" serverless/lambda/shared/tests/ | wc -l
# Esperado: 0 (reemplazados por test_parse_ua_*.py y test_ua_parser_replaces_regex_*.py)
```

Si CUALQUIERA de los 6 audits falla → detener, investigar, corregir.

## Parte B — Bateria de comandos reales (bucle "no parar")

Ejecutar TODOS los comandos siguientes en orden. Si alguno falla:
diagnosticar → corregir → re-ejecutar la suite desde el comando que
fallo. **No se marca completa con un comando fallando, un test rojo
o coverage < 80%.**

### Step 1 — Lint + format

```bash
pnpm exec biome check .
```

Esperado: cero errors. Warnings de markdown lint (MD060) son OK
(estilisticos).

### Step 2 — Typecheck

```bash
pnpm exec tsc --noEmit
pnpm exec astro check
```

Esperado: cero errors en ambos.

### Step 3 — Unit tests + coverage

```bash
# Frontend
pnpm exec vitest run --coverage --coverage.thresholds.perFile=80

# Lambda
python devtools/run.py serverless tests --type=coverage --lambda=tracking_pixel
python devtools/run.py serverless tests --type=coverage --shared

# Devtools
python devtools/run.py test_runner --module=devtools --type=unit
```

Esperado: cero rojos. Coverage per-file ≥80%. Si falla coverage,
agregar tests al archivo afectado.

### Step 4 — Build

```bash
pnpm run build
```

Esperado: las 6 apps buildean sin errors. `dist/` poblado.

### Step 5 — Stack local

```bash
python devtools/run.py docker up --env=local
sleep 8  # esperar nginx + servicios

# Smoke manual (curl)
curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:9970/
curl -sS -o /dev/null -w "%{http_code}\n" http://hub.localhost:9970/
curl -sS -o /dev/null -w "%{http_code}\n" http://fintech.localhost:9970/
# Esperado: 200 en los 6 hosts
```

### Step 6 — Feature tests Playwright

```bash
python devtools/run.py test_runner --module=feature --type=feature --env=local
```

Esperado: cero rojos. Los 3 specs nuevos (tracking + view-transitions
+ navbar) pasan en las 6 apps. Si un spec es flaky, re-run; si
persiste, debug con `--debug` flag de Playwright.

### Step 7 — Apply infra a dev

```bash
export AWS_PROFILE=tfs-dev
python devtools/run.py serverless provision-infra --stage=dev --aws-profile=tfs-dev
```

Esperado:
- `apigateway delete-domain-name` + `apigateway create-domain-name`
  (endpointType EDGE) + `apigateway create-base-path-mapping` exitosos
- CloudFront distribution nueva propagada
- `aws apigateway get-domain-name --domain-name api.portfolio.dev.the-full-stack.com --profile tfs-dev` retorna `EDGE`

DNS check:
```bash
dig api.portfolio.dev.the-full-stack.com +short
# Esperado: CNAME apunta a la distribucion CF nueva
```

### Step 8 — Apply DB migration + truncate (dev)

```bash
python devtools/run.py serverless run --lambda=db --stage=dev \
  --event=events/migrate.json --aws-profile=tfs-dev
python devtools/run.py serverless run --lambda=db --stage=dev \
  --event=events/current.json --aws-profile=tfs-dev
# Esperado: revision = b2c3d4e5f6a7

python devtools/run.py serverless run --lambda=db --stage=dev \
  --event=events/truncate-tracking.json --aws-profile=tfs-dev
# Esperado: rows_deleted = N
```

### Step 9 — Deploy Lambda a dev

```bash
python devtools/run.py serverless deploy --lambda=tracking_pixel \
  --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless deploy --lambda=contact_form \
  --stage=dev --aws-profile=tfs-dev
```

Esperado: cada deploy verde, zip ≤50MB.

### Step 10 — Deploy apps a dev

Disparar el workflow `deploy-apps.yml` (o esperar el push automatico).
Esperar a que las 6 apps esten en CF Pages dev:

```bash
gh workflow run deploy-apps.yml --ref feature/tracking-data-completeness
sleep 90
curl -sS https://generic.portfolio.dev.the-full-stack.com/ | grep -o "data-api-endpoint=\"[^\"]*\""
# Esperado: data-api-endpoint="https://api.portfolio.dev.the-full-stack.com"
```

### Step 11 — Smoke E2E real en dev (browser)

Pasos manuales en Chromium con DevTools abierto:

1. Navegar a `https://portfolio.dev.the-full-stack.com/?utm_source=verify&utm_medium=plan`
2. Network tab: filtrar por `/track` → debe haber 1 request POST
3. Click "Request" → ver `Headers` → `cloudfront-viewer-country` presente
4. Click "Payload" → JSON body con TODOS los 11 campos no vacios:
   `page_path, page_url, page_title, referrer, utm_source=verify, utm_medium=plan, utm_campaign='', utm_content='', viewport_width, viewport_height, devicePixelRatio`
5. Navegar a `/projects` (click en nav) → ver fade transition (cross-fade 300ms)
6. Network tab: debe haber un nuevo POST `/track` (con `page_path=/projects`)
7. Test navbar:
   - Desktop: click "Otras vistas" → dropdown abre. Click fuera → cierra. Repetir 3 veces.
   - Ctrl+Shift+M (mobile emulator) → 375px width → hamburger visible
   - Click hamburger → drawer abre con "Otras vistas" como `<details>` cerrado
   - Click summary → expande con 5 items
   - Cerrar drawer → reabrir → `<details>` cerrado de nuevo
8. Theme toggle: click → circular clip-path expansion
9. `prefers-reduced-motion: reduce` (DevTools → Rendering): repetir nav → sin animacion

### Step 12 — Verificar en Neon dev

```bash
DB_URL_DEV="$(grep -m1 '^DB_URL=' docker/env/server/.dev | cut -d= -f2-)"
psql "$DB_URL_DEV" -c "SELECT
  page_path, page_url, page_title, referrer,
  utm_source, utm_medium, utm_campaign, utm_content,
  viewport_width, viewport_height,
  country, browser, browser_version, os, device_type,
  created_at
FROM tracking_events
ORDER BY created_at DESC
LIMIT 3;"
```

Esperado: las 3 filas mas recientes traen TODAS las 11 columnas
populadas (country=ISO-2, browser_version=numero real, etc.).

```bash
psql "$DB_URL_DEV" -c "SELECT column_name FROM information_schema.columns WHERE table_name='tracking_events' AND column_name='stream_event_id';"
# Esperado: 0 rows (columna eliminada)
```

### Step 13 — Repeat steps 7-12 para stage

Mismas operaciones con `--stage=stage --aws-profile=tfs-stage` y
hostname `portfolio.stage.the-full-stack.com`.

### Step 14 — Repeat steps 7-12 para prod

Mismas operaciones con `--stage=prod --aws-profile=tfs-prod` y
hostname `portfolio.the-full-stack.com`.

**Cuidado** en prod:
- Bajar DNS TTL a 60s ≥10 min antes de Step 7.
- Coordinar con el horario fuera de pico.
- Tener listo el rollback (state local backup en S3 versioned).
- Verificar smoke E2E (Step 11) inmediatamente despues del Step 7
  prod — confirma que el endpoint sigue respondiendo.
- Subir DNS TTL a 3600s al cerrar.

### Step 15 — DNS TTL restore

```bash
# En Cloudflare DNS, subir el TTL del CNAME api.portfolio.* de vuelta a auto/3600s.
# Idealmente via API:
#   curl -X PATCH https://api.cloudflare.com/.../dns_records/<id> -H "Authorization: Bearer <token>" \
#     -d '{"ttl":3600}'
```

## Bucle "no parar hasta que funcione"

```text
loop:
  ejecutar la bateria (Steps 1-15)
  if cualquier_falla:
    diagnosticar (logs, gh run view, aws cli, psql)
    corregir codigo o config
    commit del fix dentro del plan
    goto loop (reinicia desde Step 1)
  else:
    salir del loop → ejecutar commit C15
```

## Gate de cierre

NO se hace `git push` ni se abre PR hasta que TODOS estos comandos
salen verdes:

- [ ] Step 1 — Biome (lint + format)
- [ ] Step 2 — TypeScript + Astro check
- [ ] Step 3 — Vitest + serverless tests (coverage per-file >=80%)
- [ ] Step 4 — Build 6 apps
- [ ] Step 5 — Docker stack levanta
- [ ] Step 6 — Playwright 3 specs en 6 apps
- [ ] Step 7 — Provision-infra EDGE en dev
- [ ] Step 8 — Migration dev aplicada (revision b2c3d4e5f6a7)
- [ ] Step 9 — Deploy Lambda dev
- [ ] Step 10 — Deploy apps dev verde
- [ ] Step 11 — Smoke browser dev (11 campos, view transitions, navbar)
- [ ] Step 12 — Neon dev: SELECT confirma columnas pobladas
- [ ] Step 13 — Stage: misma bateria verde
- [ ] Step 14 — Prod: misma bateria verde + DNS TTL gestion
- [ ] Step 15 — DNS TTL restaurado

Recien aqui:
```bash
git add docs/specs/tracking-data-completeness/  # (para el git rm del C15)
git commit -m "chore(plan): verificacion E2E final + cierre plan tracking-data-completeness"
# El commit C15 ya incluye el git rm -r de la carpeta del plan
git push -u origin feature/tracking-data-completeness
gh pr create --base dev --head feature/tracking-data-completeness ...
```

## "Como probar" del PR (reutilizable)

El PR body reutiliza Steps 7-12 (apply infra dev + migration + deploy
+ smoke browser + neon verify) como guia para el reviewer.

---

Siguiente: [09. Validacion + Definition of Done →](09-validacion-done.md)
