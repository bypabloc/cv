# 04 — Personajes procedurales anime + camaras y controles

> Materializa las decisiones 4 (3a persona default + POV), 6 (personajes
> 100% procedurales, detallados y distinguibles) y 7 (joystick + tour en
> movil).

## engine/character.ts — generador de personajes

Un solo builder parametrizado construye al jugador y a todos los NPCs:

```ts
export interface CharacterSpec {
  skin: string
  hair: { style: 'short' | 'spiky' | 'ponytail' | 'bun'; color: string }
  top: string; bottom: string
  accessory?: 'helmet' | 'glasses' | 'tie' | 'badge'
  faceSeed: number          // varia ojos/cejas/boca deterministicamente
}
export interface CharacterHandle {
  group: Group
  setWalking(on: boolean): void
  update(t: number, dt: number): void   // walk cycle / idle / parpadeo
  setVisible(on: boolean): void         // POV oculta al jugador
  dispose(): void                       // texturas de cara propias
}
export function makeCharacter(spec: CharacterSpec): CharacterHandle
export function makeNpc(opts: CharacterSpec & {
  position: [number, number, number]
  path?: readonly [number, number][]    // >= 2 waypoints -> patrulla
  rotationY?: number; speed?: number
}): NpcHandle                           // { group, update, dispose }
```

### Anatomia (proporciones chibi ~1.5 m, todo toon + outline)

- **Cabeza**: esfera r=0.22 (grande, canon anime) piel toon.
- **Cara**: plane 0.30x0.24 pegado al frente de la cabeza con CanvasTexture
  TRANSPARENTE (128 px): ojos grandes estilo anime (ovalo negro + brillo
  blanco + parpado superior segun faceSeed), cejas (trazo tinta), boca
  pequeña, rubor opcional. DOS texturas por personaje: ojos abiertos y
  cerrados — el parpadeo hace swap 120 ms cada 3-6 s (fase por faceSeed).
- **Pelo** (lo que mas distingue): casquete (esfera achatada) + flequillo
  segun estilo — `short` (casquete + 2 mechones), `spiky` (5-7 conos),
  `ponytail` (casquete + cilindro caido atras con leve sway animado),
  `bun` (casquete + esfera arriba). Color libre por spec.
- **Cuerpo**: torso capsula/box (top), caderas + piernas con pivote en
  cadera (bottom), brazos con pivote en hombro, zapatos oscuros.
- **Accesorios**: `helmet` (casquete amarillo sobre el pelo — corpoelec),
  `glasses` (dibujadas en el canvas de cara), `tie`/`badge` (box pequeño en
  el torso).
- **Outline**: inverted hull negro en cabeza/pelo/torso/extremidades
  (piezas <= 10 → costo trivial).
- **Blob shadow**: circle plane r=0.35 `#000` alpha 0.28 bajo el personaje
  — SIEMPRE en reduced; en full lo da la sombra direccional (blob apagado).

### Animacion (por codigo, sin skinning)

- `walk`: swing seno de piernas/brazos (fase opuesta) + bob 0.03 + leve
  lean adelante. `idle`: respiracion (escala torso 1±0.01), sway suave,
  parpadeo, mirar al jugador si esta a < 3 m (`lookAt` amortiguado, solo
  cabeza ±0.6 rad).
- Patrulla: se PORTA `moveAlongPath` del Npc.tsx actual (waypoints en loop
  + orientacion al tramo).

### Reparto (specs concretos, todos distintos — AC-7)

| Personaje | Spec |
|-----------|------|
| **Jugador** | short negro, hoodie azul `#0052cc`, jeans, badge |
| Aula: estudiante 1 | ponytail castaño, sueter verde, idle en pupitre |
| Aula: estudiante 2 | spiky negro, camisa ocre, idle |
| Aula: estudiante 3 | bun oscuro, sueter azul, patrulla |
| Corpoelec: tecnico 1 | short + HELMET amarillo, overol azul, idle |
| Corpoelec: tecnico 2 | spiky + HELMET, overol verde oliva, patrulla |
| Cima: dev 1 | ponytail, blusa azul marino + tie, idle (reunion) |
| Cima: dev 2 | short, hoodie gris, glasses, idle |
| Cima: dev 3 | bun, camisa azul `#0e3a80`, patrulla |

## engine/controls.ts — camaras e input

```ts
export function createControls(deps: {
  camera: PerspectiveCamera; player: CharacterHandle
  layout: JourneyLayout; walls: readonly WallBox[]
  state: EngineState; hud: Hud; canvas: HTMLCanvasElement
}): { update(dt: number): void; dispose(): void }
```

### Modo 3a persona (default, AC-5)

- Camara orbita al jugador: `yaw` (drag horizontal) + `pitch` clampeado
  [-0.15, 0.55], distancia base 4.2, altura 2.2, `lookAt` cabeza (y=1.2).
  Seguimiento con lerp exponencial (`1 - 0.001^dt`, como el prototipo).
- **Movimiento relativo a camara**: WASD/joystick se proyectan sobre el
  yaw; el personaje ROTA hacia la direccion de movimiento
  (`atan2`) y camina (walk cycle on).
- **Camara vs muros**: clamp del punto de camara al rectangulo de la zona
  activa (margen 0.35) usando el layout; en pasillo la distancia se reduce
  automaticamente hasta caber (min 1.6). Sin raycast: los volumenes son
  cajas conocidas.
- Desktop: drag con pointer (sin pointer-lock). Movil: drag fuera del
  joystick.

### Modo POV (V o boton HUD)

- Pointer-lock al click (igual que hoy), camara en `EYE_HEIGHT` sobre la
  posicion del jugador, `player.setVisible(false)`.
- Mismo `resolveMovement` (circulo vs AABB + puertas cerradas) — la
  colision es identica en ambos modos (AC-5).
- Al volver a 3a persona: exit pointer-lock, visible on, camara re-encaja
  detras del yaw actual.

### Teclas / gestos

| Input | Accion |
|-------|--------|
| WASD / flechas / joystick | caminar |
| drag (mouse o touch fuera del joystick) | girar camara (yaw/pitch) |
| E / boton accion tactil | interactuar (puerta, ficha, micro, portal, CTA) |
| V / boton HUD | alternar 3a persona <-> POV |
| M / boton HUD | menu de teletransporte |
| Escape | cerrar paneles / soltar pointer-lock |

### Interaccion por proximidad

Se porta el sistema actual: `nearestInteractable` (lib/collision) sobre el
registro de `state.interactables` cada frame; el HUD muestra el prompt del
activo; E ejecuta `onActivate`. En 3a persona no hay crosshair (el prompt
basta); en POV se conserva el punto central.

### Tour (riel opcional — AC-8)

- `startTour()`: abre todas las puertas, fija `cameraMode='third'`,
  y por frame mueve AL JUGADOR con `tourPoseAt` (lib/tour.ts sin tocar);
  la camara 3a persona lo sigue sola. Paneles abiertos congelan el riel
  (offset acumulado, igual que GuidedTour actual).
- `stopTour()`: devuelve el control. Cualquier input de movimiento tambien
  detiene el tour.
- El boton Tour vive en el HUD; visible SIEMPRE en reduced, y en full solo
  si `?tour` (querystring) — evitar ruido en desktop.

### Touch (port del prototipo)

- Joystick DOM (circulo 120 px, stick 52 px) esquina inferior izquierda +
  boton de accion circular derecha. `pointer: coarse` los muestra.
- Drag en el resto de la pantalla gira la camara.
- `touch-action: none` en los controles; el canvas no scrollea.
