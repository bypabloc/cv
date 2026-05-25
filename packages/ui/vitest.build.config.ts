/**
 * @config vitest (build tests)
 * @description Build-tests aparte: corren `pnpm build` real y verifican
 *   el dist. Lentos (~30-60s por test), por eso NO van en el vitest
 *   default. Se corren con `pnpm --filter @portfolio/ui test:build` o
 *   en pre-push con RUN_BUILD_TESTS=1.
 */
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['tests/build/**/*.test.ts'],
    // Cada test puede correr un pnpm build (~30-60s). 3 min margen.
    testTimeout: 180_000,
    hookTimeout: 180_000,
    // Build-tests no se paralelizan (comparten apps/hub/dist).
    fileParallelism: false,
  },
})
