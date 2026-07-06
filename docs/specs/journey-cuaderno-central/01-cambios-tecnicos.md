# 01 — Cambios tecnicos (helper + coordenadas por sala)

> [<- README](README.md) · [Descomposicion ->](04-descomposicion.md)

## 1. `lecternNotebook` / `infoKit` — nueva posicion + collider

Archivo: `apps/journey/src/engine/rooms/props.ts`.

### Posicion actual (a reemplazar)

```ts
// props.ts:897-906 (dentro de infoKit)
const nota = lecternNotebook({
  roomIndex: room.index,
  position: [-half + 0.9, 0, room.z + 5.1],   // <- muro -X, junto a la puerta
  rotationY: Math.PI / 2,
  theme: opts.theme,
  notebook: { title: texts.title, lines: texts.notebook },
  story: { title: texts.title, paragraphs: texts.resena },
  withLight: opts.withLight,
  onOpen: opts.onStory,
})
```

### Posicion nueva (propuesta)

```ts
// eje central, cerca de la entrada. room.z es el centro de la sala;
// zFront = room.z - room.depth/2. Un valor de referencia a mitad de
// camino entre zFront y room.z dentro de la mitad de entrada.
const NOTE_ENTRY_Z_OFFSET = room.depth / 4  // 3.3 con ROOM_SIZE=13.2
const nota = lecternNotebook({
  roomIndex: room.index,
  position: [0, 0, room.z - NOTE_ENTRY_Z_OFFSET],
  rotationY: 0,   // el jugador lo ve de frente al entrar; ajustar si el
                   // arte del cuaderno queda mejor a 90 grados (revisar
                   // visualmente, no es un AC estricto)
  theme: opts.theme,
  notebook: { title: texts.title, lines: texts.notebook },
  story: { title: texts.title, paragraphs: texts.resena },
  withLight: opts.withLight,
  onOpen: opts.onStory,
})
```

> El valor exacto de `NOTE_ENTRY_Z_OFFSET` (y si se necesita un ajuste
> puntual en alguna sala) se confirma en la implementacion con el recorrido
> visual — el numero de arriba es el punto de partida (a medio camino entre
> `zFront` y el centro de la sala).

### Nuevo collider

`lecternNotebook` hoy NO retorna collider propio (el `footprint` de
`infoKit` en `props.ts:911` usa la posicion VIEJA). Agregar el nuevo
footprint centrado en la posicion nueva:

```ts
// props.ts:907-912 (dentro de infoKit, return)
return {
  props: portal
    ? [retos, aprendizajes, portal, nota]
    : [retos, aprendizajes, nota],
  colliders: [footprint(0, room.z - NOTE_ENTRY_Z_OFFSET, 1, 1)],  // 1m x 1m
}
```

`footprint(x, z, w, d)` ya existe en `props.ts:64` y genera un `Box2` AABB
centrado en `(x, z)` con ancho `w` y profundidad `d` — ver
`apps/journey/src/lib/collision.ts:9` para el tipo y
`circleIntersectsBox` (`collision.ts:26`) para como se resuelve contra el
jugador (circulo de radio `PLAYER_RADIUS=0.35`).

## 2. Escritorios invasivos — 7 salas a ajustar

Regla uniforme: correr cada `deskSpot` afectado en `+Z` lo necesario para
que su footprint (spot + silla, ~0.8-0.9m de extension hacia -Z) quede
fuera de la franja `[zFront, zFront + 2]` de esa sala. `zFront = room.z -
6.6` (con `ROOM_SIZE=13.2`).

