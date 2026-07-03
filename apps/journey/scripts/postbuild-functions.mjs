/**
 * @script postbuild-functions
 * @description Genera el Cloudflare Pages Advanced Mode Worker en
 *   `dist/_worker.js` + sus datos en `dist/_worker-data/*.json`.
 *   El Worker monolitico maneja: POST/OPTIONS /mcp, GET .well-known/*.json
 *   y content negotiation Accept: text/markdown. Fallback al
 *   env.ASSETS.fetch (asset estatico + SPA fallback Astro).
 *   Mismo stack de discovery que los niches (regla: SEO completo).
 */
import { mkdir, rm, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  buildPagesWorker,
  bundlePagesFunction,
} from '@portfolio/markdown-export'
import {
  buildAgentCard,
  buildAgentSkills,
  buildApiCatalog,
  buildMcpServerCard,
} from '@portfolio/seo'
import { writeSnapshot } from '../../../packages/mcp/scripts/build-snapshot.mjs'

const __dirname = dirname(fileURLToPath(import.meta.url))
const APP_DIR = resolve(__dirname, '..')
const DIST_DIR = resolve(APP_DIR, 'dist')
const DATA_DIR = resolve(DIST_DIR, '_worker-data')
const WORKER_SRC_PATH = resolve(DIST_DIR, '_worker-src.ts')
const WORKER_OUT_PATH = resolve(DIST_DIR, '_worker.js')

const SITE_URL =
  process.env.SITE_URL ?? 'https://journey.portfolio.the-full-stack.com'
const API_ENDPOINT =
  process.env.PUBLIC_API_ENDPOINT ||
  (process.env.BASE_DOMAIN
    ? `https://api.${process.env.BASE_DOMAIN}`
    : 'https://api.portfolio.the-full-stack.com')

await rm(resolve(DIST_DIR, 'functions'), { recursive: true, force: true })

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
await writeFile(
  resolve(DATA_DIR, 'agent-card.json'),
  buildAgentCard({ siteUrl: SITE_URL }),
  'utf8',
)
await writeFile(
  resolve(DATA_DIR, 'agent-skills.json'),
  buildAgentSkills({ siteUrl: SITE_URL }),
  'utf8',
)
console.info(
  '[postbuild-functions] api-catalog.json + mcp-server-card.json + agent-card.json + agent-skills.json',
)

await writeFile(WORKER_SRC_PATH, buildPagesWorker(), 'utf8')
await bundlePagesFunction({
  entryPoint: WORKER_SRC_PATH,
  outFile: WORKER_OUT_PATH,
})
await rm(WORKER_SRC_PATH, { force: true })
console.info(`[postbuild-functions] _worker.js bundled -> ${WORKER_OUT_PATH}`)
