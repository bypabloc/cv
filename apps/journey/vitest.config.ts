/**
 * @config vitest
 * @description Vitest config para @portfolio/journey: unit tests de la logica
 *   pura de `src/lib/` (rooms, tiers, collision, tour). Registra el yaml
 *   plugin con JSON_SCHEMA porque `@portfolio/content` (dep transitiva de
 *   rooms.ts) carga sus `.yaml` al importarse.
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
      // site-config es wiring de defineSiteConfig (sin logica propia),
      // mismo criterio que content excluyendo src/data/**.
      exclude: ['**/*.d.ts', 'src/lib/site-config.ts'],
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
