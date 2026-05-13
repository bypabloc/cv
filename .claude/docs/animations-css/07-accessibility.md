# Accesibilidad en animaciones

> WCAG 2.3.3 (Animation from Interactions) y system preferences. Obligatorio
> para WCAG 2.2 AA (estandar internacional 2026).

## prefers-reduced-motion

El usuario indica preferencia en su SO o browser:

- **macOS**: System Settings -> Accessibility -> Display -> Reduce Motion
- **iOS**: Settings -> Accessibility -> Motion -> Reduce Motion
- **Windows**: Settings -> Ease of Access -> Display -> Show animations
- **Android**: Settings -> Accessibility -> Remove animations
- **Linux GNOME**: Settings -> Universal Access -> Enable animations OFF

### Valor

- `no-preference` (default): el usuario no expreso preferencia
- `reduce`: el usuario activo el toggle

### Estrategias

#### A) Desactivar todo (mas estricto)

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
    scroll-behavior: auto !important;
  }
}
```

Es la guard global. Va en `global.css` del landing.

#### B) Reemplazar con cross-fade simple (mas pulido)

```css
.rz-reveal {
  /* animacion completa */
  animation: rz-fade-up 600ms cubic-bezier(0.2, 0, 0, 1) both;
}
@media (prefers-reduced-motion: reduce) {
  .rz-reveal {
    /* solo fade, sin movimiento */
    animation: rz-fade-in 200ms ease both;
  }
}
@keyframes rz-fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}
```

El usuario sigue percibiendo cambio (el contenido aparece), pero no hay
movimiento brusco.

#### C) Mostrar inmediato (revealed-by-default)

Para scroll-reveal: en `reduce`, el elemento esta visible desde el inicio,
sin transition.

```css
.rz-reveal {
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 600ms, transform 600ms;
}
.rz-reveal--visible {
  opacity: 1;
  transform: none;
}
@media (prefers-reduced-motion: reduce) {
  .rz-reveal {
    opacity: 1;
    transform: none;
    transition: none;
  }
}
```

## WCAG 2.3.3 Animation from Interactions (Level AAA)

"Motion animation triggered by interaction can be disabled, unless the
animation is essential."

Ejemplos no-essential:
- Parallax al scrollear
- Marquee infinitos puramente decorativos
- Hover micro-interactions

Ejemplos essential (no requiere toggle):
- Loading spinner (informa estado del sistema)
- Drag-and-drop visual feedback (esencial para la accion)

En portfolio, todo nuestro uso es non-essential, asi que aplicamos
`prefers-reduced-motion` agresivamente.

## WCAG 2.2.2 Pause, Stop, Hide (Level A)

"For any moving, blinking, or scrolling information that:
1. Starts automatically
2. Lasts more than 5 seconds
3. Is presented in parallel with other content

There is a mechanism for the user to pause, stop, or hide it."

**Implicaciones para marquee del landing**:

Opciones:
- Marcar el marquee como `aria-hidden="true"` (decorativo). Asi no aplica
  la regla porque no es informacion para el usuario.
- O agregar un toggle visible "Pause animation".

Decision portfolio: marquee es decorativo (`aria-hidden`), el texto se
duplica en una seccion textual no animada si tuviera info critica (no es
el caso).

## Focus visible

Animaciones de focus deben ser claras y duraderas:

```css
button:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  box-shadow: 0 0 0 4px var(--color-primary-muted);
  /* sin animacion: el ring debe ser instantaneo */
}
```

NO animar focus ring (puede confundir y dropear el indicador visual).

## Vestibular disorders

Animaciones que pueden disparar mareo:
- Parallax horizontal grande
- Zoom inesperado
- Rotacion (cualquier velocidad)
- Movement multi-axis (X+Y combinados)

Si el contenido se mueve en X o Y mas de 8-10% del viewport en una
animacion automatica, considera dejar `prefers-reduced-motion` agresivo
para esa parte.

## Color contrast en animacion

Si una animacion cambia el color del texto, el contraste DEBE mantenerse
WCAG AA (4.5:1 normal, 3:1 grande) en TODO momento de la animacion, no solo
inicio/fin.

## Testing

### Manual

1. Activar `prefers-reduced-motion: reduce` en el SO.
2. Recargar la pagina.
3. Verificar: el contenido aparece sin movimiento brusco, los hovers no
   animan, el marquee se detiene o se reemplaza por texto estatico.

### Playwright

```ts
test('respeta prefers-reduced-motion', async ({ browser }) => {
  const context = await browser.newContext({
    reducedMotion: 'reduce',
  })
  const page = await context.newPage()
  await page.goto('/landing/cl')
  // Verifica que ciertos elementos no animan
  const card = await page.locator('.rz-card').first()
  const transition = await card.evaluate((el) =>
    getComputedStyle(el).transitionDuration,
  )
  expect(transition).toMatch(/0(\.001)?(m?s)?/)
})
```

## Fuentes

- [MDN - prefers-reduced-motion](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion)
- [W3C - WCAG 2.3.3 Animation from Interactions](https://www.w3.org/WAI/WCAG21/Understanding/animation-from-interactions.html)
- [WebAIM - 2026 Predictions Accessibility](https://webaim.org/blog/2026-predictions/)
