import type { Page } from '@playwright/test'

/**
 * @function inspectOverlay
 * @description Pausa la ejecucion del test e inyecta un overlay
 *   informativo (URL, viewport, browser) sobre la pagina para debugging
 *   manual con `--headed`. Solo activo si DEBUG_INSPECT=1.
 *
 * @example
 *   import { inspectOverlay } from '../helpers/inspect-overlay.js';
 *   ...
 *   await page.goto('/');
 *   await inspectOverlay(page);
 */
export async function inspectOverlay(page: Page): Promise<void> {
  if (process.env.DEBUG_INSPECT !== '1') return

  await page.evaluate(() => {
    const overlay = document.createElement('div')
    overlay.style.cssText = [
      'position: fixed',
      'top: 8px',
      'right: 8px',
      'z-index: 999999',
      'background: rgba(0,0,0,0.85)',
      'color: #fff',
      'padding: 8px 12px',
      'font: 12px monospace',
      'border-radius: 6px',
      'pointer-events: none',
    ].join(';')
    overlay.textContent = `${location.href} · ${innerWidth}x${innerHeight}`
    document.body.appendChild(overlay)
  })

  await page.pause()
}
