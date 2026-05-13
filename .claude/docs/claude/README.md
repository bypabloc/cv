# Claude Code - Referencia para Portfolio

> Documentacion de Claude Code (rules, skills, CLAUDE.md) para crear y mantener la configuracion de este proyecto.

## Contenido

| Pilar | Archivo | Proposito |
|-------|---------|-----------|
| **Rules** | `.claude/rules/*.md` | Reglas modulares por dominio/tipo de archivo (auto-load por path) |
| **Skills** | `.claude/skills/*/SKILL.md` | Capacidades especializadas invocables (manual o auto) |
| **Docs** | `CLAUDE.md` | Memoria persistente del proyecto, contexto global |

## Navegacion

| # | Documento | Cuando leer |
|---|-----------|-------------|
| 6 | [Rules](06-rules.md) | Crear reglas en `.claude/rules/`: path-specific con `globs:`, jerarquia, ejemplos |
| 7 | [Skills - Referencia](07-skills.md) | Crear skills: frontmatter, `allowed-tools`, ejemplos, diagnostico |
| 8 | [Documentacion - CLAUDE.md](08-docs.md) | Escribir o mejorar CLAUDE.md: jerarquia de memoria, Knowledge Tree |

## Reglas criticas

- SIEMPRE leer el capitulo correspondiente ANTES de crear rules, skills o modificar CLAUDE.md
- NUNCA crear skills sin leer la referencia (cap. 7) para evitar anti-patrones
- Para documentar el proyecto, leer cap. 8 que incluye el patron Knowledge Tree

## Guia practica de uso (especifica del proyecto)

Para saber **como usar** las 24 skills + 9 agents + 17 rules ya creadas en este
proyecto (con ejemplos de prompts y workflows tipicos), ver:

- [docs/claude/project-guide.md](../../../docs/claude/project-guide.md) — guia practica del proyecto

Contexto padre: [CLAUDE.md](../../../CLAUDE.md)
