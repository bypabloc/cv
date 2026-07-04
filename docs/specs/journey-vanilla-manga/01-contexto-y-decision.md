# 01 — Contexto, solucion y criterios de aceptacion

> Secciones 1-3 del plan. La seccion 5 (ER) es N/A — no hay cambios de
> datos: `lib/rooms.ts` sigue mapeando las mismas experiences de
> `@portfolio/content`.

## 1. Contexto / Problema

El MVP de la Propuesta A (journey 3D por habitaciones) esta implementado
con react-three-fiber y desplegado (`journey.portfolio.*.the-full-stack.com`).
El usuario reporta 3 problemas:

1. **Demasiado lento** — en carga inicial, FPS desktop y FPS movil.
2. **Estetica equivocada** — el look actual busca realismo (IBL + AgX +
   MeshStandardMaterial + sombras soft); el usuario quiere anime/ilustrado
   japones tipo comic, trazos a mano, personajes detallados sin realismo.
3. **Solo POV** — falta camara en 3a persona intercambiable.

### Hallazgos de exploracion (causas tecnicas de la lentitud)

- **Carga inicial**: chunk React+R3F+drei (~200 KB gzip) + troika-three-text
  parseando fuentes en el MAIN thread (fix CSP del PR #303) + compilacion de
  shaders PBR + PMREM del RoomEnvironment.
- **FPS desktop**: hasta 3 salas montadas a la vez (actual + adyacentes),
  1 pointLight castShadow POR SALA (3 shadow maps en vivo), `shadows="soft"`
  (PCSS, el modo mas caro), DPR 2, anisotropy 16 en todas las texturas,
  MeshStandardMaterial en todo, ShadowGroup re-traverse en cada mount.
- **FPS movil**: mismo pipeline PBR con DPR 1.5 + antialias; el "reduced"
  solo cambia sombras y el rail, no el costo de material/luces.
- **Memoria**: no hay dispose explicito — R3F desmonta las salas no
  adyacentes pero la estructura completa (muros/pisos/techos/luces de TODO
  el recorrido) vive siempre; las texturas canvas por sala nunca se liberan.

## 2. Solucion propuesta

Reescribir la capa 3D como motor **Three.js vanilla** en
`apps/journey/src/engine/`, aplicando la arquitectura de la guia
(`docs/progress/outputs/guia-arquitectura-mundo-inmersivo.md`) y el patron
del prototipo, conservando TODO lo puro que ya funciona
(`lib/rooms.ts`, `lib/layout.ts`, `lib/collision.ts`, `lib/tiers.ts`,
`lib/tour.ts`, audio procedural) y el contrato Astro/SEO (fallback 2D,
tiers, i18n, chunk separado).

### Decisiones clave

- **Decision 1: motor vanilla, cero React en el 3D** — elimina React,
  react-dom, R3F, drei, zustand y troika del app. El HUD pasa a DOM puro.
  Razon: decision del usuario + guia ("sin frameworks que mantener");
  el ahorro real de la reescritura es el CONTROL del ciclo de vida
  (dispose manual, un solo RAF, cero reconciliacion).
- **Decision 2: esclusa + fade (hibrido)** — al entrar a un pasillo se
  descarga el CONTENIDO de la sala anterior y se precarga el de la
  siguiente; los SHELLS (muros/piso/techo, baratos) de las zonas adyacentes
  permanecen para que nunca se vea vacio por una puerta abierta. Si la
  precarga no llego, un fade de 300-400 ms cubre el hueco. Volver atras
  reconstruye la sala con el mismo fade (procedural = rapido).
- **Decision 3: cel shading manga-ink** — MeshToonMaterial + gradient map
  de 3 escalones de alto contraste + contornos inverted hull negros +
  texturas canvas con trazos de tinta. Se elimina TODO el pipeline PBR
  (IBL/PMREM, AgX, metalness/roughness). Iluminacion: 1 hemisferio +
  1 direccional (sombra 1024 solo desktop) + max 1 acento por sala.
- **Decision 4: personaje procedural anime** — 3a persona default con
  jugador visible (chibi con cara canvas); V alterna a POV (oculta el
  personaje). NPCs generados por el mismo builder con specs distintos
  (pelo/ropa/cara/accesorio) para que se distingan.
- **Decision 5: journey sin tests unit** — decision explicita del usuario.
  Se eliminan `apps/journey/tests/`, `vitest.config.ts` y los scripts
  `test`/`test:coverage` del package. El pre-push NO corre Vitest sobre
  apps (solo `packages/*`), asi que no hay que tocar hooks: basta con que
  `pnpm -r run test` deje de encontrar script en journey. Los gates que SI
  aplican: lint, typecheck (astro check), build y el E2E app.

### Constraints

- Cloudflare Pages estatico; CSP estricta (nada de CDNs — todo procedural
  o self-hosted; al eliminar troika desaparece el ultimo punto delicado).
- `prebuild`/`postbuild` (fetch-cache, llms.txt, _worker.js, MCP functions)
  no se tocan.
- El HTML del fallback y los metadatos SEO no cambian.

## 3. Criterios de aceptacion

- **AC-1**: Given tier full o reduced, When carga `/` (o `/en/`), Then el
  canvas WebGL monta y el texto "Cargando el mundo 3D…" desaparece
  (contrato del E2E `test_journey_3d_mounts.py` intacto).
- **AC-2**: Given tier static (sin WebGL2 / reduced-motion / HW debil),
  Then NO se descarga el chunk three y el CV 2D del HTML queda visible.
- **AC-3**: Given el jugador en la sala i, When entra al pasillo i, Then el
  contenido de la sala i se libera (dispose) y el de la sala i+1 queda
  montado antes de cruzar la puerta; tras recorrer las 3 salas ida y
  vuelta, `renderer.info.memory.{geometries,textures}` vuelve al nivel de
  1 sala (sin crecimiento monotono).
- **AC-4**: Given una precarga incompleta (o teleport/portal), When el
  jugador cruza, Then un fade a negro/tinta cubre el swap y nunca se ve una
  sala vacia o a medio montar.
- **AC-5**: Given el modo default (3a persona), Then el personaje es
  visible y la camara lo sigue con lerp; When se pulsa V (o el boton HUD),
  Then alterna a POV (personaje oculto, pointer-lock) y de vuelta,
  conservando posicion y colision identica.
- **AC-6**: Given cualquier escena montada, Then todos los materiales de
  mundo/personajes son MeshToonMaterial (o MeshBasicMaterial para
  emisivos/outline) — cero MeshStandardMaterial, cero PMREM/IBL, cero
  AgX — y los personajes/props clave llevan contorno negro.
- **AC-7**: Given una sala, Then tiene >= 2 NPCs, cada uno con combinacion
  visual distinta (pelo/ropa/piel/accesorio) y cara dibujada (ojos/boca),
  con idle (respiracion + parpadeo) o patrulla por waypoints.
- **AC-8**: Given tier reduced (movil), Then hay joystick tactil + boton de
  accion + drag para girar camara, DPR <= 1.5, sombras dinamicas apagadas
  (blob shadow bajo personajes) y un boton "Tour" que recorre el riel
  abriendo puertas y pausando en cada sala con sus textos.
- **AC-9**: Given el recorrido completo, Then se conservan: puertas con E,
  fichas retos/aprendizajes como panel DOM, micro-interaccion por sala
  (proyectos, tablero, orquestacion CL+MX), portal al pasado con sepia +
  retorno, CTA de contacto de la cima, menu de teletransporte (M) y audio
  ambiente procedural opt-in.
- **AC-10**: Given cualquier zona activa, Then
  `renderer.info.render.calls < 100` y las texturas canvas son <= 512 px
  (1024 solo con justificacion en comentario).
- **AC-11**: Given `/` y `/en/`, Then HUD y textos de sala salen en el
  idioma correcto desde `lib/rooms.ts` (mismos datos del CV real).
- **AC-12**: Given un build de produccion, Then `apps/journey/dist` NO
  contiene chunks de react/react-dom/R3F/drei/troika/zustand y el chunk 3D
  sigue separado del HTML.
- **AC-13**: Given el repo tras el refactor, Then `pnpm -r run test` no
  ejecuta nada en journey, el pre-commit y pre-push pasan sin tests de
  journey, y lint/typecheck/build siguen aplicando.
- **AC-14**: Given una sesion de dev, Then un log `console.debug` con
  `renderer.info` (calls/triangles/geometries/textures) queda disponible
  para auditar el presupuesto (solo en `import.meta.env.DEV`).

## 5. Diagrama ER

N/A — no hay cambios de datos ni de schemas. Las salas siguen derivando de
`@portfolio/content` via `lib/rooms.ts` (sin tocar).
