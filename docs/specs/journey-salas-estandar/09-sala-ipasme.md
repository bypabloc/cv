# 09 — Sala IPASME (Etapa 2, sala 2)

> Informe AUTOCONTENIDO para crear la sala `ipasme` en una sesion aislada.
> Prerequisito: Etapa 1 hecha. Leer antes: [README](README.md) +
> [02-el-canon-de-sala.md](02-el-canon-de-sala.md) + [ESTADO.md](ESTADO.md).
>
> Experiencia real: slug `ipasme` · IPASME · Venezuela · junior 2014 ·
> "Desarrollador de Software". Sistema DIGITAL de historias medicas (Java
> escritorio Windows, POO+CRUD) que reemplazo el registro en papel.
> `metricsEstimated: true` (tiempos como narrativa cualitativa).

## Checklist de la sala

- [ ] `engine/rooms/ipasme.ts` (presente)
- [ ] `engine/rooms/past/ipasme.ts` (pasado)
- [ ] `engine/dialogs/ipasme-presente.ts` (4-5 NPCs)
- [ ] `engine/dialogs/ipasme-pasado.ts` (2-3 NPCs)
- [ ] theme `ipasme` con `wall: '#f2f0eb'` (verificar)
- [ ] typecheck + build + visual OK
- [ ] Actualizar [ESTADO.md](ESTADO.md)

## 1. Datos reales (es/en, textual)

**Identidad**: slug `ipasme` · company `IPASME` · country `Venezuela` · start
`2014-01` end `2014-12` · seniority `junior` · role es "Desarrollador de
Software" / en "Software Developer" · `metricsEstimated: true`.

**Summary**: es "Entregue un sistema digital de historias medicas que
reemplazo el registro en papel en el IPASME." / en "Delivered a digital
medical records system that replaced paper-based registration at IPASME."

**Responsibilities (es)**: (1) sistema de gestion de historias medicas para
registro y consulta de pacientes; (2) interfaces de ESCRITORIO en Java para
Windows (POO + modelo de datos persistente); (3) CRUD de pacientes, consultas
y registros clinicos; (4) levantamiento de requerimientos con personal medico
y administrativo (flujo real de atencion); (5) manejo de datos SENSIBLES de
salud con controles basicos de acceso y validacion.

**Achievements (es)**: (1) sistema funcional que reemplazo fichas de papel por
registro digital consultable; (2) busqueda de una historia de varios minutos
en archivo fisico a consulta inmediata en pantalla; (3) POO + CRUD en Java
consistente (bases solidas de ing. de software); (4) mejoro comunicacion
tecnica y levantamiento de requerimientos trabajando con personal de salud.

**skillsTechnical**: Aplicacion de Escritorio · Historias Medicas · Java ·
Levantamiento de Requerimientos · Programacion Orientada a Objetos.
**skillsSoft**: Adaptabilidad · Comunicacion Tecnica · Pensamiento Analitico ·
Resolucion de Problemas.

> **Claves de diseño**: (a) stack Java ESCRITORIO Windows, NO web -> el
> showcase se ve como app de escritorio 2014 (Swing/WinForms), NUNCA
> navegador. (b) Eje narrativo: papel->digital + minutos->inmediato. (c) Rol
> junior: sala MODESTA (menos densidad, luz clinica neutra plana, contrasta
> con la premium de Destacame).

## 2. Rubro y ambiente

**IPASME** = Instituto de Prevision y Asistencia Social para el personal del
Ministerio de Educacion. Publico venezolano (adscrito al MPPE). Prevision +
seguridad social + asistencia medica a docentes y familiares. Creado 1949,
opera desde 1950 -> **decadas de expedientes fisicos acumulados** (dato
narrativo clave). Alto volumen (>576k atenciones/trimestre en 2024). Servicios:
medicina general/especializada, odontologia, laboratorio, rayos X, farmacia.

**Ambiente objetivo (presente)**: oficina de desarrollo con guiños de
consultorio + admision + archivo clinico YA digitalizado (archivo de papel
casi vacio). Elementos reales: camilla con rollo de papel, escritorio con
tensiometro/estetoscopio, negatoscopio, bascula; sala de espera con sillas en
hilera + dispensador de turnos; mostrador de admision; farmacia.

