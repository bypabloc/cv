# 04 — Fase 1B: Markdown estatico (`.md` duplicado por pagina)

> **Anterior**: [03-fase-1a-fix-api-catalog.md](03-fase-1a-fix-api-catalog.md) · **Siguiente**: [05-fase-1c-cloudflare-transform-rule.md](05-fase-1c-cloudflare-transform-rule.md)
>
> **Cubre**: AC-3, AC-4, AC-5
>
> **Objetivo**: que cada pagina HTML del dist tenga un `.md` gemelo con
> el mismo contenido en Markdown, listo para que un agente lo consuma
> con `Accept: text/markdown` (servido via Transform Rule en Fase 1C).

## Estrategia

Convertir el HTML del dist a Markdown via `turndown` (libreria
estandar, MIT, 0 deps, mantenida activamente).

`turndown` recibe un string HTML y devuelve Markdown. Se invoca desde el
**postbuild** (despues de `astro build`, porque necesita el HTML
rendered). El builder convierte cada `index.html` del dist a `index.md`
en el mismo directorio.

Razon por la cual NO se hace en prebuild: el HTML aun no existe; el
prebuild solo prepara `public/`. La conversion requiere el HTML final.

## Decision tecnica: turndown vs alternativas

| Lib | Pros | Contras |
|-----|------|---------|
| **turndown** (recomendada) | 0 deps, MIT, 2M downloads/sem, plugin GFM disponible | Solo HTML→MD (no MD→HTML), config algo verbosa |
| node-html-markdown | Mas rapido, mejor por defecto | Menos plugins, comunidad mas chica |
| @astropub/md | Astro-native | Solo para componentes Astro, no para HTML rendered |

**Decision**: `turndown` + `turndown-plugin-gfm` (tablas, strikethrough, task
lists). El portfolio usa esos features en proyectos/experiencias.

## Tarea 1B.1 — Crear paquete `@portfolio/markdown-export` (nuevo)

Decision: vive como package compartido (no en `packages/seo`) porque la
logica es ortogonal a SEO. Puede consumirse desde apps/, packages/, o
incluso un script standalone.

```
packages/markdown-export/
├── package.json
├── tsconfig.json
├── vitest.config.ts
├── src/
│   ├── index.ts                    # re-exports
│   ├── lib/
│   │   ├── html-to-markdown.ts     # core converter
│   │   ├── extract-main-content.ts # extrae <main> o <article>, filtra nav/footer
│   │   └── postbuild-export.ts     # itera dist/, escribe .md por cada .html
└── tests/unit/
    ├── html-to-markdown.test.ts
    ├── extract-main-content.test.ts
    └── postbuild-export.test.ts
```

### `package.json`

```json
{
  "name": "@portfolio/markdown-export",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "main": "./src/index.ts",
  "scripts": {
    "test": "vitest run",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "turndown": "^7.2.0",
    "turndown-plugin-gfm": "^1.0.2",
    "node-html-parser": "^7.0.1"
  },
  "devDependencies": {
    "@types/turndown": "^5.0.5"
  }
}
```

### `src/lib/html-to-markdown.ts`

```ts
import TurndownService from 'turndown'
import { gfm } from 'turndown-plugin-gfm'

interface ConvertParams {
  html: string
  baseUrl?: string  // para resolver relative links a absolutos en el .md
}

export function htmlToMarkdown(params: ConvertParams): string {
  const td = new TurndownService({
    headingStyle: 'atx',         // # H1 (no underline)
    codeBlockStyle: 'fenced',    // ``` (no indented)
    bulletListMarker: '-',
    emDelimiter: '_',
    strongDelimiter: '**',
  })
  td.use(gfm)
  // ignorar scripts, styles, nav repetitivo, comments, tracking pixels
  td.remove(['script', 'style', 'noscript', 'iframe', 'svg'])
  return td.turndown(params.html).trim() + '\n'
}
```

### `src/lib/extract-main-content.ts`

El `.md` no debe incluir nav, footer, tracking pixel, scripts inline.
Filtra a `<main>` (o `<article>` o `<body>` como fallback) y elimina
elementos transversales.

```ts
import { parse } from 'node-html-parser'

export function extractMainContent(html: string): string {
  const root = parse(html)
  // Preferir <main>, luego <article>, luego <body>
  const main = root.querySelector('main')
    ?? root.querySelector('article')
    ?? root.querySelector('body')
  if (!main) return html
  // Limpiar elementos no-contenido
  for (const sel of ['nav', 'footer', 'aside', '.tracking-pixel']) {
    main.querySelectorAll(sel).forEach((el) => el.remove())
  }
  return main.innerHTML
}
```

### `src/lib/postbuild-export.ts`

```ts
import { readFile, writeFile } from 'node:fs/promises'
import { glob } from 'node:fs/promises'  // node 22+
import { join } from 'node:path'

import { htmlToMarkdown } from './html-to-markdown'
import { extractMainContent } from './extract-main-content'

interface ExportParams {
  distDir: string         // ej. 'apps/generic/dist'
  baseUrl: string         // ej. 'https://the-full-stack.com'
  pattern?: string        // default '**/index.html'
}

