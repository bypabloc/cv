# 06 — Paralelizacion con git worktrees (seccion 10)

> [<- 05 Commits](05-commits.md) · [Verificacion E2E ->](07-verificacion-e2e.md)

## Base secuencial (NO paralelizable — un worktree, en orden)

Estos commits tocan archivos TRANSVERSALES que todas las salas leen. Se hacen
PRIMERO, en la rama base, antes de abrir cualquier worktree:

- **C2** (T1) — `lib/rooms.ts`, `themes.ts`, `world.ts` manifest, `audio.ts`.
- **C3** (T2) — `themes.ts` (paleta).
- **C4** (T3) — `props.ts` (helpers) + `world.ts`/`state.ts`/`app.ts`/`hud.ts`
  (UI action showcase).
- **C5** (T4) — `world.ts` (loadPast) + `rooms/past/index.ts` + mover aula.

Motivo: `RoomId` union, el manifest WORLD, los themes y los 4 helpers son la
interfaz que las salas consumen. Si dos worktrees editan `world.ts` o
`props.ts` a la vez, colisionan. Se estabilizan ANTES.

## Fases worktree-safe (tras la base — archivos disjuntos)

Cada sala vive en archivos propios (`rooms/<id>.ts`, `rooms/past/<id>.ts`,
`dialogs/<id>-*.ts`). Tras la base, N salas se pueden construir en paralelo
sin tocarse.

**Cap duro: <=4 worktrees/agentes simultaneos** (rate-limit, ver
`orchestration.md`). 9 unidades de sala -> 3 olas de <=4.

| Ola | Salas (worktree-safe) | Commits |
|-----|-----------------------|---------|
| 1 | Aula · CORPOELEC · IPASME · Cofasa | C6, C7, C8, C9 |
| 2 | Dibal · GoodMeal · Destacame · Futuro | C10, C11, C12, C13 |
| 3 | (cierre, secuencial) audio · perf · rule | C14, C15, C16 |

Dentro de una ola: cada sala en su worktree
(`.claude/worktrees/sala-<id>`), rama `feature/journey-sala-<id>` partiendo de
la rama base ya con C2-C5. Al cerrar la ola: mergear los worktrees en orden a
la rama base, borrar los worktrees.

> Cada worktree necesita `pnpm install` propio (store compartido, rapido) +
> copiar los `.env` gitignored si el build los exige:
> `cp -rn docker/env/. <worktree>/docker/env/`. Journey no usa backend, pero
> el pre-push del monorepo puede pedir env del admin — copiarlos evita el
> ZodError (ver `parallel-sessions.md`).

## Lo que NO se paraleliza

- La base secuencial (C2-C5).
- El cierre (C14-C17): audio, perf, rule, verificacion E2E — tocan config
  central o dependen de TODAS las salas.
- `lib/rooms.ts` / `world.ts` manifest / `themes.ts`: se editan UNA vez en la
  base para las 8, no por sala.

## Como lanzar cada worktree (ola)

```bash
# base ya commiteada (C2-C5) en feature/journey-salas-estandar
git checkout feature/journey-salas-estandar

# ola 1: 4 worktrees
for id in aula corpoelec ipasme cofasa; do
  git worktree add .claude/worktrees/sala-$id -b feature/journey-sala-$id
  cp -rn docker/env/. .claude/worktrees/sala-$id/docker/env/ 2>/dev/null || true
done
# en cada worktree: pnpm install + construir la sala + commit
# al cerrar la ola: merge en orden + git worktree remove + prune
```

> Eleccion de primitiva: cada sala es trabajo de JUICIO (arte-direccion,
> guiños, dialogos) -> subagente/worktree, NO tarea deterministica. El
> typecheck/build por sala corre en Bash dentro del worktree, NO un agente
> LLM por comando (regla de oro de `orchestration.md`). Modelo por defecto
> Opus 4.8 (las salas piden juicio narrativo/estetico).

## Alternativa secuencial (si no se usa paralelismo)

Si se prefiere no abrir worktrees: hacer C2->C17 en orden en la rama base.
Mas lento pero cero coordinacion. Recomendado si el usuario quiere revisar
sala por sala antes de la siguiente (local-first).
