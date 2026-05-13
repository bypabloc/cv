# Micro-interacciones

> Pequenas animaciones de respuesta a hover/focus/click que aportan
> "feel" y feedback haptico-visual. Vanilla CSS, sin JS.

## Principios

1. **Animar `transform` y `opacity`, nunca layout** (width/height/margin
   producen reflow).
2. **Duracion corta**: 100-200ms para feedback inmediato, 200-400ms para
   transiciones de estado.
3. **Easing curvo**: `cubic-bezier(0.2, 0, 0, 1)` (portfolio standard) o
   `cubic-bezier(0.34, 1.56, 0.64, 1)` (overshoot suave para springs).
4. **`will-change` con cuidado**: solo en elementos que SE VAN a animar.
   Removerlo despues evita memory pressure.

## Patron: hover-lift

```css
.rz-card {
  transition:
    transform var(--motion-dur-fast) var(--motion-easing-standard),
    box-shadow var(--motion-dur-fast) var(--motion-easing-standard),
    border-color var(--motion-dur-fast) var(--motion-easing-standard);
}
.rz-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-medium);
  border-color: var(--color-primary);
}
@media (prefers-reduced-motion: reduce) {
  .rz-card { transition: none; }
  .rz-card:hover { transform: none; }
}
```

## Patron: button press

```css
.btn {
  transition: transform 80ms cubic-bezier(0.2, 0, 0, 1);
}
.btn:active {
  transform: scale(0.98);
}
```

## Patron: focus ring portfolio (3-color)

```css
.btn:focus-visible,
.input-base:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  box-shadow: 0 0 0 4px var(--color-primary-muted);
}
```

`focus-visible` (no `:focus`) evita mostrar el ring al hacer click con mouse;
solo aparece con teclado, que es lo a11y-correct.

## Patron: shimmer skeleton (loading)

```css
.rz-skeleton {
  background: linear-gradient(
    90deg,
    var(--color-surface-2) 0%,
    var(--color-surface) 50%,
    var(--color-surface-2) 100%
  );
  background-size: 200% 100%;
  animation: rz-shimmer 1.6s ease-in-out infinite;
}
@keyframes rz-shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
@media (prefers-reduced-motion: reduce) {
  .rz-skeleton { animation: none; opacity: 0.7; }
}
```

## Patron: pulse breathing (badge live)

```css
.badge-live::before {
  content: '';
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-success);
  margin-right: 6px;
  animation: rz-pulse 2s ease-in-out infinite;
}
@keyframes rz-pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50%      { transform: scale(1.3); opacity: 0.6; }
}
```

## Patron: rotacion smooth (FAQ chevron)

```css
.faq__icon {
  transition: transform var(--motion-dur-base) var(--motion-easing-standard);
}
details[open] .faq__icon {
  transform: rotate(45deg);
}
```

## Patron: magnetic button (cursor follow)

Requiere JS minimo, ~150 bytes:

```ts
const btn = document.querySelector<HTMLElement>('.rz-magnetic')
btn?.addEventListener('pointermove', (e) => {
  const rect = btn.getBoundingClientRect()
  const x = e.clientX - rect.left - rect.width / 2
  const y = e.clientY - rect.top - rect.height / 2
  btn.style.transform = `translate(${x * 0.2}px, ${y * 0.2}px)`
})
btn?.addEventListener('pointerleave', () => {
  btn.style.transform = ''
})
```

```css
.rz-magnetic {
  transition: transform 200ms cubic-bezier(0.2, 0, 0, 1);
}
@media (prefers-reduced-motion: reduce) {
  .rz-magnetic { transition: none; }
}
```

NO usar en CTAs primarios (puede confundir); si en botones decorativos.

## Patron: text reveal por letra

```css
.rz-text-stagger > span {
  display: inline-block;
  opacity: 0;
  transform: translateY(8px);
  animation: rz-letter-in 600ms cubic-bezier(0.2, 0, 0, 1) forwards;
  animation-delay: calc(var(--i) * 30ms);
}
@keyframes rz-letter-in {
  to { opacity: 1; transform: translateY(0); }
}
```

```html
<h2 class="rz-text-stagger">
  <span style="--i: 0">T</span>
  <span style="--i: 1">u</span>
  <!-- ... -->
</h2>
```

Aplicacion programatica: split por letra con un script `<script is:inline>`
o pre-procesado en build (sin runtime cost en cliente).

## No hacer

- `box-shadow` animado puede causar paint lag — preferir layers separados con
  `::before/::after` y opacity.
- `top/left/right/bottom` con position absolute — usar transform.
- Animaciones infinitas sin pausa (UX cansado).
- Cualquier animacion > 500ms en feedback inmediato (siente lento).
