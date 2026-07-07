# Feature D — Puerta sin túnel, cruce automático con efecto "viaje al futuro"

> AC-11 a AC-14. Ver contexto general y diagrama antes/después en
> [01-contexto-y-decision.md](01-contexto-y-decision.md).

## Diagnóstico (recordatorio)

- El pasillo hoy es un shell propio (`buildCorridorShell`,
  `world.ts:401-466`) que renderiza: muros laterales (`sideBoxes`,
  derivados de `layout.wallBoxes` con `source.kind === 'corridor'`),
  dinteles sobre la puerta (`headerSpecs`, `world.ts:374-399`, con el
  material/tema del PASILLO), piso, techo (`CORRIDOR_HEIGHT=2.6`, mucho
  más bajo que `room.height=4.24`), letrero de año en el piso y luz de
  acento.
- El "bloque de techo discontinuo" es el salto de altura/material entre
  el techo de la sala (4.24, tema de la sala) y el dintel del pasillo
  (2.6, `THEMES.corridor`, mucho más oscuro) justo sobre el vano.
- Las "barras" laterales son los 2 muros del pasillo: angostos
  (`WALL_THICKNESS=0.2`), bajos (2.6) y mucho más angostos que la sala
  (2.4 de ancho de pasillo vs. 13.2 de la sala) — un cuello de botella
  visual junto a la puerta.
- La transición sala-a-sala HOY es caminata real: `controls.ts`
  detecta el cambio de zona por posición Z (`zoneAt`) y dispara
  `world.setZone(...)` → `applyZone(...)` (la "esclusa": libera el
  contenido de la sala anterior y precarga la siguiente). El único
  teletransporte que existe hoy es `world.teleportToRoom(index)`, usado
  por el menú de teleport del HUD — no por la puerta.
- `hud.fade(on, mode)` ya soporta un efecto de transición reusable
  (`'dark'` u opacidad simple, `'dream'` con whiteout+blur ~560/650ms,
  usado hoy por `enterPast`/`exitPast` como "viaje al pasado").

## Diseño

### 1. `buildCorridorShell` se reduce a solo la puerta

```ts
// ANTES (world.ts:401-466): muros + piso + techo + letrero + luz + puerta
function buildCorridorShell(index: number): Group {
  const group = new Group()
  const corridor = layout.corridors[index]
  const door = layout.doors[index]
  if (!corridor || !door) return group
  // ...sideBoxes + headerSpecs fusionados con mergedBoxes...
  // ...floorMesh, ceilingMesh, year label, accentLight...
  group.add(walls, floorMesh(...), ceilingMesh(...), buildDoor(door))
  // ...
  return group
}
```

```ts
// DESPUES: solo la puerta (nada de muros/piso/techo/letrero/luz)
function buildCorridorShell(index: number): Group {
  const group = new Group()
  const door = layout.doors[index]
  if (!door) return group
  group.add(buildDoor(door))
  return group
}
```

`buildDoor` (world.ts:350-371) no cambia — ya es "solo la hoja + manija,
sin marco" (el comentario del propio código ya dice que los pilares
laterales se habían eliminado antes). El "marco" visual que queda es el
hueco recortado en el muro de la sala (`crossWall`, `layout.ts:130-147`),
que SÍ se mantiene sin cambios.

`headerSpecs`, `sideBoxes`, el `floorMesh`/`ceilingMesh`/año/luz de
acento del pasillo dejan de usarse dentro de esta función (se eliminan
sus llamadas; no hace falta borrar `THEMES.corridor` ni las constantes
de `layout.ts` — quedan sin romper nada, ver Decisión 2 en el capítulo
1). Esto elimina por construcción el "bloque de techo discontinuo"
(AC-13: ya no hay dintel de pasillo) y las "barras" laterales (AC-13: ya
no hay `sideBoxes`) — y de paso resuelve AC-12 (sin geometría de pasillo
visible).

### 2. `world.init()` — el interactable de la puerta pasa a async

```ts
// ANTES (world.ts:716-725)
for (const door of layout.doors) {
  registerInteractable(state, {
    id: `door-${door.corridorIndex}`,
    x: door.x, z: door.z, radius: 2.1,
    label: { es: 'Abrir la puerta', en: 'Open the door' },
    onActivate: () => world.openDoor(door.corridorIndex),
  })
}
```

```ts
// DESPUES: registra una función que arma el interactable (para poder
// re-registrarlo tras cada cruce, ya que el ciclo completo lo cierra).
function registerDoorInteractable(door: DoorLayout): void {
  registerInteractable(state, {
    id: `door-${door.corridorIndex}`,
    x: door.x, z: door.z, radius: 2.1,
    label: { es: 'Abrir la puerta', en: 'Open the door' },
    onActivate: () => {
      void world.crossDoor(door.corridorIndex)
    },
  })
}
// en world.init(): for (const door of layout.doors) registerDoorInteractable(door)
```

### 3. `world.crossDoor(index)` — nuevo método de la API (reemplaza el
   comportamiento de `openDoor`, que queda como paso interno)

