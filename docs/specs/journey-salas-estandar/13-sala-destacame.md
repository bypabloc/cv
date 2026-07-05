# 13 — Sala Destacame UNIFICADA (Etapa 2, sala 6)

> Informe AUTOCONTENIDO para crear la sala `destacame` (ex-`cima`) en una
> sesion aislada. **La sala mas compleja del recorrido.** Prerequisito: Etapa
> 1 hecha. Leer antes: [README](README.md) +
> [02-el-canon-de-sala.md](02-el-canon-de-sala.md) + [ESTADO.md](ESTADO.md).
>
> UNIFICA 2 experiencias: slug `destacame-frontend` (senior 2021-22, Vue/Nuxt +
> flujos de pago con bancos) + `destacame-architect` (lead 2022-hoy,
> microfrontends + microservicios Django + Chile+Mexico + liderazgo + vibe
> coding). La CIMA de la carrera. Company `Destacame` · `https://destacame.cl`
> · Chile. `metricsEstimated: true`.

## Checklist de la sala

- [ ] `engine/rooms/destacame.ts` (presente, 2 areas) — reescribe `cima.ts`
- [ ] `engine/rooms/past/destacame.ts` (pasado, deudas)
- [ ] `engine/dialogs/destacame-presente.ts` (4-5 NPCs)
- [ ] `engine/dialogs/destacame-pasado.ts` (2-3 NPCs)
- [ ] theme `destacame` con `wall: '#f2f0eb'` (verificar)
- [ ] ELIMINAR la micro Chile/Mexico (`buildOrchestration` con labels CHILE/
      MEXICO) — NO recrearla
- [ ] typecheck + build + visual OK
- [ ] Actualizar [ESTADO.md](ESTADO.md)

## 1. Datos reales de AMBAS experiencias (es/en, textual)

### 1.A `destacame-frontend` (senior, 2021-12/2022-08, ~8 meses)

- niches fintech/generic (fintech 90, generic 95). Role es "Desarrollador Web
  Frontend" / en "Web Frontend Developer".
- **Summary**: es "Construi interfaces Vue/Nuxt para los productos fintech de
  Destacame en Chile antes de pasar al rol de arquitecto."
- **Responsibilities (es)**: (1) frontend fintech con Vue+Nuxt (flujos
  financieros); (2) estandares y nuevas tecnologias (UX + consistencia); (3)
  datos SENSIBLES (validacion de formularios + presentacion financiera); (4)
  aprender Python/Django para crecer a full stack; (5) colaborar con producto
  y diseño; (6) refactorizar componentes para reducir deuda tecnica.
- **Achievements (es)**: (1) interfaces en uso real en Chile; (2) mejoro
  calidad/eficiencia del frontend con nuevas tecnologias; (3) redujo deuda
  tecnica refactorizando (acorto time-to-ship); (4) de frontend puro a full
  stack en ~8 meses (Python/Django desde cero); (5) versatilidad del equipo.
- **skillsTechnical**: Desarrollo Frontend/Web · Django · Nuxt.js · Python ·
  TypeScript · Vue.js. **skillsSoft**: Agilidad de Aprendizaje · Resolucion ·
  Trabajo en Equipo.

### 1.B `destacame-architect` (lead, 2022-08/presente)

- niches fintech/architect/leader/vibe/generic (los 5 en priority 100). Role
  es "Arquitecto Frontend y Desarrollador de Microservicios".
- **Summary**: es "Arquitecto frontend lidere la migracion a microfrontends y
  orqueste los productos fintech de Destacame para Chile y Mexico."
- **Responsibilities (es)**: (1) arquitectura frontend bajo **microfrontends**
  (estandares/patrones entre equipos); (2) productos fintech: plataforma para
  saldar deudas en Chile + creditos por niveles en Mexico; (3) **microservicios
  Python/Django** integrados con el frontend; (4) liderazgo tecnico del equipo
  de optimizacion y luego de plataforma; (5) herramientas internas (un admin de
  campañas que automatizo un proceso manual); (6) incorporo **desarrollo
  asistido por IA (vibe coding)** de forma productiva y segura; (7) despliegue
  en AWS.
