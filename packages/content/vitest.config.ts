/**
 * @config vitest
 * @description Vitest config para @portfolio/content: unit tests con coverage v8.
 *   Registra `@modyfi/vite-plugin-yaml` con `JSON_SCHEMA` (de js-yaml) para que
 *   los YAML 1.2 NO resuelvan strings tipo `2024-01-15` como Date objects. Las
 *   fechas se mantienen como string (lo que esperan los Zod schemas Date/YearMonth).
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
      exclude: ['src/data/**', '**/*.d.ts', 'src/index.ts'],
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
