# journey-3d-cv — CV como viaje 3D interactivo

> Plan detallado (SIN implementar) para una nueva app `apps/journey`: el CV
> de Pablo Contreras como experiencia 3D navegable/scroll-driven, basada en
> el recorrido COMPLETO de `generic` (no un niche). Desktop-first 3D +
> fallback storytelling legible en movil. Si una propuesta gusta, puede
> volverse el CV principal.

## Estado

| Fase | Estado |
|------|--------|
| Investigacion (3 research) | HECHO — ver `docs/progress/explore_*.md` |
| Scope acordado | HECHO — ver [SCOPE.md](SCOPE.md) |
| Plan detallado (este doc) | HECHO |
| Eleccion del usuario | HECHO (2026-07-02): **Propuesta A**, MVP 3 salas |
| Plan de ejecucion (secciones 8-11) | HECHO — ver [07](07-implementacion-mvp.md)-[10](10-verificacion-e2e.md) |
| Implementacion Propuesta A (MVP) | EN CURSO — rama `feature/journey-3d-propuesta-a` |

### Decisiones de arranque (2026-07-02 — no reabrir sin el usuario)

- **Alcance MVP**: 3 salas (Aula + CORPOELEC + CIMA) con TODOS los extras:
  NPCs low-poly, tour guiado (tier Reduced movil), audio ambiente opt-in.
- **Ruta**: `/` de `apps/journey` ES la experiencia 3D con el fallback CV 2D
  (CvSections) en el mismo HTML (tier Static + SEO/ATS).
- **Deploy**: solo local en este PR; provisioning Cloudflare en un PR posterior.

## Los research (fuente de este plan)

Los informes completos (referencias reales con URLs, tablas, costos) viven en:

- [../../progress/explore_scroll3d_journey.md](../../progress/explore_scroll3d_journey.md) — scroll-driven journey
- [../../progress/explore_pov3d_world.md](../../progress/explore_pov3d_world.md) — POV navegable + 6 escenarios
- [../../progress/explore_3d_stack_fable5.md](../../progress/explore_3d_stack_fable5.md) — stack tecnico 2026 + Fable 5
- [../../progress/explore_sidi_bou_said_prompt.md](../../progress/explore_sidi_bou_said_prompt.md) — leccion tecnica del prompt Sidi Bou Said (procedural-first, como se ve/construye)
- Empresas (ambientacion por rubro): [explore_empresas_venezuela.md](../../progress/explore_empresas_venezuela.md) · [explore_empresas_latam1.md](../../progress/explore_empresas_latam1.md) · [explore_empresa_destacame.md](../../progress/explore_empresa_destacame.md)

## Cuando leer cada archivo