- **Achievements (es)**: (1) arquitectura de microfrontends (equipos en
  paralelo, menos acoplamiento); (2) lidero equipos de 4-6 sosteniendo la
  entrega a traves de reorganizaciones/reducciones; (3) productos fintech en
  uso real (conocimiento de deuda y credito Chile+Mexico); (4) admin de
  campañas que redujo un proceso manual de **horas a minutos**; (5) IA-assisted
  acorto tareas repetitivas; (6) rol de creciente responsabilidad >3 años (hoy
  en plataforma).
- **skillsTechnical**: AWS · Arquitectura Frontend · Django · Microfrontend ·
  Microservicios · Python · TypeScript. **skillsSoft**: Adaptabilidad ·
  Fintech · Liderazgo Tecnico · Planificacion Estrategica.

> **CORRECCION de fidelidad**: el JSON dice **"microfrontends"** (frontend) y
> **"microservicios Python/Django"** (backend). El "Design System + DDD + fork
> por entidad" NO esta textual en el JSON — es interpretacion editorial VALIDA
> como **guiño ambiental** (props), pero los textos data-driven (retos/
> aprendizajes) salen de los campos reales, sin inventar metricas.

## 2. Rubro y ambiente

**Destacame** = fintech chilena de inclusion financiera y gestion de deudas.
App gratuita: consultar/mejorar el score crediticio, resolver deudas morosas
con descuentos, acceder a creditos. "SuperApp de salud financiera", +2-4M
usuarios en Chile y Mexico, alianza con Buro de Credito (MX). Rebancarizar a
morosos. **PagaloAqui** = plataforma web para pagar deudas online con bancos
(co-branded por banco, 100% online, WebPay).

**El score crediticio (prop firma)**: gauge/medidor semicircular con aguja,
rango **459-760**, verde->amarillo->rojo. Iconografia inconfundible de la
marca. En 3D: panel azul con arco de score + aguja + numero grande. Ancla
visual del Area B.

**Ambiente (presente, decisiones del usuario)**: oficina real (escritorios con
laptops + **gente sentada usandolas**). Pared `#f2f0eb` blanca, acento **azul
Destacame `#0052CC`** en piso/props/luz. Fintech moderno, plano, minimalista.
Azul dominante + blanco + verde "aprobado" + coral "mora". Mantener: kit info +
puerta "Proximamente" + CTA. **ELIMINAR la micro Chile/Mexico de la entrada**
(el usuario la odia; NO recrear).

## 3. Branding de las 5 webs (para los mockups)

> **Accesibilidad WebFetch**: los 3 portales PagaloAqui son SPAs con render JS.
> `pagaloaqui.cl/santander` y `/santanderconsumer` dieron **404** (rutas
> client-side); `solucionesscotiabank.pagaloaqui.cl` cargo en loading (sin
> render). NO se pudo extraer branding real de las 3 bancarias -> colores
> co-branded del conocimiento verificado de marca. **destacame.cl y
> destacame.com.mx SI cargaron** (branding real extraido).

| Web | Marca | Color primario | UI clave |
| --- | --- | --- | --- |
| pagaloaqui.cl/santander | Santander | Rojo **`#EA1D25`** | Card deuda + RUT + WebPay |
| pagaloaqui.cl/santanderconsumer | Santander Consumer | Rojo `#EA1D25` | Card "Paga tu Cuota" + WebPay |
| solucionesscotiabank.pagaloaqui.cl | Scotiabank | Rojo **`#EC111A`** (~`#EC0712`) | Card deuda vencida + WebPay |
| destacame.cl | Destacame CL | Azul **`#0052CC`** | RUT+email, gauge score, descuento 95% |
| destacame.com.mx | Destacame MX | Azul `#0052CC` | Score Buro gratis, gauge, dashboard movil |

