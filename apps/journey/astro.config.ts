/**
 * @config astro
 * @description Astro config para apps/journey (CV como viaje 3D, Propuesta A).
 *   i18n es default + en, React (isla 3D), Tailwind v4 via @tailwindcss/vite.
 *   Sin sitemap ni postbuilds de discovery: la app aun no se deploya (el PR
 *   de deploy los agrega junto con el SiteKey 'journey').
 */

import react from '@astrojs/react'
import yaml from '@modyfi/vite-plugin-yaml'
import { buildSiteUrl } from '@portfolio/app-shared/lib/site-urls'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'astro/config'
import { JSON_SCHEMA } from 'js-yaml'

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
