# 03 — Strict Mode TypeScript 6

[< 02-features](02-features.md) | [Siguiente: 04-tsconfig >](04-tsconfig.md)

> En TS 6, `"strict": true` es implicito. Esta seccion documenta las flags
> que `strict` cubre + las extras recomendadas para el portfolio.

## Flags bajo `"strict": true`

```jsonc
{
  "compilerOptions": {
    "strict": true,
    // Cubre automaticamente:
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "useUnknownInCatchVariables": true
  }
}
```

### Que enforza cada una

| Flag | Que detecta |
|------|-------------|
| `noImplicitAny` | Parametros / vars sin tipo explicito |
| `strictNullChecks` | `null` / `undefined` deben verificarse antes de usar |
| `strictFunctionTypes` | Parametros contravariantes (callbacks) |
| `strictBindCallApply` | `call` / `bind` / `apply` type-safe |
| `strictPropertyInitialization` | Properties sin inicializar (`!` o constructor) |
| `noImplicitThis` | `this` sin type context |
| `alwaysStrict` | Emite `"use strict"` en cada archivo |
| `useUnknownInCatchVariables` | `catch (e: unknown)` por default |

## Flags adicionales (recomendadas para portfolio)

```jsonc
{
  "compilerOptions": {
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noImplicitReturns": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "verbatimModuleSyntax": true,
    "noFallthroughSwitchClause": true
  }
}
```

### Trade-offs

| Flag | Benefit | Cost |
|------|---------|------|
| `noUncheckedIndexedAccess` | Previene `undefined` en arrays/dicts | Requiere checks en bucles |
| `noImplicitOverride` | Detecta typos en overrides de subclases | Verboso (`override` keyword obligatorio) |
| `noImplicitReturns` | Catch return path olvidados | Forces `return undefined` explicito |
| `noUnusedLocals` | Limpieza de variables muertas | Falla con vars `// TODO` |
| `noUnusedParameters` | Limpieza de params sin uso | Falla en callbacks de libs externas |
| `verbatimModuleSyntax` | Obliga `import type` | Requiere diligencia |
| `noFallthroughSwitchClause` | Catch missing `break` | Forces `break` o comment explicito |

## Flags MUY estrictas (opcionales, NO recomendadas para portfolio)

```jsonc
{
  // "exactOptionalPropertyTypes": true,  // Distingue field?:X vs field:X|undefined — rompe libs
  // "noPropertyAccessFromIndexSignature": true  // MUY restrictivo
}
```

Decision: el portfolio NO las activa. La complejidad excede el beneficio.

## `unknown` vs `any` (politica del proyecto)

`any` esta **PROHIBIDO** en codigo de aplicacion (rule
`.claude/rules/typescript.md`).

```typescript
// ❌ PROHIBIDO
function process(data: any) { /* ... */ }

// ✅ Correcto: unknown + narrow
function process(data: unknown) {
  if (typeof data === 'string') {
    return data.toUpperCase()
  }
  if (data && typeof data === 'object' && 'name' in data) {
    return String(data.name)
  }
  throw new TypeError('Unsupported input')
}

// ✅ Correcto: tipo especifico
function processUser(user: User) { /* ... */ }

// ✅ Correcto: generic con constraint
function first<T>(items: T[]): T | undefined { return items[0] }
```

## Manejo de catch

`useUnknownInCatchVariables` obliga:

```typescript
try {
  riskyOperation()
} catch (e: unknown) {
  if (e instanceof Error) {
    console.error(e.message)
  } else {
    console.error('Unknown error', e)
  }
}
```

## Type assertions (cuando necesario)

```typescript
// ❌ EVITAR `as` casual
const user = data as User  // bypassa checker

// ✅ Preferir `satisfies` cuando aplica
const config = { theme: 'dark' } satisfies Config

// ✅ Type guards
function isUser(x: unknown): x is User {
  return !!x && typeof x === 'object' && 'id' in x && 'email' in x
}

// ✅ Schema validation (Zod)
const user = userSchema.parse(data)  // tipo derivado + runtime check

// ✅ `as` solo cuando hay invariante externa documentada
// JSON parsing donde el shape esta garantizado por API contract
const config = JSON.parse(text) as unknown
// luego validar con Zod o type guard
```

## Anti-patterns del strict mode

| Anti-pattern | Por que | Correccion |
|--------------|---------|------------|
| `any` "rapido para iterar" | Permanente, contamina toda la cadena | `unknown` + Zod |
| `as Foo` para silenciar error | Oculta bug real | Type guard o `satisfies` |
| `// @ts-ignore` permanente | Mascarea bugs | Fix root cause o `// @ts-expect-error` con razon |
| `.toString()` sin null check | Crashea con `strictNullChecks` | Optional chaining `x?.toString()` |
| Property sin init en class | `strictPropertyInitialization` falla | `prop!: Type` o init en constructor |
| Catch sin tipo | TS 6 forza `unknown` | `catch (e: unknown)` + narrow |
| Mutar parametros de funcion | Implica side effects ocultos | Aceptar readonly, retornar nuevo objeto |