Destacame CL: azul `#0052CC`, hover `#003D99`-`#00337A`, cards `#E6F0FF`-
`#CCE0FF`, grises `#6B7280`/`#9CA3AF`, verde `#22C55E`, coral mora `#EF4444`.
Descuento hasta 95% en deuda vencida, creditos preaprobados, planes Basico/PRO
$2.600/PRO+ $8.990. Destacame MX: consulta gratis del Score de Buro sin afectar
historial, alianza Buro de Credito, dashboard movil con score meters, WhatsApp.

> **Regla de color 3D**: Area A (PagaloAqui) usa el rojo de CADA banco DENTRO
> de su card del showcase A (Santander/Santander Consumer/Scotiabank), sobre
> blanco. Area B (Destacame) usa azul `#0052CC`. El unico acento ESTRUCTURAL de
> la sala (piso/luz) es el azul `#0052CC`; los rojos viven SOLO en las cards
> del showcase A.

## 4. Las 2 areas + guiños intrinsecos

Oficina fintech blanca con acento azul, dividida en 2 areas contiguas. Los
guiños de arquitectura NO tienen area propia (props ambientales).

### AREA A — PagaloAqui (pagar deudas con bancos)

- **Showcase A** = monitor/kiosco de pago que **cicla 3 pantallas co-branded**:
  Santander -> Santander Consumer -> Scotiabank.
- Props: cards de deuda flotantes, sello **WebPay**, tarjeta bancaria low-poly,
  tag flotante **"deuda -95%"**, pila de monedas.
- NPCs cercanos: dev frontend fintech + representante de banco (de visita).

### AREA B — Producto Destacame (score + mejoras)

- **Showcase B** = monitor/totem con el **gauge de score 459-760** que **cicla
  destacame.cl <-> destacame.com.mx**.
