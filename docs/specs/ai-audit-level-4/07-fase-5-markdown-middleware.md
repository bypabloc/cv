# Fase 5 — Markdown content negotiation via Pages Function `_middleware.ts`

## Objetivo

`curl -H "Accept: text/markdown" https://{host}/` (o cualquier `/X`)
devuelve el `.md` gemelo de esa pagina (AC-5). Reemplaza Transform Rule
TR-1 (manual en dashboard) por una solucion versionada en git.

## Estrategia

- Crear `apps/<niche>/functions/_middleware.ts` que intercepta TODOS
  los requests del Pages site.
- Si `request.headers.get('accept').includes('text/markdown')`:
  - Determinar el path: `/` -> `/index.md`; `/about` -> `/about/index.md`
    (segun el output del postbuild-markdown).
  - Reescribir internamente la URL: `new URL(modifiedPath, request.url)`
    -> `fetch(newRequest, env.ASSETS)` o `context.next(newRequest)`.
  - Si el `.md` no existe -> fallback al asset original.
- Si no incluye `text/markdown` -> `context.next()` (asset normal).

## Archivos

### Crear

- `apps/<niche>/functions/_middleware.ts` (x6)
  - Sin imports externos (puro JS Workers-compatible).
  - Logica de routing inline (~30-40 lineas).

- `packages/markdown-export/src/lib/build-middleware.ts`
  - Funcion `buildMarkdownMiddleware(): string` que genera el contenido
    textual del `_middleware.ts` (compartido entre 6 niches via codegen
    en lugar de copy/paste).

- `packages/markdown-export/tests/unit/build-middleware.test.ts`
  - Coverage 100%.

- `apps/<niche>/scripts/postbuild-middleware.mjs` (x6) — opcional
  - Llama a `buildMarkdownMiddleware()` y escribe
    `apps/<niche>/functions/_middleware.ts`.
  - Alternativa simpler: commitear el archivo en cada app (6 copias
    identicas, mas verboso pero sin codegen).

### Modificar

- `packages/markdown-export/src/index.ts`
  - Exportar `buildMarkdownMiddleware`.

### Eliminar

- `cloudflare/transform-rules.md`
  - Ya no aplica — el middleware reemplaza la rule manual.
  - Documentar la migracion en el commit message.

## Tests requeridos

- `packages/markdown-export/tests/unit/build-middleware.test.ts` [AC-5]
  - WHEN buildMarkdownMiddleware THEN el output contiene la logica
    `accept.includes('text/markdown')` y el rewrite a `.md`.

### Verificacion local

```bash
cd apps/generic && pnpm run build  # con env vars
npx wrangler@latest pages dev dist --port 8790 --compatibility-date=2026-05-27 &
sleep 8

# Sin Accept: text/markdown -> HTML
curl -s localhost:8790/ -o /dev/null -w '%{content_type}\n'
# Esperado: text/html; charset=utf-8

# Con Accept: text/markdown -> markdown
curl -s -H 'Accept: text/markdown' localhost:8790/ | head -c 100
# Esperado: empieza con texto del CV (NO con <!DOCTYPE html>)

# Path interno
curl -s -H 'Accept: text/markdown' localhost:8790/projects | head -c 100
# Esperado: markdown del listado de proyectos

pkill -f 'wrangler.*pages.*dev'
```

### Verificacion dev (post-deploy)

```bash
curl -H 'Accept: text/markdown' https://generic.portfolio.dev.the-full-stack.com/ | head -c 200
# Esperado: markdown
```

## Done cuando

- [ ] Tests verde
- [ ] `_middleware.ts` reescribe segun Accept correctamente en local
- [ ] Deploy a dev + curl-check pasa
- [ ] `cloudflare/transform-rules.md` eliminado
- [ ] Commit: `feat(functions): middleware Accept: text/markdown -> .md (reemplaza Transform Rule)`
