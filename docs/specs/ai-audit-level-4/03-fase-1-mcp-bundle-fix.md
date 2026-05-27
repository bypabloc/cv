# Fase 1 — Fix bundle del MCP server (snapshot JSON inyectado)

## Objetivo

`/mcp` POST devuelve JSON-RPC valido en dev (AC-1). El bundle de la
Function NO contiene `import.meta.glob` ni dependencias de Vite.

## Estrategia

1. **Refactor `@portfolio/mcp`** para que los 3 tools no importen
   directamente de `@portfolio/content`. En su lugar, reciben los datos
   via un `DataProvider` (interface inyectado en `handleRequest`).
2. **Nuevo postbuild `postbuild-mcp-snapshot.mjs`** que genera
   `apps/<niche>/functions/_data/cv-snapshot.json` con todo el CV
   serializado (corre con `vite-node`, donde `import.meta.glob` SI
   funciona).
3. **`apps/<niche>/functions/mcp.ts`** importa el snapshot JSON
   estaticamente (`import snapshot from './_data/cv-snapshot.json'`) y
   lo pasa como `DataProvider` a `handleRequest`.
4. El bundle final NO arrastra `@portfolio/content` -> sin `import.meta.glob`.

## Archivos afectados

### Modificar

- `packages/mcp/src/lib/types.ts`
  - Agregar interface `MCPDataProvider` con metodos:
    `getProfile()`, `getExperiences()`, `getProjects()`,
    `getSkills()`, `getEducation()`.
  - Verificar: `pnpm --filter @portfolio/mcp run typecheck`

- `packages/mcp/src/lib/handle-request.ts`
  - Cambiar signature: `handleRequest(body: string, data: MCPDataProvider)`.
  - Pasar `data` a `handleToolsCall`.
  - Verificar: `pnpm --filter @portfolio/mcp exec vitest run`

- `packages/mcp/src/lib/handle-tools-call.ts`
  - Aceptar `data: MCPDataProvider` y pasar a los tools.

- `packages/mcp/src/lib/tools/get-cv-section.ts`
  - Reemplazar `import { profile, experiences, ... } from '@portfolio/content'`
    por `(data: MCPDataProvider)` como argumento.
  - El handler usa `data.getProfile()`, etc.

- `packages/mcp/src/lib/tools/list-projects.ts`
  - Idem: usa `data.getProjects()`.

- `packages/mcp/src/lib/tools/search-experience.ts`
  - Idem: usa `data.getExperiences()`.

- `packages/mcp/src/index.ts`
  - Exportar `MCPDataProvider`.

- `packages/mcp/package.json`
  - Eliminar `"@portfolio/content": "workspace:*"` de `dependencies`.
    (queda solo como devDep si los tests lo necesitan via factory).
  - Verificar: `pnpm install` no warning de unused workspace.

- `packages/mcp/tests/unit/*.test.ts`
  - Actualizar mocks para pasar un `MCPDataProvider` fake en cada test.
  - Verificar: `pnpm --filter @portfolio/mcp run test:coverage` >= 80%.

- `apps/<niche>/functions/mcp.ts` (x6 niches)
  - `import snapshot from './_data/cv-snapshot.json'`
  - `import { handleRequest, createSnapshotProvider } from '@portfolio/mcp'`
  - `const data = createSnapshotProvider(snapshot)`
  - `const response = await handleRequest(body, data)`
  - Verificar: `pnpm --filter @portfolio/<niche> run typecheck`

- `apps/<niche>/scripts/postbuild-functions.mjs` (x6)
  - Antes del bundle de `mcp.ts`, llamar al nuevo
    `postbuild-mcp-snapshot.mjs` (o invocarlo desde aqui).
  - Asegurar que el bundle target incluye el `_data/*.json`.

- `packages/markdown-export/src/lib/bundle-pages-function.ts`
  - Agregar `loader: { '.json': 'json' }` a esbuild para que el JSON
    import se inline en el bundle.

- `packages/mcp/vitest.config.ts`
  - Si los tests del package usan datos reales del CV via factory,
    mantener el plugin yaml + JSON_SCHEMA. Si usan mocks puros, simplificar.

### Crear

- `packages/mcp/src/lib/snapshot-provider.ts`
  - Factory `createSnapshotProvider(snapshot: CvSnapshot): MCPDataProvider`
    que devuelve un provider que lee del JSON snapshot estatico.
  - Tipos: `CvSnapshot = { profile, experiences, projects, skills, education }`.
  - Verificar: `pnpm --filter @portfolio/mcp exec vitest run snapshot-provider`

- `packages/mcp/tests/unit/snapshot-provider.test.ts`
  - Coverage 100% per-file en el factory.

- `apps/<niche>/scripts/postbuild-mcp-snapshot.mjs` (x6)
  - Importa `@portfolio/content` (en Node con vite-node) y serializa a JSON:
    ```js
    import { profile, experiences, projects, skills, education } from '@portfolio/content'
    const snapshot = { profile, experiences, projects, skills, education }
    await writeFile(OUTPUT, JSON.stringify(snapshot, null, 2))
    ```
  - Output: `apps/<niche>/functions/_data/cv-snapshot.json`
  - Verificar: el archivo existe + parsea como JSON.

- `apps/<niche>/functions/_data/.gitignore` (x6)
  - `cv-snapshot.json` (output, no commiteado).

### Eliminar

- Nada.

## Tests requeridos

### Unit (Vitest)

- `packages/mcp/tests/unit/snapshot-provider.test.ts` [AC-1]
  - WHEN `createSnapshotProvider(snapshot)` THEN devuelve provider con
    los 5 metodos que retornan los datos del snapshot.

- `packages/mcp/tests/unit/handle-request.test.ts` (modificar) [AC-1]
  - WHEN `handleRequest` con `initialize` Y `data: fakeProvider`
    THEN retorna `protocolVersion 2025-11-25`.

- `packages/mcp/tests/unit/handle-tools-call.test.ts` (modificar) [AC-1]
  - WHEN `tools/call name=get_cv_section section=about Y data=fakeProvider`
    THEN retorna Markdown con el about del fake provider.

### Integration manual

- `wrangler pages dev apps/generic/dist` corre sin `TypeError`.
- `curl POST localhost:8788/mcp -d '{"jsonrpc":"2.0",...}'` -> 200 + JSON-RPC valido.

## Verificacion

```bash
# 1. Build verde
pnpm --filter @portfolio/mcp run typecheck
pnpm --filter @portfolio/mcp run test:coverage
pnpm --filter @portfolio/generic run build  # con env vars de dev

# 2. Verificar bundle sin import.meta.glob
grep -c 'import.meta.glob' apps/generic/dist/functions/mcp.js
# Esperado: 0

# 3. Local con wrangler
cd apps/generic
npx wrangler@latest pages dev dist --port 8788 \
  --compatibility-date=2026-05-27 > /tmp/wd.log 2>&1 &
sleep 8
curl -X POST localhost:8788/mcp \
  -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}'
# Esperado: 200 + body JSON con result.protocolVersion

pkill -f 'wrangler.*pages.*dev'

# 4. Deploy a dev y verificar prod-like
# (ver Fase 6 para deploy)
```

## Done cuando

- [ ] `grep -c 'import.meta.glob' apps/*/dist/functions/mcp.js == 0` en los 6 niches
- [ ] Test unitario de snapshot-provider con coverage 100%
- [ ] `wrangler pages dev` local responde JSON-RPC valido en `/mcp`
- [ ] Commit Conventional: `feat(mcp): snapshot JSON inyectado en Pages Function`
