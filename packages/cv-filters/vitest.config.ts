/**
 * @config vitest
 * @description Vitest config para cv-filters. Usa happy-dom para tests que
 *   manipulan DOM (apply-filters, sync-url). Coverage v8 con threshold
 *   per-file >= 80%.
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
      include: ['src/**/*.ts'],
      exclude: [
        '**/*.d.ts',
        'src/index.ts',
        'src/types.ts',
        'src/cv-filters.bundle.ts',
      ],
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
