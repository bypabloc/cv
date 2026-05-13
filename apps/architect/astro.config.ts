/**
 * @config astro
 * @description Astro config para apps/architect.
 */
import sitemap from '@astrojs/sitemap'
import yaml from '@modyfi/vite-plugin-yaml'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'astro/config'
import { JSON_SCHEMA } from 'js-yaml'

const SITE = process.env.SITE_URL ?? 'https://architect.the-full-stack.com'

export default defineConfig({
  site: SITE,
  output: 'static',
  trailingSlash: 'ignore',
  i18n: {
    defaultLocale: 'es',
    locales: ['es', 'en'],
    routing: { prefixDefaultLocale: false },
  },
  integrations: [sitemap()],
  vite: {
    plugins: [yaml({ schema: JSON_SCHEMA }), tailwindcss()],
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
