# Journey 3D — el canon de sala (apps/journey)

> Estandar de las salas del journey 3D (`apps/journey`, Three.js vanilla
> **toon 3D limpio**, cero React/R3F): los 4 helpers del canon, la estructura
> fija de una sala presente y de un pasado, la paleta paredes-blancas + acento
> del rubro, el presupuesto <100 draw calls por sala, los 4 puntos de
> infra que exige agregar una sala y el estandar de NPCs con 2 enfoques +
> reparto de genero. Promovido del plan `journey-salas-estandar` (10 salas,
> 2026-07). **Giro visual 2026-07-07 (pedido del dueno):** se ELIMINO todo el
> postfx comico — contornos de tinta (inverted-hull) + halftone Ben-Day +
> aberracion cromatica. El render es DIRECTO (`renderer.render`, MSAA nativo,
> sin `EffectComposer`); `toon.ts::outlineGroup` es NO-OP y `outlinedMergedBoxes`
> devuelve solo el fill. Ya NO hay `postfx.ts`.

## Activacion

Aplica SIEMPRE que se:

- Cree o edite una sala: `apps/journey/src/engine/rooms/<id>.ts`
  (presente) o `rooms/past/<id>.ts` (pasado).
- Toque la infra de salas: `lib/rooms.ts` (RoomId + ROOM_SPECS),
  `engine/world.ts` (manifest WORLD), `engine/themes.ts` (THEMES +
  PAST_CAPTIONS), `engine/dialogs/*`, `engine/audio.ts` (perfiles).
- Toque los helpers del canon en `engine/rooms/props.ts` o el generador
  de NPCs (`engine/character.ts`).
- Agregue una experiencia al CV que deba ganar sala en el recorrido.
- Diagnostique perf del journey (draw calls, merges) o el look/estilo
  (pizarras por sala, cuerpos de NPC, ausencia de contornos/postfx).

NO aplica al resto de apps Astro ni al fallback 2D (`CvSections`, que es
data-driven y escala solo).

## Reglas duras (SIEMPRE / NUNCA)

- **SIEMPRE** paredes blanco hueso (`#f2f0eb`) en TODA sala presente. El
  color del rubro vive en `floor`/`trim`/`accent`/`lightColor`/pantallas
  y props firma — NUNCA en la pared. Los pasados mantienen su sepia.
- **SIEMPRE** <100 draw calls por sala (presente Y pasado). Medir en DEV
  con `window.__journeyDebug.info.render.calls` (smoke con browser,
  patron `tmp/journey-smoke-perf.py`: max sobre ventana de 4 s tras el
  mount, capturando NPCs caminantes).
- **SIEMPRE** el texto del CV (retos/aprendizajes/fichas/dialogos/
  showcase) viaja como HTML real (panel DOM), NUNCA como pixeles WebGL
  (SEO/ATS/a11y).
- **SIEMPRE** las salas son data-driven desde `@portfolio/content` via
  sus slugs en `ROOM_SPECS` (excepciones sinteticas: `aula` y `futuro`,
  con textos en `lib/rooms.ts`).
- **SIEMPRE** el `infoKit` (RETOS/APRENDIZAJES/grieta/cuaderno) en las
  posiciones canonicas (el aula es la referencia). `futuro` es la unica
  sala con `withPortal: false` (no tiene pasado).
- **SIEMPRE** el `softwareShowcase` junto a la puerta en toda sala
  presente MENOS el aula (academica, sin producto).
- **SIEMPRE** los dialogos con el shape `NpcDialog` validado por
  `defineDialog` (falla en DEV si el grafo es invalido).
- **SIEMPRE** props estaticos del mismo material fusionados
  (`mergedBoxes`; `outlinedMergedBoxes` ya NO agrega contorno, devuelve solo
  el fill); el relleno de gente de fondo son siluetas fusionadas, NUNCA
  `makeNpc`.
- **SIEMPRE** las pizarras RETOS/APRENDIZAJES (`infoKit`) toman su
  `boardStyle` por TIPO de sala: `chalk` (aula = pizarra verde de salon con
  marco de madera y tiza), `whiteboard` (oficinas = pizarra blanca con
  marcador negro, DEFAULT), `glass` (futuro = pizarra de cristal esmerilado,
  el estilo "nuevo"). El aula ademas usa mobiliario BLANCO + sillas de 4 patas
  procedurales (`schoolChair`), no la silla de oficina del pack.
- **SIEMPRE** los NPCs conversables tienen un cuerpo GLB via `spec.model`
  (6 variantes CC0 curadas: `male-casual`/`male-suit`/`male-worker` +
  `female-casual`/`female-office`/`female-worker`; `base` = el Hoodie de
  Pablo). El genero se reparte **~50/50** en el recorrido, por IDENTIDAD del
  NPC (el nombre del dialogo manda), con el modelo elegido por rol/contexto
  (obreros -> `*-worker`; jefes -> `*-suit`; oficina -> `*-casual`/`*-office`).
  EXCEPCION: el pasado del aula es solo Pablo (no se reparte).
