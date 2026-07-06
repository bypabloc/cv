# ESTADO — progreso del plan journey-salas-estandar

> Cola de trabajo persistente entre sesiones. Cada sesion que crea una sala
> de Etapa 2 ACTUALIZA este archivo al terminar (marca la sala HECHA + commit
> sha). Se lee al RETOMAR (ver "Protocolo de retoma" en [README](README.md)).
>
> Rama unica: `feature/journey-salas-estandar` (sin merge hasta cerrar las 7).

## ETAPA 1 — estandarizacion + Aula (stop gate)

| Commit | Que | Estado |
| --- | --- | --- |
| C2 | infra RoomId->8 + rename cima->destacame (stubs) | HECHO `9163b0cb` |
| C3 | paleta paredes-blancas (themes.ts) | HECHO `5405fee8` |
| C4 | helpers canon (officeLayout/npcCoworkers/wallArt/softwareShowcase) + UI action showcase | HECHO `3db5f9dc` |
| C5 | partir pasados en rooms/past/<id>.ts + dispatcher | HECHO `8acd4915` |
| C6 | Aula refactor (prueba del canon, AC-9) | HECHO `af82a772` |
| — | **STOP GATE**: verificar Etapa 1, commit, NO merge, detener | **ALCANZADO 2026-07-05** |

> ETAPA 1 HECHA (2026-07-05). Verificada: typecheck + lint + build verdes,
> smoke con browser (8 salas montan via teleport, showcase abre/cicla/cierra
> end-to-end sobre un arnes temporal en el stub de ipasme, luego revertido).
> Decisiones de ejecucion: destacame quedo como STUB VACIO (literal del
> plan); los stubs llevan placeholder "en construccion" (cartel + barrera
> con el acento). Las salas de Etapa 2 se ejecutan en sesiones separadas.

## ETAPA 2 — salas 1 a 1 (orden cronologico sugerido, se puede saltar)

| Orden | Sala | Informe | Estado | Commit |
| --- | --- | --- | --- | --- |
| 1 | `corpoelec` | [08-sala-corpoelec.md](08-sala-corpoelec.md) | HECHO | `46f28551` |
| 2 | `ipasme` | [09-sala-ipasme.md](09-sala-ipasme.md) | HECHO | `d22c3988` |
| 3 | `cofasa` | [10-sala-cofasa.md](10-sala-cofasa.md) | HECHO | `7eecf589` |
| 4 | `dibal` | [11-sala-dibal.md](11-sala-dibal.md) | HECHO | `b6059f33` |
| 5 | `goodmeal` | [12-sala-goodmeal.md](12-sala-goodmeal.md) | HECHO | `2e3459fa` |
| 6 | `destacame` | [13-sala-destacame.md](13-sala-destacame.md) | HECHO | `4d8dc7d2` |
| 7 | `futuro` | [14-sala-futuro.md](14-sala-futuro.md) | HECHO | `a50f073d` |

Estados validos: `PENDIENTE` · `EN CURSO` · `HECHO`.

> **ETAPA 2 COMPLETA (2026-07-05)**: las 7 salas estan HECHAS. Antes del
> CIERRE queda la **ETAPA 2b** (salas 2015, tabla de abajo).

## ETAPA 2b — salas 2015 (ampliacion 2026-07-05, insertadas ipasme -> cofasa)

| Orden | Paso | Informe | Estado | Commit |
| --- | --- | --- | --- | --- |
| 2b.0 | infra (RoomId->10 + stubs + aula univ. pura + CV) | [15-infra-salas-2015.md](15-infra-salas-2015.md) | HECHO | `8d051761` + `9d2e227f` |
| 2b.1 | sala `iai` (index 3 del recorrido) | [16-sala-iai.md](16-sala-iai.md) | HECHO | `5ddda72d` |
| 2b.2 | sala `asesoria` (index 4 del recorrido) | [17-sala-asesoria.md](17-sala-asesoria.md) | HECHO | `0b128c7b` |

