import type { NextConfig } from 'next'

/**
 * @config next.config.ts
 * @description Config del admin SPA: export estatico para Cloudflare Pages.
 *
 * output: 'export' genera HTML/JS estatico en out/ (sin server runtime).
 * images.unoptimized: Cloudflare Pages no corre el optimizador de imagenes.
 * trailingSlash: Cloudflare Pages prefiere paths con slash final.
 * reactCompiler: auto-memoization stable en Next 16.2 (sin useMemo/useCallback).
 */
const nextConfig: NextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
  },
  trailingSlash: true,
  poweredByHeader: false,
  productionBrowserSourceMaps: false,
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    tsconfigPath: './tsconfig.json',
  },
  reactCompiler: true,
}

export default nextConfig
