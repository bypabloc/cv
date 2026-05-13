---
name: developer-portfolios-vibe-coding
description: >
  Developer portfolio reference for the vibe coding era (Claude Code,
  Cursor, Windsurf). Covers: what tech recruiters look for 2025-2026, AI
  tools comparison (Claude Code 91% CSAT / 54 NPS / 92.4% SWE-bench
  Verified, Cursor 1M+ DAU, Windsurf acquired by Cognition AI for 10.2B),
  what projects to show (6 pinned GitHub repos, side SaaS monetized, OSS
  contributions), GitHub Profile optimization, online presence (Twitter/X,
  LinkedIn, Dev.to, Twitch), hot technical skills 2025-2026, junior vs mid
  vs senior career planning post-AI (junior pipeline -54% hiring, seniors
  2.5x shipped code), how to transparently document AI usage in projects,
  emerging trends, stack checklist, real portfolio examples. ALWAYS invoke
  this skill BEFORE answering ANY question about dev-specific portfolio,
  AI tooling stack, recruiter expectations, career seniority, GitHub
  optimization or how to document AI usage. NEVER answer from training
  data alone — this project has a consolidated 2026 research module that
  overrides generic advice.

  Use when the user says "vibe coding", "claude code portfolio",
  "cursor portfolio", "windsurf portfolio", "ai tools comparison",
  "claude code vs cursor", "cursor vs windsurf", "que herramienta ia uso",
  "que ide ia", "reclutadores tech 2026", "que buscan recruiters",
  "tech hiring 2026", "skills based hiring", "que proyectos mostrar",
  "side projects portfolio", "saas monetizado", "open source
  contributions", "github profile", "perfil github", "profile readme",
  "pinned repos", "presencia online", "twitter dev", "linkedin dev",
  "dev.to", "twitch coding", "personal brand twitter", "skills tecnicos
  hot", "skills 2026", "que aprender 2026", "ai engineer", "prompt
  engineer", "junior dev 2026", "mid dev 2026", "senior dev 2026",
  "niveles seniority post-ia", "junior pipeline", "documentar uso ia",
  "transparencia ia", "como hablar de claude code", "como documentar
  prompt", "ai disclosure", "tendencias dev 2026", "ejemplos portfolios
  dev", "portfolio bueno dev", "stack dev portfolio".
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: "<topico: reclutadores / herramientas-ia / proyectos / github / niveles / docs-ia / ejemplos>"
---

# Developer Portfolios + Vibe Coding 2026 — referencia consolidada

> Skill de referencia para decisiones de contenido tecnico del portfolio:
> que proyectos mostrar, como documentar uso de IA, GitHub profile, niveles
> jr/mid/sr. Apoyado en investigacion exhaustiva (25+ fuentes 2025-2026).

## Regla cardinal

1. **SIEMPRE leer la doc primero**: `.claude/docs/developer-portfolios-vibe-coding/README.md`
   con indice de los 14 capitulos. NO inventar; citar el modulo concreto.
2. **NUNCA listar "AI-generated codebase" como atributo positivo** -> senal
   de no poder mantener el codigo.
3. **NUNCA pinear repos sin demo en vivo o video walkthrough**.
4. **SIEMPRE documentar uso de IA de forma transparente** -> ocultarlo o
   exagerarlo penaliza igual ante reclutadores 2026.
5. **SIEMPRE incluir metricas** (usuarios, MRR, tiempo ahorrado, bugs
   reducidos) en proyectos del portfolio.

## Mapa rapido pregunta -> modulo

