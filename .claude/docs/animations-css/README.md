# Animaciones CSS modernas — referencia 2025-2026

> Base de conocimiento sobre animaciones CSS modernas aplicadas al stack
> de este portfolio (Astro 6 estatico). Usamos **vanilla CSS +
> IntersectionObserver minimal**, sin libreria. Justificacion al final.

## Indice rapido

| Tecnica | Doc | Cuando usar |
|---------|-----|-------------|
| Scroll-driven animations (CSS native) | [01-scroll-driven.md](./01-scroll-driven.md) | Reveal on scroll, progress bars, parallax. Progressive enhancement |
| View Transitions API | [02-view-transitions.md](./02-view-transitions.md) | Transiciones entre paginas MPA (CL <-> PE) o entre estados |
| Micro-interacciones | [03-micro-interactions.md](./03-micro-interactions.md) | Hover-lift, focus rings, magnetic buttons, button press |
| Gradientes modernos | [04-gradients.md](./04-gradients.md) | Mesh, conic, radial layering para hero/cards/accents |
| Marquee y loops | [05-marquee-loops.md](./05-marquee-loops.md) | Banda infinita, ticker, logo-cloud animados |
| Theme transition | [06-theme-transition.md](./06-theme-transition.md) | Smooth dark/light cycle sin paint flash |
| Accesibilidad | [07-accessibility.md](./07-accessibility.md) | prefers-reduced-motion guard, focus visible, WCAG 2.3.3 |
| Decisiones del proyecto | [08-decisions.md](./08-decisions.md) | Por que vanilla CSS y no libreria; trade-offs medidos |

## Principios obligatorios (portfolio)

1. **Animar solo `transform` y `opacity`** — esas dos propiedades viven en el
   compositor; el resto provoca relayout/repaint y dropea frames.
2. **`prefers-reduced-motion: reduce` siempre** — guard en toda animacion;
   nunca opcional. Es obligacion WCAG 2.3.3.
3. **Progressive enhancement** — features cutting-edge (scroll-driven,
   view-transitions) van detras de `@supports`; el fallback es estatico
   funcional o IntersectionObserver minimal.
4. **Bundle cero** — no agregamos libreria. WAAPI esta en todos los browsers,
   y CSS scroll-driven animations resuelven el 90% sin JS. Las animaciones
   son progressive enhancement.
5. **Duracion en tokens** — usar `--motion-dur-*` y `--motion-easing-*`
   (definidos en tokens.css). Sin numeros magicos.
6. **GPU-only props** — `transform: translateY/X/scale` y `opacity`. Cualquier
   otra animacion requiere justificacion + medicion en DevTools Performance.

## Stack del portfolio (Astro)

- **CSS**: vanilla con CSS Custom Properties (tokens.css), keyframes,
  transitions, scroll-driven animations cuando @supports.
- **JS minimal**: un solo `IntersectionObserver` global (~600 bytes minified)
  para scroll-reveal en browsers sin scroll-driven. Cargado defer.
- **No libreria**: NO motion, NO gsap, NO aos. Decision documentada en
  [08-decisions.md](./08-decisions.md).
- **View Transitions**: usaremos las nativas de Astro (`<ClientRouter />`)
  solo cuando navegamos entre paginas del portfolio, no para single-element morph.

## Quick reference — patrones

### Scroll reveal (CSS-only)

```css
@supports (animation-timeline: view()) {
  .rz-reveal {
    animation: rz-fade-up linear both;
    animation-timeline: view();
    animation-range: entry 0% cover 30%;
  }
}
```

### Hover lift (transform + shadow)

```css
.rz-card {
  transition:
    transform var(--motion-dur-fast) var(--motion-easing-standard),
    box-shadow var(--motion-dur-fast) var(--motion-easing-standard);
  will-change: transform;
}
.rz-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-medium);
}
```

### Mesh gradient hero

```css
.rz-hero {
  background:
    radial-gradient(60% 50% at 20% 30%, rgba(79, 110, 247, 0.18) 0%, transparent 50%),
    radial-gradient(40% 40% at 80% 70%, rgba(46, 207, 176, 0.12) 0%, transparent 50%),
    var(--color-bg);
}
```

### prefers-reduced-motion guard global

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

## Triggers para invocar la skill `animations-css`

La skill se activa con (espanol e ingles):

- "animacion css", "animaciones css", "css animation", "css animations"
- "scroll reveal", "scroll-driven", "scroll triggered"
- "view transition", "view transitions"
- "marquee", "infinite scroll banner"
- "hover effect", "micro interaction"
- "mesh gradient", "conic gradient"
- "prefers reduced motion", "accesibilidad animacion"
- "como animar", "que libreria de animacion", "framer motion vs"

## Fuentes (research 2025-2026)

- [MDN - Scroll-driven animations](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Scroll-driven_animations)
- [Can I Use - animation-timeline scroll](https://caniuse.com/mdn-css_properties_animation-timeline_scroll)
- [Chrome - Scroll-driven animations performance case study](https://developer.chrome.com/blog/scroll-animation-performance-case-study)
- [MDN - View Transition API](https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API)
- [Chrome - Cross-document view transitions](https://developer.chrome.com/docs/web-platform/view-transitions/cross-document)
- [Astro - View Transitions guide](https://docs.astro.build/en/guides/view-transitions/)
- [MDN - prefers-reduced-motion](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion)
- [W3C - WCAG 2.3.3 Animation from Interactions](https://www.w3.org/WAI/WCAG21/Understanding/animation-from-interactions.html)
- [Motion docs - performance](https://motion.dev/docs/performance)
- [Motion docs - CSS springs](https://motion.dev/docs/css)
- [scroll-driven-animations.style](https://scroll-driven-animations.style/)
- [Codrops - Creating 3D Scroll-Driven Text Animations](https://tympanus.net/codrops/2025/11/04/creating-3d-scroll-driven-text-animations-with-css-and-gsap/)
- [LogRocket - 6 CSS animation libraries 2025](https://blog.logrocket.com/6-css-animation-libraries-2025/)
- [WebAIM - 2026 Predictions: Web Accessibility](https://webaim.org/blog/2026-predictions/)
