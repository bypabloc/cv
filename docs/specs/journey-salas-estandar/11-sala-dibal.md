# 11 — Sala Dibal (Etapa 2, sala 4)

> Informe AUTOCONTENIDO para crear la sala `dibal` en una sesion aislada.
> Prerequisito: Etapa 1 hecha. Leer antes: [README](README.md) +
> [02-el-canon-de-sala.md](02-el-canon-de-sala.md) + [ESTADO.md](ESTADO.md).
>
> Experiencia real: slug `dibal` · Dibal (Dibal del Peru S.A.C.) ·
> `https://dibal.pe` · Peru · senior 2018-12/2021-09 ("casi 3 años") · "Lider
> de Equipo de Desarrollo y Desarrollador". SaaS POS multi-restaurante desde
> cero + facturacion electronica SUNAT + KDS. UNICO developer inicial.
> `metricsEstimated: true`. Peso mas alto del CV: **leader 95**.

## Checklist de la sala

- [ ] `engine/rooms/dibal.ts` (presente, salon + cocina)
- [ ] `engine/rooms/past/dibal.ts` (pasado)
- [ ] `engine/dialogs/dibal-presente.ts` (4-5 NPCs)
- [ ] `engine/dialogs/dibal-pasado.ts` (2-3 NPCs)
- [ ] theme `dibal` con `wall: '#f2f0eb'` (verificar)
- [ ] typecheck + build + visual OK
- [ ] Actualizar [ESTADO.md](ESTADO.md)

## 1. Datos reales (es/en, textual)

**Identidad**: slug `dibal` · company `Dibal` · country `Peru` · companyUrl
`https://dibal.pe` · start `2018-12` end `2021-09` · seniority `senior` ·
niches `[architect, leader, generic]` · priority `{architect:90, leader:95,
generic:85}` (**leader es el peso mas alto**) · `metricsEstimated: true`.

**Role**: es "Lider de Equipo de Desarrollo y Desarrollador" / en "Development
Team Lead and Developer".

**Summary**: es "Tech lead y primer desarrollador de Dibal: lleve el equipo de
1 a ~5 personas y defini sus estandares de trabajo." / en "Tech lead and first
dev at Dibal: grew the team from 1 to ~5 people and defined their engineering
standards."

**Responsibilities (es)**: (1) liderazgo del equipo (organizar, prioridades,
acompañamiento tecnico); (2) arquitecturas adaptadas al negocio, incluido
modelo de **microfrontends**; (3) primer dev, construir DESDE CERO un sistema
web multi-restaurante (jQuery + Laravel); (4) e-commerce en **Vue** que integro
gestion de restaurantes con la experiencia del cliente, minimizando la
interaccion humana; (5) despliegue en **AWS** (EC2, RDS, S3, Route 53, SES,
AutoScaling, Load Balancer); (6) definir estandares y flujos de trabajo; (7)
onboarding tecnico de los nuevos devs.

**Achievements (es)**: (1) crecio el equipo de 1 dev a ~4-6, definiendo
estandares; (2) arquitectura de microfrontends (evolucion independiente,
menos acoplamiento); (3) plataforma multi-restaurante de prototipo a uso
productivo por varios restaurantes; (4) despliegue AWS con AutoScaling + Load
Balancer (disponibilidad en picos); (5) deploy de jornadas manuales a proceso
repetible de pocas horas; (6) acompaño el crecimiento casi 3 años.

**skillsTechnical**: Arquitectura de Sistemas · Computacion en la Nube ·
Desarrollo de E-commerce · Despliegue en AWS · Laravel · Microfrontend · Vue.
**skillsSoft**: Gestion de Equipos · Liderazgo de Equipo · Metodologias Agiles
· Orientado al Cliente.

> **Integracion de fuentes**: el CV enfatiza liderazgo + microfrontends + AWS
> (perfil architect/leader). El pedido del usuario enfatiza el PRODUCTO POS en
> operacion (SUNAT + KDS + impresora termica + tablet mozo). Compatible: el CV
> es "que construyo/lidero"; la sala muestra "lo que el sistema hace vivo en un
> restaurante". Los NPCs del sitio cuentan el impacto operativo; el cuaderno/
> showcase citan textualmente el CV (liderazgo, multi-restaurante, AWS).

