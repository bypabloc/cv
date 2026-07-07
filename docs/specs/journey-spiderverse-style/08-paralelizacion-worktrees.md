# 10. Paralelización con git worktrees

## Base secuencial (T1 → T2 → T3)

T1, T2 y T3 tocan archivos compartidos por TODO el motor (`app.ts` en
particular, tocado por T2 y T3) y son prerequisito de las 3 salas — se
implementan en orden, en un solo hilo de trabajo, sin worktrees.

## Ola worktree-safe (T4a, T4b, T4c)

Una vez T1-T3 están verdes (loaders + postfx + character.ts
funcionando con un `.glb` de prueba), las 3 migraciones de sala son
**archivos disjuntos** (`rooms/aula.ts`, `rooms/futuro.ts`,
`rooms/destacame.ts` + sus respectivas carpetas `public/models/<sala>/`)
y **no comparten estado mutable entre sí** — candidatas a worktree, según
la política de [orchestration.md](../../../.claude/rules/orchestration.md)
(`isolation: 'worktree'` solo cuando los agentes mutan archivos en
paralelo; cap de ≤4 concurrentes, acá son 3).

```bash
git worktree add .claude/worktrees/journey-aula -b wt/journey-aula
git worktree add .claude/worktrees/journey-futuro -b wt/journey-futuro
git worktree add .claude/worktrees/journey-destacame -b wt/journey-destacame
```

Cada worktree corre su propio `pnpm install` (store compartido). Mergear
los 3 de vuelta a `feature/journey-spiderverse-style` en cualquier orden
(archivos disjuntos, sin conflicto esperado).

## Lo que NO se paraleliza

- T1, T2, T3 (base secuencial, archivos compartidos).
- T5 (créditos, necesita la lista final de las 3 salas).
- T6 (verificación de cierre, es el gate final).

En la práctica, dado el tamaño acotado de este prototipo (3 salas) y que
cada migración de sala es sustancial (cientos de líneas + curación de
assets), la ejecución puede hacerse igual de forma secuencial sin
worktrees si el volumen de trabajo por sala no justifica el overhead de
3 worktrees simultáneos — la paralelización queda disponible, no
obligatoria.
