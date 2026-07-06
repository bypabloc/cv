# 16 — Sala IAI (Etapa 2b, sala 2015-A)

> Informe AUTOCONTENIDO para crear la sala `iai` en una sesion aislada.
> Prerequisito: Etapa 1 hecha + informe [15-infra-salas-2015.md](15-infra-salas-2015.md)
> hecho (RoomId 10, stubs, themes, CV actualizado). Leer antes:
> [README](README.md) + [02-el-canon-de-sala.md](02-el-canon-de-sala.md) +
> [ESTADO.md](ESTADO.md).
>
> Experiencia real: slug `iai` · **Instituto Autonomo de Infraestructura del
> Estado Yaracuy (IAI)** · Venezuela · 2015 · "Lider de Desarrollo de
> Software y Arquitectura de Sistemas". Proyecto de grado LIDERADO por Pablo
> (equipo ~3): sistema de gestion de obras, presupuestos y seguimiento de
> avances, **escritorio Java** con una **PC como servidor central** en red
> local. `metricsEstimated: true`. La sala ocupa el **index 3** del recorrido
> (ids `talk-3-*`, `showcase-3`, `portal-3`; sala 4 de 10).

## Checklist de la sala

- [ ] `engine/rooms/iai.ts` (presente; reemplaza el stub)
- [ ] `engine/rooms/past/iai.ts` (pasado)
- [ ] `engine/dialogs/iai-presente.ts` (5 NPCs)
- [ ] `engine/dialogs/iai-pasado.ts` (3 NPCs)
- [ ] theme `iai` con `wall: '#f2f0eb'` (verificar, viene del informe 15)
- [ ] typecheck + build + smoke browser OK
- [ ] Actualizar [ESTADO.md](ESTADO.md)

## 1. Datos reales (es/en, textual)

**Identidad**: slug `iai` · company "Instituto Autonomo de Infraestructura
del Estado Yaracuy (IAI)" (post-informe 15) · country `Venezuela` · start
`2015-01` end `2015-12` · seniority `mid` · role es "Líder de Desarrollo de
Software y Arquitectura de Sistemas" / en "Software Development Lead and
Systems Architecture" · `metricsEstimated: true`.

**Summary (es)**: "Lideré el desarrollo y arquitectura de un proyecto
académico, coordinando un equipo pequeño hasta su entrega exitosa."

**Responsibilities (es)**: (1) liderazgo del equipo (distribucion de tareas +
seguimiento hasta la entrega); (2) arquitectura de la solucion y decisiones
tecnicas clave del sistema de gestion de obras; (3) **arquitectura de red con
una PC como servidor central** (acceso compartido a los datos); (4)
desarrollo e implementacion del sistema de gestion de obras, presupuestos y
seguimiento de avances; (5) documentacion tecnica del proyecto de grado
(justificando cada decision); (6) planificacion de hitos + gestion de
riesgos para cumplir plazos academicos.

**Achievements (es)**: (1) coordino un equipo de ~3 personas hasta la entrega
dentro del plazo; (2) arquitectura **cliente-servidor sobre red local** que
centralizo los datos y elimino copias desincronizadas; (3) consolidacion de
presupuestos y avances de obra: **de jornadas de trabajo manual a reportes
generados directamente por el sistema**; (4) documento la arquitectura
completa (base para defensa y mantenimiento).

**skillsTechnical**: Desarrollo de Software · Gestion de Datos · Gestion de
Infraestructura · Implementacion de Soluciones · Proyecto de Grado ·
Redaccion Tecnica. **skillsSoft**: Gestion de Proyectos · Gestion del
Presupuesto · Gestion del Trabajo · Planificacion de Proyecto · Trabajo
Colaborativo.

