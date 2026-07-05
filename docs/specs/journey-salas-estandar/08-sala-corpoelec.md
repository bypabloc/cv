# 08 — Sala CORPOELEC (Etapa 2, sala 1)

> Informe AUTOCONTENIDO para crear la sala `corpoelec` en una sesion aislada.
> Prerequisito: Etapa 1 hecha (canon en `props.ts`, theme paredes-blancas,
> `RoomId` de 8, pasados partidos). Leer antes: [README](README.md) +
> [02-el-canon-de-sala.md](02-el-canon-de-sala.md) + [ESTADO.md](ESTADO.md).
>
> Experiencia real: slug `corpoelec` · CORPOELEC · Venezuela · intern 2013 ·
> "Desarrollador Web". Sistema web OFFLINE de inventario de equipos electricos
> (PHP + jQuery) desplegado en 3 estados. `metricsEstimated: true`.

## Checklist de la sala (marcar al crear)

- [ ] `engine/rooms/corpoelec.ts` (presente) — refactor completo
- [ ] `engine/rooms/past/corpoelec.ts` (pasado) — refactor completo
- [ ] `engine/dialogs/corpoelec-presente.ts` (4-5 NPCs)
- [ ] `engine/dialogs/corpoelec-pasado.ts` (2-3 NPCs)
- [ ] theme `corpoelec` con `wall: '#f2f0eb'` (ya en Etapa 1; verificar)
- [ ] typecheck + build + visual OK
- [ ] Actualizar [ESTADO.md](ESTADO.md)

## 1. Datos reales de la experiencia (es/en, textual)

**Identidad**: slug `corpoelec` · company `CORPOELEC` · country `Venezuela` ·
start `2013-01` end `2013-12` · seniority `intern` · role es "Desarrollador
Web" / en "Web Developer" · `metricsEstimated: true` (metricas estimadas, usar
hedges "aproximadamente/roughly").

**Summary**
- es: "Pasantia: implemente un sistema de inventario de equipos electricos
  (PHP + jQuery) desplegado offline en 3 estados de Venezuela."
- en: "Internship: built an offline-capable electrical inventory system
  (PHP + jQuery) deployed across 3 Venezuelan states."

**Responsibilities (es)**: (1) sistema de inventario PHP+jQuery con BD
relacional para registro de activos; (2) CRUD para administrar equipos y
asociar activos a personas y dependencias; (3) diseño de operacion OFFLINE
para sedes con conectividad limitada/intermitente; (4) levantamiento de
requerimientos con personal operativo (flujo real en campo); (5)
documentacion + guias basicas para usuarios finales de cada sede.

**Achievements (es)**: (1) desplegado en 3 estados operando OFFLINE; (2)
localizar un equipo de varios minutos (busqueda manual en papel) a consulta
inmediata; (3) centralizo ~3 sedes en una BD comun, eliminando planillas
dispersas y duplicadas; (4) entregado dentro del año, capacitando al personal
de cada sede.

**skillsTechnical**: CRUD · Gestion de Activos · Gestion de Inventarios ·
PHP · Sistema Offline. **skillsSoft**: Colaboracion de Equipo · Resolucion de
Problemas.

> El JSON dice "3 estados"; el plan nombra **Yaracuy, Carabobo, Lara**. Usar
> esos 3 en toda la sala (mapa, pasado, showcase) para consistencia.

## 2. Rubro y ambiente

**CORPOELEC** = Corporacion Electrica Nacional, estatal venezolana (MPPEE).
Genera/transmite/distribuye electricidad (Sistema Electrico Nacional).
Emblema: Central Hidroelectrica Simon Bolivar / Represa del Guri.
Transmision en **3 lineas: 765 kV, 400 kV, 230 kV**. Operacion cotidiana
centrada en subestaciones + transformadores de potencia (ej. 40 MVA).

**Ambiente objetivo**: mezcla de sala de control de subestacion + oficina
tecnica/almacen de equipos. Oficina publica venezolana 2013: mobiliario
funcional, EPP presente, señaletica de riesgo electrico.

**Paleta real**: rojo/naranja (logo, acento principal) + azul marino
(institucional) + amarillo seguridad (cascos, señaletica, lineas de piso) +
gris metalico (transformadores, tableros) + marron porcelana (aisladores) +
verde/rojo LED (tablero energizado).

