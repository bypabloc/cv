/**
 * @script postbuild-functions
 * @description Bundlea las Pages Functions de esta app (functions/*.ts)
 *   a `dist/functions/*.js` standalone usando esbuild (Workers-compatible
 *   ESM). Wrangler recoge el directorio dist/functions/ al desplegar.
 *
 *   Genera ademas el snapshot JSON del CV en
 *   `functions/_data/cv-snapshot.json` que la Function `mcp.ts` importa
 *   estaticamente. Asi el bundle del Worker NO arrastra `@portfolio/content`
 *   (que usa `import.meta.glob` de Vite, incompatible con Workers runtime).
 *
 *   Hoy bundlea solo `functions/mcp.ts` (MCP server). Si se agregan
 *   nuevas Functions, listarlas en `ENTRYPOINTS` abajo.
 */
import { mkdir } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { bundlePagesFunction } from '@portfolio/markdown-export'
import { writeSnapshot } from '../../../packages/mcp/scripts/build-snapshot.mjs'

const __dirname = dirname(fileURLToPath(import.meta.url))
const APP_DIR = resolve(__dirname, '..')
const FUNCTIONS_SRC = resolve(APP_DIR, 'functions')
const FUNCTIONS_OUT = resolve(APP_DIR, 'dist/functions')
const SNAPSHOT_PATH = resolve(FUNCTIONS_SRC, '_data/cv-snapshot.json')

const ENTRYPOINTS = ['mcp.ts']

await writeSnapshot(SNAPSHOT_PATH)
console.info(`[postbuild-functions] snapshot CV -> ${SNAPSHOT_PATH}`)

await mkdir(FUNCTIONS_OUT, { recursive: true })

for (const entry of ENTRYPOINTS) {
  const inFile = resolve(FUNCTIONS_SRC, entry)
  const outFile = resolve(FUNCTIONS_OUT, entry.replace(/\.ts$/, '.js'))
  await bundlePagesFunction({ entryPoint: inFile, outFile })
  console.info(`[postbuild-functions] bundled ${entry} -> dist/functions/`)
}
