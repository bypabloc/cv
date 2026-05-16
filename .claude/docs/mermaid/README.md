# Mermaid - Referencia Tecnica

> Lenguaje de diagramas basado en texto con soporte para ER, flowchart,
> arquitectura y secuencia. Renderizado nativo en GitHub, Notion y VS Code.

## Contenido

| Tema | Archivo | Cuando leer |
|------|---------|-------------|
| Sintaxis de los 4 tipos | [01-syntax-reference.md](01-syntax-reference.md) | Buscar sintaxis exacta, escribir diagramas desde cero |
| Tipos con ejemplos del proyecto | [02-diagram-types.md](02-diagram-types.md) | Ver ejemplos reales, elegir el tipo correcto |
| Best practices y errores comunes | [03-best-practices.md](03-best-practices.md) | Evitar errores, optimizar legibilidad, nomenclatura |

## Reglas criticas

- SIEMPRE usar extension `.mmd` para archivos Mermaid
- SIEMPRE guardar en `docs/diagrams/` del root del proyecto
- SIEMPRE usar nombres kebab-case sin acentos: `<tipo>-<descripcion>.mmd`
  - Prefijos validos: `er-`, `flow-`, `arch-`, `seq-`
  - Ejemplos: `er-product-models.mmd`, `flow-order-pipeline.mmd`
- NUNCA mezclar tipos de diagrama en un mismo archivo `.mmd`
- NUNCA usar caracteres especiales sin escapar en labels de nodos
- Si el diagrama supera el limite de legibilidad, partir en multiples archivos

## Tipos disponibles

| Tipo | Keyword | Uso |
|------|---------|-----|
| Entity-Relationship | `erDiagram` | Modelos de datos, esquemas de BD |
| Flowchart | `flowchart TD` / `flowchart LR` | Pipelines, procesos, flujos de decision |
| Architecture | `graph LR` / C4Context | Servicios Docker, sistemas distribuidos |
| Sequence | `sequenceDiagram` | Llamadas a APIs, flujos de autenticacion |

## Navegacion

Contexto padre: [CLAUDE.md](../../../CLAUDE.md)
