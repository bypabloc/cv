---
name: tdd-workflow
description: >
  TDD obligatorio (Red-Green-Refactor) para todo desarrollo en este portfolio
  Astro 6. Tests primero, implementacion despues. Unit tests con Vitest.
  ALWAYS invoke before writing implementation code for new feature/bug.
  Triggers: "TDD", "test driven", "test primero", "rojo verde refactor",
  "red green refactor", "nueva feature", "implementar feature", "fix bug",
  "vibe coding", "tests primero", "RGR cycle", "ciclo TDD".
user-invocable: true
argument-hint: "presenta el flujo TDD (sin argumentos)"
metadata:
  version: "2.0"
---

# TDD Workflow - Portfolio Astro

> Test-Driven Development obligatorio. Tests primero, implementacion despues.
> El vibe coding es eficiente cuando hay red de seguridad inmediata.

## Regla principal (NEGOCIABLE = NO)

**NUNCA escribir codigo de implementacion sin un test que falle primero.**

El ciclo TDD es Red → Green → Refactor:

```text
RED      → Escribir test que falle (define el comportamiento esperado)
  |
  v
GREEN    → Codigo MINIMO para pasar el test (no optimizar aun)
  |
  v
REFACTOR → Mejorar codigo manteniendo tests verdes
  |
  +-------> volver a RED para siguiente comportamiento
```

## Cuando aplicar TDD (OBLIGATORIO)

| Caso | TDD | Razon |
|------|-----|-------|
| Funcion utility nueva (formatters, validators) | Si | Comportamiento facil de probar antes de escribir |
| Bug fix con causa reproducible | Si | Test reproduce el bug, luego se arregla |
| Refactor con cambio de comportamiento | Si | Tests garantizan no romper nada |
| Refactor puro (sin cambio de comportamiento) | No | Tests existentes ya cubren |
| Componente Astro estatico (markup puro) | No | El test serian snapshots fragiles |
| Cambio de configuracion | No | No hay logica que probar |
| Documentacion / cambios cosmeticos (CSS, copy) | No | Cubierto por E2E si es flujo critico |

## Flujo obligatorio para nuevas features

### Paso 1: Escribir TDD plan (formato estricto)

Antes de tocar codigo, listar los flujos a probar con formato:

```text
Flow: [accion del usuario o input] -> Expected: [resultado esperado]
```

Ejemplo (formateador de fecha del CV):

```text
Flow: formatear "2024-01" con locale "es" -> Expected: "enero 2024"
Flow: formatear "2024-12" con locale "en" -> Expected: "December 2024"
Flow: formatear "" -> Expected: throws Error("date is required")
Flow: formatear "invalid" -> Expected: throws Error("invalid date format")
```

Ejemplo (validador de email del form de contacto):

```text
Flow: validar "user@example.com" -> Expected: { valid: true }
Flow: validar "user@" -> Expected: { valid: false, error: "INVALID_FORMAT" }
Flow: validar "" -> Expected: { valid: false, error: "REQUIRED" }
```

### Paso 2: RED - Escribir tests (que fallen)

Crear archivos de test SEGUN el path mirroring:

- `src/lib/format-date.ts` -> `tests/unit/lib/format-date.test.ts`
- `src/lib/validators/email.ts` -> `tests/unit/lib/validators/email.test.ts`
- `src/components/Hero.astro` -> `tests/unit/components/Hero.test.ts` (parsea como string)

Ejecutar tests y confirmar que fallan:

```bash
pnpm exec vitest run --reporter=verbose
```

**Output esperado**: tests fallan con mensaje claro (no por error de import, no por sintaxis — por logica ausente).

### Paso 3: GREEN - Implementacion minima

Escribir el MENOR codigo posible que haga pasar el test. NO optimizar aun.

Reglas:

- Si copiar y pegar 3 valores hace pasar el test, esta bien
- NO agregar funcionalidad que ningun test exige
- Si el test pide una validacion, agregar SOLO esa validacion
- Verificar tests verdes antes de continuar

### Paso 4: REFACTOR - Mejorar manteniendo verde

Solo despues de tener tests verdes, refactorizar:

- Extraer constantes/funciones repetidas
- Aplicar patrones del proyecto
- Eliminar duplicacion
- Mejorar nombres

Despues de cada cambio: re-ejecutar tests. Si pasan → continuar. Si fallan → revertir o arreglar.

## BDD-style obligatorio en `it()` (Vitest)

TDD AAA en el cuerpo + **`it()` en formato Given/When/Then**:

```typescript
import { describe, expect, it } from 'vitest'
import { formatDate } from '@/lib/format-date'

describe('formatDate', () => {
  it('Given a YYYY-MM date and locale "es" When format Then returns "<month> <year>" in Spanish', () => {
    // Arrange
    const input = '2024-01'

    // Act
    const result = formatDate(input, 'es')

    // Assert
    expect(result).toBe('enero 2024')
  })
})
```

Reglas:

- `it()` empieza con `Given ... When ... Then ...`
- Asserts EXACTOS: `expect(x).toBe(42)`, NUNCA `expect(x).toBeGreaterThan(0)`
- Patron AAA con comentarios `// Arrange`, `// Act`, `// Assert` cuando el cuerpo crece

## Diferencia unit vs integration vs E2E

```text
UNIT (mockeas todo lo externo a la pieza, Vitest + happy-dom)
  |
  +-> Sirve para TDD rapido del comportamiento aislado
  +-> Milisegundos, no requiere browser
  +-> Ejemplo: validar formato de email (funcion pura)

E2E (Playwright contra build estatico o dev server)
  |
  +-> Sirve para validar flujos completos del usuario
  +-> Segundos, requiere browser real
  +-> Ejemplo: navegar a /cv, hacer click en "Descargar PDF", verificar download
```

Regla TDD: empezar con **unit** (rapido feedback). E2E solo para flujos del usuario que cruzan paginas.

## Antipatrones (PROHIBIDOS)

- ESCRIBIR CODIGO Y DESPUES TESTS — destruye el proposito de TDD
- Escribir tests que pasan en la primera ejecucion sin codigo nuevo (no fallaron en RED)
- Tests con multiples assertions que validan comportamientos distintos
- Saltarse REFACTOR (deja deuda tecnica)
- "Voy a escribir el test despues" — NO. Tests primero o no son TDD.
- Asserts vagos: `toBeGreaterThan(0)`, `toBeDefined()`, `toBeTruthy()`

## Vibe coding eficiente con TDD

TDD acelera el "vibe coding" porque:

1. **Tests son la spec ejecutable**: define comportamiento sin ambiguedad
2. **Feedback inmediato**: sabes en segundos si tu cambio rompe algo
3. **Refactor sin miedo**: puedes reescribir sabiendo que la red atrapa errores
4. **Menos debugging**: el bug se detecta cuando es minimo, no acumulado
5. **Documentacion gratis**: los tests muestran como usar el codigo

## Comandos clave

```bash
pnpm exec vitest run                 # corre todos los tests una vez
pnpm exec vitest                     # modo watch (TDD iterativo)
pnpm exec vitest run --reporter=verbose  # detalle por test
pnpm exec vitest run --coverage      # con coverage
pnpm exec vitest run --changed       # solo archivos cambiados vs HEAD
```

## Skills relacionados

- `/spec-workflow new` — desglose de feature en tasks atomicas con TDD plan integrado
- `/fix-hooks` — reparar git hooks si fallan tras un cambio

## Quality gates relacionados

Pre-commit y pre-push (si estan configurados) corren tests automaticamente.
Si no haces TDD:

- Cobertura per-file puede caer < 80%
- Asserts vagos detectables manualmente en review
