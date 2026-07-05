# 12 — Sala GoodMeal (Etapa 2, sala 5)

> Informe AUTOCONTENIDO para crear la sala `goodmeal` en una sesion aislada.
> Prerequisito: Etapa 1 hecha. Leer antes: [README](README.md) +
> [02-el-canon-de-sala.md](02-el-canon-de-sala.md) + [ESTADO.md](ESTADO.md).
>
> Experiencia real: slug `goodmeal` · GoodMeal · `https://www.goodmeal.app` ·
> Chile · mid 2021-05/2021-12 · "Desarrollador Web Full Stack". Lidero la
> MIGRACION del frontend a Vue 3 + reforzo el flujo de pagos de la app.
> `metricsEstimated: true`.

## Checklist de la sala

- [ ] `engine/rooms/goodmeal.ts` (presente)
- [ ] `engine/rooms/past/goodmeal.ts` (pasado)
- [ ] `engine/dialogs/goodmeal-presente.ts` (4-5 NPCs)
- [ ] `engine/dialogs/goodmeal-pasado.ts` (2-3 NPCs)
- [ ] theme `goodmeal` con `wall: '#f2f0eb'` (verificar)
- [ ] typecheck + build + visual OK
- [ ] Actualizar [ESTADO.md](ESTADO.md)

## 1. Datos reales (es/en, textual)

**Identidad**: slug `goodmeal` · company `GoodMeal` · country `Chile` ·
companyUrl `https://www.goodmeal.app` · start `2021-05` end `2021-12` ·
seniority `mid` · niches `[fintech, generic]` · `metricsEstimated: true`.

**Role**: es "Desarrollador Web Full Stack" / en "Full Stack Web Developer".

**Summary**: es "Lidere la migracion del frontend de GoodMeal a Vue 3,
modernizando la base de codigo y la experiencia del usuario." / en analogo.

**Responsibilities (es)**: (1) reestructuracion del frontend migrandolo a Vue 3
con tooling moderno (rendimiento + mantenibilidad); (2) desarrollo FULL STACK
integrando frontend con servicios backend; (3) resolucion de bugs + solicitudes
de PMs bajo plazos ajustados; (4) colaboracion bajo Scrum (dailies +
planificacion de iteraciones); (5) soporte al FLUJO DE PAGOS y transacciones
de la app de pedidos (consistencia de datos sensibles); (6) adopcion de
estandares de codigo.

**Achievements (es)**: (1) lidero la migracion del frontend a Vue 3
(moderniza base de codigo + mejora notable de la UX de la app de pedidos); (2)
contribuyo al flujo de pagos de la plataforma fintech-adyacente (fiabilidad de
transacciones); (3) redujo tiempo de resolucion de bugs recurrentes
estabilizando el frontend; (4) entregas consistentes bajo plazos ajustados de
startup; (5) aporto a las practicas de Scrum (previsibilidad de entregas).

**skillsTechnical**: Aplicacion Web · Correccion de Errores · Desarrollo Full
Stack · Scrum · Vue 3. **skillsSoft**: Adaptabilidad · Gestion de Proyectos ·
Gestion del Tiempo · Resolucion de Problemas · Trabajo en Equipo.

> El CV etiqueta la plataforma "fintech-adyacente" (maneja pagos/transacciones
> de pedidos) — util para el NPC de pagos.

## 2. Rubro y ambiente

**GoodMeal** = food-tech chileno anti-desperdicio: marketplace/app que rescata
el **excedente comestible** de cafeterias/panaderias/restaurantes y lo revende
rebajado antes de botarlo. Analogo chileno de **Too Good To Go**. Respaldo de
Endeavor Chile. +3.000 comercios (RM + Valparaiso). Partners reales: Starbucks,
Dunkin, Juan Valdez, Oxxo, San Camilo, Melt Pizzas.

**La "Good Bag"** (hero de branding): la bolsa sorpresa (papel **kraft** + logo
teal + tapa enrollada + "?") con una combinacion de productos que varia diario.
El cliente compra a ciegas (sabe el local y el tipo, no el contenido exacto).
Ahorro **50-70%** (el valor triplica lo pagado).

**Flujo (para animar)**: cafeteria rescata su excedente -> empaca la Good Bag
-> la publica en la app (cantidad + horario + precio) -> cliente la compra
(paga en la app: aqui entra el aporte de Pablo) -> la recoge (pin geo) -> sube
el contador de impacto (comida rescatada / CO2 evitado).

