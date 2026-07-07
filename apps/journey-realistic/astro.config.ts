/**
 * @config astro
 * @description Astro config para apps/journey-realistic (banco de pruebas
 *   experimental del plan docs/specs/journey-npc-realism — NPCs humanoides
 *   .glb riggeados en vez de las primitivas procedurales de apps/journey).
 *   Copia de apps/journey; esta app NO se despliega (sin custom domain,
 *   sin entrada en el matrix de deploy-apps.yml), por eso NO usa
 *   `buildSiteUrl` de @portfolio/app-shared (evita extender el tipo
 *   SiteKey compartido por un experimento sin deploy).
 */

import { existsSync, readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import sitemap from '@astrojs/sitemap'
import yaml from '@modyfi/vite-plugin-yaml'
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

const SITE = process.env.SITE_URL ?? 'http://localhost:4328'

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
    plugins: [yaml({ schema: JSON_SCHEMA }), tailwindcss()],
    // three llega por dynamic import (chunk 3D): prebundlearlo evita la
    // re-optimizacion de vite a mitad de la primera carga en dev
    optimizeDeps: {
      include: ['three'],
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
