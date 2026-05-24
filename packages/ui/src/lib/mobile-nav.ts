/**
 * @module mobile-nav
 * @description Hamburger drawer del Nav para mobile (<768px).
 *
 *   Monta listeners en `[data-mobile-nav-toggle]` y `[data-mobile-nav-dialog]`,
 *   abre con `dialog.showModal()` (focus trap + backdrop nativos de <dialog>),
 *   cierra con Esc (nativo), click en `[data-mobile-nav-close]`, o click en
 *   cualquier <a> interno (al navegar).
 *
 *   Sincroniza con el breakpoint --bp-md (768px): si el viewport cruza a
 *   desktop con el drawer abierto, lo cierra automaticamente.
 *
 *   Retorna funcion cleanup para usar en hooks de Astro view transitions.
 *
 * @example
 *   const cleanup = initMobileNav()
 *   document.addEventListener('astro:before-swap', cleanup)
 */

const MD_QUERY = '(min-width: 768px)'

/**
 * @function initMobileNav
 * @description Bootstrappea el drawer mobile. Idempotente: invocar despues
 *   de navegacion via view-transitions reusa los selectores actuales.
 *
 * @returns {() => void} cleanup que remueve todos los listeners
 */
export function initMobileNav(): () => void {
  const toggle = document.querySelector<HTMLElement>('[data-mobile-nav-toggle]')
  const dialog = document.querySelector<HTMLDialogElement>(
    '[data-mobile-nav-dialog]',
  )

  if (!toggle || !dialog) {
    return () => {
      /* noop */
    }
  }

  const handleToggle = (): void => {
    if (!dialog.open) {
      dialog.showModal()
    }
  }

  const handleDialogClick = (event: Event): void => {
    const target = event.target
    if (!(target instanceof Element)) return

    // Cerrar al click en boton de cerrar explicito
    if (target.closest('[data-mobile-nav-close]')) {
      dialog.close()
      return
    }

    // Cerrar al click en link interno (navegacion)
    if (target.closest('a')) {
      dialog.close()
    }
  }

  toggle.addEventListener('click', handleToggle)
  dialog.addEventListener('click', handleDialogClick)

  // Spec tracking-data-completeness (AC-13): cuando el drawer se cierra,
  // colapsa todos los <details> internos (resetea el estado para la
  // proxima apertura).
  const handleDialogClose = (): void => {
    const detailsList = dialog.querySelectorAll<HTMLDetailsElement>(
      '[data-mobile-niche-details]',
    )
    detailsList.forEach((d) => {
      d.open = false
    })
  }
  dialog.addEventListener('close', handleDialogClose)

  // Cerrar drawer si el viewport cruza a desktop
  const mql = window.matchMedia(MD_QUERY)
  const handleMqChange = (e: MediaQueryListEvent): void => {
    if (e.matches && dialog.open) {
      dialog.close()
    }
  }
  mql.addEventListener('change', handleMqChange)

  return (): void => {
    toggle.removeEventListener('click', handleToggle)
    dialog.removeEventListener('click', handleDialogClick)
    dialog.removeEventListener('close', handleDialogClose)
    mql.removeEventListener('change', handleMqChange)
  }
}
