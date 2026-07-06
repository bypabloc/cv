# journey-salas-estandar — estandarizacion + 10 salas del journey 3D

> Plan de refactor del journey 3D (`apps/journey`, motor Three.js vanilla
> manga-ink): estandariza el canon de sala (NPCs con 2 enfoques, cuadros
> de rubro, showcase de software junto a la puerta, paredes blancas +
> acento del rubro), refactoriza las 3 salas actuales, unifica Destacame,
> implementa las 4 salas pendientes + la sala Futuro, y refactoriza TODOS
> los pasados (excepto Aula). Ampliacion 2026-07-05: las experiencias 2015
> (`iai` + `projects-degrees`) ganan sala propia. El resultado es un
> recorrido de **10 salas** cronologicas + futuro, data-driven desde
> `@portfolio/content`.

## Estado

| Fase | Estado |
|------|--------|
| Lectura del plan `journey-3d-cv` (Propuesta A) | HECHO |
| Mapa tecnico del motor (world/layout/tour/hud/props/themes/dialog) | HECHO |
| Decisiones del usuario (6 tandas AskUserQuestion, 2026-07-05) | HECHO |
| Investigacion por sala (7 informes en `NN-sala-<id>.md`) | EN CURSO |
| Plan detallado (este doc) | HECHO |
| ETAPA 1 (estandarizacion + Aula) | PENDIENTE |
| ETAPA 2 (7 salas 1 a 1) | PENDIENTE — ver [ESTADO.md](ESTADO.md) |

## Flujo del plan (2 etapas + stop gate)

```text
ETAPA 1 — ESTANDARIZACION (una sesion, secuencial)
  C2 infra RoomId->8 + rename cima->destacame (stubs)
    -> C3 paleta paredes-blancas (themes.ts)
    -> C4 helpers canon (officeLayout/npcCoworkers/wallArt/softwareShowcase)
    -> C5 partir pasados en rooms/past/<id>.ts + dispatcher
    -> C6 AULA refactor (prueba del canon, AC-9)
    -> [ verificar Etapa 1: typecheck + build + visual ]
       ===============================================
       || STOP GATE: commit en la rama, NO merge,   ||
       || DETENER el plan. Retomar en otras sesiones ||
       ===============================================

ETAPA 2 — SALAS 1 A 1 (otras sesiones, 1 sala por sesion, orden sugerido)
  cada sesion:
     leer README + 02-el-canon + NN-sala-<id>.md (research completa)
     -> crear SOLO esa sala (presente + pasado + dialogos + showcase)
     -> verificar -> commit en la MISMA rama -> actualizar ESTADO.md
  orden cronologico sugerido (puedes saltarte):
     corpoelec -> ipasme -> cofasa -> dibal -> goodmeal -> destacame -> futuro

ETAPA 2b — INSERCION SALAS 2015 (ampliacion 2026-07-05, mismas reglas)
  [15-infra-salas-2015.md] infra RoomId->10 + stubs iai/asesoria + aula
    universidad pura + CV (PREREQUISITO de las 2 salas)
    -> [16-sala-iai.md] sala IAI (1 sesion)
    -> [17-sala-asesoria.md] sala Asesoria/PROSALUD (1 sesion)

  -> cuando TODAS las salas estan listas: cierre (audio + perf + rule)
     -> merge unico a dev -> git rm -r la carpeta del plan
```

- **Rama unica larga** `feature/journey-salas-estandar` (decision del usuario):
  Etapa 1 y TODAS las salas (incluidas las 2015) viven en la MISMA rama,
  **sin merge hasta el final**.
  La carpeta del plan SOBREVIVE hasta que se cierra la ultima sala (es la cola
  de trabajo persistente entre sesiones).
- El **STOP GATE** esta despues de la Etapa 1: el plan se DETIENE ahi. Las
  salas de Etapa 2 se ejecutan **1 a 1 en sesiones separadas** leyendo su
  `NN-sala-<id>.md`.

## Escala

