# 05 — Commits (seccion 9)

> [<- 04 Descomposicion](04-descomposicion.md) · [Worktrees ->](06-paralelizacion-worktrees.md)

Commits incrementales en Conventional Commits español. Cada uno deja el repo
verde (typecheck + build de journey). Rama de trabajo:
`feature/journey-salas-estandar` (partir de `dev`, NUNCA trabajar en `dev`).

> Recordatorio: `apps/journey` esta EXENTA de tests unit (no declara script
> `test`). El verde por commit = `typecheck` + `build` de la app, mas
> verificacion visual manual. No hay coverage que gatear en journey.

## Secuencia

### C1 — docs del plan

```
docs(specs): plan journey-salas-estandar (8 salas + canon + helpers)

- Agrega la carpeta docs/specs/journey-salas-estandar/ con README + 7 archivos
- Documenta las 12 decisiones cerradas del usuario (2026-07-05)
- Mapa de 8 salas data-driven, los 4 puntos de infra, AC-1..AC-20
```

### C2 — infra: RoomId a 8 + rename cima->destacame + stubs

```
feat(journey): amplia RoomId a 8 salas y renombra cima a destacame

- RoomId union: aula, corpoelec, ipasme, cofasa, dibal, goodmeal,
  destacame, futuro (lib/rooms.ts, ROOM_SPECS con las 8)
- Manifest WORLD + THEMES + PAST_CAPTIONS con las 8 entradas
- Escenas nuevas como stubs (grupo vacio) para que compile
- Verifica: typecheck verde con el union completo
```

Cubre T1. Verify: `pnpm --filter @portfolio/journey typecheck`.

### C3 — paleta paredes-blancas

```
feat(journey): estandariza paredes blancas + acento del rubro por sala

- themes.ts: wall #f2f0eb en las 8 salas; el color del rubro pasa a
  floor/trim/accent/lightColor/screen (tabla del canon)
- Verifica: dev, cada sala con pared blanca + acento correcto
```

Cubre T2 (AC-2).

### C4 — helpers del canon + UI action showcase

```
feat(journey): helpers officeLayout/npcCoworkers/wallArt/softwareShowcase

- props.ts: los 4 helpers reutilizables del canon de sala
- world.ts/state.ts/app.ts/hud.ts: UI action openShowcase + panel DOM
  operable (abre/cierra E/Esc, deshabilita controles)
- Verifica: sala de prueba invoca los 4 helpers y el showcase funciona
```

Cubre T3 (AC-3, AC-6, AC-7).

### C5 — partir pasados en archivos por sala

```
refactor(journey): separa los pasados en rooms/past/<id>.ts + dispatcher

- rooms/past/index.ts (dispatcher + shell buildPast)
- rooms/past/aula.ts movido sin cambios de contenido
- world.ts loadPast -> ./rooms/past/index
- Verifica: entrar al pasado de las salas existentes sigue OK
```

Cubre T4.

### C6 — Aula (refactor minimo)

```
feat(journey): aula con profesor y compañeros nuevos (2 enfoques)

- rooms/aula.ts + dialogs/aula-presente.ts: +profesor que elogia a Pablo,
  +compañeros de proyecto/univ ayudados (4-5 NPCs conversables)
- wallArt con diagramas cliente-servidor
- Pasado de aula intacto (decision del usuario)
```

Cubre T5 (AC-9).

### C7..C12 — una sala por commit (paralelizables via worktree)

Cada uno con el patron:

```
feat(journey): sala <NOMBRE> (presente + pasado + dialogos)

- rooms/<id>.ts: oficina + guiños del rubro + showcase + wallArt + 4-5 NPCs
- rooms/past/<id>.ts: ambiente sepia del "antes" + NPCs frustrados
- dialogs/<id>-presente.ts + <id>-pasado.ts (2 enfoques, data-driven)
- Verifica: recorrido de la sala + showcase + pasado
```

- **C7**: CORPOELEC (presente refactor + pasado refactor) — T6, T7 (AC-10, AC-11).
- **C8**: IPASME — T8 (AC-14).
- **C9**: Cofasa — T9 (AC-14).
- **C10**: Dibal — T10 (AC-14).
- **C11**: GoodMeal — T11 (AC-14).
- **C12**: Destacame unificada + pasado deudas — T12, T13 (AC-12, AC-13).
- **C13**: Futuro (sintetica) — T14 (AC-15).

> Si se paraleliza con worktrees, cada worktree produce SU commit y se mergea
> en orden a la rama. Ver [06](06-paralelizacion-worktrees.md).

### C14 — audio ambiente salas nuevas

```
feat(journey): audio ambiente opt-in de las salas nuevas

- engine/audio.ts: clip por RoomId (respeta mute, arranca en silencio)
```

Cubre T16 (AC-19).

### C15 — perf: <100 draw calls/sala

```
perf(journey): mantiene <100 draw calls por sala

- fusiona mobiliario/relleno de fondo; mide renderer.info.render.calls
- Verifica: cada sala < 100 en tier full
```

Cubre T18 (AC-4).

### C16 — rule del estandar

```
docs(rules): journey-rooms — canon de sala del journey 3D

- .claude/rules/journey-rooms.md: 4 helpers, estructura presente/pasado,
  paredes-blancas, <100 draw calls, 4 puntos de infra, 2 enfoques NPC
- Validada con claude -p (5 angulos)
```

Cubre T19.

### C17 — verificacion E2E + elimina la carpeta del plan

```
test(journey): verificacion E2E de las 8 salas + limpieza del plan

- Bateria completa (seccion 11) en verde: typecheck + build + recorrido
  manual de las 8 salas + teleport + tour + Static + perf
- git rm -r docs/specs/journey-salas-estandar/ (carpeta efimera)
```

Cubre T17, T20. Es el ultimo commit (seccion 11).

## PR

Un solo PR `feature/journey-salas-estandar -> dev`. Body con las 4 secciones
(Problema / Solucion / Como probar / TODO). **Como probar**: reutiliza la
bateria de [07](07-verificacion-e2e.md) + `pnpm --filter @portfolio/journey dev`
(http://localhost:4327/) recorriendo las 8 salas.

> **Local-first (preferencia del usuario)**: NO desplegar al terminar. Dejar
> commiteado + verificado + dar el comando dev para que Pablo pruebe. El push
> y el PR se hacen SOLO con la bateria de la seccion 11 verde. El deploy a
> Cloudflare es un PR posterior cuando el usuario lo confirme.