**Datos de impacto reales** (contador y cuadros): ">1/3 de la comida producida
se desperdicia"; "el desperdicio = 10% de los gases de efecto invernadero".

**Branding** (confirmado en goodmeal.app): **teal/turquesa** primario
(`~#1DB5A6`/`#12B7A9`, logo + CTA) + blanco (fondo minimalista) + negro (tipo) +
**kraft** (marron claro de la Good Bag, material firma) + verde-hoja
(sostenibilidad). Estetica lifestyle aspiracional (NO "sobras"). Taglines:
**"Ahorra, come rico y cuida el planeta"** / **"Salvar el mundo no es magico,
es simple"**.

> **Aplicacion (constraint)**: pared `#f2f0eb` blanca; teal GoodMeal + kraft en
> piso/props/luz; comida en colores calidos; luz calida de startup + brotes.

## 3. Props firma del rubro (presente)

- **Good Bag kraft** (logo teal, tapa enrollada, etiqueta "-50%/-70%", "?").
- **Estantes de "excedente del dia"** / comida rescatada en bandejas (marcada
  para rescate, no tacho).
- **Vitrina/mostrador de cafeteria** con donas (glaseado rosa), pizza en
  porcion, pan, pasteles low-poly.
- **Smartphone gigante con la app**: card de Good Bag con **precio tachado ->
  rebajado** + boton teal.
- **Pin de geolocalizacion** flotante.
- **Contador de impacto** (panel "X comidas rescatadas / kg CO2 evitados",
  barra creciente verde).
- **Plantas/brotes en maceta** (motivo eco).
- **Caja registradora + tarro de propinas** (merma convertida en ingreso).

## 4. Cuadros de pared (`wallArt`)

3-4 laminas, **2 inspeccionables** (★):

1. **★ "1/3 de la comida se desperdicia"** — infografia: ">1/3 de la comida se
   desperdicia" + "desperdicio = 10% de gases de efecto invernadero". Ficha: el
   dato real + el proposito de GoodMeal (cuadro-tesis del rubro).
2. **★ "Logo Vue 3"** — triangulo Vue (verde/teal conversa con el teal de
   marca) + "Migracion v2 -> v3" + barra "migracion 100%". Ficha: el logro
   tecnico de Pablo (guiño personal).
3. **"Mapa de locales"** — Santiago/Valparaiso con pines teal (+3.000
   comercios). Decorativo.
4. (Opcional) **"Ahorra, come rico y cuida el planeta"** — tagline oficial +
   Good Bag + brote. Decorativo.

## 5. softwareShowcase — la app GoodMeal + migracion Vue 3 (AC-6)

Junto a la puerta, branding teal + kraft. UI de app movil 2021 (bordes
redondeados suaves, cards con sombra ligera, CTA teal, sans limpia). 3 demos
que `E` cicla:

1. **Listado de Good Bags** — "cerca de ti": cards con foto (dona/pizza/pan),
   local (Dunkin/Juan Valdez), **precio de lista tachado -> rebajado** en teal,
   chip "-50%/-70%", horario de retiro, pin geo.
2. **Flujo de pago** (aporte de Pablo, achievement 2) — checkout de la Good
   Bag: resumen, medio de pago, boton "Pagar" teal -> "procesando" ->
   "Pedido confirmado, retiralo entre HH:MM y HH:MM". Guiño: candado/escudo de
   "transaccion segura".
3. **App vieja -> UI Vue 3 nitida** (guiño central) — split/transicion: UI
   vieja (translucida, desvaneciendose, apretada) -> UI Vue 3 nitida (limpia,
   fluida). Logo de Vue flotando + barra "migracion 100%". El antes/despues del
   refactor.

> La estabilizacion/menos bugs (achievement 3) se insinua con un contador
> "bugs recurrentes ↓" en un monitor de dev.

## 6. NPCs del presente (4-5, 2 enfoques)

Nombres chilenos. 2 devs del equipo Scrum + 2 personal del sitio + PM opcional.

