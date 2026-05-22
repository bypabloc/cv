---
description: "Convenciones Knowledge Tree para documentacion en .claude/docs/: formato README, capitulos, navegacion progresiva"
globs: ".claude/docs/**/*.md"
---

# Documentacion del proyecto

## Dos zonas en `docs/`

`docs/` tiene dos zonas con propositos distintos. Ambas conviven en la misma
raiz por decision del proyecto, pero NO se mezclan archivos dentro de la
misma subcarpeta:

| Zona | Subcarpetas | Audiencia | Estabilidad | Formato |
|------|-------------|-----------|-------------|---------|
| **Producto** (Knowledge Tree) | `cv/`, `guide/`, `design-system/`, `diagrams/`, `claude/` | Reviewers, visitantes del repo | Cambia raramente | Knowledge Tree (abajo) |
| **Harness interno** | `progress/`, `specs/`, `<area>/`, `CHECKPOINTS.md` | Orquestador (Claude + dev actual) | Cambia constantemente | Formato libre o JSON (queues, scratchpads) |

La zona harness contiene `feature_list.json` opcional (uno por area si hay
sub-areas: `docs/cv/feature_list.json`, `docs/projects/feature_list.json`),
y `docs/progress/` (scratchpads de sesion). NO sigue Knowledge Tree porque
no son documentos navegables sino artefactos del agente.

`docs/specs/` tambien es zona harness: cada carpeta de plan es un artefacto
**efimero** que se elimina al mergear el plan a `dev` (ver
`.claude/rules/plan-format.md`, "Ciclo de vida de la carpeta del plan").
`docs/specs/` solo contiene planes pendientes o en ejecucion — nunca planes
ya implementados.

Reglas autoritativas de la zona harness: `.claude/rules/harness-protocol.md`.

## Formato obligatorio (solo zona producto)

Cada archivo de la zona producto sigue el formato Knowledge Tree:

### READMEs (indice)
1. `# Titulo`
2. `> Blockquote` descriptivo de 1 linea
3. Tabla de contenidos con columna **"Cuando leer"**
4. `## Reglas criticas` — directivas SIEMPRE/NUNCA
5. `## Navegacion` — links a otros documentos

### Capitulos
1. Header de navegacion con links a anterior/siguiente
2. Contenido en secciones `## H2`
3. Ejemplos practicos con bloques de codigo
4. Footer con link de retorno

## Reglas de contenido

- Idioma: espanol. Terminos tecnicos en ingles
- Sin emojis
- Sin acentos en nombres de archivo (kebab-case)
- Links internos SIEMPRE relativos, nunca absolutos
- Cada nodo < 300 lineas
- Profundidad maxima: 3 niveles
