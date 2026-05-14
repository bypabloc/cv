/**
 * @config vite
 * @description Build config para el bundle IIFE de cv-filters. Genera
 *   `dist/cv-filters.js`: un script standalone que se inyecta en cada
 *   app via `<script src="/cv-filters.js" defer>`. Output IIFE sin
 *   dependencias externas: el codigo del filter engine queda autocontenido.
 *
 * Target: ES2020 (cubre 95%+ de navegadores modernos en 2026 sin
 *   transpilacion innecesaria). Sin minificacion para hacer auditable el
 *   bundle servido al cliente. Si gzip-size importa, agregar `minify: true`.
 */
import { resolve } from 'node:path'
import { defineConfig } from 'vite'

export default defineConfig({
  build: {
    lib: {
      entry: resolve(__dirname, 'src/cv-filters.bundle.ts'),
      formats: ['iife'],
      name: 'CvFilters',
      fileName: () => 'cv-filters.js',
    },
    target: 'es2020',
    minify: true,
    sourcemap: false,
    rollupOptions: {
      output: {
        extend: false,
      },
    },
    outDir: 'dist',
    emptyOutDir: true,
  },
})