> El paso 2b.0 es PREREQUISITO de 2b.1 y 2b.2. Tras la insercion, los
> indices de las salas posteriores se corren automaticamente (cofasa 5,
> dibal 6, goodmeal 7, destacame 8, futuro 9): los ids `talk-N-*`/
> `showcase-N`/`portal-N` derivan de `room.index` en runtime.

## CIERRE (tras TODAS las salas, incluidas las 2015)

| Commit | Que | Estado |
| --- | --- | --- |
| C14 | audio ambiente de las salas nuevas | HECHO `62c0c2c2` |
| C15 | perf <100 draw calls/sala | HECHO `3d41e07c` |
| C16 | rule del estandar (.claude/rules/journey-rooms.md) | PENDIENTE |
| C17 | verificacion E2E + `git rm -r` la carpeta del plan + merge unico a dev | PENDIENTE |

## Bitacora (append al terminar cada sala)

<!-- Formato: [YYYY-MM-DD] sala <id> HECHA en commit <sha> — notas -->

- [2026-07-06] CIERRE C15 (perf <100 draw calls) HECHO en commit
  `3d41e07c` — medicion con `tmp/journey-smoke-perf.py` (renderer.info
  via `__journeyDebug`, solo DEV; max sobre ventana de 4 s en el spawn
  de cada sala, presente Y pasado, swiftshader headless). ANTES solo
  destacame presente excedia (104) y cofasa rozaba (99); el resto ya
  cumplia. Tres optimizaciones: (1) SISTEMICA en character.ts — los 6
  pinchos del pelo `spiky` eran 6 meshes = 6 draw calls por NPC; ahora
  se fusionan en UNA geometry con la pose horneada por matrix (-5 por
  NPC spiky, beneficia a toda sala con uno); (2) destacame —
  `noOutline` en props planos/oscuros cuyo hull no aportaba trazo
  (tarjeta bancaria, sello WebPay, tarjeta prepago, panel PROXIMAMENTE,
  pedestal del CTA); (3) cofasa — el tablero de la banda de ampollas y
  la mesa de blisteres se fusionaron en los batches STEEL_DARK/STEEL
  del tanque y la llenadora (-4). Resultado antes -> despues (calls,
  presente): aula 60->60, corpoelec 93->93, ipasme 67->68, iai 86->81,
  asesoria 71->71, cofasa 99->92, dibal 67->67, goodmeal 79->79,
  destacame 104->98, futuro 37->37; pasados todos <=84 (destacame
  pasado 78->73). Las 20 vistas (10 presente + 9 pasado + futuro sin
  pasado) quedan <100 — AC-10 verde. Verificacion visual del pelo
  spiky fusionado en iai y destacame (identico). Los "quads negros"
  del muro trasero (hallazgo de iai) NO se tocaron: son las pizarras
  oscuras del canon vistas desde atras (estetica, no perf; los hulls
  no dominan el presupuesto).

- [2026-07-06] CIERRE C14 (audio ambiente) HECHO en commit `62c0c2c2` —
  decisiones del usuario (AskUserQuestion 2026-07-06, NO reabrir): (1)
  presente = FIRMA POR RUBRO (cada sala 1-2 capas procedurales WebAudio
  sobre room-tone; corpoelec y destacame conservan su perfil previo);
  (2) pasado = SEPIA GLOBAL unificado (aire sordo lowpass + tic-tac de
  reloj a 1 Hz — el reloj es el prop recurrente de los pasados; la firma
  del sistema NO suena). Helpers nuevos en audio.ts: wobbleNoiseVoice
  (murmullo/ventilador con LFO de amplitud) y patternVoice (buffer en
  loop con eventos pre-renderizados — blip ipasme, pulso cofasa,
  tic-tac del pasado — cero scheduling, cero assets). AmbientAudio gana
  el flag past (clave `<room>:past`); audioTarget (ex audioRoomId)
  resuelve sala + pasado desde state.past — onZoneApplied ya disparaba
  en enterPast/exitPast, cero wiring nuevo. prefers-reduced-motion
  cubierto estructuralmente (tier static nunca monta el engine),
  documentado en el docstring del modulo. Smoke browser verde x2
  (tmp/journey-smoke-audio.py): 2 AudioContext running tras el gesto,
  10 salas construyen su perfil via teleport, portal-1/portal-exit-1
  conmutan el sepia, toggle HUD OFF->ON, cero leaks de contexto; unico
  error: el 504 transitorio de vite (gotcha conocido). Ademas en esta
  sesion: eliminado el worktree .claude/worktrees/asesoria + la rama
  temporal feature/journey-sala-asesoria (ya integrados en 0b128c7b;
  ESTADO.md los daba por eliminados pero seguian en disco).

