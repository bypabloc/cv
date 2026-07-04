# Propuesta A — Habitaciones conectadas (POV inmersivo tipo juego) — RECOMENDADA #1

> [<- README](README.md) · [Siguiente: Propuesta B (scroll) ->](02-propuesta-b-scroll-journey.md)

Un **walking simulator** en primera persona: empiezas en una habitacion (tus
inicios en la universidad), caminas con teclado/touch hacia una **puerta**, la
abres, y entras a la habitacion de tu primera experiencia — decorada acorde a
ese logro y esa epoca. Y asi sucesivamente: **una habitacion por experiencia**,
encadenadas por puertas, con **ida y vuelta** (puedes regresar). Cada sala es
representativa de su etapa y sus logros. Es el concepto que pidio el usuario y
la propuesta **prioritaria** del plan.

## Diferencia con las Propuestas G, D y F

- **NO es G (mundo abierto libre)**: aqui el recorrido es una **secuencia
  dirigida** de salas conectadas por puertas, no un mundo abierto. Mas barato,
  mas narrativo, sin navmesh ni heightmap.
- **NO es D (museo neutro)**: no es una galeria uniforme de cuadros. Cada
  habitacion tiene **arte-direccion propia** segun la epoca/logro (la sala
  universidad no se parece a la sala de arquitecto).
- **NO es F (ciudad)**: el POV es interior, intimo, habitable — no una avenida.

Es lo mas cercano a un **videojuego narrativo** (tipo Gone Home, The Beginner's
Guide, Superliminal): explorar espacios que cuentan una historia.

## Principio de diseño: cada sala ES el rubro real de esa empresa

**CRITICO (peticion del usuario):** una habitacion NO es una oficina generica.
Cada sala recrea el **rubro real de la empresa** donde Pablo trabajo, con sus
props, colores y ambiente caracteristicos, poblada con **personas (NPCs
low-poly) trabajando/caminando**. La investigacion de cada empresa esta en
`docs/progress/explore_empresas_*.md` (rubro, props, paleta, guiños verificados
de fuentes reales).

### Estructura fija de CADA sala (5 elementos)

1. **Ambiente del rubro** — recreacion low-poly del entorno real (central
   electrica, consultorio, planta farmaceutica, POS de restaurante, fintech...)
   + NPCs (2-4 personas del rubro con idle/caminar: tecnicos, medicos,
   operarios, mozos, devs).
2. **Objeto de APRENDIZAJES** — un cuaderno O una pizarra (segun la sala) que
   al acercarse abre una ficha HTML (`<Html>` drei) con lo que Pablo APRENDIO
   alli (derivado de sus `achievements` + `skills` reales de
   `@portfolio/content`, texto real e indexable).
3. **Objeto de RETOS** — el otro objeto (si aprendizajes es cuaderno, retos es
   pizarra, o viceversa) con los DESAFIOS/problemas que enfrento (derivado del
   `summary` + `responsibilities` reales: el estado inicial, lo que habia que
   resolver).
4. **Guiños de la solucion** — 1-2 props que representan lo que Pablo construyo.
5. **DOS puertas**:
   - La **puerta principal** -> avanza a la siguiente empresa (bidireccional).
   - La **puerta-portal al pasado** (oculta/secundaria) -> lleva a una
     mini-escena del **"antes"** (el caos manual que su solucion elimino).
     Entras, ves el desastre previo, y regresas. Es el ANTES/DESPUES que
     pediste, uno por sala.

