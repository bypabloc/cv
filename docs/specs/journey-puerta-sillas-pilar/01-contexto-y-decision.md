# 1-5. Contexto, solución propuesta, criterios de aceptación y diagramas

## 1. Contexto / Problema

El plan `journey-cuaderno-central` (cerrado el 2026-07-06, commit
`654acd0d`) reubicó el pilar del cuaderno-reseña al eje central de
tránsito de cada sala y ajustó varias entradas. Al probar visualmente el
resultado, el usuario reportó 4 problemas sobre `apps/journey`:

1. **Sillas vacías no interactuables**: hoy solo las laptops de los
   puestos libres se pueden encender/apagar con `E` (patrón `toggles` de
   `officeLayout`); no existe ninguna mecánica para que el JUGADOR se
   siente en una silla sin NPC.
2. **Aula (sala 0) — pilar y libro**:
   - El pilar del cuaderno quedó en `z = room.z - room.depth/4` (a un
     cuarto de profundidad de la entrada), NO en el centro geométrico de
     la sala (`room.z`). Ademas ese punto coincide casi exactamente con el
     spawn del jugador (`pos.z = room.z - room.depth/4` en
     `controls.ts:126`), por lo que el jugador arranca la partida
     encimado con el collider del pilar.
   - El "libro" flotante (`lecternNotebook`, `props.ts:757-835`) es un
     único `PlaneGeometry` de una sola cara (`FrontSide` por defecto, sin
     `side: DoubleSide`) con normal +Z. El jugador entra caminando desde
     -Z hacia +Z, así que ve la cara TRASERA (invisible) del libro al
     acercarse — el bug exacto que reporta el usuario ("se ve la
     espalda", "cuando está por atrás no se ve").
   - Visualmente el libro es solo una lámina plana sin lomo/portada — no
     se lee como un libro real.
3. **Contorno de los cuadros (`wallArt`) se sale del marco**: el marco de
   `wallArt` se construye con `mergedBoxes` (props.ts:1146-1163) en vez de
   `outlinedMergedBoxes`. El comentario del propio helper
   (`toon.ts:690-693`) ya documenta la causa: el contorno genérico
   (`outlineGroup`, aplicado por cada sala) escala el mesh fusionado
   alrededor de su origen LOCAL, y como las posiciones de cada marco están
   "horneadas" en la geometría con coordenadas absolutas de la sala (ej.
   `z ≈ 13.12` en una sala lejana del origen del mundo), el contorno
   escalado se desplaza varios centímetros del marco real — es la
   "sombra"/borde que se sale del encuadre en la imagen 2.
4. **Túnel entre salas**: el pasillo (`buildCorridorShell`,
   `world.ts:401-466`) hoy renderiza muros laterales + techo + piso +
   letrero de año + luz de acento, y el jugador lo CAMINA. El dintel
   sobre la puerta (`headerSpecs`, `world.ts:374-399`) usa el material y
   la altura del pasillo (`CORRIDOR_HEIGHT=2.6`, tema `THEMES.corridor`,
   mucho más oscuro) mientras el techo de la sala usa su propia altura
   (`room.height=4.24`) y tema — el salto abrupto entre ambos EN el vano
   de la puerta es el "bloque de techo no continuo" reportado. Las
   "barras" laterales son los 2 muros del pasillo (`WALL_THICKNESS=0.2`,
   altura 2.6, ancho de pasillo 2.4 vs. 13.2 de la sala): un cuello de
   botella visual justo junto a la puerta.

### Hallazgos de exploración

- El motor ya tiene TODO lo necesario para resolver (3) y (4) sin
  construir nada nuevo: `outlinedMergedBoxes` (fix de contorno) y
  `world.teleportToRoom`/`hud.fade` (fade + teletransporte) ya existen y
  se usan en otros flujos (viaje al pasado). Ver detalle en cada capítulo.
- El "sentarse" (1) reutiliza la pose `'sit'` que YA existe en
  `character.ts` (usada hoy solo por NPCs) — no hace falta animación
  nueva, solo aplicarla al jugador y congelar el movimiento mientras dura.
- Las 9 salas con oficina (todas menos `aula`) comparten el helper
  `officeLayout` + una función local `laptopToggles` duplicada en cada
  archivo de sala — el mecanismo de sillas vacías se puede centralizar
  UNA sola vez en `officeLayout` en vez de duplicarse 9 veces (evita
  repetir el patrón ya duplicado de `laptopToggles`).

## 2. Solución Propuesta

Cuatro cambios independientes entre sí (no hay dependencias de datos
entre ellos, solo comparten archivos como `props.ts`), implementados y
verificados uno por uno:

- **Sentarse**: nuevo campo `playerSeat` en `EngineState` +
  `officeLayout` expone `seats: Interactable[]` (silla vacía = índice NO
  presente en `poweredSpots`, mismo criterio que ya usa `toggles`) +
  `controls.ts` congela WASD y aplica pose/posición mientras
  `playerSeat` no es `null`. `aula.ts` (layout a mano, sin
  `officeLayout`) registra sus propias sillas vacías con el mismo
  mecanismo.
- **Pilar + libro del aula**: mover `noteEntryZ` de `room.z -
  room.depth/4` a `room.z` (centro real, vale para las 10 salas por
  construcción vía `infoKit`) + girar el grupo del cuaderno
  `rotationY: Math.PI` (cara frontal hacia la entrada, -Z) + reconstruir
  el libro con una caja delgada (portada/lomo) detrás de la página
  existente, para que tenga volumen y nunca quede invisible desde ningún
  ángulo.
- **Contorno de `wallArt`**: cambiar `mergedBoxes(...)` por
  `outlinedMergedBoxes(...)` en la construcción del marco — mismo helper
  que ya usan `officeLayout`/sillas/escritorios sin este bug.
- **Puerta sin túnel**: `buildCorridorShell` deja de construir
  muros/piso/techo/letrero/luz del pasillo (solo monta la puerta); el
  `Interactable` de la puerta pasa de "abrir y listo" a una secuencia
  async: abrir la hoja → sfx `door` → breve pausa (que se vea el giro) →
  `hud.fade(true, 'warp')` (nueva variante, "viaje al futuro") → sfx
  `whoosh` → `teleportPlayer` a la entrada de la sala siguiente →
  `applyZone` → `hud.fade(false, 'warp')` → cerrar la hoja (quitar el
  índice de `state.doorsOpen`, la animación de cierre ya existe) →
  re-registrar el interactable de la puerta.

### Decisiones clave

- **Decisión 1**: el "sentarse" se centraliza UNA sola vez dentro de
  `officeLayout` (en vez de duplicar una función `sitChairs` en las 9
  salas, como ya ocurre con `laptopToggles`). Razón: es lógica 100%
  genérica sin variación por sala (misma fórmula de posición de silla,
  misma etiqueta), a diferencia de `laptopToggles` cuyo contenido de
  pantalla sí varía por sala.
- **Decisión 2**: NO se toca `lib/layout.ts` ni el tipo `Zone`
  (`'room' | 'corridor'`). Razón: remover el modelo de datos del pasillo
  obligaría a re-plantear la esclusa de preload/dispose, el riel del tour
  guiado (`tour.ts`) y el colisionador de puerta cerrada
  (`closedDoorBoxes`) — alto riesgo para cero beneficio visible, ya que
  el jugador nunca vuelve a pisar esa franja (se teletransporta). Solo se
  deja de RENDERIZAR la geometría del pasillo y de exigir que se camine.
- **Decisión 3**: el libro gana volumen con una caja simple (portada +
  lomo, 1 draw call extra) en vez de dos páginas abiertas en V. Razón:
  presupuesto de draw calls de la sala (<100, `journey-rooms.md`) y
  simplicidad — una caja sólida ya resuelve "se ve de un objeto real
  desde cualquier ángulo" sin geometría de bisagra.
- **Decisión 4**: el efecto "viaje al futuro" es una tercera variante de
  `hud.fade` (`'warp'`), no un mecanismo nuevo. Razón: reusar el
  contrato ya probado (`Promise` que resuelve tras la transición CSS) que
  ya cablean `enterPast`/`exitPast`/`teleportToRoom`.
- **Decisión 5**: tras cruzar, la puerta se cierra y su interactable se
  re-registra (a diferencia del comportamiento actual, donde una puerta
  abierta queda abierta para siempre). Razón: el usuario pide
  explícitamente "cerrarse la puerta"; además sin esto una sala
  revisitada por teleport de HUD mostraría la puerta ya abierta sin
  sentido.

## 3. Criterios de Aceptación

- **AC-1**: Given el jugador cerca de una silla vacía (índice fuera de
  `poweredSpots`) en cualquier sala con `officeLayout`, When presiona
  `E`, Then el personaje adopta la pose `'sit'` en la posición/rotación
  exacta de esa silla y el movimiento WASD queda bloqueado.
- **AC-2**: Given el jugador sentado, When presiona `E` de nuevo, Then se
  levanta (pose `'idle'`, movimiento restaurado) sin cambiar de posición.
- **AC-3**: Given una silla ocupada por un NPC (índice en `poweredSpots`
  o, en `aula`, en `NPC_PCS`/la silla del profesor), When el jugador se
  acerca, Then NO aparece ningún interactable de "sentarse" en esa silla.
- **AC-4**: Given la sala `aula` (layout a mano, sin `officeLayout`),
  When el jugador se acerca a cualquiera de sus pupitres vacíos (tu PC,
  la del laboratorio, o los 4 pupitres decorativos sin monitor), Then
  puede sentarse igual que en las demás salas.
- **AC-5**: Given el jugador sentado, When ocurre un cambio de zona
  (nueva sala) o se desmonta el contenido de la sala actual, Then
  `playerSeat` se limpia (vuelve a `null`) sin dejar el movimiento
  bloqueado en la sala nueva.
- **AC-6**: Given cualquiera de las 10 salas (vía `infoKit`), When se
  monta el pilar del cuaderno, Then su posición es el centro geométrico
  de la sala (`x=0, z=room.z`), no un cuarto de la profundidad hacia la
  entrada.
- **AC-7**: Given el jugador entrando a una sala caminando desde la
  puerta (dirección +Z), When se acerca al pilar, Then ve la cara
  FRONTAL del libro (texto legible), no el reverso.
- **AC-8**: Given el jugador rodeando el pilar hasta el lado opuesto,
  When observa el libro desde ahí, Then sigue viendo un objeto sólido
  (portada/lomo), nunca un hueco invisible.
- **AC-9**: Given el libro del pilar, When se renderiza, Then tiene
  volumen (portada/lomo con grosor), no una lámina plana.
- **AC-10**: Given un cuadro (`wallArt`) en cualquier sala y a cualquier
  distancia Z del origen del mundo, When se renderiza su contorno de
  tinta, Then el contorno queda alineado al marco (sin desplazamiento
  visible).
- **AC-11**: Given el jugador frente a la puerta entre 2 salas, When
  presiona `E` para abrirla, Then la puerta se abre, el jugador es
  teletransportado automáticamente a la entrada de la sala siguiente con
  el efecto "viaje al futuro", y la puerta se cierra tras el cruce.
- **AC-12**: Given la franja entre 2 salas, When se renderiza, Then NO
  existe geometría de pasillo visible (sin muros laterales ni techo
  intermedio) — solo la puerta en el vano de la pared.
- **AC-13**: Given el vano de la puerta entre 2 salas, When se llega ahí,
  Then no hay ningún bloque de techo discontinuo ni barras verticales
  visibles (eliminados por construcción, al no renderizarse ya el
  pasillo).
- **AC-14**: Given el jugador ya cruzó una puerta, When la vuelve a mirar
  o vuelve a esa sala por teleport de HUD, Then la puerta aparece cerrada
  y es interactuable de nuevo.

## 4. Diagrama de Flujo (Antes y Después)

Aplica solo al cruce de puerta (AC-11 a AC-14); las otras 3 features no
alteran flujo de control.

### Antes

```text
[jugador junto a la puerta] --E--> openDoor(i)
  |
  v
state.doorsOpen.add(i)  -- unregisterInteractable(door-i)
  |
  v
hoja gira (lerp visual, sin bloquear mas el paso)
  |
  v
[jugador CAMINA por el pasillo: muros+techo+piso+letrero+luz visibles]
  |
  v
zoneAt(pos.z) cruza a {kind:'corridor', index:i} --> setZone()
  |                                                    |
  v                                                    v
applyZone: preload(sala i+1), dispose sala i     (esclusa)
  |
  v
[jugador sigue caminando, cruza a {kind:'room', index:i+1}]
  |
  v
applyZone: monta sala i+1 (contenido ya precargado)
```

### Después

```text
[jugador junto a la puerta] --E--> onActivate() [async]
  |
  v
state.doorsOpen.add(i) -- sfx('door') -- hoja gira (lerp visual)
  |
  v
espera breve (que se vea el giro, ~250-400ms)
  |
  v
hud.fade(true, 'warp')  -- sfx('whoosh')          <- efecto "viaje al futuro"
  |
  v
deps.teleportPlayer(0, room[i+1].z - room[i+1].depth/2 + 1.5)
state.zone = {kind:'room', index:i+1}
applyZone(state.zone, false)   -- (misma esclusa: dispose sala i, monta i+1)
  |
  v
hud.fade(false, 'warp')
  |
  v
state.doorsOpen.delete(i)  -- sfx('door') -- hoja cierra (lerp visual)
registerInteractable(door-i)   <- vuelve a ser interactuable
```

El jugador NUNCA pisa físicamente la franja del pasillo: no hace falta
caminar por ahí porque el teletransporte cubre esa distancia. La esclusa
de preload/dispose (`applyZone`) se reutiliza sin cambios.

## 5. Diagrama ER

N/A — no hay cambios en modelos de datos ni en content collections. El
CV (`@portfolio/content`) no se toca; todo el trabajo es geometría 3D y
estado de motor en memoria.
