/**
 * @config astro
 * @description Astro config para apps/fintech.
 */
import sitemap from '@astrojs/sitemap'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'astro/config'

const SITE = process.env.SITE_URL ?? 'https://fintech.the-full-stack.com'

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
    plugins: [tailwindcss()],
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
