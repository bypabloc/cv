# ESTADO — progreso del plan journey-salas-estandar

> Cola de trabajo persistente entre sesiones. Cada sesion que crea una sala
> de Etapa 2 ACTUALIZA este archivo al terminar (marca la sala HECHA + commit
> sha). Se lee al RETOMAR (ver "Protocolo de retoma" en [README](README.md)).
>
> Rama unica: `feature/journey-salas-estandar` (sin merge hasta cerrar las 7).

## ETAPA 1 — estandarizacion + Aula (stop gate)

| Commit | Que | Estado |
| --- | --- | --- |
| C2 | infra RoomId->8 + rename cima->destacame (stubs) | HECHO `9163b0cb` |
| C3 | paleta paredes-blancas (themes.ts) | HECHO `5405fee8` |
| C4 | helpers canon (officeLayout/npcCoworkers/wallArt/softwareShowcase) + UI action showcase | HECHO `3db5f9dc` |
| C5 | partir pasados en rooms/past/<id>.ts + dispatcher | HECHO `8acd4915` |
| C6 | Aula refactor (prueba del canon, AC-9) | HECHO `af82a772` |
| — | **STOP GATE**: verificar Etapa 1, commit, NO merge, detener | **ALCANZADO 2026-07-05** |

> ETAPA 1 HECHA (2026-07-05). Verificada: typecheck + lint + build verdes,
> smoke con browser (8 salas montan via teleport, showcase abre/cicla/cierra
> end-to-end sobre un arnes temporal en el stub de ipasme, luego revertido).
> Decisiones de ejecucion: destacame quedo como STUB VACIO (literal del
> plan); los stubs llevan placeholder "en construccion" (cartel + barrera
> con el acento). Las salas de Etapa 2 se ejecutan en sesiones separadas.

## ETAPA 2 — salas 1 a 1 (orden cronologico sugerido, se puede saltar)

| Orden | Sala | Informe | Estado | Commit |
| --- | --- | --- | --- | --- |
| 1 | `corpoelec` | [08-sala-corpoelec.md](08-sala-corpoelec.md) | HECHO | `46f28551` |
| 2 | `ipasme` | [09-sala-ipasme.md](09-sala-ipasme.md) | HECHO | `d22c3988` |
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

- [2026-07-05] ETAPA 1 HECHA (C1 `2196e8dd` .. C6 `af82a772`) — canon
  completo en props.ts; aula con 6 NPCs (profesor y 2 compañeros nuevos)
  y 3 cuadros wallArt (1 inspeccionable); pasados partidos (aula intacto,
  corpoelec movido, cima eliminado); nota perf: el aula con 6 NPCs puede
  rozar los 100 draw calls — medir/optimizar en C15.
- [2026-07-05] sala `ipasme` HECHA en commit `d22c3988` — informe 09 tal
  cual (decision del usuario: 5 NPCs, sin recortar). Showcase con look app
  de escritorio Windows 2014 (3 demos: ficha, buscador 0,2 s, control de
  acceso por rol). 5 NPCs nuevos (2C+2P+1J): Daniela y Jose Miguel (devs),
  Yuleima (enfermera en ronda), Argenis (archivista), Dr. Villasmil (jefe).
  Pasado: archivo de carpetas manila + hueco del tarjeton + reloj + 3 NPCs
  (Argenis/Yuleima del arco + Petra nueva) + busqueda lenta "solo el
  tarjeton". Micros presente: buscar historia (instante) + tomar turno.
  Smoke browser completo verde x2 (23 interactables, showcase E/Esc, 5
  dialogos, ficha carnet, pasado 29 interactables); el unico error de
  consola es el 504 transitorio de vite (gotcha conocido). Nota perf: 5
  NPCs + lotes clinicos — medir en C15 igual que aula/corpoelec.
- [2026-07-05] sala `corpoelec` HECHA en commit `46f28551` — primer
  consumidor real de officeLayout + softwareShowcase (3 demos intranet
  2013, badge OFFLINE). 5 NPCs (2C+2P+1J): los 2 arboles ricos existentes
  se CONSERVARON renombrados (veterano -> Wilmer Colina, tecnica de ronda
  -> Dubraska Piña reencuadrada administrativa) + 3 nuevos (Yorman,
  Genesis, Ing. Betancourt). Pasado: 3 NPCs (Dubraska y Wilmer del arco +
  el transcriptor conservado; Alcides opcional se fusiono en el Wilmer del
  pasado). wallArt 4 cuadros (2 inspeccionables). Smoke browser completo
  verde (23 interactables, showcase E/Esc, 5 dialogos, ficha 765 kV,
  pasado). Nota perf: 5 NPCs + estanteria + showcase — medir en C15 igual
  que el aula.
