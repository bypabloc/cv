import { copyFile, mkdir, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { profile } from '@portfolio/content'
import { renderCvHtml } from '@portfolio/cv-pdf'
import { buildHeaders, buildLlmsTxt, buildRobotsTxt } from '@portfolio/seo'

const __dirname = dirname(fileURLToPath(import.meta.url))
const PUBLIC_DIR = resolve(__dirname, '../public')
const SITE_URL =
  process.env.SITE_URL ?? 'https://vibe.portfolio.the-full-stack.com'
const NICHE = 'vibe'
const API_ENDPOINT =
  process.env.PUBLIC_API_ENDPOINT ??
  (process.env.BASE_DOMAIN
    ? `https://api.${process.env.BASE_DOMAIN}`
    : 'https://api.portfolio.the-full-stack.com')
const ATS_KEYWORDS = [
  'AI-Augmented Developer',
  'Vibe Coding',
  'Claude Code',
  'Cursor',
  'Prompt Engineering',
  'Sub-agents',
  'MCP Servers',
  'GitHub Copilot',
  'VS Code Extension Development',
  'TypeScript',
  'Astro 6',
  'Python 3.14',
  'Developer Tools',
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
        'Pablo Contreras — Vibe Coding · Claude Code · Cursor · Dev tools',
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
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
