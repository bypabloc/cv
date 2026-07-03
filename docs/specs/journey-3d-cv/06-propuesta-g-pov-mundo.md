# Propuesta G — POV navegable (mundo 3D libre)

> [<- Extras C-F](03-propuestas-extra.md) · [Arquitectura comun ->](04-arquitectura-comun.md)

Controlas la camara en primera/tercera persona (WASD + mouse / joystick tactil)
y **exploras libremente** un mundo 3D donde cada zona representa una etapa de tu
carrera. Te acercas a un hito y se abre su ficha del CV. Es el patron
Bruno-Simon: maximo "wow", maximo riesgo y costo.

## Concepto (mismo mundo/sendero que B scroll, pero explorable)

Mismo mundo del sendero de la Propuesta B (scroll journey) — eje = **progresion
de seniority** (elevacion/complejidad crece de intern a arquitecto), NO
geografia — pero en vez de scroll on-rails, **caminas/conduces** a tu ritmo.
Puedes desviarte, volver, explorar los hitos en cualquier orden. La cronologia +
el ascenso profesional se sugieren con el terreno (subes hacia el presente y
hacia mayor seniority) pero no te obliga. El pais del cliente es un guiño
(etiqueta en la ficha), no zona.

Variante homenaje: un **cochecito/personaje con física** (como Bruno Simon)
que recorre el mundo; las zonas "se expanden" al pasar por encima.

## Mapeo a datos

Igual que la Propuesta B (scroll): eje protagonista **seniority = elevacion/
escala/complejidad**; ano = posicion; pais del cliente = guiño (etiqueta en ficha).
Con exploracion libre. Los hitos se activan por **proximidad** (entras en
rango -> el prop se ilumina / aparece la ficha) en vez de por scroll.

## Mecanica tecnica

- **Physics**: Rapier (`@react-three/rapier` v2, WASM). Trae **character
  controller cinematico (KCC)** oficial para caminar/subir pendientes sin bugs.
  - Alternativa arcade: cannon-es raycast vehicle (lo que uso Bruno Simon) para
    la variante cochecito.
- **Controles**:
  - Desktop first-person: `PointerLockControls` (Pointer Lock API, mouse-look).
  - Desktop 3a persona: Rapier KCC + skinned glTF.
  - Movil: joystick tactil (nipplejs) — el que peor escala en gama baja.
- **Colisiones**: truco Bruno Simon — shapes primitivas simples (box/sphere/
  plane) que matchean los modelos detallados; física sobre las primitivas,
  render del modelo bonito encima. `sleep` en cuerpos estáticos (bug de perf
  clásico si no se duermen).
  - Terreno abierto necesita heightfield collider (Rapier desde heightmap) o
    un **navmesh** exportado de Blender (three-pathfinding / recast-navigation-js).
- **Interaccion "acercarse -> ficha"**: proximidad (trigger de distancia) +
  ficha en `<Html>` de drei (DOM real, indexable, i18n desde content collection).
- **Loading**: chunked por zona (no cargar los 3 biomas de golpe — crashea
  iOS/Safari por límite de contexto WebGL). Cargar zona actual + precargar la
  siguiente.

## Fallback movil (CRITICO en esta propuesta)

Free-roam en movil es la parte mas frágil. Estrategia combinada:

- **Gama media/alta**: **auto-tour guiado** — la camara avanza sola/con scroll
  por los hitos (degrada al patron de la Propuesta B scroll). Sin joystick.
- **Gama baja / reduced-motion / sin-WebGL**: **scrollytelling 2D** (el timeline
  legible, = fallback SEO/ATS).
- Joystick tactil solo como opcion avanzada opt-in. Requiere QA cross-device
  caro (BrowserStack).

## Referencias reales (del research)

- **Bruno Simon** (bruno-simon.com) — EL referente. Cochecito con física
  (Three.js + Cannon.js), glTF+Draco, matcaps, sombras horneadas. Total ~2.8 MB.
  Código MIT: github.com/brunosimon/folio-2019. **Le costó ~3 meses siendo ya
  experto** — ese es el piso para calidad-premio.
- **Thibault Introvigne** (thibault-introvigne.com) — spaceman + 10
  coleccionables (gamificación de hitos).
- **WoraWork** (worawork.vercel.app) — personaje por mundo Zelda/Animal Crossing.
- **Henry Heffernan** (henryheffernan.com) — cuarto 3D explorable (degrada a
  desktop-only en la práctica).
- **Virtual art gallery** (github.com/rahel-yab/Virtual-art-gallery) — OPEN
  SOURCE, first-person WASD, colisiones de caja triviales.

Tabla completa + URLs en [../../progress/explore_pov3d_world.md](../../progress/explore_pov3d_world.md).

## Esfuerzo (honesto)

- **Free-roam con character controller** (Rapier KCC, colisiones, assets
  propios): **8-14 semanas** part-time. Riesgo medio-alto.
- **Calidad-premio tipo Bruno Simon** (mundo pulido, shaders, audio, física,
  movil sólido): **3-6 meses** part-time. Es un proyecto en sí mismo.
- Habilidades extra vs Propuestas A/B: Blender (importar/decimar/hornear/exportar),
  tuning de física, navmesh/heightmap, QA cross-device.

## Riesgos (los que mas duelen)

1. **Scope creep** — un mundo 3D "siempre pide una cosa mas". Riesgo #1.
2. **Movil/gama baja** — crashes WebGL en iOS/Safari, blank screen. QA caro.
3. **Peso/carga inicial** — 6s de carga pierde visitantes (sesión promedio de
   Bruno: 54s). Presupuesto duro de MB por zona, lazy por zona.
4. **Mantenimiento** — cada rol nuevo = editar el mundo, no solo un YAML.
   Mitigar con hitos data-driven desde content collection.

## Por que va al final del orden

Es la propuesta de MAYOR riesgo y costo (free-roam con physics, mundo abierto).
Reusa toda la arquitectura comun (datos, isla, fallback, tiers) que A
(habitaciones) o B (scroll) ya establecen. Construir G primero es asumir el
riesgo alto sin la base validada. Recomendacion: hacer A (habitaciones, la #1)
primero -> si se quiere el maximo wow explorable, G como "modo explorar" opt-in.
Nota: para CONTAR una carrera, la secuencia dirigida de A (habitaciones) es
superior al mundo abierto de G (que diluye el orden narrativo intern ->
arquitecto).