> **Retos y aprendizajes** son data-driven: se derivan de los campos reales del
> CV (`summary`/`responsibilities` -> retos; `achievements`/`skills` ->
> aprendizajes). Si se quiere precision editorial, se agregan campos
> `challenges`/`learnings` al schema de `experiences` mas adelante; por ahora
> se derivan de lo existente (ver [detalle de fuentes](#fuente-de-retos-y-aprendizajes)).

## Mapa de salas (9 salas: aula + 7 empresas, Destacame en 3)

Columnas: **Sala · Empresa · Ambiente (después) · Portal al pasado (antes) ·
Retos + Aprendizajes (cuaderno/pizarra) · Guiño de la solucion**.

### Sala 0 — Aula / Universidad (inicios + academico 2015)

- **Empresa/etapa**: contexto academico (proyecto academico IAI + asesoria de
  proyectos de grado, 2015). Punto de partida.
- **Ambiente (después)**: aula/laboratorio de computacion universitario:
  pupitres, pizarra con diagramas, PCs de escritorio conectados en red local,
  planos de obra sobre una mesa. NPCs: estudiantes, un par de equipos de tesis.
- **Portal al pasado (antes)**: un rincon con **dos proyectos de grado
  bloqueados** — pilas de papeles desordenados, un pizarron tachado, dos
  equipos frustrados; codigo roto en una pantalla. El "meses sin terminar".
- **RETOS** (pizarra): "Reencaminar 2 proyectos de grado que 2 equipos no
  lograron terminar en meses; liderar un equipo pequeño; definir la
  arquitectura de un sistema de gestion de obras".
- **APRENDIZAJES** (cuaderno): "Reencamine ambos en ~1 semana; capacite a ~6
  estudiantes para sostener su solucion; diseñe una arquitectura cliente-
  servidor sobre red local; documentacion tecnica y diagnostico".
- **Guiño**: pizarra con un **diagrama cliente-servidor** + un plan de rescate
  de 1 semana; dos proyectos pasando de "bloqueado" (rojo) a "listo" (verde).

### Sala 1 — CORPOELEC (central electrica estatal, VE · intern 2013)

- **Ambiente (después)**: sala de control de subestacion + almacen: **torres de
  alta tension** por la ventana, transformador, tablero de medidores, casco
  amarillo, aisladores ceramicos, **cajas de equipos con etiquetas de
  inventario**. NPCs: tecnicos con casco. Paleta: gris industrial + rojo-naranja
  CORPOELEC + amarillo seguridad.
- **Portal al pasado (antes)**: un archivo con **planillas de papel dispersas y
  duplicadas** en 3 escritorios distintos; un tecnico buscando un equipo minutos
  entre carpetas; registros desincronizados entre sedes.
- **RETOS** (pizarra): "Registrar activos electricos dispersos en planillas de
  papel duplicadas; funcionar OFFLINE en sedes con conectividad intermitente;
  levantar requerimientos con personal operativo en campo".
- **APRENDIZAJES** (cuaderno): "Sistema de inventario (PHP+jQuery) desplegado
  OFFLINE; localizacion de un equipo de minutos a inmediata; centralice 3 sedes
  en una BD comun; CRUD, sistema offline, gestion de activos".
- **Guiño**: monitor con **tabla/grid jQuery de inventario** + badge **"OFFLINE"**;
  **mapa de Venezuela con Yaracuy, Carabobo y Lara** resaltados y pines de sede.

### Sala 2 — IPASME (salud / prevision social docente, VE · junior 2014)

- **Ambiente (después)**: consultorio + archivo clinico DIGITALIZADO: camilla,
  escritorio con tensiometro/estetoscopio, sillas de sala de espera, mueble de
  farmacia, **un monitor con la historia clinica en pantalla**. NPCs: personal
  medico, un paciente-docente. Paleta: blanco clinico + azul institucional +
  verde menta + manila.
- **Portal al pasado (antes)**: el **archivo de carpetas manila en papel** hasta
  el techo, alguien buscando una historia clinica minutos entre estantes, fichas
  traspapeladas. El "registro en papel".
- **RETOS** (pizarra): "Reemplazar el registro en papel de historias medicas;
  manejar datos sensibles de salud con control de acceso; alinear el sistema con
  el flujo real de atencion medica".
- **APRENDIZAJES** (cuaderno): "Sistema digital de historias medicas (Java,
  escritorio); busqueda de historia de minutos a inmediata; POO y CRUD
  consistentes; comunicacion tecnica y levantamiento con personal de salud".
- **Guiño**: **carpetas de papel transformandose en pantallas** (folder ->
  pixelado -> tablet con ficha de paciente); badge **"Digitalizado"**.

### Sala 3 — Cofasa (laboratorio farmaceutico, VE · mid 2017-18)

- **Ambiente (después)**: planta farmaceutica: **linea de envasado (blisters)**,
  maquina de ampollas (MIOVIT), tanque de mezcla inox, batas blancas, mesa QC,
  **torre andon roja/amarilla/verde**, un monitor con el dashboard de produccion.
  NPCs: operarios con cofia. Paleta: blanco/gris sala limpia + azul Cofasa;
  rojo/verde SOLO para el andon.
- **Portal al pasado (antes)**: un supervisor anotando a mano en **planillas de
  paradas de maquina**, un reloj y una libreta; horas de consolidacion manual;
  nadie sabe por que se detiene la linea. El "registro manual de paradas".
- **RETOS** (pizarra): "Monitorear la produccion farmaceutica y las paradas de
  maquina, hoy registradas a mano en planillas; transformar datos crudos de
  planta en indicadores; reflejar el proceso real de la planta".
- **APRENDIZAJES** (cuaderno): "Sistema web (jQuery+Laravel) de monitoreo;
  reemplace las planillas por captura digital; reportes de horas a consulta
  directa; di visibilidad por primera vez a las causas de parada; lo sostuve ~2
  años".
- **Guiño**: **torre andon roja encendida** + monitor con el evento **"PARADA"**
  y dashboard de downtime (barras por causa + donut de disponibilidad).

### Sala 4 — Dibal (SaaS POS para restaurantes, PE · senior/tech lead 2018-21)

> Foco (peticion del usuario): el **sistema SaaS POS** con **facturacion
> electronica directa a la API del gobierno (SUNAT)** e **impresoras termicas**.
> NO se enfoca "islas de dev" ni "microfrontends" en esta sala (aunque existan
> en el CV) — la ambientacion es el producto POS en operacion.

- **Ambiente (después)**: un **restaurante funcionando con el POS Dibal**,
  dividido en dos mitades:
  - **Mitad salon / atencion**: mesas, comensales, **mozos con tablet tomando
    pedidos**, terminal POS tactil en la caja, **impresora termica escupiendo la
    boleta**, cajon de dinero, un **comprobante con sello "facturacion
    electronica / SUNAT"** flotando (envio directo a la API del gobierno).
  - **Mitad cocina**: cocineros, **pantallas KDS en la cocina recibiendo las
    comandas** que los mozos envian desde las tablets (remesas de pedidos en
    tiempo real), tickets de cocina imprimiendose.
  - NPCs: mozos, comensales, cocineros. Paleta: navy + teal Dibal + blanco.
- **Portal al pasado (antes)**: el **sistema manual desastroso** — comandas en
  papelitos que se pierden entre salon y cocina, un mozo gritando el pedido, la
  cocina confundida, boletas llenadas a mano, sin facturacion electronica, caos.
- **RETOS** (pizarra): "Construir desde cero un sistema POS multi-restaurante;
  integrar facturacion electronica con la API del gobierno; conectar salon y
  cocina (comandas mozo->KDS) sin errores; ser el primer y unico developer".
- **APRENDIZAJES** (cuaderno): "Plataforma POS de prototipo a produccion usada
  por varios restaurantes; facturacion electronica directa; e-commerce en Vue;
  despliegue AWS (EC2/RDS/S3/AutoScaling/Load Balancer); estandares de trabajo".
- **Guiño**: el **flujo mozo (tablet) -> KDS (pantalla de cocina)** animado con
  una comanda viajando; la **boleta termica** saliendo + el sello SUNAT.

### Sala 5 — GoodMeal (food-tech anti-desperdicio, CL · mid 2021)

- **Ambiente (después)**: un mundo **limpio, cero desperdicio**: todo el
  excedente de cafeterias se **rescata y empaca en "Good Bags" kraft** antes de
  botarse; estantes ordenados de comida rescatada, smartphone gigante con la app
  (precio tachado -> rebajado), pin de geolocalizacion, contador de impacto
  (comidas rescatadas / CO2 evitado), plantas/brotes (planeta salvado). NPCs:
  staff empacando bolsitas, un cliente feliz recogiendo. Paleta: blanco + **teal
  GoodMeal** + kraft + comida calida.
- **Portal al pasado (antes)**: la **comida desperdiciandose** — bandejas de
  pan/pizza/donas yendo a la basura al cierre, bolsas de residuos, un local
  botando excedente comestible. El "1/3 de la comida se desperdicia".
- **RETOS** (pizarra): "Modernizar un frontend heredado a Vue 3 sin frenar el
  producto; sostener el flujo de pagos de una app de pedidos; entregar bajo
  plazos ajustados de startup con Scrum".
- **APRENDIZAJES** (cuaderno): "Lidere la migracion del frontend a Vue 3 (UX +
  mantenibilidad); reforce el flujo de pagos; reduje bugs recurrentes con un
  stack mas predecible; aporte a las practicas de Scrum del equipo".
