/**
 * @module postbuild-export
 * @description Recorre el `dist/` de una app Astro, encuentra todos los
 *   `.html` (salvo `404.html`) y por cada uno escribe un
 *   `index.md` al lado con el contenido del `<main>` convertido a
 *   Markdown. Se invoca desde `apps/<niche>/scripts/postbuild-markdown.mjs`
 *   despues de `astro build`.
 */
import { readdir, readFile, writeFile } from 'node:fs/promises'
import { join } from 'node:path'

import { extractMainContent } from './extract-main-content'
import { htmlToMarkdown } from './html-to-markdown'

interface ExportParams {
  /** Path absoluto al directorio dist de la app. Ej: '/abs/apps/generic/dist'. */
  distDir: string
}

interface ExportResult {
  /** Cantidad de `.md` generados. */
  count: number
  /** Paths absolutos de cada `.md` generado (en orden de procesamiento). */
  paths: string[]
}

/**
 * @function postbuildExport
 * @description Genera `.md` gemelo por cada `index.html` del dist.
 *
 * @returns {ExportResult} `{ count, paths }`
 *
 * @example
 *   await postbuildExport({ distDir: '/abs/apps/generic/dist' })
 *   // { count: 12, paths: ['/abs/.../index.md', ...] }
 */
export async function postbuildExport(
  params: ExportParams,
): Promise<ExportResult> {
  const htmlFiles = await collectHtml(params.distDir)
  const paths: string[] = []
  for (const htmlPath of htmlFiles) {
    const html = await readFile(htmlPath, 'utf8')
    const main = extractMainContent(html)
    const md = htmlToMarkdown({ html: main })
    const mdPath = htmlPath.replace(/\.html$/, '.md')
    await writeFile(mdPath, md, 'utf8')
    paths.push(mdPath)
  }
  return { count: paths.length, paths }
}

/** Paginas de error: no tienen gemelo `.md` (no son contenido). */
const SKIP_FILES = new Set(['404.html'])

/**
 * Recorre `root` recursivamente y devuelve todos los `.html` de contenido
 * (`index.html` y sueltos como `cv.html`).
 */
async function collectHtml(root: string): Promise<string[]> {
  const entries = await readdir(root, { withFileTypes: true, recursive: true })
  return entries
    .filter(
      (e) => e.isFile() && e.name.endsWith('.html') && !SKIP_FILES.has(e.name),
    )
    .map((e) => join(e.parentPath, e.name))
    .sort()
}
