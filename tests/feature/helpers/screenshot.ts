import type { Page, TestInfo } from '@playwright/test'

/**
 * @function captureScreenshot
 * @description Toma un screenshot con nombre estandarizado y lo adjunta
 *   al test report. Util para tests visuales o evidencia de fallo.
 *
 * @param page - Playwright Page
 * @param testInfo - TestInfo del test actual
 * @param label - Etiqueta descriptiva para el nombre del archivo
 *
 * @example
 *   test('home renderiza', async ({ page }, testInfo) => {
 *     await page.goto('/');
 *     await captureScreenshot(page, testInfo, 'home-loaded');
 *   });
 */
export async function captureScreenshot(
  page: Page,
  testInfo: TestInfo,
  label: string,
): Promise<void> {
  const sanitized = label.replace(/[^a-z0-9-]+/gi, '-').toLowerCase()
  const path = `${testInfo.outputDir}/${sanitized}.png`
  await page.screenshot({ path, fullPage: true })
  await testInfo.attach(sanitized, { path, contentType: 'image/png' })
}
