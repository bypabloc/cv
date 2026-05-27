import { copyFile, mkdir, rm, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { profile } from '@portfolio/content'
import { renderCvHtml } from '@portfolio/cv-pdf'
import {
  buildApiCatalog,
  buildHeaders,
  buildMcpServerCard,
  buildLlmsTxt,
  buildRedirects,
  buildRobotsTxt,
} from '@portfolio/seo'

const __dirname = dirname(fileURLToPath(import.meta.url))
const PUBLIC_DIR = resolve(__dirname, '../public')
const SITE_URL =
  process.env.SITE_URL ?? 'https://architect.portfolio.the-full-stack.com'
const NICHE = 'architect'
const API_ENDPOINT =
  process.env.PUBLIC_API_ENDPOINT ||
  (process.env.BASE_DOMAIN
    ? `https://api.${process.env.BASE_DOMAIN}`
    : 'https://api.portfolio.the-full-stack.com')
const ATS_KEYWORDS = [
  'Frontend Architect',
  'Software Architect',
  'Microservices',
  'Microfrontend',
  'Distributed Systems',
  'System Design',
  'Vue 3',
  'Nuxt',
  'TypeScript',
  'Django',
  'AWS',
  'API Gateway',
  'PostgreSQL',
  'Clean Architecture',
]

async function write(p, c) {
  const f = resolve(PUBLIC_DIR, p)
  await mkdir(dirname(f), { recursive: true })
  await writeFile(f, c, 'utf-8')
  console.info(`[public] wrote ${p} (${c.length} bytes)`)
}

async function main() {
  await mkdir(PUBLIC_DIR, { recursive: true })
  const cvEs = renderCvHtml({ locale: 'es', niche: NICHE, enableFilters: true })
  const cvEn = renderCvHtml({ locale: 'en', niche: NICHE, enableFilters: true })
  await write('cv.html', cvEs)
  await write('cv-es.html', cvEs)
  await write('cv-en.html', cvEn)

  // 1b. Copy cv-filters.js bundle (built by @portfolio/cv-filters) to public/
  const cvFiltersBundleSrc = resolve(
    __dirname,
    '../../../packages/cv-filters/dist/cv-filters.js',
  )
  const cvFiltersBundleDest = resolve(PUBLIC_DIR, 'cv-filters.js')
  try {
    await copyFile(cvFiltersBundleSrc, cvFiltersBundleDest)
    console.info('[public] copied cv-filters.js')
  } catch (err) {
    console.warn(
      '[public] cv-filters.js bundle not found at ' +
        cvFiltersBundleSrc +
        '. Run `pnpm --filter @portfolio/cv-filters build` first.',
    )
    throw err
  }
  const pages = [
    {
      path: '/',
      title: 'Home',
      description:
        'Pablo Contreras — Architect · Microservicios · Microfrontends',
    },
    {
      path: '/about',
      title: 'About',
      description: 'Education, languages, awards, publications, references',
    },
    {
      path: '/certificates',
      title: 'Certificates',
      description: 'Technical certifications relevant to this profile',
    },
    {
      path: '/cv.html',
      title: 'CV (HTML)',
      description: 'ATS-friendly CV in Spanish',
    },
    {
      path: '/cv-en.html',
      title: 'CV (EN)',
      description: 'ATS-friendly CV in English',
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
  await write('_headers', buildHeaders({ apiEndpoint: API_ENDPOINT }))

  // 5. _redirects (alias /sitemap.xml -> /sitemap-index.xml)
  await write('_redirects', buildRedirects())

  // 6a. Limpia el archivo viejo .well-known/api-catalog (sin extension)
  //     que existia antes del fix SPA fallback de Fase 1A. Si no se borra,
  //     queda colgado en public/ y se sirve junto al .json.
  await rm(resolve(PUBLIC_DIR, '.well-known/api-catalog'), { force: true })

  // 6b. .well-known/api-catalog.json (RFC9727 linkset; _redirects 200 sirve la URL canonica sin .json)
  await write(
    '.well-known/api-catalog.json',
    buildApiCatalog({ siteUrl: SITE_URL, apiEndpoint: API_ENDPOINT }),
  )

  // 7. .well-known/mcp/server-card.json (MCP server descriptor)
  await write(
    '.well-known/mcp/server-card.json',
    buildMcpServerCard({ siteUrl: SITE_URL }),
  )
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
