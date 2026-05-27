# Fase 4 — Verificar MCP tools end-to-end

## Objetivo

Confirmar que el `/mcp` Function (post Fase 1) responde JSON-RPC valido
para el handshake completo y las 3 tools devuelven contenido real del
CV. NO se agregan tools nuevas — el alcance final es 3.

## Estrategia

- Tests E2E manuales contra `https://generic.portfolio.dev.the-full-stack.com/mcp`.
- 5 requests JSON-RPC encadenadas, validar cada response.
- Si todo pasa: cerrar fase como DONE.
- Si una tool devuelve datos vacios o malformados: bug en el snapshot
  provider (volver a Fase 1) o en el handler de la tool.

## Archivos

### Modificar

- Ninguno. Esta fase es VERIFICACION, no codigo.

### (Opcional) Crear

- `apps/generic/tests/feature/specs/mcp-server.spec.ts` (Playwright E2E)
  - Spec que hace los 5 requests JSON-RPC y valida responses.
  - Skip por defecto si `RUN_MCP_E2E != 1` (es contra dev, requiere
    deploy listo).

## Tests requeridos

### Verificacion manual (BAT)

```bash
SITE=https://generic.portfolio.dev.the-full-stack.com/mcp

# 1. initialize
curl -s -X POST $SITE -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"audit","version":"1"}}}' \
  | jq '.result.protocolVersion'
# Esperado: "2025-11-25"

# 2. tools/list
curl -s -X POST $SITE -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  | jq '.result.tools[].name'
# Esperado: "get_cv_section", "list_projects", "search_experience"

# 3. tools/call get_cv_section about
curl -s -X POST $SITE -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_cv_section","arguments":{"section":"about"}}}' \
  | jq '.result.content[0].text' | head -c 100
# Esperado: Markdown con el nombre y rol de Pablo Contreras

# 4. tools/call list_projects
curl -s -X POST $SITE -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"list_projects","arguments":{}}}' \
  | jq '.result.content[0].text' | head -c 300
# Esperado: lista de proyectos

# 5. tools/call search_experience keyword=fintech
curl -s -X POST $SITE -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"search_experience","arguments":{"keyword":"fintech"}}}' \
  | jq '.result.content[0].text' | head -c 300
# Esperado: matches con "Destacame" o similar (fintech LATAM)
```

## Done cuando

- [ ] Los 5 requests devuelven JSON-RPC valido + contenido correcto del CV.
- [ ] (Opcional) Spec E2E commiteada.
- [ ] Sin commit obligatorio (fase de verificacion). Si se agrega spec,
      commit `test(mcp): e2e contra /mcp en dev`.
