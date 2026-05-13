/**
 * @config vitest
 * @description Vitest config para cv-pdf. Registra `vite-plugin-yaml` con
 *   JSON_SCHEMA para que el package `@portfolio/content` pueda cargar sus
 *   `.yaml` files al ser importado desde `render-cv-html`.
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
      exclude: ['**/*.d.ts', 'src/index.ts', 'src/generate.ts'],
      thresholds: {
        perFile: true,
        statements: 80,
        branches: 75,
        functions: 80,
        lines: 80,
      },
    },
  },
})