export async function postbuildExport(params: ExportParams): Promise<number> {
  const pattern = params.pattern ?? '**/index.html'
  let count = 0
  for await (const path of glob(join(params.distDir, pattern))) {
    const html = await readFile(path, 'utf8')
    const main = extractMainContent(html)
    const md = htmlToMarkdown({ html: main, baseUrl: params.baseUrl })
    const mdPath = path.replace(/\.html$/, '.md')
    await writeFile(mdPath, md, 'utf8')
    count++
  }
  return count
}
```

## Tarea 1B.2 — Tests unitarios

### `tests/unit/html-to-markdown.test.ts`

```ts
describe('htmlToMarkdown', () => {
  it('Given simple HTML When convert Then returns Markdown ATX', () => {
    const out = htmlToMarkdown({ html: '<h1>Pablo</h1><p>Lorem</p>' })
    expect(out).toBe('# Pablo\n\nLorem\n')
  })

  it('Given HTML with table When convert Then returns GFM table', () => {
    const html = '<table><tr><th>A</th></tr><tr><td>1</td></tr></table>'
    const out = htmlToMarkdown({ html })
    expect(out).toContain('| A |')
    expect(out).toContain('| 1 |')
  })

  it('Given HTML with script tag When convert Then ignores script', () => {
    const html = '<p>OK</p><script>alert(1)</script>'
    expect(htmlToMarkdown({ html })).toBe('OK\n')
  })
})
```

### `tests/unit/extract-main-content.test.ts`

```ts
describe('extractMainContent', () => {
  it('Given HTML with main+nav+footer When extract Then returns only main', () => {
    const html = '<body><nav>NAV</nav><main><h1>T</h1></main><footer>F</footer></body>'
    const out = extractMainContent(html)
    expect(out).toContain('<h1>T</h1>')
    expect(out).not.toContain('NAV')
    expect(out).not.toContain('F')
  })

  it('Given HTML without main but with article When extract Then returns article', () => {
    const html = '<body><article><p>X</p></article></body>'
    expect(extractMainContent(html)).toBe('<p>X</p>')
  })

  it('Given HTML without main/article When extract Then returns body innerHTML', () => {
    const html = '<body><p>Y</p></body>'
    expect(extractMainContent(html)).toBe('<p>Y</p>')
  })
})
```

### `tests/unit/postbuild-export.test.ts`

Usar `tmp` dir o `mock-fs` para crear un dist de prueba con 3 archivos
HTML, correr `postbuildExport`, verificar que se crearon 3 `.md`.

## Tarea 1B.3 — Hook postbuild en cada app

Agregar script en cada `apps/*/package.json`:

```json
{
  "scripts": {
    "build": "astro build",
    "postbuild": "node ./scripts/postbuild-markdown.mjs"
  }
}
```

Y crear `apps/*/scripts/postbuild-markdown.mjs`:

```js
import { postbuildExport } from '@portfolio/markdown-export'
import { SITE_URL } from '../src/lib/site-config.ts'

const count = await postbuildExport({
  distDir: './dist',
  baseUrl: SITE_URL,
})
console.log(`[postbuild-markdown] generated ${count} .md files`)
```

Aplicar a las 6 apps.

## Tarea 1B.4 — Actualizar `.gitignore`

```
# Markdown duplicados generados por postbuild (espejo de cada HTML)
apps/*/dist/**/*.md
```

(`dist/` ya esta gitignored; agregar explicitamente la regla para
documentar la convencion.)

## Verificacion incremental (antes del commit)

```bash
# 1. Tests del paquete nuevo
pnpm --filter @portfolio/markdown-export run test
pnpm --filter @portfolio/markdown-export run typecheck

# 2. Coverage >= 80%
pnpm --filter @portfolio/markdown-export exec vitest run --coverage

# 3. Build + postbuild de las 6 apps
pnpm run build
find apps/*/dist -name '*.md' | wc -l   # >= 6 (al menos 1 por app)

# 4. Spot check de calidad: el .md del home tiene el H1
cat apps/generic/dist/index.md | head -5
# ESPERADO: # <nombre o tagline>
```

## Archivos afectados

### Crear

- `packages/markdown-export/package.json`
- `packages/markdown-export/tsconfig.json`
- `packages/markdown-export/vitest.config.ts`
- `packages/markdown-export/src/index.ts`
- `packages/markdown-export/src/lib/html-to-markdown.ts`
- `packages/markdown-export/src/lib/extract-main-content.ts`
- `packages/markdown-export/src/lib/postbuild-export.ts`
- `packages/markdown-export/tests/unit/html-to-markdown.test.ts`
- `packages/markdown-export/tests/unit/extract-main-content.test.ts`
- `packages/markdown-export/tests/unit/postbuild-export.test.ts`
- `apps/architect/scripts/postbuild-markdown.mjs`
- `apps/fintech/scripts/postbuild-markdown.mjs`
- `apps/generic/scripts/postbuild-markdown.mjs`
- `apps/hub/scripts/postbuild-markdown.mjs`
- `apps/leader/scripts/postbuild-markdown.mjs`
- `apps/vibe/scripts/postbuild-markdown.mjs`
  - Verificar (todos): tests verdes + coverage >= 80%

### Modificar

- `apps/architect/package.json` — agregar `postbuild`
- `apps/fintech/package.json` — agregar `postbuild`
- `apps/generic/package.json` — agregar `postbuild`
- `apps/hub/package.json` — agregar `postbuild`
- `apps/leader/package.json` — agregar `postbuild`
- `apps/vibe/package.json` — agregar `postbuild`
  - Verificar: `pnpm run build` genera N `.md` por app
- `pnpm-workspace.yaml` — agregar `packages/markdown-export` (si usa
  patron explicito; si usa `packages/*` glob no hace falta)
- `.gitignore` — agregar `apps/*/dist/**/*.md`

## Done

- [ ] Paquete `@portfolio/markdown-export` creado con 3 modulos + 3 test files
- [ ] Coverage del paquete >= 80% per-file
- [ ] Postbuild en las 6 apps genera al menos 1 `.md` por ruta
- [ ] Lint + typecheck verde
- [ ] Commit 1: `feat(markdown-export): paquete que convierte HTML del dist a Markdown via turndown`
- [ ] Commit 2: `feat(apps): postbuild genera .md gemelo por cada index.html`