- Props: smartphone con la SuperApp (gauge + boton azul), panel KPIs ("+2M
  usuarios"), tarjeta prepago Destacame azul, grafico ascendente de score,
  planta.
- NPCs cercanos: dev fullstack Python/Django+Vue/Nuxt + PM/stakeholder.

### GUIÑOS INTRINSECOS (props ambientales, repartidos por la sala)

1. **Pizarra del Design System** (tokens + componentes).
2. **Diagrama de microfrontends** (shell/host central + remotes = productos
   fintech, flechas de "fork por entidad" hacia logos de bancos). **Label:
   "microfrontends"** (dato del JSON), NO "microservicios".
3. **Grafo de microservicios Django** (nodos/aristas backend Python/Django) —
   reusar `graphTexture` de `cima.ts:67`.
4. **Mesa de reunion** con sillas (una la ocupa Pablo liderando) — guiño al
   liderazgo de equipos 4-6.
5. **Monitor de vibe coding / IA-assisted** (editor con sugerencias IA) —
   reusar el ciclo vibe->python->ts de `cima.ts:302`.
6. Holograma/cartel azul "plataforma" (el logro que corona la sala).

> Distribucion: Area A a un lado, Area B al otro; guiños de arquitectura
> (pizarras DS/microfrontends, grafo microservicios) en las paredes del fondo;
> mesa de reunion + monitor de vibe coding en un rincon "de lead" cerca del CTA
> y la puerta "Proximamente".

## 5. Los 2 showcases (AC-6)

UI fintech Vue/Nuxt (planas, tarjetas modulares, formularios validados). Cada
showcase cicla con `E`.

**Showcase A — cards de pago co-branded**:

- **A1 Santander** — "Tu deuda con Banco Santander": monto total grande (ej.
  $842.500), estado "Vencida", cuotas atrasadas, boton rojo `#EA1D25` "Pagar
  ahora" + WebPay.
- **A2 Santander Consumer** — "Paga tu Cuota": credito de consumo/automotriz,
  "Cuota del mes" $126.900, fecha, saldo, boton rojo "Pagar cuota" + WebPay.
- **A3 Scotiabank** — "Regulariza tu deuda vencida": rojo `#EC111A`, monto,
  alternativas (pago total vs repactacion) + descuento, boton "Regularizar 100%
  online" + WebPay.

**Showcase B — score gauge + producto**:

- **B1 destacame.cl** — dashboard de Score: azul `#0052CC`, **gauge 459-760**
  con aguja (ej. 612), card "hasta 95% de descuento en tu deuda vencida" +
  boton azul "Ver mis descuentos". Micro-mejora: toggle antes/despues de UI
  (vieja -> Vue/Nuxt nitida).
- **B2 destacame.com.mx** — "Tu Score de Buro GRATIS": gauge de Buro (mockup de
  telefono con score meter), "sin afectar tu historial", recomendaciones
  (cards de creditos/tarjetas con checks), alianza Buro de Credito, boton azul
  "Consultar gratis" + WhatsApp.

## 6. NPCs del presente (4-5, 2 enfoques + eje leader)

| NPC | Enfoque | Que cuenta |
| --- | --- | --- |
| **Camila Fuentes** (CL) | `[C]` dev frontend | Migraron interfaces heredadas a Vue/Nuxt y bajaron deuda tecnica; los flujos de pago de PagaloAqui (Santander/Scotiabank) pasaban por ellos -> aprendio a cuidar validacion + datos sensibles. |
| **Diego Riquelme** (CL) | `[C]` dev fullstack | Pablo entro frontend puro y en ~8 meses ya metia Python/Django (equipo mas versatil); armo microservicios Django + un admin de campañas de horas a minutos. |
| **Rodrigo Salinas** (CL) | `[P]` representante de banco (de visita) | Era el contacto del banco cuando pidieron el flujo de pago online; lo dejaron 100% online con WebPay co-branded; los clientes con deuda vencida regularizaban rapido y seguro. |
| **Valentina Cardenas** (CL) | `[J]` PM/stakeholder | Traducian requerimientos en interfaces claras; cuando Pablo paso a arquitecto definio estandares/patrones entre equipos (paralelo sin pisarse); su conocimiento de deuda/credito CL+MX los ordeno. |
| **Ana Sofia Herrera** (MX) | `[J]`/lead (opcional) | Le reporta; Pablo sostuvo la entrega a traves de reorganizaciones/reducciones; les metio el **vibe coding** (IA productiva y segura), acortando tareas repetitivas. |

> Ana Sofia (mexicana) comunica la expansion a Mexico SIN recrear los labels
> CHILE/MEXICO eliminados. Recortable a 4 quitando Ana Sofia (pero es la que
> honra los ejes leader + vibe).

## 7. Pasado (sepia, refactor — AC-13, AC-20) — drama de deudas

Cruzar la grieta -> glitch -> sepia + grano. El drama fintech previo a la
plataforma. Elementos:

- **Rincon oscuro con personas TRISTES y agobiadas por deudas**: figuras
  cabizbajas frente a papeles de cobranza, cartas de morosidad apiladas,
  telefono sonando (cobrador), gauge de score en **rojo/coral** (mora). Nadie
  sabe negociar; sin descuentos, sin plataforma online; hay que ir a la
  sucursal.
- **Operador desbordado**: un escritorio con pilas de planillas ejecutando **a
  mano un admin de campañas** que toma **horas** (el que Pablo automatizo a
  minutos). Reloj tarde, cafe frio.
- **Silos y un solo pais**: solo Chile (sin Mexico), servicios sin orquestar,
  interfaces viejas/feas, formularios rotos, stack legacy lento (el "antes de
  migrar a Vue/Nuxt").
- Paleta: **sepia + coral de mora**, SIN el azul de marca (el azul llega con la
  plataforma del presente).

**NPCs del pasado** (2-3, con nombre):

- **Don Hernan Poblete (deudor agobiado)** — "Tengo tres deudas vencidas y no
  se por donde empezar. Para regularizar tengo que ir al banco, hacer fila, y
  nadie me explica si hay descuento. Vivo con la angustia de la morosidad."
- **Marta Sepulveda (deudora triste)** — "Mi score esta por el suelo y siento
  que nadie me da una oportunidad. No hay una app donde vea mi situacion clara;
  solo cartas de cobranza. Me da verguenza pedir ayuda."
- **Nicolas Vera (operador de campañas desbordado)** — "Cada campaña la armo a
  mano en planillas: me toma horas y muchas veces algo sale mal. Un solo pais,
  todo aislado, sin herramienta que lo automatice. Termino tardisimo."

> Al volver al presente (recupera color): admin manual -> automatizado (horas->
> minutos), interfaces viejas -> Vue/Nuxt, un solo pais -> Chile+Mexico,
> deudores tristes -> plataforma que resuelve deudas con 95% de descuento +
> score gratis. Objeto de busqueda lenta: intentar pagar una deuda sin sistema.
> Panel de historia (`onStory`).

## 8. Retos y aprendizajes FUSIONADOS (infoKit)

**RETOS (es)**: migrar interfaces heredadas a Vue/Nuxt reduciendo deuda tecnica
+ construir flujos de pago con bancos (PagaloAqui) con datos sensibles; dejar
de reescribir el frontend por producto -> arquitectura de **microfrontends**
(estandares entre equipos); construir microservicios Python/Django integrados
con el frontend (frontend -> full stack); orquestar productos fintech para
**Chile y Mexico**; liderar equipos 4-6 a traves de reorganizaciones; automatizar
procesos manuales (admin de campañas de horas) + incorporar IA (vibe coding).
**(en)** analogo.

**APRENDIZAJES (es)**: interfaces fintech en uso real en Chile + refactor de
componentes (menos time-to-ship); de frontend puro a full stack en ~8 meses
(Python/Django); arquitectura de microfrontends (equipos en paralelo, menos
acoplamiento); productos fintech en uso real (deuda/credito CL+MX); liderazgo
tecnico de equipos 4-6 + rol de creciente responsabilidad >3 años; admin de
campañas de **horas a minutos** + vibe coding al equipo. Skills: Vue/Nuxt/TS/
Python/Django/Microfrontend/Microservicios/Arquitectura Frontend/AWS +
Liderazgo Tecnico/Adaptabilidad/Planificacion Estrategica/Fintech/Resolucion/
Trabajo en Equipo/Agilidad de Aprendizaje. **(en)** analogo.

## Notas de fidelidad

- **Term matching**: "microfrontends" (frontend), "microservicios Python/
  Django" (backend). DS/DDD/fork = guiño editorial, no en el JSON.
- Los 3 portales PagaloAqui NO se scrapearon (404/SPA); rojos co-branded
  verificados: Santander/Consumer `#EA1D25`, Scotiabank `#EC111A`. Destacame
  CL/MX: azul `#0052CC` (scrapeados).
- Constraints: 1 sala / 2 areas; guiños de arquitectura como props (no area);
  SIN labels Chile/Mexico en la entrada; oficina blanca + azul con gente
  sentada; pasado = deudores tristes + operador desbordado; mantener kit +
  Proximamente + CTA. La expansion a Mexico se comunica via Showcase B + la NPC
  mexicana, sin la micro de mapas eliminada.

## Fuentes

`packages/content/src/data-cache/experiences.json` (slugs destacame-frontend +
destacame-architect) · `docs/progress/explore_empresa_destacame.md` ·
`docs/specs/journey-3d-cv/01-propuesta-a-habitaciones.md` (Salas 6/7/8) ·
destacame.cl + destacame.com.mx (branding real) · pagaloaqui.cl +
solucionesscotiabank.pagaloaqui.cl (404/loading) · brand colors Santander
`#EA1D25` / Scotiabank `#EC111A`.