- **NUNCA** re-introducir contornos de tinta ni el postfx comico (halftone /
  aberracion): el look es toon limpio. `outlineGroup`/`outlinedMergedBoxes`
  quedan como no-op / solo-fill por compatibilidad de firma.
- **NUNCA** usar un cuerpo de NPC DISFRAZADO de los packs Quaternius (bruja,
  rey, punk, playero): se curaron a mano SOLO personas normales
  (casual/oficina/obrero). Todos comparten esqueleto + clips
  `CharacterArmature|*`.
- **NUNCA** cargar mas de 1 sala a la vez (regla de memoria del zone
  manager; iOS WebGL context limit).
- **NUNCA** romper el fallback 3 tiers (full/reduced/static). El tier
  static ES el CV 2D indexable, no se degrada.
- **NUNCA** diferir la carga de un NPC conversable "al pulsar E": hay
  que verlo para acercarse. El presupuesto se cuida fusionando lo demas.

## Los 4 helpers del canon (`engine/rooms/props.ts`)

| Helper | Que hace | Presupuesto |
|--------|----------|-------------|
| `officeLayout` | Filas de escritorios + sillas fusionadas + laptop por puesto. `furniture: {deskUrl, chairUrl, deskWidth?, chairWidth?}` (opt-in) reemplaza el merge por GLB CC0 (destacame Kenney, futuro Space Station Kit sci-fi). `poweredSpots` = laptops encendidas (NPC sentado); las libres quedan en `toggles` (E) | ~2 draw calls (mobiliario) + 1 por laptop encendida |
| `npcCoworkers` | NPCs conversables (encapsula `makeNpc` + `npcTalk`). Cada NPC lleva un cuerpo GLB via `spec.model` (6 variantes, ~50/50 genero). En DEV valida el mix del estandar (>=2 `coworker` + >=2 `staff`) salvo `validateMix: false` (el aula esta exenta) | ~8-14 draw calls por NPC (sin contorno); 4-5 NPCs ~40-60 — el gasto dominante |
| `wallArt` | 2-4 laminas Canvas de rubro con marco (`frameColor?` override, ej. madera en el aula). Los marcos se fusionan en 1 mesh; cada lamina es 1 plane. >=1 lleva `ficha` (E abre panel) | ~1 + 1/lamina |
| `softwareShowcase` | Totem junto a la puerta: monitor Canvas en loop (~7 fps) + panel HTML operable (`openShowcase`). E cicla las demos; `key` distingue multiples showcases (destacame tiene 2 areas) | ~4-6 |

Los mockups del showcase se diseñan con el branding real de la web
oficial de cada empresa (evocado, no pixel-perfect).

## Estructura fija de una sala PRESENTE

```text
+------------------------------------------------------------------+
|  MURO FONDO (+Z)                                                  |
|   [ wallArt: cuadros de rubro ]       [ CTA/holograma si aplica ] |
|   officeLayout: escritorios + gente sentada con laptops           |
|   [ props firma del rubro ]     [ seccion especifica del rubro ]  |
|  MURO -X: RETOS (infoKit)         MURO +X: APRENDIZAJES (infoKit) |
|  grieta al pasado (izq)           cuaderno-reseña (der)           |
|  [ softwareShowcase junto a la PUERTA al pasillo ]                |
+---------------------- PUERTA al pasillo (-Z) ---------------------+
```

Elementos obligatorios: `officeLayout`, `npcCoworkers` (4-5),
`wallArt` (>=1 ficha), `softwareShowcase` (menos aula), `infoKit`,
props firma del rubro, 1-3 micro-interacciones del sistema real.

## Estructura fija de un PASADO (`rooms/past/<id>.ts`)

1. Ambiente sepia del rubro SIN el sistema (mismos props, en papel/caos).
2. 2-3 NPCs frustrados conversables con el dialogo del "antes".
3. Objeto de busqueda lenta (el gesto que el sistema elimino).
4. Panel de historia (`past-story`, `onStory`).
5. `exitPortal` de vuelta al presente.

El reloj de pared es el prop recurrente de los pasados (y su tic-tac es
la firma del audio sepia). El pasado del aula NO se toca (decision del
usuario). Los pasados se registran en el dispatcher
`rooms/past/index.ts`.

## Estandar de NPCs (2 enfoques + genero, 4-5 por sala)

- ~2 **`coworker`** (con quienes Pablo construyo) + ~2 **`staff`**
  (personal del sitio que pedia features) + opcional 1 **`boss`**
  (jefe/cliente/profe). Todos conversables (arbol + burbuja).
- **Cuerpo por `spec.model`** (6 GLB CC0 curados: `male-casual`/`-suit`/
  `-worker`, `female-casual`/`-office`/`-worker`; `base` = Hoodie de Pablo).
  Reparto de genero **~50/50** en TODO el recorrido, POR IDENTIDAD (el nombre
  del dialogo decide el genero; el modelo, el rol/contexto). Pablo (jugador)
  y el pasado del aula = `base`. Los 6 comparten esqueleto + clips
  `CharacterArmature|*`, asi que el mapping de poses no cambia.
