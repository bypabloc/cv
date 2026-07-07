# 2. Arquitectura técnica

## Qué se toca vs qué no

Confirmado por exploración de código (`character.ts`, `world.ts`,
`props.ts`, `controls.ts`, `lib/collision.ts`, `lib/layout.ts`, `hud.ts`,
`dialog.ts`): la arquitectura actual ya separa limpiamente navegación/
datos/UI de renderizado visual.

| Sistema | Se toca | Por qué |
|---|---|---|
| `lib/layout.ts`, `lib/rooms.ts` | NO | Puramente geométrico/textual (`RoomLayout`, `RoomDef`), sin referencia a materiales/props |
| `lib/collision.ts`, `controls.ts` | NO | Colisión es `Box2[]` declarado a mano por cada sala (`footprint()`), NUNCA derivado de la geometría visual (`Box2` es un dato plano `{minX,maxX,minZ,maxZ}`, sin acceso a `BufferGeometry`). Cambiar props visuales no rompe navegación |
| `hud.ts`, `dialog.ts` | NO | 100% DOM/HTML real (`document.createElement`), conectado vía 5 callbacks (`openFicha/openContact/openStory/openDialog/openShowcase` en `WorldActions`) — regla dura de SEO/ATS/accesibilidad, se preserva intacta |
| `world.ts` (contrato `RoomFactory`) | Firma NO, implementación interna tampoco en este plan | `RoomFactory = (ctx: RoomCtx) => RoomBuild` se preserva; `buildRoomShell` (muros/portales, compartido por las 10 salas) NO se toca (decisión no-reabrible 8) |
| `character.ts` (API pública) | Firma NO | `CharacterHandle`/`NpcHandle` (`group, update, setPose, setHeadYaw, setWalking, setVisible, collider, talk, endTalk, dispose`) se preserva — cambia la implementación interna |
| `character.ts` (impl. interna), `app.ts` (renderer), `themes.ts`, `rooms/{aula,futuro,destacame}.ts` | SÍ | Núcleo del refactor |
| `toon.ts` | Parcial | Los helpers de merge (`mergedBoxes`/`outlinedMergedBoxes`) y el pool de materiales pueden seguir usándose para los props que NO migran a GLB (ej. `infoKit`, `wallArt` marcos); el sistema de outline por inverted-hull deja de usarse en personajes (reemplazado por `OutlinePass`) |

Consecuencia directa: **cero riesgo de romper navegación, diálogos,
fichas o el CV en DOM**. El refactor es sobre "qué se renderiza dentro de
la caja de la sala", no sobre cómo se camina/interactúa/lee.

## Pipeline de carga de assets

Todo dentro de `three@0.170.0` — `GLTFLoader`/`DRACOLoader`/`KTX2Loader`
viven en `three/examples/jsm/loaders/*` del paquete ya instalado, sin
dependencia npm nueva.

```ts
// engine/loaders.ts
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js'
import { KTX2Loader } from 'three/examples/jsm/loaders/KTX2Loader.js'

const dracoLoader = new DRACOLoader()
dracoLoader.setDecoderPath('/draco/')

const ktx2Loader = new KTX2Loader()
ktx2Loader.setTranscoderPath('/basis/')
// detectSupport(renderer) se llama una vez que exista el WebGLRenderer,
// desde app.ts, no acá (evita acoplar loaders.ts al renderer)

const gltfLoader = new GLTFLoader()
gltfLoader.setDRACOLoader(dracoLoader)
gltfLoader.setKTX2Loader(ktx2Loader)

export { gltfLoader, ktx2Loader }
```

`DRACOLoader.setDecoderPath()`/`KTX2Loader.setTranscoderPath()` reciben
un PREFIJO DE DIRECTORIO (concatenan `decoderPath + 'draco_decoder.js'`
internamente) — por eso los decoders van como carpeta completa en
`public/draco/` y `public/basis/`, NO como imports `?url` de Vite
(rompería el patrón de concatenación).

### Script de copia (prebuild)

```js
// scripts/copy-loader-assets.mjs — mismo patrón que build-public-assets.mjs
import { cp, mkdir } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const THREE_LIBS = resolve(__dirname, '../node_modules/three/examples/jsm/libs')
const PUBLIC_DIR = resolve(__dirname, '../public')

async function main() {
  await mkdir(PUBLIC_DIR, { recursive: true })
  await cp(resolve(THREE_LIBS, 'draco'), resolve(PUBLIC_DIR, 'draco'), { recursive: true })
  await cp(resolve(THREE_LIBS, 'basis'), resolve(PUBLIC_DIR, 'basis'), { recursive: true })
}
main()
```

