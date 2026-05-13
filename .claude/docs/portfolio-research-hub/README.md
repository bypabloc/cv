---
title: Investigaciones para Portfolio/CV 2026 — Indice Maestro
description: >
  Hub central de las 3 investigaciones exhaustivas sobre como construir un
  portfolio moderno post-IA, optimizado para reclutadores tech, vibe coding
  y crawlers de LLMs.
date: 2026-05-12
audience: Pablo Contreras (rehacer portfolio bypabloc/portfolio)
status: stable
---

# Investigaciones para Portfolio/CV 2026 — Indice Maestro

> Hub central de las 3 investigaciones que sustentan el rediseno del portfolio. Lee este indice primero, luego salta al README de la investigacion que necesites.

## Las 3 investigaciones

| # | Investigacion | Foco | Cuando leer |
|---|---------------|------|-------------|
| 1 | [Portfolios modernos post-IA](../modern-portfolios/README.md) | Tendencias generales 2025-2026, ATS, GEO/LLM-SEO, estructura, UX, tecnologias, personal branding | Antes de definir la arquitectura general del portfolio |
| 2 | [Portfolios de desarrolladores + vibe coding](../developer-portfolios-vibe-coding/README.md) | Especifico para devs: Claude Code/Cursor/Windsurf, GitHub, presencia online, junior/mid/senior post-IA | Al decidir que proyectos, skills y narrativa tecnica mostrar |
| 3 | [Optimizacion para IA / prompt injection](../ai-prompt-optimization/README.md) | White-hat / grey-hat / black-hat para influenciar como las IAs leen tu portfolio. Schema, llms.txt, riesgos eticos | Al implementar metadata y estructura tecnica del sitio |

## Resumen consolidado (los 5 hallazgos que mas importan)

1. **GEO > SEO tradicional**: aparecer en respuestas de ChatGPT/Claude/Perplexity cuando alguien pregunta "best developer for X" es la nueva primera pagina de Google. Se logra con JSON-LD Person schema + llms.txt + semantic HTML.

2. **AI Literacy es el nuevo diferenciador**: 92% de devs usan IA daily. Documentar tu workflow con Claude Code / Cursor (con prompts reales, no marketing) supera al portfolio "miren cuanto codigo escribi a mano".

3. **Proyectos > Lista de skills**: case studies narrativos (Problema → Solucion → Impacto con metricas) ganan 72% vs listas. Side projects con IA cuentan SI muestras el proceso, no solo el output. SaaS monetizado (aunque sea $100/mes) es senal fuerte.

4. **Stack ganador para portfolio dev 2026**: Astro 6.1 + Cloudflare Pages + Tailwind v4. 40% mas rapido que Next.js, 90% menos JS, hosting unlimited bandwidth. Tu propio repo del portfolio comunica skill tecnico.

5. **Solo white-hat**: black-hat prompt injection es detectable al 92%+ por SpamBrain 2025 y Claude Opus 4.5. ROI negativo. La estrategia ganadora es schema markup riguroso + llms.txt + contenido autentico bien estructurado.

## Reglas criticas

- **NUNCA** usar tecnicas black-hat (texto blanco sobre blanco, hidden divs con prompts, comentarios HTML con "ignore previous instructions"). Riesgo legal (EU AI Act Art 9, GDPR), reputacional y tecnico es prohibitivo.
- **SIEMPRE** implementar Person schema JSON-LD + llms.txt + Open Graph + sitemap.xml como baseline.
- **DOCUMENTAR uso de IA** en proyectos es ventaja competitiva en 2026, no liability. La trampa es fingir que no la usas.
- **NICHE > generalista**: portfolio que dice "Full Stack Developer con experiencia fintech Chile/Peru y agentes IA" gana a "Full Stack Developer".
- **Plan de implementacion 4 semanas**: ver checklist en cada investigacion (semana 1 = schema + semantic; semana 2 = llms.txt + robots; semana 3 = Open Graph + casos de estudio; semana 4 = testing).

## Como usar este hub

