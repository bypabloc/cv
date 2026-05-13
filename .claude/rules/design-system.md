---
description: "Design System del portfolio: tokens CSS variables (single source of truth), tipografia, modo dark/light, fonts self-hosted, Tailwind v4 (opcional)."
globs: "src/**,*.astro,*.css,*.ts,*.tsx"
---

# Design System

> Sistema de diseno del portfolio: CSS variables como API publica, escala
> tipografica unificada, modo dark y light (ambos soportados), fonts
> self-hosted via `@fontsource/*`.

## Decisiones (decision log)

1. **Tokens CSS variables como API publica del DS** — todos los componentes
   consumen `var(--color-*)`, `var(--font-size-*)`, etc. Cambiar un token =
   cambiar 1 linea, sin recompilar.
2. **Dark y light soportados (ambos modos)** — `:root` define el modo base.
   El modo alterno se activa via clase en `<html>` (`.light` o `.dark` segun
   cual sea el base), invirtiendo neutrals. Ambos modos deben verse correctos.
3. **Fonts self-hosted via `@fontsource`** — ej. `@fontsource/space-grotesk`
   (400/500/600/700) + `@fontsource/space-mono` (400/700). Mejor SEO,
   GDPR-friendly, CSP estricto. NUNCA Google Fonts CDN.
4. **Tailwind v4 opcional** — si se usa, mapear CSS vars del DS via `@theme inline`
   en el CSS global, para que las utilities respeten los tokens.

## Tokens (CSS variables)

### Colores neutrales (escala 0-95)

| Token | Hex sugerido | Uso |
|-------|--------------|-----|
| `--color-grey-0` | `#FFFFFF` | base light |
| `--color-grey-5` | `#F7F7F5` | bg light |
| `--color-grey-95` | `#0A0A0A` | bg dark (signature dark mode) |
| `--color-grey-90`/`85`/`80`/`70`/`60`/`50`/`40`/`30`/`20`/`15`/`10`/`5` | escala completa | borders, surfaces, text muted |

### Surfaces (semanticos, dark mode)

- `--color-bg`: `var(--color-grey-95)` — fondo principal
- `--color-surface`: `#161616` — cards, secciones
- `--color-surface-2`: `#1F1F1F` — surfaces secundarios
- `--color-border`: `var(--color-grey-15)` — borders sutiles
- `--color-border-strong`: `var(--color-grey-20)` — borders enfaticos

### Texto

- `--color-text`: `#F7F7F5` — texto principal
- `--color-text-muted`: `var(--color-grey-50)` — texto secundario
- `--color-text-subtle`: `var(--color-grey-40)` — texto terciario

### Brand / Primary

- `--color-primary`: brand principal (definir en `tokens.css`)
- `--color-primary-hover`: hover state
- `--color-primary-muted`: bg highlight
- `--color-primary-contrast`: texto sobre primary

### Accents y estados

- `--color-accent-*`: acentos secundarios
- Estados: `--color-success`, `--color-warning`, `--color-danger`, `--color-info`

### Tipografia

```css
/* sizes — base 8 hasta max 52 */
--font-size-8 / -10 / -11 / -12 / -13 / -14 / -16 / -20 / -24 / -32 / -40 / -52

/* line-heights */
--line-height-tight: 1.0
--line-height-snug: 1.55
--line-height-base: 1.6
--line-height-relaxed: 1.65

/* letter-spacings */
--letter-spacing-tight / -snug / -normal / -wide / -wider / -widest

/* Font families */
--font-sans: "Space Grotesk", -apple-system, ...
--font-mono: "Space Mono", "Menlo", ...
```

### Spacing (base 4px)

`--space-3 / -4 / -6 / -8 / -10 / -12 / -16 / -20 / -24 / -32 / -40 / -56 / -72 / -80 / -100`

### Radius

- `--radius-xs`: 6px
- `--radius-sm`: 8px
- `--radius-md`: 12px
- `--radius-pill`: 999px
- `--radius-full`: 50%

### Shadows

- `--shadow-light`: `0 1px 4px rgba(0, 0, 0, 0.08)`
- `--shadow-medium`: `0 4px 16px rgba(0, 0, 0, 0.12)`

### Containers

