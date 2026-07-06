# 17 — Sala Asesoria / PROSALUD (Etapa 2b, sala 2015-B)

> Informe AUTOCONTENIDO para crear la sala `asesoria` en una sesion aislada.
> Prerequisito: Etapa 1 hecha + informe [15-infra-salas-2015.md](15-infra-salas-2015.md)
> hecho (RoomId 10, stubs, themes, CV actualizado a 1 tesis + PROSALUD).
> Leer antes: [README](README.md) + [02-el-canon-de-sala.md](02-el-canon-de-sala.md)
> + [ESTADO.md](ESTADO.md).
>
> Experiencia real: slug `projects-degrees` (la URL del CV no cambia) ·
> company "Asesoria de proyectos de grado" · Venezuela · **nov-dic 2015** ·
> "Lider, Arquitecto y Desarrollador". A Pablo LE PAGARON por rescatar UNA
> tesis bloqueada por meses: desarrollo e implanto EL SOLO la solucion **web
> local (PHP + MySQL)** para **PROSALUD** (Instituto Autonomo de la Salud del
> Estado Yaracuy, San Felipe) y enseño al equipo a exponer/defender.
> `metricsEstimated: true`. La sala ocupa el **index 4** del recorrido (ids
> `talk-4-*`, `showcase-4`, `portal-4`; sala 5 de 10).

## Checklist de la sala

- [ ] `engine/rooms/asesoria.ts` (presente; reemplaza el stub)
- [ ] `engine/rooms/past/asesoria.ts` (pasado)
- [ ] `engine/dialogs/asesoria-presente.ts` (5 NPCs)
- [ ] `engine/dialogs/asesoria-pasado.ts` (3 NPCs)
- [ ] theme `asesoria` con `wall: '#f2f0eb'` (verificar, viene del informe 15)
- [ ] typecheck + build + smoke browser OK
- [ ] Actualizar [ESTADO.md](ESTADO.md)

## 1. Datos reales (es/en, textual — post-reescritura del informe 15)

**Identidad**: slug `projects-degrees` · company "Asesoría de proyectos de
grado" · country `Venezuela` · start `2015-11` end `2015-12` · seniority
`mid` · role es "Líder, Arquitecto y Desarrollador" / en "Leader, Architect
and Developer" · `metricsEstimated: true`.

**Summary (es, nuevo)**: "Me contrataron para rescatar una tesis bloqueada:
desarrollé e implanté yo solo la solución para PROSALUD y preparé al equipo
para defenderla."

**Responsibilities (es, nuevas)**: (1) diagnostico de los puntos de falla en
codigo/arquitectura heredados de un proyecto bloqueado por meses; (2)
arquitectura + plan de trabajo para reencaminarlo; (3) desarrollo e
implantacion completa de la solucion web (PHP + MySQL en red local) para
PROSALUD; (4) mentoria tecnica de los tesistas (explicando cada decision);
(5) preparacion de la defensa (ensayos de la exposicion + documentacion).

**Achievements (es, nuevos)**: (1) reencamino y completo en ~1 semana una
tesis que el equipo no habia logrado avanzar en meses; (2) desarrollo e
implanto el solo la solucion para PROSALUD, cobrando por el desarrollo y por
la capacitacion; (3) dejo a los tesistas en capacidad de explicar y sostener
su propia solucion en la defensa; (4) de meses a dias con diagnostico
preciso + plan claro.

> Si el CV aun muestra los textos viejos (2 tesis / ~6 estudiantes), PARAR:
> el informe 15 no se completo. La sala NUNCA menciona una segunda tesis
> (decision del usuario: eliminada).

> **Claves de diseño**: (a) stack **web local PHP + MySQL** (XAMPP) — el
> showcase se ve como NAVEGADOR de 2015 (unica sala venezolana web; contraste
> con los escritorios Java de IPASME/IAI). (b) Eje narrativo DOBLE: el
> RESCATE (meses bloqueado -> 1 semana) y la MENTORIA PAGADA (no solo
> programo: les enseño a defender). (c) Es el primer trabajo COBRADO como
> consultor independiente — germen del Pablo freelance/lider.

## 2. Rubro y ambiente

**PROSALUD** = Instituto Autonomo de la Salud del Estado Yaracuy (tambien
"Corposalud Yaracuy"). Instituto autonomo adscrito a la Gobernacion de
Yaracuy, sede en San Felipe: ente RECTOR de la red de atencion primaria del
estado (~610k hab, 14 municipios, ambulatorios + articulacion con Barrio
Adentro). Research completa: `docs/progress/explore_salud_san_felipe.md`.

**El software** (decision del usuario: administrativo, NO historias medicas):
sistema web integral con **citas/turnos + farmacia/inventario de insumos +
admision/afiliados**, servido en la red local del instituto (XAMPP en un
equipo del instituto, clientes por navegador).

**Ambiente objetivo (presente)**: la sede de PROSALUD ya con el sistema — dos
zonas: (a) el **instituto** (sala de espera con hilera de sillas + display de
turnos, mostrador de admision, estante de farmacia) y (b) el **rincon de
asesoria** (mesa de los tesistas con laptops + pizarra "plan de defensa" +
proyector con laminas). Es la sala PUENTE academia->consultoria: el morado
del aula reaparece como trim.

