# journey-cuaderno-central — pilar del cuaderno al eje central + entradas despejadas

> Plan de ajuste del journey 3D (`apps/journey`, motor Three.js vanilla
> manga-ink), ejecutado DESPUES del plan `journey-salas-estandar` (10 salas
> HECHAS, pendiente su CIERRE C14-C17). Dos cambios sobre las 10 salas
> existentes, via el helper compartido `infoKit`/`lecternNotebook`
> (`apps/journey/src/engine/rooms/props.ts`):
>
> 1. **Reposicionar el pilar del cuaderno** (`lecternNotebook`) del muro -X
>    (esquina lateral junto a la puerta, hoy facil de ignorar) al **eje
>    central de transito (x=0)**, cerca de la entrada de cada sala,
>    **bloqueando el paso** para forzar que el jugador lo rodee y lo perciba.
> 2. **Despejar la zona de entrada** de 7 salas donde escritorios del
>    `officeLayout` quedan atravesados en la franja de los primeros ~2m
>    desde la puerta de entrada, replicando el margen libre que ya tiene el
>    aula (canon de referencia).

## Contexto

El plan `journey-salas-estandar` (ver
[../journey-salas-estandar/README.md](../journey-salas-estandar/README.md))
ya implemento las 10 salas del recorrido con el canon fijo (`officeLayout`,
`npcCoworkers`, `wallArt`, `softwareShowcase`, `infoKit`). Al revisar el
resultado, el dueño del producto detecto dos problemas de percepcion/flujo
que no estaban cubiertos por ese plan:

1. El **cuaderno-reseña** (`lecternNotebook`, el pedestal con el resumen de
   la etapa que abre el panel de historia completa al pulsar E) vive hoy
   pegado al muro -X, junto a la puerta de salida
   (`position: [-half + 0.9, 0, room.z + 5.1]` en
   `props.ts:897-906`). El jugador puede cruzar la sala de punta a punta por
   el eje central (x=0) sin verlo ni acercarse — es fácil de ignorar pese a
   ser una pieza de contenido importante del CV.
2. Al investigar el layout de las 10 salas se confirmo que 7 de ellas
   (ipasme, iai, asesoria, cofasa, dibal, goodmeal, destacame) tienen
   `deskSpots` del `officeLayout` cuyo footprint (escritorio + silla) invade
   la franja de los primeros ~2 metros desde la entrada de la sala,
   distinto del aula (que no usa `officeLayout` y por eso tiene la entrada
   completamente despejada).

### Hallazgos de exploracion (investigacion previa a este plan)

- Sala cuadrada uniforme: `ROOM_SIZE = 13.2` m (`lib/layout.ts:15`); entrada
  en `zFront = room.z - room.depth/2`, salida en `zBack = room.z +
  room.depth/2` (`lib/layout.ts:160-161`). El jugador entra y camina en
  linea recta por x=0 hacia la puerta siguiente — hoy ese eje esta libre de
  colliders salvo en salas especificas.
- `PLAYER_RADIUS = 0.35` (`lib/layout.ts:24`). Los colliders del motor son
  AABB (`Box2`, `collision.ts:9`) resueltos como circulo-vs-caja
  (`circleIntersectsBox`, `collision.ts:26`) — **no existe collider
  circular nativo**; un pilar central se modela como `footprint(0, z, w,
  w)` cuadrado.
- El pilar (`lecternNotebook`, `props.ts:757-835`) es un cilindro delgado
  (escala `0.5 x 0.9 x 0.5`) con el cuaderno flotando encima
  (`NOTE_FLOAT_Y = 1.42`), radio de interaccion `2.2` — diseñado para estar
  contra una pared, sin collider propio hoy (el unico collider que aporta
  `infoKit` es el del pedestal, `footprint(-half + 0.9, room.z + 5.1, 0.7,
  0.7)` en `props.ts:911`, que coincide con la posicion actual del cuaderno).
