# 11. Navbar dropdown fix: NicheDropdown + MobileNavDrawer

> Referencia tecnica + tests E2E del fix del bug de "Otras vistas" en
> desktop y mobile. Sidecar del commit dedicado en
> [06-commits.md](06-commits.md).

[← 10](10-view-transitions-design.md) · [README](README.md)

## Resumen del bug (reportado por el usuario)

| Aspecto | Sintoma actual | Esperado |
|---------|----------------|----------|
| Desktop ≥768px | "Otras vistas" aparece desplegado y no parece cerrar / cierra inconsistente tras navegar | Toggle limpio: click trigger abre/cierra; click fuera cierra; Escape cierra; estable tras navegacion |
| Mobile <768px | La seccion "Otras vistas" en el drawer renderiza los 5 items SIEMPRE expandidos (ocupa media pantalla) | Seccion colapsable: summary + chevron; cerrada por default; click expande/colapsa |

## Diagnostico tecnico

### Desktop — `packages/ui/src/components/NicheDropdown.astro`

El componente actual (lineas 96-148) tiene:

- Un trigger con `aria-haspopup="menu"` + `aria-expanded` y un `<ul>`
  con `hidden`.
- Toggle binding ok.
- `document.addEventListener('click', ...)` y
  `root.addEventListener('keydown', ...)` se agregan **cada vez** que
  `setupDropdowns()` corre.
- `data-bound='1'` previene re-binding del trigger, PERO los listeners
  de nivel `document` y `root.keydown` se anaden sin proteccion.
- `astro:after-swap` re-ejecuta `setupDropdowns()` → mas listeners
  acumulados, sin limpiar los previos.

Cuando se habilita `<ClientRouter />` en commit 10, el problema empeora:
cada navegacion deja N+1 listeners. Sintomas observables:

- El close-on-outside-click dispara varias veces sobre nodos huerfanos
  del DOM previo (no visibles, pero consumen handlers).
- En navegaciones rapidas, el dropdown puede quedar "trabado" abierto
  porque el handler que lo cerraria apunta a un nodo ya removido.

### Mobile — `packages/ui/src/components/MobileNavDrawer.astro`

Las lineas 91-115 renderizan:

```astro
<li class="mobile-nav-drawer__section">
  <span class="mobile-nav-drawer__section-title">{item.label}</span>
  <ul class="mobile-nav-drawer__sublist">
    {item.dropdownItems.map((sub) => <li>...</li>)}
  </ul>
</li>
```

NO hay button ni toggle. El `<span>` con el label es solo texto.
Los 5 items siempre visibles. UX inconsistente con desktop.

## Fix 1 — `NicheDropdown.astro` con AbortController

```astro
<script>
  type DropdownInstance = {
    root: HTMLElement
    abort: AbortController
  }

  let instances: DropdownInstance[] = []

  function teardown(): void {
    for (const inst of instances) {
      inst.abort.abort()
    }
    instances = []
  }

  function setupDropdowns(): void {
    teardown()  // asegura limpieza antes de re-bind

    const dropdowns = document.querySelectorAll<HTMLDivElement>(
      '[data-niche-dropdown]',
    )
    for (const root of dropdowns) {
      const trigger = root.querySelector<HTMLButtonElement>(
        '[data-niche-dropdown-trigger]',
      )
      const menu = root.querySelector<HTMLUListElement>(
        '[data-niche-dropdown-menu]',
      )
      if (!(trigger && menu)) continue

      const abort = new AbortController()
      const signal = abort.signal

      const close = (): void => {
        trigger.setAttribute('aria-expanded', 'false')
        menu.hidden = true
      }
      const open = (): void => {
        trigger.setAttribute('aria-expanded', 'true')
        menu.hidden = false
      }

      trigger.addEventListener(
        'click',
        (ev) => {
          ev.stopPropagation()
          const expanded = trigger.getAttribute('aria-expanded') === 'true'
          if (expanded) close()
          else open()
        },
        { signal },
      )

      root.addEventListener(
        'keydown',
        (ev) => {
          if (ev.key === 'Escape') {
            close()
            trigger.focus()
          }
        },
        { signal },
      )

      document.addEventListener(
        'click',
        (ev) => {
          if (!root.contains(ev.target as Node)) close()
        },
        { signal },
      )

      instances.push({ root, abort })
    }
  }

  setupDropdowns()
  // ClientRouter lifecycle: cleanup ANTES del swap, re-bind DESPUES.
  document.addEventListener('astro:before-swap', teardown)
  document.addEventListener('astro:after-swap', setupDropdowns)
</script>
```

### Cambios vs el codigo actual

1. `instances[]` lleva referencia a cada `AbortController` activo.
2. `teardown()` aborta todos antes de re-bind.
3. Cada listener (`trigger.click`, `root.keydown`, `document.click`)
   recibe `{ signal }` → al abortar, el browser los remueve atomicamente.
4. `data-bound` se elimina (innecesario con cleanup explicito).
5. Se enlaza `astro:before-swap` para limpiar ANTES del swap (no
   queda nada apuntando al DOM previo).

### Test unit (Vitest, happy-dom)