| Sala | Archivo | Spots actuales (x, z relativo a room.z) | Ajuste sugerido |
|------|---------|------------------------------------------|------------------|
| ipasme | `rooms/ipasme.ts` (~L842-846) | `[-1.7,-4.3]` `[0.7,-4.3]` `[-0.5,-2.1]` | Correr los 2 primeros (`-4.3`) a `~-3.3/-3.8` (0.5-1m hacia +Z); el tercero ya esta fuera de la franja |
| iai | `rooms/iai.ts` (~L1069-1073) | `[-1.7,-4.3]` `[0.7,-4.3]` `[-0.5,-2.1]` (identico a ipasme) | Mismo ajuste que ipasme |
| asesoria | `rooms/asesoria.ts` (~L1027-1031) | `[-3.4,-4.2]` `[-1.6,-4.2]` `[-2.5,-2.3]` | Correr los 2 primeros a `~-3.2/-3.7` |
| cofasa | `rooms/cofasa.ts` (~L832-836) | `[-1.7,-4.5]` `[0.7,-4.5]` `[-0.5,-2.3]` | Correr los 2 primeros a `~-3.7/-4.2` (0.3-0.8m) |
| dibal | `rooms/dibal.ts` (~L1183-1186) | `[2.4,-4.9]` `[4.1,-4.9]` | Lateral (x=2.4/4.1), prioridad menor; correr igual a `~-4.0/-4.4` por consistencia |
| goodmeal | `rooms/goodmeal.ts` (~L1144-1148) | `[1.6,-4.8]` `[3.4,-4.8]` `[2.5,-2.9]` | Lateral (x=1.6/3.4), prioridad menor; correr los 2 primeros a `~-3.9/-4.3` |
| destacame | `rooms/destacame.ts` (~L1334-1338) | `[-0.9,-4.8]` `[0.9,-4.8]` `[0.0,-3.0]` | **Caso critico**: correr `[-0.9,-4.8]`/`[0.9,-4.8]` a `~-3.9/-4.3` — quedan cerca del eje central, verificar que no choquen con el pilar nuevo (z del pilar es `room.z - 3.3`, dejar margen) |

> `corpoelec`, `aula` y `futuro` NO requieren ajuste (ya tienen la entrada
> libre — `corpoelec` con spots desde `-1.8`, `aula` sin `officeLayout`,
> `futuro` con spots desde `-2.8`).

## 3. NPCs con `path` conflictivo — 2 salas

### `goodmeal` — NPC "daniela"

Archivo: `rooms/goodmeal.ts` (~L1596-1600). Path actual:

```ts
path: [[0.0, room.z - 3.2], [-1.8, room.z - 1.4], [1.6, room.z + 0.2]]
```

Ajustar el primer waypoint (o insertar uno intermedio) para que no pase por
`x=0` en la z del pilar (`room.z - 3.3` aprox, ver seccion 1). Ejemplo:
desplazar el primer punto a `[0.9, room.z - 3.2]` o insertar un waypoint
que rodee `(0, room.z - 3.3)` con margen >= 0.5m (radio del pilar 0.5m +
margen del NPC).

### `destacame` — NPC "valentina"

Archivo: `rooms/destacame.ts` (~L1909-1913). Path actual inicia en
`[0.4, room.z - 1.4]` y cruza cerca de x=0. Mismo criterio: ajustar el
waypoint mas cercano al pilar para dejar margen >= 0.5m del punto
`(0, room.z - 3.3)`. Ademas revisar el `deskSpot` `[0.0, room.z - 3.0]` de
esta sala (seccion 2) — puede requerir doble ajuste (desk + NPC) por ser el
caso mas apretado.

## 4. Sala `futuro` — verificar coexistencia con pedestal-CTA propio

`futuro` no tiene grieta (`withPortal: false`) pero SI usa `infoKit` (por
ende hereda el cuaderno). Ademas tiene su propio pedestal de CTA/holograma
centrado en el muro final (mismo lenguaje visual del cilindro, ver
`futuro.ts` ~L541-543). Verificar en la implementacion:

- Que el pilar del cuaderno (cerca de la ENTRADA, `room.z - 3.3`) y el
  pedestal-CTA (cerca del MURO FINAL, z alto) no se superpongan — deberian
  estar a >6m de distancia por diseño (entrada vs fondo de sala).
- Que ambos colliders conviven sin overlap (`footprint` del cuaderno 1x1
  vs el collider existente del CTA).

## 5. Checklist de verificacion visual por sala (adicional a AC)

Adjuntar al recorrido de la seccion 11: por cada una de las 10 salas,
confirmar que al entrar el jugador ve el pilar de frente/cerca y debe
desviarse (izq o der) para continuar, sin quedar "atascado" (dejar >= 1.5m
libres a cada lado del pilar dentro del ancho de la sala, que es 13.2m —
sobra espacio de sobra).