- Conflictos detectados de un pilar en x=0 cerca de la entrada:
  - `goodmeal`: NPC "daniela" tiene un `path` que cruza x=0 en esa franja.
  - `destacame`: `deskSpot` en `x=0.0` casi exacto Y NPC "valentina" con
    `path` que cruza cerca de x=0.
  - El resto de las salas no tiene nada en el eje x=0 mismo cerca de la
    entrada (aunque si tienen escritorios cerca, ver punto 2).
- Escritorios que invaden la franja de entrada (spot + silla, ~0.8-0.9m de
  extension): `ipasme`, `iai` (spots identicos `[-1.7,-4.3]`/`[0.7,-4.3]`),
  `asesoria` (`[-3.4,-4.2]`/`[-1.6,-4.2]`), `cofasa` (`[-1.7,-4.5]`/
  `[0.7,-4.5]`), `dibal` (`[2.4,-4.9]`/`[4.1,-4.9]`, lateral), `goodmeal`
  (`[1.6,-4.8]`/`[3.4,-4.8]`, lateral), `destacame` (`[-0.9,-4.8]`/
  `[0.9,-4.8]`, el peor caso: casi en el eje central). `corpoelec`, `aula`
  y `futuro` ya tienen la entrada libre (spots mas alejados o sin
  `officeLayout`).

## Solucion propuesta

**Un solo cambio de posicion + collider en el helper compartido
`lecternNotebook`/`infoKit`** (hereda a las 10 salas automaticamente) más
**ajustes puntuales de coordenadas** en las 7 salas con escritorios
invasivos y en los 2 NPCs con `path` conflictivo. Sin rediseño visual del
pilar (mismo cilindro + cuaderno flotante ya validado), sin tocar
retos/aprendizajes/grieta del `infoKit`.

### Decisiones clave

1. **Posicion del pilar**: `x=0` (eje central de transito), `z` cerca de la
   entrada (ej. `room.z - room.depth/4` o similar, a definir en la
   implementacion por sala si un caso puntual lo requiere — ver AC-2). Es
   lo primero que el jugador encuentra al entrar, antes de llegar a
   NPCs/showcase.
2. **Bloqueo real de paso**: el pilar agrega un `footprint` cuadrado de
   **1m x 1m** centrado en su posicion, forzando al jugador (radio 0.35m) a
   rodearlo. No es cosmetico: cambia el patron de movimiento por sala.
3. **Sin rediseño visual**: se reutiliza el mismo `lecternNotebook` (mismo
   cilindro, misma textura de cuaderno, mismo `NOTE_FLOAT_Y`, mismo radio
   de interaccion 2.2m). Solo cambia `position` + se agrega el nuevo
   collider al array que retorna `infoKit`.
4. **Aplica a las 10 salas sin excepcion**, incluida `futuro` (se debe
   verificar que no choque con su pedestal-CTA propio ya centrado en el
   muro final — son piezas distintas, `futuro` no tiene grieta pero si
   cuaderno via `infoKit`).
5. **NPCs con `path` conflictivo** (`goodmeal`/daniela, `destacame`/
   valentina): se ajustan los waypoints del `path` para rodear el punto del
   pilar, en vez de mover el pilar (mantiene el pilar consistente en x=0 en
   las 10 salas).
6. **Escritorios invasivos** (7 salas): se corren los `deskSpots`
   afectados hacia +Z (alejandolos de la entrada) lo necesario para que su
   footprint quede fuera de la franja de 2m desde `zFront` — mismo margen
   libre que ya tiene el aula. Regla uniforme, no caso por caso.
7. **Retos/aprendizajes/grieta del `infoKit` NO se tocan**: siguen en sus
   posiciones actuales contra los muros -X/+X. Solo el cuaderno se mueve.

## Criterios de aceptacion

- **AC-1**: Given cualquiera de las 10 salas, When el jugador entra y
  camina en linea recta por el eje x=0 hacia la puerta de salida, Then su
  collider (radio 0.35m) colisiona con el `footprint` de 1x1 del pilar del
  cuaderno y debe rodearlo para continuar.