> **Aplicacion de color (constraint)**: pared **`#f2f0eb`** blanca. El rubro
> (naranja CORPOELEC + amarillo seguridad) va en **piso, props, luz**. El
> amarillo seguridad entra como **lineas pintadas en el piso** demarcando la
> seccion de inventario — canal ideal sin tocar paredes.

## 3. Props firma del rubro (presente)

Subconjunto low-poly reconocible (procedural, primitivas + Canvas):

- **Transformador de potencia** (gris + aletas + aisladores) x1-2 en la
  seccion de inventario, con **etiqueta de activo** (`TX-001`).
- **Aisladores ceramicos** apilados en repisa.
- **Tablero de control** con medidores + LEDs verde/rojo (aporta el toque LED).
- **Bobinas/carretes de cable** en un rincon del almacen.
- **Señal triangulo-rayo** de riesgo electrico (pared o poste).
- **Torre de alta tension** estilizada o **maqueta de represa/turbina (Guri)**
  sobre repisa (interior: usar maqueta, no ventana).
- **Casco amarillo/blanco** suelto sobre un escritorio.
- **Lineas amarillas de seguridad** en el piso (demarcan la seccion inventario).

## 4. Seccion de inventario + equipos (AC-10, pedido explicito)

Estanteria metalica industrial con **cajas etiquetadas** + los equipos que el
sistema rastreaba, todos "de 2013" (nada moderno) con **etiqueta de activo**
visible (`RAD-014`, `PC-207`, `LAP-033`, `TAB-009`, codigo de barras):

- **Walkie-talkies / radios** (bloque negro grueso, antena de goma, PTT).
- **Radios base / transceptores** (perilla + dial + microfono con cable
  espiralado).
- **Telefonos de escritorio** fijos (base con teclado + auricular con cable
  espiralado).
- **Computadoras de escritorio** (torre gruesa + monitor LCD de marco ancho o
  CRT panzon para reforzar "sede vieja").
- **Laptops** gruesas de 2013 (bisel ancho, touchpad pequeño).
- **Tablets** de 2013 (bisel grueso, boton fisico frontal).

> **Contraste presente/pasado con los MISMOS equipos**: presente = ordenados
> en cajas etiquetadas en estantes; pasado = regados por suelo/mesas sin orden
> ni etiqueta.

## 5. Cuadros de pared (`wallArt`)

3-4 laminas tinta plana. **2 inspeccionables** (abren ficha):

1. **Lineas de transmision** — torres de celosia con las 3 lineas rotuladas
   **765 kV / 400 kV / 230 kV**. **INSPECCIONABLE** (dato real potente).
2. **Transformador de potencia** — corte con aletas + bujes ceramicos,
   etiqueta "40 MVA". **INSPECCIONABLE**.
3. **Generador / represa del Guri** — turbina/silueta de la represa Simon
   Bolivar. Decorativo.
4. (Opcional) **Mapa de 3 estados** — Venezuela low-poly con Yaracuy/Carabobo/
   Lara resaltados + pines. Decorativo o inspeccionable (guiño al despliegue).

## 6. softwareShowcase — el sistema web (AC-6, AC-10)

Junto a la puerta, badge **OFFLINE**. Estetica intranet 2013 (PHP+jQuery,
DataTables, header con banda naranja/azul CORPOELEC, tablas con paginacion,
Arial/Verdana, anchos fijos). 3 demos que `E` cicla:

1. **Grid de inventario** (jQuery DataTable) — columnas Codigo activo / Equipo
   / Estado / Ubicacion (sede) / Asignado a. Fila ej:
   `TX-001 | Transformador | Operativo | Yaracuy | J. Perez`. Badge OFFLINE.
2. **Buscador "quien lo tomo / a quien se le daño"** — input + ficha del
   equipo: responsable actual, historial de asignaciones, estado
   (operativo/dañado). El "de minutos a inmediato".
3. **Reporte de incidencias por equipo** — timeline de incidencias/daños o
   agregado (equipos por estado / por sede).

Branding del mockup (panel HTML): gris industrial + naranja CORPOELEC +
badge OFFLINE.

## 7. NPCs del presente (4-5, 2 enfoques)

