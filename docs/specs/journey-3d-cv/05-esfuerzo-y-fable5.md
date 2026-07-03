# Esfuerzo por propuesta + workflow con Fable 5

> [<- Arquitectura comun](04-arquitectura-comun.md) · [README](README.md)

## Estimacion de esfuerzo (dev senior full-stack, NO artista 3D, aprende Three.js en el camino)

| Propuesta | Alcance | Tiempo realista (part-time) | Riesgo |
|-----------|---------|-----------------------------|--------|
| **A — Habitaciones (JUEGO) — #1** | POV walk, 9 salas AMBIENTADAS por rubro real + NPCs + retos/aprendizajes + portal-al-pasado por sala + micro-interacciones + teletransporte + puerta "Próximamente" | **4-6 sem** MVP (CORPOELEC + CIMA) / **12-18** completo (9 salas) | Medio |
| **B — Scroll journey (#2)** | On-rails, camara sobre curva, assets CC0 | **3-5 sem** (2-3 si ya domina R3F) | **Bajo** |
| **G — POV mundo libre** | Free-roam, Rapier KCC, colisiones, assets propios | **8-14 sem** | **Alto** |
| **G — calidad-premio** | tipo Bruno Simon (pulido, shaders, audio, física) | **3-6 meses** | Muy alto |
| **C — Globo/mapa** | Orbit + click-to-fly, mini-escenas | **3-5 sem** | Bajo |
| **D — Museo** | First-person, salas-caja | **3-6 sem** | Bajo-medio |
| **E — Metro/tren** | On-rails, estaciones | **2-4 sem** | Bajo |
| **F — Ciudad crece** | Avenida + edificios instanced | **4-7 sem** | Medio |

### Donde se va el tiempo (invisible)

1. **Assets 3D** (lo mas caro) — mitigar con low-poly CC0 (Kenney/Quaternius/
   Poly Pizza). Modelar hero-assets propios (personaje riggeado) sube el costo
   mucho.
2. **Pipeline de optimizacion** — Draco, KTX2/Basis, instancing, baking, LOD,
   chunked loading. Aqui se va ~la mitad del tiempo "invisible".
3. **Calibrar el spline + matar el jitter** (A/C/E) o **tuning de física** (B).
4. **Sync scroll<->texto HTML** / interaccion "acercarse -> ficha".
5. **Fallback movil + tiers + QA cross-device** (caro en B, barato en A/C/E).

## El stack recomendado: R3F vs Three.js vanilla (decision)

Los research divergieron: el de scroll recomienda **Three.js vanilla** (ahorra
~1 MB de React+R3F); el de stack recomienda **R3F** (ecosistema drei + mejor
vibe-coding). **Decision para este proyecto: R3F**, porque:

- `apps/generic` (la base) YA usa React 18 + `@astrojs/react` -> R3F encaja
  nativo, no se paga React "de mas" (ya esta).
- El chunk R3F (~200-220 KB gzip) se **aisla** con dynamic import fuera del CV
  texto, asi que el CV 2D no lo descarga.
- drei abstrae boilerplate (loaders, controles, `<Html>`, `<AdaptiveDpr>`) que
  Fable 5 genera con fiabilidad -> menos codigo a mano.
- Puerta de escape: Spline exporta a R3F code si se quiere prototipar visual.

Three.js vanilla queda como alternativa SI el peso se vuelve critico en movil
(Reduced tier) — pero el tier Static ya cubre el peor caso (no carga 3D).

## Angulo Fable 5 / Claude Code (honesto)

**Fable 5 es un modelo de generacion de codigo de Anthropic (familia Claude 5,
liberado 2026-06-09), NO un motor 3D ni un generador de assets 3D.** SOTA en
software engineering (95% SWE-bench Verified, ~2x Opus 4.8 en precio: $10/$50
por Mtok).

### Evidencia real: el prompt de Sidi Bou Said 3D

Ya SI hay evidencia publica de Fable 5 generando Three.js: el prompt
[cnemri/c917e11b...](https://gist.github.com/cnemri/c917e11b3a6936823b509dcff53392aa)
produjo un **Sidi Bou Said navegable en 3D con Three.js corriendo en el
browser** — analisis completo en
[../../progress/explore_sidi_bou_said_prompt.md](../../progress/explore_sidi_bou_said_prompt.md).
Lecciones que adopta este plan:

- **Single-file, Three.js por CDN, cero assets externos** — Fable 5 puede
  generar una escena 3D completa y autocontenida.
- **Texturas procedurales (Canvas API), instancing, shaders GLSL, iluminacion
  Hemisphere+Directional, ACESFilmicToneMapping** — el modelo escribe todo esto
  sin recortes ("every function/shader/loop written out in its entirety").
- Es exactamente el enfoque **procedural-first** que adopta la Propuesta A: la
  mayoria de cada sala se genera por codigo, bajando el costo de assets. Esto
  valida que Fable 5 puede construir el grueso del journey.
- **Prompt como el del gist**: pedir codigo COMPLETO sin placeholders, escena
  estructurada (edificios/terreno/luz), constraint de "no external URLs" y target
  de 60 FPS con instancing. Replicar ese estilo de prompt por sala.

### Que delegar a Fable 5 (alto ROI) vs que NO

| Delegar al LLM | NO delegar (humano) |
|----------------|---------------------|
| Boilerplate escena R3F (`<Canvas>`, luces, camara, controles) | **Art direction** / concepto del viaje |
| Componentes drei, `useGLTF`, Suspense, lazy-load | **Assets 3D** (modelos, texturas) — CC0/IA + retopo |
| Shaders GLSL comunes (gradientes, noise, reveal, dissolve) | Shaders de fragmento complejos (ajuste fino) |
| Controles scroll-driven (GSAP/Lenis + R3F), spline camera path | Curacion estetica, timing/feel de animacion |
| Conversion glTF->JSX (gltfjsx), tipado TS | Perf percibida en movil (juicio) |
| Integracion Astro island + code-split + tiers + fallback | Trade-offs peso/calidad, direccion de producto |
| Sistema de datos data-driven desde content collection | — |

### Workflow recomendado

1. **Art direction humana**: concepto del viaje, escenas, mood, estetica.
2. **Assets**: CC0 (Kenney/Quaternius/Poly Pizza) + IA (Rodin/Meshy/Tripo) para
   piezas hero -> gltf-transform (Draco/Meshopt/KTX2).
3. **Fable 5 (Claude Code)** genera: app `apps/journey`, isla Astro + escena
   R3F + controles + shaders base + carga lazy + tiers/fallback + el bridge de
   datos con content collection. Iterar con feedback visual.
4. **Humano** ajusta feel, shaders complejos, perf movil, art.
5. **Vigilar coste**: Fable 5 a ~2x Opus por token. Usar thinking effort bajo
   para boilerplate; reservar effort alto (o Fable 5) para lo dificil, y Opus
   4.8 para iteraciones mecanicas de alto volumen.

### Realismo sobre "otros usando Fable 5 para esto"

Hay casos publicos de Fable 5 generando escenas 3D Three.js completas (el Sidi
Bou Said navegable arriba es el ejemplo directo). No se encontraron aun casos de
un PORTFOLIO/CV 3D construido con Fable 5 (uso especifico muy nuevo), pero la
capacidad base esta demostrada: escena estructurada, texturas procedurales,
instancing, shaders, iluminacion — todo generado sin recortes. El art direction
(concepto de cada sala, mood, narrativa) y los NPCs siguen siendo humanos;
Fable 5 escribe el codigo de la escena.

## Siguiente paso: del plan a la implementacion

Cuando elijas propuesta(s), el plan de implementacion (secciones 8-11 del
plan-format del repo) cubrira:

- **Descomposicion** en tareas atomicas (scaffold app, isla, spline, datos,
  fallback, deploy).
- **Commits** incrementales verdes.
- **Worktrees** si se paralelizan A y B.
- **Verificacion E2E**: build estatico, lint, typecheck, y — critico — `curl`
  real a `journey.portfolio.dev.the-full-stack.com` post-deploy (200 +
  marcador), mas verificacion visual del 3D en desktop y del fallback en movil.