**Large** (18+ archivos: 5 escenas nuevas + refactor + past por sala +
helpers en props.ts + themes + rooms + world + ~35 dialogos + 7 informes de
sala). Ver [04-descomposicion.md](04-descomposicion.md) (seccion 8),
[05-commits.md](05-commits.md) (seccion 9),
[06-paralelizacion-worktrees.md](06-paralelizacion-worktrees.md) (10) y
[07-verificacion-e2e.md](07-verificacion-e2e.md) (11).

## Cuando leer cada archivo

| Archivo | Cuando leer |
|---------|-------------|
| README.md (este) | Indice, flujo, protocolo de retoma, decisiones, mapa de salas |
| [ESTADO.md](ESTADO.md) | Progreso por sala (pendiente/en curso/hecho). Leer al RETOMAR en otra sesion |
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Contexto, solucion (1-2), criterios de aceptacion (3) |
| [02-el-canon-de-sala.md](02-el-canon-de-sala.md) | El ESTANDAR: los 4 helpers + estructura fija presente/pasado + paleta. SIEMPRE leer antes de crear una sala |
| [03-salas.md](03-salas.md) | Resumen sala por sala (indice a los informes detallados) |
| [08-sala-corpoelec.md](08-sala-corpoelec.md) .. [14-sala-futuro.md](14-sala-futuro.md) | Informe AUTOCONTENIDO de cada sala de Etapa 2 (research completa: exp, web oficial, guiños, NPCs, dialogos, items, pasado, showcase). Leer el de la sala que se va a crear |
| [15-infra-salas-2015.md](15-infra-salas-2015.md) | Etapa 2b: infra RoomId->10 + stubs `iai`/`asesoria` + aula universidad pura + actualizacion del CV. PREREQUISITO de los informes 16 y 17 |
| [16-sala-iai.md](16-sala-iai.md) · [17-sala-asesoria.md](17-sala-asesoria.md) | Informe AUTOCONTENIDO de cada sala 2015 (mismo formato que 08-13) |
| [04-descomposicion.md](04-descomposicion.md) | Seccion 8: tareas atomicas + paralelizacion |
| [05-commits.md](05-commits.md) | Seccion 9: secuencia de commits por etapa |
| [06-paralelizacion-worktrees.md](06-paralelizacion-worktrees.md) | Seccion 10: paralelizacion (N/A entre etapas: 1 sala por sesion) |
| [07-verificacion-e2e.md](07-verificacion-e2e.md) | Seccion 11: verificacion (por etapa + final) |

## Protocolo de retoma (ETAPA 2 — leer al empezar una sesion nueva)

Una sesion que crea una sala de Etapa 2 debe:

1. **Leer** este README, [ESTADO.md](ESTADO.md), [02-el-canon-de-sala.md](02-el-canon-de-sala.md)
   y el `NN-sala-<id>.md` de la sala a crear.
2. **Confirmar** que la ETAPA 1 esta HECHA (los 4 helpers en `props.ts`, el
   theme paredes-blancas, los pasados partidos). Si no, PARAR: la Etapa 1 es
   prerequisito. Para las salas 2015 (`iai`/`asesoria`), confirmar ADEMAS que
   el informe [15-infra-salas-2015.md](15-infra-salas-2015.md) esta HECHO
   (`RoomId` de 10, stubs, CV actualizado).
3. **Elegir** la siguiente sala pendiente segun [ESTADO.md](ESTADO.md) (orden
   cronologico sugerido; se puede saltar).
4. **Crear SOLO esa sala**: `rooms/<id>.ts` (presente) + `rooms/past/<id>.ts`
   (pasado, menos aula) + `dialogs/<id>-presente.ts` + `<id>-pasado.ts`,
   siguiendo el canon y el informe de la sala.
5. **Verificar**: `pnpm --filter @portfolio/journey typecheck` + `build` +
   recorrido visual (`pnpm --filter @portfolio/journey dev`, localhost:4327).
6. **Commit** en la MISMA rama `feature/journey-salas-estandar` (NO merge).
7. **Actualizar** [ESTADO.md](ESTADO.md): marcar la sala HECHA + commit sha.
8. **NO** desplegar (local-first). El merge a `dev` es al final, con las 7.

