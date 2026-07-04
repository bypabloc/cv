# 02 — Motor vanilla y carga por esclusa

> Seccion 4 del plan (flujos antes/despues) + arquitectura del motor.
> El corazon del refactor: un solo RAF, zone manager con dispose real,
> precarga en pasillo y fade hibrido.

## 4. Diagrama de flujo (antes y despues)

### Antes (R3F)

```text
[index.astro] -> isla React client:only
   -> Journey3D.tsx (detect tier) -> lazy(JourneyApp)
      -> <Canvas> R3F (ACES->AgX, IBL PMREM, shadows soft)
         -> Structure (TODOS los muros/pisos/techos/luces SIEMPRE)
         -> RoomContents (monta sala actual + ADYACENTES via React.lazy)
         -> PlayerControls (solo POV PointerLock)
         -> Hud (React DOM overlay)
   * dispose: implicito de React (parcial; estructura y texturas viven)
```

### Despues (vanilla)

```text
[index.astro] -> <div id="journey-root" data-locale> + <script> boot
   -> lib/boot.ts (detect tier; static -> NADA)
      -> loader "Cargando el mundo 3D…" -> import('../engine/app') [chunk 3D]
         -> engine/app.ts: renderer + scene + luces + RAF unico
            -> world.ts (zone manager):
                 mounted = { shells: activa+adyacentes, content: 1 sala }
            -> controls.ts (3a persona default / POV / touch / tour)
            -> hud.ts (DOM puro, i18n)
   * salir -> dispose TOTAL (renderer, listeners, DOM) + boton re-entrada
```

### Flujo de zona (esclusa + fade)

```text
        [Sala i] --camina--> {umbral pasillo i}
                                  |
                                  v
                    +-----------------------------+
                    | zona = pasillo i            |
                    | 1. dispose CONTENT sala i   |
                    | 2. preload CONTENT sala i+1 |
                    |    (import chunk + build +  |
                    |     renderer.compile)       |
                    +-----------------------------+
                                  |
                     puerta i (E para abrir)
                                  |
                        {preload listo?}
                         /            \
                       si              no
                        |               |
                 cruza directo    fade 300-400ms
                        |          hasta ready
                        v               v
                    [Sala i+1: shell ya visible, content montado]

  * volver atras: zona sala i sin content -> fade + rebuild (procedural)
  * teleport (M) / portal al pasado: siempre con fade
```

## Arquitectura de archivos del motor

```text
apps/journey/src/
├── lib/
│   ├── boot.ts          # NUEVO: entry liviano (sin three): tier + mount/exit
│   ├── rooms.ts         # SE MANTIENE (data del CV)
│   ├── layout.ts        # SE MANTIENE (coordenadas encadenadas + wallBoxes)
│   ├── collision.ts     # SE MANTIENE (circulo vs AABB + interactables)
│   ├── tiers.ts         # SE MANTIENE (deteccion pura)
│   ├── tour.ts          # SE MANTIENE (riel por tiempo)
│   └── site-config.ts   # SE MANTIENE
├── engine/              # NUEVO: motor vanilla (chunk 3D)
│   ├── app.ts           # startJourney(): renderer/escena/luces/loop/wiring
│   ├── state.ts         # estado plano + registro de interactables (sin libs)
│   ├── toon.ts          # gradientes, pool de materiales toon, outline,
│   │                    #   canvas textures ink, labels, disposeDeep
│   ├── themes.ts        # THEMES por sala/pasillo/pasado (manga-ink)
│   ├── world.ts         # WORLD manifest + shells + zone manager + preload
│   ├── character.ts     # generador de personajes anime (jugador + NPCs)
│   ├── controls.ts      # input teclado/mouse/touch + camaras 3a/POV + tour
│   ├── hud.ts           # HUD DOM completo (i18n)
│   ├── audio.ts         # MOVIDO desde components/three/ambient-audio.ts
│   └── rooms/
│       ├── aula.ts      # factory sala 0 (chunk propio via dynamic import)
│       ├── corpoelec.ts # factory sala 1
│       ├── cima.ts      # factory sala 2
│       └── past.ts      # factory de las mini-salas del pasado
└── components/          # SE ELIMINA COMPLETO (React/R3F)
```

## Contratos principales (firmas)

