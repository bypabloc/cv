/**
 * @config vite
 * @description Vite config para los scripts de prebuild (vite-node). Solo
 *   registra el yaml plugin para que `@portfolio/content` pueda cargar
 *   sus `.yaml` files al ser importado desde scripts/*.mjs.
 *
 *   NO es el config de la app Astro (ese vive en `astro.config.ts`).
 *   vite-node lo lee porque pasamos `--config` al CLI.
 */
import yaml from '@modyfi/vite-plugin-yaml'
import { JSON_SCHEMA } from 'js-yaml'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [yaml({ schema: JSON_SCHEMA })],
})
