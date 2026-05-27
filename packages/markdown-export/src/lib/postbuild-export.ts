/**
 * @module postbuild-export
 * @description Recorre el `dist/` de una app Astro, encuentra todos los
 *   `index.html` (default `**\/index.html`) y por cada uno escribe un
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
  const htmlFiles = await collectHtml(params.distDir, 'index.html')
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

/**
 * Recorre `root` recursivamente y devuelve todos los archivos con el
 * `fileName` dado. Implementacion casera para evitar dependencia de glob
 * (no esta en stdlib estable de Node 22).
 */
async function collectHtml(root: string, fileName: string): Promise<string[]> {
  const out: string[] = []
  await walk(root, fileName, out)
  out.sort()
  return out
}

async function walk(
  dir: string,
  fileName: string,
  out: string[],
): Promise<void> {
  const entries = await readdir(dir, { withFileTypes: true })
  for (const entry of entries) {
    const full = join(dir, entry.name)
    if (entry.isDirectory()) {
      await walk(full, fileName, out)
    } else if (entry.isFile() && entry.name === fileName) {
      out.push(full)
    }
  }
}
