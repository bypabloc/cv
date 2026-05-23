# 10 — Verificacion E2E iterativa (fase final)

> Fase de cierre. Dos partes. Bucle "no parar hasta que funcione" antes
> de hacer push y abrir PR.

## Parte A — Refactor de tests (limpieza)

Verificar que NO quedan referencias a archivos eliminados/renombrados.

### Verificaciones obligatorias

1. **Cero tests viejos referenciando codigo eliminado.** En este plan,
   se elimina UNICAMENTE la carpeta `docs/specs/ai-readiness-2026/` al
   final — no se elimina codigo. Comando: ninguno necesario (no hay
   refactor de cosas viejas).

2. **Tests nuevos en ruta y convencion correctas.** Verificar:

   ```bash
   # Tests unit en packages
   eza -1 packages/seo/tests/unit/{data,lib}/*.test.ts
   eza -1 packages/app-shared/tests/unit/{middleware,components}/*.test.ts

   # Tests del Lambda nlweb
   eza -1 serverless/lambda/services/nlweb/tests/unit/test_*.py | head -15
   eza -1 serverless/lambda/services/nlweb/tests/integration/test_*.py

   # Tests del devtools scan
   eza -1 devtools/tests/agent_readiness_scan/test_*.py

   # Tests E2E
   eza -1 tests/feature/specs/ai-readiness/*.spec.ts
   ```

3. **Barrido global con `rg` para asegurar consistencia.** Cada uno
   debe dar **cero resultados**:

   ```bash
   # No quedan referencias a tools no definidas
   rg -l 'cv\.get_(awards|certificates|education|languages|references|publications)' packages/ apps/
   # ↑ esperado: 0 resultados (no exponemos esas tools al MCP)

   # No hay duplicacion de la lista de tools (debe leerse de MCP_TOOLS)
   rg -l "'cv\.get_experiences'" packages/ apps/ | wc -l
   # ↑ esperado: 1 (solo packages/seo/src/data/mcp-tools.ts)

   # No hay URLs hardcodeadas a api.portfolio.*
   rg -l 'api\.portfolio\.(dev\.|stage\.|the-full)' packages/ apps/ | grep -v 'api-base.ts'
   # ↑ esperado: 0 (todos via resolveApiBase)

   # Sin atribucion IA en codigo o docstrings
   rg -l 'Claude|Anthropic|Generated|Co-Authored-By' packages/ apps/ serverless/lambda/services/nlweb/
   # ↑ esperado: 0
   ```

## Parte B — Bateria de comandos reales (verificacion full)

Ejecutar la suite completa. Bucle hasta que TODO pase.

### B.1 — Lint + format

```bash
pnpm exec biome check .
# ↑ Cero errores ni warnings
```

### B.2 — Typecheck (TS + Astro)

```bash
pnpm exec tsc --noEmit
pnpm -r run typecheck
# ↑ Cero errores
```

### B.3 — Unit tests + coverage per-file >= 80%

```bash
# packages
python devtools/run.py test_runner --module=pkg-seo --type=coverage
python devtools/run.py test_runner --module=pkg-app-shared --type=coverage

# Lambda nlweb
python devtools/run.py serverless tests --type=coverage --lambda=nlweb

# devtools
python devtools/run.py test_runner --module=devtools --type=unit
```

Criterio: cada archivo modificado/creado >= 80% per-file.

### B.4 — Build estatico de las 6 apps

```bash
for app in generic hub fintech architect leader vibe; do
  echo "=== Building $app ==="
  pnpm --filter @portfolio/$app run build || exit 1
done

# Verificacion crucial: el adapter cloudflare NO debe romper el static
for app in generic hub fintech architect leader vibe; do
  if [ ! -f "apps/$app/dist/index.html" ]; then
    echo "ERROR: apps/$app/dist/index.html no existe (adapter rompio static)"
    exit 1
  fi
done

# Verificacion: los 3 endpoints existen en cada dist
for app in generic hub fintech architect leader vibe; do
  for f in api-catalog mcp/server-card.json agent-skills/index.json; do
    if [ ! -f "apps/$app/dist/.well-known/$f" ]; then
      echo "ERROR: apps/$app/dist/.well-known/$f no existe"
      exit 1
    fi
  done
done
```

