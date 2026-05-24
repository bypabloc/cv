# 08 — Verificacion E2E iterativa (fase final)

> Bateria de cierre del plan. Ultima fase, ultimo commit (commit 12).
> "No parar hasta que funcione": ejecutar -> si falla, diagnosticar ->
> corregir -> re-ejecutar la suite -> repetir. El `git push` + PR SOLO
> ocurre cuando esta bateria pasa entera en verde.

## Parte A — Refactor de tests

Antes de la bateria de comandos, validar que ningun test viejo quedo
referenciando codigo eliminado/movido:

```bash
# Ningun test apunta a env vars hardcoded de prod
rg -l "the-full-stack.com" packages/ tests/ apps/ \
  | grep -v node_modules | xargs grep -l "expect\|assert\|toBe\|toContain" 2>/dev/null \
  | head -20
# Revisar manualmente: cada match debe ser un test que valida prod
# (caso valido) o un test que olvido actualizarse (a corregir).

# Tests nuevos estan en la ruta correcta segun convencion
test -d packages/ui/tests/build/ && echo "OK: build-test creado"
test -f packages/app-shared/tests/unit/lib/validate-build-env.test.ts \
  && echo "OK: unit test del guard"

# Barrido: ninguna referencia residual al patron viejo (TrackingPixel
# silenciandose con if (apiEndpoint) — buscar el guard nuevo en su lugar)
rg -n "if \(host && apiEndpoint\)" packages/
# Debe quedar (el guard del modulo es a otro nivel) o reemplazado
# segun la implementacion final.
```

## Parte B — Bateria de comandos reales

Bucle iterativo: si CUALQUIER comando falla -> diagnosticar -> arreglar
-> volver al inicio de la bateria.

```bash
# ============================================================
# 1. Lint global (Biome)
# ============================================================
pnpm exec biome check .
# Esperado: 0 errores

# ============================================================
# 2. Typecheck global
# ============================================================
pnpm exec tsc --noEmit
pnpm exec astro check  # por cada app, recursivo
# Esperado: 0 errores

# ============================================================
# 3. Unit tests packages
# ============================================================
pnpm exec vitest run
# Esperado: TODOS los tests verdes, incluyendo:
#   - packages/app-shared/tests/unit/lib/validate-build-env.test.ts
#   - packages/ui/tests/unit/*
# Coverage per-file >= 80% en archivos modificados

# ============================================================
# 4. Build-test (Capa B de Fase 1)
# ============================================================
pnpm --filter @portfolio/ui exec vitest run tests/build/
# Esperado: 3 tests verdes
#   - data-api-endpoint matchea PUBLIC_API_ENDPOINT
#   - dropdown hrefs NO apuntan a prod cuando BASE_DOMAIN=dev
#   - build sin PUBLIC_API_ENDPOINT FALLA

# ============================================================
# 5. Reproducir el bug original — DEBE FALLAR ahora
# ============================================================
env -u PUBLIC_API_ENDPOINT pnpm --filter @portfolio/hub run build 2>&1 \
  | grep -q "PUBLIC_API_ENDPOINT vacio" \
  && echo "OK: guard atrapa el escenario CI sin env vars" \
  || (echo "FAIL: el build paso silenciosamente" && exit 1)

# ============================================================
# 6. Build completo con env vars correctas
# ============================================================
BASE_DOMAIN=portfolio.dev.the-full-stack.com \
  BASE_SCHEME=https \
  PUBLIC_API_ENDPOINT=https://api.portfolio.dev.the-full-stack.com \
  PUBLIC_TURNSTILE_SITEKEY=0x0000000000000000_dev_test \
  pnpm run build
# Esperado: 6 apps builderan sin error

# Verificar dist hub tiene el atributo correcto
grep -qF 'data-api-endpoint="https://api.portfolio.dev.the-full-stack.com"' \
  apps/hub/dist/index.html \
  && echo "OK: hub dist tiene data-api-endpoint"

# Verificar dropdown apunta a dev
grep -q 'href="https://fintech.portfolio.dev.the-full-stack.com"' \
  apps/hub/dist/index.html \
  && echo "OK: hub dist dropdown apunta a dev"

# Verificar NINGUN niche dist apunta a prod
for niche in generic hub fintech architect leader vibe; do
  if grep -qE 'href="https://[a-z]+\.portfolio\.the-full-stack\.com' \
       apps/${niche}/dist/index.html; then
    echo "FAIL: $niche dist contiene hrefs a prod"
    exit 1
  fi
done
echo "OK: ningun niche apunta a prod"

# ============================================================
# 7. Devtools unit tests (github_sync)
# ============================================================
python devtools/run.py test_runner --module=devtools --type=unit
# Esperado: TODOS verdes, incluyendo test_github_sync

# ============================================================
# 8. github_sync dry-run contra el .dev local
# ============================================================
python devtools/run.py github_sync --env=dev --dry-run
# Esperado: reporte SKIP/PUSH/MISSING claro, SIN valores en stdout

# ============================================================
# 9. github_sync real contra GH (requiere gh auth)
# ============================================================
python devtools/run.py github_sync --env=dev
# Esperado: las GH Variables existen post-comando
gh variable list --env dev | grep -E "BASE_DOMAIN|PUBLIC_API_ENDPOINT|PUBLIC_TURNSTILE_SITEKEY"
# Debe listar las 3+ variables sincronizadas

# Repetir para stage y prod cuando se este listo
# python devtools/run.py github_sync --env=stage
# python devtools/run.py github_sync --env=prod

# ============================================================
# 10. Workflow validation (sin push real todavia)
# ============================================================
# Si actionlint esta disponible:
actionlint .github/workflows/deploy-apps.yml
actionlint .github/workflows/ci.yml
# Esperado: 0 errores

# ============================================================
# 11. Claude config tests (rule nueva)
# ============================================================
claude --permission-mode bypassPermissions \
  --disallowedTools "WebSearch" "WebFetch" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --output-format json \
  -p "como sincronizo las variables del client a github environments" \
  | jq -r '.num_turns'
# Esperado: num_turns > 1 (rule client-env-sync invocada)
```

