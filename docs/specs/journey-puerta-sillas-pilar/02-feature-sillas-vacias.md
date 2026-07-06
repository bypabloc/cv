# Feature A — Sentarse en cualquier silla vacía

> AC-1 a AC-5. Ver contexto general en
> [01-contexto-y-decision.md](01-contexto-y-decision.md).

## Diseño

### 1. Estado del jugador (`engine/state.ts`)

Nuevo campo en `EngineState`:

```ts
export interface SeatTarget {
  x: number
  z: number
  rotationY: number
}

export interface EngineState {
  // ...campos existentes...
  /** Silla donde esta sentado el jugador, o null si esta de pie. */
  playerSeat: SeatTarget | null
}
```

Inicializado a `null` en `createEngineState`. No hace falta un helper
adicional: los sitios que lo usan (props.ts al crear el interactable,
controls.ts al leerlo cada frame) lo mutan/leen directo, igual que
`state.ui`/`state.past` hoy.

### 2. `officeLayout` expone sillas vacías (`engine/rooms/props.ts`)

`officeLayout` ya sabe, por construcción, qué índices de `spots` NO
tienen NPC (`!powered.has(index)` — el mismo criterio que arma
`toggles`). Se agrega un campo `seats` al retorno:

```ts
export interface OfficeLayout {
  group: Group
  colliders: Box2[]
  toggles: { spot: number; screen: ScreenSwap }[]
  /** Interactables de "sentarse" para los puestos SIN NPC (silla vacia). */
  seats: Interactable[]
  dispose(): void
}

export function officeLayout(opts: {
  spots: readonly (readonly [number, number])[]
  color: string
  poweredSpots?: ReadonlySet<number>
  screenTheme: Pick<RoomTheme, 'screenBg' | 'screenFg' | 'ink'>
  screenFor?: (index: number) => { title: string; lines: readonly string[] }
  /** Identificador de la sala, para ids unicos del interactable. */
  roomIndex: number
  /** Estado del motor: el toggle de sentarse muta state.playerSeat
   *  directo (ver seccion 4, no hace falta una accion nueva). */
  state: EngineState
}): OfficeLayout
```

Dentro de `officeLayout`, junto al loop que ya arma `toggles`
(props.ts:1013-1036), por cada índice SIN NPC se agrega también un
`Interactable` de silla, en `(x, z - 0.55)` (mismo offset que ya usa
`chairParts`), con el patrón toggle (label cambia entre "Sentarse" y
"Levantarse", igual que las laptops cambian entre "Encender"/"Apagar"):

```ts
const SIT_LABEL = { es: 'Sentarse', en: 'Sit down' } as const
const STAND_LABEL = { es: 'Levantarse', en: 'Stand up' } as const

// dentro del forEach de opts.spots, cuando !powered.has(index):
const seatX = x
const seatZ = z - 0.55
const item: Interactable = {
  id: `silla-${opts.roomIndex}-${index}`,
  x: seatX,
  z: seatZ,
  radius: 1.4,
  label: { ...SIT_LABEL },
  onActivate: () => {
    const sameSeat =
      opts.state.playerSeat?.x === seatX && opts.state.playerSeat?.z === seatZ
    opts.state.playerSeat = sameSeat ? null : { x: seatX, z: seatZ, rotationY: 0 }
    item.label = sameSeat ? { ...SIT_LABEL } : { ...STAND_LABEL }
  },
}
seats.push(item)
```

> Nota de implementación: el toggle lee el estado REAL de
> `opts.state.playerSeat` en vez de un flag local — así, si el jugador se
> sienta en OTRA silla primero y luego vuelve a esta, el label no queda
> desincronizado. Es el mismo espíritu que el toggle de `laptopToggles`
> pero mutando `EngineState` en vez de una variable de closure, porque
> "sentado" es estado compartido con `controls.ts` (que lo lee cada
> frame), no un detalle interno de la silla. Un cambio de sala reconstruye
> las salas (y sus interactables) desde cero, así que el label arranca
> siempre sincronizado — cubierto por AC-5 (limpieza de `playerSeat` al
> cambiar de zona re-crea las salas, y con
> ellas sus interactables, desde cero).

### 3. Congelar movimiento y aplicar pose (`engine/controls.ts`)