### B.5 — Lambda nlweb compila + lint-deps

```bash
cd serverless/lambda/services/nlweb && uv sync --frozen
cd serverless/lambda/services/nlweb && uv run python -m compileall -q core
python devtools/run.py serverless lint-deps --lambda=nlweb
```

### B.6 — Stack local + E2E tests Playwright

```bash
python devtools/run.py docker up --env=local
python devtools/run.py test_runner --module=feature --type=feature --env=local
# ↑ Suite ai-readiness verde (well-known.spec, content-negotiation.spec, webmcp.spec)
```

### B.7 — Smoke tests manuales contra local

```bash
# Endpoints well-known
curl -s http://localhost:9970/.well-known/api-catalog | jq .
curl -s http://localhost:9970/.well-known/mcp/server-card.json | jq .
curl -s http://localhost:9970/.well-known/agent-skills/index.json | jq .

# Content-types correctos
for url in /.well-known/api-catalog /.well-known/mcp/server-card.json /.well-known/agent-skills/index.json; do
  ct=$(curl -sI "http://localhost:9970$url" | grep -i '^content-type:' | head -1)
  echo "$url -> $ct"
done

# Markdown negotiation
curl -sI -H 'Accept: text/markdown' http://localhost:9970/ | head -10
# ↑ Content-Type: text/markdown; charset=utf-8

# Link header en homepage
curl -sI http://localhost:9970/ | grep -i '^link:'
# ↑ debe contener rel api-catalog, mcp, agent-skills, service-doc

# Link header NO en /about
curl -sI http://localhost:9970/about | grep -i '^link:' && echo "ERROR: link header en /about" || echo "OK: no link en /about"
```

### B.8 — Lambda nlweb local + smoke

```bash
python devtools/run.py serverless run \
  --stage=local --lambda=nlweb --event=events/ask.json
# ↑ Output JSON con @context: https://schema.org, statusCode 200

python devtools/run.py serverless run \
  --stage=local --lambda=nlweb --event=events/ask_empty.json
# ↑ Output con numberOfItems: 0, statusCode 200 (no 404)
```

### B.9 — Repetir contra los 6 subdominios locales

```bash
# Patron, repetir para hub/fintech/architect/leader/vibe
for app in localhost hub.localhost fintech.localhost architect.localhost leader.localhost vibe.localhost; do
  echo "=== $app ==="
  curl -s "http://$app:9970/.well-known/mcp/server-card.json" | jq '.serverInfo.name'
done
# ↑ Cada uno debe imprimir 'the-full-stack-portfolio-<niche>'
```

## Bucle de correccion

Si CUALQUIER comando del B.1-B.9 falla:

1. Anotar el comando fallido y su output exacto
2. Diagnosticar la causa raiz (NO bypassear con `--no-verify`)
3. Aplicar fix en un commit nuevo (o ammend si el commit aun no esta
   en remote)
4. Volver al paso 1 — re-ejecutar TODA la bateria desde B.1
5. Repetir hasta que TODO esta en verde

**NUNCA** declarar la fase completa con un solo comando en rojo.

## Gate: push + PR

Cuando la Parte A y la Parte B.1-B.9 pasan completas en local:

