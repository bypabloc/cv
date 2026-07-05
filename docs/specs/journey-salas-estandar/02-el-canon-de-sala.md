# 02 — El canon de sala (el estandar reutilizable)

> [<- 01 Contexto](01-contexto-y-decision.md) · [Salas ->](03-salas.md)

Este archivo define el ESTANDAR que replican todas las salas: los 4 helpers
nuevos en `props.ts`, la estructura fija de una sala presente y de un pasado,
y la paleta paredes-blancas. Es la fuente de verdad tecnica del plan y del
que se promueve la rule `.claude/rules/journey-rooms.md`.

## Estructura fija de una sala PRESENTE (canon)

Toda sala presente (menos Aula, que no tiene showcase) se compone de:

```text
+------------------------------------------------------------------+
|  MURO FONDO (+Z)                                                  |
|   [ cuadros de rubro / wallArt ]      [ CTA/holograma si aplica ] |
|                                                                  |
|   officeLayout: filas de escritorios + sillas + laptops          |
|   (gente sentada usando laptops)                                 |
|                                                                  |
|   [ props firma del rubro ]     [ seccion especifica del rubro ] |
|                                                                  |
|  MURO -X: RETOS (infoKit)          MURO +X: APRENDIZAJES (infoKit)|
|  grieta al pasado (izq)            cuaderno-reseña (der)          |
|                                                                  |
|  [ softwareShowcase junto a la PUERTA al pasillo ]               |
+---------------------- PUERTA al pasillo (-Z) --------------------+
```

Elementos obligatorios (AC-3, AC-5..AC-8):

1. **`officeLayout`** — filas de escritorios + sillas + laptops (fusionadas).
2. **`npcCoworkers`** — 4-5 NPCs conversables (2 enfoques).
3. **`wallArt`** — 2-4 cuadros de rubro, ≥1 inspeccionable.
4. **`softwareShowcase`** — monitor Canvas + panel HTML junto a la puerta.
5. **`infoKit`** (ya existe) — RETOS/APRENDIZAJES/grieta/cuaderno, posiciones
   canonicas.
6. **props firma del rubro** — geometria propia de la sala (ver
   [03-salas.md](03-salas.md)).

## Los 4 helpers nuevos (en `engine/rooms/props.ts`)

Firmas propuestas, siguiendo el estilo de los helpers existentes (retornan
`Group`/`PropHandle`/structs, fusionan con `outlinedMergedBoxes`).

### `officeLayout` — filas de oficina fusionadas

```ts
export function officeLayout(opts: {
  /** Centros [x,z] de cada puesto de escritorio. */
  spots: readonly (readonly [number, number])[]
  /** Color del mobiliario (acento del rubro por defecto ink). */
  color: string
  /** Puestos (indice en spots) que llevan laptop ENCENDIDA (NPC sentado). */
  poweredSpots?: ReadonlySet<number>
  /** Tema para las pantallas de las laptops encendidas. */
  screenTheme: Pick<RoomTheme, 'screenBg' | 'screenFg' | 'ink'>
  /** Contenido de pantalla por puesto (loop de codigo del rubro). */
  screenFor?: (index: number) => { title: string; lines: readonly string[] }
}): {
  group: Group
  colliders: Box2[]
  /** ScreenSwap de las laptops togglables (puestos sin NPC), para E. */
  toggles: { spot: number; screen: ScreenSwap }[]
}
```

- Fusiona TODOS los escritorios + sillas en 2 draw calls
  (`outlinedMergedBoxes`), como hace hoy el aula con `allDesks`.
- Las laptops encendidas (NPC sentado) van con `switchableMonitor` inicial
  `on`; las libres quedan togglables con E (reusa el patron del aula).
- **Presupuesto**: ~2 draw calls (mobiliario) + 1 por laptop encendida.

### `npcCoworkers` — NPCs conversables con 2 enfoques

```ts
export function npcCoworkers(opts: {
  roomIndex: number
  /** Definicion de cada NPC: apariencia + rol narrativo + dialogo. */
  npcs: readonly {
    key: string
    /** Enfoque narrativo (para la doc/estandar, no afecta render). */
    role: 'coworker' | 'staff' | 'boss'
    spec: NpcSpec           // skin/hair/top/bottom/accessory/faceSeed
    position: readonly [number, number, number]
    rotationY?: number
    pose?: 'sit' | 'kneel'
    path?: readonly (readonly [number, number])[]
    speed?: number
    dialog: NpcDialog
  }[]
  openDialog: OpenDialog
}): {
  npcs: NpcHandle[]
  talks: { interactable: Interactable; update(t: number, dt: number): void }[]
}
```

