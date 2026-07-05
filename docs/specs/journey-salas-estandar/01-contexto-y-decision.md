# 01 — Contexto, solucion y criterios de aceptacion

> [<- README](README.md) · [El canon de sala ->](02-el-canon-de-sala.md)

## 1. Contexto / Problema

El journey 3D (`apps/journey`, Three.js vanilla manga-ink, PR #306) hoy tiene
**3 salas** del MVP: Aula, CORPOELEC, CIMA. El plan `journey-3d-cv`
(Propuesta A) preveia 9 salas pero se acoto a 3 para el MVP. El resultado
actual tiene 3 problemas que el usuario quiere resolver:

### Hallazgos de exploracion

- **Solo el Aula presente cumple el estandar deseado**: NPCs dedicados
  (2 tesistas sentados + 1 en ronda, todos conversables) + items dedicados
  (PCs encendibles, tesis en papel). CORPOELEC y CIMA tienen NPCs pero les
  falta el **doble enfoque** (compañeros de desarrollo + personal del sitio
  que pedia features) y no tienen la **interfaz de software** al lado de la
  puerta.
- **CORPOELEC presente**: los escritorios no parecen una oficina ordenada,
  falta la seccion de equipos de inventario (walkie-talkies, telefonos,
  laptops, tablets — lo que el sistema rastreaba) y falta la demo del sistema
  web de gestion de equipos/personal + buscador + reportes.
- **CORPOELEC pasado**: casi vacio (mesas + un par de NPCs), no comunica el
  caos previo (oficinas viejas, personal frustrado, equipos regados).
- **CIMA presente**: tiene un diseño "Chile"/"Mexico" en la entrada que el
  usuario considera molesto y sin sentido — hay que eliminarlo. No simula una
  oficina real (escritorios con laptops y gente sentada usandolas).
- **CIMA pasado**: existe pero el usuario quiere gente triste con deudas
  (el drama fintech del "antes").
- **Salas de Destacame dispersas**: el plan tenia 3 (FE, arquitecto, CIMA);
  el usuario quiere **unificarlas en 1 sola**.
- **Faltan 4 salas** (IPASME, Cofasa, Dibal, GoodMeal) del plan original.
- **Colores poco realistas**: paredes de colores (aula beige, corpoelec gris,
  cima azul). El usuario quiere paredes blancas + acento del rubro.
- **Faltan cuadros de rubro** en las paredes (el usuario da el ejemplo de
  CORPOELEC: generadores, transformadores, lineas de transmision).

El motor ya escala data-driven: `lib/layout.ts`, `lib/tour.ts`,
`engine/hud.ts` (menu teleport) y el fallback `CvSections.astro` iteran sobre
las rooms sin nada hardcodeado a 3. Solo 4 puntos requieren edicion por sala
(ver README). Esto hace viable pasar a 8 salas sin reescribir la infra.

## 2. Solucion Propuesta

Un plan en dos capas: **(A) el estandar/canon** (helpers reutilizables +
paleta paredes-blancas + doc) y **(B) su aplicacion** sala por sala (refactor
de 3 + 5 salas nuevas + refactor de pasados). Todo data-driven desde
`@portfolio/content`.

### Decisiones clave

- **Decision 1: el canon de sala se codifica en 3 helpers nuevos** en
  `engine/rooms/props.ts` — `officeLayout` (filas de escritorios+sillas+
  laptops fusionadas), `npcCoworkers` (crea N NPCs conversables con los 2
  enfoques), `softwareShowcase` (monitor Canvas loop + panel HTML operable
  junto a la puerta). Cada sala solo aporta sus guiños de rubro + dialogos +
  mockup. Maxima reutilizacion (decision del usuario: "Full helpers").
  *Por que*: replicar a mano 8 salas es inmantenible; el aula ya demostro el
  patron y hay que abstraerlo.

- **Decision 2: paredes blancas uniformes + acento del rubro** — se refactoriza
  `engine/themes.ts` para que todas las salas presentes tengan
  `wall: '#f2f0eb'` (blanco hueso) y el color del rubro viva en
  `floor/trim/accent/lightColor/screenFg`. *Por que*: realismo tipo oficina +
  identidad por acento, no por pared (decision del usuario).

- **Decision 3: Destacame unificada en 2 areas** — la sala `cima` se renombra
  a `destacame` y absorbe las 3 experiencias fintech. Area A = PagaloAqui
  (3 demos bancarias), Area B = producto Destacame (2 demos). Fullstack/DS/
  microservicios/liderazgo = guiños ambientales, no una tercera area.
  *Por que*: el usuario pidio 1 sola sala con esas 2 areas reales.

- **Decision 4: recorrido de 8 salas cronologicas + futuro** — orden real del
  CV. `RoomId` union de 8. La sala `futuro` es sintetica (sin slug), cierre
  inspiracional con CTA. *Por que*: cuenta la progresion completa + deja la
  puerta abierta.

- **Decision 5: cuadros de rubro con `wallArt`** — helper que cuelga 2-4
  laminas Canvas por sala; 1-2 inspeccionables (abren ficha). *Por que*: el
  usuario quiere guiños visuales del rubro en las paredes.

- **Decision 6: pasados en archivos separados** — `rooms/past.ts` (34k y
  creciendo) se parte en `rooms/past/<id>.ts` + un `rooms/past/index.ts`
  dispatcher. Cada pasado (menos Aula) se refactoriza al nivel del presente.
  *Por que*: evitar un archivo gigante (decision del usuario) + regla de <300
  lineas del repo.

- **Decision 7: showcase con demos ciclables** — un `softwareShowcase` por
  area/sala; `E` cicla la siguiente demo del sistema (patron `switchableMonitor`
  ya usado en CIMA fork/vibe). El panel HTML al acercarse muestra la demo
  activa operable. *Por que*: coherente con el patron existente + demo profunda
  opt-in sin romper la estetica 3D.

## 3. Criterios de Aceptacion (AC)

Formato BDD. Fuente de verdad de tests/tareas.

### Infraestructura y estandar

- **AC-1**: Given el motor con `RoomId` de 8 ids, When se arranca el journey,
  Then el recorrido tiene 8 salas en orden `aula, corpoelec, ipasme, cofasa,
  dibal, goodmeal, destacame, futuro` y el build pasa (`RoomId` union completo
  en los 4 puntos de infra).
- **AC-2**: Given cualquier sala presente, When se inspecciona su theme, Then
  `wall === '#f2f0eb'` (blanco hueso) y el acento del rubro esta en
  `floor`/`trim`/`accent`/`lightColor`.
- **AC-3**: Given `officeLayout`, `npcCoworkers`, `softwareShowcase` y
  `wallArt` en `props.ts`, When una sala los invoca, Then produce escritorios+
  sillas+laptops fusionados, N NPCs conversables, el showcase junto a la puerta
  y los cuadros — sin que la sala reimplemente esa geometria.
- **AC-4**: Given cualquier sala renderizada en tier full, When se cuentan los
  draw calls, Then son **< 100** (medido con `renderer.info.render.calls`).

### Estandar de contenido por sala

- **AC-5**: Given cualquier sala presente (menos Aula), When se cuentan sus
  NPCs conversables, Then hay **4-5** repartidos en los 2 enfoques: ≥2
  compañeros de desarrollo + ≥2 personal del sitio (+ opcional 1 jefe/
  cliente/profe), cada uno con `NpcDialog` valido (`defineDialog` no lanza).
- **AC-6**: Given cualquier sala presente (menos Aula), When el visitante se
  acerca al showcase junto a la puerta y pulsa E, Then abre un panel HTML con
  la demo del sistema real (branding del rubro) y E cicla a la siguiente demo.
- **AC-7**: Given cualquier sala presente, When se inspeccionan sus paredes,
  Then hay 2-4 cuadros de rubro (`wallArt`) y ≥1 es inspeccionable (E abre
  ficha).
- **AC-8**: Given cualquier sala, When se busca el kit informativo, Then RETOS/
  APRENDIZAJES/grieta-al-pasado/cuaderno-reseña estan en las MISMAS posiciones
  que el aula (`infoKit` sin cambios de layout).

### Salas concretas

- **AC-9**: Given la sala Aula presente, When se cuentan sus NPCs, Then hay los
  2 tesistas actuales + NPCs nuevos (compañeros de proyecto + compañeros de
  univ ayudados) + **1 profesor sentado en el escritorio del profesor** que
  habla bien de Pablo como ingeniero de software. El pasado de Aula NO cambia.
- **AC-10**: Given la sala CORPOELEC presente, When se recorre, Then los
  escritorios forman una oficina ordenada, hay una **seccion de inventario**
  con equipos (walkie-talkies, telefonos, computadoras, laptops, tablets) +
  cajas, NPCs con **cascos** (algunos caminando, otros sentados), cuadros de
  generadores/transformadores/lineas de transmision, y junto a la puerta el
  showcase del **sistema web de gestion de equipos/personal + buscador (quien
  lo tomo) + reportes e incidencias**.
- **AC-11**: Given la sala CORPOELEC pasado, When se entra por la grieta, Then
  hay oficinas viejas SIN el software, personal frustrado y equipos
  (telefonos, walkie-talkies) regados por el suelo.
- **AC-12**: Given la sala `destacame` (unificada), When se recorre, Then el
  diseño "Chile"/"Mexico" de la entrada **NO existe**, hay oficina real
  (escritorios con laptops + gente sentada usandolas), 2 areas (PagaloAqui:
  Santander/Santander Consumer/Scotiabank · producto: destacame.cl/.com.mx),
  el kit info (retos/aprendizajes/cuaderno/grieta) y la puerta "Proximamente".
- **AC-13**: Given la sala `destacame` pasado, When se entra, Then hay personas
  tristes con deudas (el drama fintech previo a la plataforma).
- **AC-14**: Given las 4 salas nuevas (ipasme, cofasa, dibal, goodmeal), When
  se recorren, Then cada una cumple el canon (AC-5..AC-8) con los guiños de su
  rubro (consultorio, planta farma, restaurante+KDS, food-tech) definidos en
  [03-salas.md](03-salas.md).
- **AC-15**: Given la sala `futuro`, When se entra, Then representa la vision
  profesional (roadmap en pizarra, puerta "Proximamente", CTA de contacto
  fuerte) con textos sinteticos, sin romper el build (no depende de un slug).

### Sistema completo

- **AC-16**: Given el menu de teletransporte (M), When se abre con 8 salas,
  Then lista las 8 automaticamente (sin hardcodear) con su titulo/periodo.
- **AC-17**: Given el tour guiado (tier reduced/movil), When corre, Then
  recorre las 8 salas derivando el riel de `layout.rooms`.
- **AC-18**: Given el tier Static (sin WebGL), When se carga la pagina, Then el
  CV 2D (`CvSections`) sigue indexable con todas las experiencias (SEO/ATS
  intacto).
- **AC-19**: Given cada sala con audio ambiente, When el visitante activa el
  audio (opt-in), Then suena el clip del rubro (respeta mute del sistema,
  arranca en silencio).
- **AC-20**: Given todos los pasados menos Aula, When se entran, Then cada uno
  tiene ambiente sepia del rubro sin el sistema + 2-3 NPCs frustrados con
  dialogo del "antes" + objeto de busqueda lenta + panel de historia.

## Que NO entra en este plan

- Nuevos ejes de journey (`apps/journey-tech`, `apps/journey-impact`) — son
  apps paralelas futuras.
- Deploy a Cloudflare (local-first; se hace en un PR posterior cuando el
  usuario lo confirme).
- Cambios al schema de `experiences` en la DB (campos `challenges`/`learnings`
  explicitos) — se derivan de lo existente, como hoy.
