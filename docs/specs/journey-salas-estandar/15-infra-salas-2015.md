# 15 — Infra: insercion de las salas 2015 (`iai` + `asesoria`)

> Informe AUTOCONTENIDO de la "mini-etapa" de infraestructura que inserta las
> 2 salas nuevas de 2015 en el recorrido (RoomId 8 -> 10), convierte el Aula
> en "universidad pura" y actualiza los datos del CV. Es PREREQUISITO de los
> informes [16-sala-iai.md](16-sala-iai.md) y
> [17-sala-asesoria.md](17-sala-asesoria.md).
> Leer antes: [README](README.md) + [02-el-canon-de-sala.md](02-el-canon-de-sala.md)
> + [ESTADO.md](ESTADO.md).

## Contexto

El recorrido tenia 8 salas y las experiencias `iai` (2015) y
`projects-degrees` (nov-dic 2015) vivian como guiños del Aula. Decision del
usuario (2026-07-05): ganan sala propia, en orden cronologico
`ipasme -> iai -> asesoria -> cofasa`. El recorrido pasa a **10 salas**:

```text
aula(0) -> corpoelec(1) -> ipasme(2) -> iai(3) -> asesoria(4) -> cofasa(5)
  -> dibal(6) -> goodmeal(7) -> destacame(8) -> futuro(9)
```

Investigacion que sustenta este informe (leer si hace falta mas contexto):

- `docs/progress/explore_iai_yaracuy.md` — dominio de presupuestos de obra
  publica venezolana (COVENIN, APU, valuaciones) + ambiente + Yaracuy 2015.
- `docs/progress/explore_iai_naming.md` — **CONFIRMA** el nombre "Instituto
  Autonomo de Infraestructura del Estado Yaracuy (IAI)" via sentencia TSJ
  N° 01229 (24-oct-2012) + noticia oficial de la gobernacion. Singular
  "Infraestructura". Predecesor del IVOPEY (reorganizado 23-dic-2015).
- `docs/progress/explore_salud_san_felipe.md` — candidatos de salud; el
  usuario reconocio **PROSALUD / Corposalud Yaracuy** (Instituto Autonomo de
  la Salud del Estado Yaracuy).

## Decisiones del usuario (2026-07-05 — NO reabrir)

1. **Aula -> universidad pura**: deja de leer `iai`+`projects-degrees`; pasa
   a textos sinteticos derivados de `education` (UPTYAB 2011-2016). Sus NPCs
   se re-enfocan a la vida universitaria; el profesor puede ANTICIPAR las
   historias (foreshadowing) sin contarlas completas.
2. **CV se actualiza completo** (DB fuente de verdad + regenerar cache):
   - `iai`: company pasa de "Proyecto académico" a **"Instituto Autónomo de
     Infraestructura del Estado Yaracuy (IAI)"**. Fechas quedan ene-dic 2015.
   - `projects-degrees`: fechas pasan a **nov-dic 2015**; se ELIMINA la
     segunda tesis de la narrativa (fue UNA tesis, para PROSALUD); company
     queda "Asesoría de proyectos de grado".
3. **Stack IAI** = escritorio **Java (Swing)** con una PC-servidor central en
   red local. **Stack PROSALUD** = **web local PHP + MySQL** (XAMPP).
4. **Narrativa projects-degrees**: asesoria de desarrollo de tesis + el
   desarrollo mismo — a Pablo **le pagaron** por desarrollar el software del
   equipo (el solo) y por enseñarles como exponer/defender la solucion.
5. **Id de sala** de projects-degrees = **`asesoria`** (el slug del CV y su
   URL `/experience/projects-degrees/` NO cambian).
6. Ambiente sala asesoria = instituto de salud + rincon de asesoria; pasado =
   instituto en caos + mesa de tesis bloqueada (ver informe 17).

## Checklist de la sesion

- [ ] Paso 0: working tree limpio (si hay WIP ajeno, NO revertirlo; preguntar)
- [ ] CV: textos nuevos aplicados en la DB + cache regenerado (o fallback
      acordado con Pablo, ver seccion CV)
- [ ] `lib/rooms.ts`: RoomId 10 + specs `iai`/`asesoria` + aula sintetica
- [ ] `engine/world.ts`: manifest con stubs `iai`/`asesoria`
- [ ] `engine/themes.ts`: 2 paletas nuevas + 2 PAST_CAPTIONS
- [ ] stubs `rooms/iai.ts` + `rooms/asesoria.ts` (placeholder "en construccion")
- [ ] Aula: dialogos re-enfocados (universidad pura + foreshadowing)
- [ ] typecheck + lint + build + smoke (10 salas montan via teleport)
- [ ] commit en `feature/journey-salas-estandar` + actualizar ESTADO.md

## Paso 0 — estado de partida

Las 7 salas de la Etapa 2 original estan HECHAS (la ultima, `futuro`, en el
commit `a50f073d`). Esta mini-etapa se ejecuta SOBRE ese estado: 8 salas
funcionando + el cierre C14-C17 aun pendiente. Verificar `git status` al
empezar: si hay WIP ajeno en el working tree, NO revertirlo (preguntar a
Pablo).

