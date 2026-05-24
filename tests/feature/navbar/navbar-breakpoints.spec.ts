/**
 * @feature Navbar across breakpoints (NicheDropdown + MobileNavDrawer)
 * @description Spec tracking-data-completeness (AC-12, AC-13, AC-14):
 *   - Desktop (>=768px): NicheDropdown trigger togglea expand/collapse,
 *     cierra al click outside, cierra al Escape (devuelve focus al
 *     trigger).
 *   - Mobile (<768px): hamburger abre <dialog>. La seccion "Otras
 *     vistas" se renderiza como <details> cerrado por default; click
 *     summary expande. Al cerrar el drawer, <details> se resetea.
 *   - Breakpoint resize 1280<->375: el dropdown desktop se oculta
 *     cuando viewport <768px sin freeze visual.
 */
import { expect, subdomainUrl, test } from '../fixtures/index.js'

test.describe('Feature: navbar desktop (1280x800)', () => {
  test.use({ viewport: { width: 1280, height: 800 } })

  test('Given trigger When click Then aria-expanded togglea true/false [AC-12]', async ({
    page,
  }) => {
    await page.goto(`${subdomainUrl()}/`, { waitUntil: 'domcontentloaded' })

    const trigger = page.locator('[data-niche-dropdown-trigger]').first()
    const menu = page.locator('[data-niche-dropdown-menu]').first()

    await expect(trigger).toBeVisible()
    await expect(menu).toBeHidden()
    await expect(trigger).toHaveAttribute('aria-expanded', 'false')

    await trigger.click()
    await expect(menu).toBeVisible()
    await expect(trigger).toHaveAttribute('aria-expanded', 'true')

    await trigger.click()
    await expect(menu).toBeHidden()
    await expect(trigger).toHaveAttribute('aria-expanded', 'false')
  })

  test('Given menu abierto When click outside Then cierra [AC-12]', async ({
    page,
  }) => {
    await page.goto(`${subdomainUrl()}/`, { waitUntil: 'domcontentloaded' })

    const trigger = page.locator('[data-niche-dropdown-trigger]').first()
    const menu = page.locator('[data-niche-dropdown-menu]').first()

    await trigger.click()
    await expect(menu).toBeVisible()

    // Click en una esquina libre del documento
    await page.mouse.click(5, 5)
    await expect(menu).toBeHidden()
  })

  test('Given menu abierto When Escape Then cierra y trigger recibe focus [AC-12]', async ({
    page,
  }) => {
    await page.goto(`${subdomainUrl()}/`, { waitUntil: 'domcontentloaded' })

    const trigger = page.locator('[data-niche-dropdown-trigger]').first()
    const menu = page.locator('[data-niche-dropdown-menu]').first()

    await trigger.click()
    await expect(menu).toBeVisible()

    await page.keyboard.press('Escape')
    await expect(menu).toBeHidden()
    await expect(trigger).toBeFocused()
  })
})

test.describe('Feature: navbar mobile (375x667)', () => {
  test.use({ viewport: { width: 375, height: 667 } })

  test('Given hamburger When click Then drawer abre y <details> "Otras vistas" cerrado por default [AC-13]', async ({
    page,
  }) => {
    await page.goto(`${subdomainUrl()}/`, { waitUntil: 'domcontentloaded' })

    // NicheDropdown desktop debe estar oculto (CSS @media >= 768px)
    const desktopDropdown = page.locator('[data-niche-dropdown]').first()
    // Puede no existir en el DOM (responsive) o estar hidden. Si existe,
    // verificamos que no este visible.
    if ((await desktopDropdown.count()) > 0) {
      await expect(desktopDropdown).toBeHidden()
    }

    const hamburger = page.locator('[data-mobile-nav-toggle]').first()
    await expect(hamburger).toBeVisible()
    await hamburger.click()

    const dialog = page.locator('[data-mobile-nav-dialog]').first()
    await expect(dialog).toBeVisible()

    const details = page.locator('[data-mobile-niche-details]').first()
    await expect(details).toBeVisible()
    // <details> cerrado por default
    await expect(details).not.toHaveJSProperty('open', true)

    // Click summary -> expande
    await details.locator('summary').click()
    await expect(details).toHaveJSProperty('open', true)

    // Items renderizados dentro del details (5 niches; verifica > 0)
    const sublinks = details.locator('a.mobile-nav-drawer__sublink')
    expect(await sublinks.count()).toBeGreaterThan(0)
  })

  test('Given drawer cerrado When reabro Then <details> vuelve a estado cerrado [AC-13]', async ({
    page,
  }) => {
    await page.goto(`${subdomainUrl()}/`, { waitUntil: 'domcontentloaded' })

    const hamburger = page.locator('[data-mobile-nav-toggle]').first()
    await hamburger.click()
    const details = page.locator('[data-mobile-niche-details]').first()
    await details.locator('summary').click()
    await expect(details).toHaveJSProperty('open', true)

    // Cerrar drawer via boton X
    const closeBtn = page.locator('[data-mobile-nav-close]').first()
    await closeBtn.click()

    // Reabrir
    await hamburger.click()
    // <details> resetea a cerrado (handleDialogClose en mobile-nav.ts)
    await expect(details).not.toHaveJSProperty('open', true)
  })
})

test.describe('Feature: navbar breakpoint transition', () => {
  test('Given desktop 1280 con dropdown abierto When resize a 375 Then dropdown se oculta y hamburger aparece [AC-14]', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1280, height: 800 })
    await page.goto(`${subdomainUrl()}/`, { waitUntil: 'domcontentloaded' })

    const trigger = page.locator('[data-niche-dropdown-trigger]').first()
    const menu = page.locator('[data-niche-dropdown-menu]').first()
    await trigger.click()
    await expect(menu).toBeVisible()

    // Cruza el breakpoint 768px
    await page.setViewportSize({ width: 375, height: 667 })

    // El dropdown desktop deja de estar visible (CSS oculta en mobile)
    await expect(menu).toBeHidden()
    // El hamburger pasa a estar visible
    await expect(page.locator('[data-mobile-nav-toggle]').first()).toBeVisible()
  })
})