- Nombres unicos en TODO el recorrido (colision real detectada: "Camila
  Fuentes" existia en goodmeal y destacame — se renombro).
- El relleno de fondo (densidad barata) son siluetas fusionadas con
  `mergedBoxes`, no NPCs (ya sin contorno).

## Los 4 puntos de infra por sala nueva (el compilador los exige)

`RoomId` es un union literal: falta uno y el build falla.

1. `lib/rooms.ts` — `RoomId` + entrada en `ROOM_SPECS` (slugs del CV).
2. `engine/world.ts` — entrada en el manifest `WORLD` (dynamic import);
   `rooms/<id>.ts` con `export default`.
3. `engine/themes.ts` — entrada en `THEMES` (paleta paredes-blancas) +
   `PAST_CAPTIONS`.
4. `engine/dialogs/<id>-presente.ts` + `-pasado.ts` + rama en
   `rooms/past/index.ts`.

Ademas (audio, C14): perfil de la sala en `profileFor` de
`engine/audio.ts` (1-2 capas procedurales WebAudio sobre el room-tone;
el pasado usa el perfil sepia GLOBAL `<room>:past`, no uno propio).

Lo que escala solo (NO tocar): `lib/layout.ts` (cursor lineal),
`lib/tour.ts`, `engine/hud.ts` (menu teleport itera rooms), fallback
`CvSections.astro`. Los ids `talk-N-*`/`showcase-N`/`portal-N` derivan
de `room.index` en runtime (insertar una sala corre los indices solos).

Los 10 ids vigentes: `aula`, `corpoelec`, `ipasme`, `iai`, `asesoria`,
`cofasa`, `dibal`, `goodmeal`, `destacame`, `futuro`. El viejo id
`cima` fue RENOMBRADO a `destacame` (y las 3 salas Destacame se
unificaron en una): `cima` NO existe como `RoomId` ni se reintroduce.

## Perf: como se cuida el presupuesto

- Palanca #1: fusionar estaticos del mismo material (`mergedBoxes` = 1
  draw call). `outlinedMergedBoxes` ya NO agrega contorno (devuelve solo el
  fill en 1 draw call); quitar los contornos BAJO el conteo respecto al
  pipeline manga-ink viejo.
- `userData.noOutline` ya no tiene efecto (los contornos se eliminaron); se
  conserva en el codigo sin costo.
- Piezas repetidas de un prop (ej. los 6 pinchos del pelo `spiky`) se
  fusionan en una geometry horneando la pose con matrix (C15).
- Medir SIEMPRE antes/despues con el smoke de perf; atribuir con el
  patron `onBeforeRender` (`tmp/journey-diag-drawlist.py`) cuando no es
  obvio que domina.

## Paleta por sala (wall fija, acento por rubro)

`wall = '#f2f0eb'` en TODAS. `floor`/`accent`/`trim`/`lightColor` dan la
identidad (tabla completa en `engine/themes.ts`). El acento tambien
colorea el audio: cada sala presente tiene su firma sonora por rubro.

## Anti-patrones

| Anti-patron | Correccion |
|-------------|------------|
| Color del rubro en la pared | Pared `#f2f0eb`; el acento va en piso/trim/props/luz |
| Texto del CV renderizado en WebGL | Panel DOM/HTML real (`openFicha`/`openStory`/showcase) |
| Un mesh por caja estatica | `mergedBoxes` por material (1 draw call) |
| Re-introducir contornos de tinta o postfx comico (halftone/aberracion) | Look toon limpio; `outlineGroup` no-op, sin `EffectComposer` |
| Pizarra RETOS/APRENDIZAJES con el estilo equivocado | `boardStyle` por sala: chalk (aula) / whiteboard (oficinas) / glass (futuro) |
| Cuerpo de NPC disfrazado (bruja/rey/punk) o genero desbalanceado | 6 cuerpos normales curados; ~50/50 por identidad |
| NPC de relleno con `makeNpc` | Siluetas fusionadas (`mergedBoxes`); `makeNpc` solo para conversables |
| Cargar la sala siguiente "por si acaso" | 1 sala viva; el zone manager desmonta la anterior |
| Sala nueva sin los 4 puntos de infra | El build falla en `RoomId`; completar los 4 + audio |
| Textos hardcodeados de una experiencia | Data-driven desde `@portfolio/content` (slug en `ROOM_SPECS`) |
| Declarar la sala lista sin medir draw calls | Smoke de perf presente+pasado <100 |

## Referencias cruzadas

- Codigo: `apps/journey/src/engine/rooms/props.ts` (helpers, `boardStyle`,
  `schoolChair`), `engine/toon.ts` (merges; `outlineGroup` no-op),
  `engine/character.ts` (NPCs + `CharacterModel`/`MODEL_URLS`),
  `engine/themes.ts` (paleta), `engine/audio.ts` (perfiles C14).
  Cuerpos CC0 + CREDITS: `apps/journey/public/models/characters/`.
- [.claude/rules/astro-landing.md](astro-landing.md) — convenciones del
  monorepo (la app journey es exenta de tests unit, ver PR #306).
- [.claude/rules/verify-before-done.md](verify-before-done.md) — la
  verificacion antes de declarar una sala lista.