**Paleta** (theme del informe 15): pared `#f2f0eb`; piso verde grisaceo
`#dce6de`; acento **verde salud** `#2e8b57`; trim **morado asesoria**
`#7a4fc0` (eco del aula); luz `#f2f8f4`. Distinta del azul institucional +
verde menta de IPASME (aqui manda el verde + morado). Blanco clinico en
batas/mostrador; toques kraft/manila en el archivo del pasado.

## 3. Props firma del rubro (presente)

- **Sala de espera**: hilera de sillas (fusionadas) + **display de turnos**
  ("TURNO 042") sobre el mostrador — la pantalla del sistema.
- **Mostrador de admision** con monitor (afiliados en pantalla) + carnet de
  afiliado sobre el meson.
- **Estante de farmacia** con cajas de medicamentos + monitor de inventario
  (stock con una fila en alerta roja de minimo).
- **Cartelera de campañas** de salud (vacunacion, dengue) — textura PROSALUD.
- **El rincon de asesoria** (la firma UNICA de esta sala): mesa con los
  puestos de los tesistas (`officeLayout` de 3 puestos, 2 encendidos con
  codigo PHP), **pizarra con el plan de la semana** (7 dias: diagnostico ->
  arquitectura -> build -> implantacion -> ensayo) y **proyector + pantalla**
  con la lamina 1 de la defensa.
- **Torre XAMPP**: una PC del instituto con etiqueta "SERVIDOR LOCAL" (donde
  vive el sistema) + router/switch con cables.
- **Sobre de pago** discreto sobre la mesa de asesoria (guiño: el primer
  trabajo cobrado) — opcional, decidir en sesion.

## 4. Cuadros de pared (`wallArt`)

4 laminas, **2 inspeccionables** (★):

1. **★ Cartel institucional PROSALUD** (cruz + silueta de comunidad +
   "Instituto Autonomo de la Salud del Estado Yaracuy"). Ficha: que es
   PROSALUD (rector de la red de atencion primaria del estado, 14
   municipios) + por que un instituto asi necesitaba dejar los papelitos.
2. **★ El plan de rescate de 1 semana** (cronograma 7 dias con checkmarks).
   Ficha: la tesis llevaba MESES bloqueada; diagnostico en una tarde, plan
   claro, desarrollo en solitario, implantacion y ensayo de defensa — de
   meses a dias. (Esta pieza se MUDA aqui desde el aula, informe 15.)
3. **Diagrama del sistema** (navegador -> XAMPP/PHP -> MySQL en red local) —
   decorativa.
4. **Afiche "Defensa de proyecto de grado — Dic 2015"** (universidad) —
   decorativa, ata el hilo academico.

## 5. softwareShowcase — web local PHP 2015 (AC-6)

Junto a la puerta. Look **navegador 2015** (chrome de ventana con pestaña +
barra de direcciones `http://192.168.1.10/prosalud/`, UI tipo Bootstrap 2-3:
navbar verde, botones con degradado suave, tablas striped). Badge "RED
LOCAL · XAMPP". 3 demos que `E` cicla:

1. **Turnos / citas** — la cola del dia: tabla de turnos (numero, afiliado,
   servicio, estado) + boton "Asignar turno" que incrementa el numero del
   display.
2. **Farmacia / inventario** — stock de medicamentos e insumos con alerta de
   minimos (fila roja "acetaminofen — 12 unidades"), entradas/salidas,
   boton "Despachar".
3. **Admision / afiliados** — buscador de afiliados (cedula/nombre) con
   resultado al instante + ficha del afiliado + boton "Imprimir carnet".

## 6. NPCs del presente (5, 2 enfoques)

| NPC | Enfoque | Que cuenta |
| --- | --- | --- |
| **Jhonny Parra** | `[C]` tesista | Llevaban meses bloqueados y la fecha de defensa encima; Pablo diagnostico en una tarde que estaba roto; ahora entiende SU propio sistema linea por linea — "no nos regalo la tesis: nos la explico". |
| **Oriana Castillo** | `[C]` tesista | Le pagaron a Pablo por desarrollar Y por enseñarles a exponer; ensayaron la defensa con laminas hasta que salio sola; ella presenta el modulo de farmacia y ya no le tiembla la voz. |
| **Coromoto Linares** | `[P]` encargada de farmacia | Antes el inventario era un cuaderno con tachones; se enteraba de que no habia acetaminofen cuando ya no habia; ella pidio la alerta de minimos y Pablo se la puso en dos dias. |
| **Maigualida Torres** | `[P]` admision/citas | La cola de la mañana era papelitos numerados a mano y peleas; ahora el display canta el turno; busca un afiliado por cedula y sale al instante. |
| **Dra. Xiomara Graterol** | `[J]` directora/coordinadora | Encargo (y pago) la solucion; exigio que quedara IMPLANTADA y que los tesistas pudieran mantenerla; quedo tan conforme que firmo la carta de aceptacion para la universidad. |