- **AC-2**: Given el pilar reposicionado, When se mide su posicion en
  cualquier sala, Then `x=0` (eje central) y `z` cae dentro de la mitad de
  la sala mas cercana a la entrada (entre `zFront` y `room.z`).
- **AC-3**: Given el pilar movido al centro, When se inspecciona su
  geometria/material, Then es identico al `lecternNotebook` actual (mismo
  cilindro, misma textura, mismo `NOTE_FLOAT_Y`, mismo radio de
  interaccion 2.2m) — cero cambios visuales.
- **AC-4**: Given retos/aprendizajes/grieta del `infoKit`, When se
  compara su posicion antes/despues del cambio, Then permanecen
  IDENTICAS (solo el cuaderno se movio).
- **AC-5**: Given las salas `goodmeal` y `destacame`, When sus NPCs
  "daniela" y "valentina" recorren su `path`, Then ninguno de sus waypoints
  cruza el `footprint` del pilar (ruta ajustada para rodearlo).
- **AC-6**: Given las 7 salas con escritorios invasivos (ipasme, iai,
  asesoria, cofasa, dibal, goodmeal, destacame), When se mide el footprint
  de cada `deskSpot` (spot + silla) tras el ajuste, Then queda fuera de la
  franja de 2m desde `zFront` de esa sala (mismo margen que el aula).
- **AC-7**: Given la sala `futuro` (pedestal-CTA propio ya centrado en el
  muro final), When se agrega el pilar del cuaderno en el eje central cerca
  de la entrada, Then ambas piezas coexisten sin superposicion de
  colliders ni de geometria.
- **AC-8**: Given cualquier sala, When se interactua con el pilar
  reposicionado (acercarse + E), Then abre el panel de historia completa
  igual que antes (comportamiento de interaccion sin cambios).
- **AC-9**: Given el build/typecheck de `apps/journey`, When se ejecuta
  tras todos los cambios, Then pasa sin errores (0 TypeScript, 0 Biome).

## Diagrama de flujo (antes y despues)

### Antes

```text
entrada sala (x=0, z=zFront)
        |
        | (eje libre, sin colliders)
        v
  [officeLayout: puede invadir 0-2m desde zFront en 7 salas]
        |
        v
  ... NPCs / showcase / infoKit (retos/aprendizajes/grieta) ...
        |
        v
  [cuaderno: PEGADO al muro -X, junto a la puerta z+5.1 -- facil de ignorar]
        |
        v
puerta de salida (z=zBack)
```

### Despues

```text
entrada sala (x=0, z=zFront)
        |
        v
  [officeLayout: despejado los primeros 2m, como el aula] (AC-6)
        |
        v
  [PILAR DEL CUADERNO: x=0, z cerca de zFront, footprint 1x1 -- BLOQUEA]
        |             (AC-1, AC-2, AC-3)
        | <--- jugador rodea el pilar (izq o der) --->
        v
  ... NPCs (paths ajustados en goodmeal/destacame, AC-5) / showcase ...
        |
        v
  ... infoKit sin el cuaderno: retos/aprendizajes/grieta sin cambios (AC-4) ...
        |
        v
puerta de salida (z=zBack)
```

## Diagrama ER

N/A — el journey no modela entidades de dominio nuevas; es geometria y
colliders del motor 3D. Sin cambios en `@portfolio/content` ni schemas.

## Escala

**Small** (helper compartido + ajustes en 9 archivos de sala: 7 con
deskSpots + 2 con `path` de NPC, mas `props.ts`). Ver
[04-descomposicion.md](04-descomposicion.md) (seccion 8),
[05-commits.md](05-commits.md) (seccion 9),
[06-paralelizacion-worktrees.md](06-paralelizacion-worktrees.md) (10) y
[07-verificacion-e2e.md](07-verificacion-e2e.md) (11).

## Cuando leer cada archivo