- [2026-07-06] sala `asesoria` HECHA en commit `0b128c7b` — informe 17
  (Etapa 2b.2, index 4 del recorrido, sala 5 de 10; ETAPA 2b COMPLETA:
  las 10 salas existen — solo queda el CIERRE C14-C17). Ejecutada en
  PARALELO con la sesion de iai via WORKTREE (`git worktree add` manual
  desde e1653064 + rama temporal `feature/journey-sala-asesoria`,
  commit original `3e21fca8` cherry-pickeado a la rama del plan cuando
  iai commiteo; git auto-mergeo `rooms/past/index.ts` sin conflicto;
  worktree y rama temporal eliminados tras integrar). Decisiones del
  usuario (AskUserQuestion 2026-07-06, NO reabrir): (1) 5 NPCs presente
  (informe completo): Jhonny Parra y Oriana Castillo (tesistas sentados
  en el officeLayout con codigo PHP), Coromoto Linares (farmacia),
  Maigualida Torres (admision) y la Dra. Xiomara Graterol (directora en
  ronda mostrador->rincon); (2) LAS 3 MICROS: tomar un turno (el ticket
  vuela del mostrador a la sala de espera + el display sube 042->043
  con ring), despachar un medicamento (la caja vuela del estante a la
  mesa, el stock del monitor baja y el minimo alerta en rojo — la
  feature de Coromoto; tras la alerta "llega el pedido" y repone) y
  ENSAYAR LA DEFENSA, la micro firma (E cicla las 5 laminas del
  proyector titulo->problema->arquitectura->demo->conclusiones; al
  completar el ciclo Jhonny y Oriana SALTAN con el cartel "¡ensayo
  redondo!"); (3) sobre de pago SI, CON FICHA (el guiño del primer
  trabajo COBRADO como consultor — abre panel con la historia).
  Presente en dos zonas: INSTITUTO (sala de espera con siluetas +
  display de turnos, mostrador de admision con monitor de afiliados +
  carnet + cruz verde, farmacia con estante + mesa de despacho,
  cartelera de campañas vacunacion/dengue, torre XAMPP "SERVIDOR
  LOCAL" con router y canaleta) y RINCON DE ASESORIA (officeLayout 3
  puestos — 2 encendidos con citas.php/farmacia.php, 1 libre togglable
  —, proyector + pantalla, sobre de pago). wallArt 4 laminas / 2 fichas
  (cartel PROSALUD con la red de 14 municipios + el plan de rescate de
  7 dias — la pieza MUDADA del aula por el informe 15; diagrama web
  local y afiche de la defensa decorativos). Showcase look NAVEGADOR
  2015 (unica sala venezolana web: chrome con pestaña + barra
  192.168.1.10/prosalud/ + navbar verde Bootstrap 2, badge RED LOCAL ·
  XAMPP; 3 demos: turnos, farmacia con alerta de minimos, afiliados con
  buscador por cedula). Pasado sepia con los DOS hilos (decision del
  informe): instituto en papel (sala de espera desbordada con siluetas,
  pincho de papelitos, cuaderno de tachones, archivador manila y
  reloj) mas la mesa de tesis varada (stack trace PHP en rojo, pizarra SIN
  plan con 3 planes tachados y DEFENSA: 15 DIC rodeada en rojo,
  calendario con meses tachados); micro "atender a un afiliado sin el
  sistema" con DOS veredictos (la carpeta aparece a los 9 min... el
  papelito del turno PERDIDO). Nota tecnica: turnoMicro/despachoMicro/
  ensayoMicro extraidas a funciones modulo (limite de complejidad de
  Biome, patron dibal/iai); las carpetas del archivador del pasado van
  en coords LOCALES con pivote para poder animar el temblor
  (mergedBoxes hornea coords absolutas en la geometria). Smoke browser
  verde x2 en el worktree Y x2 tras integrar en la rama del plan (26
  interactables, showcase E/Esc con 3 demos, 5 dialogos, 3 fichas, 3
  micros, laptop toggle, pasado 31-32 interactables con los 3 NPCs del
  arco); unico error de consola: el 504 transitorio de vite (gotcha
  conocido). Nota perf: 5 NPCs + 2 zonas + proyector — medir en C15
  igual que las demas.

