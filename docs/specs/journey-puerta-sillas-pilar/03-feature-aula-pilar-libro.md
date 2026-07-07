# Feature B — Pilar centrado y libro con estilo real (aula y las 10 salas)

> AC-6 a AC-9. Ver contexto general en
> [01-contexto-y-decision.md](01-contexto-y-decision.md). El fix vive en
> `infoKit`/`lecternNotebook` (`engine/rooms/props.ts`), así que aplica
> por construcción a las 10 salas — no solo a `aula` (que es la sala de
> la captura reportada por el usuario).

## Diseño

### 1. Centrar el pilar (`infoKit`, props.ts:900-913)

```ts
// ANTES
const noteEntryZ = room.z - room.depth / 4
const nota = lecternNotebook({
  roomIndex: room.index,
  position: [0, 0, noteEntryZ],
  rotationY: 0,
  // ...
})
// ...
colliders: [footprint(0, noteEntryZ, 1, 1)],
```

```ts
// DESPUES
const nota = lecternNotebook({
  roomIndex: room.index,
  position: [0, 0, room.z],
  rotationY: Math.PI,
  // ...
})
// ...
colliders: [footprint(0, room.z, 1, 1)],
```

`x=0` ya estaba centrado (eje de tránsito); el cambio es `z`: pasa de
`room.z - room.depth/4` (a un cuarto de sala de la entrada) a `room.z`
(centro geométrico exacto). El collider footprint (1×1) se mueve con él,
así que el jugador sigue debiendo rodearlo (mismo comportamiento de
"bloquear el paso" que trajo `journey-cuaderno-central`, solo que ahora
en el centro real en vez de casi pegado a la entrada — y ya NO se
superpone con el punto de spawn del jugador, `controls.ts:126`).

### 2. Girar el libro hacia la entrada

`rotationY: Math.PI` en vez de `0`: el grupo completo de
`lecternNotebook` (pilar + cuaderno flotante) gira 180°, así la cara
frontal del `PlaneGeometry` (normal +Z por defecto) queda mirando hacia
-Z — la dirección desde la que camina el jugador al entrar
(`teleportPlayer`/spawn dejan al jugador en `z` menor que `room.z`,
mirando +Z). Esto resuelve AC-7 sin tocar el material ni el mesh.

### 3. Libro con volumen (AC-8, AC-9)

Reemplazar el único `PlaneGeometry` de `lecternNotebook` (props.ts:789-808)
por una pequeña construcción de 2 piezas dentro del mismo grupo `float`:

```ts
// portada + lomo: una caja delgada detras de la pagina (1 draw call extra)
const cover = new Mesh(
  new BoxGeometry(0.66, 0.52, 0.06),
  toonMat(trim), // mismo acento de la sala que ya usa el "lip" del pilar
)
cover.position.z = -0.03
cover.castShadow = true
// pagina existente, ahora AL FRENTE de la portada (no reemplaza, se apoya)
const page = new Mesh(
  new PlaneGeometry(0.6, 0.48),
  new MeshBasicMaterial({ map: notebookTexture(opts.notebook) }),
)
page.position.z = 0.005
page.userData.noOutline = true
float.add(halo, cover, page)
```

Con esto:

- Desde el frente (-Z, la entrada) se ve la página con el texto —
  comportamiento igual al actual, sin regresión.
- Desde CUALQUIER otro ángulo (atrás, costados) se ve la caja sólida
  (portada/lomo, color del acento de la sala) en vez de un hueco
  invisible — resuelve AC-8.
- El objeto ya no es una lámina plana sino un cuerpo con espesor real —
  resuelve AC-9.
- `cover` SÍ participa del contorno de tinta genérico normal (es un mesh
  chico, no un merge con posiciones horneadas lejos del origen — no
  aplica el bug de la Feature C aquí, porque `lecternNotebook` no usa
  `mergedBoxes`/`outlineGroup` sobre geometría con offsets grandes; el
  grupo entero está ya centrado en `opts.position` como transform local).
- Costo: +1 draw call por sala (el pilar ya sumaba 2: `pedestal` + `lip`;
  ahora 3: `pedestal` + `lip` + `cover`, más `page`/`halo` que ya llevan
  `noOutline`/son planos sin contorno). Sigue muy por debajo del
  presupuesto de <100 draw calls por sala.

### 4. Por qué no re-diseñar como "libro abierto" (2 páginas en V)

Se consideró un libro abierto con dos planos en ángulo (más parecido a
un libro real abriéndose), pero se descarta para este alcance: exige
geometría con bisagra + UVs partidas + más draw calls, y no resuelve
mejor los AC (el problema reportado es "se ve una lámina", no "no se
abre"). La caja de portada + página es la mejora mínima que ya cumple
"tiene estilo de libro" y "siempre se ve algo sólido".

## Verificación de la feature

- Typecheck (`astro check`).
- Smoke visual en `aula` y en al menos 1 sala más (para confirmar que el
  fix de `infoKit` es realmente compartido, no solo del aula):
  1. Entrar a la sala caminando desde la puerta → el libro se lee de
     frente, sin rodearlo.
  2. Caminar hasta el pilar → confirmar que ahora está en el centro
     visual de la sala, no pegado a la entrada.
  3. Rodear el pilar hasta el lado opuesto → confirmar que se ve la
     portada/lomo (nunca un hueco).
  4. Confirmar que el spawn inicial del jugador en `aula` ya NO aparece
     encimado con el collider del pilar.
