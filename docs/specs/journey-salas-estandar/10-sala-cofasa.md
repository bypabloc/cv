# 10 — Sala Cofasa (Etapa 2, sala 3)

> Informe AUTOCONTENIDO para crear la sala `cofasa` en una sesion aislada.
> Prerequisito: Etapa 1 hecha. Leer antes: [README](README.md) +
> [02-el-canon-de-sala.md](02-el-canon-de-sala.md) + [ESTADO.md](ESTADO.md).
>
> Experiencia real: slug `cofasa` · Laboratorio Cofasa S.A. ·
> `https://laboratoriocofasa.com` · Venezuela · mid 2017-01/2018-11 ("casi 2
> años") · "Desarrollador de Sistemas Web". Sistema web (jQuery + Laravel) de
> monitoreo de produccion y PARADAS DE MAQUINA que reemplazo planillas de
> papel. `metricsEstimated: true`.

## Checklist de la sala

- [ ] `engine/rooms/cofasa.ts` (presente)
- [ ] `engine/rooms/past/cofasa.ts` (pasado)
- [ ] `engine/dialogs/cofasa-presente.ts` (4-5 NPCs)
- [ ] `engine/dialogs/cofasa-pasado.ts` (2-3 NPCs)
- [ ] theme `cofasa` con `wall: '#f2f0eb'` (verificar)
- [ ] typecheck + build + visual OK
- [ ] Actualizar [ESTADO.md](ESTADO.md)

## 1. Datos reales (es/en, textual)

**Identidad**: slug `cofasa` · company `Laboratorio Cofasa S.A.` · country
`Venezuela` · companyUrl `https://laboratoriocofasa.com` · start `2017-01` end
`2018-11` · seniority `mid` · role es "Desarrollador de Sistemas Web" / en "Web
Systems Developer" · `metricsEstimated: true` · priority generic 70.

**Summary**: es "Desarrolle un sistema web (jQuery + Laravel) para monitorear
la produccion farmaceutica y analizar paradas de maquina." / en "Built a web
system (jQuery + Laravel) to monitor pharmaceutical production and analyze
machine downtime for productivity."

**Responsibilities (es)**: (1) sistema web jQuery+Laravel de monitoreo del
proceso de produccion, registrando paradas de maquina para analisis de
productividad; (2) implementacion en toda la empresa sobre la red LOCAL, con
login usuario/contraseña por empleado; (3) modelado de BD relacional
(eventos de produccion, tiempos de parada y causas); (4) reportes y vistas de
analisis que transformaron datos crudos en indicadores accionables; (5)
levantamiento de requerimientos con personal de produccion; (6)
mantenimiento/ajuste continuo segun feedback.

**Achievements (es)**: (1) contribuyo al aumento de productividad via analisis
de datos (decisiones informadas); (2) reemplazo el registro manual de paradas
en planillas de papel por captura digital centralizada y consultable; (3)
reportes de productividad de varias horas de consolidacion manual a consulta
directa; (4) dio visibilidad POR PRIMERA VEZ a las causas de parada mas
frecuentes; (5) sostuvo el sistema en uso productivo casi 2 años.

**skillsTechnical**: Analisis de Productividad · Laravel · Monitoreo de
Produccion · Plataforma Web · Red Local · jQuery. **skillsSoft**: Colaboracion
de Equipo · Resolucion de Problemas.

## 2. Rubro y ambiente

**Laboratorio Cofasa** (Compañia Farmaceutica Aue) = farmaceutica venezolana
emblematica (70 años en 2024, ~1954). Empezo distribuyendo (rep. de E. Merck
1954 -> fusion "Merck-Cofasa"); en 1974 empezo a fabricar en su **planta en la
Urb. Industrial Lebrun, Petare, Caracas** (donde Pablo trabajo). Produce 3
lineas (Etica con receta, Genericos, OTC). Formatos: **ampollas/inyectables**
(firma), tabletas, jarabes, colirios.

> **CORRECCION IMPORTANTE**: **MIOVIT NO es una maquina, es el PRODUCTO
> ESTRELLA** de Cofasa: el complejo B inyectable ("el que todos los
> venezolanos llevan en la sangre"), se vende como **Kit Miovit** (1/3/6
> dosis: ampollas de vidrio + inyectadoras + compresas). En la sala: MIOVIT =
> producto en la linea de envasado (cajas marca Miovit, ampollas ambar). La
> "maquina de ampollas" es la **llenadora de inyectables generica** con Miovit
> corriendo encima.

**Ambiente objetivo (presente)**: oficina de planta + sala limpia (cGMP) con
operarios en atuendo esteril (bata, guantes, **cofia**, mascarilla). Causas
tipicas de parada de linea farma (para dashboard y pasado): changeover (cambio
de formato/lote), limpieza/sanitizacion, falta de material, atasco mecanico,
falla electrica, calibracion, falta de operario, mantenimiento, control de
calidad.

**Paleta**: **azul Cofasa** (`~#0a4a9e`/`#1560bd`, acento institucional) en
logo/franjas/header dashboard; acero inox/gris (`#b8bcc0`-`#8a8f95`) en
tanque/llenadora/banda; blanco clinico (batas); vidrio ambar de ampolla
(`#c9862e` translucido); aluminio de blister (`#cfd3d6`). **Rojo/amarillo/
verde SOLO en la torre andon** (rojo `#e23b34`, amarillo `#f2c035`, verde
`#3aa856`) y en los estados del dashboard.

> **Aplicacion (constraint)**: pared `#f2f0eb` blanca + acento azul; el
> semaforo rojo/amarillo/verde vive UNICAMENTE en la torre andon y el
> dashboard, NUNCA en muros.

## 3. Props firma del rubro (presente)

- **Torre andon** roja/amarilla/verde (micro: disparar una PARADA -> andon
  roja; unico lugar con rojo/verde).
- **Maquina llenadora de ampollas** con banda de ampollas de vidrio ambar
  (Miovit corriendo).
- **Linea de blisteres** (InstancedMesh de blisteres de tabletas saliendo).
- **Tanque de mezcla inox** cilindrico con valvulas.
- **Mesa QC** con frascos + ampollas de muestra + lupa/instrumento.
- **Cajas de producto Miovit** apiladas (marca reconocible).
- **Monitor con dashboard de produccion** (el sistema, showcase).
- **NPCs con bata + cofia + mascarilla**.

## 4. Cuadros de pared (`wallArt`)

4 laminas, **2 inspeccionables** (★):

1. **★ Proceso de envasado de inyectables** — flujo: mezcla -> llenado ampolla
   -> sellado a la llama -> inspeccion -> blisteado/estuchado -> Kit Miovit.
   Ficha explica el flujo real de la planta (ancla el rubro).
2. **★ Causas de parada de maquina** — poster Pareto: changeover, limpieza,
   atasco, falta de material, falla electrica, calibracion. Ficha: "esto es lo
   que antes nadie media" (conecta con el sistema).
3. **Disponibilidad de linea** — donut + formula `disponibilidad = operando /
   total`. Decorativo (o 3er inspeccionable si se quiere).
4. **Poster buenas practicas (cGMP / sala limpia)** — normas de higiene,
   cofia/bata. Decorativo (textura farma).

## 5. softwareShowcase — dashboard de paradas (AC-6)

Junto a la puerta. Sistema web interno sobre **red LOCAL (LAN)**, login por
empleado, reemplazo las planillas de papel del supervisor. **UI 2017-18:
jQuery + Bootstrap-like, panel admin clasico** (DataTables, graficos Chart.js/
Highcharts/Flot, header azul, sidebar de modulos). **NADA de React/Vue** (era
2017-18). 3 demos que `E` cicla:

1. **EVENTO PARADA** (captura en vivo) — formulario: maquina/linea, timestamp,
   selector de causa, boton "Registrar". Al disparar la micro (torre andon
   roja), esta pantalla registra la causa en tiempo real. El antes/despues
   tactil.
2. **PARADAS POR CAUSA** (barras/Pareto) — barras horizontales ordenadas por
   causa (changeover, limpieza, atasco...). La vista que "dio visibilidad por
   primera vez a las causas mas frecuentes". Cada barra = horas perdidas.
3. **DISPONIBILIDAD / DOWNTIME** (donut) — % operando (verde) vs % detenido
   (rojo/amarillo por causa). El indicador de productividad resumen.

> El semaforo verde/amarillo/rojo del dashboard = mismo lenguaje que la torre
> andon (ningun otro rojo/verde en la sala).

## 6. NPCs del presente (4-5, 2 enfoques)

| NPC | Enfoque | Que cuenta |
| --- | --- | --- |
| **Yorman Rondon** | `[C]` dev/soporte TI | Pablo levanto todo en jQuery+Laravel, corriendo en la red local con login por empleado; se sentaba con produccion antes de codear (modelo de BD segun la planta real). |
| **Douglas Materan** | `[C]` dev/analitico | Con las barras por causa vieron que changeover y limpieza comian mas tiempo; priorizaron por ahi; los datos crudos por fin fueron indicadores usables en reunion. |
| **Nelida Guerra** | `[P]` supervisora de planta | Antes cargaba libreta y reloj todo el turno apuntando cada parada; horas cuadrando a mano; ahora lo registra en la pantalla y los reportes salen con una consulta. |
| **Rafael Escalona** | `[P]` operario (con cofia) | Cuando la maquina de ampollas se para, avisa y la parada queda registrada al toque con causa y hora; antes nadie sabia por que se detenia tanto. |
| **Carmen Yepez** | `[J]` jefa de produccion | Por primera vez tuvo los numeros de productividad a la vista (no planillas sueltas); decidio con datos que corregir; valoro que llevo casi 2 años sosteniendolo y ajustandolo. |

> Recortable a 4 quitando Douglas.

## 7. Pasado (sepia, refactor — AC-20)

**El registro manual de paradas** (caos previo). Mismo espacio de planta
desaturado sepia + grano. Elementos:

- **Escritorio de supervision** junto a la linea, con **planillas de paradas
  en papel** apiladas/sueltas, manchadas, tachadas, anotadas a lapiz. Cada
  parada = una fila a mano.
- **Supervisora anotando a mano**: reloj de pulsera + reloj de pared (para
  cronometrar), libreta/talonario, lapiz.
- **Calculadora vieja** + pila de reportes a medio consolidar ("varias horas
  de consolidacion manual").
- **Torre andon apagada o en rojo fijo**: la linea detenida y **nadie sabe por
  que** (cero visibilidad de causas).
- **Maquina de ampollas detenida** con un operario mirandola sin datos.
- Papeles traspapelados (datos crudos que nunca se vuelven indicadores).

**NPCs del pasado** (2-3, reusar nombres crea el arco):

- **Nelida (antes)** — "Otra parada... y yo aqui con la libreta y el reloj
  apuntando a mano. Al final del turno me llevo tres horas cuadrando esto."
- **Rafael (antes)** — "La linea se para y se para, pero nadie sabe por que. Yo
  aviso gritando y quien sabe si alguien lo anota."
- **Carmen (antes, opcional)** — "¿Cuanto perdimos esta semana y por que causa?
  No se. Tengo un monton de planillas que ni cuadran entre si."

Objeto de busqueda lenta: consolidar planillas. Panel de historia (`onStory`).

## 8. Retos y aprendizajes (infoKit)

**RETOS (es)**: monitorear la produccion farmaceutica y las paradas de maquina,
hoy registradas a mano en planillas; modelar una BD relacional (eventos,
tiempos de parada, causas); desplegar en toda la empresa sobre la red local con
login por empleado; transformar datos crudos en indicadores accionables;
levantar requerimientos con el personal de produccion. **(en)** analogo.

**APRENDIZAJES (es)**: sistema web jQuery+Laravel de monitoreo, en uso
productivo casi 2 años; reemplazar planillas por captura digital consultable;
reportes de horas a consulta directa; visibilidad por primera vez a las causas
de parada; decisiones informadas analizando los datos. Skills: analisis de
productividad, monitoreo de produccion, Laravel, jQuery, plataforma web, red
local, resolucion + colaboracion. **(en)** analogo.

## Notas de consistencia

- MIOVIT = producto (Kit complejo B inyectable), NO maquina. La llenadora de
  ampollas corre Miovit encima.
- Colores: pared `#f2f0eb`, acento azul Cofasa, rojo/verde SOLO andon +
  dashboard.
- Temporal: 2017-18 -> UI jQuery/Bootstrap/Chart.js, NADA React/Vue.
- Guiño fino opcional: planta en Urb. Industrial Lebrun, Petare, Caracas (mapa/
  etiqueta discreta, analogo al mapa de estados de CORPOELEC).

## Fuentes

`packages/content/src/data-cache/experiences.json` (slug cofasa) ·
`docs/progress/explore_empresas_venezuela.md` (Cofasa) ·
`docs/specs/journey-3d-cv/01-propuesta-a-habitaciones.md` (Sala 3) ·
laboratoriocofasa.com (inicio/historia: lineas, formatos, planta Lebrun) ·
prensa Miovit 70 años (complejo B, Kit 1/3/6) · docs de llenado de ampollas
farma (sala limpia, changeover/limpieza bajan OEE).
