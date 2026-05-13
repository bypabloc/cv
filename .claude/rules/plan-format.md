---
description: "Template obligatorio para planes de implementacion (best practices 2026): scope-based ceremony, AC en BDD/EARS, TDD WHEN/THEN, diagramas ASCII, tests por modulo, archivos con verificacion, definition of done. Aplica en plan mode o cuando el usuario dice disenar, planificar, arquitectura, plan, roadmap, desglosar."
---

# Formato de Plan de Implementacion

> Template obligatorio cuando Claude esta en plan mode o el usuario solicita disenar/planificar/arquitecturar algo. Alineado con best practices 2025-2026 (Anthropic Explore-Plan-Implement-Commit, EARS notation, BDD acceptance criteria).

## Activacion

Aplicar cuando:

- Claude esta en plan mode (Shift+Tab o EnterPlanMode tool)
- El usuario dice: "disenar", "planificar", "arquitectura", "plan", "roadmap", "desglosar"
- El usuario pide evaluar impacto de un cambio
- El usuario pide approach o strategy para implementar algo

## Workflow: Explore → Plan → Implement → Commit

Anthropic recomienda 4 fases para cambios no triviales:

1. **Explore** (plan mode): leer archivos relevantes. Sin escribir codigo.
2. **Plan** (plan mode): redactar siguiendo este template. Editable con `Ctrl+G`.
3. **Implement** (modo normal): ejecutar el plan, correr tests, verificar.
4. **Commit**: commit descriptivo + PR.

Para features grandes o requisitos ambiguos, considerar fase de **Interview** previa con `AskUserQuestion` cubriendo edge cases, tradeoffs y constraints.

## Escala del plan (scope-based ceremony)

| Tamano | Archivos | Formato |
|--------|----------|---------|
| **Micro** | 1-2 archivos, hotfix | Plan corto: 3 lineas (objetivo + archivo + done). Saltar template. |
| **Small** | 3-5 archivos | Template completo, secciones condicionales colapsadas |
| **Medium** | 6-10 archivos | Template completo, todas las secciones aplicables |
| **Large** | 11+ archivos | Template completo + Seccion 8 (ver `.claude/docs/plan-format-large/README.md`) |

Si puedes describir el diff en una oracion, NO uses el template. Anti-pattern: forzar 8 secciones para un cambio de 5 lineas.

## Secciones obligatorias (en orden)

Para Small/Medium/Large, incluir en este orden. Secciones 4, 5, 6 y 8 son condicionales.

---

### 1. Contexto / Problema

- Descripcion del problema o necesidad actual
- Por que se necesita el cambio (bug, feature request, deuda tecnica)
- Si hubo exploracion, resumir hallazgos clave (1-2 bullets)

Estructura: 1-3 parrafos concisos + sub-seccion opcional `### Hallazgos de exploracion`.

---

### 2. Solucion Propuesta

- UNA sola solucion recomendada (no alternativas — converger antes del plan)
- Decisiones clave con razonamiento
- Constraints considerados (performance, compatibilidad, scope)

Estructura: descripcion del approach + sub-seccion `### Decisiones clave` con `Decision N: [que] — [por que]`.

Las alternativas se discuten en Interview/Exploracion, no aqui. El plan converge.

---

### 3. Criterios de Aceptacion (AC)

Definir el "que debe pasar" en formato BDD (`Given/When/Then`) o EARS (`WHEN/THEN`, `WHILE/WHEN/THEN`). Numerados AC-1, AC-2... — fuente de verdad referenciada por tests y tareas.

Ejemplo:

- **AC-1**: Given un usuario no autenticado, When accede a `/dashboard`, Then es redirigido a `/login?next=/dashboard`
- **AC-2**: When se crea un registro sin nombre, Then la API retorna HTTP 400 con codigo `NAME_REQUIRED`

Reglas:

- Numeracion estable (AC-1, AC-2, ...)
- Elegir BDD o EARS y mantenerlo en todo el plan
- Cada AC debe ser convertible a un test ejecutable (observable y verificable)
- Cubrir happy path + edge cases + error cases criticos
- 3-10 AC por feature. Mas indica scope grande → descomponer

---

### 4. Diagrama de Flujo (Antes y Despues) — CONDICIONAL

Incluir solo si el cambio modifica flujo de control, secuencia de pasos o decisiones.

Si no aplica: `## 4. Diagrama de Flujo` + `N/A — el cambio no altera flujos de control`.

Si aplica: dos sub-secciones `### Antes` y `### Despues`, ambas con diagrama ASCII inline mostrando solo las partes cambiadas.

Reglas:

- Solo ASCII inline, NO Mermaid (portabilidad en plan mode)
- Diagramas de decision: `{Condicion?}` con ramas `-->` etiquetadas
- Maximo 15 nodos por diagrama
- Si justifica `.mmd` permanente para `docs/diagrams/`, anotarlo en seccion 7

---

### 5. Diagrama ER — CONDICIONAL

Incluir solo si hay cambios en modelos/tablas/campos.

Si no aplica: `## 5. Diagrama ER` + `N/A — no hay cambios en base de datos`.

Si aplica: ASCII inline marcando `(*)` campos nuevos, `(NUEVO)` tablas nuevas. Solo modelos/campos que cambian.

Reglas:

- Tipos validos: `uuid`, `string`, `int`, `float`, `boolean`, `datetime`, `jsonb`, `text`
- En este portfolio no hay DB. Esta seccion aplica solo si se modelan
  entidades en content collections (`src/content/config.ts` con schemas Zod)
  o tipos TypeScript que representen entidades.
