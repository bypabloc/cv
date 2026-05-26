# 12 — Verificacion E2E iterativa (fase final)

> **Anterior**: [11-paralelizacion-worktrees.md](11-paralelizacion-worktrees.md)
>
> **Cubre**: AC-12
>
> **Objetivo**: bucle "no parar hasta que funcione" — ejecutar la
> bateria completa, si algo falla diagnosticar + corregir + repetir.
> Es el gate del PR a dev.

## Parte A — Refactor de tests

Antes de la bateria, validar que ningun test viejo referencia codigo
eliminado o renombrado.

### A.1 Barrido global de strings sensibles

```bash
# La URL canonica RFC 9727 sigue funcionando (rewrite 200), pero el
# archivo real es .json. Verificar que los tests usan el path correcto:
rg -l "well-known/api-catalog" packages/ apps/ tests/ devtools/
# Para cada match, decidir si debe quedar como '/.well-known/api-catalog'
# (URL publica, validar redirect) o '/.well-known/api-catalog.json' (path
# real del file).
```

### A.2 Tests del ai_audit (devtools)

```bash
# El validator de api-catalog en devtools/ai_audit/tools/validators.py
# probablemente tiene un fetch a /.well-known/api-catalog. Verificar que
# parsea JSON ahora que el rewrite 200 esta activo, no HTML.
rg -n "api-catalog" devtools/ai_audit/
# Si hay un test fixture que asume HTTP 404 o HTML, actualizarlo.
```

### A.3 Tests del paquete MCP

```bash
# Verificar coverage del paquete nuevo
pnpm --filter @portfolio/mcp exec vitest run --coverage --reporter=verbose

# Verificar coverage del paquete markdown-export
pnpm --filter @portfolio/markdown-export exec vitest run --coverage --reporter=verbose
```

Cero tests rojos. Coverage >= 80% per-file en los archivos modificados.

## Parte B — Bateria de comandos reales

### B.1 Lint global

```bash
pnpm exec biome check .
```

Cero errores. Si hay warnings nuevos, justificar o silenciar via
overrides legitimos.

### B.2 Typecheck global

```bash
pnpm exec tsc --noEmit
pnpm exec astro check  # o pnpm --recursive --filter "@portfolio/*" run typecheck
```

Cero errores.

### B.3 Unit tests + coverage

```bash
pnpm run test
# Recursivo sobre todos los packages

pnpm --recursive --filter "@portfolio/seo" --filter "@portfolio/mcp" --filter "@portfolio/markdown-export" exec vitest run --coverage
# Coverage >= 80% per-file en los archivos modificados
```

### B.4 Build de las 6 apps

```bash
pnpm run build
```

Cero errores. Para cada app, verificar:

```bash
for app in architect fintech generic hub leader vibe; do
  echo "=== $app ==="
  test -f apps/$app/dist/.well-known/api-catalog.json || echo "FALTA api-catalog.json"
  test -f apps/$app/dist/.well-known/mcp/server-card.json || echo "FALTA mcp/server-card.json"
  test -f apps/$app/dist/index.md || echo "FALTA index.md"
  test -f apps/$app/dist/_headers || echo "FALTA _headers"
  test -f apps/$app/dist/_redirects || echo "FALTA _redirects"
  test -f apps/$app/functions/mcp.ts || echo "FALTA functions/mcp.ts"
done
```

Cero "FALTA".

### B.5 Smoke local con wrangler pages dev

```bash
# Verificar UN niche localmente (no los 6 — toma tiempo)
npx wrangler pages dev apps/generic/dist --port 8788 &
WRANGLER_PID=$!
sleep 5

# AC-1: api-catalog via URL canonica RFC 9727
test "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8788/.well-known/api-catalog)" = "200"
test "$(curl -s http://localhost:8788/.well-known/api-catalog | jq -r '.linkset[0].anchor')" = "https://the-full-stack.com"

# AC-2: api-catalog directo
test "$(curl -s http://localhost:8788/.well-known/api-catalog.json | jq -r '.linkset[0].anchor')" = "https://the-full-stack.com"

# AC-3 / AC-5: .md gemelo existe
test "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8788/index.md)" = "200"

# AC-7: MCP initialize
curl -X POST http://localhost:8788/mcp -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  | jq .result.protocolVersion | grep -q '2025-11-25'

# AC-8: MCP tools/list devuelve 3 tools
curl -X POST http://localhost:8788/mcp -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  | jq '.result.tools | length' | grep -q '^3$'

# AC-9: get_cv_section
curl -X POST http://localhost:8788/mcp -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_cv_section","arguments":{"section":"about"}}}' \
  | jq .result.content[0].text | grep -q '^"# About'

# AC-11: MCP server card valido
curl -s http://localhost:8788/.well-known/mcp/server-card.json | jq -r .name | grep -q '^portfolio-mcp$'

kill $WRANGLER_PID
```

Si cualquier `test`/`grep` falla → diagnosticar + corregir + repetir.

