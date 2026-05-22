# Fase 3 — Experiencias: reestructurar, contexto y logros

[← Fase 2](03-fase-db-migracion.md) · [Fase 4 →](05-fase-proyectos.md)

## Objetivo

Reestructurar las 4 experiencias "Independiente / Académico" con su
contexto real, y reorientar el contenido de las 9 experiencias por nicho
con logros y métricas. Cubre AC-4, AC-5, AC-7 (data).

## Estado actual

Las 9 experiencias en `packages/content/src/data/experiences/`. Las 4
con `company: "Independiente / Académico"`:

| slug | rol | periodo | contexto real (de los YAML) |
|------|-----|---------|------------------------------|
| `corpoelec` | Desarrollador Web | 2013 | Sistema de inventario, PHP/jQuery — Venezuela |
| `ipasme` | Desarrollador de Software | 2014 | Sistema de gestión de historias médicas, Java desktop — Venezuela |
| `iai` | Líder de Desarrollo | 2015 | Sistema de gestión de obras + arquitectura de red — Venezuela |
| `projects-degrees` | Líder/Arquitecto | 2015 | Reestructuró 2 proyectos de grado — Venezuela |

Las 9 ya tienen `responsibilities` y `achievements` (6-13 cada lista).

## Sub-tareas

### 3.1 — Reestructurar las 4 "Independiente / Académico"

Cada una pasa a tener un `company` con su institución real. Los nombres
exactos los confirma el usuario (ver "Datos a confirmar" abajo). Valores
propuestos a partir del contexto de los YAML:

| slug | `company` propuesto | `country` |
|------|---------------------|-----------|
| `corpoelec` | CORPOELEC (Corporación Eléctrica Nacional) | Venezuela |
| `ipasme` | IPASME (Instituto de Previsión y Asistencia Social) | Venezuela |
| `iai` | proyecto académico — institución a confirmar | Venezuela |
| `projects-degrees` | proyecto académico — institución a confirmar | Venezuela |

> `corpoelec` e `ipasme` fueron trabajos reales en instituciones
> venezolanas (la sigla es el nombre del organismo). `iai` y
> `projects-degrees` son proyectos académicos — el `company` puede ser
> el nombre de la universidad o "Proyecto académico" si no aplica una
> empresa. El usuario lo confirma.

### 3.2 — Campo `country` en las 9 experiencias

| Experiencia | `country` |
|-------------|-----------|
| `corpoelec`, `ipasme`, `iai`, `projects-degrees` | Venezuela |
| `cofasa` | Venezuela (Laboratorio Cofasa es venezolano — **confirmar**) |
| `dibal` | Perú |
| `goodmeal` | Chile (**confirmar** — puede ser otro) |
| `destacame-frontend`, `destacame-architect` | Chile |

> 4 países distintos esperados (AC-3): Venezuela, Perú, Chile, México.
> **Punto a confirmar**: la respuesta del usuario al cuestionario dijo
> "Chile y México son Destacame". Pero las 2 experiencias Destacame
> tienen un solo `country` cada una. Si Pablo trabajó para las dos
> sucursales (Chile y México) DESDE el mismo puesto, hay dos opciones:
> (a) `country` de las experiencias Destacame = "Chile" (sede) y México
> aparece como mercado en los proyectos `destacame-credit-mexico`;
> (b) agregar un campo `countries` (array) a Experience. **Decisión del
> plan**: opción (a) — `country` = país de la sede del empleo; México
> queda representado en el proyecto fintech de México. Así
> `stats.countries=4` se deriva de: Venezuela + Perú + Chile (de
> experiencias) + México (del proyecto). Si el usuario prefiere (b), es
> un cambio de schema menor.

### 3.3 — Reorientar el contenido por nicho

El contenido de cada experiencia debe enfatizar el ángulo del nicho
donde aparece (D-1). Como una experiencia se muestra en varios niches
con el MISMO contenido (no hay contenido por-nicho en el schema), la
reorientación se hace así:

- **`responsibilities` y `achievements`** se redactan cubriendo los
  ángulos de TODOS los niches de esa experiencia, ordenando primero el
  bullet más relevante al nicho de mayor `priority`.
- El **orden** de aparición de las experiencias ya lo controla
  `sortByPriority` por nicho (existente).
- El nicho irrelevante muestra la experiencia al final como tarjeta
  resumen (Fase 6, D-3) — no requiere contenido distinto.

> No se agrega contenido por-nicho al schema: sería duplicar 9×5 bloques
> de texto. El contenido es uno, redactado para que sirva a todos los
> niches de esa experiencia.

### 3.4 — Logros con métricas

Para cada experiencia, revisar/ampliar `achievements` con logros que
incluyan métricas (D-2). Reglas:

- Las cifras son **plausibles y conservadoras**, coherentes con el rol,
  la seniority y la época.
- Cada experiencia con cifras inventadas lleva `metricsEstimated: true`.
- Cada cifra se registra en el anexo `11-metricas-estimadas.md` con su
  justificación, para que el usuario la valide.
- Español neutro; inglés con tono US (D-13, D-14).

Ejemplo de logro reorientado (Destacame, ángulo fintech/architect):

```yaml
achievements:
  es:
    - >-
      Diseñé la arquitectura de onboarding que permite integrar nuevas
      instituciones financieras (Scotiabank, Santander, Santander
      Consumer) como configuración, no como desarrollo nuevo,
      deprecando el sistema anterior.
    - >-
      Implementé un sistema de iteración basado en datos de
      comportamiento de usuario, [MÉTRICA A CONFIRMAR].
```

## Datos a confirmar (no bloquean la entrega del plan)

El plan se entrega para revisión; estos puntos los completa el usuario
antes de ejecutar la Fase 3:

1. Nombre real de la institución de `iai` y `projects-degrees`.
2. País de `cofasa` (Laboratorio Cofasa) y `goodmeal`.
3. ¿Las experiencias Destacame llevan `country: Chile` (opción a) o se
   agrega un array `countries` (opción b)?
4. Revisar las cifras del anexo `11-metricas-estimadas.md` una vez
   generado.

## Verificación de la fase

```bash
pnpm --filter @portfolio/content exec vitest run
pnpm --filter @portfolio/content run typecheck
```

El test de paridad de slugs valida que cada YAML matchea su filename.

## Definition of Done de la fase

- [ ] Las 4 experiencias antes "Independiente / Académico" tienen
      `company` con su institución real.
- [ ] Las 9 experiencias tienen `country`.
- [ ] `achievements` reorientados por nicho, con métricas donde aplique.
- [ ] Las experiencias con cifras inventadas tienen
      `metricsEstimated: true`.
- [ ] Cada cifra registrada en `11-metricas-estimadas.md`.
- [ ] `vitest` content + typecheck verdes.

[← Fase 2](03-fase-db-migracion.md) · [Fase 4 →](05-fase-proyectos.md)
