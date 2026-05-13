# Theme transition (dark/light)

> Como animar el switch entre temas sin "paint flash" ni saltos visibles.

## Problema clasico

Al cambiar `:root` class de `dark` -> `light`:
- Todos los componentes que tienen `transition: background-color` empiezan
  a transicionar al MISMO tiempo. 
- Causa un "ripple" caotico.
- Tarjetas, navbars y badges no se sincronizan.

## Solucion 1: transitions sutiles + uniform duration

En portfolio usamos:

```css
:root {
  --motion-dur-theme: 200ms;
  --motion-easing-theme: cubic-bezier(0.2, 0, 0, 1);
}
body {
  background-color: var(--color-bg);
  color: var(--color-text);
  transition:
    background-color var(--motion-dur-theme) var(--motion-easing-theme),
    color var(--motion-dur-theme) var(--motion-easing-theme);
}
```

Solo `body` transiciona; los descendientes heredan o usan tokens. Asi
toda la pagina cambia al mismo tiempo, sin staircase.

## Solucion 2: transition guard durante el switch (recomendada)

Para evitar TODO transition durante el cambio (mas snappy y consistente):

```html
<button id="theme-toggle">...</button>
```

```ts
function cycleTheme() {
  document.documentElement.classList.add('rz-theme-switching')
  // ... aplicar nuevo tema
  // remueve el guard despues de 1 frame
  requestAnimationFrame(() => {
    setTimeout(() => {
      document.documentElement.classList.remove('rz-theme-switching')
    }, 0)
  })
}
```

```css
.rz-theme-switching,
.rz-theme-switching *,
.rz-theme-switching *::before,
.rz-theme-switching *::after {
  transition: none !important;
}
```

Resultado: el switch es instantaneo (sin baileo).

## Solucion 3: View Transitions API (moderno)

```ts
function cycleTheme(newTheme: string) {
  if (!document.startViewTransition) {
    // Fallback: cambio directo
    applyTheme(newTheme)
    return
  }
  document.startViewTransition(() => {
    applyTheme(newTheme)
  })
}
```

Con CSS:

```css
::view-transition-old(root),
::view-transition-new(root) {
  animation-duration: 300ms;
  animation-timing-function: cubic-bezier(0.2, 0, 0, 1);
}
```

Algunos sitios hacen "ripple effect" desde el boton:

```ts
async function cycleTheme(newTheme: string, event: MouseEvent) {
  const x = event.clientX
  const y = event.clientY
  const endRadius = Math.hypot(
    Math.max(x, innerWidth - x),
    Math.max(y, innerHeight - y),
  )
  const transition = document.startViewTransition(() => {
    applyTheme(newTheme)
  })
  await transition.ready
  document.documentElement.animate(
    {
      clipPath: [`circle(0 at ${x}px ${y}px)`, `circle(${endRadius}px at ${x}px ${y}px)`],
    },
    {
      duration: 500,
      easing: 'cubic-bezier(0.2, 0, 0, 1)',
      pseudoElement: '::view-transition-new(root)',
    },
  )
}
```

Browser support: Chrome 126+, Safari 18.2+, Firefox 144+. Fallback graceful
si no esta disponible.

## Solucion 4: Pre-paint guard (sin flash al cargar)

El script `is:inline` en `<head>` aplica el tema antes de que pinte el body:

```html
<script is:inline>
  ;(function () {
    var theme = localStorage.getItem('theme-preference') || 'dark'
    var html = document.documentElement
    html.classList.remove('light', 'dark')
    if (theme === 'dark') html.classList.add('dark')
    else if (theme === 'light') html.classList.add('light')
    else html.classList.add(
      matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light',
    )
  })()
</script>
```

Esto va en `<head>` ANTES del `<body>`. Critico para evitar "flash of
unstyled content" en tema dark sobre fondo blanco default.

## Decision portfolio

Usamos **Solucion 2 (transition guard)** por defecto: snappy, sin animacion
chunky, predecible. Cuando agreguemos animacion mas "wow" (ripple effect),
sera opt-in con un toggle visible (la mayoria de users prefiere snap).

## prefers-reduced-motion

```css
@media (prefers-reduced-motion: reduce) {
  body { transition: none !important; }
}
```
