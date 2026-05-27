/**
 * @script postbuild-functions
 * @description Bundlea las Pages Functions de esta app (functions/*.ts)
 *   a `dist/functions/*.js` standalone usando esbuild (Workers-compatible
 *   ESM). Wrangler recoge el directorio dist/functions/ al desplegar.
 *
 *   Hoy bundlea solo `functions/mcp.ts` (MCP server). Si se agregan
 *   nuevas Functions, listarlas en `ENTRYPOINTS` abajo.
 */
import { mkdir } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { bundlePagesFunction } from '@portfolio/markdown-export'

const __dirname = dirname(fileURLToPath(import.meta.url))
const APP_DIR = resolve(__dirname, '..')
const FUNCTIONS_SRC = resolve(APP_DIR, 'functions')
const FUNCTIONS_OUT = resolve(APP_DIR, 'dist/functions')

const ENTRYPOINTS = ['mcp.ts']

await mkdir(FUNCTIONS_OUT, { recursive: true })

for (const entry of ENTRYPOINTS) {
  const inFile = resolve(FUNCTIONS_SRC, entry)
  const outFile = resolve(FUNCTIONS_OUT, entry.replace(/\.ts$/, '.js'))
  await bundlePagesFunction({ entryPoint: inFile, outFile })
  console.info(`[postbuild-functions] bundled ${entry} -> dist/functions/`)
}
