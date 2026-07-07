/**
 * @module dialogs/dibal-pasado (engine)
 * @description Arboles de dialogo de la sala 4 pasado: el restaurante
 *   antes de Dibal (2018). El sistema manual desastroso: comandas en
 *   papelitos que se pierden entre salon y cocina, el mozo gritando los
 *   pedidos, la cocina descifrando letras y la caja llenando boletas a
 *   mano con papel carbon, con el susto de SUNAT encima. 3 NPCs
 *   frustrados (canon, informe 11 — nombres distintos: "el equipo de
 *   antes"): Julio Vargas (mozo ronco), Doña Carmen Flores (cocinera
 *   descifrando papelitos) y Elena Torres (cajera del talonario).
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const DIBAL_PASADO_DIALOGS = {
  julio: defineDialog({
    name: { es: 'Julio Vargas', en: 'Julio Vargas' },
    chatter: [
      {
        es: '¡MESA 4, DOS LOMOS! ¿Me oyeron? ¡DOS!',
        en: 'TABLE 4, TWO LOMOS! Did you hear me? TWO!',
      },
      {
        es: '¿Donde esta la comanda de la 6? ¿DONDE?',
        en: 'Where is table 6’s order slip? WHERE?',
      },
      {
        es: 'Otra vez ronco. Otro turno, otra voz perdida.',
        en: 'Hoarse again. Another shift, another lost voice.',
      },
      {
        es: 'Este papelito estaba aqui hace un segundo...',
        en: 'That slip was right here a second ago...',
      },
      {
        es: 'La cocina saco pollo. Yo pedi pescado. PESCADO.',
        en: 'The kitchen sent out chicken. I asked for fish. FISH.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Julio, mozo — y pregonero, y mensajero, y detective de ' +
            'papelitos perdidos. Todo a la vez, todo corriendo. ' +
            'Pregunta rapido que tengo tres mesas esperando.',
          en:
            'Julio, waiter — and town crier, and courier, and lost-slip ' +
            'detective. All at once, all running. Ask quickly, I have ' +
            'three tables waiting.',
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
              es: '¿Que le paso a la mesa 6?',
              en: 'What happened to table 6?',
            },
            next: 'mesa6-1',
          },
          {
            label: { es: 'Te dejo trabajar', en: 'I will let you work' },
            next: null,
          },
        ],
      },
      'pedido-1': {
        text: {
          es:
            'Anoto en la libreta, arranco la hoja, cruzo el salon ' +
            'esquivando sillas, pincho el papelito en el clavo del pase ' +
            'y GRITO el pedido por si acaso — porque el papelito a ' +
            'veces vuela, a veces se mancha y a veces sencillamente ' +
            'desaparece.',
          en:
            'I write it in the notepad, tear the page, cross the floor ' +
            'dodging chairs, pin the slip on the pass nail and SHOUT ' +
            'the order just in case — because the slip sometimes flies ' +
            'off, sometimes gets stained and sometimes simply ' +
            'vanishes.',
        },
        options: [
          {
            label: {
              es: '¿Y el grito funciona?',
              en: 'And does the shouting work?',
            },
            next: 'pedido-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'pedido-2': {
        text: {
          es:
            'A medias: la cocina oye "lomo" donde dije "pollo" y saca ' +
            'lo que entendio. Despues el cliente reclama, yo reclamo, ' +
            'la cocina reclama... y nadie tiene pruebas, porque el ' +
            'papelito — SI aparece — dice otra cosa distinta de lo que ' +
            'grite. Termino cada turno ronco y peleado.',
          en:
            'Halfway: the kitchen hears "lomo" where I said "pollo" and ' +
            'cooks what it understood. Then the customer complains, I ' +
            'complain, the kitchen complains... and nobody has proof, ' +
            'because the slip — IF it turns up — says something ' +
            'different from what I shouted. I end every shift hoarse ' +
            'and at war.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: {
              es: '¿Y nadie piensa arreglarlo?',
              en: 'Is nobody going to fix this?',
            },
            next: 'deseo-1',
          },
        ],
      },
      'mesa6-1': {
        text: {
          es:
            'La mesa 6 pidio hace CUARENTA minutos. La comanda salio de ' +
            'mi libreta, cruzo el salon en mi mano... y en algun punto ' +
            'entre esa mesa y la cocina, desaparecio. Ahi anda, tirada ' +
            'en el piso o pegada a la suela de alguien. Y la señora de ' +
            'la 6 preguntandome a MI.',
          en:
            'Table 6 ordered FORTY minutes ago. The slip left my ' +
            'notepad, crossed the floor in my hand... and somewhere ' +
            'between that table and the kitchen, it vanished. It is out ' +
            'there, lying on the floor or stuck to someone’s shoe. ' +
            'And the lady at table 6 keeps asking ME.',
        },
        options: [
          {
            label: {
              es: '¿Y ahora que haces?',
              en: 'So what do you do now?',
            },
            next: 'mesa6-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'mesa6-2': {
        text: {
          es:
            'Volver a tomar el pedido, pedir disculpas, regalar la ' +
            'gaseosa y REZAR para que esta vez llegue. Si quieres ' +
            'ayudar, sigue ese papelito que anda por el piso — asi ' +
            'termina siempre la historia. Dicen que van a contratar a ' +
            'un muchacho de sistemas... ojala sea verdad.',
          en:
            'Take the order again, apologise, comp the soda and PRAY ' +
            'it arrives this time. If you want to help, follow that ' +
            'slip lying on the floor — that is how the story always ' +
            'ends. They say they are hiring a systems kid... I hope it ' +
            'is true.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Suerte con la 6', en: 'Good luck with table 6' },
            next: null,
          },
        ],
      },
      'deseo-1': {
        text: {
          es:
            'Yo sueño con algo simple: que lo que anoto en la mesa ' +
            'aparezca SOLO en la cocina, escrito claro, sin que yo ' +
            'corra ni grite. Que la mesa 6 coma lo que pidio. No pido ' +
            'magia... ¿o si? Cruza de vuelta por la grieta y me ' +
            'cuentas.',
          en:
            'I dream of something simple: whatever I write at the ' +
            'table just APPEARS in the kitchen, clearly written, ' +
            'without me running or shouting. Table 6 eating what it ' +
            'ordered. I am not asking for magic... or am I? Cross back ' +
            'through the rift and tell me.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Te vas a sorprender', en: 'You will be surprised' },
            next: null,
          },
        ],
      },
    },
  }),

  carmen: defineDialog({
    name: { es: 'Doña Carmen Flores', en: 'Doña Carmen Flores' },
    chatter: [
      {
        es: '¿Dos ceviches o dos cevichitos? ¿QUE dice aqui?',
        en: 'Two ceviches or two small ceviches? WHAT does this say?',
      },
      {
        es: 'Tres platos devueltos hoy. TRES. Y no es mi sazon.',
        en: 'Three dishes sent back today. THREE. And it is not my cooking.',
      },
      {
        es: 'Este papelito tiene grasa encima del pedido. Genial.',
        en: 'This slip has grease right over the order. Wonderful.',
      },
      {
        es: '¿Esta comanda llego antes que aquella? Ni idea.',
        en: 'Did this order come before that one? No idea.',
      },
      {
        es: 'El clavo del pase ya no da abasto con tanto papel.',
        en: 'The pass nail cannot hold this much paper anymore.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Carmen Flores, cocinera — treinta años de sazon y ni un ' +
            'dia de paz con estos papelitos. Mire ese clavo: eso es mi ' +
            '"sistema de comandas". Pregunte, pero cortito.',
          en:
            'Carmen Flores, cook — thirty years of seasoning and not ' +
            'one day of peace with these paper slips. Look at that ' +
            'nail: that is my "order system". Ask away, but keep it ' +
            'short.',
        },
        options: [
          {
            label: {
              es: '¿Que dice ese papelito?',
              en: 'What does that slip say?',
            },
            next: 'letra-1',
          },
          {
            label: {
              es: '¿Como decides que cocinar primero?',
              en: 'How do you pick what to cook first?',
            },
            next: 'orden-1',
          },
          {
            label: { es: 'La dejo cocinar', en: 'I will let you cook' },
            next: null,
          },
        ],
      },
      'letra-1': {
        text: {
          es:
            'Ese es el problema: NO SE. Julio escribe corriendo, el ' +
            'papel se mancha con la grasa del pase y a mi me toca ' +
            'ADIVINAR. ¿Dos ceviches o dos cevichitos? ¿"s/cebolla" es ' +
            'sin cebolla o con cebolla? Hoy ya devolvi tres platos por ' +
            'adivinar mal.',
          en:
            'That is the problem: I DO NOT KNOW. Julio writes on the ' +
            'run, the paper gets stained with pass grease and I am ' +
            'left GUESSING. Two ceviches or two small ones? Does ' +
            '"n/onion" mean no onion or extra onion? Three dishes came ' +
            'back today because I guessed wrong.',
        },
        options: [
          {
            label: {
              es: '¿Y quien paga esos platos?',
              en: 'And who pays for those dishes?',
            },
            next: 'letra-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'letra-2': {
        text: {
          es:
            'El restaurante — o sea, todos. Comida buena al tacho, ' +
            'cliente molesto, y la culpa rebotando entre el salon y mi ' +
            'cocina. Yo no necesito mas manos: necesito LEER lo que la ' +
            'mesa pidio. Asi de humilde es mi sueño.',
          en:
            'The restaurant — meaning all of us. Good food in the bin, ' +
            'an upset customer, and the blame bouncing between the ' +
            'floor and my kitchen. I do not need more hands: I need to ' +
            'READ what the table ordered. That is how humble my dream ' +
            'is.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Ojala se cumpla', en: 'May it come true' },
            next: null,
          },
        ],
      },
      'orden-1': {
        text: {
          es:
            'A ojo y a memoria: el papelito de mas abajo DEBERIA ser ' +
            'el mas viejo... si nadie los reacomodo. ¿Cual mesa lleva ' +
            'mas esperando? Ni idea — los papelitos no tienen hora. A ' +
            'veces una mesa nueva come antes que una que llego hace ' +
            'media hora.',
          en:
            'By eye and by memory: the slip at the bottom SHOULD be ' +
            'the oldest... if nobody reshuffled them. Which table has ' +
            'waited longest? No clue — slips carry no time. Sometimes ' +
            'a new table eats before one that arrived half an hour ' +
            'ago.',
        },
        options: [
          {
            label: {
              es: '¿Y eso como termina?',
              en: 'And how does that end?',
            },
            next: 'orden-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'orden-2': {
        text: {
          es:
            'Con Julio ronco pidiendome milagros y la señora de la 6 ' +
            'parada en la puerta de MI cocina. Un dia de estos alguien ' +
            'va a inventar una pantalla que ponga las comandas en ' +
            'orden, con su hora y su letra de imprenta. Ese dia yo ' +
            'cocino en paz.',
          en:
            'With Julio hoarse begging me for miracles and the lady ' +
            'from table 6 standing at MY kitchen door. One of these ' +
            'days somebody will invent a screen that lines the orders ' +
            'up, with their time and printed letters. That day I cook ' +
            'in peace.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Ese dia llega', en: 'That day is coming' },
            next: null,
          },
        ],
      },
    },
  }),

  elena: defineDialog({
    name: { es: 'Elena Torres', en: 'Elena Torres' },
    chatter: [
      {
        es: 'Boleta numero... ¿en que numero iba? Ay no.',
        en: 'Receipt number... which number was I on? Oh no.',
      },
      {
        es: 'El carbon me mancho las manos otra vez.',
        en: 'The carbon paper stained my hands again.',
      },
      {
        es: 'Falta S/40 en el cajon. ¿O sobran? Ya ni se.',
        en: 'The drawer is S/40 short. Or over? I cannot even tell.',
      },
      {
        es: 'IGV del 18%... calculadora, no me falles ahora.',
        en: '18% IGV... calculator, do not fail me now.',
      },
      {
        es: 'Como venga SUNAT a revisar, yo me muero aqui mismo.',
        en: 'If SUNAT comes to audit, I will die right here.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Elena, cajera — la del talonario y el papel carbon. Cada ' +
            'boleta la lleno A MANO, con la fila mirandome, y el cuadre ' +
            'de la caja me tiene aqui hasta medianoche. Pregunte ' +
            'nomas... total, la calculadora no se va a sumar sola.',
          en:
            'Elena, cashier — receipt book and carbon paper. I fill ' +
            'every receipt BY HAND with the queue staring at me, and ' +
            'balancing the till keeps me here until midnight. Ask away ' +
            '— the calculator will not add itself anyway.',
        },
        options: [
          {
            label: {
              es: '¿Como emites una boleta?',
              en: 'How do you issue a receipt?',
            },
            next: 'boleta-1',
          },
          {
            label: {
              es: '¿Que es eso de SUNAT?',
              en: 'What is this SUNAT thing?',
            },
            next: 'sunat-1',
          },
          {
            label: { es: 'La dejo trabajar', en: 'I will let you work' },
            next: null,
          },
        ],
      },
      'boleta-1': {
        text: {
          es:
            'Talonario, lapicero y papel carbon: escribo cada plato, ' +
            'sumo a calculadora, calculo el IGV del 18% a mano y firmo. ' +
            'Tres minutos por boleta SI no me equivoco — y con la fila ' +
            'creciendo, me equivoco. Entonces: boleta anulada, y a ' +
            'empezar de nuevo.',
          en:
            'Receipt book, pen and carbon paper: I write each dish, ' +
            'add it up on the calculator, work out the 18% IGV by hand ' +
            'and sign. Three minutes per receipt IF I make no mistakes ' +
            '— and with the queue growing, I make mistakes. Then: void ' +
            'the receipt, start over.',
        },
        options: [
          {
            label: {
              es: '¿Y el cierre de caja?',
              en: 'And closing the till?',
            },
            next: 'boleta-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'boleta-2': {
        text: {
          es:
            'Medianoche, todos los dias: sumar boleta por boleta, ' +
            'contar el cajon y perseguir la diferencia. Hoy faltan ' +
            'S/40 — ahi esta el post-it. ¿Se traspapelo una boleta? ' +
            '¿Di mal un vuelto? Nunca lo sabre. El cajon guarda ' +
            'billetes, pero no guarda MEMORIA.',
          en:
            'Midnight, every single day: adding receipt by receipt, ' +
            'counting the drawer and chasing the difference. Today it ' +
            'is S/40 short — there is the sticky note. Did a receipt ' +
            'get misplaced? Did I give wrong change? I will never ' +
            'know. The drawer keeps bills, but it keeps no MEMORY.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: {
              es: '¿Y nadie ve una salida?',
              en: 'Does nobody see a way out?',
            },
            next: 'deseo-1',
          },
        ],
      },
      'sunat-1': {
        text: {
          es:
            'El fisco, niño. SUNAT exige que cada venta quede ' +
            'declarada con su boleta, su serie y su impuesto — y ' +
            'multa al que se equivoca. Yo hago TODO a mano: si un ' +
            'numero me baila, la multa no le llega a mi talonario... ' +
            'le llega al negocio. Vivo con ese susto.',
          en:
            'The taxman, kid. SUNAT demands every sale be declared ' +
            'with its receipt, its series and its tax — and fines ' +
            'whoever slips. I do EVERYTHING by hand: if one digit ' +
            'dances on me, the fine does not hit my receipt book... it ' +
            'hits the business. I live with that fright.',
        },
        options: [
          {
            label: {
              es: '¿Y como se arreglaria?',
              en: 'And how would you fix it?',
            },
            next: 'deseo-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'deseo-1': {
        text: {
          es:
            'Dicen que ya existe: boletas que se emiten solas, se ' +
            'envian solas a SUNAT y vuelven aceptadas, con la caja ' +
            'cuadrandose en vivo. Suena a cuento... pero contrataron a ' +
            'un muchacho de sistemas, asi que cruce los dedos por mi. ' +
            'Y si viene del futuro: NO me cuente el final.',
          en:
            'They say it already exists: receipts that issue ' +
            'themselves, send themselves to SUNAT and come back ' +
            'accepted, with the till balancing live. Sounds like a ' +
            'fairy tale... but they hired a systems kid, so cross your ' +
            'fingers for me. And if you come from the future: do NOT ' +
            'spoil the ending.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'No prometo nada', en: 'No promises' },
            next: null,
          },
        ],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
