/**
 * @module dialogs/goodmeal-presente (engine)
 * @description Arboles de dialogo de la sala 5 presente: GoodMeal, el
 *   food-tech chileno anti-desperdicio (2021). 5 NPCs del canon (informe
 *   12, decision del usuario: los 5): Camila Fuentes (dev frontend) y
 *   Matias Rojas (dev backend) hablan de trabajar con Pablo — la
 *   migracion a Vue 3 y el flujo de pagos —; Jorge Aravena (staff del
 *   local que empaca Good Bags) y Valentina Soto (clienta) hablan del
 *   impacto que la app habilita; Daniela Herrera (PM/Product Owner)
 *   cierra con el Scrum y las entregas parejas de startup.
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const GOODMEAL_PRESENTE_DIALOGS = {
  camila: defineDialog({
    name: { es: 'Camila Fuentes', en: 'Camila Fuentes' },
    chatter: [
      {
        es: 'El hot reload nuevo me tiene malacostumbrada.',
        en: 'The new hot reload has me spoiled.',
      },
      {
        es: 'Composition API... ya no vuelvo atras.',
        en: 'Composition API... I am never going back.',
      },
      {
        es: 'Este componente quedo limpio despues del refactor.',
        en: 'This component came out clean after the refactor.',
      },
      {
        es: 'Antes cada cambio rompia dos cosas. Ahora ninguna.',
        en: 'Before, every change broke two things. Now, none.',
      },
      {
        es: 'Ya ni me acuerdo de lo lento que era el build viejo.',
        en: 'I barely remember how slow the old build was.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Camila, frontend del equipo. Estas parado sobre una app ' +
            'recien migrada a Vue 3 — y se nota: todo carga mas rapido, ' +
            'hasta mi animo. ¿Que quieres saber?',
          en:
            'Camila, frontend on the team. You are standing on an app ' +
            'freshly migrated to Vue 3 — and it shows: everything loads ' +
            'faster, even my mood. What do you want to know?',
        },
        options: [
          {
            label: {
              es: '¿Como fue la migracion a Vue 3?',
              en: 'How did the Vue 3 migration go?',
            },
            next: 'vue-1',
          },
          {
            label: {
              es: '¿Que cambio para el usuario?',
              en: 'What changed for the user?',
            },
            next: 'ux-1',
          },
          {
            label: { es: 'Te dejo seguir', en: 'I will let you carry on' },
            next: null,
          },
        ],
      },
      'vue-1': {
        text: {
          es:
            'La app estaba en un Vue viejo y cada cambio DOLIA: ' +
            'tocabas un componente y rezabas. Pablo lidero el paso a ' +
            'Vue 3 con tooling moderno — reestructuro el frontend ' +
            'completo pensando en rendimiento y mantenibilidad, sin ' +
            'frenar el producto que seguia andando.',
          en:
            'The app ran on an old Vue and every change HURT: you ' +
            'touched a component and prayed. Pablo led the move to ' +
            'Vue 3 with modern tooling — he restructured the whole ' +
            'frontend for performance and maintainability, without ' +
            'stopping a product that kept running.',
        },
        options: [
          {
            label: {
              es: '¿Y como se migra sin frenar?',
              en: 'How do you migrate without stopping?',
            },
            next: 'vue-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'vue-2': {
        text: {
          es:
            'Por partes y con estandares: Pablo dejo reglas de codigo ' +
            'claras — como se nombra, como se estructura, que patron ' +
            'usa un componente nuevo — y el equipo migraba pieza a ' +
            'pieza sobre esa base. Cuando me toco entrar, el camino ya ' +
            'estaba marcado. Eso es liderar una migracion.',
          en:
            'Piece by piece and with standards: Pablo left clear code ' +
            'rules — how to name, how to structure, which pattern a ' +
            'new component follows — and the team migrated on top of ' +
            'that base. By the time I joined in, the path was already ' +
            'marked. That is leading a migration.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Buen camino', en: 'A good path' },
            next: null,
          },
        ],
      },
      'ux-1': {
        text: {
          es:
            'Todo. La app de pedidos se sentia pesada: pantallas que ' +
            'se pegaban, listas que tardaban. Con la base nueva la UX ' +
            'mejoro notablemente — abres, eliges tu Good Bag, pagas y ' +
            'listo. La gente lo nota aunque no sepa por que.',
          en:
            'Everything. The ordering app felt heavy: screens that ' +
            'froze, lists that lagged. On the new base the UX improved ' +
            'notably — open, pick your Good Bag, pay, done. People ' +
            'notice even if they do not know why.',
        },
        options: [
          {
            label: {
              es: '¿Y los bugs de siempre?',
              en: 'And the usual bugs?',
            },
            next: 'ux-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'ux-2': {
        text: {
          es:
            'Esa es mi parte favorita: los bugs RECURRENTES — los que ' +
            'volvian cada dos semanas con otro disfraz — se fueron ' +
            'apagando. Con el frontend estabilizado, resolverlos toma ' +
            'horas en vez de dias. Mira el monitor de Pablo: el ' +
            'contador de bugs va para abajo.',
          en:
            'That is my favourite part: the RECURRING bugs — the ones ' +
            'that came back every two weeks in a new disguise — kept ' +
            'fading out. With the frontend stabilised, fixing them ' +
            'takes hours instead of days. Look at Pablo’s monitor: ' +
            'the bug counter points down.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Se nota el orden', en: 'The order shows' },
            next: null,
          },
        ],
      },
    },
  }),

  matias: defineDialog({
    name: { es: 'Matias Rojas', en: 'Matias Rojas' },
    chatter: [
      {
        es: 'El webhook del pago respondio 200. Respira.',
        en: 'The payment webhook returned 200. Breathe.',
      },
      {
        es: 'Consistencia, consistencia, consistencia.',
        en: 'Consistency, consistency, consistency.',
      },
      {
        es: 'Nadie quiere un pago cobrado dos veces. NADIE.',
        en: 'Nobody wants a payment charged twice. NOBODY.',
      },
      {
        es: 'Front y back hablando el mismo idioma, por fin.',
        en: 'Front and back speaking the same language, at last.',
      },
      {
        es: 'Reserva, pago, retiro. Si eso fluye, todo fluye.',
        en: 'Reserve, pay, pick up. If that flows, everything flows.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Matias, backend. Yo cuido los servicios: reservas, pagos, ' +
            'el contador de impacto. ¿Sabes que fue lo raro de Pablo? ' +
            'Que decia "frontend" en el contrato... y termino metido ' +
            'hasta aca atras. Pregunta.',
          en:
            'Matias, backend. I look after the services: reservations, ' +
            'payments, the impact counter. You know what was odd about ' +
            'Pablo? His contract said "frontend"... and he ended up ' +
            'all the way back here. Ask away.',
        },
        options: [
          {
            label: {
              es: '¿Como era trabajar con el?',
              en: 'What was working with him like?',
            },
            next: 'full-1',
          },
          {
            label: {
              es: '¿Que paso con los pagos?',
              en: 'What happened with payments?',
            },
            next: 'pago-1',
          },
          {
            label: { es: 'Sigue con lo tuyo', en: 'Carry on with yours' },
            next: null,
          },
        ],
      },
      'full-1': {
        text: {
          es:
            'Full stack de verdad: integraba su frontend con mis ' +
            'servicios sin tirar el problema por encima del muro. Si ' +
            'un endpoint devolvia algo incomodo, lo conversabamos y lo ' +
            'arreglabamos JUNTOS — el contrato de datos primero, el ' +
            'codigo despues. Se agradece.',
          en:
            'Actual full stack: he wired his frontend into my services ' +
            'without throwing problems over the wall. If an endpoint ' +
            'returned something awkward, we talked it through and ' +
            'fixed it TOGETHER — data contract first, code second. ' +
            'Much appreciated.',
        },
        options: [
          {
            label: {
              es: '¿Y bajo presion?',
              en: 'And under pressure?',
            },
            next: 'full-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'full-2': {
        text: {
          es:
            'Startup: los PMs piden para ayer y los plazos aprietan. ' +
            'Pablo resolvia bugs y solicitudes sin drama, parejo. En ' +
            'un equipo chico eso vale oro: sabes que lo que toma, lo ' +
            'entrega. Y si no llega, lo dice en la daily — no el ' +
            'viernes a las seis.',
          en:
            'Startup life: PMs want it yesterday and deadlines bite. ' +
            'Pablo cleared bugs and requests without drama, steadily. ' +
            'In a small team that is gold: whatever he takes, he ' +
            'ships. And if it will not land, he says so at the daily — ' +
            'not on Friday at six.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Vale oro, si', en: 'Gold indeed' },
            next: null,
          },
        ],
      },
      'pago-1': {
        text: {
          es:
            'El corazon sensible de la app: aca la gente PAGA su Good ' +
            'Bag. Pablo entro a reforzar ese flujo — transacciones ' +
            'fiables, datos sensibles tratados con guantes, y el ' +
            'estado del pedido siempre consistente entre la app, el ' +
            'local y nosotros.',
          en:
            'The app’s sensitive heart: people PAY for their Good Bag ' +
            'here. Pablo came in to harden that flow — reliable ' +
            'transactions, sensitive data handled with gloves, and ' +
            'order state always consistent across the app, the venue ' +
            'and us.',
        },
        options: [
          {
            label: {
              es: '¿Que puede salir mal en un pago?',
              en: 'What can go wrong in a payment?',
            },
            next: 'pago-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'pago-2': {
        text: {
          es:
            'Todo: un doble cobro, un pago que confirma pero no ' +
            'reserva, una bolsa vendida dos veces. Cada caso borde que ' +
            'cerramos es una persona que retira su comida sin pelear ' +
            'con soporte. Por eso el mantra: consistencia. La ' +
            'plataforma mueve plata — fintech-adyacente, le dicen.',
          en:
            'Everything: a double charge, a payment that confirms but ' +
            'does not reserve, a bag sold twice. Every edge case we ' +
            'close is a person picking up food without fighting ' +
            'support. Hence the mantra: consistency. This platform ' +
            'moves money — fintech-adjacent, they call it.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Que no se caiga', en: 'Keep it standing' },
            next: null,
          },
        ],
      },
    },
  }),

  jorge: defineDialog({
    name: { es: 'Jorge Aravena', en: 'Jorge Aravena' },
    chatter: [
      {
        es: 'Tres Good Bags mas y cierro la publicacion de hoy.',
        en: 'Three more Good Bags and I close today’s listing.',
      },
      {
        es: 'Esta dona estaba condenada al tacho. Ya no.',
        en: 'This donut was doomed to the bin. Not anymore.',
      },
      {
        es: 'En la app ya reservaron cinco bolsas. Cinco.',
        en: 'Five bags already reserved on the app. Five.',
      },
      {
        es: 'La tapa se enrolla asi: dos vueltas y listo.',
        en: 'The top rolls like this: two turns and done.',
      },
      {
        es: 'Antes esto era basura. Ahora es venta.',
        en: 'This used to be garbage. Now it is a sale.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Jorge, de la cafeteria de la esquina — el que arma las ' +
            'Good Bags. Cada tarde junto el excedente del dia, lo ' +
            'empaco en estas bolsas kraft y lo publico en la app. ' +
            '¿Quieres ver como funciona?',
          en:
            'Jorge, from the corner cafe — the one who packs the Good ' +
            'Bags. Every afternoon I gather the day’s surplus, pack it ' +
            'into these kraft bags and list it on the app. Want to see ' +
            'how it works?',
        },
        options: [
          {
            label: {
              es: '¿Como armas una Good Bag?',
              en: 'How do you pack a Good Bag?',
            },
            next: 'bag-1',
          },
          {
            label: {
              es: '¿Que hacian antes con esto?',
              en: 'What did you do with this before?',
            },
            next: 'antes-1',
          },
          {
            label: { es: 'Sigue empacando', en: 'Keep packing' },
            next: null,
          },
        ],
      },
      'bag-1': {
        text: {
          es:
            'Junto lo que quedo perfecto pero no se vendio — pan, ' +
            'donas, alguna porcion de pizza —, lo meto en la bolsa y ' +
            'publico en la app: cuantas bolsas hay, a que hora se ' +
            'retiran y el precio rebajado. El contenido es sorpresa: ' +
            'esa es la gracia del signo de pregunta.',
          en:
            'I gather what ended the day perfect but unsold — bread, ' +
            'donuts, the odd pizza slice —, pack it into the bag and ' +
            'list it on the app: how many bags, pickup window and the ' +
            'discounted price. The contents are a surprise: that is ' +
            'the point of the question mark.',
        },
        options: [
          {
            label: {
              es: '¿Y como sabes si se vendio?',
              en: 'How do you know it sold?',
            },
            next: 'bag-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'bag-2': {
        text: {
          es:
            'La app me lo dice sola: veo cuantas reservaron, quien ' +
            'viene en camino y a que hora. Cuando llegan muestran el ' +
            'pedido en el telefono, yo entrego la bolsa y ya. Sin ' +
            'llamadas, sin libreta — y el contador de comida rescatada ' +
            'sube solito.',
          en:
            'The app tells me on its own: I see how many were ' +
            'reserved, who is on the way and when. They show the order ' +
            'on their phone, I hand over the bag, done. No calls, no ' +
            'notebook — and the rescued-food counter climbs by ' +
            'itself.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Redondo el sistema', en: 'A tidy system' },
            next: null,
          },
        ],
      },
      'antes-1': {
        text: {
          es:
            'Botarlo. Asi de simple y asi de triste: cajas de pan y ' +
            'donas PERFECTAS a la bolsa negra, cada noche. Comida que ' +
            'alguien se habria comido feliz, directo al camion de la ' +
            'basura. Si cruzas esa grieta lo ves con tus propios ' +
            'ojos... yo estuve ahi.',
          en:
            'Bin it. That simple and that sad: boxes of PERFECT bread ' +
            'and donuts into the black bag, every night. Food someone ' +
            'would have loved, straight to the garbage truck. Cross ' +
            'that rift and you will see it with your own eyes... I ' +
            'was there.',
        },
        options: [
          {
            label: {
              es: '¿Y ahora cuanto rescatan?',
              en: 'And how much do you rescue now?',
            },
            next: 'antes-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'antes-2': {
        text: {
          es:
            'Casi todo el excedente del dia se va en Good Bags — y lo ' +
            'que era merma ahora es ingreso. La gente ahorra, el ' +
            'local recupera plata y la comida se come, que es para lo ' +
            'que existe. Mas de tres mil locales ya lo hacen. Miralo ' +
            'en el mapa de la pared.',
          en:
            'Nearly all of the day’s surplus leaves in Good Bags — ' +
            'and what used to be shrinkage is now income. People save, ' +
            'the venue recovers money and the food gets EATEN, which ' +
            'is what it is for. Over three thousand venues do it ' +
            'already. Check the map on the wall.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'A seguir rescatando', en: 'Keep rescuing' },
            next: null,
          },
        ],
      },
    },
  }),

  valentina: defineDialog({
    name: { es: 'Valentina Soto', en: 'Valentina Soto' },
    chatter: [
      {
        es: '¿Que tocara hoy? Esa es la gracia.',
        en: 'What will it be today? That is the fun part.',
      },
      {
        es: 'Me salio como un tercio del precio. Un TERCIO.',
        en: 'It cost me about a third of the price. A THIRD.',
      },
      {
        es: 'Pago en dos toques y sigo caminando.',
        en: 'I pay in two taps and keep walking.',
      },
      {
        es: 'La de ayer venia con torta. TORTA.',
        en: 'Yesterday’s came with cake. CAKE.',
      },
      {
        es: 'Retiro a las siete, justo saliendo de la pega.',
        en: 'Pickup at seven, right after leaving work.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Valentina — clienta seria: una Good Bag casi todos los ' +
            'dias. Recien reserve la de esta tarde en el telefono ' +
            'gigante ese, por si quieres mirar. ¿Que me preguntas?',
          en:
            'Valentina — serious customer: a Good Bag almost every ' +
            'day. I just reserved this afternoon’s on that giant phone ' +
            'over there, in case you want a look. What would you ask ' +
            'me?',
        },
        options: [
          {
            label: {
              es: '¿Como funciona para ti?',
              en: 'How does it work for you?',
            },
            next: 'compra-1',
          },
          {
            label: {
              es: '¿Y la app, se porta bien?',
              en: 'Does the app behave?',
            },
            next: 'app-1',
          },
          {
            label: { es: 'Disfruta la bolsa', en: 'Enjoy the bag' },
            next: null,
          },
        ],
      },
      'compra-1': {
        text: {
          es:
            'Abro la app, veo que locales cerca de la pega tienen ' +
            'bolsas hoy, elijo una y pago ahi mismo — dos toques. Me ' +
            'sale como un tercio de lo que costaria, y el pin del mapa ' +
            'me lleva al local a la hora del retiro. Sorpresa incluida: ' +
            'no sabes que trae hasta abrirla.',
          en:
            'I open the app, see which venues near work have bags ' +
            'today, pick one and pay right there — two taps. It costs ' +
            'me about a third of the shelf price, and the map pin ' +
            'walks me to the venue at pickup time. Surprise included: ' +
            'you do not know what is inside until you open it.',
        },
        options: [
          {
            label: {
              es: '¿Y si no te gusta lo que toca?',
              en: 'What if you do not like the draw?',
            },
            next: 'compra-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'compra-2': {
        text: {
          es:
            'Casi nunca pasa — es comida del dia, rica, del mismo ' +
            'mostrador que a precio lleno no alcance a comprar. Y ' +
            'aunque un dia toque puro pan: pague un tercio y esa ' +
            'comida no termino en la basura. Ahorro yo, gana el local, ' +
            'gana el planeta. Dificil perderle.',
          en:
            'Almost never happens — it is same-day food, tasty, from ' +
            'the very counter I could not afford at full price. And ' +
            'even if one day it is all bread: I paid a third and that ' +
            'food did not end up in the bin. I save, the venue wins, ' +
            'the planet wins. Hard to lose.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Buen negocio', en: 'A good deal' },
            next: null,
          },
        ],
      },
      'app-1': {
        text: {
          es:
            'Ahora si. Antes se PEGABA: la lista tardaba, el boton de ' +
            'pagar se quedaba pensando y una vez casi pierdo la bolsa ' +
            'por el reintento. Hace unos meses la app cambio — se ' +
            'siente nueva, fluida — y el pago sale a la primera. No se ' +
            'que hicieron, pero gracias.',
          en:
            'Now it does. It used to FREEZE: the list lagged, the pay ' +
            'button sat thinking and once I nearly lost my bag to a ' +
            'retry. A few months ago the app changed — it feels new, ' +
            'fluid — and payment lands first try. No idea what they ' +
            'did, but thank you.',
        },
        options: [
          {
            label: {
              es: 'Creo que se quien fue',
              en: 'I think I know who did it',
            },
            next: 'app-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'app-2': {
        text: {
          es:
            '¿En serio? Pues dale las gracias de mi parte. Para mi la ' +
            'app ES GoodMeal: si anda lenta, no compro; si fluye, ' +
            'compro todos los dias. Parece detalle tecnico, pero de ' +
            'eso vive el rescate de comida.',
          en:
            'Really? Then thank them for me. To me the app IS ' +
            'GoodMeal: if it drags, I do not buy; if it flows, I buy ' +
            'every day. It sounds like a technical detail, but food ' +
            'rescue lives off it.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Se lo dire', en: 'I will pass it on' },
            next: null,
          },
        ],
      },
    },
  }),

  daniela: defineDialog({
    name: { es: 'Daniela Herrera', en: 'Daniela Herrera' },
    chatter: [
      {
        es: 'El sprint cierra el viernes. Vamos bien.',
        en: 'Sprint closes Friday. We are on track.',
      },
      {
        es: 'Daily en cinco minutos, equipo.',
        en: 'Daily in five minutes, team.',
      },
      {
        es: 'Ese bug lleva dos sprints sin volver. Record.',
        en: 'That bug has stayed dead two sprints. A record.',
      },
      {
        es: 'El backlog esta priorizado. No me lo desordenen.',
        en: 'The backlog is prioritised. Do not shuffle it.',
      },
      {
        es: 'Contra el tiempo, como siempre. Pero llegamos.',
        en: 'Against the clock, as always. But we deliver.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Daniela, Product Owner. Mi trabajo es que esta startup ' +
            'entregue valor cada sprint sin quemarse en el intento. ' +
            'Spoiler: no siempre es elegante. ¿Que quieres saber?',
          en:
            'Daniela, Product Owner. My job is getting this startup ' +
            'to ship value every sprint without burning out on the ' +
            'way. Spoiler: it is not always pretty. What do you want ' +
            'to know?',
        },
        options: [
          {
            label: {
              es: '¿Como es el ritmo aqui?',
              en: 'What is the pace like here?',
            },
            next: 'ritmo-1',
          },
          {
            label: {
              es: '¿Que aporto Pablo al equipo?',
              en: 'What did Pablo bring the team?',
            },
            next: 'pablo-1',
          },
          {
            label: { es: 'Que cierre el sprint', en: 'Go close that sprint' },
            next: null,
          },
        ],
      },
      'ritmo-1': {
        text: {
          es:
            'Startup pura: plazos ajustados, prioridades que giran y ' +
            'un producto vivo con miles de locales encima. Trabajamos ' +
            'en Scrum — dailies, planificacion de iteraciones, ' +
            'retrospectivas — porque sin ese orden la urgencia se lo ' +
            'come todo.',
          en:
            'Pure startup: tight deadlines, spinning priorities and a ' +
            'live product with thousands of venues on top. We run ' +
            'Scrum — dailies, iteration planning, retros — because ' +
            'without that order, urgency devours everything.',
        },
        options: [
          {
            label: {
              es: '¿Y el orden funciona?',
              en: 'And does the order work?',
            },
            next: 'ritmo-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'ritmo-2': {
        text: {
          es:
            'Cuando el equipo lo abraza, si. La diferencia entre ' +
            'prometer y ENTREGAR es un equipo que estima honesto y ' +
            'avisa a tiempo. Este equipo aprendio a hacerlo — y hubo ' +
            'gente que empujo esa cultura mas que otros. Adivina a ' +
            'quien me refiero.',
          en:
            'When the team embraces it, yes. The gap between ' +
            'promising and DELIVERING is a team that estimates ' +
            'honestly and flags early. This team learned to do that — ' +
            'and some pushed that culture harder than others. Guess ' +
            'who I mean.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me hago una idea', en: 'I can guess' },
            next: 'pablo-1',
          },
        ],
      },
      'pablo-1': {
        text: {
          es:
            'Previsibilidad. Como PO vivo de eso: Pablo entregaba ' +
            'PAREJO, sprint tras sprint — sin heroismos de ultima ' +
            'noche ni sorpresas el jueves. Bug que le asignaba, bug ' +
            'que moria rapido; y los recurrentes dejaron de volver ' +
            'cuando estabilizo el frontend.',
          en:
            'Predictability. As a PO I live off it: Pablo delivered ' +
            'STEADILY, sprint after sprint — no last-night heroics, ' +
            'no Thursday surprises. Any bug I assigned him died fast; ' +
            'and the recurring ones stopped coming back once he ' +
            'stabilised the frontend.',
        },
        options: [
          {
            label: {
              es: '¿Y fuera del codigo?',
              en: 'And beyond the code?',
            },
            next: 'pablo-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'pablo-2': {
        text: {
          es:
            'Aporto al Scrum mismo: dailies al grano, estimaciones ' +
            'honestas y esa costumbre suya de avisar los riesgos ' +
            'ANTES de que dolieran. Con siete meses aca dejo la ' +
            'entrega mas ordenada de lo que la encontro. Eso, en una ' +
            'startup, es un regalo.',
          en:
            'He fed Scrum itself: to-the-point dailies, honest ' +
            'estimates and that habit of flagging risks BEFORE they ' +
            'hurt. In seven months here he left delivery tidier than ' +
            'he found it. In a startup, that is a gift.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Buen legado', en: 'A fine legacy' },
            next: null,
          },
        ],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