- **Guiño**: **app vieja desvaneciendose detras de la UI Vue 3 nitida**; **logo
  de Vue** flotando sobre el smartphone (su verde conversa con el teal de marca).

### Sala 6 — Destacame Frontend (fintech, CL · senior 2021-22)

- **Ambiente (después)**: oficina fintech; pantallas con **interfaces modernas
  Vue/Nuxt** de los productos: el **dashboard de score** (gauge 459-760
  verde->rojo) y flujos tipo **PagaloAqui** (pagar deudas con entidades chilenas:
  **Santander, Scotiabank, Líder**) — logos de esos bancos en las cards de pago.
  Tarjeta prepago azul, editor con `<script setup>` Vue. Paleta: **azul
  `#0052CC`** + blanco + verde "aprobado" + coral "mora". Un mapa: **Chile**.
- **Portal al pasado (antes)**: las **interfaces antiguas** — UIs desactualizadas,
  formularios feos, un stack legacy lento, componentes heredados con deuda
  tecnica. El "antes de migrar".
- **RETOS** (pizarra): "Migrar interfaces heredadas a Vue/Nuxt reduciendo deuda
  tecnica; construir flujos de pago de deudas con bancos (Santander, Scotiabank,
  Líder) manejando datos financieros sensibles; crecer de frontend a full-stack".
