/**
 * @script postbuild-functions
 * @description Bundlea las Pages Functions de esta app (todas las
 *   `functions/**\/*.ts`) a `dist/functions/...` standalone usando esbuild
 *   (Workers-compatible ESM). Wrangler recoge el directorio dist/functions/
 *   al desplegar.
 *
 *   Genera ademas:
 *   - `functions/_data/cv-snapshot.json`: CV serializado para que la
 *     Function `mcp.ts` lo importe estaticamente (evita arrastrar
 *     @portfolio/content que usa `import.meta.glob` de Vite, incompatible
 *     con Workers runtime).
 */
import { mkdir, readdir, stat, writeFile } from 'node:fs/promises'
import { dirname, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { bundlePagesFunction } from '@portfolio/markdown-export'
import { buildApiCatalog, buildMcpServerCard } from '@portfolio/seo'
import { writeSnapshot } from '../../../packages/mcp/scripts/build-snapshot.mjs'

const __dirname = dirname(fileURLToPath(import.meta.url))
const APP_DIR = resolve(__dirname, '..')
const FUNCTIONS_SRC = resolve(APP_DIR, 'functions')
const FUNCTIONS_OUT = resolve(APP_DIR, 'dist/functions')
const DATA_DIR = resolve(FUNCTIONS_SRC, '_data')
const SNAPSHOT_PATH = resolve(DATA_DIR, 'cv-snapshot.json')

const SITE_URL = process.env.SITE_URL ?? 'https://the-full-stack.com'
const API_ENDPOINT =
  process.env.PUBLIC_API_ENDPOINT ||
  (process.env.BASE_DOMAIN
    ? `https://api.${process.env.BASE_DOMAIN}`
    : 'https://api.portfolio.the-full-stack.com')

await mkdir(DATA_DIR, { recursive: true })
await writeSnapshot(SNAPSHOT_PATH)
console.info(`[postbuild-functions] snapshot CV -> ${SNAPSHOT_PATH}`)

await writeFile(
  resolve(DATA_DIR, 'api-catalog.json'),
  buildApiCatalog({ siteUrl: SITE_URL, apiEndpoint: API_ENDPOINT }),
  'utf8',
)
await writeFile(
  resolve(DATA_DIR, 'mcp-server-card.json'),
  buildMcpServerCard({ siteUrl: SITE_URL }),
  'utf8',
)
console.info(
  '[postbuild-functions] api-catalog.json + mcp-server-card.json -> _data/',
)

// _middleware.ts es convencion de Cloudflare Pages (file-based routing)
// y DEBE bundlearse. El resto de archivos con prefijo _ son auxiliares
// (helpers, fixtures) y se excluyen.
const ALLOWED_UNDERSCORE = new Set(['_middleware.ts'])

async function* walkTs(dir) {
  for (const entry of await readdir(dir)) {
    if (entry === '_data') continue
    const full = resolve(dir, entry)
    const s = await stat(full)
    if (s.isDirectory()) {
      yield* walkTs(full)
    } else if (
      entry.endsWith('.ts') &&
      (!entry.startsWith('_') || ALLOWED_UNDERSCORE.has(entry))
    ) {
      yield full
    }
  }
}

await mkdir(FUNCTIONS_OUT, { recursive: true })

let count = 0
for await (const inFile of walkTs(FUNCTIONS_SRC)) {
  const rel = relative(FUNCTIONS_SRC, inFile).replace(/\.ts$/, '.js')
  const outFile = resolve(FUNCTIONS_OUT, rel)
  await mkdir(dirname(outFile), { recursive: true })
  await bundlePagesFunction({ entryPoint: inFile, outFile })
  console.info(`[postbuild-functions] bundled ${rel}`)
  count += 1
}
console.info(`[postbuild-functions] ${count} Pages Functions bundled`)
