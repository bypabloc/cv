/**
 * @module bundle-pages-function
 * @description Bundlea un archivo TypeScript fuente (una Pages Function)
 *   a un archivo JS standalone que Cloudflare Pages reconoce como Function
 *   al desplegar el dist. Usa esbuild en modo Workers (target=es2022,
 *   format=esm, sin externals).
 *
 *   Razon: el deploy actual hace `wrangler pages deploy <dist>`. Wrangler
 *   busca `<dist>/functions/` para Functions; no resuelve workspaces de
 *   pnpm ni hace transpilacion TS de imports a `@portfolio/mcp`. Bundlear
 *   en build elimina ese problema (el .js standalone va al dist con
 *   todo el codigo inline).
 */
import { build } from 'esbuild'

interface BundleParams {
  /** Path absoluto al archivo .ts fuente. */
  entryPoint: string
  /** Path absoluto al archivo .js destino. */
  outFile: string
}

export async function bundlePagesFunction(params: BundleParams): Promise<void> {
  await build({
    entryPoints: [params.entryPoint],
    outfile: params.outFile,
    bundle: true,
    format: 'esm',
    target: 'es2022',
    platform: 'neutral',
    conditions: ['worker', 'browser'],
    mainFields: ['module', 'main'],
    sourcemap: false,
    minify: false,
    logLevel: 'warning',
  })
}