- Tipos validos: `string`, `int`, `float`, `boolean`, `datetime`, `array`, `object`
- Relaciones (entre content collections): `──<` (1-to-many), `──` (1-to-1)
- Si justifica `.mmd` permanente, anotarlo en seccion 7

---

### 6. Tests Requeridos — CONDICIONAL por tipo

Incluir solo subsecciones aplicables. Cada test referencia al menos un AC entre corchetes.

#### 6.A. TDD Flows (logica nueva en `src/lib/`)

Escribir antes de implementar, formato `WHEN <accion> THEN <resultado> [AC-X]`.

Ejemplo: `WHEN formatear "2024-01" con locale "es" THEN retorna "enero 2024" [AC-1]`.

#### 6.B. Unit Tests (Vitest)

- Path mirroring: `src/<X>` -> `tests/unit/<X>.test.ts` (componentes `.astro` mapean a `.test.ts`)
- Vitest + happy-dom
- Coverage v8 >= 80% per-file en archivos modificados
- Mockear: fetch externos (si hay), date/time si se manipula
- NO mockear: utilities propias dentro del scope del test
- Patron AAA + BDD-style en `it()` (`Given/When/Then`)

#### 6.C. Typecheck

- `pnpm exec tsc --noEmit` (TypeScript 6 strict)
- `pnpm exec astro check` para componentes `.astro` modificados
- Falla en CI/hooks

#### 6.D. E2E Tests (Playwright, CONDICIONAL — solo flujos completos del usuario)

- Suite en `tests/e2e/`
- Formato `WHEN paso 1 THEN paso 2 THEN resultado [AC-X]`
- NUNCA incluir si los cambios son solo internos (refactor utilidades/types, ajustes de copy/estilos sin nuevos flujos)
- Ejecutar localmente antes de merge (opt-in en CI por costo)

---

### 7. Archivos Afectados

Listar paths relativos desde root, agrupados por operacion (`### Crear`, `### Modificar`, `### Eliminar`). Cada archivo: descripcion + comando de **verificacion** explicito (convierte la lista en checklist ejecutable).

Ejemplo compacto:

```markdown
### Crear
- `src/lib/format-date.ts` — formatter de fecha YYYY-MM con locale
  - Verificar: `pnpm exec vitest run tests/unit/lib/format-date.test.ts`

### Modificar
- `src/components/ExperienceCard.astro` — agregar prop `endDate?: string`
  - Verificar: `pnpm exec astro check` sin errores
  - Verificar: `pnpm run build` exitoso
```

Reglas:

- Paths relativos desde root
- Descripcion despues de ` — ` (espacio + em dash + espacio)
- **Verificacion explicita** por archivo (comando o criterio observable)
- Omitir secciones vacias
- Incluir tests nuevos, archivos `.mmd` para diagramas permanentes

---

### 8. Descomposicion para Paralelizacion — CONDICIONAL: solo Large

Aplicar solo si el plan es Large (11+ archivos) o se planea implementacion con multiples agentes en git worktrees.

**Documento detallado**: `.claude/docs/plan-format-large/README.md` (plantilla, reglas de paralelizabilidad, granularidad, anti-patrones).

Resumen: cada tarea debe pasar 3 checks (File Exclusivity, Interface Stability, Bounded Scope) y tener 6 campos (**Archivos**, **AC referenciados**, **Depende de**, **Paralelizable con**, **Verify**, **Done**). Limite practico: 5-7 agentes concurrentes.

---

### 9. Validacion y Definition of Done

Dos checklists:

**Pre-implementacion**:

- [ ] Todos los AC numerados y referenciados por tests
- [ ] Tests TDD escritos y fallando (Red phase)
- [ ] Fixtures necesarios existen o estan planificados
- [ ] Dependencias instaladas (`pnpm install` sin warnings)
- [ ] Dev server arranca limpio (`pnpm run dev`)
- [ ] No hay breaking changes en APIs publicas (o estan documentados)

**Definition of Done**:

- [ ] Todos los AC tienen al menos un test que los cubre y pasa
- [ ] Coverage per-file >= 80% en archivos modificados/creados
- [ ] Typecheck pasa (`pnpm exec tsc --noEmit` + `pnpm exec astro check`)
- [ ] Conformance pasa (`pnpm exec biome check .`)
- [ ] Build estatico exitoso (`pnpm run build`)
- [ ] Preview verificado visualmente si hay cambios de UI (`pnpm run preview`)
- [ ] Pre-commit hooks pasan en local (`SKIP_STEPS=""`)
- [ ] Documentacion actualizada si cambian APIs publicas o convenciones

---

## Reglas generales

- Idioma espanol; ingles para terminos tecnicos
- Sin emojis
- Conciso: cada seccion lo mas corta posible sin perder informacion
- Seccion condicional que no aplica → escribir `N/A — [razon]`
- NO Mermaid en el plan, solo ASCII inline (portabilidad)
- Si un diagrama justifica `.mmd` permanente, anotarlo en seccion 7
- AC numerados son la fuente de verdad: tests y tareas los referencian
- Para Large/Huge: considerar implementacion con subagentes paralelos en git worktrees

## Anti-patrones

- Forzar template completo en cambios Micro
- Presentar multiples alternativas en seccion 2 (converger antes)
- AC vagos sin formato BDD/EARS
- Tests sin referencia a AC (rompe trazabilidad)
- Lista de archivos sin verificacion explicita (no es ejecutable)
- Mermaid inline en plan (usar ASCII + `.mmd` separado)
- Definition of Done implicita en lugar de criterios observables
- Descomposicion para paralelizacion sin verificar file exclusivity (race conditions)