Encadenado en `package.json#scripts.prebuild` después de
`build-public-assets.mjs`.

### Fix de CSP (gotcha verificado en código)

`DRACOLoader`/`KTX2Loader` crean Web Workers desde Blob URL en runtime
(`URL.createObjectURL(new Blob([...]))`). La CSP que arma
`packages/seo/src/lib/build-headers.ts` no incluye `worker-src` por
defecto → cae a `default-src 'self'` → bloquea el worker `blob:` en
Cloudflare Pages (funciona en dev local, falla solo en producción). El
flag `allowBlobWorkers` ya existe (pensado para troika-three-text, no
usado hoy por journey):

```diff
// apps/journey/scripts/build-public-assets.mjs
- await write('_headers', buildHeaders({ apiEndpoint: API_ENDPOINT }))
+ await write('_headers', buildHeaders({ apiEndpoint: API_ENDPOINT, allowBlobWorkers: true }))
```

## Pipeline de postprocesado

`EffectComposer`/`RenderPass`/`ShaderPass`/`OutlinePass` viven en
`three/examples/jsm/postprocessing/*`, con `.d.ts` en `@types/three`
(sin warnings de TS strict).

```ts
// engine/postfx.ts (forma; el shader real se ajusta visualmente en T2)
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js'
import { ShaderPass } from 'three/examples/jsm/postprocessing/ShaderPass.js'
import { OutlinePass } from 'three/examples/jsm/postprocessing/OutlinePass.js'
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js'

export function createPostFx({ renderer, scene, camera, width, height }) {
  const composer = new EffectComposer(renderer)
  composer.addPass(new RenderPass(scene, camera))

  const outline = new OutlinePass(new Vector2(width, height), scene, camera)
  outline.edgeStrength = 6
  outline.edgeThickness = 1.5
  outline.visibleEdgeColor.set('#141018') // ink de toon.ts
  composer.addPass(outline)

  composer.addPass(new ShaderPass(HalftoneShader))          // Ben-Day dots
  composer.addPass(new ShaderPass(ChromaticAberrationShader))
  composer.addPass(new OutputPass())                        // resuelve tone mapping/color space

  return { composer, outline, resize: (w, h) => composer.setSize(w, h) }
}
```

`OutlinePass` reemplaza el inverted-hull SOLO para personajes: opera en
screen-space sobre la silueta rasterizada final, por lo que funciona
sobre `SkinnedMesh` deformándose sin depender de inflar normales sobre la
geometría fuente (a diferencia del inverted-hull, frágil bajo skinning —
razón por la que la investigación previa, tanto la de esta conversación
como la de la rama huérfana, coincide en esta elección). Los props
estáticos que se queden con `mergedBoxes` (si los hay) pueden seguir con
su inverted-hull existente sin conflicto — son geometrías distintas.

`HalftoneShader`/`ChromaticAberrationShader` son GLSL propios (prototipo,
ver [05-riesgos-y-decisiones-abiertas.md](05-riesgos-y-decisiones-abiertas.md)),
inspirados en [neftale99/halftone-shader](https://github.com/neftale99/halftone-shader)
(WebGL/GLSL, portable a `ShaderPass`).

Loop de render (`app.ts`): `renderer.render(scene, camera)` se reemplaza
por `postfx.composer.render()`; `onResize` gana `postfx.resize(w, h)`.

## Sistema de personajes

`character.ts` preserva su API pública. La implementación interna de
`makeCharacter`/`makeNpc` pasa de ensamblar primitivas a:

```ts
const gltf = await gltfLoader.loadAsync('/models/characters/base.glb')
const mesh = SkeletonUtils.clone(gltf.scene) // clon con skeleton independiente por instancia
const mixer = new AnimationMixer(mesh)
const clips = new Map(gltf.animations.map(c => [c.name, c]))

// mapeo CharacterPose -> AnimationClip (nombres reales del pack, TBD en T3)
const POSE_CLIP: Partial<Record<CharacterPose, string>> = {
  idle: 'Idle', walk: 'Walk', talk: 'Talk', wave: 'Wave', /* ... */
}
```

`SkeletonUtils.clone` (de `three/examples/jsm/utils/SkeletonUtils.js`,
mismo paquete) es necesario para clonar un `SkinnedMesh` con su skeleton
correctamente — `Object3D.clone()` normal NO clona bones compartidos
entre instancias.

Los NPCs que no tengan un clip 1:1 (`fight`/`sit`/`kneel`) usan el clip
más cercano disponible del pack (o quedan en pose estática) — se resuelve
en T3 según la cobertura real de las 24 animaciones de Quaternius (ver
[03-sourcing-assets.md](03-sourcing-assets.md)).