```ts
// engine/app.ts
export interface JourneyHandle { dispose(): void }
export function startJourney(opts: {
  container: HTMLElement
  tier: 'full' | 'reduced'
  locale: Locale
  onExit: () => void
}): JourneyHandle

// engine/world.ts — manifest data-driven (agregar sala = 1 entrada + 1 factory)
export interface RoomBuild {
  group: Group
  interactables: Interactable[]
  update?(t: number, dt: number): void
  dispose(): void            // libera SOLO lo propio (no el pool toon)
}
export type RoomFactory = (ctx: RoomCtx) => RoomBuild
export const WORLD: Record<RoomId, {
  load: () => Promise<{ default: RoomFactory }>   // dynamic import => chunk/sala
}>

// engine/state.ts — estado plano, sin libs
export interface EngineState {
  tier: 'full' | 'reduced'; locale: Locale
  zone: Zone; past: number | null
  doorsOpen: Set<number>
  cameraMode: 'third' | 'pov'
  ui: 'none' | 'ficha' | 'contact' | 'teleport'
  ficha: { roomIndex: number; kind: 'retos' | 'aprendizajes' } | null
  audioOn: boolean; tourOn: boolean
  interactables: Map<string, Interactable>; activeId: string | null
}
```

El motor es dueño del estado y llama metodos del HUD directamente
(`hud.setZoneLabel(...)`, `hud.showPrompt(...)`) — sin pub/sub ni store.

## Zone manager (world.ts) — reglas exactas

Estado interno: `shells: Map<ZoneKey, Group>`, `contents: Map<number,
RoomBuild>`, `pending: Map<number, Promise<RoomBuild>>` (ZoneKey =
`room-N` | `corridor-N` | `past-N`).

Al cambiar `zone` (lo reporta controls con `zoneAt`):

| Nueva zona | Shells montados | Content montado | Acciones |
|------------|-----------------|-----------------|----------|
| `room-i` | room i, corridor i-1, corridor i | sala i | si falta content i: fade + build; dispose contents != i |
| `corridor-i` | corridor i, room i, room i+1 | sala i+1 (preload) | dispose content sala i; `preload(i+1)` |
| `past-i` (portal) | past i | past i | fade siempre; al salir: dispose past + restaurar sala i |

- Los **shells** (muros/piso/techo/puerta/año del pasillo) se construyen
  con las MISMAS `WallBox` de `layout.ts` (visual == colision) y se
  cachean: montar/desmontar es add/remove del scene graph; dispose de shell
  solo al salir de la experiencia. Costo GPU minimo (cajas + 2-3 texturas
  ink compartidas por theme).
- El **content** (props/NPCs/interactables/micro-interacciones) es lo que
  se paga: 1 solo content de sala vivo (regla de memoria de la guia).
- `preload(i)`: `WORLD[id].load()` (descarga el chunk si es la 1a vez) →
  `factory(ctx)` → `group.visible = true` montado detras de la puerta +
  `renderer.compile(scene, camera)` para calentar shaders. Los materiales
  toon del pool ya estan compilados tras la sala 1 → el compile es barato.
- **Colision**: el array completo de `WallBox` + bloqueadores de puertas
  cerradas vive SIEMPRE (son datos, no GPU) — igual que hoy.
- `dispose()` de RoomBuild: `disposeDeep(group)` que libera geometrias,
  materiales y texturas EXCEPTO los marcados `userData.shared === true`
  (pool toon, gradientes, geometrias unitarias compartidas).

## Renderer y presupuesto

| Ajuste | full (desktop) | reduced (movil) |
|--------|----------------|-----------------|
| DPR | `min(devicePixelRatio, 2)` | `min(devicePixelRatio, 1.5)` |
| Antialias | on | on (geometria simple; si FPS < 30 sostenido → recrear sin AA no aplica: bajar DPR a 1) |
| Sombras | 1 directional, mapSize 1024, frustum ceñido a la zona activa | OFF — blob shadows |
| Tone mapping | `NoToneMapping` (colores planos manga) | idem |
| Luces | hemi + dir + max 1 acento/sala | hemi + dir |
| Anisotropy | 4 | 2 |
| Draw calls/zona | < 100 (medir con `renderer.info`) | < 80 |
| Degradacion automatica | si FPS medio < 30 por 5 s: DPR -= 0.25 (piso 1) y apagar acento | idem |

Un solo `requestAnimationFrame` (clock con `dt` clampeado a 0.05):
`controls.update(dt)` → `world.update(t, dt)` (anims de sala + NPCs +
puertas) → `hud tick` (solo si cambio algo) → `renderer.render`.

En `import.meta.env.DEV`: cada 5 s `console.debug('[journey]',
renderer.info.render.calls, renderer.info.memory)` (AC-14).

## Que se elimina del pipeline actual

| Hoy (R3F) | Refactor |
|-----------|----------|
| PMREM + RoomEnvironment (IBL) | fuera — toon no lo usa |
| AgX tone mapping + exposure | `NoToneMapping` |
| `shadows="soft"` + 1 pointLight castShadow por sala | 1 directional (desktop) / blob (movil) |
| 3 salas montadas (React.lazy adyacentes) | 1 content + shells adyacentes |
| troika-three-text + fuente woff | labels canvas (strokeText tinta) |
| zustand store | estado plano en engine/state.ts |
| ShadowGroup traverse por mount | flags cast/receive al construir |
| anisotropy 16 | 4 (2 en movil) |
