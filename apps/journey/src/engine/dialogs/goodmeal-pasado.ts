/**
 * @module dialogs/goodmeal-pasado (engine)
 * @description Arboles de dialogo de la sala 5 pasado: el cierre del
 *   local antes de GoodMeal (2021). Comida en perfecto estado yendo a
 *   la bolsa negra cada noche: nadie a quien darsela, plata pagada que
 *   no se recupera. 3 NPCs resignados (canon, informe 12 — decision del
 *   usuario: los 3): Rodrigo Caceres (encargado de cierre), Ignacia
 *   Muñoz (dependienta) y el Sr. Peña (dueño), que planta el deseo de
 *   "vender aunque sea barato lo que sobra" — la solucion que GoodMeal
 *   traera.
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const GOODMEAL_PASADO_DIALOGS = {
  rodrigo: defineDialog({
    name: { es: 'Rodrigo Caceres', en: 'Rodrigo Caceres' },
    chatter: [
      {
        es: 'Otra noche, otra media vitrina al tacho.',
        en: 'Another night, another half display case binned.',
      },
      {
        es: 'Esta perfecta. PERFECTA. Y va a la basura.',
        en: 'It is perfect. PERFECT. And it goes in the garbage.',
      },
      {
        es: 'Las bolsas de hoy pesan mas que las de ayer.',
        en: 'Tonight’s bags weigh more than yesterday’s.',
      },
      {
        es: 'No me mires asi, dona. No depende de mi.',
        en: 'Do not look at me like that, donut. It is not up to me.',
      },
      {
        es: 'Plata a la basura. Todos los dias lo mismo.',
        en: 'Money in the bin. Every single day the same.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Rodrigo, encargado del cierre — o sea, el que bota la ' +
            'comida. Cada noche a esta hora vacio la vitrina a la ' +
            'bolsa negra y saco todo a la puerta trasera. Pregunta ' +
            'rapido, que el camion pasa a las once.',
          en:
            'Rodrigo, closing manager — meaning, the one who bins the ' +
            'food. Every night around now I empty the display case ' +
            'into the black bag and haul it out the back door. Ask ' +
            'fast, the truck comes at eleven.',
        },
        options: [
          {
            label: {
              es: '¿Por que botas comida buena?',
              en: 'Why bin good food?',
            },
            next: 'bota-1',
          },
          {
            label: {
              es: '¿Cuanto se pierde por noche?',
              en: 'How much is lost per night?',
            },
            next: 'plata-1',
          },
          {
            label: { es: 'Te dejo cerrar', en: 'I will let you close' },
            next: null,
          },
        ],
      },
      'bota-1': {
        text: {
          es:
            'Porque manana no se puede vender: el pan de hoy ya no es ' +
            '"del dia", la vitrina tiene que amanecer llena de cosas ' +
            'frescas. Y a las diez de la noche no hay NADIE a quien ' +
            'venderle una dona. Asi que mirala bien... y a la bolsa.',
          en:
            'Because tomorrow it cannot be sold: today’s bread is no ' +
            'longer "fresh-baked", the case has to open full of new ' +
            'stock. And at ten at night there is NOBODY to sell a ' +
            'donut to. So take a good look at it... and into the bag.',
        },
        options: [
          {
            label: {
              es: '¿Y no hay otra salida?',
              en: 'Is there no other way out?',
            },
            next: 'bota-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'bota-2': {
        text: {
          es:
            'Yo no la conozco. Rebajar precios a ultima hora seria ' +
            'anunciarlo a gritos en la puerta — ¿y quien pasa por aca ' +
            'a esta hora? Si existiera una forma de avisarle a la ' +
            'gente "queda esto, a mitad de precio, ven a buscarlo"... ' +
            'otra cosa seria. Pero no existe.',
          en:
            'Not that I know of. Slashing prices at the last minute ' +
            'would mean shouting it at the door — and who walks past ' +
            'at this hour? If there were a way to tell people "this ' +
            'is left, half price, come get it"... it would be another ' +
            'story. But there is not.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: {
              es: 'Quizas algun dia exista',
              en: 'Maybe one day there will be',
            },
            next: null,
          },
        ],
      },
      'plata-1': {
        text: {
          es:
            'Mira el carro: bandejas de pan, donas glaseadas, pizza ' +
            'entera en porciones. Todo horneado HOY, todo pagado, ' +
            'todo perfecto. Facil un veinte por ciento de lo que ' +
            'producimos termina asi. El dueño saca la calculadora ' +
            'cada noche y le da lo mismo: perdida.',
          en:
            'Look at the cart: trays of bread, glazed donuts, a whole ' +
            'pizza in slices. All baked TODAY, all paid for, all ' +
            'perfect. Easily twenty percent of what we make ends like ' +
            'this. The owner runs the numbers every night and it ' +
            'comes out the same: loss.',
        },
        options: [
          {
            label: {
              es: '¿Y a ti que te provoca?',
              en: 'And how does it make you feel?',
            },
            next: 'plata-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'plata-2': {
        text: {
          es:
            'Rabia, la verdad. Yo esta pega la agarre porque me gusta ' +
            'la comida — y termino cada turno enterrandola en bolsas ' +
            'negras. Uno se acostumbra a casi todo... a esto no. Si ' +
            'algun dia inventan algo para salvarla, yo firmo primero.',
          en:
            'Anger, honestly. I took this job because I love food — ' +
            'and I end every shift burying it in black bags. You get ' +
            'used to almost anything... not to this. If someone ever ' +
            'invents a way to save it, I will sign first.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Guarda esa firma', en: 'Hold that signature' },
            next: null,
          },
        ],
      },
    },
  }),

  ignacia: defineDialog({
    name: { es: 'Ignacia Muñoz', en: 'Ignacia Muñoz' },
    chatter: [
      {
        es: 'Me da una lata botar este pan...',
        en: 'It pains me to bin this bread...',
      },
      {
        es: 'Alguien se comeria esto feliz. ALGUIEN.',
        en: 'Someone would eat this happily. SOMEONE.',
      },
      {
        es: 'La bolsa negra otra vez. Que pena.',
        en: 'The black bag again. Such a shame.',
      },
      {
        es: 'Ni regalarlo podemos a esta hora.',
        en: 'We cannot even give it away at this hour.',
      },
      {
        es: 'Y manana horneamos de nuevo, como si nada.',
        en: 'And tomorrow we bake again, as if nothing happened.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Ignacia, dependienta. Yo atendi todo el dia este ' +
            'mostrador — y ahora me toca vaciarlo al tacho. Las donas ' +
            'que vendi a precio lleno a las cinco, a las diez las ' +
            'estoy botando. ¿Quieres preguntarme algo?',
          en:
            'Ignacia, shop assistant. I worked this counter all day — ' +
            'and now I get to empty it into the bin. The donuts I ' +
            'sold at full price at five, I am binning at ten. Did you ' +
            'want to ask me something?',
        },
        options: [
          {
            label: {
              es: '¿Que se siente botarlo?',
              en: 'How does binning it feel?',
            },
            next: 'pena-1',
          },
          {
            label: {
              es: '¿Por que no lo regalan?',
              en: 'Why not give it away?',
            },
            next: 'regalo-1',
          },
          {
            label: { es: 'La dejo terminar', en: 'I will let you finish' },
            next: null,
          },
        ],
      },
      'pena-1': {
        text: {
          es:
            'Como botar trabajo. La masa se amaso de madrugada, el ' +
            'horno estuvo prendido desde las seis, alguien glaseo ' +
            'cada dona a mano... y todo eso termina en una bolsa ' +
            'negra porque dieron las diez. A mi me da lata hasta ' +
            'mirarlo.',
          en:
            'Like binning work itself. The dough was kneaded before ' +
            'dawn, the oven ran since six, someone hand-glazed every ' +
            'donut... and all of it ends in a black bag because the ' +
            'clock struck ten. I can hardly bear to watch.',
        },
        options: [
          {
            label: {
              es: '¿Y los clientes lo saben?',
              en: 'Do customers know?',
            },
            next: 'pena-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'pena-2': {
        text: {
          es:
            'No tienen idea. La clienta de la tarde me pregunto si ' +
            'quedaba pan para manana — y el pan de HOY, perfecto, se ' +
            'bota esta noche. Si ella supiera, se lo llevaria ' +
            'rebajado feliz. Pero no hay como avisarle... no existe ' +
            'ese canal.',
          en:
            'No idea at all. The afternoon customer asked if there ' +
            'would be bread tomorrow — while TODAY’s bread, perfect, ' +
            'gets binned tonight. If she knew, she would happily take ' +
            'it discounted. But there is no way to tell her... that ' +
            'channel does not exist.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: {
              es: 'Alguien inventara ese canal',
              en: 'Someone will invent that channel',
            },
            next: null,
          },
        ],
      },
      'regalo-1': {
        text: {
          es:
            'Lo intentamos: a esta hora no hay a QUIEN. Los comedores ' +
            'retiran temprano y con papeleo, los vecinos ya cenaron, ' +
            'y dejarlo en la puerta no se puede. Media hora entre que ' +
            'cierro caja y pasa el camion — no alcanza para repartir ' +
            'nada.',
          en:
            'We tried: at this hour there is NOBODY. Food banks pick ' +
            'up early and want paperwork, the neighbours already had ' +
            'dinner, and leaving it at the door is not allowed. Half ' +
            'an hour between closing the till and the truck — no time ' +
            'to hand out anything.',
        },
        options: [
          {
            label: {
              es: '¿Que necesitarias?',
              en: 'What would you need?',
            },
            next: 'regalo-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'regalo-2': {
        text: {
          es:
            'Que la gente SUPIERA antes de que cierre: "en esta ' +
            'cafeteria sobro esto, ven por el a tal hora". Que pague ' +
            'poquito aunque sea, y que pase a buscarlo camino a su ' +
            'casa. Yo se lo empacaria con un lazo si hiciera falta. ' +
            'Sueño con eso, fijate.',
          en:
            'For people to KNOW before we close: "this cafe has this ' +
            'left over, come get it by such a time". Pay a little, ' +
            'even, and pick it up on the way home. I would pack it ' +
            'with a ribbon if needed. I dream about that, you know.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: {
              es: 'Ese sueño esta cerca',
              en: 'That dream is close',
            },
            next: null,
          },
        ],
      },
    },
  }),

  pena: defineDialog({
    name: { es: 'Sr. Peña', en: 'Mr. Peña' },
    chatter: [
      {
        es: 'Cada bolsa que sale es plata que pague.',
        en: 'Every bag that leaves is money I paid.',
      },
      {
        es: 'El margen del dia se me va en el tacho.',
        en: 'The day’s margin walks out in the bin.',
      },
      {
        es: '¿Vender mas barato lo que sobra? ¿Pero COMO?',
        en: 'Sell the surplus cheaper? But HOW?',
      },
      {
        es: 'Hoy botamos casi el veinte por ciento. Otra vez.',
        en: 'We binned nearly twenty percent today. Again.',
      },
      {
        es: 'Tiene que haber una forma. TIENE que.',
        en: 'There has to be a way. There HAS to be.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Peña, dueño del local. Llevo la cuenta de cada kilo de ' +
            'harina que entra... y de cada bolsa de comida que sale ' +
            'por la puerta de atras sin dejar un peso. ¿Quieres ' +
            'hablar de numeros tristes?',
          en:
            'Peña, owner. I track every kilo of flour that comes ' +
            'in... and every bag of food that leaves through the back ' +
            'door without earning a peso. Care to talk sad numbers?',
        },
        options: [
          {
            label: {
              es: '¿Cuanto le cuesta la merma?',
              en: 'What does the waste cost you?',
            },
            next: 'cuenta-1',
          },
          {
            label: {
              es: '¿Que haria usted distinto?',
              en: 'What would you do differently?',
            },
            next: 'deseo-1',
          },
          {
            label: { es: 'Lo dejo con la caja', en: 'Back to your till' },
            next: null,
          },
        ],
      },
      'cuenta-1': {
        text: {
          es:
            'Saque la cuenta: cada bandeja que se bota la pague dos ' +
            'veces — la materia prima y las horas de horno. La ' +
            'basura no me devuelve nada, y encima pago porque se la ' +
            'lleven. Un negocio donde el producto sobrante VALE CERO ' +
            'es un negocio cojo.',
          en:
            'I ran the numbers: every binned tray I paid for twice — ' +
            'raw material and oven hours. The garbage gives nothing ' +
            'back, and I even pay to have it hauled. A business where ' +
            'leftover product is WORTH ZERO is a limping business.',
        },
        options: [
          {
            label: {
              es: '¿Y bajarle el precio?',
              en: 'What about lowering the price?',
            },
            next: 'cuenta-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'cuenta-2': {
        text: {
          es:
            'Rebajar en la vitrina canibaliza la venta de manana — ' +
            'la gente esperaria las diez para comprar todo a mitad. ' +
            'El truco seria venderlo AFUERA de mi vitrina: otro ' +
            'canal, otra gente, sorpresa en vez de catalogo. Pero ese ' +
            'canal hay que inventarlo.',
          en:
            'Discounting in the case cannibalises tomorrow’s sales — ' +
            'people would wait until ten to buy everything at half ' +
            'price. The trick would be selling it OUTSIDE my case: ' +
            'another channel, other people, surprise instead of ' +
            'catalogue. But that channel has yet to be invented.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: {
              es: 'Suena a una app',
              en: 'Sounds like an app',
            },
            next: 'deseo-2',
          },
        ],
      },
      'deseo-1': {
        text: {
          es:
            'Vender aunque sea barato lo que sobra. Prefiero mil ' +
            'veces recuperar un tercio del precio a pagar por botar ' +
            'comida perfecta. Si alguien juntara a los locales como ' +
            'el mio con gente dispuesta a comprar la sorpresa del ' +
            'dia... se hace rico y nos salva a todos.',
          en:
            'Sell the surplus, even cheap. I would a thousand times ' +
            'rather recover a third of the price than pay to bin ' +
            'perfect food. If someone connected venues like mine with ' +
            'people happy to buy the day’s surprise... they would get ' +
            'rich and save us all.',
        },
        options: [
          {
            label: {
              es: '¿Se imagina como seria?',
              en: 'Can you picture it?',
            },
            next: 'deseo-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'deseo-2': {
        text: {
          es:
            'Me lo imagino simple: yo publico "quedan cinco bolsas ' +
            'sorpresa, retiro hasta las ocho", la gente paga desde el ' +
            'telefono y pasa a buscarlas. La vitrina termina vacia ' +
            'por VENTA y no por tacho. Si eso existe algun dia... ' +
            'cruce de vuelta y cuentemelo.',
          en:
            'I picture it simple: I post "five surprise bags left, ' +
            'pickup until eight", people pay from their phone and ' +
            'swing by. The case ends the day empty from SALES, not ' +
            'the bin. If that ever exists... cross back and tell me ' +
            'about it.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: {
              es: 'Le va a gustar el futuro',
              en: 'You will like the future',
            },
            next: null,
          },
        ],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