- **APRENDIZAJES** (cuaderno): "Interfaces fintech en uso real en Chile;
  eficiencia y calidad del frontend con nuevos estandares; refactor de
  componentes heredados; pase a full-stack (Python/Django) en ~8 meses".
- **Guiño**: monitor partido **interfaz vieja -> UI Vue/Nuxt nueva**; card de
  **PagaloAqui** pagando una deuda a un banco (logos Santander/Scotiabank/Líder).

### Sala 7 — Destacame Arquitecto Frontend (fintech, CL+MX · lead 2022-hoy)

- **Ambiente (después)**: sala de arquitectura: pared grande con el **Design
  System** (tokens, componentes) y un **diagrama DDD por modulos**; pantallas
  mostrando el **codigo base reutilizable que se forkea por entidad financiera**
  (Santander, Scotiabank, Líder... cada una un fork). Setup de 3-4 monitores.
  NPCs: equipo consultando el DS. Paleta: azul `#0052CC`, sofisticada.
- **Portal al pasado (antes)**: **codigo duplicado por cada banco** — N proyectos
  frontend copiados y pegados, inconsistencias visuales entre entidades,
  reescribir todo desde cero para cada integracion. El "antes del DS + fork".
- **RETOS** (pizarra): "Dejar de reescribir el frontend por cada entidad
  financiera; establecer estandares y patrones compartidos entre equipos;
  arquitectura frontend reutilizable y consistente".
- **APRENDIZAJES** (cuaderno): "Arquitectura de **Design System + DDD (modules)**
  que hoy es el **codigo base que se forkea para cualquier entidad financiera**;
  estandares compartidos; equipos trabajando en paralelo con menor acoplamiento".
- **Guiño**: el **codigo base central** con flechas de **fork** hacia logos de
  Santander/Scotiabank/Líder (mismo DS, N entidades); un tablero de tokens del
  Design System.

### Sala 8 — Destacame Fullstack & Líder (LA CIMA, CL+MX · lead 2022-hoy)

- **Empresa/etapa**: es la faceta fullstack + liderazgo del rol actual (misma
  experiencia `destacame-architect`, zona distinta): **arquitecturas de backend
  en Django + microservicios**, **implementaciones completas para entidades
  financieras trabajando directo con sus equipos tech**, **liderazgo de
  equipos**, **vibe coding**. La CIMA de la carrera.
- **Ambiente (después)**: **war room / control tower** premium: ultrawide +
  monitores verticales, luz de acento azul dramatica; pared con **diagrama de
  microservicios Django** + **orquestacion Chile + Mexico** (dos mapas
  conectados a un nodo central); un panel de observabilidad multi-servicio; una
  mesa de reunion (lidera equipos); un monitor con **vibe coding / IA-assisted**
  en accion. NPCs: equipo en reunion con Pablo liderando. Paleta: azul `#0052CC`
  dominante, premium.
- **Portal al pasado (antes)**: procesos **manuales y aislados** — un admin de
  campañas hecho a mano que tomaba horas, servicios sin orquestar, un solo pais,
  trabajo en silos. El "antes de la plataforma".
- **RETOS** (pizarra): "Orquestar productos fintech para dos paises (Chile +
  Mexico); construir microservicios backend (Django) e integrarlos con el
  frontend; liderar equipos a traves de reorganizaciones; automatizar procesos
  manuales; adoptar IA en el flujo de forma productiva y segura".
- **APRENDIZAJES** (cuaderno): "Arquitecturas backend Django + microservicios;
  implementaciones completas directo con los equipos tech de las entidades
  financieras; lidere equipos de 4-6; admin de campañas de horas a minutos;
  incorpore vibe coding / desarrollo asistido por IA al equipo".
- **Guiño**: el **nodo central orquestando Chile + Mexico**; un **grafo de
  microservicios Django**; el monitor de **vibe coding**; holograma **"plataforma"**.
- **PUERTA FINAL "Próximamente"**: al fondo de esta sala, una **puerta extra
  cerrada con un cartel "Próximamente / Ideas futuras"** (peticion del usuario)
  — insinua lo que viene, invita a volver. No lleva a ninguna sala aun.

