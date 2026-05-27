/**
 * @config astro
 * @description Astro config para apps/vibe.
 */

import react from '@astrojs/react'
import sitemap from '@astrojs/sitemap'
import yaml from '@modyfi/vite-plugin-yaml'
import { buildSiteUrl } from '@portfolio/app-shared/lib/site-urls'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'astro/config'
import { JSON_SCHEMA } from 'js-yaml'

const SITE = process.env.SITE_URL ?? buildSiteUrl('vibe')

export default defineConfig({
  site: SITE,
  output: 'static',
  trailingSlash: 'ignore',
  i18n: {
    defaultLocale: 'es',
    locales: ['es', 'en'],
    routing: { prefixDefaultLocale: false },
  },
  integrations: [sitemap(), react()],
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
        '@portfolio/cv-pdf',
        '@portfolio/seo',
        '@portfolio/ui',
      ],
    },
  },
})
