# Decisiones de animacion portfolio (decision log)

> Decisiones tomadas para el landing portfolio (Astro 6 estatico) sobre
> animaciones CSS. Cada decision tiene fecha + razon + trade-off + cuando
> revisar.

## DEC-001: Sin libreria de animacion (vanilla CSS + IO minimal)

**Fecha**: 2026-05-12

**Decision**: NO agregamos libreria de animacion (motion, gsap, aos,
framer-motion). Usamos:

- **CSS nativo** para keyframes, transitions, scroll-driven animations
  (cuando `@supports`).
- **IntersectionObserver minimal** (~600 bytes minified) como fallback de
  scroll-reveal en browsers sin scroll-driven animations.
- **WAAPI** (`element.animate()`) si necesitamos animacion programatica
  one-off (zero bundle, nativo).

**Razon**:

1. El landing es Astro estatico (deploy S3+CloudFront). Cada KB de JS
   costara tiempo de paint y mas latencia.
2. La mayoria de animaciones del landing son simples: fade-up en scroll,
   hover-lift, marquee, theme transition. Todas resolubles con CSS.
3. CSS scroll-driven animations llegaron a soporte > 85% global en
   octubre 2025 (Firefox 144). Safari 18+ tiene partial. Polyfill no es
   necesario porque tenemos fallback con IntersectionObserver.
4. Motion (~3-5KB gzipped) es excelente pero NO necesario para nuestro caso
   de uso. La regla es: agregar libreria solo cuando el feature NO esta
   en CSS nativo o costaria > 200 lineas de CSS replicarlo.

**Trade-off aceptado**:

- Falta de "springs" perfectas (motion las da gratis). Nosotros usamos
  `cubic-bezier(0.34, 1.56, 0.64, 1)` (overshoot suave) que aproxima sin
  ser fisica real.
- Sin sequencing complejo nativo. Si necesitamos secuencias largas (>5
  animaciones encadenadas), revisariamos motion.

**Cuando revisar**:

- Si necesitamos animaciones complejas (drag, reorder, layout-aware),
  evaluamos motion (web-friendly).
- Si una feature requiere physics (drag inertia, snap-to-grid), evaluamos
  motion.

## DEC-002: Scroll-reveal via @supports + IO fallback

**Fecha**: 2026-05-12

**Decision**: Implementar scroll-reveal con CSS scroll-driven
animations cuando `@supports (animation-timeline: view())`, y un
IntersectionObserver minimal para el resto.

**Razon**:

- CSS scroll-driven es progressive enhancement perfecto: cuando esta,
  corre en el compositor (GPU), sin JS.
- IntersectionObserver es nativo, performant, no requiere libreria.
- Combinacion da: experiencia premium en Chrome/Firefox/Edge moderno;
  experiencia funcional en Safari < 18 y otros browsers.

**Alternativas descartadas**:

- AOS (Animate On Scroll): ~14KB gzipped, IO interno, decente. Pero
  excesivo para nuestro single use case.
- ScrollReveal.js: ~10KB, custom scroll handler. Mas pesado, scroll
  listener (no IO). Descartado.
- Pure JS solo (sin CSS scroll-driven): perdemos GPU compositor en
  browsers modernos.

## DEC-003: View Transitions API solo para misma-pagina, NO cross-document

**Fecha**: 2026-05-12

**Decision**: NO usar Astro `<ClientRouter />` para view transitions
cross-document. Si las usamos para morph dentro de la misma pagina
(cuando lo necesitemos).

**Razon**:

- ClientRouter agrega ~5KB de JS para una feature de 85% de browser
  support nativo. El beneficio es marginal en un portfolio de pocas paginas.
- Las paginas del portfolio suelen ser suficientemente distintas (home, CV,
  proyectos, contacto): un crossfade entre ellas no aporta narrative.

**Cuando revisar**:

- Si agregamos secciones tipo SPA en el mismo dominio, las view
  transitions cross-document pueden ser un win UX.
- Si hacemos detail pages con morph del card -> detail, usamos
  `document.startViewTransition()` nativo (zero bundle).

## DEC-004: prefers-reduced-motion guard global

**Fecha**: 2026-05-12

**Decision**: Aplicar `@media (prefers-reduced-motion: reduce)` en `global.css`
con `!important` para anular toda animacion. Cada componente puede
overridear con fade simple si tiene sentido.

**Razon**:

- WCAG 2.3.3 lo exige (Level AAA, en 2026 muchos paises lo van a Level
  AA via legislacion).
- Es bug-prone confiar en que cada componente acuerde respetar la
  preferencia. Mejor blanket disable + opt-in.

**Trade-off**:

- En reduce mode, algunos elementos aparecen "saltando" porque el reveal
  esta deshabilitado. Es preferible al riesgo de mareo del usuario.

## DEC-005: Animar solo `transform` y `opacity`

**Fecha**: 2026-05-12

**Decision**: La regla es: solo animar `transform` y `opacity`. Cualquier
otra propiedad requiere justificacion + medicion.

**Razon**:

- Esas dos propiedades corren en el compositor (GPU). El resto causa
  layout/paint.
- Garantiza 60fps incluso en hardware modesto (mobile mid-range).
- Reduce CLS (Cumulative Layout Shift) porque transform no afecta el
  layout.

**Excepciones permitidas**:

- `background-position` para mesh gradient drift (corre en paint, lento
  en mobile, lo usamos solo en hero con animacion 24s).
- `filter: blur()` solo en glow effects, NO en animacion constante (blur
  es costoso).
- `clip-path` para reveals tipo curtain (poco usado).

## DEC-006: Marquee con 3 copias + translateX -33.333%

**Fecha**: 2026-05-12

**Decision**: El marquee triplica el contenido y anima `translateX(-33.333%)`.

**Razon**:

- Duplicar y animar a `-50%` causa visible "snap" cuando el contenido es
  asimetrico (palabras de longitudes distintas).
- Triplicar garantiza loop perfecto: al -33.333%, el segundo cycle queda
  en posicion del primero. Loop seamless.

## Politica de revision

Cada 6 meses (mayo, noviembre), revisar:

1. Cambios en soporte de browsers (Can I Use)
2. Performance metrics del landing (LCP, INP, CLS via Web Vitals)
3. Si una feature requirio bypass de la regla (transform + opacity only),
   evaluar si vale la pena agregar libreria.
4. Si el uso del IntersectionObserver fallback supera al 30% de visitas
   (significa que > 30% del trafico es Safari < 18), evaluar polyfill
   oficial de scroll-driven.

Ultima revision: 2026-05-12 (esta).