> **Total: 9 salas** (aula + CORPOELEC + IPASME + Cofasa + Dibal + GoodMeal +
> Destacame Frontend + Destacame Arquitecto + Destacame Fullstack/Líder) +
> **9 portales al pasado** (uno por sala) + la **puerta "Próximamente"** al
> final. Es data-driven desde `@portfolio/content`: agregar una experiencia =
> agregar una sala. Las 3 salas Destacame provienen de sus 2 experiencias del
> CV (la etapa lead se despliega en arquitecto-FE + fullstack-líder por su
> riqueza); si se quiere acortar, se fusionan en 2 o 1 sala con zonas.

Cada sala materializa el **eje seniority**: crecen en tamaño, luz, detalle y
"estatus" del aula humilde (2013) al war room de la CIMA (hoy). El pais del
cliente es un guiño (banderin/mapa), no la estructura.

### Fuente de retos y aprendizajes

Se derivan de los campos REALES de cada experiencia en `@portfolio/content`
(los mismos que alimentan las paginas `/experience/<slug>/` del CV):

- **RETOS** <- `summary` + `responsibilities` (el problema/contexto: que habia
  que resolver, el estado inicial).
- **APRENDIZAJES** <- `achievements` + `skillsTechnical`/`skillsSoft` (lo que
  logro y las capacidades que gano).

Opcional a futuro: agregar campos explicitos `challenges` y `learnings` al
schema de `experiences` para control editorial fino (una sola fuente que
alimenta el 3D y el CV 2D). Por ahora se derivan de lo existente.

## Los "logros" dentro de cada sala (el cuaderno/pizarra)

El objeto focal de logros que pediste — un **cuaderno** o una **pizarra** segun
la sala — es data-driven:

- **Al acercarse** (proximidad + prompt "Leer" / tap), se abre la **ficha HTML**
  (`<Html>` drei) con los **achievements reales** de esa experiencia desde
  `@portfolio/content` (texto real, i18n es/en, indexable — no pixeles).
- El **tipo de objeto** encaja con el rubro: cuaderno de campo (CORPOELEC),
  ficha clinica (IPASME), pizarra de paradas (Cofasa), organigrama en pizarra
  (Dibal), monitor de dev (GoodMeal/Destacame-front), pizarra de arquitectura
  (Destacame-arquitecto).
- Ademas: los **certificados** (11) pueden ser cuadros inspeccionables
  repartidos, y cada **proyecto** (ERP, fintech, microservicios) una
  maqueta/pantalla que abre su case study.

## Navegacion (decisiones del usuario)

- **Desktop**: WASD/flechas para caminar + mouse-look (`PointerLockControls`).
  Acercarse a una puerta + tecla/click -> se abre (animacion) -> entras.
- **Movil**: joystick tactil (nipplejs) para caminar + arrastre para mirar +
  tap en la puerta para abrir. Es el caso mas delicado (ver fallback abajo).
- **Ida y vuelta**: las puertas son bidireccionales; puedes volver a la sala
  anterior. Indicador de "sala N de 9".
- **Menu de teletransporte (decision del usuario)**: un **mapa/menu de salas**
  (tecla `M` / boton) permite **saltar directo a cualquier empresa** sin caminar
  todo el recorrido. Critico para un reclutador con prisa que quiere ir directo
  a Destacame (la CIMA). El teletransporte hace fade-out -> carga la sala ->
  fade-in (mismo mecanismo de carga que las puertas). El recorrido caminando
  sigue disponible para quien quiere la inmersion completa.
- **Apertura de puerta**: animacion de bisagra + carga de la siguiente sala
  mientras la puerta se abre (esconde el loading — truco clasico de juegos, el
  "pasillo de carga").

## Micro-interacciones simbolicas por sala (decision del usuario)

Ademas de caminar/mirar/leer, cada sala tiene **hasta 3 micro-acciones
tematicas** (una sola pulsacion, sin gamificacion ni coleccionables): pequeños
gestos que dejan al visitante "tocar" el antes/despues con sus manos. Refuerzan
la narrativa sin distraer del mensaje profesional. Propuestas por sala:

| Sala | Micro-interacciones (hasta 3, simbolicas) |
|------|-------------------------------------------|
| 0 Aula | Encender un PC en red · pasar un proyecto de "bloqueado" a "listo" · abrir el cuaderno de logros |
| 1 CORPOELEC | Accionar el **tablero de control** (luces verde/rojo) · buscar un equipo en la tabla (papel lento vs sistema inmediato) · alternar badge OFFLINE |
| 2 IPASME | **Digitalizar una carpeta** (papel -> pantalla con un gesto) · buscar una historia clinica · ver el archivo vaciarse |
| 3 Cofasa | Disparar una **parada de maquina** (andon roja) · ver el dashboard registrar la causa · alternar registro papel vs digital |
| 4 Dibal | **Tomar un pedido** en la tablet del mozo · verlo llegar al **KDS de cocina** · imprimir la boleta (sello SUNAT) |
| 5 GoodMeal | **Empacar una Good Bag** (rescatar comida antes del tacho) · ver subir el contador de impacto · alternar "desperdicio vs rescate" |
| 6 Destacame FE | **Migrar una pantalla** (vieja -> Vue/Nuxt) · pagar una deuda via PagaloAqui (elegir banco) · toggle antes/despues de UI |
| 7 Destacame Arq | **Forkear el codigo base** hacia una entidad (Santander/Scotiabank/Líder) · ver el Design System aplicarse · toggle codigo duplicado vs DS |
| 8 CIMA | **Orquestar** un servicio entre Chile y Mexico · lanzar el admin de campañas (horas -> minutos) · abrir la puerta "Próximamente" |

