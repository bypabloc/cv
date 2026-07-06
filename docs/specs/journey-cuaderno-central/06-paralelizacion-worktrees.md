# 06 — Paralelizacion con git worktrees (seccion 10)

> [<- 05 Commits](05-commits.md) · [Verificacion E2E ->](07-verificacion-e2e.md)

## Base secuencial

**C1 (carpeta del plan) + C2 (reposicionar el pilar en `props.ts`)** son
la base: TODAS las tareas de sala dependen de que el helper compartido
`infoKit` ya tenga la posicion/collider nuevos, porque cada verificacion de
sala necesita el pilar ya en su lugar para confirmar que no choca con nada.

No se paraleliza C1/C2: es un solo archivo (`props.ts`) tocado una vez.

## Fases worktree-safe (tras C2)

| Fase | Tareas | Archivos | Cap |
|------|--------|----------|-----|
| Ola 1 | T2 (ipasme+iai), T3 (asesoria+cofasa), T4 (dibal+goodmeal desk), T5 (destacame) | 6 archivos de sala distintos | 4 agentes (dejar T6 para la ola 2 por la colision de archivo con T4) |
| Ola 2 | T6 (goodmeal path), T7 (futuro) | `rooms/goodmeal.ts` (secuencial tras T4), `rooms/futuro.ts` | 2 agentes |

Si se prefiere evitar la dependencia T4->T6 dentro de la misma sala,
fusionar ambos ajustes de `goodmeal` (desk + path) en una sola tarea/commit
y correrla en la Ola 1 junto a las demas (asi la Ola 2 queda solo con T7).

## Lo que NO se paraleliza

- C2 (el helper compartido) — base de todo.
- La verificacion final (seccion 11, T8) — corre en Bash/1 agente, no en
  fan-out.
- `rooms/goodmeal.ts` si T4 y T6 corren en worktrees distintos (colision de
  archivo) — secuenciar o fusionar (ver arriba).

## Como lanzar cada worktree

```bash
# tras commitear C1 + C2 en la rama de trabajo del plan
git worktree add .claude/worktrees/cuaderno-t2 -b tmp/cuaderno-t2
git worktree add .claude/worktrees/cuaderno-t3 -b tmp/cuaderno-t3
git worktree add .claude/worktrees/cuaderno-t4 -b tmp/cuaderno-t4
git worktree add .claude/worktrees/cuaderno-t5 -b tmp/cuaderno-t5
# cada worktree: pnpm install propio (store compartido), ajustar su sala,
# typecheck local, commit en su rama tmp/*
# luego mergear cada rama tmp/* a la rama del plan EN ORDEN (T2, T3, T4,
# T5), y recien despues correr T6/T7 (secuencial o en 1-2 worktrees mas)
git worktree remove .claude/worktrees/cuaderno-t2   # limpiar al terminar
```

> Dado el tamaño Small de este plan (7 tareas, ajustes de pocas lineas por
> archivo), worktrees son OPCIONALES: correr las tareas secuencialmente en
> la misma sesion (sin worktrees) es igual de rapido y mas simple. Usar
> worktrees solo si se quiere paralelizar de verdad con varios agentes a la
> vez (cap <=4, ver `.claude/rules/orchestration.md`).
