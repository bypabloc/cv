/**
 * @function GET llms-full.txt
 * @description Todas las guias de post en es completas en un solo Markdown
 *   (llmstxt.org), con una cabecera por articulo.
 */
import type { APIRoute } from 'astro'
import { llmsFull } from '../lib/llms-full'

export const GET: APIRoute = async ({ site }) =>
  new Response(await llmsFull('es', site?.href.replace(/\/$/, '') ?? ''), {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  })
