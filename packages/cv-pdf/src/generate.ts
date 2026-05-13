/**
 * @script generate
 * @description Genera cv-{es,en}.html y opcionalmente cv-{es,en}.pdf desde
 *   las content collections. PDF requiere PUPPETEER instalado; si no esta,
 *   solo emite HTML.
 *
 *   Uso desde apps:
 *     pnpm --filter @portfolio/cv-pdf run generate -- \
 *       --niche generic \
 *       --out ../../apps/generic/public \
 *       --pdf
 */
import { mkdir, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { parseArgs } from 'node:util'
import type { Niche } from '@portfolio/content'
import { renderCvHtml } from './lib/render-cv-html'

interface CliOptions {
  niche: Niche
  out: string
  pdf: boolean
}

function parseCli(): CliOptions {
  const { values } = parseArgs({
    options: {
      niche: { type: 'string', default: 'generic' },
      out: { type: 'string', default: './dist' },
      pdf: { type: 'boolean', default: false },
    },
    allowPositionals: true,
  })
  return {
    niche: (values.niche ?? 'generic') as Niche,
    out: values.out ?? './dist',
    pdf: Boolean(values.pdf),
  }
}

interface PuppeteerPage {
  setContent: (html: string, opts: { waitUntil: string }) => Promise<void>
  pdf: (opts: Record<string, unknown>) => Promise<unknown>
}

interface PuppeteerBrowser {
  newPage: () => Promise<PuppeteerPage>
  close: () => Promise<void>
}

interface PuppeteerModule {
  launch: (opts?: { args?: string[] }) => Promise<PuppeteerBrowser>
}

async function loadPuppeteer(): Promise<PuppeteerModule | null> {
  try {
    // Optional peer: 'puppeteer' may not be installed (kept out of deps to
    // avoid pulling Chromium into every CI run). Resolve dynamically.
    const mod = (await import(/* @vite-ignore */ 'puppeteer' as string).catch(
      () => null,
    )) as { default?: PuppeteerModule } | PuppeteerModule | null
    if (!mod) return null
    return (
      'default' in mod && mod.default ? mod.default : mod
    ) as PuppeteerModule
  } catch {
    return null
  }
}

async function maybeRenderPdf(html: string, outPath: string): Promise<boolean> {
  const puppeteer = await loadPuppeteer()
  if (!puppeteer) {
    console.warn(
      `[cv-pdf] puppeteer not installed; skipping PDF for ${outPath}`,
    )
    return false
  }
  try {
    const browser = await puppeteer.launch({
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    })
    try {
      const page = await browser.newPage()
      await page.setContent(html, { waitUntil: 'networkidle0' })
      await page.pdf({
        path: outPath,
        format: 'A4',
        printBackground: true,
        margin: { top: '16mm', bottom: '16mm', left: '14mm', right: '14mm' },
      })
    } finally {
      await browser.close()
    }
    return true
  } catch (err) {
    console.warn(
      `[cv-pdf] failed to render PDF for ${outPath}:`,
      err instanceof Error ? err.message : err,
    )
    return false
  }
}

async function main(): Promise<void> {
  const opts = parseCli()
  const outDir = resolve(opts.out)
  await mkdir(outDir, { recursive: true })

  for (const locale of ['es', 'en'] as const) {
    const html = renderCvHtml({ locale, niche: opts.niche })
    const htmlPath = resolve(outDir, `cv-${locale}.html`)
    await writeFile(htmlPath, html, 'utf-8')
    console.info(`[cv-pdf] wrote ${htmlPath} (${html.length} bytes)`)

    if (opts.pdf) {
      const pdfPath = resolve(outDir, `cv-${locale}.pdf`)
      await maybeRenderPdf(html, pdfPath)
    }
  }

  // Default cv.html / cv.pdf = español
  const esHtml = renderCvHtml({ locale: 'es', niche: opts.niche })
  await writeFile(resolve(outDir, 'cv.html'), esHtml, 'utf-8')
  if (opts.pdf) await maybeRenderPdf(esHtml, resolve(outDir, 'cv.pdf'))
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
