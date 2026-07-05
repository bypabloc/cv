# ESTADO — progreso del plan journey-salas-estandar

> Cola de trabajo persistente entre sesiones. Cada sesion que crea una sala
> de Etapa 2 ACTUALIZA este archivo al terminar (marca la sala HECHA + commit
> sha). Se lee al RETOMAR (ver "Protocolo de retoma" en [README](README.md)).
>
> Rama unica: `feature/journey-salas-estandar` (sin merge hasta cerrar las 7).

## ETAPA 1 — estandarizacion + Aula (stop gate)

| Commit | Que | Estado |
| --- | --- | --- |
| C2 | infra RoomId->8 + rename cima->destacame (stubs) | PENDIENTE |
| C3 | paleta paredes-blancas (themes.ts) | PENDIENTE |
| C4 | helpers canon (officeLayout/npcCoworkers/wallArt/softwareShowcase) + UI action showcase | PENDIENTE |
| C5 | partir pasados en rooms/past/<id>.ts + dispatcher | PENDIENTE |
| C6 | Aula refactor (prueba del canon, AC-9) | PENDIENTE |
| — | **STOP GATE**: verificar Etapa 1, commit, NO merge, detener | — |

> Cuando ETAPA 1 este HECHA, marcar aqui y **detener el plan**. Las salas de
> Etapa 2 se ejecutan en sesiones separadas.

## ETAPA 2 — salas 1 a 1 (orden cronologico sugerido, se puede saltar)

| Orden | Sala | Informe | Estado | Commit |
| --- | --- | --- | --- | --- |
| 1 | `corpoelec` | [08-sala-corpoelec.md](08-sala-corpoelec.md) | PENDIENTE | — |
| 2 | `ipasme` | [09-sala-ipasme.md](09-sala-ipasme.md) | PENDIENTE | — |
| 3 | `cofasa` | [10-sala-cofasa.md](10-sala-cofasa.md) | PENDIENTE | — |
| 4 | `dibal` | [11-sala-dibal.md](11-sala-dibal.md) | PENDIENTE | — |
| 5 | `goodmeal` | [12-sala-goodmeal.md](12-sala-goodmeal.md) | PENDIENTE | — |
| 6 | `destacame` | [13-sala-destacame.md](13-sala-destacame.md) | PENDIENTE | — |
| 7 | `futuro` | [14-sala-futuro.md](14-sala-futuro.md) | PENDIENTE | — |

Estados validos: `PENDIENTE` · `EN CURSO` · `HECHO`.

## CIERRE (tras las 7 salas)

| Commit | Que | Estado |
| --- | --- | --- |
| C14 | audio ambiente de las salas nuevas | PENDIENTE |
| C15 | perf <100 draw calls/sala | PENDIENTE |
| C16 | rule del estandar (.claude/rules/journey-rooms.md) | PENDIENTE |
| C17 | verificacion E2E + `git rm -r` la carpeta del plan + merge unico a dev | PENDIENTE |

## Bitacora (append al terminar cada sala)

<!-- Formato: [YYYY-MM-DD] sala <id> HECHA en commit <sha> — notas -->

- (vacio: aun no se ha implementado ninguna sala)