1. Hacer commit 21 (`chore(specs): elimina docs/specs/ai-readiness-2026/`)
2. `git push origin feature/ai-readiness-2026`
3. `gh pr create --base dev --head feature/ai-readiness-2026 \
     --title "feat: ai-readiness 2026 (Cloudflare Agent Readiness 33 -> 75+)" \
     --body "$(cat <<'EOF'
   ## Problema

   El portfolio esta en 33/100 en Cloudflare Agent Readiness (scan 22-May-2026).
   Faltan 6 items del area API/MCP/Skill que las IAs en runtime usan para
   descubrir y consumir el sitio.

   ## Solucion

   5 fases en 21 commits:

   1. Endpoints `.well-known/{api-catalog, mcp/server-card.json, agent-skills/index.json}` tipados con Zod en cada una de las 6 apps Astro (via `@portfolio/seo` builders)
   2. Middleware Astro compartido para markdown content negotiation (`Accept: text/markdown`) + Link headers en homepage
   3. Lambda Python nueva `nlweb` con retrieval estructurado contra Neon, response schema.org JSON-LD, cache 5min
   4. Componente `WebMCPRegistration.astro` que registra las tools en `navigator.modelContext` en runtime con feature-detect
   5. Script `devtools/agent_readiness_scan` (Playwright + BeautifulSoup) que ejecuta scan oficial y publica JSON

   ## Como probar

   - Local: `python devtools/run.py docker up --env=local` y ejecutar la bateria de `docs/specs/ai-readiness-2026/10-verificacion-e2e.md` (resumida en CI)
   - Post-merge a stage: `python devtools/run.py agent_readiness_scan --url=https://stage.the-full-stack.com --min-score=70`

   ## TODO post-merge

   - [ ] Web Bot Auth signatures (HTTP message signatures) — defer porque requiere setup de keys
   - [ ] OAuth/OIDC discovery — NO aplica (sin APIs autenticadas)
   - [ ] Refactor: WebMCPRegistration lee MCP_TOOLS desde @portfolio/seo en lugar de duplicar
   EOF
   )"
   ```

## Verificacion final post-merge (manual)

Tras mergear el PR a `dev` y promover a `stage`:

```bash
# 1. Re-ejecutar el scan contra el dominio publico de stage
python devtools/run.py agent_readiness_scan \
  --url=https://stage.the-full-stack.com \
  --output=docs/progress/agent_readiness_stage_$(date +%s).json \
  --min-score=70

# 2. Scan de los 6 subdominios
python devtools/run.py agent_readiness_scan \
  --url=https://stage.the-full-stack.com \
  --url=https://hub.portfolio.stage.the-full-stack.com \
  --url=https://fintech.portfolio.stage.the-full-stack.com \
  --url=https://architect.portfolio.stage.the-full-stack.com \
  --url=https://leader.portfolio.stage.the-full-stack.com \
  --url=https://vibe.portfolio.stage.the-full-stack.com \
  --output=docs/progress/agent_readiness_stage_all_$(date +%s).json \
  --min-score=70
```

Resultado esperado: **TODOS** los 6 dominios con score >= 70 (Level 4
Agent-Ready o superior).

Si algun dominio falla:

- Diagnosticar (probablemente endpoint no deployo correctamente o
  middleware cloudflare no esta activo en ese subdominio)
- Aplicar fix en un PR de seguimiento (no en este)

## Definition of Done (checklist)

Pre-implementacion:

- [ ] AC-1 a AC-14 numerados (12 AC iniciales + AC-13/AC-14 del score)
- [ ] Tests TDD escritos antes de implementacion (BDD-style en `it()` / docstrings)
- [ ] Fixtures existen (seed CV en Neon dev)
- [ ] Dev server arranca limpio (`pnpm run dev`)
- [ ] No hay breaking changes en APIs publicas existentes (Lambda cv,
      contact_form, tracking_pixel siguen verdes)

Definition of Done (cierre del plan):

- [ ] Todos los AC tienen >= 1 test que los cubre y pasa
- [ ] Coverage per-file >= 80% en archivos modificados/creados
  - [ ] `packages/seo/` >= 80%
  - [ ] `packages/app-shared/` >= 80%
  - [ ] `serverless/lambda/services/nlweb/` >= 80%
  - [ ] `devtools/agent_readiness_scan/` >= 80%
- [ ] Typecheck pasa en todas las apps + packages
- [ ] Conformance pasa (`pnpm exec biome check .` cero errores)
- [ ] Build estatico exitoso de las 6 apps (cada `dist/index.html` existe)
- [ ] Preview verificado visualmente (`pnpm run preview` en cualquier app)
- [ ] Pre-push hook pasa en local (SKIP_STEPS="")
- [ ] Scan stage `>= 70` para cada subdominio
- [ ] Carpeta `docs/specs/ai-readiness-2026/` eliminada en el ultimo commit
- [ ] PR mergeado a `dev`
- [ ] (post) Promocion `dev -> stage -> main` exitosa