### B.6 Pre-push hook local (full quality gates)

```bash
git push --dry-run origin feature/ai-audit-level-3-4
# El hook .git-hooks/pre-push ejecuta lint + typecheck + unit + coverage
# + build + (E2E si aplica). NO usar --no-verify.
```

### B.7 Validacion de skills/rules (claude -p)

Ejecutar la matriz de 5 prompts de Fase 3 ([09-fase-3-validar-skills.md](09-fase-3-validar-skills.md))
y registrar resultado en el body del commit final:

```text
Matriz claude -p (5 prompts):
1. cuanto deberia esperar de score isitagentready: num_turns=N PASS
2. /.well-known/openid-configuration: num_turns=N PASS (no recomienda)
3. API Catalog is not valid JSON: num_turns=N PASS (menciona SPA fallback)
4. configurar Astro 6 con Tailwind: num_turns=1 PASS (no dispara ai-audit)
5. agent-native level 5: num_turns=N PASS (explica ceiling)
```

5/5 PASS obligatorio.

### B.8 ai_audit local contra dev (NO contra prod aun)

Despues de mergear a dev y esperar el deploy:

```bash
# El comando default audita prod. Para dev:
./devtools/.venv/bin/python devtools/run.py ai_audit --env=dev
```

Resultados esperados contra dev:
- isitagentready: probablemente 2/5 (dev bloquea AI crawlers por diseno
  via robots.txt — esto es esperable, NO un fallo)
- lighthouse_psi: 95-100/100 (sin cambio significativo)
- validators: **mejorado** vs baseline; api-catalog ahora cuenta como
  pass (no fail por "no JSON")
- MCP server card detectable

Si validators NO mejora vs baseline → diagnostico (probablemente el
archivo `.json` no se sube; verificar el dist del deploy).

## Bucle "no parar hasta que funcione"

```text
1. Ejecutar B.1 (lint)
   ├─ verde → seguir
   └─ rojo → corregir, volver a 1

2. Ejecutar B.2 (typecheck)
   ├─ verde → seguir
   └─ rojo → corregir, volver a 1 (lint puede romperse con el fix)

3. Ejecutar B.3 (tests)
   ├─ verde + coverage OK → seguir
   └─ rojo → corregir, volver a 1

4. Ejecutar B.4 (build)
   ├─ verde + assets OK → seguir
   └─ rojo o assets faltantes → corregir, volver a 1

5. Ejecutar B.5 (wrangler smoke)
   ├─ todos los curl asserts OK → seguir
   └─ falla → corregir (puede ser tests, builder, function) → volver a 1

6. Ejecutar B.6 (pre-push hook)
   ├─ verde → seguir
   └─ rojo → corregir, volver a 1

7. Ejecutar B.7 (claude -p)
   ├─ 5/5 PASS → seguir
   └─ falla → ajustar rule/skill, volver a 1

NUNCA "marcar listo" con un comando fallando.
NUNCA pushear con tests rojos.
```

## Gate de cierre

El commit 13 (cierre del plan) SOLO se crea cuando:

- [ ] B.1 (lint) verde
- [ ] B.2 (typecheck) verde
- [ ] B.3 (unit tests + coverage >= 80% per-file) verde
- [ ] B.4 (build) verde + los 6 assets generados por niche
- [ ] B.5 (wrangler smoke) los 7 curl asserts pasan
- [ ] B.6 (pre-push hook completo) verde
- [ ] B.7 (claude -p) 5/5 PASS
- [ ] Plan eliminado: `git rm -r docs/specs/ai-audit-level-3-4/`

## Post-merge a dev

Despues del merge:

1. Esperar deploy-apps a dev OK.
2. Correr ai_audit contra dev: validar que el archivo `.well-known/api-catalog.json`
   se sirve y el MCP server card aparece.
3. Promover dev -> stage (PR + merge) -> esperar deploy stage.
4. Promover stage -> main (PR + merge) -> esperar deploy prod.
5. Correr ai_audit contra prod (default del comando):
   ```bash
   ./devtools/.venv/bin/python devtools/run.py ai_audit
   ```
6. **AC-12**: validar que:
   - `isitagentready >= 3/5` en al menos 3 niches
   - `validators >= 95/100` en los 6 niches
   - `avg global >= 85/100`
   - El top 5 fixes NO incluye "API Catalog is not valid JSON" ni "MCP
     Server Card not found"

Si AC-12 NO se cumple → diagnostico iterativo (puede requerir un
plan-2 con ajustes finos). Documentar en `MEMORY.md` que items
quedaron pendientes y por que.

## Que NO esta cubierto por esta verificacion

- **Cloudflare Transform Rule** (Fase 1C) — se valida MANUALMENTE
  post-deploy con `curl -H 'Accept: text/markdown'`. NO se puede
  validar localmente con wrangler.
- **Costo recurrente del MCP server** — depende del trafico real;
  evaluar despues de 30 dias en prod.