> **Claves de diseño**: (a) stack **Java ESCRITORIO** (Swing) sobre Windows +
> BD central en la PC-servidor — el showcase se ve como app de escritorio
> 2015, NUNCA navegador (mismo patron visual que IPASME, pero dominio de
> obras). (b) Eje narrativo: **de Excel/papel que se rehace cada mes -> un
> clic**; la PC-servidor que acabo con las copias desincronizadas. (c) Es el
> PRIMER liderazgo real de Pablo: la sala muestra a Pablo dirigiendo (mesa de
> coordinacion, plan de hitos en pizarra) — puente entre el aula y las salas
> laborales.

## 2. Rubro y ambiente

**IAI** = Instituto Autonomo de Infraestructura del Estado Yaracuy. Ente de
obra publica de la Gobernacion de Yaracuy (San Felipe): vialidad, asfaltado,
edificaciones, drenajes. Existencia 2010-2015 confirmada por sentencia TSJ
N° 01229/2012 (contrato de obra 2010-026, resolucion firmada por **la
Presidenta** del instituto) y noticia oficial "IAI culmino asfaltado de calle
19 y Av. 7 municipio San Felipe". En dic-2015 se reorganizo como IVOPEY.
Research completa: `docs/progress/explore_iai_yaracuy.md` +
`docs/progress/explore_iai_naming.md`.

**El dominio (corazon del software)**: presupuesto de obra publica venezolano
= partidas codificadas **COVENIN 2000** (codigo, descripcion, unidad m3/m2/kg,
cantidad del computo metrico, precio unitario) -> el PU sale del **APU**
(Analisis de Precios Unitarios: materiales + mano de obra con tabulador y
FCAS + equipos + % administracion/utilidad/financiamiento) -> el seguimiento
son las **valuaciones** (avance fisico-financiero por periodo, conformadas
por el Ingeniero Inspector, curva S). Antes del sistema: Excel + papel,
rehaciendo APUs cada vez que el BCV publicaba indices (inflacion). Software
comercial de la epoca (contraste): LuloWin NG, DataLaing MaPreX.

**Ambiente objetivo (presente)**: oficina tecnica de instituto de obras
publicas con el rincon de desarrollo del equipo de Pablo. Calor de San
Felipe: ventilador. Guiños del gobierno regional SOLO como props (tricolor /
escudo Yaracuy en la valla), NUNCA en la pared.