| Archivo | Cuando leer |
|---------|-------------|
| README.md (este) | Indice, contexto, decisiones, AC, diagramas |
| [01-cambios-tecnicos.md](01-cambios-tecnicos.md) | Detalle tecnico exacto: firma nueva de `lecternNotebook`/`infoKit`, coordenadas por sala (pilar, deskSpots, paths) |
| [04-descomposicion.md](04-descomposicion.md) | Seccion 8: tareas atomicas + paralelizacion |
| [05-commits.md](05-commits.md) | Seccion 9: secuencia de commits |
| [06-paralelizacion-worktrees.md](06-paralelizacion-worktrees.md) | Seccion 10: paralelizacion (worktrees) |
| [07-verificacion-e2e.md](07-verificacion-e2e.md) | Seccion 11: verificacion final |

## Decisiones cerradas (2026-07-06 — NO reabrir sin el usuario)

1. **Alcance**: spec independiente, NO se inserta en el CIERRE (C14-C17) de
   `journey-salas-estandar`. Se ejecuta despues (o en paralelo) de ese
   cierre, tocando las 10 salas ya existentes via el helper compartido.
2. **Posicion del pilar**: eje central x=0, cerca de la entrada (mitad de
   sala mas proxima a `zFront`), NO en el centro geometrico exacto de la
   sala ni cerca de la salida.
3. **Bloquea el paso**: SI, con collider `footprint` 1m x 1m. El jugador
   debe rodearlo — es el efecto buscado ("forzado a leerse").
4. **Sin rediseño visual**: mismo cilindro + cuaderno flotante actual, solo
   reposicion + collider nuevo.
5. **Aplica a las 10 salas sin excepcion**, incluida `futuro` (verificar
   coexistencia con su pedestal-CTA propio).
6. **Solo el cuaderno se mueve**: retos/aprendizajes/grieta del `infoKit`
   quedan en sus posiciones actuales.
7. **NPCs con `path` conflictivo** (goodmeal/daniela, destacame/valentina):
   se ajusta el `path` del NPC para rodear el pilar, NO se desplaza el
   pilar.
8. **Escritorios invasivos** (7 salas): regla uniforme, correr los
   `deskSpots` afectados hacia +Z hasta liberar la franja de 2m desde la
   entrada — mismo margen que el aula. Sin ajuste caso por caso fuera de
   esa regla.
9. **Collider del pilar**: `footprint` cuadrado de 1m x 1m.

## Reglas criticas (SIEMPRE / NUNCA)

- **SIEMPRE** el cambio de posicion del pilar vive en el helper compartido
  `infoKit`/`lecternNotebook` (`props.ts`) — las 10 salas lo heredan sin
  tocar su propia llamada a `infoKit`, salvo overrides puntuales si hiciera
  falta (ej. `futuro`).
- **SIEMPRE** verificar sala por sala tras el cambio (recorrido visual +
  colliders): NPCs, `officeLayout`, showcase y props firma no deben quedar
  atravesados por el nuevo `footprint` del pilar.
- **SIEMPRE** los `deskSpots` ajustados mantienen la composicion visual
  general de la sala (correr en +Z, no reordenar ni eliminar puestos).
- **SIEMPRE** retos/aprendizajes/grieta del `infoKit` permanecen
  bit-a-bit identicos (mismo `position`/`rotationY`).
- **NUNCA** cambiar el diseño visual del `lecternNotebook` (cilindro,
  textura, radio de interaccion) — este plan es SOLO de posicion/collider.
- **NUNCA** desplegar automaticamente al terminar: local-first (misma
  politica que `journey-salas-estandar`) — dejar commiteado + verificado y
  dar el comando `pnpm --filter @portfolio/journey dev` para que Pablo
  pruebe primero.
- **NUNCA** atribucion de IA en commits, PRs ni codigo (politica del repo).

## Navegacion

- Detalle tecnico: [01-cambios-tecnicos.md](01-cambios-tecnicos.md)
- Ejecucion: [04-descomposicion.md](04-descomposicion.md) ·
  [05-commits.md](05-commits.md) ·
  [06-paralelizacion-worktrees.md](06-paralelizacion-worktrees.md) ·
  [07-verificacion-e2e.md](07-verificacion-e2e.md)
