/**
 * @config vitest
 * @description Vitest config para @portfolio/mcp. Tras Fase 1
 *   (ai-audit-level-4), el package NO importa @portfolio/content en
 *   runtime; los tests usan fakes/mocks puros. Sin plugin yaml.
 */
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['tests/unit/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json-summary'],
      include: ['src/lib/**/*.ts'],
      exclude: ['**/*.d.ts', 'src/index.ts', 'src/lib/tools/index.ts'],
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