```ts
async crossDoor(index) {
  if (state.doorsOpen.has(index)) {
    return // ya hay un cruce en curso
  }
  const target = layout.rooms[index + 1]
  if (!target) {
    return
  }
  unregisterInteractable(state, `door-${index}`)
  state.doorsOpen.add(index)              // hoja gira a abierta (lerp existente)
  sfx.play('door')
  await wait(320)                          // deja ver el giro antes del fade
  sfx.play('whoosh')
  await deps.fade(true, 'warp')            // efecto "viaje al futuro"
  deps.teleportPlayer(0, target.z - target.depth / 2 + 1.5)
  state.zone = { kind: 'room', index: index + 1 }
  await applyZone(state.zone, false)       // misma esclusa que ya usa teleportToRoom
  deps.onZoneApplied?.()
  await deps.fade(false, 'warp')
  state.doorsOpen.delete(index)            // hoja cierra (lerp existente)
  sfx.play('door')
  const door = layout.doors[index]
  if (door) {
    registerDoorInteractable(door)         // vuelve a ser interactuable (AC-14)
  }
},
```

`wait(ms)` es un helper trivial (`new Promise((r) => setTimeout(r, ms))`)
si no existe ya uno en el módulo — revisar antes de agregarlo (evitar
duplicar si `world.ts` ya tiene un equivalente).

Este método reutiliza EXACTAMENTE el mismo patrón que
`teleportToRoom`/`enterPast`/`exitPast` (fade → mutación de estado →
`applyZone` → fade inverso) — cero mecanismo nuevo de zona/esclusa.

### 4. Nueva variante de `hud.fade`: `'warp'`

```ts
// ANTES (hud.ts:795-806)
fade(on, mode = 'dark') {
  if (mode === 'dream') {
    dreamEl.classList.toggle('on', on)
    return new Promise((resolve) => window.setTimeout(resolve, on ? 560 : 650))
  }
  fadeEl.style.opacity = on ? '1' : '0'
  return new Promise((resolve) => window.setTimeout(resolve, 380))
},
```

```ts
// DESPUES: rama nueva 'warp' (mismo contrato: toggle de clase CSS +
// Promise que resuelve tras la duracion de la transicion)
fade(on, mode = 'dark') {
  if (mode === 'dream') { /* igual */ }
  if (mode === 'warp') {
    warpEl.classList.toggle('on', on)
    return new Promise((resolve) => window.setTimeout(resolve, on ? 420 : 480))
  }
  /* rama 'dark' igual */
},
```

`warpEl` es un nuevo `<div class="jny-warp">` montado junto a
`dreamEl`/`fadeEl` en la construcción del HUD, con su propio bloque CSS
(franja de luz azul/cian + leve zoom-blur, distinto del whiteout sepia
de `'dream'` para no confundir "viaje al pasado" con "viaje al futuro").
Es un efecto puramente CSS (gradiente + transición de opacidad/blur),
sin canvas ni JS de animación nuevo.

### 5. Qué NO cambia (alcance explícito)

- `lib/layout.ts`: `ROOM_SIZE`, `CORRIDOR_WIDTH/LENGTH/HEIGHT`,
  `layout.corridors`, `layout.doors`, `buildWallBoxes` — sin cambios. El
  hueco/franja sigue existiendo como dato (lo usa `applyZone`/`focusShadow`/
  el tour), solo deja de caminarse y de renderizarse.
- `Zone` (`'room' | 'corridor'`) y `zoneAt` — sin cambios. En juego
  normal, `zoneAt(pos.z)` nunca vuelve a devolver `'corridor'` (el
  teletransporte salta directo de una sala a la otra), pero el código
  sigue siendo válido — no se borra por prudencia (bajo riesgo de romper
  el tour guiado, que sí interpola posiciones de puerta como waypoint).
- `tour.ts`: sin cambios. El riel del tour (`tourPoseAt`) interpola
  posiciones libres de cámara, no depende de que haya geometría de
  pasillo — con el pasillo vacío, la cámara guiada simplemente atraviesa
  un tramo sin nada que ver, en vez de un pasillo con bugs visuales
  (mejora indirecta, no requiere cambio de código).
- `THEMES.corridor`, `CORRIDOR_HEIGHT`, etc. quedan declarados pero sin
  uso dentro de `buildCorridorShell`; no se eliminan en este plan
  (limpieza opcional fuera de alcance, no bloquea ningún AC).

## Verificación de la feature

- Typecheck (`astro check`).
- Smoke visual (headed, con audio si es posible) en al menos 2 cruces de
  sala consecutivos:
  1. Acercarse a la puerta, confirmar prompt `[E] Abrir la puerta`.
  2. Pulsar `E` → confirmar: la hoja gira, un instante después aparece el
     efecto "warp", el jugador aparece en la sala siguiente, el efecto
     se desvanece y la puerta (vista desde la sala nueva o al volver) se
     ve cerrada.
  3. Confirmar visualmente que en el tramo entre salas ya NO hay muros
     laterales, techo ni piso distinto — solo el vano recortado en la
     pared.
  4. Repetir en la última puerta del recorrido (antes de `futuro`) para
     confirmar que el índice `+1` no rompe en el borde final.
  5. Medir draw calls de 2 salas (antes/después de la puerta) para
     confirmar que la simplificación de `buildCorridorShell` no afecta
     el presupuesto de la sala en sí (el pasillo nunca contaba para el
     presupuesto POR SALA, pero conviene confirmar que no quedó ningún
     recurso huérfano sin `dispose`).
