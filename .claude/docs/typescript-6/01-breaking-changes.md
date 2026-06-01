# 01 — Breaking Changes TypeScript 5.x -> 6.0

[< README](README.md) | [Siguiente: 02-features >](02-features.md)

> Cambios que rompen codigo TS 5.x al actualizar a 6.0. El codemod
> `@andrewbranch/ts5to6` resuelve los mecanicos; el resto requiere fix
> manual (mayoria son `strict null checks`).

## 1. Strict mode implicito por default

**TS 5.x**: `"strict": false` era el default sloppy.
**TS 6.0**: `"strict": true` es implicito si no se setea.

Flags activados:

- `noImplicitAny`
- `strictNullChecks`
- `strictFunctionTypes`
- `strictBindCallApply`
- `strictPropertyInitialization`
- `noImplicitThis`
- `alwaysStrict`
- `useUnknownInCatchVariables`

**Mitigacion temporal**: setear `"strict": false` (deprecado en TS 7,
solo para migration window).

## 2. Module resolution defaults cambiados

| Setting | TS 5.x default | TS 6.0 default |
|---------|----------------|----------------|
| `module` | `commonjs` | `ESNext` |
| `moduleResolution` | `node` | `bundler` |
| `target` | `ES5` (luego `ES2025`) | `ES2025` |

**Impact**:

- Apps con bundlers (Astro 6, Next 16, Vite) — auto-detecta correcto.
- Node CLI scripts — considerar `"module": "NodeNext"` +
  `"moduleResolution": "nodenext"`.

## 3. `types` array OBLIGATORIO

**TS 5.x**: auto-descubria `@types/*` instalados.
**TS 6.0**: sin `"types": [...]` NO se carga ningun tipo global.

**Beneficio**: cold builds 20-50% mas rapidos (skip scan innecesario).
**Costo**: olvidar listar = perder intellisense.

```jsonc
{
  "compilerOptions": {
    "types": ["node", "vitest/globals", "astro/astro-jsx"]
  }
}
```

## 4. `baseUrl` REMOVIDO

**TS 5.x**: `baseUrl` + `paths` con resolucion implicita.
**TS 6.0**: solo `paths` con rutas relativas.

```jsonc
// TS 5.x (ERROR en TS 6)
{
  "baseUrl": ".",
  "paths": { "@/*": ["src/*"] }
}

// TS 6.0 (OK)
{
  "paths": { "@/*": ["./src/*"] }
}
```

Codemod `ts5to6` aplica este fix automaticamente.

## 5. Namespace syntax — `module Foo { }` ERROR

```typescript
// TS 5.x OK
module Foo { export const bar = 42 }

// TS 6.0 ERROR
// Conflicto con propuesta ECMAScript de module blocks
```

Reemplazo: `namespace Foo { export const bar = 42 }`.

## 6. Target minimo ES2015 (ES5 deprecated)

```jsonc
// TS 6.0 ERROR
{ "target": "ES5" }

// OK
{ "target": "ES2015" }  // o superior, recomendado ES2023
```

## 7. `esModuleInterop` y `allowSyntheticDefaultImports` removidas

En TS 6 ambas son SIEMPRE `true` (no se pueden setear `false`).

```jsonc
// TS 6.0 SYNTAX ERROR
{ "esModuleInterop": false }
{ "allowSyntheticDefaultImports": false }
```

## 8. Implicit default exports removidas

TS 6 SIEMPRE exige `export default` explicito.

## Codemod `ts5to6` (resuelve mecanicos)

```bash
# Instalacion + uso (Andrew Branch, TS team member)
pnpm dlx @andrewbranch/ts5to6 .

# Que hace:
# - Elimina baseUrl, reescribe paths a relativos
# - Setea rootDir explicito (preserva structure)
# - Sigue extends chains en node_modules
# - Patch tsconfig recursivo en monorepo
```

## Migracion paso a paso

```bash
# 1. Upgrade workspace
pnpm add -D -w typescript@^6.0.0

# 2. Codemod
pnpm dlx @andrewbranch/ts5to6 .

# 3. Typecheck para ver errores nuevos
pnpm exec tsc --noEmit
pnpm exec astro check

# 4. Listar @types en tsconfig.types

# 5. Arreglar strict errors (mayoria null checks)
# Estrategia: fix uno a uno; opcional temporal "strict": false para iterar

# 6. Verificar builds
pnpm run build

# 7. Tests
pnpm exec vitest run --coverage

# 8. Commit
git commit -m "upgrade(typescript): migrate to TS 6.0 GA"
```

## Deprecation escape hatch (temporal)

```jsonc
{
  "compilerOptions": {
    "ignoreDeprecations": "6.0"
    // Silencia warnings deprecated.
    // NO funciona en TS 7.0 — arreglar antes.
  }
}
```

## Anti-patterns

| Anti-pattern | Por que | Correccion |
|--------------|---------|------------|
| Migrar sin codemod | Mecanicos toman horas manual | `pnpm dlx @andrewbranch/ts5to6 .` |
| Setear `"strict": false` permanente | Pierde todos los safety nets | Fix errores iterativo |
| Dejar `baseUrl` | ERROR en TS 6 | Solo paths relativos |
| Olvidar `@types` en `"types"` | Intellisense roto silenciosamente | Listar todos los requeridos |
| `ignoreDeprecations: "6.0"` como solucion final | Falla en TS 7 | Fix deprecations ahora |
