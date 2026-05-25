/**
 * @script build-public-assets
 * @description Pre-build step que genera assets dinámicos a /public:
 *   - cv.html, cv-es.html, cv-en.html (CV ATS-friendly)
 *   - llms.txt (lista de páginas para crawlers de IA)
 *   - robots.txt (allow all + sitemap)
 *
 *   Se ejecuta antes de `astro build` (prebuild en package.json).
 */
import { copyFile, mkdir, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { profile } from '@portfolio/content'
import { renderCvHtml } from '@portfolio/cv-pdf'
import {
  buildApiCatalog,
  buildHeaders,
  buildLlmsTxt,
  buildRedirects,
  buildRobotsTxt,
} from '@portfolio/seo'

const __dirname = dirname(fileURLToPath(import.meta.url))
const PUBLIC_DIR = resolve(__dirname, '../public')
const SITE_URL = process.env.SITE_URL ?? 'https://the-full-stack.com'
const NICHE = 'generic'
const API_ENDPOINT =
  process.env.PUBLIC_API_ENDPOINT ||
  (process.env.BASE_DOMAIN
    ? `https://api.${process.env.BASE_DOMAIN}`
    : 'https://api.portfolio.the-full-stack.com')
const ATS_KEYWORDS = [
  'Senior Full Stack Developer',
  'Senior Software Engineer',
  'Vue 3',
  'Nuxt',
  'TypeScript',
  'Django',
  'Python',
  'AWS',
  'Microservicios',
  'PostgreSQL',
  'Fintech LATAM',
  'Tech Lead',
  'Architect',
  'Claude Code',
]

async function write(path, content) {
  const full = resolve(PUBLIC_DIR, path)
  await mkdir(dirname(full), { recursive: true })
  await writeFile(full, content, 'utf-8')
  console.info(`[public] wrote ${path} (${content.length} bytes)`)
}

async function main() {
  await mkdir(PUBLIC_DIR, { recursive: true })

  // 1. CV HTML — es (default), -es and -en variants
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

  // 2. llms.txt
  const pages = [
    {
      path: '/',
      title: 'Home',
      description: 'Senior Full Stack Engineer (Vue + Django + AWS), 8+ years',
    },
    {
      path: '/about',
      title: 'About',
      description: 'Education, languages, awards, publications, references',
    },
    {
      path: '/certificates',
      title: 'Certificates',
      description: '11 certifications from Udemy and DevTalles',
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
  const llms = buildLlmsTxt({
    siteUrl: SITE_URL,
    profile,
    niche: NICHE,
    pages,
    atsKeywords: ATS_KEYWORDS,
  })
  await write('llms.txt', llms)

  // 3. robots.txt
  await write('robots.txt', buildRobotsTxt(SITE_URL))

  // 4. _headers (Cloudflare Pages) con CSP connect-src del env actual
  await write('_headers', buildHeaders({ apiEndpoint: API_ENDPOINT }))

  // 5. _redirects (alias /sitemap.xml -> /sitemap-index.xml)
  await write('_redirects', buildRedirects())

  // 6. .well-known/api-catalog (RFC9727 linkset apuntando al openapi.json)
  await write(
    '.well-known/api-catalog',
    buildApiCatalog({ siteUrl: SITE_URL, apiEndpoint: API_ENDPOINT }),
  )
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