- Encapsula el patron `makeNpc` + `npcTalk` que hoy repiten aula/cima.
- El campo `role` documenta el enfoque (compañero / personal del sitio /
  jefe), y sirve para un helper de validacion en DEV (cada sala debe tener
  ≥2 coworker + ≥2 staff — AC-5).
- **Presupuesto**: ~10-16 draw calls por NPC (contorno inverted-hull). Con
  4-5 NPCs -> ~50-70 draw calls. Es el gasto dominante; por eso el resto
  (mobiliario, props, cuadros) se fusiona agresivamente para no pasar de 100.

> **Nota de perf (decision 10)**: NO se puede diferir la carga del NPC "al
> pulsar E" — hay que verlo para acercarse. El relleno de gente/mobiliario de
> FONDO (no conversable) se hace con `outlinedMergedBoxes` (siluetas
> sentadas fusionadas, 2 draw calls) para dar densidad barata sin sumar NPCs
> completos. Solo los 4-5 conversables son `makeNpc`.

### `softwareShowcase` — monitor Canvas + panel HTML junto a la puerta

```ts
export function softwareShowcase(opts: {
  roomIndex: number
  /** Posicion del panel (junto a la puerta al pasillo). */
  position: readonly [number, number, number]
  rotationY?: number
  theme: Pick<RoomTheme, 'screenBg' | 'screenFg' | 'ink' | 'accent'>
  locale: Locale
  /** Demos del sistema; E cicla a la siguiente. */
  demos: readonly {
    key: string
    /** Titulo mostrado en el monitor y el panel. */
    title: Record<Locale, string>
    /** Loop Canvas ambiente (dibujado con la DrawFn del rubro). */
    draw: DrawFn
    /** Contenido HTML operable del panel (al pulsar E cerca). */
    panel: {
      brand: string          // color de branding del sistema real
      html: Record<Locale, string>  // markup del mockup (buscador, tabla...)
    }
  }[]
  /** Abre el panel HTML (nueva UI action, ver §UI actions). */
  openShowcase: (demo: ShowcaseRef) => void
}): PropHandle
```

- El monitor muestra el loop Canvas de la demo activa (ambiente barato).
- Al **acercarse + E**: abre el panel HTML operable (`openShowcase`) con el
  mockup real (buscador de equipos, KDS, cards PagaloAqui...). Segundo E (o
  con el panel abierto) cicla a la siguiente demo — coherente con
  `switchableMonitor` (fork/vibe de CIMA).
- Los mockups se diseñan con el **branding real** de cada web oficial (colores
  y layout evocados de la web, no pixel-perfect). Ver [03-salas.md](03-salas.md)
  por sala.

### `wallArt` — cuadros de rubro en la pared

```ts
export function wallArt(opts: {
  roomIndex: number
  /** Cuadros: cada uno una lamina Canvas del rubro. */
  frames: readonly {
    key: string
    position: readonly [number, number, number]
    rotationY?: number
    size?: readonly [number, number]  // default 1.1 x 0.8
    /** Lamina Canvas (tinta plana, estilo manga). */
    draw: DrawFn
    /** Si es inspeccionable: al pulsar E abre esta ficha. */
    ficha?: { title: Record<Locale, string>; paragraphs: Record<Locale, string[]> }
  }[]
  onFicha: (title: string, paragraphs: string[]) => void
}): { props: PropHandle[]; colliders: Box2[] }
```

- Los cuadros no inspeccionables se fusionan en 1 lote (marco `boxMesh` +
  plane con textura Canvas) -> pocas draw calls.
- 1-2 por sala llevan `ficha` (E abre panel) — AC-7. Reutilizar los 11
  certificados del CV como fichas cuando aplique (decision 8, opcion mezcla).

## UI actions nuevas

El showcase necesita una accion `openShowcase` (analoga a `openFicha`/
`openContact`/`openStory`/`openDialog`). Se agrega a:

- `WorldActions` (`world.ts:65`) — `openShowcase(ref)`.
- `UiPanel` (`state.ts:15`) — nuevo valor `'showcase'`.
- El glue de UI en `app.ts` + un render DOM en `hud.ts` (panel HTML operable,
  cierra con Esc, deshabilita controles mientras esta abierto — igual que
  ficha/dialog).