> El protocolo tambien vive en la memoria del proyecto (engram, key
> `journey-salas-etapa2-protocolo`) para que cualquier sesion lo recuerde.

## Decisiones cerradas (2026-07-05 — NO reabrir sin el usuario)

1. **Alcance**: refactor de las 3 salas actuales (Aula, CORPOELEC, CIMA) +
   implementar las 4 pendientes (IPASME, Cofasa, Dibal, GoodMeal) +
   **unificar** las 3 Destacame en 1 sala + **nueva sala Futuro** + refactor
   de TODOS los pasados **excepto Aula**. Ademas: helpers reutilizables + doc
   del estandar (spec + rule). Fallback Static, teleport, tour y **audio
   ambiente por sala** entran en este plan.
2. **Recorrido final = 10 salas cronologicas + futuro** (ampliado
   2026-07-05): `aula -> corpoelec -> ipasme -> iai -> asesoria -> cofasa ->
   dibal -> goodmeal -> destacame -> futuro`. `RoomId` paso de 3 a 8 ids en
   Etapa 1 y pasa de 8 a 10 en el informe 15 (Etapa 2b).
3. **Estandar de NPCs (2 enfoques, 4-5 por sala)**: cada sala tiene ~2
   **compañeros** de desarrollo (con los que Pablo construyo) + ~2 **personal
   del sitio** (quienes pedian features y a quienes ayudo) + ocasional 1
   **jefe/cliente/profe**. Todos conversables (arbol de dialogo + burbuja).
4. **Estandar de showcase de software** (junto a la puerta, TODAS menos Aula):
   monitor Canvas en loop (ambiente) + **panel HTML operable al pulsar E**
   con la demo del sistema real. `E` cicla a la siguiente demo del sistema.
   Los mockups se diseñan a partir del **branding real** de cada web oficial.
5. **Destacame unificada = 2 AREAS reales**: (A) **PagaloAqui** (Santander /
   Santander Consumer / Scotiabank) y (B) **producto Destacame**
   (destacame.cl / destacame.com.mx). La arquitectura fullstack + Design
   System + microservicios + liderazgo NO es una tercera area: son **guiños
   intrinsecos** (props ambientales, pantallas de fondo, dialogos). Un
   showcase por area; `E` cicla las demos dentro de cada uno.
6. **Sala Futuro = vision profesional**: hacia donde va Pablo
   (staff/principal, mas IA/arquitectura, mentoria). Roadmap en pizarra,
   puerta "Proximamente", CTA de contacto fuerte. Cierre inspiracional.
7. **Paredes blancas uniformes + acento del rubro** en piso, zocalo (trim),
   marcos, props firma, pantallas y color de luz. Blanco hueso (~`#f2f0eb`)
   en TODAS las salas presentes. La identidad la da el **acento**, no la
   pared. (Los pasados mantienen su sepia.)
8. **Cuadros de rubro en la pared** (helper `wallArt`): 2-4 laminas Canvas
   (estilo tinta plana) por sala con imagenes del rubro (CORPOELEC:
   generadores, transformadores, lineas de transmision). 1-2 por sala son
   **inspeccionables** (abren ficha). Ademas los certificados reales del CV
   pueden colgar como cuadros inspeccionables.
9. **Estetica**: oficina base uniforme (escritorios, gente sentada con
   laptops, kit info estandar, showcase junto a puerta) + **guiños fuertes
   del rubro** sobre esa base (props firma identificables). Coherencia +
   identidad por sala.
10. **Perf**: presupuesto **<100 draw calls/sala**. NPCs conversables (4-5)
    individuales; el relleno de gente/mobiliario de fondo se hace con
    props fusionados (`outlinedMergedBoxes`) — NO se puede cargar el NPC
    "al pulsar E" porque hay que verlo para acercarse. AC de perf por sala.
11. **Pasados** (refactor de todos menos Aula): mismo nivel que el presente
    — ambiente sepia del rubro SIN el sistema, 2-3 NPCs frustrados con
    dialogo del "antes", objeto de busqueda lenta + panel de historia.