| Archivo | Cuando leer |
|---------|-------------|
| [SCOPE.md](SCOPE.md) | Decisiones del usuario + datos reales disponibles |
| README.md (este) | Decision de propuesta, comparativa, arquitectura comun, datos |
| [01-propuesta-a-habitaciones.md](01-propuesta-a-habitaciones.md) | Propuesta A: 9 habitaciones por puertas (POV tipo JUEGO), CADA SALA ambientada por el rubro real + retos/aprendizajes + portal-al-pasado (antes/después) + puerta "Próximamente" — RECOMENDADA #1 |
| [02-propuesta-b-scroll-journey.md](02-propuesta-b-scroll-journey.md) | Propuesta B: scroll-driven journey (#2, menor riesgo, posible CV principal) |
| [03-propuestas-extra.md](03-propuestas-extra.md) | Propuestas C-F extra (mapa/globo, museo, metro, ciudad) |
| [06-propuesta-g-pov-mundo.md](06-propuesta-g-pov-mundo.md) | Propuesta G: POV navegable (mundo 3D libre, free-roam) |
| [04-arquitectura-comun.md](04-arquitectura-comun.md) | App `apps/journey`, islas, code-split, datos, fallback, deploy |
| [05-esfuerzo-y-fable5.md](05-esfuerzo-y-fable5.md) | Estimacion de esfuerzo por propuesta + workflow con Fable 5 |
| [07-implementacion-mvp.md](07-implementacion-mvp.md) | EJECUCION: decisiones cerradas, AC numerados, descomposicion (seccion 8) |
| [08-commits.md](08-commits.md) | EJECUCION: secuencia de commits C1-C8 (seccion 9) |
| [09-paralelizacion-worktrees.md](09-paralelizacion-worktrees.md) | EJECUCION: base secuencial + salas worktree-safe (seccion 10) |
| [10-verificacion-e2e.md](10-verificacion-e2e.md) | EJECUCION: bateria de verificacion final (seccion 11) |

## Decision central: que construir primero

El usuario pidio **scroll + POV + ideas extra + una propuesta tipo JUEGO
(habitaciones por puertas)**, como app `apps/journey` basada en `generic`. Este
plan describe **7 propuestas** (A-G) y recomienda un **orden de ejecucion** para
no caer en scope creep (el riesgo #1 de todo mundo 3D — verificado en el research).

### Orden de prioridad (decision del usuario — no reabrir sin justificar)

1. **Propuesta A — Habitaciones (tipo JUEGO)** es la **#1**. Es el concepto que
   pidio el usuario: POV inmersivo, 9 salas ambientadas por el rubro real de
   cada empresa, conectadas por puertas con ida y vuelta + portal-al-pasado,
   navegacion teclado/touch + teletransporte. 4-6 semanas MVP (CORPOELEC + la
   CIMA). La mas fiel a la vision.
2. **Propuesta B — Scroll journey** es la **#2 / alternativa**: menor riesgo,
   degrada limpio a un timeline 2D indexable (SEO/ATS), 2-6 semanas, puede ser
   el CV principal. Puede convivir con A en `apps/journey` (A como `/world`
   inmersivo, B como `/` scroll).
3. **G** (POV mundo abierto libre, free-roam) solo si se quiere el maximo wow
   explorable — mas caro y disperso que A. **D/E/F** como variantes de menor
   esfuerzo. **C** (mapa) es secundaria (geografica, choca con el eje).

> A y B comparten `apps/journey` + `@portfolio/content` + el sistema de tiers/
> fallback. Se pueden construir ambas. Ver [04-arquitectura-comun.md](04-arquitectura-comun.md).

## Comparativa de las 7 propuestas

Columna clave: **Encaje con el eje seniority** (que tan bien la metafora
cuenta la progresion profesional, el foco acordado). La geografia ya NO puntua.

| Prop | Nombre | Mecanica | Inmersion | Encaje eje seniority | Esfuerzo | Fallback movil | Riesgo |
|------|--------|----------|-----------|----------------------|----------|----------------|--------|
| **A** ⭐ | **Habitaciones (JUEGO) — #1** | **POV camina sala a sala por puertas, ida/vuelta** | **Muy alta** | **Muy alto** (sala por etapa, ambientada) | Medio | Buena | Medio |
| **B** | Scroll journey (#2) | Scroll mueve camara por sendero que asciende | Alta | **Muy alto** (elevacion = seniority) | **Bajo-medio** | **Excelente** | **Bajo** |
| **G** | POV mundo libre | WASD/joystick, free-roam | **Muy alta** | Alto | **Alto** | Medio | **Alto** |
| C | Globo/mapa mercados | Orbit + click-to-fly (Lima base + clientes) | Media | **Bajo** (es geografico, choca con el eje) | Medio | **Excelente** | Bajo tecnico / alto narrativo |
| D | Museo de salas | First-person WASD, sala por nivel de carrera | Muy alta | Alto (salas mas opulentas al subir) | Bajo-medio | Buena | Bajo-medio |
| E | Metro/tren de carrera | On-rails, estaciones = roles/anos | Media | Medio-alto | **Bajo** | **Excelente** | Bajo |
| F | Ciudad que crece | Avanzas y la ciudad se densifica con tu nivel | Alta | **Muy alto** (altura edificio = seniority) | Medio | Buena | Medio |

## Regla dura (ADN del portfolio — NUNCA romper)

- El CV canonico/indexable/ATS/SEO/GEO SIGUE siendo la version 2D de `generic`.
  El 3D es una **capa experiencial opt-in** (`/` de `apps/journey` o una ruta
  `/world`), NUNCA la unica via de leer el CV.
- El texto del CV viaja como **HTML real** (overlay estatico o `<Html>` de
  drei / CSS3D), NUNCA como pixeles dentro del WebGL (no se indexa, no es ATS,
  hostil a lectores de pantalla).
- La escena WebGL vive en UNA isla `client:only` (nunca `client:load` — rompe
  el build por `window`/`document`). El chunk 3D (~155-220 KB gzip) se separa
  del CV texto.
- Fallback en 3 tiers detectado en init: Full (desktop GPU) / Reduced (movil
  con WebGL) / Static (sin WebGL, HW debil, `prefers-reduced-motion`) — el
  Static ES el storytelling 2D legible.

## Eje protagonista: PROGRESION PROFESIONAL (correccion del usuario)

**IMPORTANTE (2026-07-02):** el foco NO es el arco migratorio. El eje que
estructura el viaje es la **progresion de seniority + complejidad tecnica**
(intern -> junior -> mid -> senior -> lead/arquitecto). La geografia es un
**guiño sutil** (etiqueta/bandera del cliente por estacion), NUNCA la columna
vertebral.

Geografia real: Pablo reside en **Lima, Peru**; migro UNA sola vez
(Venezuela -> Peru). Desde Peru trabaja **remoto** para clientes de Chile y
Mexico. El `country` de cada experiencia es el pais del EMPLEADOR/CLIENTE, NO
el lugar de residencia. NO hay arco VE->PE->CL de residencia.

El usuario abrio la puerta a construir **journeys adicionales con otros ejes**
(evolucion tecnica, impacto/proyectos) como apps paralelas — ver "Journeys por
eje alternativo" abajo.

## Datos reales que alimentan cualquier propuesta

De `packages/content` (data-cache JSON, generado de la DB — misma fuente que
el CV 2D).

- **9 experiencias** 2013-2026. Seniority: intern (2013) -> junior -> mid ->
  senior (2018) -> lead/arquitecto (2022-hoy). El `country` es el pais del
  CLIENTE (VE hasta 2018; luego PE/CL como clientes), NO residencia.
- **Eje protagonista mapeable SIN texto**: **seniority = elevacion/escala/
  complejidad de la escena**. Secundarios: ano = distancia/posicion; pais del
  cliente = etiqueta discreta (guiño).
- **skills**: 7 categorias tecnicas (AI Workflows, Arquitectura, Backend,
  Cloud/DevOps, Datos/SQL, Dominios, Frontend) + 3 soft.
- **stats**: 12 anos, 8 empresas, 4 paises (de clientes), 11 certs.
- **projects (4)**: ERP, plataformas fintech, microservicios... Cada uno con
  metricas. Ademas profile, education, awards, certificates, languages. Todo
  via `@portfolio/content` (Zod + JSON cache).

## Journeys por eje alternativo (apps paralelas)

El usuario habilito crear varias apps journey, cada una con un eje distinto.
El mismo mundo/mecanica, distinto criterio de estructura:

| App | Eje | Que estructura el viaje |
|-----|-----|-------------------------|
| `apps/journey` (base) | **Seniority** | Ascenso intern -> arquitecto (RECOMENDADA #1) |
| `apps/journey-tech` (opcional) | **Evolucion tecnica** | De web basico -> full-stack -> microservicios/AWS -> AI workflows |
| `apps/journey-impact` (opcional) | **Impacto/proyectos** | Los sistemas construidos (ERP, fintech) y sus metricas |

Todas comparten `@portfolio/content` + la arquitectura comun (isla, tiers,
fallback). Cambiar de eje = re-mapear los datos al spline, no rehacer la infra.
Recomendacion: construir primero la de seniority; las otras son iteraciones.

## Stack recomendado (sintesis de los 3 research)

- **Motor**: react-three-fiber + drei. `generic` (base) ya usa React 18 +
  `@astrojs/react`, asi que R3F encaja nativo. El "impuesto" de ~200-220 KB
  gzip se aisla en su propio chunk (dynamic import), fuera del CV texto.
  - Alternativa considerada: Three.js vanilla (~155 KB, sin React) — mas
    liviano pero pierde el ecosistema drei y el terreno de vibe-coding. Dado
    que React YA esta en la base, R3F gana por DX/ecosistema. Ver
    [05-esfuerzo-y-fable5.md](05-esfuerzo-y-fable5.md) para el trade-off.
- **Scroll/animacion**: GSAP (100% gratis desde 2025) + Lenis, un unico RAF loop.
- **Physics (solo POV free-roam)**: Rapier (`@react-three/rapier` v2, KCC).
  Las propuestas on-rails (A, C, E) NO necesitan physics.
- **Camino**: `THREE.CatmullRomCurve3` (15-40 control points) + scroll
  normalizado -> `getPointAt(t)` con lerp/damping 0.05-0.1 (mata el jitter).
- **Assets**: low-poly CC0 (Kenney / Quaternius / Poly Pizza) como base;
  IA (Rodin/Meshy/Tripo) solo para piezas hero. TODO por Draco/Meshopt + KTX2.
- **Hosting**: Cloudflare Pages (<=25 MiB/archivo); lo que exceda -> R2.
  Lazy-load por escena/zona (no cargar los 3 biomas de golpe — crashea iOS).
- **Fable 5**: acelerador de desarrollo (boilerplate R3F, GLSL comun,
  integracion Astro), NO motor 3D ni fuente de assets. Ver
  [05-esfuerzo-y-fable5.md](05-esfuerzo-y-fable5.md).

## Proximos pasos (que necesito de ti)

1. Elegir que propuesta(s) construir primero (recomiendo A; o A+B en paralelo).
2. Confirmar la estetica (low-poly/papercraft/voxel/realista — afecta costo).
3. Confirmar subdominio de la nueva app (ej. `journey.portfolio...` o
   `/world` dentro de generic — ver [04-arquitectura-comun.md](04-arquitectura-comun.md)).
4. Recien ahi paso a plan de implementacion (secciones 8-11 del plan-format:
   descomposicion, commits, worktrees, verificacion E2E).
