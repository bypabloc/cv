---
name: ai-prompt-optimization
description: >
  Ethical AI optimization reference for the portfolio. Covers white-hat
  techniques (JSON-LD Person/Article/FAQ schema, llms.txt honest, robots.txt
  with explicit GPTBot/ClaudeBot/Google-Extended allow, semantic HTML, Open
  Graph), grey-hat zone (not recommended without total honesty), black-hat
  (educational ONLY, NEVER implement — 92% detection rate by modern ATS like
  Cangrade/Greenhouse/ManpowerGroup and by Claude Opus 4.5 / GPT-4o /
  Gemini; legal risk EU AI Act Art 9 + GDPR + ToS violation). Covers how
  modern LLMs (Claude Opus 4.5, GPT-4o, Gemini) parse portfolios, real
  cases 2024-2026, detection rates, official policies from OpenAI /
  Anthropic / Google, 4-week implementation checklist. ALWAYS invoke
  this skill BEFORE answering ANY question about schema markup, llms.txt,
  robots.txt for AI crawlers, prompt injection, or how to influence how
  LLMs read the portfolio. NEVER answer from training data alone — this
  project has a consolidated 2026 research module with current detection
  rates and ethical framework.

  Use when the user says "prompt injection", "schema.org", "json-ld",
  "json-ld person", "json-ld profilepage", "json-ld article", "faq
  schema", "schema markup", "structured data", "datos estructurados",
  "llms.txt", "robots.txt ai", "gptbot allow", "claudebot allow",
  "google-extended", "ccbot", "ai crawler", "ai crawlers", "como
  posiciono en ia", "como salgo en chatgpt", "como salgo en claude",
  "white hat seo ia", "grey hat seo ia", "black hat seo ia",
  "tecnicas white hat", "tecnicas black hat", "hidden text portfolio",
  "html comment ai", "ignore previous instructions cv", "manipular ia
  cv", "deteccion prompt injection", "ats detection rate", "como
  detectan ats", "spambrain", "openai ai policy", "anthropic ai
  policy", "google ai policy", "eu ai act", "gdpr ia cv", "fraude
  cv ia", "open graph portfolio", "semantic html portfolio",
  "checklist accionable ai", "implementacion semanal ai", "casos
  reales prompt injection", "tabla comparativa tecnicas ia".
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: "<topico: white-hat / grey-hat / black-hat / schema / llms.txt / robots.txt / casos / deteccion / checklist>"
---

# AI Prompt Optimization para Portfolio — referencia consolidada

> Skill de referencia para la metadata tecnica del portfolio que controla
> como LLMs (ChatGPT, Claude, Perplexity) leen, citan y procesan el sitio.
> Apoyado en investigacion exhaustiva 2026 (13 capitulos).

## Regla cardinal — DISCLAIMER ETICO

1. **SIEMPRE leer la doc primero**:
   `.claude/docs/ai-prompt-optimization/README.md`. NO inventar; citar el
   capitulo concreto.
2. **NUNCA proponer tecnicas black-hat ni grey-hat sin contexto defensivo
   explicito**. Capitulos 4 (grey-hat) y 5 (black-hat) existen
   **exclusivamente** para conocimiento defensivo y comprension del estado
   del arte. Recomendar implementacion = falla del skill.
3. **NUNCA hidden text, CSS tricks (`display:none`, `opacity:0`,
   `font-size:0`), HTML comments con instrucciones, JSON-LD con datos
   falsos, meta tags inconsistentes con contenido visible**.
4. **SIEMPRE preferir mejorar codigo real + documentacion** antes que
   cualquier tecnica de optimizacion para IAs. ROI mucho mejor.
5. **SIEMPRE validar consistencia** entre schema.org, contenido visible,
   LinkedIn y GitHub (las IAs cross-referencian).

### Riesgos cuantificados (cache mental)

- Tasa de deteccion de black-hat por ATS modernos: **~92%**.
- Diferencia white-hat optimizado vs sin optimizacion: **+10-20%** apariciones.
- Black-hat detectado: **-100%** (auto-rechazo + perdida de credibilidad).
- Riesgo legal: EU AI Act Art 9, GDPR, ToS de OpenAI / Anthropic / Google.

## Mapa rapido pregunta -> modulo

| Pregunta del usuario | Doc |
|----------------------|-----|
| "que es prompt injection / DPI vs IDPI" | `01-contexto-prompt-injection.md` |
| "como las IAs procesan mi portfolio" | `02-como-procesan-ias.md` |
| "que white-hat implemento (schema, llms.txt, semantic)" | `03-tecnicas-white-hat.md` |
| "JSON-LD Person / ProfilePage / Article / FAQ" | `03a-json-ld-schemas.md` |
| "semantic HTML + meta tags + Open Graph" | `03b-semantic-html-meta.md` |
| "llms.txt + robots.txt + sitemap.xml para crawlers IA" | `03c-llms-robots-sitemap.md` |
| "zona gris (grey-hat) — solo para evaluar riesgo" | `04-tecnicas-grey-hat.md` |
| "black-hat — solo defensivo, NUNCA implementar" | `05-tecnicas-black-hat.md` |
| "casos reales 2024-2026, por que black-hat falla" | `06-casos-reales.md` |
| "tasas de deteccion por ATS / humanos / LLMs" | `07-deteccion-riesgos.md` |
| "politica oficial OpenAI / Anthropic / Google" | `08-posturas-openai-anthropic.md` |
| "que implemento y que evito en mi portfolio" | `09-recomendacion-final.md` |
| "plan semanal de implementacion (4 semanas)" | `10-checklist-accionable.md` |
| "tabla comparativa: etica / efectividad / riesgo" | `11-tabla-comparativa.md` |
| "resumen + ROI" | `12-conclusion.md` |
| "fuentes bibliograficas" | `13-fuentes.md` |

