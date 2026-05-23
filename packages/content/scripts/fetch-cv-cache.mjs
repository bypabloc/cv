#!/usr/bin/env node
/**
 * @script fetch-cv-cache
 * @description Bootstrap del prebuild: trae el CV del API GET /cv y lo
 *   escribe como JSON en packages/content/src/data-cache/.
 *
 *   Los index.ts de cada entidad (awards, experiences, ...) leen ese JSON
 *   en build-time via import sincrono. Asi se mantiene la API publica
 *   del package (arrays sincronos) y se reemplaza el origen YAML por API.
 *
 *   Variables de entorno:
 *   - PUBLIC_CV_API_URL (preferida) o CV_API_URL: base URL del API.
 *     Ej: https://gvz6y2xcsa.execute-api.us-east-1.amazonaws.com/dev
 *   - CV_CACHE_REUSE=1 (opcional): si el cache YA existe, no llama al API
 *     (util para builds rapidos sin red).
 */
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const CACHE_DIR = resolve(__dirname, '..', 'src', 'data-cache')

const API_BASE = (
  process.env.PUBLIC_CV_API_URL ??
  process.env.CV_API_URL ??
  ''
).replace(/\/+$/, '')

if (!API_BASE) {
  throw new Error(
    'fetch-cv-cache: ni PUBLIC_CV_API_URL ni CV_API_URL estan seteadas.\n' +
      'Setea la URL del API antes del prebuild, ej:\n' +
      '  export PUBLIC_CV_API_URL=https://<id>.execute-api.us-east-1.amazonaws.com/dev',
  )
}

/**
 * Las 10 actions del API y el archivo cache de salida.
 * Cada action carga TODOS los entries (sin niche): los componentes Astro
 * filtran client-side con filterByNiche. locale=es porque el shape ya
 * trae todas las traducciones bilingues.
 */
const ACTIONS = [
  ['profile', 'profile.json'],
  ['experiences', 'experiences.json'],
  ['projects', 'projects.json'],
  ['certificates', 'certificates.json'],
  ['awards', 'awards.json'],
  ['education', 'education.json'],
  ['languages', 'languages.json'],
  ['references', 'references.json'],
  ['skills', 'skills.json'],
]

async function callApi(action) {
  const url = `${API_BASE}/cv?operation=cv&action=${action}&locale=es`
  const res = await fetch(url, { headers: { Accept: 'application/json' } })
  if (!res.ok) {
    throw new Error(
      `fetch-cv-cache: ${url} respondio HTTP ${res.status} ${res.statusText}`,
    )
  }
  return res.json()
}

async function cacheExists(file) {
  try {
    await readFile(file, 'utf-8')
    return true
  } catch {
    return false
  }
}

async function main() {
  await mkdir(CACHE_DIR, { recursive: true })

  const reuse = process.env.CV_CACHE_REUSE === '1'
  const skipped = []
  const fetched = []

  for (const [action, filename] of ACTIONS) {
    const file = resolve(CACHE_DIR, filename)
    if (reuse && (await cacheExists(file))) {
      skipped.push(filename)
      continue
    }
    const data = await callApi(action)
    await writeFile(file, `${JSON.stringify(data, null, 2)}\n`, 'utf-8')
    fetched.push(filename)
  }

  // biome-ignore lint/suspicious/noConsole: CLI script output
  console.log(
    `[fetch-cv-cache] OK — base=${API_BASE}, fetched=${fetched.length}, ` +
      `skipped=${skipped.length}`,
  )
  if (fetched.length > 0) {
    // biome-ignore lint/suspicious/noConsole: CLI script output
    console.log(`  fetched: ${fetched.join(', ')}`)
  }
}

main().catch((err) => {
  console.error(err.message ?? err)
  process.exit(1)
})