## Cierre del plan

Cuando los 11 comandos pasan en VERDE, ejecutar el commit 12:

```bash
# 1. Eliminar la carpeta del spec (es efimera, ya implementada)
git rm -r docs/specs/build-env-vars-per-env/

# 2. Commit final
git commit -m "$(cat <<'EOF'
chore(specs): cierra el plan build-env-vars-per-env

- Plan implementado en 11 commits previos
- Bateria E2E (08-verificacion-e2e.md) pasa entera en verde
- TrackingPixel ya no se autodesactiva en silencio
- Dropdown "Otras vistas" linkea al hostname del env correcto
- GitHub Environments dev/stage/prod sincronizados con docker/env/client/
EOF
)"

# 3. Push y PR
git push -u origin feature/build-env-vars-per-env
gh pr create --base dev --head feature/build-env-vars-per-env \
  --title "feat(deploy): env vars por env + regression guards" \
  --body "$(cat <<'EOF'
## Problema

1. El dropdown "Otras vistas" linkea a produccion desde dev/stage
   (verificado en HTML live).
2. El endpoint /track NUNCA se ejecuta en dev/stage: el
   <div id="cf-tracking-pixel"> queda sin data-api-endpoint porque
   el build no recibe PUBLIC_API_ENDPOINT, y el script se
   autodesactiva en silencio.
3. canonical/og:url/JSON-LD Person.url apuntan a prod desde dev.

Root cause: deploy-apps.yml builda sin pasar NINGUNA env var del env
destino. SITE_URLS y `import.meta.env.*` caen a defaults de prod.

## Solucion

1. Regression guards (3 capas) que cortan el bug en seco:
   - A: TrackingPixel.astro lanza error si PUBLIC_API_ENDPOINT vacio
        o no matchea BASE_DOMAIN. El build CI falla antes de subir.
   - B: build-test en packages/ui/tests/build/ verifica que el dist
        contiene los valores esperados.
   - C: smoke test post-deploy con curl + grep al hostname dev/stage.

2. Script devtools/github_sync sincroniza docker/env/client/.{env}
   a GitHub Environment Variables (dev/stage/prod). Hermetico
   (no imprime valores), idempotente.

3. deploy-apps.yml declara environment: <stage> y consume las GH
   Variables en env: del step de build. Las 6 astro.config.ts usan
   buildSiteUrl() en vez del hardcode prod.

4. Docs actualizadas (pages-config.md, ci-cd-pipeline.md, rule
   nueva client-env-sync.md).

## Como probar

Bateria completa: ver docs/specs/build-env-vars-per-env/08-verificacion-e2e.md
(eliminada en este PR como cierre del plan).

Verificaciones criticas post-merge:

- curl https://fintech.portfolio.dev.the-full-stack.com/
  -> grep cf-tracking-pixel: contiene data-api-endpoint
  -> grep dropdown hrefs: apuntan a *.portfolio.dev.*
- POST /track aparece en DevTools al cargar cualquier subdominio dev

## TODO (fuera de scope)

- Splittear `_headers` CSP `connect-src` por env (hoy esta sobre-
  permisivo con los 3 hostnames de API).
- Migrar `TURNSTILE_SECRET_KEY` a Environment Secrets (hoy vive en
  SSM AWS — ya es seguro, no urge).
EOF
)"
```

## Regla de cierre

- El `git push` y `gh pr create` SOLO se ejecutan cuando los 11
  comandos de la Parte B pasan en VERDE.
- Si la bateria deja de pasar despues de un commit nuevo: revertir o
  arreglar el commit, NO bypasear.
- Si un comando es flaky (E2E contra red): re-ejecutar; si persiste,
  reportar como bug del plan y NO cerrar.