## Resumen ejecutivo (cache mental)

- **White-hat es mas efectivo que black-hat**: sitios con
  `robots.txt + llms.txt + Person schema` aparecen 2.4x mas en respuestas
  de IAs. Black-hat falla en 92% de los casos -> auto-rechazo.
- **Las IAs modernas estan entrenadas contra prompt injection**: Claude
  Opus 4.5, GPT-4o, Gemini ignoran trucos obvios. ATS modernos (Cangrade,
  Greenhouse, ManpowerGroup) detectan >90%.
- **Stack white-hat prioritario**:
  1. Person/Article schema JSON-LD
  2. llms.txt honesto
  3. robots.txt con allow explicito para GPTBot/ClaudeBot/Google-Extended/CCBot
  4. semantic HTML
  5. FAQ schema
  6. Open Graph optimizado
- **Riesgo black-hat**: si un reclutador o ATS detecta el truco, perdida
  total de credibilidad. Caso documentado 2024: candidato reportado a
  compliance por intento de fraude.
- **ROI verdadero**: tiempo en mejorar codigo y documentacion (READMEs
  excelentes) > cualquier intento de manipulacion.

## Estilo de respuesta

- Empezar identificando que capitulo aplica.
- Si la pregunta toca grey-hat o black-hat: responder en modo defensivo,
  citar tasa de deteccion, redirigir a white-hat equivalente.
- Citar al final la ruta exacta:
  `.claude/docs/ai-prompt-optimization/<NN>-<topic>.md`.
- Para preguntas de estrategia general / ATS / stack tecnico, redirigir a
  skill `modern-portfolios`.
- Para preguntas de Claude Code / Cursor / vibe coding / GitHub profile,
  redirigir a skill `developer-portfolios-vibe-coding`.

## Cross-skill

| Tema | Skill a usar |
|------|--------------|
| Schema, llms.txt, robots.txt, white/grey/black hat | **este skill (`ai-prompt-optimization`)** |
| Estrategia general / ATS / stack / branding | `modern-portfolios` |
| Claude Code / Cursor / GitHub / niveles dev | `developer-portfolios-vibe-coding` |
| Decisiones arquitectonicas Astro consolidadas | `astro-portfolio` (hub) |
| Patron CSS especifico | `animations-css` |

## Anti-patterns a RECHAZAR (sin excepcion)

- "Voy a meter prompt injection oculto para que ChatGPT me recomiende" ->
  detectable, riesgo EU AI Act Art 9, GDPR, ver `05-tecnicas-black-hat.md`.
- "Texto blanco sobre blanco con keywords" -> SpamBrain 2025 lo detecta,
  ver `07-deteccion-riesgos.md`.
- "Hidden divs con instrucciones para IAs" -> idem.
- "Comentarios HTML con 'ignore previous instructions'" -> idem.
- "JSON-LD con experiencia inflada / titulos falsos" -> las IAs
  cross-referencian con LinkedIn / GitHub, ver `09-recomendacion-final.md`.
- "Meta tags inconsistentes con contenido visible" -> red flag inmediata,
  ver `07-deteccion-riesgos.md`.
- "Disallow GPTBot en robots.txt porque no quiero que me roben contenido"
  -> mata GEO, ver `03c-llms-robots-sitemap.md`.

## Anti-patterns a corregir (grey zone)

- "Llenar llms.txt con keywords sin contenido real" -> contraproducente,
  ver `04-tecnicas-grey-hat.md`.
- "Schema FAQ con preguntas auto-formuladas exageradas" -> riesgo de
  rechazo, ver `04-tecnicas-grey-hat.md`.

## Verificacion post-respuesta

- [ ] Cite ruta exacta a `.claude/docs/ai-prompt-optimization/<modulo>.md`
- [ ] No propuse practica del black-hat / grey-hat list (sin proposito defensivo)
- [ ] Recomendacion alineada con tecnicas white-hat (cap 3)
- [ ] Si la pregunta sugeria black-hat, propuse alternativa white-hat
- [ ] Cite tasa de deteccion / riesgo legal cuando aplique

## Fuentes canonicas

- Indice de la investigacion: `.claude/docs/ai-prompt-optimization/README.md`
- Hub de las 3 investigaciones: `.claude/docs/portfolio-research-hub/README.md`
- CV actual: `.claude/docs/cv/README.md`
- Convenciones Astro: `.claude/rules/astro-landing.md`