| NPC | Enfoque | Que cuenta |
| --- | --- | --- |
| **Camila Fuentes** | `[C]` frontend dev | La app estaba en Vue viejo (cada cambio dolia); Pablo lidero el paso a Vue 3 con tooling moderno; dejo estandares de codigo claros. |
| **Matias Rojas** | `[C]` backend dev | Pablo no se quedaba en el frontend: full stack, integraba front con los servicios y le entraba al flujo de pagos; reforzo las transacciones cuidando la consistencia. |
| **Jorge Aravena** | `[P]` staff del local (empaca Good Bags) | "Antes botabamos cajas de pan y donas cada noche; ahora armo las Good Bags con lo que sobra y la gente las viene a buscar; en la app veo cuantas reservaron." |
| **Valentina Soto** | `[P]` clienta | "Reservo una Good Bag cerca de la pega y pago en la app en dos toques; me sale como un tercio; la app antes se pegaba, ahora anda fluida." |
| **Daniela Herrera** | `[J]` PM/Product Owner (opcional) | "En una startup asi todo es contra el tiempo; Pablo entregaba parejo sprint a sprint y resolvia bugs recurrentes rapido; aporto a ordenar el Scrum." |

> Los devs (Camila, Matias, Daniela) hablan de trabajar con Pablo; staff/
> clienta (Jorge, Valentina) del impacto/experiencia que la app habilita.
> Recortable a 4 quitando Daniela.

## 7. Pasado (sepia, refactor — AC-20) — "el antes del rubro: el desperdicio"

Cruzar el portal lleva al momento del **cierre** del local, botando comida
comestible. Sepia + grano, luz apagada de cierre. Contrasta con el "mundo cero
desperdicio" del presente. Elementos:

- Es de noche, el local va a cerrar. Luz fria/tenue, colores lavados.
- **Bandejas de pan, pizza en porcion y donas yendo a la basura**: comida en
  perfecto estado volcandose a un tacho grande o a **bolsas de residuos negras**
  junto a la puerta trasera.
- **Vitrina a medio vaciar** empujada a un carro de desechos en vez de
  rescatarse.
- **Bolsas de basura apiladas** con siluetas de cajas de comida adentro.
- **Reloj marcando el cierre** + tacho rebosante. Ningun cliente, ningun
  smartphone, ninguna Good Bag.
- Cartel gris "excedente -> basura" (flujo inverso al presente).

**NPCs del pasado** (2-3, staff resignado):

- **Rodrigo Caceres (encargado de cierre)** — "Otra noche botando media
  vitrina. Esta perfecta, pero al cierre no la puedo vender... derecho al tacho.
  Es plata a la basura, y todos los dias lo mismo."
- **Ignacia Muñoz (dependienta)** — "Me da lata tirar el pan y las donas que
  sobran; alguien se las comeria feliz. Pero no hay como... no tenemos a quien
  darselas antes de cerrar."
- **Sr. Peña (dueño, opcional)** — "Cada bolsa de basura que sacamos es producto
  que pague y no recupere. Si hubiera una forma de vender aunque sea barato lo
  que sobra..." (planta la solucion que GoodMeal traera).

> Al volver al presente, la escena recupera color y el mismo Jorge (NPC del
> presente) empaca Good Bags en vez de llenar bolsas de basura — el antes/
> despues en la misma persona. Objeto de busqueda lenta: ver la comida ir al
> tacho. Panel de historia (`onStory`).

## 8. Retos y aprendizajes (infoKit)

**RETOS (es)**: modernizar un frontend heredado a Vue 3 sin frenar el producto
en marcha; integrar frontend con los servicios backend (full stack); sostener y
reforzar el flujo de pagos/transacciones cuidando la consistencia de datos
sensibles; resolver bugs y atender a los PMs bajo plazos ajustados; entregar
consistente bajo Scrum. **(en)** analogo.

**APRENDIZAJES (es)**: lidere la migracion a Vue 3 (rendimiento +
mantenibilidad + UX); reforce el flujo de pagos (fiabilidad de transacciones);
reduje tiempo de bugs recurrentes con un stack mas predecible; adopte estandares
de codigo; aporte al Scrum (previsibilidad). Skills: Vue 3, Full Stack,
Correccion de Errores, Scrum, Aplicacion Web + Adaptabilidad, Gestion de
Proyectos/Tiempo, Resolucion, Trabajo en Equipo. **(en)** analogo.

## Fuentes

`packages/content/src/data-cache/experiences.json` (slug goodmeal) ·
`docs/progress/explore_empresas_latam1.md` (GoodMeal: props, paleta teal+kraft,
Good Bags) · `docs/specs/journey-3d-cv/01-propuesta-a-habitaciones.md` (Sala 5)
· goodmeal.app (modelo, taglines, partners, "-50%", ">1/3", branding teal+
kraft) · Too Good To Go (referente global del rubro). paiscircular.cl dio 403
(no usada; fundadores/año no verificados, omitidos).
