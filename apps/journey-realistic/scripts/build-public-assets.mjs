import { mkdir, rm, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { profile } from '@portfolio/content'
import {
  buildHeaders,
  buildLlmsTxt,
  buildOpenApi,
  buildRedirects,
  buildRobotsTxt,
} from '@portfolio/seo'

const __dirname = dirname(fileURLToPath(import.meta.url))
const PUBLIC_DIR = resolve(__dirname, '../public')
const SITE_URL = process.env.SITE_URL ?? 'http://localhost:4328'
// journey recorre el CV COMPLETO: usa el curriculum del niche generic.
const NICHE = 'generic'
const API_ENDPOINT =
  process.env.PUBLIC_API_ENDPOINT ||
  (process.env.BASE_DOMAIN
    ? `https://api.${process.env.BASE_DOMAIN}`
    : 'https://api.portfolio.the-full-stack.com')
const ATS_KEYWORDS = [
  'Interactive 3D CV',
  'three.js',
  'React Three Fiber',
  'WebGL',
  'Creative Developer',
  'TypeScript',
  'Astro 6',
  'Full Stack Senior',
  'Vue',
  'Django',
  'AWS',
]

async function write(p, c) {
  const f = resolve(PUBLIC_DIR, p)
  await mkdir(dirname(f), { recursive: true })
  await writeFile(f, c, 'utf-8')
  console.info(`[public] wrote ${p} (${c.length} bytes)`)
}

async function main() {
  await mkdir(PUBLIC_DIR, { recursive: true })
  // A diferencia de los niches, journey NO genera cv.html propio: la
  // experiencia 3D + el fallback CvSections en pagina son el contenido, y
  // el link "CV" apunta al cv.html de generic (SITE_URLS.generic).
  const pages = [
    {
      path: '/',
      title: 'Home',
      description:
        'Pablo Contreras — el CV como viaje 3D: recorre mi carrera sala por sala (walking-sim en three.js) con fallback de CV completo en HTML',
    },
    {
      path: '/en/',
      title: 'Home (EN)',
      description:
        'Pablo Contreras — the CV as a 3D journey: walk my career room by room (three.js walking-sim) with a full HTML CV fallback',
    },
  ]
  await write(
    'llms.txt',
    buildLlmsTxt({
      siteUrl: SITE_URL,
      profile,
      niche: NICHE,
      pages,
      atsKeywords: ATS_KEYWORDS,
    }),
  )
  await write('robots.txt', buildRobotsTxt(SITE_URL))
  // CSP identica a los niches: troika tipografia en el main thread
  // (configureTextBuilder useWorker:false en text-font.ts), asi que no
  // hace falta relajar worker-src/script-src con blob:.
  await write('_headers', buildHeaders({ apiEndpoint: API_ENDPOINT }))
  await write('_redirects', buildRedirects())
  await write('openapi.json', buildOpenApi({ apiEndpoint: API_ENDPOINT }))

  // Limpieza: .well-known/* se sirve via _worker.js (Advanced Mode), nunca
  // como assets (Cloudflare Pages excluye dotdirs del upload).
  await rm(resolve(PUBLIC_DIR, '.well-known'), { recursive: true, force: true })
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
