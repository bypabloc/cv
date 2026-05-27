# Fase 6 — Verificacion E2E iterativa (fase final)

> SIEMPRE es la ultima fase y el ultimo commit del plan. Sin esto en
> verde, NO se hace `git push` ni se crea el PR (gate de cierre).

## Parte A — Refactor de tests

Antes de la bateria de comandos, confirmar que:

- Ningun test viejo referencia codigo eliminado (`grep -l 'cloudflare/transform-rules' tests/`).
- Tests nuevos estan en la ruta correcta:
  - `packages/mcp/tests/unit/snapshot-provider.test.ts`
  - `packages/seo/tests/unit/build-openapi.test.ts`
  - `packages/markdown-export/tests/unit/build-middleware.test.ts`
- Convencion BDD-style (Given/When/Then) en cada `it()`.
- Asserts EXACTOS (no rangos).

Barrido global con `rg -l`:

```bash
# Deberia dar 0 resultados (cloudflare/transform-rules.md eliminado)
rg -l 'transform-rules\|TR-1\|cloudflare/transform' packages/ apps/ docs/ 2>&1 | grep -v 'specs/ai-audit-level-4'
```

## Parte B — Bateria de comandos reales

Ejecutar la verificacion completa de punta a punta con el codigo final.
Bucle "no parar hasta que funcione": ejecutar -> si falla, diagnosticar
-> corregir -> re-ejecutar la suite -> repetir.

### B.1 — Local (pre-push)

```bash
# 1. Lint + format
pnpm exec biome check .
# Esperado: sin errores

# 2. Typecheck (recursive)
pnpm run typecheck
# Esperado: sin errores en todos los workspaces

# 3. Unit tests + coverage por package modificado
pnpm --filter @portfolio/mcp run test:coverage
pnpm --filter @portfolio/seo run test:coverage
pnpm --filter @portfolio/markdown-export run test:coverage
# Esperado: coverage >= 80% per-file en archivos modificados

# 4. Build local de los 6 niches (con env vars de dev)
DEV_ENV_KEYS=$(cat docker/env/client/.dev | grep -E '^(PUBLIC_|BASE_)' | xargs)
env $DEV_ENV_KEYS pnpm run build
# Esperado: build exitoso, 6 dist/ generados

# 5. Verificacion de artefactos en dist/ (representativo: generic)
test -f apps/generic/dist/openapi.json && echo "openapi OK"
test -f apps/generic/functions/_data/cv-snapshot.json && echo "snapshot OK"
test -f apps/generic/functions/.well-known/api-catalog.json.ts && echo "Function api-catalog OK"
test -f apps/generic/functions/.well-known/mcp/server-card.json.ts && echo "Function mcp-server-card OK"
test -f apps/generic/functions/_middleware.ts && echo "middleware OK"
grep -c 'import.meta.glob' apps/generic/dist/functions/mcp.js
# Esperado: 0

# 6. Wrangler dev local: smoke E2E
cd apps/generic && \
  npx wrangler@latest pages dev dist --port 8788 --compatibility-date=2026-05-27 > /tmp/wd.log 2>&1 &
sleep 8
BASE=http://localhost:8788
curl -s $BASE/.well-known/api-catalog.json | jq '.linkset[0].anchor' || echo FAIL
curl -s $BASE/.well-known/mcp/server-card.json | jq '.protocolVersion' || echo FAIL
curl -s $BASE/openapi.json | jq '.openapi' || echo FAIL
curl -s -X POST $BASE/mcp -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"e2e","version":"1"}}}' | jq '.result.protocolVersion' || echo FAIL
curl -s -H 'Accept: text/markdown' $BASE/ | head -c 50
pkill -f 'wrangler.*pages.*dev'
```

### B.2 — Deploy a dev + smoke E2E remoto

```bash
SKIP_STEPS="feature_tests" git push origin feature/ai-audit-level-4
# Esperar a que los workflows de dev verde
gh run watch  # o gh run list --branch feature/ai-audit-level-4
```

Tras merge a dev y deploy verde:

```bash
BASE=https://generic.portfolio.dev.the-full-stack.com
curl -sI $BASE/.well-known/api-catalog.json | grep -i '^content-type'
curl -s $BASE/.well-known/api-catalog.json | jq '.linkset' | head -10
curl -s $BASE/.well-known/mcp/server-card.json | jq '.protocolVersion'
curl -s $BASE/openapi.json | jq '.paths | keys'

# MCP handshake completo
curl -s -X POST $BASE/mcp -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize",...}' | jq .
curl -s -X POST $BASE/mcp -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | jq '.result.tools | length'
# Esperado: 3

# Markdown negotiation
curl -s -H 'Accept: text/markdown' $BASE/ | head -c 100
# Esperado: empieza con texto del CV
```

### B.3 — Promover a stage y prod

```bash
# dev -> stage
gh pr create --base stage --head dev --title "promote: dev -> stage (ai-audit-level-4)"
gh pr merge <N> --merge

# Esperar workflows en stage
gh run list --branch stage --limit 3 --json status

# stage -> main
gh pr create --base main --head stage --title "promote: stage -> main (ai-audit-level-4)"
gh pr merge <N> --merge

# Esperar workflows en main
gh run list --branch main --limit 3 --json status
```

### B.4 — Audit final contra prod (AC-6)

```bash
python devtools/run.py ai_audit
# Esperado: 18/18 OK
# Esperado: isitagentready >= 3/5 en los 6 niches
```

### B.5 — Cierre

Si TODO esta verde:

```bash
git rm -r docs/specs/ai-audit-level-4/
git add -A
git commit -m "$(cat <<'EOF'
chore(specs): cierra plan ai-audit-level-4 (verificacion E2E completa)

- AC-1..AC-5 verificados en prod
- AC-6: isitagentready score X/5 en los 6 niches (resultado del audit)
- Elimina la carpeta del plan segun el ciclo de vida plan-format
EOF
)"
```

## Bucle de correccion ante fallos

Si CUALQUIER paso de B.1, B.2, B.3 o B.4 falla:

1. Diagnosticar (logs de wrangler, response body, network tab).
2. Corregir en la fase correspondiente (volver a editar archivos).
3. Re-correr la verificacion incremental de esa fase.
4. Re-correr Parte B desde el paso fallido.
5. Repetir hasta que TODO este en verde.

NO marcar el plan completo con un comando fallando o coverage < 80%.

## Regla de cierre

`git push` y el PR `feature/ai-audit-level-4 -> dev` se hacen
UNICAMENTE cuando B.1 completa (lint + typecheck + tests + build local
+ wrangler dev local).

La parte B.2/B.3/B.4 sucede DESPUES del merge a dev. Si dev falla,
hotfix en la rama y nuevo push (no se reabre el PR).
