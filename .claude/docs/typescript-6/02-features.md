# 02 — Features Nuevos TypeScript 6

[< 01-breaking-changes](01-breaking-changes.md) | [Siguiente: 03-strict-mode >](03-strict-mode.md)

> Features estables y recomendados en TS 6.0. Algunos llegaron en
> versiones 5.x pero se vuelven idiomaticos / optimizados en 6.0.

## 1. Native Node.js TypeScript support

Node.js 22.18+ / 23.6+ ejecutan `.ts` directo sin compilar:

```bash
node --no-warnings=ExperimentalWarning script.ts
```

Mecanismo: **type stripping** — elimina tipos en el parser, preserva
sintaxis runtime.

Impact en portfolio: futuros scripts Node podrian correr `.ts` directo
sin `tsx`/`ts-node`/`vite-node`.

## 2. Incremental compilation

```jsonc
{
  "compilerOptions": {
    "incremental": true,
    "tsBuildInfoFile": ".tsbuildinfo"
  }
}
```

Mejora: 40-60% rebuilds mas rapidos en proyectos grandes. El
`.tsbuildinfo` cachea tipo y dependency graph.

## 3. Project references mejoradas

Para monorepos pnpm (5 packages compartidos + 6 apps + dashboard):

```jsonc
// tsconfig.json (root)
{
  "files": [],
  "references": [
    { "path": "packages/content" },
    { "path": "packages/ui" },
    { "path": "packages/seo" },
    { "path": "packages/cv-pdf" },
    { "path": "packages/app-shared" }
  ]
}
```

Build paralelo:

```bash
pnpm exec tsc -b              # paralelo automatico
pnpm exec tsc -b --watch      # watch mode
pnpm exec tsc -b --clean      # limpiar artifacts
```

Ejemplo real: monorepo 22-package, build time **11min -> 3min**.

## 4. `module: "Preserve"` (nuevo)

Preserva imports exactos como fueron escritos (no los reescribe).

```jsonc
{
  "compilerOptions": {
    "module": "Preserve"
    // Util para libraries que mezclan ESM + CommonJS
  }
}
```

## 5. `satisfies` operator (estable)

Valida contra interface sin perder literal inference:

```typescript
type Config = {
  database: 'postgres' | 'mysql'
  port: number
}

const myConfig = {
  database: 'postgres',
  port: 5432
} satisfies Config

// myConfig.database sigue siendo 'postgres' literal (no 'postgres' | 'mysql')
// myConfig.port sigue siendo 5432 literal (no number generico)
```

Reemplaza el patron `as Config` (que pierde inference).

## 6. `using` y `await using` (Symbol.dispose / asyncDispose)

Cleanup automatico al salir scope (ES2024):

```typescript
async function processFile(path: string) {
  await using handle = await fs.promises.open(path, 'r')
  const content = await handle.readFile()
  // handle.close() llamado automaticamente al salir
}

class MyResource {
  async [Symbol.asyncDispose]() {
    // cleanup code
  }
}
```

Reemplaza patrones `try/finally` repetitivos.

## 7. `const` type parameters

Preserva literal types en generics (estable desde TS 5.0, idiomatico en 6):

```typescript
function createTuple<const T extends readonly unknown[]>(items: T): T {
  return items
}

const result = createTuple(['a', 'b'] as const)
// result type: readonly ['a', 'b']
```

## 8. `isolatedDeclarations`

Para library authors. Genera `.d.ts` sin invocar full type-checker:

```jsonc
{
  "compilerOptions": {
    "declaration": true,
    "isolatedDeclarations": true
  }
}
```

- 10x mas rapido para tools como Bun, swc, tsup
- Requiere tipos explicitos en exports publicos (trade-off)

Recomendado en packages internos del portfolio (`packages/<X>/`).

## 9. Type narrowing mejorado

```typescript
function filterStrings(arr: (string | number)[]): string[] {
  // El compiler infiere automaticamente como type guard
  return arr.filter((x): x is string => typeof x === 'string')
}
```

## 10. `verbatimModuleSyntax` (recomendado)

Obliga `import type` para imports type-only:

```typescript
// ERROR con verbatimModuleSyntax
import { type Component } from 'vue'

// OK
import type { Component } from 'vue'

// O si Vue es value:
import Vue from 'vue'
import type { Component } from 'vue'
```

Biome enforza con `useImportType`.

## Patrones recomendados

### Type-safe config con `satisfies`

```typescript
type ThemeConfig = {
  colors: { primary: string; secondary: string }
  fonts: ('serif' | 'sans-serif')[]
}

const config = {
  colors: { primary: '#3B82F6', secondary: '#10B981' },
  fonts: ['serif', 'sans-serif']
} satisfies ThemeConfig
```

### Validated schemas con Zod + z.infer

```typescript
import { z } from 'zod'

const userSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  role: z.enum(['admin', 'user']).default('user')
})

type User = z.infer<typeof userSchema>
const user = userSchema.parse(data)
```
