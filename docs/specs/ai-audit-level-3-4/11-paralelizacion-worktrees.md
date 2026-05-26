# 11 — Paralelizacion con git worktrees

> **Anterior**: [10-commits.md](10-commits.md) · **Siguiente**: [12-verificacion-e2e.md](12-verificacion-e2e.md)

## Base secuencial obligatoria (NO paralelizable)

Los siguientes commits DEBEN aplicarse secuencialmente porque tocan
archivos transversales o son prerequisitos para otras fases:

| Commit | Por que no paralelizar |
|--------|------------------------|
| 1 (plan inicial) | Crea la carpeta del plan; commits posteriores asumen su existencia |
| 2 (Fase 0 diagnostico) | Solo doc; no bloquea pero conviene tenerlo antes para validar el fix |
| 3 (Fase 1A fix api-catalog) | Modifica `packages/seo/src/lib/build-redirects.ts` + `build-headers.ts` + los 6 `build-public-assets.mjs`. Fase 1B-2C tambien modifican estos archivos, asi que SI o SI va antes. |
| 12 (Fase 3 validar skills) | Toca `.claude/rules/ai-audit.md` que documenta decisiones del plan. Conviene al final cuando todo este implementado. |
| 13 (cierre) | Elimina la carpeta del plan; debe ser el ultimo. |

## Fases worktree-safe (paralelizables)

Tras el commit 3 (Fase 1A), las siguientes fases se pueden ejecutar en
paralelo porque tocan archivos disjuntos:

| Worktree | Fases | Archivos exclusivos | Commits | Conflictos potenciales |
|----------|-------|---------------------|---------|------------------------|
| W1 | 1B + 1C | `packages/markdown-export/**` + `cloudflare/transform-rules.md` + apps `postbuild-markdown.mjs` + bloque `.md` en `build-headers.ts` | 4, 5, 6 | con W3 en `build-headers.ts` (resolver mergeando bloques) |
| W2 | 2A + 2B | `packages/mcp/**` + apps `functions/mcp.ts` | 7, 8, 9, 10 | ninguno con W1/W3 |
| W3 | 2C | `packages/seo/src/lib/build-mcp-server-card.ts` + bloque api-catalog en `build-headers.ts` + apps `build-public-assets.mjs` (linea del server card) | 11 | con W1 en `build-headers.ts` (resolver mergeando bloques); con W2 (necesita `packages/mcp` exporte `TOOLS`) |

### Dependencia W3 → W2

W3 (server card builder) **necesita** que `packages/mcp` exporte `TOOLS`
y `PROTOCOL_VERSION`. Como esos exports los crea W2 (Fase 2A), W3 NO
puede empezar hasta que W2 haya hecho el commit 7 (paquete creado).

**Estrategia**: W3 empieza despues del commit 7 de W2. Si se quiere
paralelizar al maximo, W3 puede mockear los exports temporalmente y
remplazarlos al rebasear sobre W2 (mas complejo, no recomendado).

### Resolucion de conflictos en `build-headers.ts`

W1 y W3 ambos agregan bloques nuevos al final del builder. Resolver al
mergear:

1. Agregar bloque `.md` (de W1)
2. Agregar bloque `api-catalog.json` + Link mcp-server-card (de W3)
3. Tests de ambos worktrees deben pasar en el merge

## Comando para lanzar worktrees

```bash
# Asumiendo que estamos en feature/ai-audit-level-3-4 con commit 3 aplicado

# W1: Markdown estatico + Transform Rule docs
git worktree add ../portfolio-w1-markdown -b feature/ai-audit-l34-w1-markdown

# W2: MCP server + tools
git worktree add ../portfolio-w2-mcp -b feature/ai-audit-l34-w2-mcp

# W3: MCP server card (esperar a que W2 haga commit 7)
git worktree add ../portfolio-w3-mcp-card -b feature/ai-audit-l34-w3-mcp-card
```

Luego en cada worktree:

```bash
cd ../portfolio-w1-markdown && pnpm install --frozen-lockfile
cd ../portfolio-w2-mcp && pnpm install --frozen-lockfile
cd ../portfolio-w3-mcp-card && pnpm install --frozen-lockfile
```

Y trabajar las fases asignadas. Al terminar cada worktree:

```bash
# En el worktree
git push -u origin <branch>

# De vuelta en la rama principal feature/ai-audit-level-3-4
git merge origin/feature/ai-audit-l34-w1-markdown
git merge origin/feature/ai-audit-l34-w2-mcp
git merge origin/feature/ai-audit-l34-w3-mcp-card

# Limpiar worktrees
git worktree remove ../portfolio-w1-markdown
git worktree remove ../portfolio-w2-mcp
git worktree remove ../portfolio-w3-mcp-card
```

## Que NO se paraleliza

- **Fase 0** (diagnostico): un solo commit, doc puro.
- **Fase 1A** (fix api-catalog): base de todo el plan, toca archivos
  transversales (build-redirects, build-headers, build-public-assets x6).
- **Fase 3** (skills + rules): toca `.claude/*`, conviene tras todo
  implementado.
- **Fase 4** (verificacion E2E + cierre): tiene que ser el ultimo
  commit; ejecuta la bateria completa.

## Limites de paralelizacion

| Limite | Valor |
|--------|-------|
| Worktrees concurrentes | 3 (W1, W2, W3) — bien por debajo del soft limit de 5-7 |
| Tareas concurrentes por worktree | 1 |
| Commits totales del plan | 13 (3 secuenciales + 10 paralelos en 3 ramas + 1 cierre + 1 plan inicial) |

## Anti-patterns

| Anti-pattern | Por que esta mal |
|--------------|------------------|
| Lanzar W3 antes de que W2 commitee el paquete @portfolio/mcp | TOOLS no existe; el builder no compila |
| Modificar `build-headers.ts` en 3 worktrees a la vez | 3-way merge conflict garantizado |
| Saltar Fase 1A y empezar 2B directamente | Sin fix de api-catalog, el server card publicado va a tener el mismo bug de SPA fallback |
| Pushear cualquier worktree a `dev` directamente | TODO va via PR a `feature/ai-audit-level-3-4` primero |