| Pregunta del usuario | Doc |
|----------------------|-----|
| "contexto / datos macro del cambio de paradigma" | `01-introduccion-vibe-coding.md` |
| "que buscan reclutadores tech 2025-2026" | `02-reclutadores-tech.md` |
| "Claude Code vs Cursor vs Windsurf, que IDE elijo" | `03-herramientas-ia.md` |
| "que side projects / OSS / hackatons priorizar" | `04-proyectos-mostrar.md` |
| "como rediseno mi GitHub profile / pinned repos" | `05-github-profile.md` |
| "Twitter/X / LinkedIn / Dev.to / Twitch strategy" | `06-presencia-online.md` |
| "que aprender / profundizar 2025-2026" | `07-skills-tecnicos.md` |
| "diferencia junior / mid / senior post-IA" | `08-niveles-junior-mid-senior.md` |
| "como describir que construi con IA" | `09-documentacion-uso-ia.md` |
| "hacia donde va el mercado" | `10-tendencias-emergentes.md` |
| "stack + checklist pre-publicar" | `11-stack-checklist.md` |
| "ejemplos reales de portfolios destacados" | `12-ejemplos-portfolios.md` |
| "fuentes / referencias" | `13-fuentes.md` |
| "resumen 2026 vs 2020" | `14-conclusion.md` |

## Resumen ejecutivo (cache mental)

- **Vibe coding** = Palabra del Ano 2025 (Oxford). 92% de devs US usan IA
  daily, 41% del codigo global es AI-generado en 2026.
- **Recruiting pivoto** de "puede escribir codigo" a "puede orquestar IA,
  evaluar output criticamente, entregar features rapido". 70% skills-based.
- **Claude Code** lidera satisfaccion (91% CSAT, 54 NPS, 92.4% SWE-bench
  Verified). Cursor 1M+ DAU. Windsurf adquirido por Cognition AI ($10.2B).
- **Portfolio ganador**: 6 repos pinneados estrategicos + side SaaS
  monetizado + OSS visible + Twitter/X + blog tecnico + AI docs
  transparente.
- **Mercado bifurcado**: junior hiring -54%, pero seniors con IA fluida
  ganan 2.5x mas shipped code. AI Engineer +300% YoY, Prompt Engineer -60%.

## Estilo de respuesta

- Empezar identificando que capitulo aplica.
- Citar al final la ruta exacta:
  `.claude/docs/developer-portfolios-vibe-coding/<NN>-<topic>.md`.
- Indicar siempre si la sugerencia aplica a junior / mid / senior (puede
  variar mucho).
- Para preguntas de estrategia general / ATS / stack tecnico, redirigir a
  skill `modern-portfolios`.
- Para preguntas de schema markup / llms.txt / prompt injection, redirigir
  a skill `ai-prompt-optimization`.

## Cross-skill

| Tema | Skill a usar |
|------|--------------|
| Vibe coding, Claude Code, GitHub profile, niveles | **este skill (`developer-portfolios-vibe-coding`)** |
| Estrategia general / ATS / GEO / stack | `modern-portfolios` |
| JSON-LD, llms.txt, white/grey/black hat | `ai-prompt-optimization` |
| Decisiones arquitectonicas Astro consolidadas | `astro-portfolio` (hub) |
| Patron CSS especifico | `animations-css` |

## Anti-patterns a corregir cuando aparezcan

- "Voy a pinear 6 repos sin demos" -> sin demo en vivo o video walkthrough
  resta credibilidad, ver `05-github-profile.md`.
- "Listo 'AI-generated codebase' como ventaja" -> senal de no mantenibilidad,
  ver `09-documentacion-uso-ia.md`.
- "Oculto que uso Claude Code" -> en 2026 es liability, ver `09-documentacion-uso-ia.md`.
- "Exagero como uso IA (90% del codigo es vibe)" -> red flag, ver
  `09-documentacion-uso-ia.md`.
- "Soy Full Stack Developer" generico -> niche dev (ver `02-reclutadores-tech.md`).
- "Pongo Prompt Engineer como titulo" -> rol declino 60%, ver `07-skills-tecnicos.md`.

## Verificacion post-respuesta

- [ ] Cite ruta exacta a `.claude/docs/developer-portfolios-vibe-coding/<modulo>.md`
- [ ] Indique nivel (jr/mid/sr) si la respuesta varia
- [ ] Redirigi a skill complementaria cuando aplique
- [ ] No propuse practica del anti-patterns list

## Fuentes canonicas

- Indice de la investigacion: `.claude/docs/developer-portfolios-vibe-coding/README.md`
- Hub de las 3 investigaciones: `.claude/docs/portfolio-research-hub/README.md`
- CV actual: `.claude/docs/cv/README.md`
