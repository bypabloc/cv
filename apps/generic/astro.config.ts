/**
 * @config astro
 * @description Astro config para apps/generic. Site URL, i18n (es default + en),
 *   sitemap integration, Tailwind v4 via @tailwindcss/vite.
 */
import sitemap from '@astrojs/sitemap'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'astro/config'

const SITE = process.env.SITE_URL ?? 'https://hub.the-full-stack.com'

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
