# Loop health check - portfolio

> Activado con `/loop <interval>` (por ejemplo `/loop 15m`). Claude ejecuta este
> contenido en cada tick para verificar el estado del proyecto.

## Objetivo

Health check rapido del portfolio en background mientras el desarrollador esta
trabajando en otra cosa. NO modificar codigo. Solo reportar estado en una linea.

## Pasos

### 1. Toolchain

```bash
pnpm --version >/dev/null 2>&1 && echo "pnpm $(pnpm --version)"
test -d node_modules && echo "node_modules: OK" || echo "node_modules: FALTA"
```

### 2. Conformance Biome

Solo si hay archivos modificados:

```bash
git diff --name-only HEAD | grep -E '\.(ts|tsx|astro|js|jsx|mjs|cjs|json|jsonc|css)$' | head -1 && \
  pnpm exec biome check . 2>&1 | tail -3
```

### 3. Typecheck

Solo si hay archivos modificados:

```bash
git diff --name-only HEAD | grep -E '\.(ts|tsx|astro)$' | head -1 && \
  pnpm exec tsc --noEmit 2>&1 | tail -3 && \
  pnpm exec astro check 2>&1 | tail -3
```

### 4. Tests sobre cambios

```bash
pnpm exec vitest run --changed 2>&1 | tail -3
```

### 5. Estado git

```bash
git status --short
git log --oneline -3
```

## Reporte esperado (1-3 lineas)

Si todo OK:

```text
[health] OK | pnpm + node_modules | 0 biome issues | tests verde | branch=feature/x | 2 commits ahead
```

Si hay issues:

```text
[health] WARN | 3 errores Biome (corre lint-fix) | rest OK
```

## Reglas

- NO editar archivos. Esto es solo lectura/diagnostico.
- NO commitear ni pushear.
- Si encuentras un error: reportar UNA linea con la pista, no fixear automaticamente.
- Si node_modules falta: reportar y sugerir `pnpm install`, no instalar automaticamente.
- Si pasan 3 ticks consecutivos con todo verde: incrementa el intervalo (sugerir `/loop 30m` o `/loop 1h`).