Nombres venezolanos plausibles. Todos con casco (unos caminando, unos
sentados). Resumenes = base del arbol de dialogo (anclados a la data real).

| NPC | Enfoque | Que cuenta (base del dialogo) |
| --- | --- | --- |
| **Yorman Rodriguez** | `[C]` dev | Construyo el CRUD PHP + tablas jQuery con Pablo; modelaron la BD relacional (equipo -> responsable -> sede); Pablo insistio en OFFLINE desde el diseño. |
| **Genesis Marcano** | `[C]` dev | El levantamiento de requerimientos con el personal operativo (Pablo iba a campo antes de codear) + documentacion y guias por sede. |
| **Wilmer Colina** | `[P]` personal (almacenista/tecnico, con casco) | Antes perdia minutos buscando un equipo en papel; ahora consulta inmediata. Pidio "quien tomo el equipo" y registro de daños. |
| **Dubraska Piña** | `[P]` personal (administrativa) | Antes planillas duplicadas que no cuadraban; ahora una sola BD. Pablo la capacito e hizo caso a sus pedidos de reportes. |
| **Ing. Rafael Betancourt** | `[J]` jefe (opcional) | Aprueba que el pasante entregara en el año un sistema en 3 estados offline; "entendio la operacion real, no solo el codigo". |

> Para bajar a 4: quitar el jefe o fusionar Genesis en Yorman.

## 8. Pasado (sepia, refactor completo — AC-11, AC-20)

Oficinas viejas grises/sepia SIN software. Personal frustrado. Equipos
(walkie-talkies, radios, telefonos, un PC apagado polvoriento) **regados** por
suelo y mesas, sin etiquetas (el mismo pool que en el presente esta ordenado).
Sobre 3 escritorios rotulados **"Sede Yaracuy" / "Sede Carabobo" / "Sede
Lara"**, pilas de **planillas de papel duplicadas** escritas a mano, con
tachaduras y datos que no cuadran entre sedes. Archivador metalico saturado,
carpetas manila.

**NPCs del pasado** (2-3, frustrados — reusar nombres crea el arco):

- **Wilmer Colina (antes)** — con pila de carpetas: "Cada vez que buscan un
  equipo reviso hoja por hoja; me toma minutos y a veces ni aparece."
- **Dubraska Piña (antes)** — frente a 2 planillas contradictorias: "En
  Yaracuy dice una cosa, en Carabobo otra, en Lara ni figura. Copiamos las
  mismas planillas tres veces y nunca cuadran."
- **Alcides (tecnico de campo, opcional)** — con casco y walkie, buscando: "Nadie
  sabe quien se llevo el radio ni si volvio; si se daña, no queda registro."

Objeto de busqueda lenta: hurgar carpetas por un equipo. Panel de historia
(`onStory`) con el "antes" completo.

## 9. Retos y aprendizajes (infoKit, derivados de la data)

**RETOS** (es): registrar activos dispersos en planillas de papel duplicadas y
desincronizadas entre 3 sedes (Yaracuy/Carabobo/Lara); hacerlo funcionar
OFFLINE en sedes con conectividad intermitente; levantar requerimientos con el
personal operativo. **(en)**: track scattered assets across duplicated,
out-of-sync paper spreadsheets in 3 sites; make it run OFFLINE; gather
requirements with operations staff.

**APRENDIZAJES** (es): sistema de inventario PHP+jQuery desplegado OFFLINE en 3
estados; localizacion de minutos a consulta inmediata; centralizar ~3 sedes en
una BD comun; entrega en el año + capacitacion; Skills: CRUD, sistema offline,
gestion de activos/inventarios, PHP + colaboracion y resolucion de problemas.
**(en)** analogo.

> Retos/aprendizajes finales los deriva `buildRooms` de `summary`/
> `responsibilities`/`achievements`/`skills` reales — este texto es la guia
> narrativa, no reemplaza la derivacion data-driven del kit.

## Fuentes

`packages/content/src/data-cache/experiences.json` (slug corpoelec) ·
`docs/progress/explore_empresas_venezuela.md` (CORPOELEC) ·
`docs/specs/journey-3d-cv/01-propuesta-a-habitaciones.md` (Sala 1) ·
Wikipedia/sitio oficial CORPOELEC (rubro, lineas 765/400/230 kV, Guri).