12. **Contenido de dialogos y mockups**: Claude los redacta **data-driven**
    (derivados de `@portfolio/content` + research en
    `docs/progress/explore_empresas_*.md` + branding de las webs oficiales).
    El usuario revisa y corrige despues.

### Ampliacion 2026-07-05 — salas 2015 (decisiones cerradas, NO reabrir)

1. **`iai` y `projects-degrees` ganan sala propia** entre `ipasme` y
    `cofasa` (orden: ipasme -> iai -> asesoria -> cofasa). Recorrido = 10
    salas. Ids de sala: `iai` y `asesoria` (el slug `projects-degrees` y su
    URL no cambian).
2. **Aula -> universidad pura**: deja los slugs 2015 y pasa a textos
    sinteticos desde `education` (UPTYAB); sus NPCs se re-enfocan (el
    profesor solo ANTICIPA las historias). Detalle en el informe 15.
3. **CV se actualiza** (DB fuente de verdad + regenerar cache): `iai`
    company = "Instituto Autonomo de Infraestructura del Estado Yaracuy
    (IAI)" (confirmado por sentencia TSJ 01229/2012 — singular
    "Infraestructura"), fechas ene-dic 2015; `projects-degrees` = nov-dic
    2015, narrativa reescrita a UNA tesis para PROSALUD (la segunda tesis se
    ELIMINA), company queda "Asesoria de proyectos de grado".
4. **Stacks fieles a la epoca**: IAI = escritorio Java (Swing) + PC-servidor
    en red local; PROSALUD = web local PHP + MySQL (XAMPP). El software de
    PROSALUD = citas/turnos + farmacia/inventario + admision/afiliados.
5. **Narrativa asesoria**: a Pablo LE PAGARON por desarrollar el solo la
    solucion del equipo de tesis y por enseñarles a exponer/defender. Sala =
    instituto de salud + rincon de asesoria; pasado = instituto en caos +
    mesa de tesis bloqueada.

## Mapa de salas (10 salas, data-driven)

| Orden | RoomId | Etapa | Informe | Slug(s) `@portfolio/content` | Acento (guiño) |
| --- | --- | --- | --- | --- | --- |
| 0 | `aula` | **1** | (en [03-salas.md](03-salas.md)) | (sinteticos desde `education`, tras informe 15) | azul `#2f6fd0` + morado |
| 1 | `corpoelec` | 2 | [08-sala-corpoelec.md](08-sala-corpoelec.md) | `corpoelec` | naranja `#e2572b` + amarillo |
| 2 | `ipasme` | 2 | [09-sala-ipasme.md](09-sala-ipasme.md) | `ipasme` | azul institucional + verde menta |
| 3 | `iai` | **2b** | [16-sala-iai.md](16-sala-iai.md) | `iai` | ambar obra `#d9a013` + gris concreto |
| 4 | `asesoria` | **2b** | [17-sala-asesoria.md](17-sala-asesoria.md) | `projects-degrees` | verde salud `#2e8b57` + morado |
| 5 | `cofasa` | 2 | [10-sala-cofasa.md](10-sala-cofasa.md) | `cofasa` | azul Cofasa + andon |
| 6 | `dibal` | 2 | [11-sala-dibal.md](11-sala-dibal.md) | `dibal` | navy + teal Dibal |
| 7 | `goodmeal` | 2 | [12-sala-goodmeal.md](12-sala-goodmeal.md) | `goodmeal` | teal GoodMeal + kraft |
| 8 | `destacame` | 2 | [13-sala-destacame.md](13-sala-destacame.md) | `destacame-frontend`, `destacame-architect` | azul `#0052cc` |
| 9 | `futuro` | 2 | [14-sala-futuro.md](14-sala-futuro.md) | (sin slug: sintetica) | azul-violeta premium |

> **Etapa 1** (antes del stop): estandarizacion + `aula` (prueba del canon).
> El viejo id `cima` se **renombra** a `destacame` en la infra de Etapa 1
> (queda como stub hasta que Etapa 2 la construye). **Etapa 2** (1 a 1): las
> 7 salas restantes, cada una con su informe autocontenido. **Etapa 2b**
> (ampliacion 2026-07-05): el informe 15 hace la infra (RoomId 8->10 + aula
> universidad pura + CV) y los informes 16/17 crean las salas `iai` y
> `asesoria`. Las salas `futuro` y `aula` NO tienen slug: sus textos son
> sinteticos.

