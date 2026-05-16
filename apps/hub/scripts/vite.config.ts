/**
 * @config vite
 * @description Vite config para los scripts de prebuild (vite-node) del hub.
 *   Registra el yaml plugin para que cualquier import transitivo de
 *   `@portfolio/content` pueda cargar sus `.yaml` files.
 */
import yaml from '@modyfi/vite-plugin-yaml'
import { JSON_SCHEMA } from 'js-yaml'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [yaml({ schema: JSON_SCHEMA })],
})