> Ubicacion: Jhonny + Oriana en el rincon de asesoria (sentados en el
> `officeLayout`); Coromoto junto al estante de farmacia; Maigualida detras
> del mostrador de admision; Dra. Xiomara de ronda entre el mostrador y el
> rincon. Recortable a 4 quitando a Jhonny (Oriana absorbe el hilo del
> bloqueo).

## 7. Pasado (sepia — `rooms/past/asesoria.ts`)

**Instituto en caos + mesa de tesis bloqueada** (decision del usuario: los
DOS hilos en el mismo pasado):

Zona instituto (sin sistema):

- **Sala de espera desbordada**: sillas llenas (siluetas fusionadas) +
  **papelitos de turno numerados a mano** clavados en un pincho.
- **Cuaderno de farmacia** abierto con tachones + estante a medio inventariar
  (cajas apiladas sin orden).
- **Archivador de afiliados** con carpetas manila (buscar un afiliado =
  hojear).
- **Reloj de pared** (la mañana que se va en la cola).

Zona tesis (el rincon, bloqueado):

- **Mesa de tesistas**: laptop con **stack trace en pantalla** (rojo sobre
  sepia), pila de impresiones de intentos fallidos, tazas de cafe.
- **Pizarra SIN plan**: garabatos tachados + la **fecha de defensa** rodeada
  en rojo ("DEFENSA: 15 DIC").
- **Calendario** con los meses tachados (el tiempo perdido).

**Objeto de busqueda lenta**: atender a un afiliado sin el sistema — buscar
su carpeta en el archivador Y su papelito de turno (tarda; contraste con el
buscador + display del presente). Panel de historia (`onStory`) que narra los
dos hilos: el instituto en papel y la tesis varada, y como un contrato de
noviembre lo cambio todo en diciembre.

**NPCs del pasado** (3, arco antes/despues):

- **Jhonny (antes)** — junto al stack trace: "Cuatro meses. CUATRO. Y esto no
  compila desde agosto. La defensa es en diciembre y yo no se ni explicar lo
  que hay. Alguien nos hablo de un tal Pablo..."
- **Coromoto (antes)** — con el cuaderno: "Se me acabo el acetaminofen y me
  entere cuando la señora ya estaba en la ventanilla. Este cuaderno tiene mas
  tachones que letras."
- **Maigualida (antes)** — con los papelitos: "Numero cuarenta y dos... ¿y el
  cuarenta y uno? Señora, si pierde el papelito pierde el turno. Asi no se
  puede."

## 8. Retos y aprendizajes (infoKit)

**RETOS (es)**: rescatar en ~1 semana una tesis bloqueada por meses (con la
defensa encima); diagnosticar codigo y arquitectura heredados y priorizar lo
critico; desarrollar e implantar EN SOLITARIO una solucion web (PHP + MySQL
en red local) para un instituto publico de salud; enseñar al equipo a
sostener tecnicamente SU solucion (no solo entregarla); cumplir como primer
trabajo pagado de consultoria. **(en)** analogo.

**APRENDIZAJES (es)**: diagnostico tecnico preciso + plan de trabajo claro
convierten meses en dias; la mentoria vale tanto como el codigo (el equipo
defendio su tesis con solvencia); implantacion real en el sitio del cliente
(XAMPP, red local, datos administrativos de salud); arquitectura y
reestructuracion de proyectos heredados; consultoria: alcance, entrega y
cobro. Skills: Arquitectura de Software, Diagnostico Tecnico, Implementacion
de Soluciones, Reestructuracion de Proyectos + Consultoria Tecnica, Direccion
de Proyecto, Gestion del Tiempo, Resolucion de Problemas, Adaptabilidad.
**(en)** analogo.

## 9. Micro-interacciones propuestas (elegir en sesion con Pablo)

1. **Tomar un turno** (mostrador/display): E imprime un ticket que vuela al
   afiliado en la sala de espera + el display sube "TURNO 042 -> 043" con
   ding.
2. **Despachar un medicamento** (estante farmacia): E — una caja vuela del
   estante, el stock del monitor baja y si toca el minimo la fila se pone
   roja + alerta (la feature que pidio Coromoto).
3. **Ensayar la defensa** (rincon asesoria, la micro UNICA de esta sala): E
   cicla las laminas del proyector (titulo -> problema -> arquitectura ->
   demo -> conclusiones); al completar el ciclo, los tesistas celebran
   (jump/manos arriba) — el ensayo que salio perfecto.
4. **Laptop libre togglable** del `officeLayout` (patron estandar).

## Fuentes

`packages/content/src/data-cache/experiences.json` (slug projects-degrees,
post-informe 15) · `docs/progress/explore_salud_san_felipe.md` (PROSALUD:
adscripcion, red de ambulatorios, ambiente visual, colores salud) ·
decisiones del usuario 2026-07-05 (PROSALUD confirmado; 1 sola tesis —
eliminar la segunda; desarrollo en solitario PAGADO + enseñar a exponer;
stack web PHP+MySQL; ambiente instituto + rincon asesoria; pasado mixto;
fechas nov-dic 2015; id de sala `asesoria`; company queda "Asesoria de
proyectos de grado").