## Los 4 puntos de infra por sala (el compilador los exige)

Agregar una sala toca 4 lugares (`RoomId` es un union literal -> falla el
build si falta alguno). Mapa tecnico verificado:

1. `lib/rooms.ts` — `RoomId` union + entrada en `MVP_ROOM_SPECS` (+ renombrar
   la constante a `ROOM_SPECS`, ya no es "MVP").
2. `engine/world.ts:116` — entrada en el manifest `WORLD` (dynamic import) +
   `rooms/<id>.ts` con `export default`.
3. `engine/themes.ts:40,111` — entrada en `THEMES` (paleta paredes-blancas) +
   `PAST_CAPTIONS`.
4. `engine/dialogs/<id>-presente.ts` + `-pasado.ts` + rama en
   `rooms/past/<id>.ts` (los pasados se parten en archivos por sala,
   decision 2 del usuario).

Lo que **escala solo** (no tocar): `lib/layout.ts` (cursor lineal),
`lib/tour.ts` (deriva de rooms), `engine/hud.ts` (menu teleport itera
rooms), fallback `CvSections.astro` (data-driven desde content). Confirmado
en el mapa tecnico.

## Reglas criticas (SIEMPRE / NUNCA)

- **SIEMPRE** paredes blanco hueso en toda sala presente; el color del rubro
  vive en piso/trim/props/luz/pantallas, NUNCA en la pared.
- **SIEMPRE** el texto del CV (retos/aprendizajes/fichas/dialogos) viaja como
  HTML real (panel DOM / `<Html>`), NUNCA como pixeles WebGL (SEO/ATS/a11y).
- **SIEMPRE** <100 draw calls por sala: props estaticos fusionados con
  `outlinedMergedBoxes` (2 draw calls por lote), NPCs conversables 4-5.
- **SIEMPRE** las salas y sus textos son data-driven desde
  `@portfolio/content` (salvo `futuro`, sintetica). Agregar experiencia =
  agregar sala.
- **SIEMPRE** el kit informativo estandar (`infoKit`: retos/aprendizajes/
  grieta/cuaderno) en las MISMAS posiciones en todas las salas (el aula es
  el canon).
- **SIEMPRE** cada sala presente (menos Aula) tiene el `softwareShowcase`
  junto a la puerta; Aula NO (es academica, sin producto).
- **SIEMPRE** los dialogos con el shape `NpcDialog` (`name/chatter/start/
  nodes`) validado por `defineDialog` (falla en DEV si el grafo es invalido).
- **NUNCA** cargar todas las salas de golpe: 1 solo content de sala vivo
  (regla de memoria del zone manager; iOS WebGL context limit).
- **NUNCA** romper el fallback 3 tiers (full/reduced/static). El Static ES el
  CV 2D indexable (`CvSections`), no se degrada.
- **NUNCA** eliminar el pasado de Aula (decision del usuario: esta perfecto).
- **NUNCA** atribucion de IA en commits, PRs ni codigo (politica del repo).
- **NUNCA** desplegar automaticamente al terminar: local-first (preferencia
  del usuario) — dejar commiteado + verificado + dar el comando
  `pnpm --filter @portfolio/journey dev` para que Pablo pruebe primero.

## Navegacion

- Contexto + AC: [01-contexto-y-decision.md](01-contexto-y-decision.md)
- El estandar (helpers + canon): [02-el-canon-de-sala.md](02-el-canon-de-sala.md)
- Sala por sala: [03-salas.md](03-salas.md)
- Ejecucion: [04-descomposicion.md](04-descomposicion.md) ·
  [05-commits.md](05-commits.md) ·
  [06-paralelizacion-worktrees.md](06-paralelizacion-worktrees.md) ·
  [07-verificacion-e2e.md](07-verificacion-e2e.md)