## 2. Rubro y ambiente (salon + cocina)

**SaaS POS de restaurantes**: software en la nube (suscripcion, multi-local)
que unifica salon/mesas, cocina (KDS/KOT), caja, **facturacion electronica**,
inventario y analitica. Dibal (dibal.pe): tagline "El Mejor Sistema para
Restaurantes", respaldo del Min. de Produccion + Proinnovate, facturacion
electronica "Ilimitada" (boletas/facturas/notas de credito), planes PLATA
S/.250 / ORO S/.350 / DIAMANTE S/.450 + setup S/.1,500. Ademas e-commerce de
hardware (tienda.dibal.pe: impresoras termicas, cajones, tablets).

> La landing de Dibal confirma facturacion electronica y planes, pero **no
> lista KDS/termica** explicitamente. Se toma como verdad del CV (Pablo lo
> afirma) + patron verificado del sector en Peru (PANCA/Qway/Quesito describen
> salon->cocina en tiempo real + KDS + SUNAT).

**Presente en DOS mitades**:

- **SALON**: mesas con comensales (comida peruana: lomo saltado, ceviche, Inca
  Kola), **mozo con tablet** tomando pedido, **caja con terminal POS tactil
  todo-en-uno** navy, **impresora termica** escupiendo la boleta + rollo de
  repuesto, **cajon de dinero** con soles, **comprobante flotante con sello
  "Aceptado por SUNAT" + QR**.
- **COCINA**: cocineros en linea, **pantallas KDS** con tarjetas de comanda +
  cronometro (verde->ambar->rojo por antiguedad), **impresora de cocina**
  imprimiendo KOT, estacion de emplatado "para servir".

**Flujo (corazon de la sala)**: `Mesa -> mozo (tablet) -> [SaaS Dibal nube] ->
KDS cocina tiempo real` + `caja: cobro -> boleta termica + envio SUNAT`.

**SUNAT** = fisco peruano. Comprobante electronico OBLIGATORIO desde 2022-24
(multas hasta ~1 UIT). **Boleta de venta electronica**: serie empieza con `B`
(`B001`), consumidor final. Estructura del ticket termico (para el mockup):
LOGO + RUC emisor + `BOLETA DE VENTA ELECTRONICA B001-00001547` + fecha + items
en S/ + `Op. Gravada + IGV (18%) + TOTAL` + QR + hash + "Representacion impresa
de la Boleta de Venta Electronica / Consulte en www.sunat.gob.pe". El "sello
SUNAT" = badge **"Enviado a SUNAT correctamente ✓"** verde.

**Paleta Dibal**: **navy** (`#1B2A4A`/`#16233F`, primario: mobiliario, marco
POS, texto branding) + **teal** (`#17B3A6`/`#1DBAB0`, acento: botones/highlights
UI, cableado, luz de acento) + blanco (tickets, mostrador) + gris claro (UI,
hardware). Rojo/ambar SOLO en el estado "comanda atrasada" del KDS.

> **Aplicacion (constraint)**: pared `#f2f0eb` blanca; navy en piso/props/
> mobiliario/marcos; teal en luz de acento + highlights de pantallas.

## 3. Props firma (hardware POS)

Salon: terminal POS tactil todo-en-uno, impresora termica + rollo, cajon de
dinero con soles, tablet de pedidos en soporte, comprobante flotante con sello
SUNAT + QR, router/switch con cableado teal. Cocina: pantallas KDS con tarjetas,
impresora de cocina imprimiendo KOT. Prop focal: **flujo mozo (tablet) -> KDS**
animado con la comanda viajando + la boleta termica saliendo con sello SUNAT.

## 4. Cuadros de pared (`wallArt`)

4 laminas, **2 inspeccionables** (★):

1. **★ El flujo mozo -> KDS** — infografia mesa->tablet->nube->cocina con la
   comanda como sobre navy. Ficha: como el sistema conecto salon y cocina en
   tiempo real y elimino los papelitos (cita responsibilities 2 + impacto).
