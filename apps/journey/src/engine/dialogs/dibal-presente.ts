/**
 * @module dialogs/dibal-presente (engine)
 * @description Arboles de dialogo de la sala 4 presente: Dibal (Peru,
 *   2018-21), el SaaS POS multi-restaurante que Pablo construyo desde
 *   cero como PRIMER y unico developer, y donde crecio el equipo de 1 a
 *   ~5 como tech lead. 5 NPCs (informe 11, variante unico dev: el
 *   compañero de desarrollo se sustituye por el dueño): Don Ricardo
 *   Quispe (dueño del restaurante, define requisitos), Milagros Huaman
 *   (moza con tablet), Chef Ernesto Ramos (cocinero del KDS), Rosa
 *   Palomino (cajera de la facturacion SUNAT) y Andrea Chavez
 *   (comensal). Todos anclados a la data real: jQuery + Laravel desde
 *   cero, e-commerce en Vue, AWS (EC2/RDS/AutoScaling/Load Balancer),
 *   facturacion electronica directa a SUNAT, multi-restaurante en uso
 *   productivo, equipo de 1 a ~4-6 con estandares.
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const DIBAL_PRESENTE_DIALOGS = {
  ricardo: defineDialog({
    name: { es: 'Don Ricardo Quispe', en: 'Don Ricardo Quispe' },
    chatter: [
      {
        es: 'Mis tres locales, en el celular. Miralos: verdecitos.',
        en: 'My three restaurants, on my phone. Look: all green.',
      },
      {
        es: 'Antes vivia con miedo a SUNAT. Ahora duermo tranquilo.',
        en: 'I used to live in fear of SUNAT. Now I sleep just fine.',
      },
      {
        es: 'Yo pedia y Pablo lo hacia realidad. Asi de simple.',
        en: 'I asked and Pablo made it real. Simple as that.',
      },
      {
        es: 'Empezo un muchacho solo. Termino un equipo entero.',
        en: 'It started as one kid alone. It ended as a whole team.',
      },
      {
        es: 'La hora del almuerzo ya no tumba el sistema. Ya no.',
        en: 'The lunch rush does not knock the system down. Not anymore.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Ricardo Quispe, dueño de esta casa — y de otras dos mas. El ' +
            'sistema que ve funcionando aqui lo construyo Pablo, desde ' +
            'cero, cuando era el UNICO desarrollador de Dibal. ¿Que ' +
            'quiere saber?',
          en:
            'Ricardo Quispe, owner of this house — and of two more. The ' +
            'system you see running here was built by Pablo, from ' +
            'scratch, back when he was Dibal’s ONLY developer. What ' +
            'would you like to know?',
        },
        options: [
          {
            label: {
              es: '¿Como empezo todo esto?',
              en: 'How did all this start?',
            },
            next: 'historia-1',
          },
          {
            label: {
              es: '¿Que le pedia usted a Pablo?',
              en: 'What did you ask Pablo for?',
            },
            next: 'req-1',
          },
          {
            label: { es: 'Hay mas temas, ¿no?', en: 'There is more, right?' },
            next: 'hub2',
          },
          {
            label: { es: 'Nada, siga usted', en: 'Nothing, carry on' },
            next: null,
          },
        ],
      },
      hub2: {
        text: {
          es:
            'Quedan mis dos favoritos: como este sistema me quito el ' +
            'miedo a SUNAT, y como el muchacho solo termino liderando un ' +
            'equipo.',
          en:
            'My two favourites are left: how this system took away my ' +
            'fear of SUNAT, and how the lone kid ended up leading a ' +
            'team.',
        },
        options: [
          {
            label: {
              es: 'Cuenteme lo de SUNAT',
              en: 'Tell me about SUNAT',
            },
            next: 'sunat-1',
          },
          {
            label: {
              es: '¿Como crecio el equipo?',
              en: 'How did the team grow?',
            },
            next: 'equipo-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Pruebe el POS junto a la puerta: ahi esta la demo del ' +
            'sistema completo. Y si se queda a almorzar, el lomo saltado ' +
            'es el orgullo de la casa.',
          en:
            'Try the POS by the door: the full system demo lives there. ' +
            'And if you stay for lunch, the lomo saltado is the pride of ' +
            'the house.',
        },
        options: [{ label: { es: 'Hasta luego', en: 'See you' }, next: null }],
      },

      'historia-1': {
        text: {
          es:
            'En 2018 esto era un restaurante que crecia y un caos que ' +
            'crecia con el: comandas en papelitos, boletas a mano, la ' +
            'cocina gritando. Dibal contrato a Pablo como su primer ' +
            'desarrollador — el solo, con jQuery y Laravel — para ' +
            'construir el sistema desde CERO.',
          en:
            'In 2018 this was a growing restaurant and a chaos growing ' +
            'with it: paper order slips, handwritten receipts, the ' +
            'kitchen shouting. Dibal hired Pablo as its first developer ' +
            '— alone, with jQuery and Laravel — to build the system from ' +
            'SCRATCH.',
        },
        options: [
          {
            label: {
              es: '¿Y de un prototipo a esto?',
              en: 'From a prototype to this?',
            },
            next: 'historia-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'historia-2': {
        text: {
          es:
            'De prototipo a plataforma: hoy VARIOS restaurantes operan ' +
            'con Dibal, cada uno con su salon, su cocina y su caja ' +
            'conectadas a la misma nube. Multi-restaurante de verdad — ' +
            'por eso yo veo mis tres locales desde el celular.',
          en:
            'From prototype to platform: today SEVERAL restaurants run ' +
            'on Dibal, each with its floor, kitchen and till connected ' +
            'to the same cloud. Truly multi-restaurant — that is why I ' +
            'can watch my three places from my phone.',
        },
        options: [
          {
            label: {
              es: '¿Y aguanta la hora punta?',
              en: 'Does it survive the rush?',
            },
            next: 'aws-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'aws-1': {
        text: {
          es:
            'Eso le pregunte yo: "¿y cuando el almuerzo llene los tres ' +
            'locales a la vez?". Pablo lo desplego en AWS con ' +
            'autoescalado y balanceador de carga: en los picos el ' +
            'sistema crece solo y despues se encoge. Yo no entiendo ' +
            'como — entiendo que NUNCA se cae cuando mas lo necesito.',
          en:
            'I asked him exactly that: "what about when lunch fills all ' +
            'three places at once?". Pablo deployed it on AWS with ' +
            'autoscaling and a load balancer: at peak times the system ' +
            'grows on its own and shrinks after. I do not understand ' +
            'how — I understand it NEVER falls when I need it most.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
      'req-1': {
        text: {
          es:
            'Yo no se de sistemas; se de restaurantes. Le decia: ' +
            '"quiero ver mis tres locales desde el celular", "quiero que ' +
            'la boleta salga sola", "quiero que la cocina no grite". Y ' +
            'el lo hacia REALIDAD. Cada pedido mio volvia convertido en ' +
            'una pantalla que funcionaba.',
          en:
            'I know nothing about systems; I know restaurants. I would ' +
            'say: "I want to see my three places from my phone", "I want ' +
            'the receipt to print itself", "I want the kitchen to stop ' +
            'shouting". And he made it REAL. Every request of mine came ' +
            'back as a working screen.',
        },
        options: [
          {
            label: {
              es: '¿Nunca le dijo que no?',
              en: 'Did he never say no?',
            },
            next: 'req-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'req-2': {
        text: {
          es:
            'Claro que si — y eso lo hizo mas valioso. Cuando algo no ' +
            'convenia, me explicaba por que y me proponia algo mejor. ' +
            'Hasta un e-commerce en Vue me armo, para que el cliente ' +
            'pida solo y el local trabaje sin que nadie conteste el ' +
            'telefono. Orientado al cliente, dicen. Yo digo: escucha.',
          en:
            'Of course he did — and that made him more valuable. When ' +
            'something was a bad idea, he explained why and proposed ' +
            'something better. He even built me a Vue e-commerce so ' +
            'customers order on their own and the place runs without ' +
            'anyone answering the phone. Client-oriented, they say. I ' +
            'say: he listens.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy. Gracias', en: 'I will go. Thanks' },
            next: 'bye',
          },
        ],
      },
      'sunat-1': {
        text: {
          es:
            'En Peru la boleta electronica es OBLIGATORIA: SUNAT — el ' +
            'fisco — la exige, y el que no cumple paga multas que ' +
            'duelen. Yo vivia con ese susto en el cuerpo: talonarios, ' +
            'carbon, "¿habre declarado bien?". Ese miedo tenia nombre y ' +
            'apellido.',
          en:
            'In Peru the electronic receipt is MANDATORY: SUNAT — the ' +
            'tax authority — demands it, and whoever fails pays fines ' +
            'that hurt. I lived with that fright in my body: receipt ' +
            'books, carbon paper, "did I file it right?". That fear had ' +
            'a first and last name.',
        },
        options: [
          {
            label: {
              es: '¿Y ahora como funciona?',
              en: 'And how does it work now?',
            },
            next: 'sunat-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'sunat-2': {
        text: {
          es:
            'Ahora cada boleta se emite y se ENVIA SOLA a SUNAT, ' +
            'directo del sistema, y vuelve aceptada con su codigo QR. ' +
            'Rosa cobra, la termica imprime y yo no toco nada. Cero ' +
            'multas desde entonces. Ese solo cambio ya pagaba el ' +
            'sistema completo.',
          en:
            'Now every receipt is issued and SENDS ITSELF to SUNAT, ' +
            'straight from the system, and comes back accepted with its ' +
            'QR code. Rosa charges, the thermal printer prints and I ' +
            'touch nothing. Zero fines ever since. That single change ' +
            'already paid for the whole system.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
      'equipo-1': {
        text: {
          es:
            'Al principio Pablo era el equipo: UNO. Pero Dibal crecio, ' +
            'y el en vez de guardarse el codigo, armo cantera: entraron ' +
            'nuevos desarrolladores y el los recibia, les enseñaba el ' +
            'sistema y les marcaba estandares. De uno a cuatro, cinco... ' +
            'y el pasando de programar todo a LIDERAR.',
          en:
            'At first Pablo WAS the team: ONE. But Dibal grew, and ' +
            'instead of hoarding the code he built a bench: new ' +
            'developers came in and he onboarded them, taught them the ' +
            'system and set the standards. From one to four, five... ' +
            'and he went from coding everything to LEADING.',
        },
        options: [
          {
            label: {
              es: '¿Y eso se noto en el producto?',
              en: 'Did the product show it?',
            },
            next: 'equipo-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'equipo-2': {
        text: {
          es:
            'Se noto en que nada se detuvo: el sistema siguio creciendo ' +
            'con el equipo. Pablo partio el frontend en piezas — ' +
            'microfrontends, les dicen — para que cada quien avanzara ' +
            'sin pisar al otro. Casi tres años estuvo aqui, y el cuadro ' +
            'de la pared del frente cuenta esa historia: de 1 a 5.',
          en:
            'It showed in that nothing stalled: the system kept growing ' +
            'with the team. Pablo split the frontend into pieces — ' +
            'microfrontends, they call them — so everyone could move ' +
            'without stepping on each other. He was here almost three ' +
            'years, and the picture on the front wall tells that story: ' +
            'from 1 to 5.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Voy a ver el cuadro', en: 'I will see the picture' },
            next: 'bye',
          },
        ],
      },
    },
  }),

  milagros: defineDialog({
    name: { es: 'Milagros Huaman', en: 'Milagros Huaman' },
    chatter: [
      {
        es: 'Mesa 4: un ceviche, un lomo. Ya esta en cocina. YA.',
        en: 'Table 4: one ceviche, one lomo. Already in the kitchen. ALREADY.',
      },
      {
        es: 'Nunca mas grite un pedido. Nunca mas.',
        en: 'I never shouted an order again. Never again.',
      },
      {
        es: '"Sin cebolla" — lo escribo y la cocina lo LEE.',
        en: '"No onion" — I type it and the kitchen READS it.',
      },
      {
        es: 'Antes corria con papelitos. Ahora camino con la tablet.',
        en: 'I used to run with paper slips. Now I walk with the tablet.',
      },
      {
        es: 'La propina subio desde que las mesas rotan mas rapido.',
        en: 'Tips went up since the tables turn faster.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Milagros, moza del salon — la de la tablet. Yo tomo el ' +
            'pedido aqui en la mesa y la cocina lo esta leyendo antes de ' +
            'que yo me de la vuelta. ¿Que quieres saber?',
          en:
            'Milagros, floor waitress — the one with the tablet. I take ' +
            'the order right at the table and the kitchen is reading it ' +
            'before I even turn around. What do you want to know?',
        },
        options: [
          {
            label: {
              es: '¿Como tomas un pedido?',
              en: 'How do you take an order?',
            },
            next: 'pedido-1',
          },
          {
            label: {
              es: '¿Como era antes de la tablet?',
              en: 'What was it like before the tablet?',
            },
            next: 'antes-1',
          },
          {
            label: { es: 'Hay mas temas, ¿no?', en: 'There is more, right?' },
            next: 'hub2',
          },
          {
            label: { es: 'Nada, sigue con lo tuyo', en: 'Nothing, carry on' },
            next: null,
          },
        ],
      },
      hub2: {
        text: {
          es:
            'Te puedo contar el detalle que mas me gusta: las ' +
            'observaciones. O como el sistema me cambio la propina.',
          en:
            'I can tell you my favourite detail: the order notes. Or ' +
            'how the system changed my tips.',
        },
        options: [
          {
            label: {
              es: '¿Que pasa con las observaciones?',
              en: 'What about the order notes?',
            },
            next: 'obs-1',
          },
          {
            label: {
              es: '¿La propina? Cuentame',
              en: 'The tips? Tell me',
            },
            next: 'propina-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Dale E a la tablet del soporte y manda una comanda de ' +
            'prueba — vas a ver la tarjeta aparecer en la pantalla de la ' +
            'cocina. Ernesto ni se inmuta: le llegan asi todo el dia.',
          en:
            'Press E on the tablet stand and send a test order — you ' +
            'will see the card pop up on the kitchen screen. Ernesto ' +
            'will not even flinch: they arrive like that all day.',
        },
        options: [{ label: { es: 'Hasta luego', en: 'See you' }, next: null }],
      },

      'pedido-1': {
        text: {
          es:
            'Llego a la mesa, abro la tablet y toco: categoria, plato, ' +
            'cantidad. ¿Ceviche? Toque. ¿Lomo saltado? Toque. ¿Inca ' +
            'Kola? Toque. El carrito se arma solo con los precios, y ' +
            'cuando confirmo, la comanda VIAJA: del salon a la cocina ' +
            'sin tocar un papel.',
          en:
            'I get to the table, open the tablet and tap: category, ' +
            'dish, quantity. Ceviche? Tap. Lomo saltado? Tap. Inca ' +
            'Kola? Tap. The cart builds itself with the prices, and ' +
            'when I confirm, the order TRAVELS: floor to kitchen ' +
            'without touching paper.',
        },
        options: [
          {
            label: {
              es: '¿Y la cocina que ve?',
              en: 'And what does the kitchen see?',
            },
            next: 'pedido-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'pedido-2': {
        text: {
          es:
            'La tarjeta completa en su pantalla: mesa, hora, platos y ' +
            'mis notas, en el ORDEN en que llegaron. Ernesto ya no ' +
            'adivina mi letra — no HAY letra. Y yo ya se si su tarjeta ' +
            'va verde o va roja antes de que me pregunte el cliente.',
          en:
            'The full card on their screen: table, time, dishes and my ' +
            'notes, in the ORDER they arrived. Ernesto no longer ' +
            'guesses my handwriting — there IS no handwriting. And I ' +
            'know if his card is green or red before the customer even ' +
            'asks me.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
      'antes-1': {
        text: {
          es:
            'Papelitos. PAPELITOS. Anotaba en una libreta, arrancaba la ' +
            'hoja, corria a la cocina, la pinchaba en un clavo y ' +
            'gritaba el pedido por encima de las ollas. Algunos se ' +
            'caian, otros se manchaban, y el de la mesa 6... el de la ' +
            'mesa 6 se perdia SIEMPRE.',
          en:
            'Paper slips. PAPER SLIPS. I wrote in a notepad, tore the ' +
            'page, ran to the kitchen, pinned it on a nail and shouted ' +
            'the order over the pots. Some fell, some got stained, and ' +
            'table 6’s... table 6’s ALWAYS got lost.',
        },
        options: [
          {
            label: {
              es: '¿Y que pasaba con la mesa?',
              en: 'And what happened to the table?',
            },
            next: 'antes-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'antes-2': {
        text: {
          es:
            'La mesa esperaba, preguntaba, se molestaba... y yo volvia ' +
            'a la cocina a gritar el pedido OTRA vez. Terminaba el ' +
            'turno ronca y con las piernas molidas. Si quieres ver ese ' +
            'mundo, cruza la grieta del muro: alla sigue Julio ' +
            'corriendo con sus papelitos.',
          en:
            'The table waited, asked, got upset... and I went back to ' +
            'the kitchen to shout the order AGAIN. I ended every shift ' +
            'hoarse with my legs ground down. If you want to see that ' +
            'world, cross the rift on the wall: Julio is still there ' +
            'running with his paper slips.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Voy a cruzar', en: 'I will cross over' },
            next: 'bye',
          },
        ],
      },
      'obs-1': {
        text: {
          es:
            'El cliente dice "sin cebolla", "aji aparte", "termino tres ' +
            'cuartos" — y yo lo ESCRIBO en la comanda. Llega textual a ' +
            'la pantalla de cocina, pegado al plato. Antes esas cosas ' +
            'viajaban en mi memoria, y mi memoria a mitad de turno ya ' +
            'no viaja bien.',
          en:
            'The customer says "no onion", "chili on the side", ' +
            '"medium-well" — and I TYPE it on the order. It lands ' +
            'verbatim on the kitchen screen, attached to the dish. That ' +
            'used to travel in my memory, and mid-shift my memory does ' +
            'not travel well.',
        },
        options: [
          {
            label: {
              es: '¿Y la cocina lo respeta?',
              en: 'And does the kitchen honour it?',
            },
            next: 'obs-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'obs-2': {
        text: {
          es:
            'Lo respeta porque lo LEE — negro sobre pantalla, no letra ' +
            'apurada en papel mojado. Los platos devueltos bajaron un ' +
            'monton. El dia que un "sin cebolla" vuelve CON cebolla, la ' +
            'discusion dura dos segundos: la comanda esta ahi, escrita.',
          en:
            'It honours it because it READS it — sharp on a screen, ' +
            'not rushed handwriting on damp paper. Returned dishes ' +
            'dropped a ton. The day a "no onion" comes back WITH onion, ' +
            'the argument lasts two seconds: the order is right there, ' +
            'in writing.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
      'propina-1': {
        text: {
          es:
            'Piensalo: la comanda llega al instante, la cocina prioriza ' +
            'con su cronometro y el plato sale antes. La mesa come ' +
            'antes, paga antes y se va contenta — y entra la siguiente. ' +
            'Mas rotacion, mejor atencion... y si, mejor propina. El ' +
            'sistema tambien trabaja para MI bolsillo.',
          en:
            'Think about it: the order arrives instantly, the kitchen ' +
            'prioritises with its timer and the dish comes out sooner. ' +
            'The table eats sooner, pays sooner and leaves happy — and ' +
            'the next one sits down. More turnover, better service... ' +
            'and yes, better tips. The system works for MY pocket too.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy. Gracias', en: 'I will go. Thanks' },
            next: 'bye',
          },
        ],
      },
    },
  }),

  ernesto: defineDialog({
    name: { es: 'Chef Ernesto Ramos', en: 'Chef Ernesto Ramos' },
    chatter: [
      {
        es: 'Tarjeta nueva: mesa 4, ceviche y lomo. Marchando.',
        en: 'New card: table 4, ceviche and lomo. Coming up.',
      },
      {
        es: 'Rojo en pantalla = mesa esperando. Esa sale primero.',
        en: 'Red on screen = a table waiting. That one goes out first.',
      },
      {
        es: 'Ya no adivino letras. Leo comandas.',
        en: 'I no longer guess handwriting. I read orders.',
      },
      {
        es: '"Sin cebolla" dice aqui. Sin cebolla sale.',
        en: '"No onion" it says here. No onion it goes.',
      },
      {
        es: 'La impresora canta un KOT y la linea se mueve.',
        en: 'The printer sings a KOT and the line moves.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Ernesto, jefe de cocina. Esa pantalla de ahi es mi ' +
            'directora de orquesta: cada comanda del salon entra como ' +
            'una tarjeta, con su hora y su cronometro. ¿Que quieres ' +
            'saber?',
          en:
            'Ernesto, head cook. That screen over there is my ' +
            'conductor: every order from the floor comes in as a card, ' +
            'with its time and its timer. What do you want to know?',
        },
        options: [
          {
            label: {
              es: '¿Como funciona la pantalla?',
              en: 'How does the screen work?',
            },
            next: 'kds-1',
          },
          {
            label: {
              es: '¿Como era antes?',
              en: 'What was it like before?',
            },
            next: 'antes-1',
          },
          {
            label: { es: 'Hay mas temas, ¿no?', en: 'There is more, right?' },
            next: 'hub2',
          },
          {
            label: { es: 'Nada, sigue cocinando', en: 'Nothing, keep cooking' },
            next: null,
          },
        ],
      },
      hub2: {
        text: {
          es:
            'Te puedo contar del "para servir" — el final feliz de cada ' +
            'tarjeta — o de lo que cocinamos aqui, que tambien tiene su ' +
            'ciencia.',
          en:
            'I can tell you about "ready to serve" — the happy ending ' +
            'of every card — or about what we cook here, which has its ' +
            'own science too.',
        },
        options: [
          {
            label: {
              es: '¿Que es el "para servir"?',
              en: 'What is "ready to serve"?',
            },
            next: 'servir-1',
          },
          {
            label: {
              es: '¿Que se cocina aqui?',
              en: 'What do you cook here?',
            },
            next: 'carta-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Mira la pantalla un rato y vas a entender la cocina sin ' +
            'que yo hable. Y no me toques el pase, que ahi los platos ' +
            'ya van con destino.',
          en:
            'Watch the screen a while and you will understand the ' +
            'kitchen without me talking. And do not touch the pass — ' +
            'those dishes already have a destination.',
        },
        options: [{ label: { es: 'Hasta luego', en: 'See you' }, next: null }],
      },

      'kds-1': {
        text: {
          es:
            'Cada tarjeta es una comanda: mesa, hora, platos y las ' +
            'observaciones de la moza, TEXTUALES. Entran en orden de ' +
            'llegada, como debe ser. Yo cocino mirando la pantalla igual ' +
            'que un piloto mira sus instrumentos.',
          en:
            'Each card is an order: table, time, dishes and the ' +
            'waitress’s notes, VERBATIM. They come in arrival ' +
            'order, as they should. I cook watching the screen the way ' +
            'a pilot watches his instruments.',
        },
        options: [
          {
            label: {
              es: '¿Y el cronometro de colores?',
              en: 'And the colour timer?',
            },
            next: 'kds-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'kds-2': {
        text: {
          es:
            'Verde: recien llegada, todo bien. Ambar: se esta ' +
            'poniendo vieja. ROJO: esa mesa lleva demasiado esperando — ' +
            'y sale primero, sin discusion. Antes "¿cual va primero?" ' +
            'era un griterio; ahora lo decide un color.',
          en:
            'Green: just arrived, all good. Amber: it is getting old. ' +
            'RED: that table has waited too long — and it goes out ' +
            'first, no argument. "Which one goes first?" used to be a ' +
            'shouting match; now a colour decides it.',
        },
        options: [
          {
            label: {
              es: '¿Y la impresora de cocina?',
              en: 'And the kitchen printer?',
            },
            next: 'kds-3',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'kds-3': {
        text: {
          es:
            'El KOT — el ticket de cocina. La misma comanda de la ' +
            'pantalla sale en papelito termico para la estacion que lo ' +
            'necesita: frios, calientes, bar. La pantalla ordena la ' +
            'batalla; el KOT viaja con el plato. Cinturon Y tirantes.',
          en:
            'The KOT — the kitchen ticket. The same order on the ' +
            'screen prints as a small thermal slip for whichever ' +
            'station needs it: cold, hot, bar. The screen runs the ' +
            'battle; the KOT travels with the dish. Belt AND braces.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
      'antes-1': {
        text: {
          es:
            'Un clavo con papelitos pinchados y la moza gritando por ' +
            'encima de las ollas. ¿Esa letra dice dos ceviches o dos ' +
            'cevichitos? ¿Esta comanda llego antes que aquella? Nadie ' +
            'sabia. Los platos salian mal y la culpa volaba de la ' +
            'cocina al salon y de vuelta.',
          en:
            'A nail with paper slips pinned on it and the waitress ' +
            'shouting over the pots. Does that handwriting say two ' +
            'ceviches or two small ceviches? Did this order arrive ' +
            'before that one? Nobody knew. Dishes went out wrong and ' +
            'the blame flew kitchen-to-floor and back.',
        },
        options: [
          {
            label: {
              es: '¿Y el sistema arreglo eso?',
              en: 'And the system fixed that?',
            },
            next: 'antes-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'antes-2': {
        text: {
          es:
            'De raiz: la comanda llega ESCRITA, con hora, y no se ' +
            'pierde ni se mancha ni se vuela. El "yo te lo grite" y el ' +
            '"a mi no me llego" se acabaron el mismo dia. Ahora la ' +
            'unica pelea de esta cocina es con el punto del arroz.',
          en:
            'At the root: the order arrives WRITTEN, timestamped, and ' +
            'it cannot get lost, stained or blown away. "I shouted it ' +
            'to you" and "it never reached me" died the same day. The ' +
            'only fight left in this kitchen is with the rice.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
      'servir-1': {
        text: {
          es:
            'Cuando el plato esta emplatado, toco "Listo" en la tarjeta ' +
            'y pasa a PARA SERVIR: la moza lo ve al instante en su ' +
            'tablet y viene a buscarlo. El plato no se enfria en el ' +
            'pase esperando que alguien lo descubra. Suena simple; ' +
            'cambia el servicio entero.',
          en:
            'When the dish is plated, I tap "Done" on the card and it ' +
            'flips to READY TO SERVE: the waitress sees it instantly on ' +
            'her tablet and comes for it. The dish does not go cold on ' +
            'the pass waiting to be discovered. Sounds simple; it ' +
            'changes the whole service.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
      'carta-1': {
        text: {
          es:
            'Cocina peruana con orgullo: ceviche fresco del dia, lomo ' +
            'saltado con su fuego alto, aji de gallina los jueves. Y en ' +
            'cada mesa su Inca Kola, por supuesto. El sistema sera de ' +
            'Pablo, pero el sabor es NUESTRO — cada quien su oficio.',
          en:
            'Peruvian cooking with pride: fresh ceviche of the day, ' +
            'lomo saltado on high flame, aji de gallina on Thursdays. ' +
            'And an Inca Kola on every table, of course. The system may ' +
            'be Pablo’s, but the flavour is OURS — to each their ' +
            'craft.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Se me antojo. Me voy', en: 'Now I am hungry. Bye' },
            next: 'bye',
          },
        ],
      },
    },
  }),

  rosa: defineDialog({
    name: { es: 'Rosa Palomino', en: 'Rosa Palomino' },
    chatter: [
      {
        es: 'Cobro, un clic, y la boleta sale impresa Y enviada.',
        en: 'I charge, one click, and the receipt prints AND sends itself.',
      },
      {
        es: '¿Efectivo, tarjeta o Yape? Todo entra igual de facil.',
        en: 'Cash, card or Yape? All equally easy.',
      },
      {
        es: 'SUNAT la acepta antes de que el cliente guarde el vuelto.',
        en: 'SUNAT accepts it before the customer pockets the change.',
      },
      {
        es: 'El cierre de caja se cuadra SOLO. Yo solo lo miro.',
        en: 'The till closes ITSELF. I just watch it.',
      },
      {
        es: 'Antes llenaba boletas a mano, con papel carbon. A MANO.',
        en: 'I used to fill receipts by hand, with carbon paper. BY HAND.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Rosa, cajera — la del terminal navy. Aqui termina cada ' +
            'visita: el cobro, la boleta y el envio a SUNAT, todo en un ' +
            'gesto. ¿Que quieres saber?',
          en:
            'Rosa, cashier — the one at the navy terminal. Every visit ' +
            'ends here: the charge, the receipt and the SUNAT filing, ' +
            'all in one gesture. What do you want to know?',
        },
        options: [
          {
            label: {
              es: '¿Como cobras una mesa?',
              en: 'How do you charge a table?',
            },
            next: 'cobro-1',
          },
          {
            label: {
              es: '¿Que pasa con el cierre?',
              en: 'What about closing time?',
            },
            next: 'cierre-1',
          },
          {
            label: { es: 'Hay mas temas, ¿no?', en: 'There is more, right?' },
            next: 'hub2',
          },
          {
            label: { es: 'Nada, sigue con lo tuyo', en: 'Nothing, carry on' },
            next: null,
          },
        ],
      },
      hub2: {
        text: {
          es:
            'Falta lo importante: que es SUNAT y por que esa palabrita ' +
            'quitaba el sueño en este pais.',
          en:
            'The important part is left: what SUNAT is and why that ' +
            'little word kept people awake in this country.',
        },
        options: [
          {
            label: {
              es: 'Explicame lo de SUNAT',
              en: 'Explain the SUNAT thing',
            },
            next: 'sunat-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Dale E a la impresora termica y emite una boleta de ' +
            'prueba: vas a ver el ticket salir con su QR y su sello de ' +
            'SUNAT. Es mi sonido favorito del dia.',
          en:
            'Press E on the thermal printer and issue a test receipt: ' +
            'you will see the ticket come out with its QR and its SUNAT ' +
            'stamp. It is my favourite sound of the day.',
        },
        options: [{ label: { es: 'Hasta luego', en: 'See you' }, next: null }],
      },

      'cobro-1': {
        text: {
          es:
            'La cuenta de la mesa ya viene armada del sistema — lo que ' +
            'pidieron, tal cual. Elijo el medio de pago: efectivo, ' +
            'tarjeta o Yape. Un clic en "Emitir boleta" y pasan TRES ' +
            'cosas a la vez: se imprime, se guarda y se va a SUNAT.',
          en:
            'The table’s bill comes pre-built from the system — ' +
            'exactly what they ordered. I pick the payment method: ' +
            'cash, card or Yape. One click on "Issue receipt" and THREE ' +
            'things happen at once: it prints, it saves and it flies to ' +
            'SUNAT.',
        },
        options: [
          {
            label: {
              es: '¿Y antes del sistema?',
              en: 'And before the system?',
            },
            next: 'cobro-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'cobro-2': {
        text: {
          es:
            'Talonario fisico con papel carbon: boleta a MANO, con el ' +
            'cliente esperando y la fila creciendo. Numeros ilegibles, ' +
            'series que saltaban, y el IGV calculado con calculadora. ' +
            'Cada boleta era un tramite; ahora es un clic.',
          en:
            'A physical receipt book with carbon paper: receipts BY ' +
            'HAND, with the customer waiting and the queue growing. ' +
            'Illegible numbers, skipped series, and the tax worked out ' +
            'on a calculator. Every receipt was a chore; now it is a ' +
            'click.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
      'cierre-1': {
        text: {
          es:
            'Antes el cierre era mi pesadilla: sumar boletas, contar el ' +
            'cajon, perseguir un sol perdido hasta medianoche. Ahora el ' +
            'sistema suma cada venta al momento: al cerrar, el reporte ' +
            'ya esta cuadrado. Yo cuento el efectivo y confirmo. Quince ' +
            'minutos, no tres horas.',
          en:
            'Closing used to be my nightmare: adding receipts, counting ' +
            'the drawer, chasing a lost sol until midnight. Now the ' +
            'system tallies every sale as it happens: at closing, the ' +
            'report is already balanced. I count the cash and confirm. ' +
            'Fifteen minutes, not three hours.',
        },
        options: [
          {
            label: {
              es: '¿Y Don Ricardo lo ve?',
              en: 'And does Don Ricardo see it?',
            },
            next: 'cierre-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'cierre-2': {
        text: {
          es:
            'Desde el celular, este local y los otros dos: ventas del ' +
            'dia, boletas emitidas, todo en vivo. Es la gracia de que ' +
            'el sistema viva en la nube — la caja de cada local reporta ' +
            'sola. Ya nadie llama a preguntar "¿como vamos?": lo MIRAN.',
          en:
            'From his phone, this place and the other two: the day’s ' +
            'sales, receipts issued, all live. That is the point of the ' +
            'system living in the cloud — each till reports on its own. ' +
            'Nobody calls asking "how are we doing?" anymore: they LOOK.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
      'sunat-1': {
        text: {
          es:
            'SUNAT es el fisco peruano, y la boleta electronica es ' +
            'OBLIGATORIA: cada venta tiene que declararse, con su serie ' +
            '— B001, la nuestra — su IGV del 18% y su codigo QR. El que ' +
            'factura mal o tarde, multa. Y las multas de SUNAT no son ' +
            'cuento.',
          en:
            'SUNAT is Peru’s tax authority, and the electronic ' +
            'receipt is MANDATORY: every sale must be filed, with its ' +
            'series — B001, ours — its 18% IGV tax and its QR code. ' +
            'File wrong or late, and you get fined. And SUNAT fines are ' +
            'no joke.',
        },
        options: [
          {
            label: {
              es: '¿Y el sistema como cumple?',
              en: 'And how does the system comply?',
            },
            next: 'sunat-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'sunat-2': {
        text: {
          es:
            'Directo: la boleta sale del sistema HACIA SUNAT en el ' +
            'momento, y vuelve aceptada con su constancia. El QR del ' +
            'ticket la deja consultar a cualquiera. Pablo integro eso ' +
            'cuando era el unico dev — y es la funcion que mas paga: ' +
            'cero multas, cero sustos, boletas ilimitadas.',
          en:
            'Directly: the receipt leaves the system FOR SUNAT the ' +
            'moment it is issued, and comes back accepted with its ' +
            'proof. The QR on the ticket lets anyone verify it. Pablo ' +
            'integrated that while he was the only dev — and it is the ' +
            'feature that pays the most: zero fines, zero scares, ' +
            'unlimited receipts.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: {
              es: 'Voy a probar la termica',
              en: 'I will try the printer',
            },
            next: 'bye',
          },
        ],
      },
    },
  }),

  andrea: defineDialog({
    name: { es: 'Andrea Chavez', en: 'Andrea Chavez' },
    chatter: [
      {
        es: 'Pedi y a los diez minutos ya estaba comiendo. DIEZ.',
        en: 'I ordered and ten minutes later I was eating. TEN.',
      },
      {
        es: 'La boleta me llego con QR y todo. Al toque.',
        en: 'My receipt came with a QR and everything. Right away.',
      },
      {
        es: 'Este ceviche esta en su punto. En su PUNTO.',
        en: 'This ceviche is just right. JUST right.',
      },
      {
        es: 'Aca nadie grita. En otros sitios el pedido se grita.',
        en: 'Nobody shouts here. Elsewhere they shout the orders.',
      },
      {
        es: 'Se nota que aqui todo esta conectado.',
        en: 'You can tell everything here is connected.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            '¿Yo? Andrea, clienta de toda la vida — bueno, de todos los ' +
            'viernes. Vengo por el ceviche y me quedo por lo rapido que ' +
            'atienden. ¿Quieres saber como se come aqui?',
          en:
            'Me? Andrea, lifelong customer — well, every-Friday ' +
            'customer. I come for the ceviche and stay for how fast the ' +
            'service is. Want to know what eating here is like?',
        },
        options: [
          {
            label: {
              es: '¿Que pediste hoy?',
              en: 'What did you order today?',
            },
            next: 'pedido-1',
          },
          {
            label: {
              es: '¿Se nota el sistema desde la mesa?',
              en: 'Can you feel the system from the table?',
            },
            next: 'sistema-1',
          },
          {
            label: { es: 'Buen provecho', en: 'Enjoy your meal' },
            next: null,
          },
        ],
      },
      bye: {
        text: {
          es:
            'Pide el lomo saltado y una Inca Kola bien helada — y fijate ' +
            'en el ticket cuando pagues: trae un QR chiquito que es pura ' +
            'magia legal.',
          en:
            'Order the lomo saltado and an ice-cold Inca Kola — and ' +
            'check the ticket when you pay: it carries a tiny QR that is ' +
            'pure legal magic.',
        },
        options: [{ label: { es: 'Hasta luego', en: 'See you' }, next: null }],
      },

      'pedido-1': {
        text: {
          es:
            'Ceviche y una Inca Kola. Milagros lo anoto en su tablet ' +
            'ahi mismo, sin papelito, y cuando iba llegando a la barra ' +
            'ya se escuchaba la cocina trabajando MI pedido. A los diez ' +
            'minutos, plato en mesa.',
          en:
            'Ceviche and an Inca Kola. Milagros typed it on her tablet ' +
            'right there, no paper slip, and by the time she reached ' +
            'the bar you could hear the kitchen working MY order. Ten ' +
            'minutes later, dish on the table.',
        },
        options: [
          {
            label: {
              es: '¿Y al pagar?',
              en: 'And when paying?',
            },
            next: 'pedido-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'pedido-2': {
        text: {
          es:
            'Pague con Yape y la boleta salio impresa AL TOQUE, con su ' +
            'QR de SUNAT. Nada de esperar la cuenta veinte minutos ' +
            'mirando al techo. En otros restaurantes la sobremesa la ' +
            'pone la cocina; aqui la pongo YO.',
          en:
            'I paid with Yape and the receipt printed INSTANTLY, with ' +
            'its SUNAT QR. No twenty-minute wait for the bill staring ' +
            'at the ceiling. In other restaurants the kitchen decides ' +
            'how long you linger; here I decide.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Buen provecho', en: 'Enjoy your meal' },
            next: 'bye',
          },
        ],
      },
      'sistema-1': {
        text: {
          es:
            'Se nota sin verlo: nadie grita, nadie corre con papelitos, ' +
            'los platos llegan bien y RAPIDO. La moza mira su tablet y ' +
            'sabe cuando esta listo lo mio. Todo fluye como si el ' +
            'restaurante entero se hubiera puesto de acuerdo.',
          en:
            'You feel it without seeing it: nobody shouts, nobody runs ' +
            'with paper slips, dishes arrive right and FAST. The ' +
            'waitress glances at her tablet and knows when mine is ' +
            'ready. Everything flows as if the whole restaurant had ' +
            'agreed on it.',
        },
        options: [
          {
            label: {
              es: '¿Y eso antes no pasaba?',
              en: 'And it was not like that before?',
            },
            next: 'sistema-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'sistema-2': {
        text: {
          es:
            'Uy, no. Yo vengo de años: antes pedias y a rezar — que la ' +
            'comanda llegara, que llegara BIEN, que la boleta no ' +
            'tardara otra era geologica. Un viernes me trajeron el ' +
            'plato de otra mesa dos veces. DOS. Hoy eso no pasa ni de ' +
            'chiste.',
          en:
            'Oh no. I go way back: you used to order and pray — that ' +
            'the order arrived, that it arrived RIGHT, that the receipt ' +
            'did not take a geological era. One Friday I got another ' +
            'table’s dish twice. TWICE. Today that does not happen ' +
            'even as a joke.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Buen provecho', en: 'Enjoy your meal' },
            next: 'bye',
          },
        ],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
