/**
 * @script build-public-assets (hub)
 * @description Pre-build step que genera assets dinamicos a /public para el
 *   hub selector. A diferencia de las apps niche, el hub NO renderiza CV:
 *   solo genera robots.txt (con deteccion de entorno + AI crawlers) y un
 *   llms.txt propio que enumera los 5 sitios del portfolio.
 *
 *   Se ejecuta antes de `astro build` (prebuild en package.json).
 */
import { mkdir, rm, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  buildHeaders,
  buildOpenApi,
  buildRedirects,
  buildRobotsTxt,
} from '@portfolio/seo'

const __dirname = dirname(fileURLToPath(import.meta.url))
const PUBLIC_DIR = resolve(__dirname, '../public')
const SITE_URL =
  process.env.SITE_URL ?? 'https://hub.portfolio.the-full-stack.com'
const API_ENDPOINT =
  process.env.PUBLIC_API_ENDPOINT ||
  (process.env.BASE_DOMAIN
    ? `https://api.${process.env.BASE_DOMAIN}`
    : 'https://api.portfolio.the-full-stack.com')

async function write(path, content) {
  const full = resolve(PUBLIC_DIR, path)
  await mkdir(dirname(full), { recursive: true })
  await writeFile(full, content, 'utf-8')
  console.info(`[public] wrote ${path} (${content.length} bytes)`)
}

function buildHubLlmsTxt() {
  return [
    '# Pablo Contreras — Portfolio Hub',
    '',
    '> Pablo Contreras is a senior Full Stack engineer (Vue + Django + AWS)',
    '> with 12+ years of experience, specialized in LATAM fintech (Chile,',
    '> Mexico). This is the entry point to 5 specialized portfolio sites —',
    '> pick the angle that matches your need.',
    '',
    `Canonical: ${SITE_URL}. Author: Pablo Contreras (bypabloc).`,
    'Location: Lima, Peru. Contact: pacg1991@gmail.com.',
    '',
    '## Sites',
    '',
    '- [Generic Full Stack](https://the-full-stack.com): all 12+ years of',
    '  experience, all skills.',
    '- [Fintech LATAM](https://fintech.portfolio.the-full-stack.com): Chile,',
    '  Mexico, debt settlement, credit scoring.',
    '- [Architect](https://architect.portfolio.the-full-stack.com):',
    '  microservices, microfrontend, scalable systems.',
    '- [Tech Lead](https://leader.portfolio.the-full-stack.com): team',
    '  leadership, mentoring, shipping product.',
    '- [Vibe Coding](https://vibe.portfolio.the-full-stack.com): Claude Code,',
    '  Cursor, dev tools, AI workflows.',
    '',
    '## Identity',
    '',
    '- LinkedIn: https://linkedin.com/in/bypabloc',
    '- GitHub: https://github.com/bypabloc',
    '',
    '## Disclosure',
    '',
    'All code in linked repositories is reviewed, tested and maintained by',
    'Pablo Contreras. AI tools (Claude Code, Cursor) are used as accelerators',
    '— never as authors. This llms.txt is honest white-hat content; no prompt',
    'injection or hidden instructions.',
    '',
  ].join('\n')
}

async function main() {
  await mkdir(PUBLIC_DIR, { recursive: true })
  await write('robots.txt', buildRobotsTxt(SITE_URL))
  await write('llms.txt', buildHubLlmsTxt())
  await write('_headers', buildHeaders({ apiEndpoint: API_ENDPOINT }))

  // 5. _redirects (alias /sitemap.xml -> /sitemap-index.xml)
  await write('_redirects', buildRedirects())

  // 6b. /openapi.json (OpenAPI 3.1 spec del backend serverless)
  //     Servido desde el portfolio (mismo origen), no del API Gateway.
  //     El api-catalog.json (Pages Function) linkea aqui via service-desc.
  await write('openapi.json', buildOpenApi({ apiEndpoint: API_ENDPOINT }))

  // 6. Limpieza historica: .well-known/* eran assets en plan ai-audit-level-3-4
  //    pero Cloudflare Pages excluye dotdirs del upload (regla de dotfiles).
  //    Plan ai-audit-level-4 los sirve via Pages Functions
  //    (apps/<niche>/functions/.well-known/*.ts). Si quedan archivos en
  //    public/.well-known/ de builds anteriores, eliminarlos.
  await rm(resolve(PUBLIC_DIR, '.well-known'), { recursive: true, force: true })
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