`packages/ui/tests/unit/components/NicheDropdown.test.ts`:

```typescript
import { describe, expect, it, vi } from 'vitest'

describe('NicheDropdown', () => {
  it('Given trigger When click Then aria-expanded toggles', () => { /* ... */ })

  it('Given menu open When click outside Then menu closes', () => { /* ... */ })

  it('Given menu open When Escape Then closes and trigger keeps focus', () => { /* ... */ })

  it('Given astro:before-swap When event fires Then all listeners cleanup', () => {
    // Setup: instance creada con AbortController.
    // Trigger astro:before-swap event.
    // Assert: trigger.click ya NO togglea (signal abortado).
  })

  it('Given multiple navigations When astro:after-swap fires N times Then listeners stay at 1 per instance', () => {
    // Setup: spy en document.addEventListener.
    // Disparar astro:after-swap 3 veces.
    // Assert: cada nuevo bind viene precedido por teardown (count de signals abortados == 3).
  })
})
```

## Fix 2 — `MobileNavDrawer.astro` con `<details>`

```astro
<!-- antes: lineas 91-115 -->
<li class="mobile-nav-drawer__section">
  <details class="mobile-nav-drawer__details" data-mobile-niche-details>
    <summary class="mobile-nav-drawer__summary">
      <span class="mobile-nav-drawer__section-title text-mono-label">
        {item.label}
      </span>
      <svg class="mobile-nav-drawer__summary-chevron" width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </summary>
    <ul class="mobile-nav-drawer__sublist">
      {item.dropdownItems.map((sub) => (
        <li>
          <a
            href={sub.href}
            class:list={[
              'mobile-nav-drawer__sublink',
              { 'is-current': sub.current },
            ]}
            aria-current={sub.current ? 'page' : undefined}
          >
            <span>{sub.label}</span>
            {sub.current && currentViewLabel && (
              <span class="mobile-nav-drawer__sublink-meta text-mono-label">
                {currentViewLabel}
              </span>
            )}
          </a>
        </li>
      ))}
    </ul>
  </details>
</li>
```

### CSS adicional

```css
.mobile-nav-drawer__details {
  margin-top: var(--space-12);
  padding-top: var(--space-12);
  border-top: 1px solid var(--color-border);
}
.mobile-nav-drawer__summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-8);
  padding: var(--space-12);
  cursor: pointer;
  list-style: none;
  color: var(--color-text-muted);
  font-size: var(--font-size-14);
  border-radius: var(--radius-sm);
}
.mobile-nav-drawer__summary::-webkit-details-marker {
  display: none;
}
.mobile-nav-drawer__summary:hover,
.mobile-nav-drawer__summary:focus-visible {
  background: var(--color-surface-2);
  color: var(--color-text);
  outline: none;
}
.mobile-nav-drawer__summary-chevron {
  transition: transform var(--motion-fast) var(--easing-out);
}
.mobile-nav-drawer__details[open] .mobile-nav-drawer__summary-chevron {
  transform: rotate(180deg);
}
.mobile-nav-drawer__details[open] .mobile-nav-drawer__sublist {
  animation: details-expand var(--motion-fast) var(--easing-out);
}
@keyframes details-expand {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}
@media (prefers-reduced-motion: reduce) {
  .mobile-nav-drawer__summary-chevron,
  .mobile-nav-drawer__details[open] .mobile-nav-drawer__sublist {
    animation: none;
    transition: none;
  }
}
```

### Reset al cerrar el drawer

En el script de inicializacion del drawer (parte de
`packages/ui/src/lib/init-mobile-nav.ts`):

```typescript
function resetDropdownsOnClose(dialog: HTMLDialogElement): void {
  dialog.addEventListener('close', () => {
    const detailsList = dialog.querySelectorAll<HTMLDetailsElement>(
      '[data-mobile-niche-details]',
    )
    detailsList.forEach((d) => { d.open = false })
  })
}
```

## Tests E2E (Playwright)

`tests/feature/specs/navbar.spec.ts`:

