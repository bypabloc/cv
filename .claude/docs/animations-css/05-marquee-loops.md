# Marquee y loops infinitos

> Banda de texto/logos que scroll horizontalmente sin parar. Vanilla CSS,
> sin JS, sin libreria.

## Patron base

```html
<div class="rz-marquee" aria-hidden="true">
  <div class="rz-marquee__track">
    <span>RESERVAS · SIN FRICCION · EN 30s</span>
    <span>RESERVAS · SIN FRICCION · EN 30s</span>
    <span>RESERVAS · SIN FRICCION · EN 30s</span>
  </div>
</div>
```

Repetir el contenido **3 veces** (no 2) garantiza que el loop nunca muestre
"el corte" (al desplazarse -33% queda en posicion identica visual).

```css
.rz-marquee {
  overflow: hidden;
  white-space: nowrap;
  background: var(--color-text);
  color: var(--color-bg);
}
.rz-marquee__track {
  display: flex;
  gap: var(--space-48);
  width: max-content;
  animation: rz-marquee 24s linear infinite;
}
@keyframes rz-marquee {
  from { transform: translateX(0); }
  to   { transform: translateX(-33.333%); }
}
@media (prefers-reduced-motion: reduce) {
  .rz-marquee__track { animation: none; }
}
```

`-33.333%` porque triplicamos. Si duplicas, usa `-50%`.

## Bidireccional (oposing tracks)

```css
.rz-marquee--reverse .rz-marquee__track {
  animation-direction: reverse;
}
```

## Pause on hover (opcional)

```css
.rz-marquee:hover .rz-marquee__track {
  animation-play-state: paused;
}
```

UX: solo si el contenido tiene CTAs clickeables y necesita pausa. Para
brand stripe no aplica.

## Logos cloud animados

Para logos clients que scrollean:

```html
<div class="rz-logos">
  <div class="rz-logos__track">
    <img src="/logos/a.svg" alt="A" />
    <img src="/logos/b.svg" alt="B" />
    <!-- ... -->
    <img src="/logos/a.svg" alt="A" aria-hidden="true" />
    <img src="/logos/b.svg" alt="B" aria-hidden="true" />
  </div>
</div>
```

```css
.rz-logos {
  overflow: hidden;
  mask-image: linear-gradient(
    90deg,
    transparent 0,
    black 64px,
    black calc(100% - 64px),
    transparent 100%
  );
}
.rz-logos__track {
  display: flex;
  gap: var(--space-48);
  width: max-content;
  animation: rz-logos-scroll 32s linear infinite;
}
.rz-logos__track img {
  height: 32px;
  filter: grayscale(1) opacity(0.5);
  transition: filter 200ms cubic-bezier(0.2, 0, 0, 1);
}
.rz-logos__track img:hover {
  filter: grayscale(0) opacity(1);
}
@keyframes rz-logos-scroll {
  from { transform: translateX(0); }
  to   { transform: translateX(-50%); }
}
```

`mask-image` con linear-gradient transparente en bordes crea el "fade out"
clasico.

## A11y

- **`aria-hidden="true"`** en el marquee si el texto es decorativo y se
  repite. Screen readers no lo leen.
- **Si tiene info no decorativa**: mostrar el texto tambien fuera del
  marquee (visible o sr-only), y marcar el marquee solo como visual.
- WCAG 2.2.2 Pause, Stop, Hide: contenido que se mueve > 5s debe poder
  pausarse. Si el marquee es decorativo (`aria-hidden`), no aplica esta
  regla.

## Performance

- `transform: translateX` corre en compositor (GPU).
- `will-change: transform` solo si la pista es muy ancha (>2x viewport).
- Evitar `background-position` animado (causa paint en cada frame).

## Velocidad correcta

Eyeballed por velocidad de lectura, no por tiempo:

- Textos largos: 24-32s para un loop completo (3 copias).
- Textos cortos (palabras sueltas): 16-24s.
- Logos: 30-40s (mas relajado).

Si el viewport es mas chico, el loop visualmente es mas rapido. Para
homogeneizar, usar `animation-duration` proporcional al width via
`@container` queries.
