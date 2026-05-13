import { mkdir, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { profile } from '@portfolio/content'
import { renderCvHtml } from '@portfolio/cv-pdf'
import { buildLlmsTxt, buildRobotsTxt } from '@portfolio/seo'

const __dirname = dirname(fileURLToPath(import.meta.url))
const PUBLIC_DIR = resolve(__dirname, '../public')
const SITE_URL = process.env.SITE_URL ?? 'https://architect.the-full-stack.com'
const NICHE = 'architect'

async function write(p, c) {
  const f = resolve(PUBLIC_DIR, p)
  await mkdir(dirname(f), { recursive: true })
  await writeFile(f, c, 'utf-8')
  console.info(`[public] wrote ${p} (${c.length} bytes)`)
}

async function main() {
  await mkdir(PUBLIC_DIR, { recursive: true })
  const cvEs = renderCvHtml({ locale: 'es', niche: NICHE })
  const cvEn = renderCvHtml({ locale: 'en', niche: NICHE })
  await write('cv.html', cvEs)
  await write('cv-es.html', cvEs)
  await write('cv-en.html', cvEn)
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
    buildLlmsTxt({ siteUrl: SITE_URL, profile, niche: NICHE, pages }),
  )
  await write('robots.txt', buildRobotsTxt(SITE_URL))
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
