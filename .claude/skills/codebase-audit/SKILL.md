---
name: codebase-audit
description: >
  Codebase health audit (dead code, complexity, duplication, tech debt) for
  this portfolio Astro 6 + TypeScript project. ALWAYS invoke for codebase
  quality or tech debt assessment. Triggers: "codebase audit", "auditoria",
  "tech debt", "deuda tecnica", "dead code", "codigo muerto", "complexity",
  "duplication", "code smell", "code quality", "health check", "refactor
  candidates".
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash(pnpm:*), Bash(npx:*)
argument-hint: "scope: full | src | tests | configs | module-name"
metadata:
  version: "2.0"
---

# Codebase Audit

Auditoria de salud del codebase del portfolio: codigo muerto, complejidad, duplicacion, conformidad con convenciones del proyecto.

## Areas de auditoria

### 1. Codigo muerto y sin usar

Biome detecta automaticamente:

```bash
pnpm exec biome check . --max-diagnostics=200
```

Reglas activas relevantes: `noUnusedVariables`, `noUnusedImports`, `noUnusedFunctionParameters`.

Buscar manualmente con Grep:

- Funciones/clases exportadas sin referencias en el resto del codebase
- Componentes Astro en `src/components/` sin imports
- Utilities en `src/lib/` sin imports
- Content entries en `src/content/` sin renderizar en ninguna pagina

### 2. Complejidad cognitiva

Biome `noExcessiveCognitiveComplexity` (max 15) reporta funciones complejas.

Candidatas a refactor:

- Componentes Astro con > 50 lineas de logica en frontmatter
- Utilities con muchas ramas (extraer a sub-funciones puras)
- Pipelines de transformacion (extraer pasos a funciones nombradas)

### 3. Conformidad arquitectural

Verificar que el proyecto sigue sus propias convenciones:

| Regla | Verificacion |
|-------|-------------|
| Archivos < 300-500 lineas | `wc -l src/**/*.{ts,astro}` (o equivalente con Grep tool) |
| Componentes en `src/components/`, paginas en `src/pages/` | Buscar componentes fuera de su carpeta |
| Tokens del DS via vars, sin hex inline | Grep `#[0-9a-fA-F]{3,8}` en `.astro` y `.ts` |
| Type-only imports cuando aplica | Biome `useImportType` lo enforce |
| Sin `any` | Grep `: any` o `as any` |
| Sin fonts desde Google Fonts CDN | Grep `fonts.googleapis.com` |

### 4. Duplicacion de codigo

Buscar patrones repetidos:

- Mismo formatter de fecha/numero implementado en varios archivos
- Misma validacion en multiples componentes
- Estilos CSS duplicados (deberian usar tokens del DS)
- Markup repetido (candidato a extraer componente)

### 5. Coverage gaps

Verificar archivos sin tests (path mirroring):

```text
Para cada archivo en src/lib/, src/components/:
  Verificar que existe tests/unit/<mismo path>/<nombre>.test.ts
```

### 6. Performance / bundle

```bash
pnpm run build              # genera dist/ con sizes
ls -lh dist/                # inspeccionar output
```

Buscar:

- `client:load` en componentes que podrian ser `client:visible` o `client:idle`
- Imagenes sin optimizar (no usan `<Image>` de Astro)
- Imports innecesarios que inflan bundle

### 7. Tech debt score

| Metrica | Peso | Calculo |
|---------|------|---------|
| Archivos > 500 lineas | 3 | Contar archivos |
| Funciones complejidad > 15 | 3 | Contar funciones (Biome output) |
| Coverage < 80% | 2 | Contar archivos sin mirror |
| Codigo muerto | 1 | Contar items (Biome output) |
| Duplicacion estimada | 1 | Instancias detectadas |
| `any` o `as any` | 2 | Contar ocurrencias |
| Hex inline (sin token DS) | 1 | Contar ocurrencias |

Score = suma(items * peso). Menor es mejor.

## Formato de reporte

```markdown
## Codebase Audit Report — [fecha]

### Tech Debt Score: [N] ([bajo/medio/alto/critico])
- 0-10: Saludable
- 11-30: Deuda menor
- 31-60: Atencion requerida
- 61+: Critico

### Codigo muerto
| Archivo | Tipo | Ultima referencia |
|---------|------|-------------------|

### Complejidad excesiva (> 15)
| Archivo | Funcion | Complejidad | Sugerencia |
|---------|---------|-------------|-----------|

### Violaciones arquitecturales
| Regla violada | Archivo | Linea | Fix |
|---------------|---------|-------|-----|

### Coverage gaps (archivos sin tests)
| Source | Test esperado | Existe |
|--------|--------------|--------|

### Duplicacion detectada
| Patron | Archivos | Sugerencia |
|--------|----------|-----------|

### Archivos mas grandes (> 300 lineas)
| Archivo | Lineas | Sugerencia |
|---------|--------|-----------|

### Recomendaciones priorizadas
1. [Accion] — Impacto: [alto/medio/bajo]
2. [Accion] — Impacto: [alto/medio/bajo]
```

## Reglas

- SIEMPRE ejecutar `pnpm exec biome check .` como primera fuente de datos
- SIEMPRE verificar con Grep/Read antes de declarar codigo como muerto
- NUNCA sugerir eliminar codigo sin confirmar que no tiene referencias
- NUNCA sugerir refactoring masivo — priorizar por impacto
- Enfocarse en `src/` (codigo activo)