```
Paso 1: Lee este README (estas aqui)
Paso 2: Lee ../modern-portfolios/README.md para entender el marco general
Paso 3: Lee ../developer-portfolios-vibe-coding/README.md para skills/proyectos
Paso 4: Lee ../ai-prompt-optimization/README.md para metadata tecnica
Paso 5: Cruza con .claude/docs/cv/ (tu CV actual) para identificar gaps
Paso 6: Genera plan de implementacion con spec-workflow skill
```

## Cobertura cruzada (que investigacion responde que pregunta)

| Pregunta | Investigacion principal | Investigacion complementaria |
|----------|--------------------------|------------------------------|
| ¿Que stack uso para construir el portfolio? | [Modern #6 Tecnologias](../modern-portfolios/06-tecnologias.md) | [Dev #11 Stack/Checklist](../developer-portfolios-vibe-coding/11-stack-checklist.md) |
| ¿Como paso el filtro de ATS? | [Modern #2 ATS](../modern-portfolios/02-optimizacion-ats.md) | [AI-Opt #3 White-Hat](../ai-prompt-optimization/03-tecnicas-white-hat.md) |
| ¿Como aparezco en respuestas de ChatGPT/Claude? | [Modern #3 GEO](../modern-portfolios/03-geo-llm-seo.md) | [AI-Opt #3a JSON-LD](../ai-prompt-optimization/03a-json-ld-schemas.md), [AI-Opt #3c llms.txt](../ai-prompt-optimization/03c-llms-robots-sitemap.md) |
| ¿Que proyectos muestro? | [Dev #4 Proyectos](../developer-portfolios-vibe-coding/04-proyectos-mostrar.md) | [Modern #4 Estructura](../modern-portfolios/04-estructura-contenido.md) |
| ¿Como hablo de mi uso de Claude Code? | [Dev #9 Documentacion IA](../developer-portfolios-vibe-coding/09-documentacion-uso-ia.md) | [Dev #3 Herramientas IA](../developer-portfolios-vibe-coding/03-herramientas-ia.md) |
| ¿Que NO hacer? | [Modern #9 Anti-patterns](../modern-portfolios/09-anti-patterns.md) | [AI-Opt #5 Black-Hat](../ai-prompt-optimization/05-tecnicas-black-hat.md), [AI-Opt #7 Riesgos](../ai-prompt-optimization/07-deteccion-riesgos.md) |
| ¿Que diferencia junior/mid/senior 2026? | [Dev #8 Niveles](../developer-portfolios-vibe-coding/08-niveles-junior-mid-senior.md) | [Dev #2 Reclutadores](../developer-portfolios-vibe-coding/02-reclutadores-tech.md) |

## Recursos relacionados en el proyecto

- [.claude/docs/cv/README.md](../cv/README.md) — CV actual de Pablo Contreras (fuente de datos)
- [.claude/docs/animations-css/README.md](../animations-css/README.md) — Animaciones permitidas para el portfolio
- [.claude/rules/design-system.md](../../rules/design-system.md) — Tokens, tipografia, modo dark/light
- [.claude/rules/astro-landing.md](../../rules/astro-landing.md) — Convenciones Astro 6.1

## Metodologia de las investigaciones

- **Fuentes**: minimo 20 fuentes por investigacion (papers, tech blogs, reclutadores reales en LinkedIn/Twitter, HackerNews, dev.to, prensa tech). URLs citadas en seccion `fuentes.md` de cada modulo.
- **Periodo**: solo contenido 2025-2026 (excluye info obsoleta pre-IA o pre-vibe coding).
- **Idioma**: espanol, terminos tecnicos en ingles cuando aporte claridad.
- **Sin emojis** en contenido (convencion del proyecto).
- **Disclaimer etico**: la investigacion #3 incluye tecnicas black-hat con proposito educativo. La recomendacion explicita es usar SOLO white-hat.

## Proximos pasos sugeridos

1. Revisar este README y los 3 sub-READMEs (~15 min)
2. Identificar 3-5 gaps entre CV actual y recomendaciones (`.claude/docs/cv/` vs investigaciones)
3. Generar plan de implementacion con `/spec-workflow` skill (descompone en tareas atomicas)
4. Implementar baseline tecnico (schema + llms.txt + robots.txt) — semana 1
5. Iterar contenido (case studies, narrativa, proyectos) — semanas 2-4
