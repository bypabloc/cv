# Gradientes modernos (mesh, conic, radial layering)

> Tecnicas CSS para crear backgrounds organicos, accents y "lava lamp" looks
> sin SVG ni JS. Compatible 100% con todos los browsers modernos.

## Linear gradient (basico)

```css
background: linear-gradient(135deg, #4f6ef7 0%, #2edfb0 100%);
```

Para hero, evitar full-bleed: combinar con radial para mayor profundidad.

## Radial gradient

```css
background: radial-gradient(
  ellipse 80% 60% at 50% 30%,
  rgba(79, 110, 247, 0.3) 0%,
  transparent 70%
);
```

`80% 60%` = tamano. `at 50% 30%` = posicion. `at` puede ser `top`, `right`,
`bottom left`, etc.

## Conic gradient

```css
background: conic-gradient(
  from 0deg at 50% 50%,
  #4f6ef7 0deg,
  #2edfb0 120deg,
  #b5ff2e 240deg,
  #4f6ef7 360deg
);
```

Ideal para accent rings, charts, color wheels. En hero portfolio lo usamos
en un blob decorativo del frame del ProductPreview.

## Mesh gradient (layering radial)

No existe `mesh-gradient` nativo en CSS aun (propuesta WICG en draft). Se
simula con multiples `radial-gradient` apiladas:

```css
.rz-mesh {
  background:
    radial-gradient(60% 50% at 15% 20%, rgba(79, 110, 247, 0.20) 0%, transparent 50%),
    radial-gradient(50% 40% at 85% 30%, rgba(46, 207, 176, 0.14) 0%, transparent 50%),
    radial-gradient(40% 30% at 50% 90%, rgba(181, 255, 46, 0.10) 0%, transparent 50%),
    var(--color-bg);
}
```

3-5 capas suelen ser suficientes. Cada `rgba` con alpha baja (0.08-0.20).

### Animado (mesh "vivo")

```css
.rz-mesh--animated {
  background:
    radial-gradient(60% 50% at 15% 20%, rgba(79, 110, 247, 0.22) 0%, transparent 50%),
    radial-gradient(50% 40% at 85% 30%, rgba(46, 207, 176, 0.16) 0%, transparent 50%),
    var(--color-bg);
  background-size: 200% 200%;
  animation: rz-mesh-drift 24s ease-in-out infinite alternate;
}
@keyframes rz-mesh-drift {
  0%   { background-position: 0% 0%, 100% 0%; }
  100% { background-position: 50% 50%, 50% 100%; }
}
@media (prefers-reduced-motion: reduce) {
  .rz-mesh--animated { animation: none; }
}
```

## Conic accent stripe (portfolio V1 inspired)

Las tres bandas verticales del logo se inspiran en el patron de marca.
Para hero/footer accents, usar diagonal con `repeating-linear-gradient`:

```css
.rz-stripes {
  background-image: repeating-linear-gradient(
    45deg,
    transparent 0,
    transparent 8px,
    rgba(79, 110, 247, 0.04) 8px,
    rgba(79, 110, 247, 0.04) 12px
  );
}
```

## Border gradient (sin border-image)

`border-image` tiene limitaciones (no respeta `border-radius`). Alternativa
con doble background:

```css
.rz-card-gradient {
  background:
    linear-gradient(var(--color-surface), var(--color-surface)) padding-box,
    linear-gradient(135deg, var(--color-primary), var(--color-accent-teal)) border-box;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
}
```

El primer fondo es el "real"; el segundo se muestra solo en el border.

## Glow effects

```css
.rz-glow {
  position: relative;
}
.rz-glow::before {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: inherit;
  background: linear-gradient(135deg, var(--color-primary), var(--color-accent-teal));
  filter: blur(12px);
  opacity: 0;
  transition: opacity 200ms cubic-bezier(0.2, 0, 0, 1);
  z-index: -1;
}
.rz-glow:hover::before {
  opacity: 0.5;
}
```

## Performance

- Gradients son render-time, no animan smooth si se animan los colores
  directamente.
- Animar `background-position` o `transform` del contenedor, no el gradient.
- En backgrounds con muchas capas, considera `will-change: transform` solo
  si va a animarse.

## Fuentes

- [MDN - linear-gradient()](https://developer.mozilla.org/en-US/docs/Web/CSS/gradient/linear-gradient)
- [MDN - radial-gradient()](https://developer.mozilla.org/en-US/docs/Web/CSS/gradient/radial-gradient)
- [MDN - conic-gradient()](https://developer.mozilla.org/en-US/docs/Web/CSS/gradient/conic-gradient)
- [Better Gradient - Mesh Gradients with CSS](https://better-gradient.com/blog/mesh-gradient-css-guide)