```typescript
import { test, expect } from '@playwright/test'

const APPS = [
  { name: 'generic', host: 'localhost' },
  { name: 'hub', host: 'hub.localhost' },
  { name: 'fintech', host: 'fintech.localhost' },
  { name: 'architect', host: 'architect.localhost' },
  { name: 'leader', host: 'leader.localhost' },
  { name: 'vibe', host: 'vibe.localhost' },
]

const PROXY_PORT = process.env.PROXY_PORT ?? '9970'

for (const { name, host } of APPS) {
  test.describe(`navbar — ${name}`, () => {
    test.describe('desktop (1280x800)', () => {
      test.use({ viewport: { width: 1280, height: 800 } })

      test('NicheDropdown trigger toggles open/close [AC-12]', async ({ page }) => {
        await page.goto(`http://${host}:${PROXY_PORT}/`)
        const trigger = page.locator('[data-niche-dropdown-trigger]')
        const menu = page.locator('[data-niche-dropdown-menu]')

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

      test('click outside closes the menu [AC-12]', async ({ page }) => {
        await page.goto(`http://${host}:${PROXY_PORT}/`)
        await page.locator('[data-niche-dropdown-trigger]').click()
        await page.mouse.click(10, 10)
        await expect(page.locator('[data-niche-dropdown-menu]')).toBeHidden()
      })

      test('Escape closes the menu and returns focus [AC-12]', async ({ page }) => {
        await page.goto(`http://${host}:${PROXY_PORT}/`)
        const trigger = page.locator('[data-niche-dropdown-trigger]')
        await trigger.click()
        await page.keyboard.press('Escape')
        await expect(page.locator('[data-niche-dropdown-menu]')).toBeHidden()
        await expect(trigger).toBeFocused()
      })

      test('stays stable across ClientRouter navigation [AC-12]', async ({ page }) => {
        await page.goto(`http://${host}:${PROXY_PORT}/`)
        await page.click('nav a[href$="/projects"]')
        await page.waitForLoadState('networkidle')
        await page.click('nav a[href$="/"]')
        await page.waitForLoadState('networkidle')

        const trigger = page.locator('[data-niche-dropdown-trigger]')
        await trigger.click()
        await expect(page.locator('[data-niche-dropdown-menu]')).toBeVisible()
        await trigger.click()
        await expect(page.locator('[data-niche-dropdown-menu]')).toBeHidden()
      })
    })

    test.describe('mobile (375x667)', () => {
      test.use({ viewport: { width: 375, height: 667 } })

      test('hamburger opens drawer and dropdown section is collapsed [AC-13]', async ({ page }) => {
        await page.goto(`http://${host}:${PROXY_PORT}/`)
        const hamburger = page.locator('[data-mobile-nav-trigger]')
        await expect(hamburger).toBeVisible()

        // NicheDropdown desktop hidden
        await expect(page.locator('[data-niche-dropdown]')).toBeHidden()

        await hamburger.click()
        const dialog = page.locator('[data-mobile-nav-dialog]')
        await expect(dialog).toBeVisible()

        const details = page.locator('[data-mobile-niche-details]')
        await expect(details).toHaveJSProperty('open', false)

        await details.locator('summary').click()
        await expect(details).toHaveJSProperty('open', true)

        // 5 items dentro
        await expect(details.locator('a')).toHaveCount(5)
      })

      test('closing drawer resets details to collapsed [AC-13]', async ({ page }) => {
        await page.goto(`http://${host}:${PROXY_PORT}/`)
        await page.locator('[data-mobile-nav-trigger]').click()
        const details = page.locator('[data-mobile-niche-details]')
        await details.locator('summary').click()
        await expect(details).toHaveJSProperty('open', true)

        await page.locator('[data-mobile-nav-close]').click()
        await page.locator('[data-mobile-nav-trigger]').click()
        await expect(details).toHaveJSProperty('open', false)
      })
    })

    test.describe('breakpoint transition', () => {
      test('resize desktop → mobile hides niche dropdown without freezing [AC-14]', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 800 })
        await page.goto(`http://${host}:${PROXY_PORT}/`)
        await page.locator('[data-niche-dropdown-trigger]').click()
        await expect(page.locator('[data-niche-dropdown-menu]')).toBeVisible()

        await page.setViewportSize({ width: 375, height: 667 })

        await expect(page.locator('[data-niche-dropdown]')).toBeHidden()
        await expect(page.locator('[data-mobile-nav-trigger]')).toBeVisible()
      })
    })
  })
}
```

### Notas de los E2E

- **Breakpoint**: el CSS actual usa `@media (min-width: 768px)`. Los
  tests viewport 1280 y 375 cruzan ese punto.
- **Items count = 5**: los 5 niches del portfolio (fintech, architect,
  leader, vibe, generic). Si en el futuro se agrega uno, ajustar.
- **Selectores `data-*`**: el plan ya usa `data-niche-dropdown*` y se
  agregan `data-mobile-nav-trigger`, `data-mobile-nav-dialog`,
  `data-mobile-nav-close`, `data-mobile-niche-details`. Documentar en
  el commit que estos `data-*` son contrato del E2E (no removerlos sin
  actualizar tests).
- **`networkidle` tras nav**: el view transition fade dura 300ms; el
  flow Playwright espera el `astro:after-swap` implicitamente.

## Audit antes del PR

```bash
# Listeners fugados en NicheDropdown (manual, DevTools console):
#   getEventListeners(document).click.length  → max 1 + listeners de otros components
#   En produccion: usar window.__DEBUG_LISTENERS__ helper si se agrega.

# Selectores data-* existen en cada app
for app in generic hub fintech architect leader vibe; do
  rg -l "data-niche-dropdown" apps/$app/ packages/ui/ || echo "MISSING: $app"
done

# Tests E2E pasan en chromium
python devtools/run.py test_runner --module=feature --type=feature --env=local \
  -- --grep="navbar"
```

## Referencias

- MDN: [AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)
- MDN: [`<details>` element](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/details)
- Astro: [Client-side router events](https://docs.astro.build/en/guides/view-transitions/#lifecycle-events)
- WAI-ARIA: [Disclosure pattern](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/)

---

Volver al [README](README.md).
