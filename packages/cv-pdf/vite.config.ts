/**
 * @config vite
 * @description Vite config para `cv-pdf` (CLI standalone via `vite-node`).
 *   Registra `@modyfi/vite-plugin-yaml` con `JSON_SCHEMA` para que el package
 *   `@portfolio/content` pueda cargar sus `.yaml` files en runtime al
 *   importarlo desde este package.
 */
import yaml from '@modyfi/vite-plugin-yaml'
import { JSON_SCHEMA } from 'js-yaml'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [yaml({ schema: JSON_SCHEMA })],
})
