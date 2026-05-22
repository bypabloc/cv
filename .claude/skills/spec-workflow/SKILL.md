---
name: spec-workflow
description: >
  Specification-driven dev workflow (decompose features into specs, atomic
  tasks, persistent spec files, progress tracking). Extends plan-format rule.
  ALWAYS invoke for feature specification or task decomposition. Triggers:
  "spec", "especificacion", "descomponer feature", "breakdown", "plan
  feature", "task decomposition", "tareas atomicas", "requirements", "design
  doc", "RFC", "proposal", "feature planning".
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep
argument-hint: "mode: new | bug | review | status"
metadata:
  version: "2.0"
---

# Spec Workflow - Desarrollo Guiado por Especificaciones

Workflow estructurado para features y bugs: de requisitos a implementacion.

## Modos

### `new` (default) — Nueva feature

1. **Recopilar requisitos** del usuario
2. **Generar spec** en `docs/specs/SPEC-NNN-nombre.md`
3. **Descomponer** en tasks atomicas
4. **Validar** spec con el usuario antes de implementar

### `bug` — Fix de bug

1. **Documentar** el bug (sintomas, reproduccion, impacto)
2. **Analizar** causa raiz (leer codigo, logs del navegador)
3. **Proponer** fix con scope minimo
4. **Verificar** que el fix no introduce regresiones

### `review` — Revisar spec existente

1. Leer spec de `docs/specs/`
2. Verificar progreso vs tasks definidas
3. Identificar blockers o cambios de scope

### `status` — Estado de specs activas

1. Listar specs en `docs/specs/`
2. Mostrar estado de cada una (draft/approved/in-progress/done)

## Template de spec (generado automaticamente)

```markdown
# SPEC-NNN: [Titulo]

**Estado**: draft | approved | in-progress | done
**Autor**: [nombre]
**Fecha**: [YYYY-MM-DD]
**Areas afectadas**: [paginas, componentes, lib, content]

## Contexto

[Por que se necesita este cambio]

## Requisitos

### Funcionales (formato Given/When/Then)
- [ ] AC-1: Given <precondicion>, When <accion>, Then <resultado observable>
- [ ] AC-2: Given ..., When ..., Then ...

### No funcionales
- [ ] RNF-1: Performance: [criterio — ej. LCP < 2.5s en mobile 4G]
- [ ] RNF-2: Accesibilidad: [criterio — ej. WCAG 2.1 AA en flujos criticos]
- [ ] RNF-3: SEO: [criterio — ej. metadata + sitemap + robots.txt]

## Solucion propuesta

[Descripcion tecnica concisa]

### Estructura de archivos afectados
[Lista de paths nuevos/modificados]

### Datos/contenido afectado
[Solo si hay cambios en src/content/ o data files]

## Tasks atomicas

| # | Task | Archivo(s) | Estimacion | Estado |
|---|------|-----------|------------|--------|
| 1 | [task] | [path] | S/M/L | pending |
| 2 | [task] | [path] | S/M/L | pending |

## Tests requeridos

### TDD (escribir primero, formato Given/When/Then)
- AC-X: Given <precondicion>, When <accion>, Then <resultado>

### Unit (BDD-style en `it()`, AAA en cuerpo)
- [componente/lib]: [que testear con Given/When/Then en el `it()`]

### E2E (opcional, solo flujos completos del usuario)
- [flujo]: [navegar, accion, resultado verificado]

## Riesgos

| Riesgo | Probabilidad | Mitigacion |
|--------|-------------|-----------|

## Notas

[Decisiones, trade-offs, alternativas descartadas]
```

## Workflow detallado (mode: new)

### Paso 1: Entender el requerimiento

Preguntar al usuario (si no esta claro):

- Que problema resuelve
- Como interactua el visitante (lectura, descarga PDF, contacto)
- Criterios de aceptacion
- Constraints (performance, SEO, accesibilidad, i18n)

### Paso 2: Analizar impacto

Leer el codigo relevante:

- `src/pages/` — paginas Astro
- `src/components/` — componentes
- `src/layouts/` — layouts
- `src/content/` — content collections (si aplica)
- `src/lib/` — utilities
- `astro.config.*` — config Astro (si requiere integraciones nuevas)

### Paso 3: Generar spec

1. Determinar siguiente numero: buscar ultimo SPEC-NNN en `docs/specs/`
2. Crear archivo con template
3. Llenar con informacion recopilada
4. Descomponer en tasks atomicas (max 2-4 horas cada una)

### Paso 4: Validar con usuario

Presentar la spec y pedir feedback:

- Scope correcto?
- Tasks razonables?
- Falta algo?

### Paso 5: Aprobar e implementar

Marcar spec como `approved`, comenzar por tasks en orden.

## Reglas

- SIEMPRE crear spec en `docs/specs/` (crear directorio si no existe)
- SIEMPRE numerar specs secuencialmente (SPEC-001, SPEC-002, etc.)
- SIEMPRE descomponer en tasks atomicas (max 2-4 horas cada una)
- SIEMPRE incluir tests requeridos en la spec
- NUNCA implementar sin spec aprobada para features complejas
- NUNCA cambiar scope sin actualizar la spec
- Tasks deben ser ejecutables independientemente cuando sea posible
- Usar plan-format rule para diagramas inline (ASCII, no Mermaid)
- La spec es un artefacto **efimero**: cuando el plan esta implementado y su
  PR se mergea a `dev`, la carpeta/archivo de `docs/specs/` se ELIMINA (el
  ultimo commit del PR la borra con `git rm`). `docs/specs/` solo conserva
  planes pendientes o en curso — ver `.claude/rules/plan-format.md`, "Ciclo
  de vida de la carpeta del plan".