> La sala `futuro` ya construida usa `room.index` dinamico, igual que todas:
> la insercion de `iai`/`asesoria` la corre del index 7 al 9 sin tocar su
> codigo. Verificar en el smoke que sigue montando bien.

## Tarea 1 — Actualizacion del CV (fuente de verdad: DB Neon)

El cache `packages/content/src/data-cache/experiences.json` se genera con
`scripts/fetch-cv-cache.mjs` desde el API GET /cv (Lambda `cv` -> Neon).
**NO se edita a mano** (regla del modulo `data/experiences/index.ts`).

Flujo canonico: Pablo aplica los textos via el admin (`/cv`, operation
`content` del Lambda `cv`) -> regenerar el cache con el script -> commit del
JSON regenerado. Si Pablo prefiere diferir la DB, el fallback ACORDADO en
sesion es editar el cache localmente Y dejar anotado en ESTADO.md el
pendiente "sincronizar DB antes del cierre C17". Preguntarle al empezar.

### Cambios a `iai`

- `company`: `"Instituto Autónomo de Infraestructura del Estado Yaracuy (IAI)"`
  (en: identico — nombre propio). Singular "Infraestructura" (forma juridica
  del TSJ).
- Fechas: quedan `2015-01` -> `2015-12`.
- El resto de textos NO cambia (ya describen el sistema de gestion de obras,
  presupuestos y seguimiento con red cliente-servidor).

### Cambios a `projects-degrees` (reescritura a 1 tesis + PROSALUD)

- `start`: `2015-11` · `end`: `2015-12` · `company` queda
  `"Asesoría de proyectos de grado"` · `metricsEstimated: true` se mantiene.
- Textos nuevos propuestos (ajustar en sesion si Pablo corrige):

**summary.es**: "Me contrataron para rescatar una tesis bloqueada: desarrollé
e implanté yo solo la solución para PROSALUD y preparé al equipo para
defenderla."
**summary.en**: "I was hired to rescue a stalled thesis: I single-handedly
built and deployed the solution for PROSALUD and coached the team through
their defense."

**responsibilities.es**:

1. "Diagnóstico de los puntos de falla en el código y la arquitectura
   heredados de un proyecto de grado bloqueado durante meses."
2. "Definición de la arquitectura y del plan de trabajo para reencaminar el
   proyecto hacia su entrega."
3. "Desarrollo e implantación completa de la solución web (PHP y MySQL sobre
   la red local) para el Instituto Autónomo de la Salud del Estado Yaracuy
   (PROSALUD)."
4. "Mentoría técnica de los tesistas, explicando cada implementación y el
   razonamiento detrás de las decisiones."
5. "Preparación del equipo para la defensa: ensayos de la exposición y
   documentación de soporte."

(en: analogo, redactar en la sesion.)

**achievements.es**:

1. "Reencaminé y completé en aproximadamente una semana una tesis que el
   equipo no había logrado avanzar en varios meses."
2. "Desarrollé e implanté yo solo la solución para PROSALUD, cobrando por el
   desarrollo y por la capacitación del equipo."
3. "Dejé a los tesistas en capacidad de explicar y sostener técnicamente su
   propia solución en la defensa."
4. "Reduje el tiempo estimado de finalización de meses a días mediante un
   diagnóstico técnico preciso y un plan de trabajo claro."

(en: analogo.) `skillsTechnical`/`skillsSoft` quedan; opcional agregar
"PHP"/"MySQL" a skillsTechnical si Pablo confirma.

> El docstring de `data/experiences/index.ts` dice "9 puestos" — sigue siendo
> 9 (solo se editan 2 entradas, no se agregan).

## Tarea 2 — RoomId 8 -> 10 + stubs (los 4 puntos de infra)

Mismo patron del commit C2 de Etapa 1 (stubs con cartel "en construccion" +
barrera con el acento):

1. `lib/rooms.ts`: agregar `'iai'` y `'asesoria'` al union `RoomId` (entre
   `'ipasme'` y `'cofasa'`) + 2 entradas en `ROOM_SPECS` en esa posicion:

   - `iai`: `slugs: ['iai']` · title `{ es: 'IAI — Obras publicas', en: 'IAI
     — Public works' }` · represents es: "Esta sala representa mi proyecto de
     grado hecho realidad: el sistema de presupuestos y seguimiento de obras
     del Instituto Autonomo de Infraestructura del Estado Yaracuy, con un
     equipo de tres y una PC como servidor central." (en: analogo).
   - `asesoria`: `slugs: ['projects-degrees']` · title `{ es: 'Asesoria —
     PROSALUD', en: 'Advisory — PROSALUD' }` · represents es: "Esta sala
     representa mi primer trabajo pagado como consultor: rescatar en una
     semana una tesis bloqueada, desarrollar yo solo el sistema de PROSALUD y
     enseñar al equipo a defenderlo." (en: analogo).

