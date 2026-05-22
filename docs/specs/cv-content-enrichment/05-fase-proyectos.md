# Fase 4 — Proyectos: case studies, métricas y proyecto cv

[← Fase 3](04-fase-experiencias.md) · [Fase 5 →](06-fase-summary-nicho.md)

## Objetivo

Completar `caseStudyDetailed` + `metrics` en los 6 proyectos y agregar el
proyecto `cv`. Cubre AC-6, AC-7 (data), AC-8.

## Estado actual

| slug | `caseStudyDetailed` | `metrics` |
|------|---------------------|-----------|
| `cv-builder` | sí | sí |
| `destacame-debt-chile` | sí | sí |
| `destacame-credit-mexico` | sí | sí |
| `faststruct` | sí | sí |
| `mvp-template-full-stack` | **NO** | sí |
| `portfolio-astro` | **NO** | **NO** |

Faltan: `caseStudyDetailed` en 2 proyectos, `metrics` en 1, y el
proyecto `cv` no existe.

## Sub-tareas

### 4.1 — `caseStudyDetailed` en mvp-template-full-stack y portfolio-astro

Agregar el bloque `caseStudyDetailed` (problem/process/result, bilingüe)
a los 2 proyectos que no lo tienen. El contenido se redacta a partir del
`summary` y `description` ya existentes — es contar el caso, no inventar
el proyecto.

`portfolio-astro` (este mismo repo) — esquema del case study:
- **problem**: tener un CV/portfolio que funcione para varios
  posicionamientos (fintech, architect, leader, vibe) sin mantener 5
  sitios a mano.
- **process**: monorepo Astro 6 con 6 apps que comparten packages
  (`content`, `ui`, `app-shared`); la data del CV es un singleton
  filtrado por nicho.
- **result**: 6 sitios estáticos desde una sola fuente de datos;
  [MÉTRICA A CONFIRMAR — ej. tiempo de build, peso de página].

`mvp-template-full-stack` — esquema análogo a partir de su `description`.

### 4.2 — `metrics` en portfolio-astro

Agregar el objeto `metrics` (claves variables, valores string). Para
`portfolio-astro`, métricas verificables del propio repo:
- `apps`: "6 sitios Astro desde un monorepo"
- `stack`: "Astro 6 + TypeScript 6 + Biome v2"
- otras cifras (LCP, peso) → estimadas, marcar `metricsEstimated`.

### 4.3 — Revisar métricas de los 6 proyectos

Los proyectos que ya tienen `metrics` se revisan: si alguna cifra es
inventada, marcar el proyecto con `metricsEstimated: true` y registrarla
en `11-metricas-estimadas.md`. Si la métrica es un hecho verificable
(ej. "publicado en VS Code Marketplace"), no se marca.

### 4.4 — Proyecto `cv` nuevo

Crear `packages/content/src/data/projects/cv.yaml`. Datos conocidos:

```yaml
slug: cv
name: CV  # o el nombre que prefiera el usuario
summary:
  es: >-
    CV descargable de código abierto: cualquiera puede clonarlo y
    generar su propio currículum.
  en: >-
    Open-source downloadable CV: anyone can clone it and generate
    their own résumé.
repo: https://github.com/bypabloc/cv
status: active
niches:
  - vibe
  - generic
  # confirmar con el usuario si aplica a architect
priority:
  vibe: 60
  generic: 55
stack:
  # confirmar el stack real del repo
  - TypeScript
projectType: library  # o el que corresponda — confirmar
caseStudyDetailed:
  problem: { es: "...", en: "..." }
  process: { es: "...", en: "..." }
  result: { es: "...", en: "..." }
metrics:
  # estimadas -> metricsEstimated: true
metricsEstimated: true
```

> **Datos a confirmar del proyecto `cv`**: nombre exacto, stack real del
> repo, `projectType`, niches donde aplica, si tiene `url` (demo) además
> del `repo`. El plan se entrega; el usuario completa estos campos o
> autoriza que se infieran del README del repo.

## Datos a confirmar (no bloquean la entrega del plan)

1. Case study y métricas de `portfolio-astro` y `mvp-template-full-stack`.
2. Nombre, stack, `projectType`, niches y `url` del proyecto `cv`.
3. Revisar el anexo `11-metricas-estimadas.md` (sección proyectos).

## Verificación de la fase

```bash
pnpm --filter @portfolio/content exec vitest run
pnpm --filter @portfolio/content run typecheck
```

El test de paridad valida que `cv.yaml` tiene `slug: cv`.

## Definition of Done de la fase

- [ ] Los 6 proyectos existentes tienen `caseStudyDetailed` y `metrics`
      no vacíos.
- [ ] El proyecto `cv` existe con `repo` apuntando a
      `github.com/bypabloc/cv`.
- [ ] Los proyectos con cifras inventadas tienen `metricsEstimated: true`.
- [ ] Cada cifra registrada en `11-metricas-estimadas.md`.
- [ ] `vitest` content + typecheck verdes.

[← Fase 3](04-fase-experiencias.md) · [Fase 5 →](06-fase-summary-nicho.md)
