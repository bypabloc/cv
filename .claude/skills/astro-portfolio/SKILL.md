---
name: astro-portfolio
description: >
  Portfolio/CV strategy reference for this Astro 6.1 project, post-AI era.
  Covers: GEO/LLM-SEO (appearing in ChatGPT/Claude/Perplexity answers),
  ATS optimization, JSON-LD Person schema, llms.txt, vibe coding narrative,
  AI literacy as differentiator, recommended Astro templates (astrofy,
  satnaing/astro-paper), folder structure, content collections, View
  Transitions, dark/light mode, 2026 design trends (brutalism, swiss
  minimalism, mesh gradients), prioritized animation stack, anti-patterns
  (black-hat prompt injection, parallax, heavy animation libraries).
  ALWAYS invoke this skill BEFORE answering ANY question about how to
  build, structure, position, or improve this portfolio. NEVER answer
  portfolio-strategy questions from training data alone — this project has
  3 consolidated 2026 research reports that override generic advice.

  Use when the user says "portfolio", "portafolio", "cv", "curriculum",
  "astro template", "plantilla astro", "astro portfolio", "astro cv",
  "astrofy", "astro-paper", "astro theme", "tema astro", "showcase",
  "content collections", "colecciones de contenido", "seo astro",
  "geo", "llm seo", "llms.txt", "sitemap astro", "rss astro",
  "open graph", "json-ld", "structured data", "person schema",
  "ats", "applicant tracking system", "filtro ats", "pasar ats",
  "ai literacy", "vibe coding", "claude code portfolio",
  "cursor portfolio", "github profile", "perfil github",
  "case study portfolio", "caso de estudio", "narrativa tecnica",
  "dark mode astro", "modo oscuro astro", "theme toggle",
  "view transitions", "view transitions api", "transiciones de
  pagina", "page transitions", "design trends 2026", "tendencias
  diseno 2026", "brutalism", "neo-brutalism", "swiss design",
  "minimalismo", "mesh gradient hero", "hero portfolio",
  "estructura portfolio", "estructura cv astro", "que template uso",
  "que plantilla astro", "como armo mi cv en astro", "como hago un
  portafolio en astro", "lighthouse 95 astro", "performance astro",
  "como animo mi cv", "animaciones portfolio", "animaciones cv",
  "que animaciones poner", "fade in stagger", "section reveal",
  "scroll reveal cv", "tech stack marquee", "typewriter hero",
  "link underline animation", "smooth theme transition cv",
  "prompt injection portfolio", "black hat seo ia",
  "personal branding dev", "niveles junior mid senior 2026",
  "que diferencia senior 2026", "reclutadores tech 2026",
  "que proyectos mostrar", "side projects portfolio",
  "saas monetizado portfolio".
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: "<aspecto: stack / template / seo / geo / llms / animacion / proyectos / ats / vibe-coding>"
---

# Astro Portfolio (post-AI 2026) — este proyecto

> Skill maestro para todas las decisiones de estrategia, arquitectura,
> contenido y animacion del portfolio personal de Pablo Contreras.
> Apoyado en 3 investigaciones consolidadas 2026.

## Regla cardinal

1. **SIEMPRE leer el hub maestro primero**:
   `.claude/docs/portfolio-research-hub/README.md`. NO inventar
   recomendaciones; cada respuesta cita el modulo concreto.
