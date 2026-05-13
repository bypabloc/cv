---
name: modern-portfolios
description: >
  Modern developer portfolio strategy reference for 2026 (post-AI era).
  Covers ATS optimization (job title keywords, 10.6x interview probability),
  GEO (Generative Engine Optimization, appearing in ChatGPT/Claude/Perplexity
  answers), JSON-LD Person/ProfilePage schema, llms.txt, robots.txt with
  GPTBot/ClaudeBot allow, recommended stack (Astro 6.1 + Tailwind v4 +
  Cloudflare Pages, 40% faster than Next.js), 2026 design trends, dark mode
  (82.7% users), WCAG AA + EU Accessibility Act (mandatory since Jun 2025,
  ADA deadline Apr 2026), Core Web Vitals (LCP < 2.0s threshold Mar 2026),
  personal branding (niche > generalist), case studies (Problem -> Process
  -> Result with metrics), anti-patterns. ALWAYS invoke this skill BEFORE
  answering ANY question about overall portfolio strategy, ATS, GEO,
  technical stack choice, personal branding for this project. NEVER answer
  from training data alone — this project has a consolidated 2026 research
  module that overrides generic advice.

  Use when the user says "portfolio strategy", "estrategia portfolio",
  "como armo mi portfolio", "ats", "applicant tracking system",
  "filtro ats", "pasar ats", "ats keywords", "job title keywords",
  "geo", "generative engine optimization", "llm seo", "llms.txt",
  "robots.txt portfolio", "gptbot", "claudebot", "google-extended",
  "ccbot", "schema person", "json-ld person", "profilepage schema",
  "structured data portfolio", "stack portfolio", "que stack uso",
  "astro vs next", "cloudflare pages", "tailwind v4", "core web vitals
  2026", "lcp threshold", "dark mode portfolio", "modo oscuro",
  "wcag aa", "eu accessibility act", "ada compliance", "personal
  branding dev", "niche developer", "case studies portfolio",
  "problema solucion resultado", "narrative case study", "tendencias
  diseno 2026", "design trends 2026", "anti-patterns portfolio",
  "errores comunes portfolio", "que NO hacer portfolio",
  "verificacion tecnica portfolio", "checklist portfolio".
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: "<topico: ats / geo / stack / diseno / branding / checklist / anti-patterns>"
---

# Modern Portfolios 2026 — referencia consolidada

> Skill de referencia para todas las decisiones de estrategia general del
> portfolio: ATS, GEO, stack, diseno visual, personal branding,
> verificacion tecnica. Apoyado en investigacion exhaustiva (25+ fuentes).

## Regla cardinal

1. **SIEMPRE leer la doc primero**: `.claude/docs/modern-portfolios/README.md`
   con indice de los 12 capitulos. NO inventar recomendaciones; siempre
   citar el modulo concreto al final.
2. **NUNCA bloquear GPTBot / ClaudeBot / CCBot / Google-Extended** en
   `robots.txt` — mata GEO. Allow explicito.
3. **NUNCA tablas / multi-columna / imagenes con texto critico en el CV**
   ATS-friendly: rompe parsing.
4. **SIEMPRE case studies narrativos** (Problema -> Proceso -> Resultado
   con metricas concretas), no listas planas de skills.
5. **Lighthouse 95+** en performance / accessibility / best-practices /
   SEO es no-negociable.

## Mapa rapido pregunta -> modulo

| Pregunta del usuario | Doc |
|----------------------|-----|
| "panorama 2025-2026, como cambio respecto a 2024" | `01-contexto-tendencias.md` |
| "como paso el filtro ATS / job title keywords" | `02-optimizacion-ats.md` |
| "como aparezco en ChatGPT / Claude / Perplexity" | `03-geo-llm-seo.md` |
| "que contenido pongo (hero, case studies, skills)" | `04-estructura-contenido.md` |
| "estetica, dark mode, Core Web Vitals, a11y" | `05-diseno-visual-ux.md` |
| "que stack uso (Astro vs Next, hosting, CMS)" | `06-tecnologias.md` |
| "niche, GitHub README, LinkedIn" | `07-personal-branding.md` |
| "schema JSON-LD, robots.txt, validacion antes de publicar" | `08-verificacion-tecnica.md` |
| "top 10 errores que descartan automatica" | `09-anti-patterns.md` |
| "portfolio ganador 2026 + checklist por semana" | `10-conclusiones.md` |
| "fuentes / referencias" | `11-referencias.md` |
| "checklist rapida pre-deploy" | `12-checklist.md` |