2. `engine/world.ts`: 2 entradas en el manifest `WORLD` apuntando a los stubs.
3. `engine/themes.ts`: 2 entradas en `THEMES` + `PAST_CAPTIONS`:

   | RoomId | wall | floor | accent | trim | lightColor | Mood |
   |--------|------|-------|--------|------|------------|------|
   | `iai` | `#f2f0eb` | `#d9dbdd` (gris cemento) | `#d9a013` (ambar obra) | `#8f959e` (gris concreto) | `#f6f4ee` | obra publica: ambar + concreto; rojo Yaracuy SOLO en props (valla/bandera). Distinto del naranja corpoelec |
   | `asesoria` | `#f2f0eb` | `#dce6de` (verde grisaceo) | `#2e8b57` (verde salud) | `#7a4fc0` (morado asesoria, eco del aula) | `#f2f8f4` | salud publica + academia; distinto del azul+menta de ipasme |

   PAST_CAPTIONS es/en: iai -> "IAI, meses antes — presupuestos a mano" /
   "IAI, months earlier — budgets by hand"; asesoria -> "PROSALUD, meses
   antes — la tesis bloqueada" / "PROSALUD, months earlier — the stalled
   thesis" (ajustar al formato exacto de las captions existentes).

4. `rooms/iai.ts` + `rooms/asesoria.ts`: stubs placeholder (reusar
   `stub.ts`). Los pasados y dialogos NO se crean aqui (van en los informes
   16 y 17).

Lo que escala solo (NO tocar): `lib/layout.ts`, `lib/tour.ts`,
`engine/hud.ts` (teleport itera rooms), fallback `CvSections` (data-driven).

> Crear AMBOS stubs en esta sesion deja los indices estables para las
> sesiones de sala: `iai` = index 3 (ids `talk-3-*`, `showcase-3`,
> `portal-3`), `asesoria` = index 4. Las salas posteriores se corren:
> cofasa 5, dibal 6, goodmeal 7, destacame 8, futuro 9 — es automatico
> (los ids derivan de `room.index` en runtime, verificado).

## Tarea 3 — Aula -> universidad pura

1. `lib/rooms.ts`: la spec `aula` pasa a `slugs: []` + `synthetic` (mismo
   patron que `futuro`): `year: '2011 — 2016'` y `RoomTexts` es/en derivados
   de `education` (entry `uptyab`: Universidad Politecnica Territorial de
   Yaracuy "Aristides Bastidas", 2011-2016; leer el JSON de education para
   titulo/carrera exactos) + el hilo autodidacta (`youtube-autodidacta`,
   2012+). Redactar en la sesion:
   - retos: pagarse la carrera trabajando, aprender a programar de verdad
     (POO, redes, BD), primeros liderazgos academicos, disciplina.
   - aprendizajes: base de ingenieria de software, redes cliente-servidor,
     el habito autodidacta, liderar y documentar.
   - `represents` del aula se ajusta: universidad como CIMIENTO (sin narrar
     el IAI ni el rescate).
2. `engine/dialogs/aula-presente.ts`: re-enfocar los arboles que hoy cuentan
   el rescate/IAI completos ("Compañero del proyecto", "Estudiante
   desatascado", "Tesista aliviada", "Tesista de los sockets", "Profesor de
   la catedra"):
   - El profesor habla del potencial de Pablo + FORESHADOWING: "lo del
     instituto de obras y el rescate de la tesis... eso miralo dos salas mas
     adelante" (una linea, sin spoiler).
   - Los estudiantes hablan de la vida universitaria: clases, laboratorio,
     redes, el server del aula, Pablo ayudando a otros.
   - NO duplicar las historias que ahora viven en 16 (IAI) y 17 (asesoria).
3. `rooms/aula.ts` (wallArt): el cuadro/lamina del "plan de rescate de 1
   semana" (si existe como tal) se ELIMINA del aula (esa pieza se muda
   conceptualmente a la sala asesoria); los diagramas cliente-servidor se
   quedan (semilla academica).
4. El PASADO del aula NO SE TOCA (decision original del plan).

## Verificacion (antes del commit)

```bash
pnpm --filter @portfolio/journey typecheck
pnpm --filter @portfolio/journey lint       # o el biome check del repo
pnpm --filter @portfolio/journey build
pnpm --filter @portfolio/journey dev        # smoke browser (localhost:4327)
```

Smoke minimo (patron `tmp/journey-smoke-*.py` de las sesiones previas): las
10 salas montan via teleport; `iai` y `asesoria` muestran el placeholder "en
construccion"; el aula muestra los textos nuevos y sus dialogos re-enfocados;
el fallback Static (CvSections) sigue mostrando las 9 experiencias del CV.

Commits sugeridos (verificacion incremental por commit):

1. `feat(content): actualiza CV de iai y projects-degrees (IAI + PROSALUD)`.
2. `feat(journey): infra 10 salas (iai + asesoria stubs) + aula universidad pura`.

Actualizar [ESTADO.md](ESTADO.md) (fila "infra-2015" HECHA + sha) y dar el
prompt de la siguiente sesion (sala `iai`, informe 16).
