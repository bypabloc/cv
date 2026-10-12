/**
 * @config astro
 * @description Astro 7 config para apps/post (post.the-full-stack.com):
 *   guias tecnicas estaticas, i18n es (default) + en, sitemap, Shiki con
 *   tema dual (CSS vars, sigue el toggle claro/oscuro) y el remark plugin
 *   que une los capitulos de cada guia en una sola pagina.
 */

import { unified } from '@astrojs/markdown-remark'
import sitemap from '@astrojs/sitemap'
import { buildSiteUrl } from '@portfolio/app-shared/lib/site-urls'
import { defineConfig } from 'astro/config'
import { remarkGuide } from './src/lib/remark-guide'

export default defineConfig({
  site: process.env.SITE_URL ?? buildSiteUrl('post'),
  output: 'static',
  trailingSlash: 'ignore',
  i18n: {
    defaultLocale: 'es',
    locales: ['es', 'en'],
    routing: { prefixDefaultLocale: false },
  },
  integrations: [sitemap()],
  markdown: {
    // Astro 7: el default es Satteri; los plugins remark van en unified().
    processor: unified({ remarkPlugins: [remarkGuide] }),
    shikiConfig: {
      themes: { light: 'github-light', dark: 'github-dark' },
      defaultColor: false,
      langAlias: { cron: 'txt' },
    },
  },
  vite: {
    ssr: { noExternal: ['@portfolio/app-shared', '@portfolio/ui'] },
  },
})
