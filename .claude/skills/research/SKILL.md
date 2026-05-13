---
name: research
description: >
  Deep research of technologies, libraries, APIs and solutions with
  comparative analysis. ALWAYS invoke when user requests technical research.
  Triggers: "investigar", "research", "comparar", "buscar informacion sobre",
  "evaluar opciones", "alternativas a", "que opciones hay para".
user-invocable: true
allowed-tools: Read, Glob, Grep, Agent, WebSearch, WebFetch
argument-hint: "tema a investigar"
metadata:
  version: "3.1"
---

# Research - Investigacion Tecnologica

## Regla Principal

Delegar SIEMPRE la investigacion al agente `researcher` usando el Agent tool con `subagent_type: "researcher"`.

## Workflow

### Paso 1: Delegar al agente researcher

Usar el Agent tool para lanzar un subagente con el siguiente prompt:

```
Eres un agente de investigacion tecnologica para este portfolio.

Contexto del proyecto:
- Stack: Astro 6 + TypeScript 6 + Biome v2 + Vitest + Playwright
- Package manager: pnpm
- Output: build estatico para hosting CDN
- Enfoque: site personal de CV/portfolio (no backend)

Lee el archivo .claude/agents/researcher.md para entender tu rol completo.

Investiga: [TEMA DEL USUARIO]

Formato de salida obligatorio:
## [Tema]
### Contexto
### Opciones evaluadas (tabla comparativa, min 2-3 opciones)
### Recomendacion (concreta, justificada para este portfolio)
### Fuentes (con fecha)
```

Pasar `$ARGUMENTS` como el tema a investigar.

### Paso 2: Presentar resultados

Mostrar al usuario los resultados del agente sin modificaciones.

## Reglas

- SIEMPRE delegar al agente researcher — no investigar en el contexto principal
- SIEMPRE pasar el contexto del proyecto al agente
- SIEMPRE buscar contenido 2025+ primero, 2024 como fallback
- SIEMPRE incluir tabla comparativa en los resultados
- SIEMPRE citar fuentes con fecha
- SIEMPRE dar recomendacion concreta
- NUNCA usar informacion de 2023 o anterior sin advertencia
- Responder en el idioma del usuario (espanol por defecto)