> Regla: la micro-interaccion es OPCIONAL para el visitante (el recorrido
> funciona solo caminando/leyendo); es un plus, no un gate. Cada una es una
> accion con una animacion — barata de implementar, alto retorno narrativo.

## Mejoras acordadas (creativas)

Decisiones del usuario para elevar la experiencia:

1. **Pasillo/hub que conecta las salas** — entre sala y sala hay un breve
   pasillo neutro con la "huella" de Pablo (su color/logo) y un **mini-timeline
   en el piso** con el año de la etapa. Da continuidad entre rubros dispares,
   ubica al visitante ("vas por 2015") y sirve de **pasillo de carga** (oculta
   el `<Suspense>` de la siguiente sala). Es el pegamento narrativo del recorrido.
2. **Portal al pasado con estetica retro + glitch** — cruzar la puerta-portal
   hace una **transicion glitch** y el "antes" se renderiza en **sepia/
   desaturado con grano** (shader/post-fx, barato). Comunica "pasado" al
   instante y se ve profesional. Al volver al presente, la escena recupera color.
3. **Audio ambiente por sala** — cada rubro con su sonido sutil (zumbido
   electrico en CORPOELEC, cocina + tickets en Dibal, teclas/notificaciones en
   fintech, murmullo de consultorio en IPASME). Sube mucho la inmersion.
   Requiere clips CC0 curados + **respeta mute del sistema** y un toggle de
   sonido (audio SIEMPRE opt-in, arranca en silencio hasta gesto del usuario —
   politica de autoplay de browsers).
4. **CTA de contacto en la CIMA** — en la sala 8 (junto a la puerta
   "Próximamente"), un objeto claro (telefono/tarjeta/holograma) que abre el
   **contacto + CV-PDF + LinkedIn**. Convierte la experiencia en accion para el
   reclutador — es el objetivo de negocio del portfolio.
5. **Modo "tour guiado" auto-reproducible** — un boton "Tour automatico" que
   recorre las 9 salas solo (**camara sobre riel** `CatmullRomCurve3`, el mismo
   patron de la Propuesta B scroll-journey) mientras aparecen los textos de cada
   etapa. Sirve
   para: (a) quien no quiere caminar, (b) **el fallback movil elegante** (en vez
   de joystick, el movil corre el tour guiado por defecto con opcion de tomar el
   control), (c) un preview rapido de toda la carrera.

## Mecanica tecnica

- **Colisiones**: salas cerradas = colisionadores AABB/box triviales por pared
  (lo mismo que D-museo). **Cero navmesh, cero heightmap** -> es el POV
  free-walk mas barato de implementar. Puerta = trigger de proximidad + estado.
- **Carga por sala (clave)**: cada habitacion es un chunk `<Suspense>` que se
  carga al abrir su puerta (no todas de golpe -> respeta el limite de contexto
  WebGL de iOS). Precargar la sala siguiente al entrar en la actual. La
  animacion de puerta cubre el tiempo de carga.
- **Physics**: opcional. Un character controller simple (Rapier KCC) da un
  caminar solido; pero para salas planas basta un controlador de camara con
  colision de cajas (sin engine de physics). Empezar sin Rapier.
- **Estado**: Zustand (`currentRoom`, `isDoorOpen`, `activeAchievement`,
  `isFichaOpen`); deshabilitar controles mientras una ficha esta abierta.
- **Interaccion logro**: raycast desde el centro de camara -> hover resalta el
  objeto -> click abre la ficha `<Html>` (DOM real, indexable, i18n).
- **Datos**: cada sala + sus logros se generan desde `@portfolio/content`
  (experiences + projects + certificates + awards). Agregar una experiencia =
  agregar una sala (data-driven).

## Estetica y como se espera que se vea (detalle tecnico)