En `applyMovement` (o el punto equivalente donde se lee `keys`/`joy`),
agregar guard temprano:

```ts
function applyMovement(dt: number): boolean {
  if (state.playerSeat) {
    return false // sentado: sin WASD
  }
  // ...resto igual...
}
```

Y en el loop de `update`/donde se aplica la pose al jugador (cerca de
`player.setWalking(...)`), si `state.playerSeat` está activo:

```ts
if (state.playerSeat) {
  pos.x = state.playerSeat.x
  pos.z = state.playerSeat.z
  player.group.position.set(pos.x, 0, pos.z)
  player.group.rotation.y = state.playerSeat.rotationY
  player.setPose('sit')
} else if (/* rama existente de idle/walk */) {
  // ...
}
```

`player.setPose('sit')` ya existe (reusa `poseSeated` de
`character.ts:543-562`, la misma que usan los NPCs). No hace falta
tocar `character.ts`.

### 4. `onSit`: no hace falta una acción nueva en `world.ts`

`RoomCtx.state: EngineState` YA se pasa completo a cada sala
(`world.ts:78-85`, desestructurado en cada `build*(ctx)` como
`const { def, room, theme, state, actions } = ctx`), y `props.ts` YA
importa tipos desde `../state` (`Interactable`, `FichaKind`,
`ShowcaseRef`, `ShowcaseView`). No hace falta inventar una
`WorldActions.sitAt` nueva: `officeLayout` recibe `state: EngineState`
como una opción más (mismo import, sin nueva indirección) y su
`onActivate` muta `state.playerSeat` directo — igual de simple que
`item.label = powered ? ... : ...` en `laptopToggles`, pero mutando el
estado compartido en vez de una variable local:

```ts
onActivate: () => {
  const here = { x: seatX, z: seatZ, rotationY: 0 }
  const sameSeat =
    state.playerSeat?.x === seatX && state.playerSeat?.z === seatZ
  state.playerSeat = sameSeat ? null : here
  item.label = sameSeat ? { ...SIT_LABEL } : { ...STAND_LABEL }
},
```

Cada sala solo necesita pasar el `state` que ya tiene en su `ctx` al
llamar `officeLayout({ ..., roomIndex: room.index, state })` — no hay
wiring nuevo en `world.ts`/`app.ts`, y por lo tanto la Feature A NO toca
`engine/world.ts` en absoluto.

### 5. Sala `aula` (layout a mano, sin `officeLayout`)

`aula.ts` no llama a `officeLayout`; construye sus pupitres+sillas con
`outlinedMergedBoxes` directo (aula.ts:296-310). Se agregan
interactables de silla para:

- `deskSpots[1]` y `deskSpots[2]` (índices fuera de `NPC_PCS = {0, 3}`):
  tu PC y la del laboratorio.
- Los 4 `emptySpots` (pupitres decorativos sin monitor).

Mismo mecanismo que la sección 4 (mutar `state.playerSeat` directo,
`state` ya disponible en `ctx`), con ids `silla-aula-<roomIndex>-<index>`
y posición `(x, z-0.55)`. El escritorio del profesor (`[-2,
room.z+3.6]`, silla en `room.z+4.15` con `dir=-1`) queda EXCLUIDO: lo
ocupa el NPC `profesor` (pose `'sit'`, aula.ts:474-487) — no es una
silla vacía.

## Verificación de la feature

- Typecheck: `pnpm --filter @portfolio/journey exec astro check`.
- Smoke visual (headed o headless, ver
  [11-verificacion-e2e.md](11-verificacion-e2e.md)): en al menos 2 salas
  con `officeLayout` (ej. `cofasa`, `destacame`) + en `aula`:
  1. Acercarse a una silla vacía, confirmar el prompt `[E] Sentarse`.
  2. Pulsar `E`, confirmar pose sentado + WASD sin efecto.
  3. Pulsar `E` de nuevo, confirmar que se levanta y WASD vuelve a mover.
  4. Acercarse a una silla CON NPC, confirmar que NO aparece el prompt de
     sentarse (solo el de hablar con el NPC, si aplica).
  5. Sentarse y, sin levantarse, cruzar la puerta (o usar el menú
     teleport del HUD) — confirmar que la sala nueva no arranca con el
     jugador congelado.
