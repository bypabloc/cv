# Scroll-driven animations (CSS native)

> Animaciones donde el "tiempo" de la animacion lo controla el scroll, no
> el reloj. Aterrizaron en Chrome 115+ (2023) y desde Firefox 144 (oct
> 2025) tienen soporte cross-browser amplio (Safari sigue parcial).
>
> En portfolio usamos un `@supports (animation-timeline: ...)` para activar
> solo donde estan disponibles, con fallback de **IntersectionObserver
> minimal** para Safari y browsers viejos.

## Conceptos

### `scroll-timeline`

Vincula una animacion al progreso del scroll de un contenedor.

```css
.parallax {
  animation: rz-slide linear;
  animation-timeline: scroll(root block);
}
@keyframes rz-slide {
  to { transform: translateY(-200px); }
}
```

`scroll(root block)` toma el scroll del root (html) en eje block (vertical).

### `view-timeline`

Vincula la animacion al avance del elemento dentro del viewport. Es lo
que usamos para **reveal-on-scroll**.

```css
.rz-reveal {
  animation: rz-fade-up linear both;
  animation-timeline: view();
  animation-range: entry 0% cover 30%;
}
@keyframes rz-fade-up {
  from {
    opacity: 0;
    transform: translateY(24px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

`animation-range`:
- `entry 0%` — el elemento empieza a entrar al viewport.
- `cover 30%` — el elemento esta 30% adentro.
- Por defecto: `entry 0% exit 100%` (animacion dura todo el scroll).

### `animation-fill-mode: both`

Importante para reveal: mantiene el estado inicial antes de que la
animacion se dispare (sin esto, el elemento estaria visible al inicio).

## Patron portfolio: reveal-on-scroll

```css
/* tokens.css ya define --motion-dur-* */

/* Estado inicial (visible solo si NO hay scroll-driven y NO hay JS) */
.rz-reveal {
  opacity: 1;
  transform: none;
}

/* Si hay scroll-driven, usa animacion nativa */
@supports (animation-timeline: view()) {
  .rz-reveal {
    opacity: 0;
    transform: translateY(24px);
    animation: rz-fade-up linear both;
    animation-timeline: view();
    animation-range: entry 5% cover 25%;
  }
  /* Variants para staggering manual */
  .rz-reveal--up    { animation-name: rz-fade-up; }
  .rz-reveal--left  { animation-name: rz-fade-left; }
  .rz-reveal--right { animation-name: rz-fade-right; }
  .rz-reveal--scale { animation-name: rz-fade-scale; }
}

@keyframes rz-fade-up {
  from { opacity: 0; transform: translateY(24px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes rz-fade-left {
  from { opacity: 0; transform: translateX(-24px); }
  to   { opacity: 1; transform: translateX(0); }
}
@keyframes rz-fade-right {
  from { opacity: 0; transform: translateX(24px); }
  to   { opacity: 1; transform: translateX(0); }
}
@keyframes rz-fade-scale {
  from { opacity: 0; transform: scale(0.96); }
  to   { opacity: 1; transform: scale(1); }
}

/* Fallback IntersectionObserver: el elemento esta oculto y se revela
   con la clase .rz-reveal--visible que agrega el observer */
@supports not (animation-timeline: view()) {
  .rz-reveal {
    opacity: 0;
    transform: translateY(24px);
    transition:
      opacity 600ms cubic-bezier(0.2, 0, 0, 1),
      transform 600ms cubic-bezier(0.2, 0, 0, 1);
  }
  .rz-reveal--visible {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Accesibilidad: desactivar si reduce */
@media (prefers-reduced-motion: reduce) {
  .rz-reveal {
    opacity: 1 !important;
    transform: none !important;
    animation: none !important;
    transition: none !important;
  }
}
```

### Observer minimal (~600 bytes minified)

```ts
// landing/src/lib/animations/reveal.ts
const els = document.querySelectorAll<HTMLElement>('.rz-reveal')
if (els.length > 0 && 'IntersectionObserver' in window) {
  const io = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.add('rz-reveal--visible')
          io.unobserve(entry.target)
        }
      }
    },
    { rootMargin: '0px 0px -10% 0px', threshold: 0.1 },
  )
  els.forEach((el) => io.observe(el))
}
```

Carga via `<script>` defer en LandingLayout — corre una vez por pagina, sin
framework.

## Performance considerations

- Las animaciones scroll-driven corren en el **compositor**: 60fps sin
  bloquear main thread.
- `transform` y `opacity` son las unicas safe-to-animate. Otras props
  causaran janks (medido en case study de Chrome team).
- En Safari (sin soporte aun), el IntersectionObserver es la alternativa
  performant — no hay listener `scroll` en el path critico.
- Throttle no es necesario para IntersectionObserver (es nativo).

## Fuentes

- [MDN - Using scroll-driven animations](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Scroll-driven_animations)
- [Chrome - Scroll-driven case study](https://developer.chrome.com/blog/scroll-animation-performance-case-study)
- [scroll-driven-animations.style](https://scroll-driven-animations.style/)
- [Can I Use - animation-timeline scroll](https://caniuse.com/mdn-css_properties_animation-timeline_scroll)
