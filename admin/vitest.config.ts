import path from 'node:path'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

/**
 * @config vitest.config.ts
 * @description Unit tests del admin: happy-dom + coverage v8 (>= 80% per-file).
 *
 * Aliases @ -> src y @tests -> tests espejando tsconfig#paths.
 * Excluye de coverage: shadcn primitives, barrels, layouts, pages, types.
 */
export default defineConfig({
  plugins: [react()],
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
        'src/app/**',
        'src/components/ui/**',
        'src/types/**',
        'src/styles/**',
      ],
      thresholds: {
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
