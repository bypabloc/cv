import path from 'node:path'
import { defineConfig } from 'vitest/config'

/**
 * @config vitest.config.ts
 * @description Unit tests del admin: happy-dom + coverage v8 (>= 80% per-file).
 *
 * JSX via esbuild (runtime automatic). NO se usa `@vitejs/plugin-react`: en
 * este workspace `plugin-react@6` quedo resuelto contra vite 7 (su peer es
 * vite ^8) e importa `vite/internal`, que vite 7 no exporta -> rompe la carga
 * de la config. Los unit tests no necesitan Fast Refresh ni el React Compiler,
 * asi que basta la transformacion JSX de esbuild.
 *
 * Aliases @ -> src y @tests -> tests espejando tsconfig#paths.
 * Excluye de coverage: shadcn primitives, barrels, layouts, pages, types.
 */
export default defineConfig({
  esbuild: { jsx: 'automatic', jsxImportSource: 'react' },
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./tests/setup.ts'],
    css: false,
    include: ['tests/unit/**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/**/*.d.ts',
        'src/**/index.ts',
        'src/**/query-keys.ts',
        'src/app/**',
        'src/components/ui/**',
        'src/components/msw-provider.tsx',
        'src/providers/**',
        'src/types/**',
        'src/styles/**',
      ],
      thresholds: {
        perFile: true,
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@tests': path.resolve(__dirname, './tests'),
    },
  },
})
