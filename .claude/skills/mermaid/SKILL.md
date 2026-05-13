---
name: mermaid
description: >
  Creates and modifies Mermaid diagrams (.mmd) in docs/diagrams/. ALWAYS
  invoke for any .mmd file creation/modification. Triggers: "mermaid",
  "diagrama mermaid", "crear diagrama", "flowchart", "diagrama ER", "diagrama
  de secuencia", "erDiagram", "sequenceDiagram", "ER diagram", "sequence
  diagram", "flow diagram", "crear mmd", "generar mmd". More keywords:
  .claude/docs/skills/mermaid.md
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep
argument-hint: "tipo: er | flow | arch | seq"
metadata:
  version: "2.0"
---

# Mermaid - Generador de Diagramas

Crea y modifica archivos `.mmd` en `docs/diagrams/` del proyecto.

## Pre-requisitos OBLIGATORIOS

Antes de generar cualquier diagrama, leer segun el tipo solicitado:

| Tipo | Archivos a leer |
|------|----------------|
| `er` | `.claude/docs/mermaid/01-syntax-reference.md` seccion erDiagram + `.claude/docs/mermaid/02-diagram-types.md` seccion erDiagram |
| `flow` | `.claude/docs/mermaid/01-syntax-reference.md` seccion flowchart + `.claude/docs/mermaid/02-diagram-types.md` seccion flowchart |
| `arch` | `.claude/docs/mermaid/01-syntax-reference.md` seccion architecture + `.claude/docs/mermaid/02-diagram-types.md` seccion architecture |
| `seq` | `.claude/docs/mermaid/01-syntax-reference.md` seccion sequenceDiagram + `.claude/docs/mermaid/02-diagram-types.md` seccion sequenceDiagram |
| cualquiera | `.claude/docs/mermaid/03-best-practices.md` (siempre) |

## Argumentos

- `$ARGUMENTS[0]`: tipo de diagrama (`er`, `flow`, `arch`, `seq`)
- `$ARGUMENTS[1]+`: descripcion del contenido (opcional, se infiere del contexto)

## Mapeo tipo → diagrama Mermaid

| Argumento | Tipo Mermaid | Prefijo de archivo |
|-----------|-------------|-------------------|
| `er` | `erDiagram` | `er-` |
| `flow` | `flowchart TD` | `flow-` |
| `arch` | `graph LR` o `C4Context` | `arch-` |
| `seq` | `sequenceDiagram` | `seq-` |

Si no hay argumento, inferir el tipo del contexto de la solicitud del usuario.

## Workflow

### Paso 1: Leer documentacion

Leer los archivos de `.claude/docs/mermaid/` correspondientes al tipo segun la tabla
de pre-requisitos. Siempre leer `03-best-practices.md`.

### Paso 2: Determinar nombre del archivo

Construir nombre siguiendo la convencion `<tipo>-<descripcion>.mmd` en kebab-case sin acentos:

- `er-generation-models.mmd`
- `flow-processing-pipeline.mmd`
- `arch-docker-services.mmd`
- `seq-api-call.mmd`

Si la descripcion no fue provista, usar el contexto de la solicitud del usuario.

### Paso 3: Verificar existencia

Usar Glob para buscar en `docs/diagrams/*.mmd`:

- Si el usuario menciono un archivo existente: leerlo con Read para entender su contenido actual
- Si es un diagrama nuevo: continuar con la generacion

### Paso 4: Recopilar contexto del proyecto (segun tipo)

**Para `er` (entity-relationship):**

Solo aplica si el proyecto tiene modelos de datos (content collections de
Astro con schema Zod, o tipos TypeScript que modelen entidades). Si es solo
contenido del CV (perfil, experiencia, educacion), el ER es opcional y
suele no aportar valor.

Si aplica, leer schemas en `src/content/config.ts` o tipos en `src/types/`
y mapearlos al diagrama segun `02-diagram-types.md`.

**Para `arch` (architecture):**

En un portfolio estatico Astro, la arquitectura tipica es trivial
(browser ↔ CDN ↔ static files). Considerar si el diagrama aporta valor
antes de generarlo. Si aplica, modelar build pipeline, integraciones de
Astro, o flujo de despliegue.

**Para `flow` y `seq`:**

Leer el archivo fuente relevante (`src/pages/*.astro`, `src/lib/*.ts`) si
el usuario lo especifica o si se puede inferir del contexto.

### Paso 5: Generar el diagrama

Construir el contenido `.mmd` siguiendo la sintaxis de `01-syntax-reference.md`.

Estructura obligatoria del archivo:

```
---
title: Titulo Descriptivo del Diagrama
---
<tipo de diagrama>
    <contenido>
```

El frontmatter YAML con `title` es opcional pero mejora la visualizacion en previews.

Validar mentalmente antes de escribir:

- Sin caracteres especiales no escapados en labels (parentesis, dos puntos, comas)
- Relaciones y flechas validas para el tipo elegido
- Indentacion consistente de 4 espacios
- Un solo tipo de diagrama en el archivo
- Sin keyword `end` como nombre de nodo
- Cardinalidades con `--` obligatorio entre las dos partes (ej: `||--o{`)

### Paso 6: Escribir el archivo

- **Nuevo**: usar Write en `docs/diagrams/<nombre>.mmd`
- **Modificacion**: leer el archivo actual con Read, aplicar cambios con Edit

### Paso 7: Reportar al usuario

Informar:

- Ruta exacta del archivo: `docs/diagrams/<nombre>.mmd`
- Tipo de diagrama usado
- Herramientas para visualizar:
  - GitHub: renderiza en bloques de codigo con lenguaje `mermaid` en `.md`
  - VS Code: extension `bierner.markdown-mermaid` (Markdown Preview Mermaid Support)
  - Online: mermaid.live para prototipado rapido
  - MCP: `claude-mermaid` configurado en el proyecto para preview live

## Reglas

- SIEMPRE leer la documentacion de `.claude/docs/mermaid/` antes de generar
- SIEMPRE guardar en `docs/diagrams/`, nunca en `tmp/` ni en otro directorio
- SIEMPRE usar extension `.mmd`
- SIEMPRE nombres en kebab-case sin acentos
- NUNCA mezclar tipos de diagrama en un archivo
- NUNCA usar `end` como nombre de nodo en flowchart
- Para ER: SIEMPRE leer los `models.py` del proyecto antes de diagramar
- Para architecture: preferir C4Context para sistemas, `graph LR` para servicios Docker
- Si el diagrama supera el limite de legibilidad, partir en multiples archivos con sufijo `-part1`, `-part2`