- `--container-narrow`: 380px
- `--container-medium`: 960px
- `--container-wide`: 1120px

## Mapping CSS vars → Tailwind v4 (opcional)

Si se decide usar Tailwind v4, leer tokens via `@theme inline` en
`src/styles/global.css`:

```css
@theme inline {
  --color-background: var(--color-bg);
  --color-foreground: var(--color-text);
  --color-card: var(--color-surface);
  --color-card-foreground: var(--color-text);
  --color-primary: var(--color-primary);
  --color-primary-foreground: var(--color-primary-contrast);
  --color-border: var(--color-grey-15);
  --color-ring: var(--color-primary);
}
```

Asi `bg-background`, `text-foreground`, `border-border`, etc. son utilities
generadas a partir de los tokens del DS.

### Tipografia (utility classes globales sugeridas)

- `.text-display-1` — 52px, weight 700, tight, tracking-tight
- `.text-h1` — 40px, weight 700
- `.text-h2` — 32px, weight 600
- `.text-h3` — 24px, weight 600
- `.text-h4` — 20px, weight 600
- `.text-h5` — 16px, weight 600
- `.text-h6` — 13px, weight 600, uppercase, tracking-widest
- `.text-body` — 14px, weight 400, snug
- `.text-caption` — 12px, weight 400
- `.text-label` — 11px, weight 500, uppercase, tracking-wide
- `.text-mono` — Space Mono 13px

## Modos dark y light (ambos soportados)

```css
/* :root define el modo base (sin clase) */
:root {
  --color-bg: var(--color-grey-95);
  --color-text: #F7F7F5;
  /* ... */
}

/* Modo alterno (clase .light en <html>) */
:root.light {
  --color-bg: var(--color-grey-5);
  --color-text: #0A0A0A;
  /* ... */
}
```

Implementacion del toggle: vanilla JS en un `<script>` inline en
`BaseLayout.astro` (o componente `ThemeToggle.astro`) que:

1. Lee `localStorage` o `prefers-color-scheme` al cargar (sin flash)
2. Aplica clase al `<html>` antes de que pinten los componentes
3. Toggle escribe a `localStorage` y aplica la clase

Cycle: `dark → light → system → dark`. Ambos modos deben verse correctos
en cualquier componente nuevo.

## Como agregar un token nuevo

1. Editar `src/styles/tokens.css` agregando la var
2. Si se usa Tailwind v4, agregar al bloque `@theme inline` en `src/styles/global.css`
3. Documentar en este archivo si forma parte de la API publica del DS
4. Verificar que ambos modos (dark / light) reciben el token correctamente

## Como agregar un componente UI

1. Crear `src/components/<Name>.astro` (PascalCase, descriptivo)
2. JSDoc en frontmatter (ver `docstring-standard.md`)
3. `data-testid="..."` si se va a testear E2E
4. Tokens del DS via clases Tailwind o `var(--color-*)` directo en `<style>`
5. Crear test mirror si tiene logica (`tests/unit/components/<Name>.test.ts`)

## Fonts self-hosted

Importar via `@fontsource/*` en archivo CSS dedicado:

```css
/* src/styles/fonts.css */
@import '@fontsource/space-grotesk/400.css';
@import '@fontsource/space-grotesk/500.css';
@import '@fontsource/space-grotesk/600.css';
@import '@fontsource/space-grotesk/700.css';
@import '@fontsource/space-mono/400.css';
@import '@fontsource/space-mono/700.css';
```

NUNCA importar fonts desde `fonts.googleapis.com` — falla GDPR/CSP estricto.

## Verificacion

```bash
# Lint pasa (Biome no acepta hex inline cuando hay token)
pnpm exec biome check .

# Tests unit pasan
pnpm exec vitest run

# Build estatico OK
pnpm run build

# Sin requests a Google Fonts (verificar en Network tab al servir el build)
pnpm run preview
```

## Anti-patterns

- ❌ Hex inline en componentes (`color: #4F6EF7`) — usar `color: var(--color-primary)`
- ❌ Importar fuentes desde Google Fonts CDN
- ❌ Definir colores fuera de `tokens.css`
- ❌ Componentes sin test mirror cuando tienen logica
- ❌ Olvidar verificar como se ve el componente en ambos modos (dark + light)
