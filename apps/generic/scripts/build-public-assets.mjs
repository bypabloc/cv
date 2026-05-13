/**
 * @script build-public-assets
 * @description Pre-build step que genera assets dinámicos a /public:
 *   - cv.html, cv-es.html, cv-en.html (CV ATS-friendly)
 *   - llms.txt (lista de páginas para crawlers de IA)
 *   - robots.txt (allow all + sitemap)
 *
 *   Se ejecuta antes de `astro build` (prebuild en package.json).
 */
import { mkdir, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { profile } from '@portfolio/content'
import { renderCvHtml } from '@portfolio/cv-pdf'
import { buildLlmsTxt, buildRobotsTxt } from '@portfolio/seo'

const __dirname = dirname(fileURLToPath(import.meta.url))
const PUBLIC_DIR = resolve(__dirname, '../public')
const SITE_URL = process.env.SITE_URL ?? 'https://hub.the-full-stack.com'
const NICHE = 'generic'

async function write(path, content) {
  const full = resolve(PUBLIC_DIR, path)
  await mkdir(dirname(full), { recursive: true })
  await writeFile(full, content, 'utf-8')
  console.info(`[public] wrote ${path} (${content.length} bytes)`)
}

async function main() {
  await mkdir(PUBLIC_DIR, { recursive: true })

  // 1. CV HTML — es (default), -es and -en variants
  const cvEs = renderCvHtml({ locale: 'es', niche: NICHE })
  const cvEn = renderCvHtml({ locale: 'en', niche: NICHE })
  await write('cv.html', cvEs)
  await write('cv-es.html', cvEs)
  await write('cv-en.html', cvEn)

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
  const llms = buildLlmsTxt({ siteUrl: SITE_URL, profile, niche: NICHE, pages })
  await write('llms.txt', llms)

  // 3. robots.txt
  await write('robots.txt', buildRobotsTxt(SITE_URL))
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