> **Detalle real del archivo clinico venezolano** (oro para el pasado): cada
> paciente = un expediente unico en carpeta con **numeracion unica**; se usan
> **tarjetones** en el hueco de la carpeta extraida para saber que expediente
> falta y donde esta. Un tarjeton mal puesto = historia perdida.

**Paleta**: azul institucional (`~#2a6fb0`, acento principal) + verde menta
(`~#63c2a8`) en piso/props/luz; blanco clinico (`#ffffff` batas/camilla);
manila/beige (`#d9c39a` carpetas, protagonista del pasado); rojo puntual solo
en la cruz medica (`#c0392b`); gris/plateado (archivadores, instrumental).

> **Aplicacion (constraint)**: pared `#f2f0eb` blanca. Azul institucional +
> verde menta = los 2 acentos sobre base blanca (encaja con manga-ink).

## 3. Props firma del rubro (presente)

- **Camilla de examen** con rollo de papel (icono #1 de consultorio).
- **Escritorio de medico** con tensiometro + estetoscopio colgado.
- **Sillas de sala de espera** en hilera (InstancedMesh) + dispensador de
  turnos.
- **Mueble de farmacia** con cajas de medicamentos (unicos toques calidos).
- **Mostrador de admision** con ventanilla + cartel "IPASME".
- **Negatoscopio** en pared con una radiografia (guiña a rayos X).
- **Monitor con la historia clinica** sobre el mostrador.
- **Archivador metalico con cajones semivacios** (el papel migrado; el hueco
  del tarjeton).

## 4. Cuadros de pared (`wallArt`)

4 laminas, **2 inspeccionables** (★):

1. **★ Lamina de anatomia humana** (torso/esqueleto, cartel de consultorio).
   Ficha: IPASME = salud integral docente / gancho narrativo.
2. **★ Carnet de afiliado IPASME ampliado** (docente + N° afiliado + cruz +
   azul). Ficha: quien es el "paciente" (docentes+familiares), el volumen
   (>576k/trimestre) por que el papel no daba abasto.
3. **Organigrama / flujo clinico** (recepcion->admision->consulta->farmacia/
   archivo). Decorativo (refuerza responsibility 4).
4. **Cartel "IPASME va a la Escuela"** / lema salud docente. Decorativo (color
   azul).

## 5. softwareShowcase — app de escritorio Windows 2014 (AC-6)

Junto a la puerta. Guiño **"carpeta papel -> pantalla"** (folder ->
pixelado -> monitor con ficha) + badge **"Digitalizado"**. **Look de app de
escritorio Windows 2014 (Swing/WinForms), NO navegador**: barra de titulo gris
con menu clasico (Archivo/Edicion/Pacientes/Consultas/Reportes/Ayuda),
toolbar con iconos XP/Win7, formularios densos (labels izq, campos con borde
3D hundido, GroupBox), JTable con rejilla, grises Windows Classic
(`#ece9d8`/`#f0f0f0`), azul de seleccion `#316AC5`, Tahoma/Segoe. 3 demos que
`E` cicla:

1. **Ficha de paciente** — expediente docente: avatar, N° historia/afiliado,
   cedula, edad, antecedentes, lista de consultas/registros (fecha, motivo,
   diagnostico), botones CRUD.
2. **Buscador de historia** — busqueda por N° / cedula / apellido; resultado
   **al instante** (contraste con el archivista lento del pasado; puede
   mostrar "0.2s" vs "varios minutos"). Es la micro-interaccion clave.
3. **Control de acceso a datos sensibles** — login/permisos (medico/admin/
   recepcion), candado en seccion "datos de salud", validacion de campos. Es
   el germen del hilo "datos sensibles" que reaparece en fintech (Destacame).

## 6. NPCs del presente (4-5, 2 enfoques)

| NPC | Enfoque | Que cuenta |
| --- | --- | --- |
| **Yuleima Rondon** | `[P]` enfermera | Antes corria al archivo por cada paciente (perdia media hora); pidio digitalizar. Pablo se sentaba a ver como atendian de verdad. Ahora mete la cedula y esta al instante. |
| **Argenis Colmenares** | `[P]` archivista | Se sabia el archivo de memoria (pasillo/estante/numero); una carpeta traspapelada = un dia perdido. Pablo le pregunto como numeraba antes de programar. |
| **Dr. Hector Villasmil** | `[J]` medico/jefe | Exigio que la historia no la vea cualquiera (datos sensibles); Pablo le puso claves y validacion; firmo el visto bueno cuando vio que seguia el flujo real. |
| **Daniela Guerra** | `[C]` dev | Aprendian Java juntos; Pablo se clavaba con POO ("clase Paciente bien hecha"), dejo el CRUD limpio; hablaba con las enfermeras mejor que con los devs. |
| **Jose Miguel Aponte** | `[C]` dev/soporte | Instalaba el sistema en cada PC del mostrador (escritorio Java Windows, nada de nube en 2014); Pablo anotaba bugs sin ponerse a la defensiva. |

> Ubicacion: Yuleima + Dr. Villasmil en consultorio; Argenis junto al
> archivador semivacio; Daniela + Jose Miguel en el rincon de desarrollo.
> Recortable a 4 quitando Jose Miguel.

## 7. Pasado (sepia, refactor — AC-20)

**El Departamento de Historias Medicas ANTES del sistema**: cuarto-archivo sin
fin, sofocante, fluorescente parpadeante (sepia amarillento). Elementos:

- **Estanterias metalicas de carpetas manila hasta el techo** (InstancedMesh
  masivo): filas de folders con pestañas/etiquetas amarillas, numeracion a
  mano, algunas atadas con ligas. Montaña de +75 años de expedientes.
- **Fichas traspapeladas**: pila de folders volcada, un tarjeton fuera de su
  hueco.
- **El "hueco" delator**: un espacio vacio con solo el tarjeton (la carpeta se
  extrajo y quiza no volvio).
- **Escritorio de admision saturado**: pila de solicitudes sin atender,
  telefono sonando, lista manuscrita de "pendientes por buscar".
- **Reloj de pared** (refuerza "varios minutos" por paciente).

**NPCs del pasado** (2-3, reusar nombres crea el arco antes/despues):

- **Argenis (antes)** — con carpetas: "Tengo cuatro medicos esperando cuatro
  historias y soy uno solo. Si una carpeta esta traspapelada, se acabo mi
  mañana. Numeramos a mano; un cero mal puesto y no la encuentra nadie."
- **Yuleima (antes)** — "El doctor me manda por la historia del señor Perez y
  hay tres Perez. Vuelvo con las tres carpetas y ninguna es. Media consulta se
  me va esperando un papel."
- **Petra Salazar (recepcionista, nueva en el pasado)** — "La cola no baja.
  Cada afiliado son diez minutos de buscar su historia antes de que lo vean. Si
  el archivo cierra, no hay atencion."

Objeto de busqueda lenta: buscar una historia entre estantes (tarda, contraste
con el buscador instantaneo del presente). Panel de historia (`onStory`).

## 8. Retos y aprendizajes (infoKit)

**RETOS (es)**: reemplazar el registro en papel de historias medicas por un
sistema digital consultable en una institucion con decadas de expedientes;
manejar datos sensibles de salud con controles de acceso y validacion; alinear
el sistema con el flujo real de atencion; construir una app de escritorio Java
(POO+CRUD) siendo junior; levantar requerimientos con personal medico y
administrativo. **(en)** analogo.

**APRENDIZAJES (es)**: sistema digital de historias medicas que reemplazo las
fichas de papel; busqueda de minutos a consulta inmediata; bases solidas de
ing. de software (POO+CRUD en Java); comunicacion tecnica + levantamiento con
personal de salud; primer contacto con manejo responsable de datos sensibles.
Skills: Java, POO, App de Escritorio, Historias Medicas, Levantamiento +
Comunicacion Tecnica, Pensamiento Analitico, Resolucion, Adaptabilidad.
**(en)** analogo.

## Fuentes

`packages/content/src/data-cache/experiences.json` (slug ipasme) ·
`docs/progress/explore_empresas_venezuela.md` (IPASME) ·
`docs/specs/journey-3d-cv/01-propuesta-a-habitaciones.md` (Sala 2) ·
Wikipedia/sitio oficial IPASME (creacion 1949/50, servicios, volumen) · blog
Archivos de Historias Clinicas 2014 (mecanica carpeta/numeracion/tarjeton).
