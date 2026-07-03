/**
 * @config astro
 * @description Astro config para apps/journey (CV como viaje 3D, Propuesta A).
 *   i18n es default + en, React (isla 3D), Tailwind v4 via @tailwindcss/vite.
 *   Sin sitemap ni postbuilds de discovery: la app aun no se deploya (el PR
 *   de deploy los agrega junto con el SiteKey 'journey').
 */

import { existsSync, readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import react from '@astrojs/react'
import yaml from '@modyfi/vite-plugin-yaml'
import { buildSiteUrl } from '@portfolio/app-shared/lib/site-urls'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'astro/config'
import { JSON_SCHEMA } from 'js-yaml'

// Dev/build local SIN Docker: journey corre suelta en el host (las otras
// apps reciben las env vars del compose o del pre-push hook). Si
// PUBLIC_API_ENDPOINT no viene del entorno, el guard de TrackingPixel
// rompe el render — se extrae SOLO esa key de docker/env/client/.local.
// En CI el archivo no existe (gitignored) y las vars vienen del GH
// Environment: el guard de defensa en profundidad sigue vigente alli.
const CLIENT_ENV_LOCAL = fileURLToPath(
  new URL('../../docker/env/client/.local', import.meta.url),
)
if (!process.env.PUBLIC_API_ENDPOINT && existsSync(CLIENT_ENV_LOCAL)) {
  const line = readFileSync(CLIENT_ENV_LOCAL, 'utf-8')
    .split('\n')
    .find((entry) => entry.startsWith('PUBLIC_API_ENDPOINT='))
  if (line) {
    process.env.PUBLIC_API_ENDPOINT = line
      .slice('PUBLIC_API_ENDPOINT='.length)
      .trim()
  }
}

// journey aun no es un SiteKey (sin deploy en este PR): deriva su hostname
// del patron de los niches (`journey.<BASE_DOMAIN>`) a partir de otro key.
const SITE =
  process.env.SITE_URL ??
  buildSiteUrl('fintech').replace('//fintech.', '//journey.')

export default defineConfig({
  site: SITE,
  output: 'static',
  trailingSlash: 'ignore',
  i18n: {
    defaultLocale: 'es',
    locales: ['es', 'en'],
    routing: {
      prefixDefaultLocale: false,
    },
  },
  integrations: [react()],
  vite: {
    plugins: [yaml({ schema: JSON_SCHEMA }), tailwindcss()],
    optimizeDeps: {
      include: [
        'react',
        'react-dom',
        'react-dom/client',
        'react/jsx-runtime',
        'react/jsx-dev-runtime',
      ],
    },
    ssr: {
      noExternal: [
        '@portfolio/app-shared',
        '@portfolio/content',
        '@portfolio/seo',
        '@portfolio/ui',
      ],
    },
  },
})