## Resumen ejecutivo (cache mental)

- **Portfolio web propio > LinkedIn**: 72% de reclutadores evaluan
  primariamente via sitio personal.
- **ATS evoluciono a contextual**: adoption IA en ATS paso de 26% (2024)
  a 43% (2025). Job title visible = 10.6x mas probable entrevista.
- **GEO emerge**: SEO tradicional declinara 25% para 2026, 50% para 2028.
  `llms.txt` + Schema.org Person / ProfilePage son la nueva base.
- **Stack recomendado**: Astro 6.1 + Tailwind v4 + Cloudflare Pages
  (40% mas rapido que Next.js, bandwidth ilimitado).
- **Dark mode + WCAG AA obligatorios**: 82.7% usuarios dark, EU
  Accessibility Act vigente desde Jun 2025, ADA deadline Abr 2026.
  LCP < 2.0s (umbral nuevo Mar 2026).
- **Personal branding 2026 = criterio + accion**, no visibilidad. Niche
  claro + voice autentico + accion demostrable supera a "publica mas".

## Estilo de respuesta

- Empezar identificando que capitulo aplica.
- Citar al final la ruta exacta: `.claude/docs/modern-portfolios/<NN>-<topic>.md`.
- Indicar bundle / a11y impact cuando aplique.
- Para preguntas de animacion CSS especifica, redirigir a skill
  `animations-css`.
- Para preguntas de vibe coding / Claude Code / niveles dev, redirigir a
  skill `developer-portfolios-vibe-coding`.
- Para preguntas de schema / llms.txt / prompt injection white/grey/black
  hat, redirigir a skill `ai-prompt-optimization`.

## Cross-skill

| Tema | Skill a usar |
|------|--------------|
| Estrategia general / ATS / GEO / stack / branding | **este skill (`modern-portfolios`)** |
| Vibe coding, Claude Code/Cursor, GitHub, niveles | `developer-portfolios-vibe-coding` |
| JSON-LD details, llms.txt, white/grey/black hat | `ai-prompt-optimization` |
| Patron CSS especifico (keyframes, scroll, mesh) | `animations-css` |
| Decisiones arquitectonicas Astro consolidadas | `astro-portfolio` (hub) |
| TDD para componente nuevo | `tdd-workflow` |
| Lint Biome conformance | `fix-hooks` |

## Anti-patterns a corregir cuando aparezcan

- "Mete CCBot/GPTBot/ClaudeBot en disallow del robots.txt" -> mata GEO,
  ver `03-geo-llm-seo.md`.
- "Pongo tabla de skills en el PDF del CV" -> rompe parsing ATS, ver
  `02-optimizacion-ats.md`.
- "Lista plana de skills sin contexto" -> case studies narrativos ganan,
  ver `04-estructura-contenido.md`.
- "Full Stack Developer generico" -> niche gana, ver `07-personal-branding.md`.
- "Imagen con texto critico en CV" -> ATS no la lee, ver `02-optimizacion-ats.md`.
- "Mete Three.js en el hero" -> a11y / perf, ver `09-anti-patterns.md`.
- "Saltar Lighthouse" -> requisito no-negociable, ver `05-diseno-visual-ux.md`.

## Verificacion post-respuesta

- [ ] Cite ruta exacta a `.claude/docs/modern-portfolios/<modulo>.md`
- [ ] Redirigi a skill complementaria cuando aplique
- [ ] No propuse practica del anti-patterns list
- [ ] Recomendacion alineada con resumen ejecutivo

## Fuentes canonicas

- Indice de la investigacion: `.claude/docs/modern-portfolios/README.md`
- Hub de las 3 investigaciones: `.claude/docs/portfolio-research-hub/README.md`
- CV actual: `.claude/docs/cv/README.md`
- Convenciones Astro: `.claude/rules/astro-landing.md`
- Design system: `.claude/rules/design-system.md`