2. **★ Boleta electronica SUNAT** — representacion `B001-xxxxx` con IGV 18% +
   QR + "Aceptado por SUNAT". Ficha: que es la facturacion electronica directa
   a la API del gobierno, diferenciador legal (obligatoriedad). El "sello
   SUNAT" hecho cuadro.
3. **Mapa de restaurantes Dibal** — Peru/Lima con pines de los restaurantes +
   icono de nube (SaaS multi-local). Decorativo (multi-restaurante en uso).
4. **De 1 a 5 devs** — organigrama: Pablo ("Founding Dev / Tech Lead") + 4
   nodos + timeline 2018->2021 (MVP->produccion). Decorativo (honra el eje
   **leader** peso 95). Si se quiere reforzar liderazgo: hacerlo inspeccionable
   en vez del #3.

## 5. softwareShowcase — el POS Dibal (AC-6)

Junto a la puerta, branding navy + teal. UI de POS moderno tactil (chrome navy,
acentos teal, fondo blanco/gris, touch-first). 3 demos que `E` cicla:

1. **Tomar pedido (tablet mozo)** — header "Mesa 4 · Mozo: X", categorias en
   chips teal, grid de platos con precio S/ (Ceviche S/42, Lomo S/38, Inca Kola
   S/10), carrito lateral con observacion ("sin cebolla"), boton teal "Enviar a
   cocina" -> anima la comanda.
2. **Comanda al KDS (cocina)** — fondo oscuro, tarjetas de comanda; la de la
   demo 1 entra animada ("MESA 4 · 20:41", items, observacion, cronometro
   verde); boton "Listo" -> "PARA SERVIR" (badge teal). Tiempo real, sin
   papelitos.
3. **Boleta SUNAT (caja)** — resumen con subtotal + IGV 18% + TOTAL S/, selector
   de medio de pago (Efectivo/Tarjeta/Yape), boton teal "Emitir boleta" -> anima
   la termica escupiendo el ticket + badge "Enviado a SUNAT correctamente ✓" +
   QR + la boleta `B001-00001547`.

**Placa del showcase** (cita el CV): "Plataforma POS multi-restaurante ·
construida desde cero (jQuery + Laravel + Vue) · facturacion electronica directa
a SUNAT · desplegada en AWS (EC2/RDS/S3/AutoScaling/Load Balancer) · Founding
Dev & Tech Lead, 2018-2021".

## 6. NPCs del presente (4-5) — VARIANTE unico dev