2. **NUNCA tecnicas black-hat** (texto blanco sobre blanco, hidden divs
   con prompt injection, comentarios HTML con "ignore previous
   instructions"). Detectables al 92%+ por SpamBrain 2025 y Claude Opus
   4.5. ROI negativo, riesgo legal (EU AI Act Art 9, GDPR).
3. **NO librerias de animacion pesadas** (motion, gsap, aos,
   framer-motion). Vanilla CSS + IntersectionObserver minimal + View
   Transitions API nativa de Astro 6.1 cubren el 100% del CV.
4. **Lighthouse 95+** en performance/accessibility/best-practices/SEO es
   no-negociable. Cualquier sugerencia que comprometa esto se descarta.
5. **GEO > SEO tradicional**: aparecer en ChatGPT/Claude/Perplexity es la
   nueva primera pagina. Se logra con JSON-LD Person + llms.txt +
   semantic HTML + contenido autentico bien estructurado.

## Mapa de la base de conocimiento

### Hub central

`.claude/docs/portfolio-research-hub/README.md` — indice maestro de las
3 investigaciones, con 5 hallazgos consolidados y matriz cruzada.

### Las 3 investigaciones

| # | Investigacion | Foco | Cuando consultar |
|---|---------------|------|------------------|
| 1 | `.claude/docs/modern-portfolios/` | Tendencias 2025-2026, ATS, GEO/LLM-SEO, estructura, UX, tecnologias, personal branding | Decisiones de arquitectura general |
| 2 | `.claude/docs/developer-portfolios-vibe-coding/` | Especifico devs: Claude Code/Cursor/Windsurf, GitHub, presencia online, junior/mid/senior post-IA | Que proyectos, skills y narrativa tecnica mostrar |
| 3 | `.claude/docs/ai-prompt-optimization/` | White-hat / grey-hat / black-hat para influenciar lectura de IAs. Schema, llms.txt, riesgos eticos | Metadata y estructura tecnica del sitio |

### Mapa pregunta → modulo

| Pregunta del usuario | Modulo principal | Complemento |
|----------------------|------------------|-------------|
| "que stack uso" | `modern-portfolios/06-tecnologias.md` | `developer-portfolios-vibe-coding/11-stack-checklist.md` |
| "como paso el filtro ATS" | `modern-portfolios/02-optimizacion-ats.md` | `ai-prompt-optimization/03-tecnicas-white-hat.md` |
| "como aparezco en ChatGPT/Claude" | `modern-portfolios/03-geo-llm-seo.md` | `ai-prompt-optimization/03a-json-ld-schemas.md`, `03c-llms-robots-sitemap.md` |
| "que proyectos muestro" | `developer-portfolios-vibe-coding/04-proyectos-mostrar.md` | `modern-portfolios/04-estructura-contenido.md` |
| "como hablo de Claude Code/Cursor" | `developer-portfolios-vibe-coding/09-documentacion-uso-ia.md` | `developer-portfolios-vibe-coding/03-herramientas-ia.md` |
| "que NO hacer" | `modern-portfolios/09-anti-patterns.md` | `ai-prompt-optimization/05-tecnicas-black-hat.md`, `07-deteccion-riesgos.md` |
| "que diferencia junior/mid/senior 2026" | `developer-portfolios-vibe-coding/08-niveles-junior-mid-senior.md` | `developer-portfolios-vibe-coding/02-reclutadores-tech.md` |
| "diseno visual / UX / tendencias" | `modern-portfolios/05-diseno-visual-ux.md` | `modern-portfolios/01-contexto-tendencias.md` |
| "personal branding / niche" | `modern-portfolios/07-personal-branding.md` | — |
| "GitHub profile" | `developer-portfolios-vibe-coding/05-github-profile.md` | `developer-portfolios-vibe-coding/06-presencia-online.md` |
| "checklist de implementacion" | `modern-portfolios/12-checklist.md` | `ai-prompt-optimization/10-checklist-accionable.md` |
| "casos reales / ejemplos" | `developer-portfolios-vibe-coding/12-ejemplos-portfolios.md` | `ai-prompt-optimization/06-casos-reales.md` |

### Datos del CV actual

`.claude/docs/cv/README.md` — fuente de verdad del CV de Pablo. Cruzar con
investigaciones para identificar gaps.

## Resumen ejecutivo (cache mental)

### Los 5 hallazgos consolidados

1. **GEO > SEO tradicional**. Aparecer en respuestas de ChatGPT/Claude/
   Perplexity cuando alguien pregunta "best developer for X". Se logra con
   JSON-LD Person + llms.txt + semantic HTML.
2. **AI Literacy es el diferenciador**. 92% de devs usan IA daily.
   Documentar workflow real con Claude Code/Cursor (prompts reales, no
   marketing) supera al "miren cuanto codigo escribi a mano".
3. **Proyectos > Lista de skills**. Case studies narrativos
   (Problema → Solucion → Impacto con metricas) ganan 72% vs listas. SaaS
   monetizado aunque sea $100/mes es senal fuerte.
4. **Stack ganador**: Astro 6.1 + Cloudflare Pages + Tailwind v4. 40% mas
   rapido que Next.js, 90% menos JS. El repo del portfolio comunica skill
   tecnico por si mismo.
5. **Solo white-hat**. Black-hat prompt injection detectable al 92%+. ROI
   negativo. Estrategia ganadora: schema markup riguroso + llms.txt +
   contenido autentico bien estructurado.

### Stack de animaciones priorizado (cross-skill)

Detalle completo en skill `animations-css`. Resumen:

| Prioridad | Animacion | Tecnica | Bundle |
|-----------|-----------|---------|--------|
| MUST | Hero fade-in stagger | `@keyframes` + `animation-delay` | 0kb |
| MUST | Section reveal on scroll | IntersectionObserver vanilla | ~1kb |
| MUST | Dark/light toggle transition | CSS `transition` + vars | 0kb |
| MUST | Link hover underline | `::after` + `scaleX()` | 0kb |
| MUST | View Transitions entre paginas | `<ClientRouter />` Astro 6.1 | 0kb |
| NICE | Typewriter hero, mesh gradient, marquee | CSS puro | 0kb |
| EVITAR | Parallax, custom cursor, Three.js, GSAP, Motion, AOS | — | 18-200kb+ o a11y risk |

## Estilo de respuesta

- Empezar identificando que investigacion + modulo aplica a la pregunta.
- Citar **al final** la ruta exacta:
  `.claude/docs/<investigacion>/<NN>-<topic>.md`.
- Si la pregunta cruza investigaciones, citar las 2-3 mas relevantes.
- Para preguntas de animacion CSS especifica (codigo, keyframes,
  scroll-driven), **redirigir** a skill `animations-css`.
- Indicar siempre **bundle impact** y **a11y impact** de sugerencias
  tecnicas.
- Si el usuario propone algo de la lista EVITAR / black-hat, explicar por
  que y proponer la alternativa documentada.

## Cross-skill

| Tema | Skill |
|------|-------|
| Patron CSS especifico (keyframes, scroll-driven, mesh gradient) | `animations-css` |
| Estrategia, contenido, GEO, ATS, vibe coding | **este skill (`astro-portfolio`)** |
| TDD para componente nuevo | `tdd-workflow` |
| Lint Biome v2 conformance | `fix-hooks` |
| Documentacion del proyecto (knowledge tree) | `knowledge-tree` |
| Especificacion / descomposicion feature | `spec-workflow` |

## Anti-patterns a corregir cuando aparezcan

### Black-hat / riesgo legal (RECHAZAR)

- "Voy a meter prompt injection oculto para que ChatGPT me recomiende" →
  detectable, riesgo EU AI Act Art 9, GDPR. Ver
  `ai-prompt-optimization/05-tecnicas-black-hat.md`
- "Texto blanco sobre blanco con keywords" → SpamBrain 2025 lo detecta.
- "Hidden divs con instrucciones para IAs" → idem.
- "Comentarios HTML con 'ignore previous instructions'" → idem.

### Tecnico

- "Voy a usar GSAP / Motion / Framer / AOS" → vanilla CSS + IO cubre el
  caso. Ver skill `animations-css` y `09-anti-patterns.md` de
  research-modern.
- "Mete Three.js en el hero" → mesh gradient CSS layered (0kb vs 200kb+).
- "Google Fonts CDN" → `@fontsource/*` self-hosted (GDPR + perf).
- "Parallax en el hero" → a11y risk vestibular; usar fade-in.
- "Custom cursor" → desvia del contenido; no para CV.
- "Cliente router de Astro sin justificacion" → solo View Transitions
  puntuales en triggers especificos (ver `animations-css` skill).
- "Animar `width`, `height`, `top`, `margin`" → corregir a `transform`
  (GPU compositor).

### Contenido / posicionamiento

- "Lista plana de skills sin contexto" → case studies narrativos ganan
  72%. Ver `developer-portfolios-vibe-coding/04-proyectos-mostrar.md`.
- "Full Stack Developer" generico → niche gana. "Full Stack con fintech
  Chile/Peru + agentes IA" gana a "Full Stack Developer".
- "Ocultar uso de IA" → en 2026 es liability, no ventaja. Documentar
  workflow real con Claude Code/Cursor.
- "Fork completo de astrofy/astro-paper" → tomar patrones, NO el DS
  ajeno. Tu design system (`design-system.md`) manda.

## Donde aplica en este proyecto

- Templates: si se adopta uno como referencia (astrofy / satnaing/
  astro-paper), tomar patrones, NO hacer fork completo.
- Estructura: ubicar componentes en `src/components/` con prefijo
  consistente (ver `astro-landing.md`).
- SEO/GEO: `astro.config.ts` con integraciones `@astrojs/sitemap`,
  `@astrojs/rss`, metadata + JSON-LD Person en `BaseLayout.astro`,
  `public/llms.txt` y `public/robots.txt`.
- Animaciones: keyframes en `src/styles/animations.css`, IO helpers en
  `src/lib/animations/`.

## Verificacion post-respuesta

Antes de cerrar una recomendacion, confirmar:

- [ ] Cite ruta exacta a `.claude/docs/<investigacion>/<modulo>.md`
- [ ] Si toca animaciones: redirigi/complementi con `animations-css`
- [ ] No propuse black-hat
- [ ] Indique bundle y a11y impact si aplica
- [ ] Recomendacion alineada con los 5 hallazgos consolidados

## Fuentes canonicas

- Hub maestro: `.claude/docs/portfolio-research-hub/README.md`
- Investigacion 1: `.claude/docs/modern-portfolios/README.md`
- Investigacion 2: `.claude/docs/developer-portfolios-vibe-coding/README.md`
- Investigacion 3: `.claude/docs/ai-prompt-optimization/README.md`
- CV actual: `.claude/docs/cv/README.md`
- Convenciones Astro: `.claude/rules/astro-landing.md`
- Design system: `.claude/rules/design-system.md`