**Paleta** (theme del informe 15): pared `#f2f0eb`; piso gris cemento
`#d9dbdd`; acento **ambar obra** `#d9a013`; trim **gris concreto** `#8f959e`;
luz `#f6f4ee`. Rojo/tricolor Yaracuy SOLO en la valla y banderin. Distinto
del naranja+amarillo industrial de corpoelec (aqui el mood es "concreto +
maquinaria + planos").

## 3. Props firma del rubro (presente)

- **Meson de planos** grande con planos enrollados (cilindros) + uno
  desplegado sujeto con pesas; **planoteca** (mueble de cajones anchos).
- **Valla de obra** apoyada en la pared: "GOBIERNO BOLIVARIANO DE YARACUY ·
  IAI · Asfaltado calle 19" + escudo (la iconografia real).
- **Cascos** amarillos en perchero + **conos** naranjas apilados en un rincon.
- **Estante tecnico**: Guia de Costos del CIV (lomos gruesos), normas
  COVENIN, carpetas manila rotuladas por obra.
- **Corcho con tabulador** de la construccion pinchado con chinches + sellos
  humedos ("CONFORME") sobre un escritorio administrativo.
- **La PC-SERVIDOR**: torre beige sobre una mesita propia con etiqueta
  "SERVIDOR — NO APAGAR" + cable de red visible que corre a los puestos (el
  guiño al achievement de la red local). Puede llevar LED parpadeante barato.
- **Ventilador de pie** (calor de San Felipe) + termo de cafe.
- `officeLayout`: 3 puestos (rincon del equipo), 2 con laptop encendida
  (screens con Java/consulta SQL), 1 libre togglable con E.

## 4. Cuadros de pared (`wallArt`)

4 laminas, **2 inspeccionables** (★):

1. **★ Valla/lamina institucional del IAI** (escudo Yaracuy + "Instituto
   Autonomo de Infraestructura del Estado Yaracuy"). Ficha: que es el IAI
   (obra publica de la gobernacion, San Felipe; confirmado en registros del
   TSJ; predecesor del actual IVOPEY) + que Pablo implanto ahi su proyecto
   de grado.
2. **★ Diagrama de red cliente-servidor** (la PC-servidor central + clientes
   del instituto). Ficha: el achievement — centralizar los datos elimino las
   copias desincronizadas; el acceso compartido en red local, montado por un
   estudiante en 2015.
3. **Lamina de un APU** (hoja de analisis: materiales / mano de obra /
   equipos / %) — decorativa, textura del dominio.
4. **Plano de via agricola** (vialidad rural, perfil del Yaracuy 2015) —
   decorativa.

## 5. softwareShowcase — app de escritorio Java 2015 (AC-6)

Junto a la puerta. Look **Java Swing 2015 sobre Windows 7** (mismo lenguaje
visual que el showcase de IPASME pero NO identico: barra de menu
Archivo/Obras/Presupuestos/Valuaciones/Reportes, tablas con rejilla, grises
`#ece9d8`/`#f0f0f0`, seleccion azul `#316AC5`). Badge "RED LOCAL" (guiño a la
PC-servidor). 3 demos que `E` cicla:

1. **Presupuesto de obra** — tabla de partidas COVENIN (codigo, descripcion,
   unidad, cantidad, PU, total) + total de la obra; boton "Recalcular"
   (indices BCV) que actualiza los totales AL INSTANTE (el contraste con
   rehacerlo a mano).
2. **APU (Analisis de Precios Unitarios)** — la hoja de UNA partida:
   materiales, mano de obra (tabulador + FCAS), equipos, % administracion /
   utilidad / financiamiento -> precio unitario.
3. **Valuaciones / seguimiento de avance** — lista de obras con avance
   fisico vs financiero (barras/curva S, ej. "68% fisico / 72% financiero"),
   estado "CONFORMADA" y el cuadro demostrativo de lo ejecutado.

## 6. NPCs del presente (5, 2 enfoques)

| NPC | Enfoque | Que cuenta |
| --- | --- | --- |
| **Keiber Mendoza** | `[C]` tesista/dev del equipo | Pablo repartia tareas y seguia el avance sin perseguir a nadie; documentaba TODO ("la defensa fue un paseo"); aprendieron Java en serio armando los modulos de presupuesto. |
| **Marielys Ochoa** | `[C]` tesista/dev del equipo | La BD central en la PC-servidor: antes cada quien tenia su copia y nada cuadraba; Pablo diseño la red y se acabaron las versiones desincronizadas; ella armo las pantallas de partidas. |
| **Ing. Gregorio Salcedo** | `[P]` ingeniero inspector | Hacia las valuaciones a mano (hojas de medicion, fotos de testigos, cotejar Excel); ahora el sistema le arma el cuadro demostrativo; el pidio la vista de curva S; entre valuacion y valuacion la ley da 5 a 45 dias — antes se le iban en papeleo. |
| **Belkis Camacaro** | `[P]` analista de presupuestos | Cada vez que el BCV publicaba indices, rehacia los APU a mano; ahora recalcula con un clic; ella le enseño a Pablo como se arma una partida COVENIN (levantamiento de requerimientos real). |
| **Ing. Maritza Oropeza** | `[J]` presidenta del instituto | Exigia el consolidado de TODAS las obras para firmar resoluciones; antes tardaba jornadas, ahora lo pide y sale del sistema; firmo la carta de aceptacion del proyecto de grado. (Guiño historico: el IAI real tenia una Presidenta en 2011, TSJ.) |

> Ubicacion: Keiber + Marielys en el `officeLayout` (rincon dev, sentados);
> Belkis en el escritorio administrativo del corcho/sellos; Ing. Gregorio de
> ronda entre el meson de planos y el showcase; Ing. Maritza cerca de la
> valla institucional. Recortable a 4 quitando a Keiber.

## 7. Pasado (sepia — `rooms/past/iai.ts`)

**La oficina tecnica ANTES del sistema** (mismo espacio, sepia): presupuestos
a mano y Excel por todos lados.

- **Meson saturado**: planos + calculadora + escalimetro + hojas de computos
  metricos a medio tachar.
- **Pilas de carpetas manila por obra** (torres desordenadas); AZ abiertos.
- **Impresiones de Excel** pegadas con cinta (APUs vencidos: "indices BCV
  SEP", "OCT", "NOV" — la inflacion que obliga a rehacer).
- **El hueco delator**: falta LA carpeta de una obra (nadie sabe quien la
  tiene) — eco del tarjeton de IPASME pero version obras.
- **Reloj de pared** + telefono descolgado (el instituto pidiendo el
  consolidado).
- SIN la PC-servidor (una sola PC vieja compartida, apagada o con Excel).

**Objeto de busqueda lenta**: consolidar el avance de todas las obras —
buscar la carpeta de una obra entre las pilas para copiar sus numeros a la
planilla (tarda; contraste con el reporte instantaneo del presente). Panel de
historia (`onStory`) con la narrativa completa.

**NPCs del pasado** (3, arco antes/despues):

- **Belkis (antes)** — "El BCV publico indices nuevos. ¿Sabes que significa?
  Cuarenta APU. A mano. Otra vez. Si me equivoco en uno, el presupuesto
  entero sale mal firmado."
- **Ing. Gregorio (antes)** — "Tengo la valuacion de la calle 19 en tres
  papeles distintos y ninguno cuadra con mi Excel. Y la presidenta quiere el
  consolidado para el viernes."
- **Pastor Rivas (maestro de obra, nuevo en el pasado)** — "Vine a ver si
  conformaron la valuacion, porque hasta que no la firmen, a mi gente no le
  pagan. Llevo tres viajes esta semana."

## 8. Retos y aprendizajes (infoKit)

**RETOS (es)**: liderar un equipo pequeño (~3) hasta la entrega dentro del
plazo academico; definir la arquitectura del sistema de gestion de obras y
presupuestos; montar una red con una PC como servidor central para compartir
los datos; digitalizar un dominio regulado (partidas COVENIN, APU,
valuaciones) que se llevaba en Excel y papel; documentar cada decision para
la defensa. **(en)** analogo.

**APRENDIZAJES (es)**: arquitectura cliente-servidor sobre red local que
centralizo los datos y elimino copias desincronizadas; consolidacion de
presupuestos y avances de jornadas manuales a reportes del sistema; primer
liderazgo tecnico real (distribucion de tareas, hitos, riesgos);
levantamiento de requerimientos con ingenieros e inspectores de obra;
documentacion tecnica completa. Skills: Desarrollo de Software, Gestion de
Datos, Gestion de Infraestructura, Proyecto de Grado, Redaccion Tecnica +
Gestion de Proyectos, Presupuesto, Planificacion. **(en)** analogo.

## 9. Micro-interacciones propuestas (elegir en sesion con Pablo)

1. **Recalcular el presupuesto** (junto al showcase o la PC-servidor): E
   dispara "indices BCV nuevos" -> los PU de la tabla parpadean y el TOTAL se
   recalcula al instante con easing; tag "antes: 40 APU a mano".
2. **Conformar una valuacion**: E estampa el sello "CONFORME" sobre la
   caratula (el sello 3D baja y golpea) + la barra de avance fisico sube.
3. **Laptop libre togglable** del `officeLayout` (patron estandar).

## Fuentes

`packages/content/src/data-cache/experiences.json` (slug iai) ·
`docs/progress/explore_iai_yaracuy.md` (dominio COVENIN/APU/valuaciones,
ambiente, Yaracuy 2015) · `docs/progress/explore_iai_naming.md` (nombre IAI
confirmado: TSJ N° 01229/2012 + noticia gobernacion; presidenta; IVOPEY) ·
decisiones del usuario 2026-07-05 (stack Java escritorio, fechas ene-dic
2015, nombre IAI en el CV).