> El panel HTML del showcase es DOM real (indexable), consistente con la regla
> "el texto viaja como HTML, no pixeles". El mockup operable (input de
> buscador que filtra una tabla estatica de ejemplo) vive en el panel, no en
> WebGL.

## Paleta paredes-blancas (refactor de `engine/themes.ts`)

Regla: `wall = '#f2f0eb'` (blanco hueso) en TODAS las salas presentes. El
color del rubro va en `floor` (tono del rubro, mas oscuro), `trim` (zocalo/
marcos), `accent` (fichas/portal/micro), `lightColor` (mood de la luz),
`screenBg`/`screenFg`. Los pasados mantienen su sepia (no se tocan sus
colores base, solo su contenido).

| RoomId | wall | floor | accent | trim | lightColor | Nota de mood |
|--------|------|-------|--------|------|------------|--------------|
| aula | `#f2f0eb` | `#e6dcc4` | `#2f6fd0` | `#7a4fc0` | `#eef2ff` | academico claro, guiño morado |
| corpoelec | `#f2f0eb` | `#c9cdd4` | `#e2572b` | `#f2b705` | `#f0f3f8` | oficina industrial, naranja+amarillo seguridad |
| ipasme | `#f2f0eb` | `#dbe8e4` | `#2f7fb0` | `#7ecab0` | `#f2f8ff` | clinico, azul institucional + verde menta |
| cofasa | `#f2f0eb` | `#dfe4ea` | `#1f6fb0` | `#c8ccd2` | `#f4f7fb` | sala limpia farma, andon rojo/verde SOLO en su prop |
| dibal | `#f2f0eb` | `#d6dee0` | `#1f8f8a` | `#1b2433` | `#f2f6f6` | restaurante+POS, navy + teal Dibal |
| goodmeal | `#f2f0eb` | `#e2ddc8` | `#1fa08a` | `#c8a86a` | `#f4f8f2` | food-tech, teal + kraft |
| destacame | `#f2f0eb` | `#d5dae6` | `#0052cc` | `#8ea6d8` | `#eef3ff` | fintech premium, azul Destacame |
| futuro | `#f2f0eb` | `#d8dce4` | `#5a6ff0` | `#a0a8d8` | `#eef0ff` | vision, azul-violeta neutro premium |

`gradient`, `fog`, `sky`, `screenBg`, `screenFg` se derivan del acento (se
ajustan al pasar de "pared oscura" a "pared blanca": el `sky`/`fog` de sala
sube a un gris claro para coherencia con paredes blancas, salvo destacame que
mantiene su drama con luz de acento). Detalle exacto en el commit de themes.

> **Impacto verificado**: `wall`/`floor` los consume `buildRoomShell`
> (`world.ts:295`); `accent`/`trim` los consumen `infoKit`, `pastPortal`,
> las micro-interacciones. Cambiar los valores NO requiere tocar world.ts (es
> puro dato). El `gradient` alimenta el toon shading (`makeToonGradient`).

## Estructura fija de un PASADO (canon, refactor menos Aula)

Cada pasado (menos Aula) — archivo `rooms/past/<id>.ts` — tiene:

1. **Ambiente sepia del rubro SIN el sistema** — los mismos props del
   presente pero desordenados/rotos/en papel (reusan geometria).
2. **2-3 NPCs frustrados** conversables con dialogo del "antes" (buscando
   cosas, quejandose del caos).
3. **Objeto de busqueda lenta** — el gesto que el sistema elimino (buscar un
   equipo entre carpetas, una comanda perdida, una deuda sin gestionar).
4. **Panel de historia** (`past-story`) — expande la narrativa completa
   (`onStory`), ya existe el patron.
5. **exitPortal** de vuelta al presente (ya existe).

Los pasados se parten: `rooms/past/index.ts` (dispatcher `def.id -> builder`,
+ el shell comun `buildPast`), `rooms/past/aula.ts` (MOVIDO tal cual, NO se
toca su contenido), `rooms/past/<id>.ts` por sala.

## Doc del estandar (rule)

Al final del plan se promueve este canon a `.claude/rules/journey-rooms.md`
(decision 4 del usuario: "full helpers + doc de estandar en spec y rule") para
que futuras salas y otros journeys por eje lo sigan sin releer el codigo.
Contendra: los 4 helpers + firmas, la estructura fija presente/pasado, la
regla paredes-blancas, el presupuesto <100 draw calls, los 4 puntos de infra
por sala nueva, y el estandar de 2 enfoques de NPC.
