# 1-3. Contexto, decisión y criterios de aceptación

## 1. Contexto / Problema

Un tweet de [@probiex007](https://x.com/probiex007/status/2066516721259917320)
mostró [messenger.abeto.co](https://messenger.abeto.co/), un juego WebGL/
Three.js cel-shaded de alta fidelidad (planeta chico, entregas, NPCs con
diálogos/quests). Se investigó su bundle servido (reverse engineering:
descarga y grep del JS de producción) y su cobertura técnica pública
(Hacker News, webgpu.com, 80 Level), confirmando stack (Three.js +
Svelte 5/Vite), técnicas (KTX2/Draco/meshopt, bloom, GodRays, DoF, ACES,
BatchedMesh, matcap, wind-shader) y equipo (2 devs, pipeline de arte real
Houdini/Blender/Substance).

El dueño pidió reemplazar el estilo visual de las 10 salas de
`apps/journey` (CV interactivo 3D, Three.js vanilla r0.170, hoy 100%
procedural manga-ink: `MeshToonMaterial` + gradiente de 3 escalones +
Canvas 2D + inverted-hull, cero assets, `NoToneMapping`, <100 draw
calls/sala) por ese nivel de detalle. Durante la interview de
clarificación agregó una segunda referencia: **"Into the Spider-Verse"**,
que terminó siendo el estilo elegido.

### Hallazgo crítico durante la exploración: rama huérfana

Al explorar el engine se encontró `feature/journey-npc-realism` (4
commits, no mergeada a `dev`, no referenciada por el dueño al pedir este
plan) — evidencia de una sesión previa interrumpida (reflog +
`git log`): un plan completo (`docs/specs/journey-npc-realism/` en esa
rama) que construyó un pipeline Blender headless (MPFB2 + Rigify +
keyframing manual + glTF-Transform/Meshopt) para generar NPCs `.glb`
riggeados, con **Etapa 1** (geometría/rig/animación) commiteada y
funcionando en una app sandbox `apps/journey-realistic` (copia de
`apps/journey`, sin tocar producción), y una **Etapa 2** (estilo
painterly) en exploración sin commitear que ya había comparado 5 estilos
NPC y confirmado 3 favoritos con el dueño — **Puss in Boots
(painterly rim-light), Spider-Verse (Ben-Day dots + aberración
cromática) y Caricatura (toon flat + stamp)** — antes de cortarse, con 2
bugs conocidos sin resolver (pantalón lavado en outfits office/formal,
ojos de Puss in Boots que no renderizan) y una galería visual publicada
como Artifact.

Se reconcilió esto con el dueño en vivo (ver decisión no-reabrible 2).

## 2. Solución propuesta

Prototipar el estilo Spider-Verse (halftone/Ben-Day dots, contorno de
tinta, aberración cromática) en 3 salas — `aula`, `futuro`, `destacame` —
más el sistema de personajes completo (jugador + NPCs), migrando de
geometría/texturas 100% procedurales a assets 3D reales CC0 descargados
(Kenney, Quaternius, Mixamo), con un shader propio en Three.js
(inspirado en el repo público `neftale99/halftone-shader`) aportando la
"pintura" Spider-Verse sobre esa geometría — los packs CC0 en sí NO
vienen con ese estilo, es geometría real + nuestro shader.

### Decisiones clave

1. **Reemplazo total**, no evolución del manga-ink — la identidad tinta/
   screentone/gradiente-3-escalones se retira de las 3 salas prototipo.
   Razón: pedido explícito del dueño tras evaluar ambas opciones.
2. **NO se retoma `feature/journey-npc-realism`** — se arranca de cero
   con assets CC0 (no generación Blender local). Razón: decisión explícita
   del dueño al reconciliar el hallazgo; evita depender de un pipeline
   con bugs abiertos y sin outfits definitivos.
3. **Assets 100% CC0** curados (Kenney, Quaternius, poly.pizza como
   agregador, Mixamo para animación/retarget si hace falta). Ninguno
   exige atribución ni prohíbe uso comercial.
4. **Sin límite fijo de draw calls** en este plan — no se instrumenta ni
   bloquea por performance. Razón: decisión explícita del dueño; se
   revisará en el plan de generalización si hace falta.
5. **Personajes también migran** (jugador + NPCs), mismo nivel de detalle
   que el entorno, desde este prototipo.
6. **Reemplaza `apps/journey` directamente** — sin app sandbox nueva.
   Riesgo alto reconocido y mitigado con el workflow local-first ya
   establecido (memoria `journey-local-first-workflow`): implementación y
   verificación en rama local, sin push/PR/deploy hasta confirmación
   visual del dueño.
7. **Prototipo acotado a 3 salas**: `aula`, `futuro`, `destacame`. Las
   otras 7 + los 10 "pasados" (sepia) quedan fuera de este plan.
8. **El shell de sala NO se toca** (`world.ts::buildRoomShell`, compartido
   por las 10 salas, cacheado por `ShellKey`) — solo el contenido interior
   de las 3 salas prototipo migra. Razón: tocar el shell afectaría las 7
   salas no prototipadas antes de validar el estilo nuevo.

### Constraints considerados

- Cero dependencias npm nuevas: `GLTFLoader`/`DRACOLoader`/`KTX2Loader`/
  `EffectComposer`/`OutlinePass` ya vienen en `three@0.170.0` (confirmado
  en `three/examples/jsm/*` del paquete instalado).
- La compresión KTX2 (`gltf-transform` + binario `ktx` de KTX-Software)
  requiere un binario externo no instalable via npm y ausente en el
  runner de CI actual (`ubuntu-24.04` sin steps de instalación de
  binarios de sistema) — se trata como paso de AUTORÍA manual, no de
  build/CI (los `.glb` ya comprimidos se commitean).
- La CSP de Cloudflare Pages (`packages/seo/src/lib/build-headers.ts`)
  bloquea por defecto los Workers `blob:` que Draco/KTX2 crean en
  runtime — requiere `allowBlobWorkers: true` (flag ya existe, solo
  falta activarlo para journey).

## 3. Criterios de Aceptación

- **AC-1**: Given el loader nuevo (`engine/loaders.ts`), When se invoca
  `GLTFLoader.loadAsync()` sobre un `.glb` comprimido en
  `apps/journey/public/models/`, Then carga sin error usando
  `DRACOLoader`+`KTX2Loader` con paths `/draco/`/`/basis/`.
- **AC-2**: Given el build de producción (Cloudflare Pages), When el
  browser instancia los Workers de Draco/KTX2, Then la CSP los permite
  (`allowBlobWorkers: true` activo en `build-headers.ts` para journey).
- **AC-3**: Given la escena renderizada, When se activa el pipeline de
  postprocesado (`engine/postfx.ts`), Then se ve el efecto halftone
  (Ben-Day dots) + contorno de tinta (`OutlinePass`) + aberración
  cromática sobre la geometría CC0.
- **AC-4**: Given un NPC `SkinnedMesh` animándose (walk/idle/talk), When
  se aplica `OutlinePass`, Then el contorno se ve correcto durante la
  deformación esquelética (sin los artefactos del inverted-hull viejo,
  frágil bajo skinning).
- **AC-5**: Given `character.ts` refactorizado, When `rooms/aula.ts`,
  `props.ts::npcCoworkers` y `dialog.ts::npcTalk` invocan `makeCharacter`/
  `makeNpc` sin cambios en su código, Then siguen funcionando (mismo
  contrato `CharacterHandle`/`NpcHandle`: `group, update, setPose,
  setHeadYaw, setWalking, setVisible, collider, talk, endTalk, dispose`).
- **AC-6**: Given las 3 salas migradas, When el jugador navega
  aula→pasillo→futuro→pasillo→destacame, Then la colisión, los portales,
  las fichas RETOS/APRENDIZAJES y los diálogos de NPC funcionan igual que
  antes (cero regresión en `layout.ts`/`collision.ts`/`hud.ts`).
- **AC-7**: Given el texto del CV (fichas, historia, diálogos) en las 3
  salas migradas, Then sigue siendo HTML real en el DOM — cero texto
  renderizado como textura/píxel WebGL.
- **AC-8**: Given los assets CC0 usados, When se documenta su origen,
  Then queda registrado pack + URL + licencia de cada uno en
  `apps/journey/public/models/CREDITS.md`.
- **AC-9**: Given el trabajo terminado, When se completa la verificación
  visual, Then NO hay push/PR/deploy automático — queda en rama local
  para que el dueño confirme primero
  (`pnpm --filter @portfolio/journey run dev`).

## 4. Diagrama de Flujo (Antes y Después)

### Antes (procedural, manga-ink)

```text
makeNpc(spec) --> primitivas (Box/Sphere/Capsule) fusionadas
  --> CanvasTexture (cara) --> toonMat() + outlineGroup() [inverted-hull]
  --> Group (poses = transforms manuales por parte del cuerpo)

buildAula(ctx) --> props.ts::officeLayout/wallArt/softwareShowcase
  --> mergedBoxes/outlinedMergedBoxes (geometría procedural + Canvas 2D)
```

### Después (Spider-Verse, assets CC0)

```text
[autoría, 1 vez por asset — manual, no CI]
  descargar .glb CC0 (Kenney/Quaternius)
    --> gltf-transform optimize --compress draco --texture-compress ktx2
    --> commitear en apps/journey/public/models/

[runtime]
  GLTFLoader+DRACOLoader+KTX2Loader --> SkinnedMesh + AnimationMixer
    --> EffectComposer: RenderPass -> HalftonePass -> ChromaticAberrationPass
        -> OutlinePass
  character.ts: mismo CharacterHandle/NpcHandle, implementación interna
    carga el .glb en vez de ensamblar primitivas
```

## 5. Diagrama ER

N/A — no hay cambios en modelos de datos ni content collections. Los
tipos TypeScript (`RoomId`, `CharacterSpec`, `CharacterPose`) se
preservan.
