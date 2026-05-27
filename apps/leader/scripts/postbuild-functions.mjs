/**
 * @script postbuild-functions
 * @description Genera el Cloudflare Pages Advanced Mode Worker en
 *   `dist/_worker.js` + sus datos en `dist/_worker-data/*.json`.
 *   El Worker monolitico maneja: POST/OPTIONS /mcp, GET .well-known/*.json
 *   y content negotiation Accept: text/markdown. Fallback al
 *   env.ASSETS.fetch (asset estatico + SPA fallback Astro).
 *
 *   Razon: las Pages Functions en `dist/functions/` SOLO se reconocen
 *   en wrangler dev local; en Cloudflare Pages prod NO se ejecutan
 *   (verificado contra dev tras Fase 2A). Advanced Mode con
 *   `dist/_worker.js` SI funciona universalmente.
 *
 *   Flujo:
 *   1. Genera 3 JSONs en `dist/_worker-data/`:
 *      - cv-snapshot.json: CV serializado para el MCP server.
 *      - api-catalog.json: linkset RFC9727.
 *      - mcp-server-card.json: MCP descriptor.
 *   2. Genera el TS source del Worker en un tempfile.
 *   3. Bundle a `dist/_worker.js` con esbuild (loader json, target Workers).
 */
import { mkdir, rm, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  buildPagesWorker,
  bundlePagesFunction,
} from '@portfolio/markdown-export'
import { buildApiCatalog, buildMcpServerCard } from '@portfolio/seo'
import { writeSnapshot } from '../../../packages/mcp/scripts/build-snapshot.mjs'

const __dirname = dirname(fileURLToPath(import.meta.url))
const APP_DIR = resolve(__dirname, '..')
const DIST_DIR = resolve(APP_DIR, 'dist')
const DATA_DIR = resolve(DIST_DIR, '_worker-data')
const WORKER_SRC_PATH = resolve(DIST_DIR, '_worker-src.ts')
const WORKER_OUT_PATH = resolve(DIST_DIR, '_worker.js')

const SITE_URL = process.env.SITE_URL ?? 'https://the-full-stack.com'
const API_ENDPOINT =
  process.env.PUBLIC_API_ENDPOINT ||
  (process.env.BASE_DOMAIN
    ? `https://api.${process.env.BASE_DOMAIN}`
    : 'https://api.portfolio.the-full-stack.com')

// 1. Cleanup directorios viejos del approach de Pages Functions
//    (apps/<niche>/dist/functions/ ya no se usa: Advanced Mode con
//    _worker.js es la unica entrada al routing del site).
await rm(resolve(DIST_DIR, 'functions'), { recursive: true, force: true })

// 2. Generar JSONs en dist/_worker-data/
await mkdir(DATA_DIR, { recursive: true })
const SNAPSHOT_PATH = resolve(DATA_DIR, 'cv-snapshot.json')
await writeSnapshot(SNAPSHOT_PATH)
console.info(`[postbuild-functions] cv-snapshot.json -> ${SNAPSHOT_PATH}`)

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
console.info('[postbuild-functions] api-catalog.json + mcp-server-card.json')

// 3. Generar source del Worker + bundle a dist/_worker.js
await writeFile(WORKER_SRC_PATH, buildPagesWorker(), 'utf8')
await bundlePagesFunction({
  entryPoint: WORKER_SRC_PATH,
  outFile: WORKER_OUT_PATH,
})
await rm(WORKER_SRC_PATH, { force: true })
console.info(`[postbuild-functions] _worker.js bundled -> ${WORKER_OUT_PATH}`)
