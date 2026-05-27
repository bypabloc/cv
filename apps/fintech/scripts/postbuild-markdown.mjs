/**
 * @script postbuild-markdown
 * @description Despues de `astro build`, genera un `.md` gemelo por cada
 *   `index.html` del dist usando @portfolio/markdown-export (turndown +
 *   GFM, sin chrome). El `.md` lo sirve Cloudflare via Transform Rule
 *   cuando el cliente envia `Accept: text/markdown`.
 */
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { postbuildExport } from '@portfolio/markdown-export'

const __dirname = dirname(fileURLToPath(import.meta.url))
const DIST_DIR = resolve(__dirname, '../dist')

const { count } = await postbuildExport({ distDir: DIST_DIR })
console.info(`[postbuild-markdown] generated ${count} .md files`)
