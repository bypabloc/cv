# Fases 5-6: Nav dropdown + hub hero

## Fase 5: Nav dropdown con 5 niches

### Contexto

Hoy el Nav tiene un item "Otras vistas" con `external: true` que apunta
a `hub.portfolio.the-full-stack.com` y abre en pestana nueva. El usuario
quiere reemplazarlo por un dropdown que muestre los 5 niches (fintech,
architect, leader, vibe, generic) y navegue a cada uno en la misma
pestana.

### Diseno

#### Estructura del item

`NavItem` necesita soportar tres formas:

1. Link interno (path local, `external: false`)
2. Link externo (`external: true`, abre `_blank`)
3. **Dropdown** (`kind: 'dropdown'`, contiene items)

Cambio minimo: agregar `kind?: 'link' | 'dropdown'` (default 'link') y
`items?: NavItem[]` opcional.

#### URLs por entorno

Definidas en `SITE_URLS` (ya existe en
`packages/app-shared/src/lib/site-urls.ts` o similar). Verificar que
expone:

- `SITE_URLS.fintech.{local,dev,stage,prod}`
- Idem para architect, leader, vibe, generic

El componente `NicheDropdown.astro` recibe el entorno actual (derivado
de `import.meta.env.MODE` o de `Astro.url.host`) y resuelve la URL
correcta de cada niche.

#### Componente nuevo: NicheDropdown.astro

Archivo: `packages/ui/src/components/NicheDropdown.astro`

```astro
---
import { resolveNicheUrls } from '@portfolio/app-shared/lib/site-urls'

interface Props {
  currentNiche: 'fintech' | 'architect' | 'leader' | 'vibe' | 'generic'
  label: string  // texto del button trigger ("Otras vistas" / "Other views")
  closeLabel: string  // a11y "Cerrar dropdown"
}

const { currentNiche, label, closeLabel } = Astro.props
const niches = resolveNicheUrls(Astro.url.host)
// niches = [{ niche: 'fintech', url: '...', label: 'Fintech', current: bool }, ...]
---

<div class="niche-dropdown" data-niche-dropdown>
  <button
    type="button"
    class="niche-dropdown__trigger"
    aria-haspopup="menu"
    aria-expanded="false"
    data-niche-dropdown-trigger
  >
    {label}
    <svg ...><!-- chevron --></svg>
  </button>
  <ul class="niche-dropdown__menu" role="menu" hidden data-niche-dropdown-menu>
    {niches.map((n) => (
      <li role="none">
        <a
          href={n.url}
          role="menuitem"
          class:list={['niche-dropdown__item', { 'is-current': n.current }]}
          aria-current={n.current ? 'page' : undefined}
        >
          {n.label}
        </a>
      </li>
    ))}
  </ul>
</div>

<script>
  // Toggle del dropdown:
  // - click en trigger: toggle aria-expanded
  // - click fuera o Escape: cerrar
  // - misma tab (sin target="_blank")
  // - keyboard nav (arrow up/down, Home/End, Escape)
  // ... (vanilla JS, sin dependencias)
</script>

<style>
  .niche-dropdown { position: relative; }
  .niche-dropdown__menu {
    position: absolute;
    top: 100%;
    right: 0;
    min-width: 200px;
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    padding: var(--space-4);
    z-index: 10;
  }
  /* ... */
</style>
```

A11y obligatoria:

- `aria-haspopup="menu"` en el trigger
- `aria-expanded` toggleable
- `role="menu"` en `<ul>` y `role="menuitem"` en cada `<a>`
- Cerrar con Escape, click fuera, click en item
- Focus trap dentro del menu cuando abierto
- `aria-current="page"` en el niche actual (deshabilitado clickable o
  con feedback visual; el usuario YA esta en ese niche)

#### Integracion en Nav.astro

Archivo: `packages/ui/src/components/Nav.astro`

En el bucle de items, agregar branch para `kind: 'dropdown'`:

```astro
{
  items.map((item) => (
    item.kind === 'dropdown' ? (
      <NicheDropdown
        currentNiche={currentNiche}
        label={item.label}
        closeLabel={...}
      />
    ) : item.external ? (
      <a href={item.href} target="_blank" rel="noopener noreferrer">...</a>
    ) : (
      <a href={item.href}>...</a>
    )
  ))
}
```

#### Update de define-site-config.ts

Archivo: `packages/app-shared/src/lib/define-site-config.ts:79`

Hoy inyecta un item con `external: true` apuntando al hub. Cambiar a un
item dropdown:

```typescript
// Antes:
nav.push({
  key: 'other-views',
  label: t.nav.otherLocaleLink,
  href: SITE_URLS.hub[env],
  external: true,
})

// Despues:
nav.push({
  key: 'other-niches',
  label: 'Otras vistas',  // o desde i18n
  kind: 'dropdown',
})
// El dropdown construye los items internamente desde SITE_URLS
```

El item "Otras vistas" pierde el `href` porque ahora es un dropdown.
La etiqueta del trigger viene del i18n string (puede ser el mismo).

## Fase 6: Hub hero intro

### Contexto

El hero del hub tiene un parrafo `heroIntro` que:

1. Tiene fondo limitado (no se extiende a 100vw como en los otros niches)
2. Es muy largo (>250 caracteres) y la fuente es grande (`text-body-lg`)

### Diseno

#### Cambio CSS: full-bleed background

Archivo: `apps/hub/src/pages/index.astro` (lineas 65-72 aprox)

Tecnica de full-bleed:

```astro
<div class="hero-intro-wrapper">
  <p class="hero-intro text-body text-muted">{sel.heroIntro}</p>
</div>

<style>
  .hero-intro-wrapper {
    /* Full-bleed: ocupa 100vw del viewport */
    width: 100vw;
    margin-left: calc(50% - 50vw);
    padding: var(--space-8) var(--space-6);
    background: var(--color-surface);
    /* Opcionalmente, un degradado sutil */
  }
  .hero-intro {
    max-width: 64ch;
    margin-inline: auto;
    /* Texto centrado horizontalmente dentro del wrapper full-bleed */
  }
</style>
```

#### Cambio i18n: reducir texto

Archivos:

- `packages/content/src/data/i18n/hub-selector/es.yaml`
- `packages/content/src/data/i18n/hub-selector/en.yaml`

Reducir `heroIntro` de ~280 caracteres a 140-180 caracteres. Texto
sugerido:

- ES: "Elige el angulo de mi perfil: fintech, arquitectura, liderazgo, vibe coding o generalista. Cada nicho cuenta la misma historia desde una perspectiva distinta."
- EN: "Pick the angle of my profile: fintech, architecture, leadership, vibe coding, or generalist. Each niche tells the same story from a different perspective."

(Ambos ~150 caracteres.)

#### Cambio de tipografia

En el mismo archivo `apps/hub/src/pages/index.astro`:

```astro
<!-- Antes -->
<p class="text-body-lg text-muted" style="max-width: 56ch">{sel.heroIntro}</p>

<!-- Despues -->
<div class="hero-intro-wrapper">
  <p class="hero-intro text-body text-muted">{sel.heroIntro}</p>
</div>
```

(`text-body` = 14px vs `text-body-lg` = 16px-18px.)

### Verificacion visual

```bash
pnpm --filter @portfolio/hub run dev
# Abrir http://hub.localhost:9970 (o /:port real)
# Verificar:
# - El fondo del intro ocupa todo el ancho de la pantalla
# - El texto esta centrado horizontalmente, max-width ~64ch
# - El texto es mas corto que antes
```

Tomar screenshot manual para confirmar (o `playwright codegen`).