**Direccion**: **low-poly estilizado por epoca**, construido en su mayoria de
forma **PROCEDURAL** (sin depender de assets externos), siguiendo el enfoque
del prompt de Sidi Bou Said 3D (single-file Three.js, texturas Canvas,
instancing, shaders) — ver [../../progress/explore_sidi_bou_said_prompt.md](../../progress/explore_sidi_bou_said_prompt.md).
Esto baja el costo de assets (el punto mas caro) y encaja con vibe-coding con
Fable 5, que genera bien escenas Three.js completas.

### Referencia visual concreta (el "target look")

Cada sala se ve como un **diorama low-poly habitable**: geometria limpia de
pocas caras, paleta acotada del rubro (2-4 colores + acentos), **iluminacion
que da el mood** (no texturas fotorealistas). El referente de calidad/tecnica
es un interior tipo el Sidi Bou Said del prompt pero en interior y estilizado:
formas simples bien compuestas + luz + un par de props "firma" que identifican
el rubro al instante. NO es realismo AAA; es un mundo de juego indie pulido
(piensa Monument Valley / Alto's Odyssey en 3D interior).

### Como se construye cada sala (procedural-first, hibrido)

| Elemento | Tecnica |
|----------|---------|
| **Estructura de sala** (paredes, piso, techo, puertas) | primitivas `BoxGeometry`/`PlaneGeometry` compuestas + material plano. Cero .glb. |
| **Texturas** (plaster, metal, madera, baldosa) | **generadas con Canvas API en runtime** (patron + ruido dibujado por codigo), NO archivos. Barato, sin peso de red, sin limite de 25 MiB de Cloudflare. |
| **Props "firma" del rubro** (transformador, camilla, terminal POS, torre andon, servidor) | **compuestos de primitivas** (cylinder + box + plane) + material. Un transformador = caja gris + aletas + bujes cilindricos. Reproducible por codigo. |
| **Elementos repetidos** (sillas de espera, blisters, mesas del restaurante, monitores, cajas de inventario) | **`InstancedMesh`** (una geometria, N instancias) -> 60 FPS, pocas draw calls. Es la clave de performance del prompt. |
| **NPCs humanos** (unico asset externo) | assets **CC0 ya animados** (Quaternius/Mixamo, idle/walk). Es el unico lugar donde un .glb vale la pena (lo organico es caro de hacer procedural). |
| **Iluminacion (la identidad de cada sala)** | `HemisphereLight` (cielo/suelo) + `DirectionalLight` con `PCFSoftShadowMap`. El MOOD por rubro se logra con luz casi gratis: frio industrial (CORPOELEC), clinico neutro (IPASME), calido startup (GoodMeal), premium azul dramatico (CIMA). |
| **Tone mapping** | `ACESFilmicToneMapping` para un look cinematografico coherente entre salas. |
| **Efectos (guiños, portal, transiciones)** | **shaders GLSL**: el glitch + sepia del portal al pasado, el brillo de una pantalla, el "digitalizando" de IPASME. Fable 5 genera GLSL comun con fiabilidad. |

### El eje seniority, con LUZ y densidad (casi gratis)

La progresion intern -> arquitecto NO exige mas assets: se comunica con
(a) **iluminacion** (de austera/plana en el aula a premium/dramatica en la
CIMA), (b) **densidad de props instanciados** (pocos objetos al inicio, sala
rica y compleja en la CIMA), (c) **tamaño de sala** (crece). Todo procedural.

### Dos vias de assets (decision de produccion)

- **Procedural-first (recomendada)**: arquitectura + mobiliario + props firma +
  texturas + efectos por CODIGO; solo los **NPCs** son assets CC0 animados. Baja
  el costo, coherencia total, ideal para Fable 5. Es el enfoque del prompt de
  Sidi Bou Said llevado a interiores.
- **Hibrida con mas CC0**: si algun prop organico (una planta, un vehiculo)
  sale mejor como asset, se usa CC0 puntual (Poly Pizza/Kenney) pasado por
  Draco/KTX2. Excepcion, no regla.

> Implicacion: la estimacion de esfuerzo del plan asume procedural-first. Si se
> fuera 100% asset-based (Blender por sala) el costo subiria; el enfoque
> procedural es lo que mantiene el MVP en 4-6 semanas.

## Fallback movil (3 tiers)

- **Full** (desktop): recorrido completo con free-walk + puertas + micro-
  interacciones + menu de teletransporte.
- **Reduced** (movil con WebGL): por defecto corre el **modo "tour guiado"**
  (camara sobre riel que recorre las salas sola, decision del usuario) — evita
  el joystick fragil; el visitante puede tomar el control (walk simple) si
  quiere. Menos props, sin sombras dinamicas. El menu de teletransporte permite
  saltar a una sala concreta.
- **Static** (sin WebGL / HW debil / `prefers-reduced-motion`): las habitaciones
  se vuelven un **storytelling 2D** — una seccion por sala, con la imagen
  representativa de esa epoca + los retos y aprendizajes en texto. Este ES el
  fallback legible + SEO/ATS. La metafora "habitaciones" degrada naturalmente a
  "capitulos".

## Referencias reales (del research + genero)

- **Henry Heffernan** (henryheffernan.com) — cuarto 3D Windows 98 explorable con
  objetos interactivos (jugar Mario, ver proyectos). El referente directo del
  sub-genero "3D room" con objetos-logro. Degrada a desktop-only en la practica.
- **Virtual art gallery** (github.com/rahel-yab/Virtual-art-gallery) — OPEN
  SOURCE, first-person WASD, colisiones de caja triviales multi-sala. Molde
  tecnico directo.
- **WoraWork** (worawork.vercel.app) — personaje por espacios acogedores
  (casa+jardin), estetica low-poly calida = molde para "habitacion habitable".
- Genero juego (inspiracion narrativa): Gone Home, The Beginner's Guide,
  Superliminal — "explorar espacios que cuentan una historia".

Tablas + URLs en [../../progress/explore_pov3d_world.md](../../progress/explore_pov3d_world.md).

## Esfuerzo (revisado por la ambientacion por-rubro)

Ambientar cada sala segun el rubro real (9 sets distintos: aula, central
electrica, consultorio, planta farma, restaurante+POS, food-tech, 3x fintech) +
NPCs + **un portal-al-pasado (mini-escena "antes") por sala** sube el costo de
assets frente a un museo neutro. El "antes" reusa muchos props del "despues"
(desordenados/rotos), asi que no dobla el costo, pero suma. Estimacion:

- **MVP (decision del usuario: la primera + la CIMA, arcos extremos)** — 2 salas
  ambientadas: **CORPOELEC** (intern, inicios) + **Destacame Fullstack/Líder**
  (CIMA), cada una con su portal al pasado + retos/aprendizajes + 1-2
  micro-interacciones, free-walk con colision de cajas (sin physics engine),
  cuaderno+pizarra con raycast, puertas con animacion+carga, y el **menu de
  teletransporte** entre las dos. Valida el loop completo (caminar -> leer ->
  micro-interaccion -> portal al pasado -> teletransporte) en las 2 salas que
  demuestran el salto intern->líder. **4-6 semanas** part-time. Riesgo medio.
  - (Opcional en el MVP: sumar el Aula como sala 0 de arranque si se quiere el
    "inicio" narrativo — +1 semana.)
- **Completo** (las 9 salas + 9 portales al pasado + NPCs animados + retos y
  aprendizajes por sala + micro-interacciones + guiños + puerta "Próximamente" +
  menu de teletransporte + physics KCC + audio + movil solido): **12-18
  semanas**. Riesgo medio-alto.
- **Lo caro**: (1) art direction + assets POR RUBRO — 9 sets tematicos, es el
  costo dominante; mitigar con packs CC0 de interiores (Kenney/Quaternius/Poly
  Pizza) + reutilizar mobiliario base y solo variar los props "firma" de cada
  rubro; (2) **NPCs** low-poly con idle/walk (Quaternius/Mixamo tienen
  personajes CC0 animados — usar esos, NO riggear propios); (3) navegacion
  movil + QA cross-device; (4) calibrar el free-walk con colision. Las
  micro-interacciones son baratas (1 accion + 1 animacion c/u).
- **Estrategia recomendada**: MVP con la primera + la CIMA (validar el loop y
  el salto narrativo), luego agregar salas incrementalmente por impacto (las 3
  Destacame + las mas visuales), todas data-driven.

## Donde encaja vs las otras propuestas

- Es el **punto medio** entre D (museo, mas barato pero neutro) y G (mundo
  libre, mas caro y disperso): POV inmersivo real, dirigido, con narrativa
  fuerte por sala, sin la complejidad de un mundo abierto.
- **Mejor que G para contar una carrera**: la secuencia de salas IMPONE el
  orden narrativo (intern -> arquitecto) que un mundo abierto diluye.
- Comparte 100% la [arquitectura comun](04-arquitectura-comun.md): app
  `apps/journey`, datos de `@portfolio/content`, 3 tiers de fallback.

## Recomendacion

Es la **propuesta #1 del plan** (decision del usuario): el enfoque tipo juego
inmersivo que describio. Mejor que G (mundo abierto) o D (museo) para esto: POV
caminable real + narrativa dirigida por tu progresion + costo acotado (salas
box) + fallback 2D limpio (capitulos). Orden: **A es la #1**; B (scroll) es la
alternativa "menor riesgo + posible CV principal indexable". Se pueden construir
ambas en `apps/journey` (A como `/world` inmersivo, B como `/` scroll).