Pablo fue el UNICO developer inicial. Se **sustituye el "compañero de
desarrollo" por 1 jefe/dueño del restaurante** (stakeholder, `Orientado al
Cliente`) + 3-4 personal del sitio. Los NPCs cuentan como el sistema cambio su
trabajo diario. Nombres peruanos.

| NPC | Enfoque | Que cuenta |
| --- | --- | --- |
| **Don Ricardo Quispe** | `[J]` dueño (define requisitos) | "Le decia a Pablo lo que necesitaba y lo hacia realidad ('ver mis 3 locales desde el celular')"; "antes vivia con miedo a SUNAT, ahora cada boleta se envia sola, aceptada, sin multas". |
| **Milagros Huaman** | `[P]` moza (tablet) | "Antes corria con papelitos que se perdian; ahora toco la tablet y la comanda ya esta en cocina"; "nunca mas grite un pedido". |
| **Chef Ernesto Ramos** | `[P]` cocinero (KDS) | "Las comandas entran ordenadas en la pantalla, con hora y observaciones; ya no adivino letras"; "veo cual mesa lleva mas esperando en rojo". |
| **Rosa Palomino** | `[P]` cajera (facturacion) | "Cobro, elijo medio de pago y en un clic sale la boleta impresa y enviada a SUNAT; antes las llenaba a mano"; "al cierre el sistema me cuadra la caja sola". |
| **Andrea Chavez** | `[P]` comensal (opcional) | "Pedi, me atendieron rapido y me llego la boleta con QR al toque; se nota que aca todo esta conectado." |

> Ceñir a 4: dejar dueño + moza + cocinero + cajera. Andrea es extra de
> ambientacion.

## 7. Pasado (sepia, refactor — AC-20) — "el restaurante antes de Dibal"

Sistema manual desastroso, sepia + grano. Reusa props del presente rotos/
desordenados:

- **Papelitos de comanda por todos lados**: arrugados en el piso, pinchados en
  un clavo sobre el pase, uno volando, varios **perdidos entre salon y cocina**
  (uno caido a mitad de camino).
- **Mozo gritando el pedido** (bocadillo manga: "¡MESA 4, DOS LOMOS!"),
  corriendo con libreta.
- **Cocina confundida**: cocineros mirando papelitos ilegibles, uno rascandose
  la cabeza, 2 platos equivocados en el pase, un "?" flotando.
- **Caja con boletas a mano**: talonario fisico con papel carbon, calculadora
  vieja, boletas a medio llenar. **Sin termica, sin QR, sin SUNAT**.
- **Cajon descuadrado**: post-it "falta S/40 (?)".
- Reloj marcando tarde (cierre a medianoche por el cuadre manual).

**NPCs del pasado** (2-3, frustrados, nombres distintos = "el equipo de
antes"):

- **Julio Vargas (mozo)** — "¡Otra vez se perdio la comanda de la mesa 6! Corro,
  grito, y la cocina saca lo que no es. Termino el turno ronco."
- **Doña Carmen Flores (cocinera)** — "No entiendo la letra de este papelito...
  ¿son dos ceviches o dos cevichitos? Ya salio mal el plato tres veces hoy."
- **Elena Torres (cajera)** — "Lleno cada boleta a mano, con carbon, y el cuadre
  me lleva hasta medianoche. Vivo con el susto de una multa de SUNAT."

Ceñir a 2: mozo (Julio) + cajera (Elena). Objeto de busqueda lenta: seguir un
papelito perdido. Panel de historia (`onStory`).

## 8. Retos y aprendizajes (infoKit)

**RETOS (es)**: construir desde cero un POS multi-restaurante (jQuery+Laravel)
siendo el primer y unico dev; integrar facturacion electronica directa con
SUNAT sin errores; conectar salon y cocina en tiempo real (comanda mozo->KDS);
sostener la plataforma en AWS en picos de demanda; definir arquitecturas
(microfrontends) mientras lidera y crece el equipo de 1 a ~5. **(en)** analogo.

**APRENDIZAJES (es)**: plataforma multi-restaurante de prototipo a uso
productivo por varios restaurantes; facturacion electronica a SUNAT + e-commerce
en Vue; arquitectura de microfrontends (menos acoplamiento); despliegue AWS
(EC2/RDS/S3/Route 53/SES/AutoScaling/Load Balancer), deploy de jornadas a pocas
horas; crecer como lider (de unico dev a ~4-6 con estandares). Skills:
arquitectura, cloud, e-commerce, AWS, Laravel, microfrontend, Vue + gestion/
liderazgo/agilidad/orientacion al cliente. **(en)** analogo.

## Notas de consistencia

- Prioriza el producto POS (pedido del usuario) pero cita el CV en showcase +
  fichas (veracidad/indexabilidad). El eje leader (95) se honra con el cuadro
  "De 1 a 5 devs" + la placa, sin desplazar el foco del restaurante.
- Color: pared `#f2f0eb`; navy en piso/mobiliario/marcos/branding; teal en luz
  + highlights UI; rojo/ambar SOLO en "comanda atrasada" del KDS.

## Fuentes

`packages/content/src/data-cache/experiences.json` (slug dibal) ·
`docs/progress/explore_empresas_latam1.md` (Dibal: props, paleta navy+teal) ·
`docs/specs/journey-3d-cv/01-propuesta-a-habitaciones.md` (Sala 4) · dibal.pe
(tagline, facturacion, planes) · PANCA/Qway/Quesito (flujo salon->cocina, KDS,
boleta B001, "Enviado a SUNAT") · SUNAT (boleta electronica serie B, QR).
