/**
 * @config vitest
 * @description Vitest config para @portfolio/app-shared: unit tests con coverage v8.
 *   Registra `@modyfi/vite-plugin-yaml` (con JSON_SCHEMA) para que el package
 *   `@portfolio/content` pueda cargar sus `.yaml` files al ser importado desde
 *   tests/lib/* (ej. build-stats que importa `experiences`, `certificates`).
 *
 *   Excluye `define-site-config.ts` y `site-config.ts` del coverage scope:
 *   son adapters trivials sobre helpers de Astro/runtime.
 */
import yaml from '@modyfi/vite-plugin-yaml'
import { JSON_SCHEMA } from 'js-yaml'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [yaml({ schema: JSON_SCHEMA })],
  test: {
    globals: true,
    environment: 'node',
    include: ['tests/unit/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json-summary'],
      include: ['src/lib/**/*.ts'],
      exclude: ['**/*.d.ts', 'src/index.ts', 'src/lib/site-config.ts'],
      thresholds: {
        perFile: true,
        statements: 80,
        branches: 80,
        functions: 80,
        lines: 80,
      },
    },
  },
})
