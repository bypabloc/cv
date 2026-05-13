/**
 * @config vitest
 * @description Vitest config para @portfolio/ui. Cubre lib/ vanilla TS.
 *   Componentes .astro NO se testean aqui (no se renderean en JSDOM); su
 *   verificacion es astro check + E2E.
 */
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    environment: 'happy-dom',
    include: ['tests/unit/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json-summary'],
      include: ['src/lib/**/*.ts'],
      exclude: ['**/*.d.ts', 'src/index.ts'],
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
