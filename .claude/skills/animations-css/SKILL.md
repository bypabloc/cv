---
name: animations-css
description: >
  CSS animation reference for this portfolio: scroll-driven animations,
  View Transitions API, micro-interactions, mesh gradients, marquee loops,
  smooth theme transitions, prefers-reduced-motion guards. ALWAYS invoke
  for any CSS animation question in this project. Cover the decision: NO
  external animation library (motion, gsap, aos) - vanilla CSS + minimal
  IntersectionObserver.

  Use when the user says "animation", "animacion", "css animation",
  "animacion css", "scroll reveal", "scroll-driven", "scroll triggered",
  "view transition", "view transitions", "marquee", "infinite scroll
  banner", "hover effect", "micro interaction", "micro-interaccion",
  "mesh gradient", "conic gradient", "prefers reduced motion",
  "accesibilidad animacion", "como animar", "que libreria de animacion",
  "framer motion vs", "motion-one", "anim de scroll", "fade in scroll",
  "reveal on scroll", "animar este componente", "animar landing", "smooth
  transition theme", "transition dark light", "transicion tema".
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: "<aspecto a animar o tipo de animacion>"
---

# Animaciones CSS — portfolio

Cuando el usuario pregunta sobre animaciones CSS en este proyecto:

1. **Leer la doc primero**: `.claude/docs/animations-css/README.md` con
   indice de los 8 capitulos especificos. NO inventar; siempre apoyarse en
   la doc.
2. **Recordar la regla cardinal**: NO se agregan librerias en este proyecto.
   Vanilla CSS + IntersectionObserver minimal cubren el 99% de casos.
   Justificacion en `.claude/docs/animations-css/08-decisions.md`.
3. **Animar solo `transform` y `opacity`** (GPU compositor). Otras props
   requieren justificacion.
4. **`prefers-reduced-motion: reduce`** SIEMPRE. Es obligatorio WCAG.

## Mapa rapido

| Pregunta | Doc |
|----------|-----|
| "como animar fade in al scrollear" | `01-scroll-driven.md` (CSS `view()` + IO fallback) |
| "como hacer transicion entre paginas" | `02-view-transitions.md` (decision: NO ClientRouter, si `startViewTransition` puntual) |
| "hover lift, button press, magnetic, focus ring" | `03-micro-interactions.md` |
| "mesh gradient, conic, radial layering" | `04-gradients.md` |
| "marquee infinito, logos scroll" | `05-marquee-loops.md` (triplicar, -33.333%) |
| "transicion dark/light smooth, sin flash" | `06-theme-transition.md` (transition guard) |
| "prefers-reduced-motion, WCAG 2.3.3, mareo" | `07-accessibility.md` |
| "que libreria uso", "motion vs gsap vs nada" | `08-decisions.md` (DEC-001: nada) |

## Estilo de respuesta

- Mostrar el patron CSS especifico, no descripcion teorica.
- Indicar siempre el `prefers-reduced-motion` guard del patron.
- Si el patron tiene fallback (CSS scroll-driven + IO), mostrar ambos.
- Citar la doc relevante al final como `.claude/docs/animations-css/<n>-<topic>.md`.

## Donde aplica en este proyecto

Cuando se implemente animacion en el portfolio, ubicar:

- Keyframes globales en `src/styles/animations.css`
- IntersectionObserver minimal (cuando CSS scroll-driven no alcanza) en `src/lib/animations/`
- Componentes Astro con clase de reveal (revelan en scroll)
- Theme toggle: guard de transicion para evitar flash en `src/components/`

## Anti-patterns a corregir cuando aparezcan

- Si alguien sugiere agregar motion, gsap, aos: redirigir a DEC-001.
- Si alguien anima `width`, `height`, `top`, `left`, `margin`: corregir a
  `transform`.
- Si alguien usa `:focus` sin `:focus-visible`: corregir a `focus-visible`
  (a11y best practice).
- Si alguien hace animaciones > 500ms en feedback inmediato (hover/click):
  reducir a 100-300ms.

## Referencias canonicas externas

- MDN scroll-driven animations
- Can I Use animation-timeline
- WCAG 2.3.3, 2.2.2
- W3C CSS Animations spec

Todas listadas en `.claude/docs/animations-css/README.md#fuentes-research-2025-2026`.