- [2026-07-06] sala `iai` HECHA en commit `5ddda72d` — informe 16
  (Etapa 2b.1, index 3 del recorrido, sala 4 de 10) con 4 decisiones
  del usuario (AskUserQuestion 2026-07-05, NO reabrir): (1) 5 NPCs
  presente (informe completo, sin recortar a 4): Keiber Mendoza y
  Marielys Ochoa (tesistas dev sentados en el officeLayout), Ing.
  Gregorio Salcedo (inspector en ronda meson->showcase), Belkis
  Camacaro (analista en su escritorio de sellos) y la Ing. Maritza
  Oropeza (presidenta junto a la valla); (2) 3 NPCs pasado (con Pastor
  Rivas, el maestro de obra nuevo: "hasta que no firmen la valuacion,
  a mi gente no le pagan"); (3) LAS 2 MICROS: recalcular el presupuesto
  (indices BCV -> los PU parpadean y el TOTAL sale al instante + tag
  "antes: 40 APU a mano") y conformar una valuacion (el sello CONFORME
  3D baja y golpea + el avance fisico sube ciclando 68->74->80->86%);
  (4) wallArt con 3 FICHAS (upgrade sobre el informe que decia 2): la
  lamina del APU SUBIO a inspeccionable (ficha de como se arma una
  partida COVENIN) junto a la valla institucional y el diagrama de red;
  el plano de via agricola quedo decorativo. Showcase look Java/Windows
  2015 con badge RED LOCAL (3 demos: presupuesto con Recalcular, hoja
  de APU, valuaciones con curva S). Props firma: la PC-SERVIDOR
  ("SERVIDOR — NO APAGAR", LED parpadeante, cable de red a los
  puestos), meson de planos con plano desplegado y pesas, planoteca,
  valla de la calle 19 con escudo, estante COVENIN/Guia CIV, corcho con
  tabulador, ventilador oscilante (calor de San Felipe). Pasado: meson
  saturado + torres de carpetas por obra + Excel con indices BCV
  vencidos pegados con cinta + telefono descolgado + reloj + PC vieja
  compartida + consolidar el avance a mano (falta la carpeta de la via
  agricola). Nota tecnica: recalcMicro/selloMicro extraidas a funciones
  con selloYAt puro (limite de complejidad de Biome, mismo patron que
  dibal). Smoke browser verde x2 (25 interactables, showcase E/Esc con
  3 demos, 5 dialogos, 3 fichas, 2 micros, laptop toggle, pasado 31
  interactables con Pastor conversable); unico error de consola: el 504
  transitorio de vite (gotcha conocido). Hallazgo visual verificado con
  sala de CONTROL (ipasme girada 180): los "quads negros" junto al muro
  trasero y la columna sobre la puerta aparecen IGUAL en ipasme — son
  artefacto preexistente del canon/shell (pizarras oscuras + vano de la
  puerta), NO de esta sala; si se decide pulir, es transversal y va al
  CIERRE (C15). Nota perf: 5 NPCs + valla + showcase + 2 micros — medir
  en C15 igual que las demas.

- [2026-07-06] paso `2b.0` (infra salas 2015) HECHO en commits
  `8d051761` (content) + `9d2e227f` (journey) — informe 15 completo.
  CV: los textos nuevos se aplicaron DIRECTO en la DB Neon de dev Y de
  prod (decision del usuario en sesion: "db via servicios/conexion
  directa") usando el write-path real del backend
  (`shared.db.repositories.cv_write_entities.upsert_experience` +
  UPDATE puntual de company para iai); el data-cache se regenero desde
  el API dev con `fetch-cv-cache.mjs` y el baseline de paridad con
  `REGEN_BASELINE=1`. projects-degrees quedo nov-dic 2015, UNA tesis
  PROSALUD, con PHP y MySQL sumados a skillsTechnical (confirmado por
  el usuario).
  Gotchas de la sesion: (1) el cache regenerado trajo DRIFT
  pre-existente del API (`priority` en todas las entidades y education
  SIN `end` en formacion en curso — `ended_on` es DATE nullable
  post-rename): se arreglo de raiz haciendo `EducationSchema.end`
  optional + fallback Actual/Present en AboutSection y cv-pdf; (2) el
  cache DDB del Lambda cv en PROD no se pudo invalidar (SSO AWS
  expirado, sin creds estaticas) — se auto-sana por TTL de 15 min, sin
  impacto (no hay build de prod inminente). Journey: RoomId->10, stubs
  `iai`/`asesoria` (cartel + barrera con su acento), aula SINTETICA
  universidad pura (spec slugs [] + AULA_TEXTS desde education), los 6
  arboles de dialogo reescritos (profesor con foreshadowing de una
  linea; `tesista-uno`/`tesista-dos` renombrados a `companera-lab`/
  `estudiante-sockets` — tambien sus ids talk-aula-0-*), wallArt sin
  plan-rescate (entra lamina pensum) y ficha cliente-servidor con
  guiño sin spoiler. Smoke browser verde x2 (10 salas montan con los
  indices corridos, stubs con 0 interactables propios — door-N es del
  shell —, futuro en index 9 con talk-9-pablo y sin portal-9, aula 22
  interactables con foreshadowing + cuaderno UPTYAB); static con las 9
  experiences y la company nueva del IAI. Unico error de consola: el
  504 transitorio de vite (gotcha conocido).

- [2026-07-05] sala `futuro` HECHA en commit `a50f073d` — informe 14, la
  ULTIMA (Etapa 2 completa: 7/7). Sala SINTETICA de cierre con las 3
  excepciones documentadas: SIN grieta al pasado (infoKit gano el flag
  `withPortal` — futuro es la unica sala que lo usa en false y el smoke
  asserta que `portal-7` NO existe), SIN showcase de producto y 1 solo
  NPC. Decisiones del usuario (AskUserQuestion 2026-07-05, NO reabrir):
  (1) las 8 ideas de futuro elegidas TODAS — productos con IA propios,
  indie/SaaS, emprendimiento LATAM, open source + comunidad, nuevos
  rubros, nuevos conocimientos, contenido tecnico publico y la
  meta-narrativa del journey — sumadas a los 3 ejes base del informe
  (Staff/Principal, IA+arquitectura, mentoria); (2) NPC "Pablo del
  futuro" SI + escritorios ligeros (3 puestos, laptops APAGADAS
  togglables con pantallas de lo-que-viene); (3) puerta PROXIMAMENTE:
  mantener AMBAS (la de destacame queda como guiño; futuro recibe LA
  grande y central en el muro final — el recorrido termina de frente a
  ella con el CTA holograma contact-7 en el eje). Pizarra de roadmap
  via wallArt (5 nodos ascendentes + estrella) en el muro +X — donde
  las otras salas tienen la grieta, esta mira adelante; Pablo del
  futuro la presenta (dialogo 9 nodos es/en, validateMix off). wallArt
  4 laminas / 3 fichas (manifiesto hacia-donde-voy, productos propios
  IA/indie/LATAM, comunidad y aprendizaje; la meta-narrativa Astro +
  Three.js + vibe coding queda decorativa). Los textos sinteticos de
  lib/rooms.ts se extendieron con las ideas elegidas (+2 retos, +2
  aprendizajes es/en). Smoke browser verde x2 (18 interactables, sin
  portal-7, dialogo, 3 fichas, CTA abre el panel Hablemos con
  LinkedIn, laptops togglean) + pasada visual del muro final y la
  pizarra; unico error de consola: el 504 transitorio de vite (gotcha
  conocido). Nota perf: sala liviana (1 NPC) — medir en C15 igual que
  las demas; destacame sigue siendo la candidata mas pesada.

- [2026-07-05] sala `destacame` HECHA en commit `4d8dc7d2` — informe 13
  (la sala unificada de 2 AREAS, la mas compleja) con 4 decisiones del
  usuario: 5 NPCs presente con la dev frontend RENOMBRADA a Camila
  Espinoza (el informe decia "Camila Fuentes" pero ese nombre exacto ya
  existe en GoodMeal — colision detectada y resuelta; los otros 4:
  Diego Riquelme dev fullstack, Rodrigo Salinas representante de banco,
  Valentina Cardenas PM como staff, Ana Sofia Herrera lead MX que honra
  leader+vibe), 3 NPCs pasado (Don Hernan, Marta y Nicolas — el arco
  completo), wallArt 4 laminas / 3 fichas (microfrontends +
  microservicios Django + campañas horas->minutos; pizarra Design
  System decorativa) y LAS 3 MICROS propuestas: pagar la deuda (el
  kiosco co-branded procesa WebPay -95%, confirma y cicla el banco),
  mejorar el score (la aguja 3D del gauge 459-760 sube de coral a
  verde con easing y el numero celebra 487->712) y lanzar campaña (el
  admin junto a la mesa del lead procesa en 4 min lo que antes tomaba
  horas). AREA A (muro -X): kiosco de pago + tarjeta bancaria + sello
  WebPay + monedas + tag flotante "deuda -95%". AREA B (muro +X):
  gauge totem + SuperApp en pedestal + tarjeta prepago + panel KPIs
  "+2M usuarios". Guiños intrinsecos heredados de cima: mesa de
  reunion (Ana Sofia preside), ciclo vibe coding (E cicla
  vibe->python->ts), CTA holograma de contacto (contact-6) y puerta
  PROXIMAMENTE. 2 showcases con key (showcase-6-pagaloaqui: Santander /
  Consumer / Scotiabank con los rojos SOLO dentro de las cards;
  showcase-6-producto: destacame.cl + destacame.com.mx). La micro
  Chile/Mexico fue ELIMINADA (mandato del informe). Pasado: drama de
  deudas sepia + coral (cartas de cobranza, telefono, gauge en rojo,
  ventanilla de sucursal con barrotes, operador con planillas, reloj)
  mas intentar pagar la deuda (la carta rebota con el "vuelva mañana").
  officeLayout = 3 puestos (Camila y Diego powered {0,1}, laptop libre
  togglable con el panel de plataforma). Smoke browser verde x2 (27
  interactables, 2 showcases E/Esc con 3+2 demos, 5 dialogos, 3
  fichas, 3 micros, ciclo vibe, laptop toggle, pasado 33
  interactables); unico error de consola: el 504 transitorio de vite
  (gotcha conocido). Nota perf: 5 NPCs + 2 showcases + gauge + mesa +
  CTA — medir en C15 igual que aula/corpoelec/ipasme/cofasa/dibal/
  goodmeal.

- [2026-07-05] sala `goodmeal` HECHA en commit `2e3459fa` — informe 12
  con 4 decisiones del usuario: 5 NPCs presente (Daniela la PM
  incluida), 3 NPCs pasado (el Sr. Peña opcional incluido), 4 laminas
  wallArt con 3 fichas INSPECCIONABLES (1/3 se desperdicia + migracion
  Vue 3 + mapa +3.000 comercios con los partners reales — upgrade
  sobre el informe que tenia el mapa decorativo; el tagline queda
  decorativo) y LAS 2 MICROS propuestas: empacar una Good Bag (la dona
  vuela de la vitrina a la bolsa kraft y el contador de impacto
  celebra el +1) y comprar la Good Bag (el checkout procesa ciclando
  tarjeta/Webpay/MACH, confirma y el pin geo late). officeLayout =
  rincon dev de 3 puestos (Camila y Matias sentados powered {0,1},
  laptop libre togglable que muestra el contador "bugs recurrentes ↓"
  — el guiño del achievement 3). Presente en dos mitades: CAFETERIA
  partner (-X: vitrina con donas/pan/pizza, caja + tarro de propinas,
  estante del excedente, mesa de empaque con 3 Good Bags kraft + logo
  teal, contador de impacto) y APP (smartphone gigante con card de
  precio tachado + pin geo flotante + plantas eco). Showcase teal +
  kraft (3 demos: Good Bags cerca de ti, checkout con transaccion
  segura, split Vue 2 vs Vue 3). Pasado: el cierre botando comida
  (vitrina a medio vaciar + carro de desechos + tacho rebosante +
  bolsas negras de la puerta trasera + reloj + cartel "excedente →
  basura" + ver la comida irse al tacho) con el arco Rodrigo/Ignacia/
  Sr. Peña (el dueño planta la idea de GoodMeal). Smoke browser verde
  x2 (23 interactables, showcase E/Esc, 5 dialogos, 3 fichas, 2
  micros, laptop toggle, pasado 29 interactables); unico error de
  consola: el 504 transitorio de vite (gotcha conocido). Nota perf: 5
  NPCs + vitrina + smartphone — medir en C15 igual que aula/corpoelec/
  ipasme/cofasa/dibal.

- [2026-07-05] sala `dibal` HECHA en commit `b6059f33` — informe 11 con
  4 decisiones del usuario: 5 NPCs presente (Andrea la comensal
  incluida), 3 NPCs pasado (Doña Carmen Flores la opcional incluida),
  3 cuadros INSPECCIONABLES (flujo mozo->KDS + boleta SUNAT +
  organigrama "De 1 a 5 devs" que honra el eje leader 95; mapa
  multi-local decorativo) y officeLayout = LA MESA DE PABLO (unico dev:
  laptop encendida con codigo Laravel/Vue mas 1 libre togglable con E;
  validateMix off como el aula). Presente en dos mitades: SALON (3
  mesas peruanas + comensales fusionados + caja navy con POS/termica/
  boleta flotante QR+sello) y COCINA (mesada + KDS + KOT + pase "para
  servir"). Micros nuevas: enviar comanda (sobre navy VUELA de la
  tablet al KDS; tarjeta nueva -> para servir) y emitir boleta (ticket
  sube de la termica + "Enviado a SUNAT ✓" ciclando efectivo/tarjeta/
  Yape). Showcase POS navy+teal (3 demos: pedido tablet, KDS, boleta
  SUNAT con placa del CV). Pasado: papelitos + clavo del pase +
  talonario/carbon + cajon descuadrado (falta S/40) + reloj + seguir
  el papelito perdido + arco Julio/Carmen/Elena. Nota tecnica:
  comandaMicro/boletaMicro y kdsVariantsFor/posVariantsFor extraidas a
  modulo por el limite de complejidad de Biome. Smoke browser verde x2
  (23 interactables, showcase E/Esc, 5 dialogos, 3 fichas, 2 micros,
  laptop toggle, pasado 29 interactables); unico error de consola: el
  504 transitorio de vite (gotcha conocido). Nota perf: 5 NPCs + salon
  + cocina — medir en C15 igual que aula/corpoelec/ipasme/cofasa.

- [2026-07-05] ETAPA 1 HECHA (C1 `2196e8dd` .. C6 `af82a772`) — canon
  completo en props.ts; aula con 6 NPCs (profesor y 2 compañeros nuevos)
  y 3 cuadros wallArt (1 inspeccionable); pasados partidos (aula intacto,
  corpoelec movido, cima eliminado); nota perf: el aula con 6 NPCs puede
  rozar los 100 draw calls — medir/optimizar en C15.
- [2026-07-05] sala `ipasme` HECHA en commit `d22c3988` — informe 09 tal
  cual (decision del usuario: 5 NPCs, sin recortar). Showcase con look app
  de escritorio Windows 2014 (3 demos: ficha, buscador 0,2 s, control de
  acceso por rol). 5 NPCs nuevos (2C+2P+1J): Daniela y Jose Miguel (devs),
  Yuleima (enfermera en ronda), Argenis (archivista), Dr. Villasmil (jefe).
  Pasado: archivo de carpetas manila + hueco del tarjeton + reloj + 3 NPCs
  (Argenis/Yuleima del arco + Petra nueva) + busqueda lenta "solo el
  tarjeton". Micros presente: buscar historia (instante) + tomar turno.
  Smoke browser completo verde x2 (23 interactables, showcase E/Esc, 5
  dialogos, ficha carnet, pasado 29 interactables); el unico error de
  consola es el 504 transitorio de vite (gotcha conocido). Nota perf: 5
  NPCs + lotes clinicos — medir en C15 igual que aula/corpoelec.
- [2026-07-05] sala `cofasa` HECHA en commit `7eecf589` — informe 10 con
  3 decisiones del usuario: 5 NPCs presente (sin recortar a Douglas), 3
  NPCs pasado (Carmen la opcional incluida), 3 cuadros INSPECCIONABLES
  (envasado + Pareto + disponibilidad; cGMP decorativo) + guiño Lebrun
  (etiqueta sobre la puerta). Showcase panel admin jQuery/Bootstrap 2017
  (3 demos: registrar parada, Pareto por causa, disponibilidad). Micro
  nueva: torre andon (unico rojo/verde) — E simula una parada, el
  monitor de linea registra la causa ciclando el catalogo real y vuelve
  a verde a los ~4 s. NPCs: Yorman y Douglas (devs en officeLayout,
  powered {0,1}, 1 laptop libre togglable), Nelida (ronda), Rafael
  (cofia = hair bun blanco), Carmen (jefa). Pasado: llenadora detenida +
  andon rojo fijo + reloj de pared + consolidar planillas (los totales
  NO cuadran) + arco Nelida/Rafael/Carmen. Smoke browser completo verde
  x2 (22 interactables, showcase E/Esc, 5 dialogos, 3 fichas, laptop
  toggle, pasado 28 interactables); unico error de consola: el 504
  transitorio de vite (gotcha conocido). Nota perf: 5 NPCs + linea +
  andon — medir en C15 igual que aula/corpoelec/ipasme.
- [2026-07-05] sala `corpoelec` HECHA en commit `46f28551` — primer
  consumidor real de officeLayout + softwareShowcase (3 demos intranet
  2013, badge OFFLINE). 5 NPCs (2C+2P+1J): los 2 arboles ricos existentes
  se CONSERVARON renombrados (veterano -> Wilmer Colina, tecnica de ronda
  -> Dubraska Piña reencuadrada administrativa) + 3 nuevos (Yorman,
  Genesis, Ing. Betancourt). Pasado: 3 NPCs (Dubraska y Wilmer del arco +
  el transcriptor conservado; Alcides opcional se fusiono en el Wilmer del
  pasado). wallArt 4 cuadros (2 inspeccionables). Smoke browser completo
  verde (23 interactables, showcase E/Esc, 5 dialogos, ficha 765 kV,
  pasado). Nota perf: 5 NPCs + estanteria + showcase — medir en C15 igual
  que el aula.
