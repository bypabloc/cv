/**
 * @module dialogs/corpoelec-pasado (engine)
 * @description Arboles de dialogo de la sala 1 pasado: CORPOELEC (2013)
 *   antes del sistema. Oficina de planillas en papel: copias duplicadas
 *   entre las sedes de Yaracuy, Carabobo y Lara, busquedas de 20+ minutos
 *   entre carpetas y el rumor de que un pasante esta armando un sistema.
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const CORPOELEC_PASADO_DIALOGS = {
  'oficinista-planillas': defineDialog({
    name: { es: 'Oficinista de planillas', en: 'Paperwork clerk' },
    chatter: [
      {
        es: 'Estas pilas no se cargan solas.',
        en: 'These stacks do not carry themselves.',
      },
      {
        es: '¿Copia uno o copia dos? Nadie sabe.',
        en: 'Copy one or copy two? Nobody knows.',
      },
      {
        es: '¿Buscas algo? Agarra cafe primero.',
        en: 'Looking for something? Get coffee first.',
      },
      {
        es: 'Dicen que un pasante arma un sistema.',
        en: 'They say an intern is building a system.',
      },
      {
        es: 'Otra planilla. Y otra. Y otra mas.',
        en: 'One more form. And another. And more.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Cuidado con las pilas, que tienen su equilibrio. Yo llevo ' +
            'las planillas del inventario entre escritorios. ¿Que ' +
            'quieres saber?',
          en:
            'Watch the stacks, they have their own balance. I carry ' +
            'the inventory forms between desks. What do you want ' +
            'to know?',
        },
        options: [
          {
            label: {
              es: '¿Por que hay tantas copias?',
              en: 'Why are there so many copies?',
            },
            next: 'cop-1',
          },
          {
            label: {
              es: 'Hay mas temas, ¿verdad?',
              en: 'There is more, right?',
            },
            next: 'hub2',
          },
          {
            label: {
              es: 'Nada, sigue con lo tuyo',
              en: 'Nothing, carry on',
            },
            next: null,
          },
        ],
      },
      hub2: {
        text: {
          es:
            'Claro que hay mas. Aqui sobran historias y faltan ' +
            'carpetas. ¿Que sigue?',
          en:
            'Of course there is more. Stories we have plenty, folders ' +
            'we lack. What next?',
        },
        options: [
          {
            label: {
              es: '¿Como encuentran un equipo aqui?',
              en: 'How do you find equipment here?',
            },
            next: 'bus-1',
          },
          {
            label: {
              es: 'Oi un rumor sobre un sistema',
              en: 'I heard a rumor about a system',
            },
            next: 'rum-1',
          },
          {
            label: { es: '¿Algo mas?', en: 'Anything else?' },
            next: 'hub3',
          },
        ],
      },
      hub3: {
        text: {
          es: 'Queda lo mio: el oficio de cargar papel. ¿O ya te ' + 'aburri?',
          en:
            'What is left is my part: the craft of hauling paper. Or ' +
            'did I bore you already?',
        },
        options: [
          {
            label: {
              es: 'Cuentame tu dia a dia',
              en: 'Tell me about your day',
            },
            next: 'dia-1',
          },
          {
            label: {
              es: 'Volvamos al principio',
              en: 'Back to the beginning',
            },
            next: 'hub',
          },
          {
            label: { es: 'Me voy ya', en: 'I will go now' },
            next: 'bye',
          },
        ],
      },
      bye: {
        text: {
          es:
            'Ve tranquilo. Y si ves una carpeta suelta por ahi, no la ' +
            'toques: seguro es la unica copia de algo.',
          en:
            'Take care. And if you see a loose folder out there, do ' +
            'not touch it: it is surely the only copy of something.',
        },
        options: [
          {
            label: { es: 'Hasta luego', en: 'See you' },
            next: null,
          },
        ],
      },
      'cop-1': {
        text: {
          es:
            'El mismo inventario vive en tres planillas: Yaracuy ' +
            'lleva una copia, Carabobo lleva otra... y no dicen lo ' +
            'mismo.',
          en:
            'The same inventory lives in three forms: Yaracuy keeps ' +
            'one copy, Carabobo keeps another... and they do not ' +
            'match.',
        },
        options: [
          {
            label: {
              es: '¿Y la tercera sede?',
              en: 'And the third site?',
            },
            next: 'cop-2',
          },
          {
            label: {
              es: '¿Cual es la buena?',
              en: 'Which one is the good one?',
            },
            next: 'cop-4',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'cop-2': {
        text: {
          es:
            'La copia de Lara se perdio. Asi, sin drama: un dia ' +
            'estaba y al otro nadie la habia visto nunca.',
          en:
            'The Lara copy got lost. Just like that: one day it was ' +
            'there, the next day nobody had ever seen it.',
        },
        options: [
          {
            label: {
              es: '¿Como se pierde eso?',
              en: 'How does that get lost?',
            },
            next: 'cop-3',
          },
          {
            label: {
              es: '¿Y cual vale entonces?',
              en: 'So which one counts?',
            },
            next: 'cop-4',
          },
        ],
      },
      'cop-3': {
        text: {
          es:
            'Una mudanza, una caja mal rotulada, un archivador que se ' +
            'cerro para siempre. Elige tu teoria, todas valen igual.',
          en:
            'A move, a mislabeled box, a cabinet that closed forever. ' +
            'Pick your theory, they are all equally valid.',
        },
        options: [
          {
            label: {
              es: '¿Y cual copia vale?',
              en: 'So which copy counts?',
            },
            next: 'cop-4',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'cop-4': {
        text: {
          es:
            'Ninguna y todas. Cuando Yaracuy y Carabobo no coinciden, ' +
            'gana la sede que grita mas fuerte por telefono.',
          en:
            'None and all of them. When Yaracuy and Carabobo disagree, ' +
            'the site that yells louder on the phone wins.',
        },
        options: [
          {
            label: {
              es: '¿No coinciden seguido?',
              en: 'Do they disagree often?',
            },
            next: 'cop-5',
          },
          {
            label: {
              es: '¿Nadie las unifica?',
              en: 'Does nobody merge them?',
            },
            next: 'cop-7',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'cop-5': {
        text: {
          es:
            'Seguido. Un transformador figura operativo en una copia ' +
            'y dañado en la otra. El pobre no sabe ni como esta.',
          en:
            'Often. A transformer shows as working in one copy and ' +
            'damaged in the other. The poor thing does not even know ' +
            'how it is doing.',
        },
        options: [
          {
            label: {
              es: '¿Y como lo resuelven?',
              en: 'How do you settle it?',
            },
            next: 'cop-6',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'cop-6': {
        text: {
          es:
            'Llamadas, un viaje entre sedes si la cosa es seria, y al ' +
            'final... fe. Mucha fe.',
          en:
            'Phone calls, a trip between sites if it is serious, and ' +
            'in the end... faith. A lot of faith.',
        },
        options: [
          {
            label: {
              es: '¿Nadie unifico las copias?',
              en: 'Did nobody merge the copies?',
            },
            next: 'cop-7',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'cop-7': {
        text: {
          es:
            'Se intento una vez. Semanas comparando planilla contra ' +
            'planilla, a mano. ¿Resultado? Peor que antes.',
          en:
            'It was tried once. Weeks comparing form against form, by ' +
            'hand. The result? Worse than before.',
        },
        options: [
          {
            label: { es: '¿Peor? ¿Como?', en: 'Worse? How?' },
            next: 'cop-8',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'cop-8': {
        text: {
          es:
            'Aparecio una cuarta version. La llamaron "la ' +
            'consolidada". Nadie la firmo y nadie confia en ella.',
          en:
            'A fourth version appeared. They called it "the ' +
            'consolidated one". Nobody signed it and nobody trusts it.',
        },
        options: [
          {
            label: {
              es: '¿Cuatro versiones ya?',
              en: 'Four versions already?',
            },
            next: 'cop-9',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'cop-9': {
        text: {
          es:
            'Cuatro versiones de una sola verdad. Para saber cuantos ' +
            'equipos tenemos, primero hay que decidir a quien creerle.',
          en:
            'Four versions of a single truth. To know how much ' +
            'equipment we own, first you must decide who to believe.',
        },
        options: [
          {
            label: {
              es: 'Necesitan una sola fuente',
              en: 'You need a single source',
            },
            next: 'cop-10',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'cop-10': {
        text: {
          es:
            'Una sola fuente para las tres sedes... suena a sueño. ' +
            'Aunque dicen que un pasante anda en algo asi.',
          en:
            'A single source for all three sites... sounds like a ' +
            'dream. Though they say an intern is onto something like ' +
            'that.',
        },
        options: [
          {
            label: {
              es: 'Cuentame del pasante',
              en: 'Tell me about the intern',
            },
            next: 'rum-1',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'bus-1': {
        text: {
          es:
            '¿Ves ese archivador? Encontrar un equipo ahi toma veinte ' +
            'minutos. Y eso cuando hay suerte.',
          en:
            'See that cabinet? Finding one piece of equipment in ' +
            'there takes twenty minutes. And that is with luck.',
        },
        options: [
          {
            label: {
              es: '¿Veinte minutos?',
              en: 'Twenty minutes?',
            },
            next: 'bus-2',
          },
          {
            label: { es: '¿Y sin suerte?', en: 'And without luck?' },
            next: 'bus-4',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'bus-2': {
        text: {
          es:
            'Carpeta por sede, dentro por año, dentro por tipo de ' +
            'equipo. En teoria. En la practica, cada quien archivo a ' +
            'su manera.',
          en:
            'Folder by site, then by year, then by equipment type. In ' +
            'theory. In practice, everyone filed their own way.',
        },
        options: [
          {
            label: {
              es: '¿Quien ordeno esto asi?',
              en: 'Who set it up like this?',
            },
            next: 'bus-3',
          },
          {
            label: {
              es: '¿Y si no aparece?',
              en: 'And if it never shows up?',
            },
            next: 'bus-4',
          },
        ],
      },
      'bus-3': {
        text: {
          es:
            'Nadie y todos. Años de manos distintas, cada una con su ' +
            'logica. El archivador es un museo de criterios.',
          en:
            'Nobody and everybody. Years of different hands, each ' +
            'with its own logic. That cabinet is a museum of criteria.',
        },
        options: [
          {
            label: {
              es: '¿Y si el equipo no aparece?',
              en: 'What if it never shows up?',
            },
            next: 'bus-4',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'bus-4': {
        text: {
          es:
            'Si no aparece hay tres opciones: se traspapelo, esta en ' +
            'otra sede, o nunca existio. Ninguna te consuela.',
          en:
            'If it does not show up there are three options: ' +
            'misfiled, at another site, or it never existed. None is ' +
            'comforting.',
        },
        options: [
          {
            label: {
              es: '¿Como que nunca existio?',
              en: 'What do you mean, never existed?',
            },
            next: 'bus-5',
          },
          {
            label: {
              es: '¿Que haces entonces?',
              en: 'What do you do then?',
            },
            next: 'bus-6',
          },
        ],
      },
      'bus-5': {
        text: {
          es:
            'Hay equipos que figuran en una planilla y en el galpon ' +
            'no estan. Y equipos en el galpon que ninguna planilla ' +
            'conoce.',
          en:
            'Some equipment shows on a form but is not in the ' +
            'warehouse. And some sits in the warehouse and no form ' +
            'knows about it.',
        },
        options: [
          {
            label: {
              es: '¿Y que haces entonces?',
              en: 'And what do you do then?',
            },
            next: 'bus-6',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'bus-6': {
        text: {
          es:
            'Vuelvo a empezar, carpeta por carpeta. Y a veces no ' +
            'aparece nunca. Se anota "no ubicado" y se cierra la ' +
            'carpeta.',
          en:
            'I start over, folder by folder. And sometimes it never ' +
            'shows up. You write down "not located" and close the ' +
            'folder.',
        },
        options: [
          {
            label: {
              es: '¿Y eso queda asi?',
              en: 'And it just stays like that?',
            },
            next: 'bus-7',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'bus-7': {
        text: {
          es:
            'Queda asi hasta que alguien lo necesita con urgencia. ' +
            'Ese dia todos recuerdan que existe y nadie sabe donde ' +
            'esta.',
          en:
            'It stays like that until someone needs it urgently. That ' +
            'day everyone remembers it exists and nobody knows where ' +
            'it is.',
        },
        options: [
          {
            label: {
              es: '¿Y que pasa ese dia?',
              en: 'What happens that day?',
            },
            next: 'bus-8',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'bus-8': {
        text: {
          es:
            'Suena el telefono, viene el jefe, y media oficina ' +
            'termina de rodillas revisando gavetas. Un clasico de la ' +
            'casa.',
          en:
            'The phone rings, the boss shows up, and half the office ' +
            'ends up on their knees going through drawers. A house ' +
            'classic.',
        },
        options: [
          {
            label: { es: 'Suena agotador', en: 'Sounds exhausting' },
            next: 'bus-9',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'bus-9': {
        text: {
          es:
            'Lo es. Por eso cargo estas pilas con cariño y con rabia, ' +
            'mitad y mitad. El papel pesa mas de lo que parece.',
          en:
            'It is. That is why I carry these stacks with love and ' +
            'with anger, half and half. Paper weighs more than it ' +
            'looks.',
        },
        options: [
          {
            label: {
              es: '¿No hay una mejor forma?',
              en: 'Is there no better way?',
            },
            next: 'bus-10',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'bus-10': {
        text: {
          es:
            'Dicen que si. Que un pasante esta armando algo con una ' +
            'computadora. Yo, mientras tanto, sigo cargando.',
          en:
            'They say there is. That an intern is building something ' +
            'with a computer. Meanwhile, I keep hauling.',
        },
        options: [
          {
            label: {
              es: 'Cuentame de ese rumor',
              en: 'Tell me about that rumor',
            },
            next: 'rum-1',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'rum-1': {
        text: {
          es:
            'El rumor dice que un pasante esta armando un sistema ' +
            'para el inventario. Con computadora y todo.',
          en:
            'The rumor says an intern is building a system for the ' +
            'inventory. Computer and all.',
        },
        options: [
          {
            label: {
              es: '¿Y tu que crees?',
              en: 'And what do you think?',
            },
            next: 'rum-2',
          },
          {
            label: {
              es: '¿Un pasante? ¿En serio?',
              en: 'An intern? Seriously?',
            },
            next: 'rum-5',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'rum-2': {
        text: {
          es:
            'He visto pasar tres grandes ideas en esta oficina. Las ' +
            'tres terminaron dentro del archivador, bien selladas.',
          en:
            'I have seen three big ideas come through this office. ' +
            'All three ended up inside the cabinet, properly stamped.',
        },
        options: [
          {
            label: {
              es: '¿Entonces no crees?',
              en: 'So you do not believe it?',
            },
            next: 'rum-3',
          },
          {
            label: {
              es: '¿Y si esta vez funciona?',
              en: 'What if this time it works?',
            },
            next: 'rum-4',
          },
        ],
      },
      'rum-3': {
        text: {
          es:
            'No dije eso. Digo que el papel nunca me ha dejado sin ' +
            'trabajo... aunque tampoco me deja dormir.',
          en:
            'I did not say that. I say paper has never left me ' +
            'without a job... though it does not let me sleep either.',
        },
        options: [
          {
            label: {
              es: '¿Y si esta vez funciona?',
              en: 'What if this time it works?',
            },
            next: 'rum-4',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'rum-4': {
        text: {
          es:
            'Si funciona, escribes el nombre del equipo y aparece. ' +
            'Sin carpetas, sin gavetas. No me hagas ilusionar, que ' +
            'luego duele.',
          en:
            'If it works, you type the equipment name and it shows ' +
            'up. No folders, no drawers. Do not get my hopes up, it ' +
            'hurts afterwards.',
        },
        options: [
          {
            label: {
              es: '¿Que le pedirias al sistema?',
              en: 'What would you ask of it?',
            },
            next: 'rum-6',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'rum-5': {
        text: {
          es:
            'Eso dije yo: ¿un pasante? Pero se queda hasta tarde y ' +
            'pregunta como trabajamos de verdad. Eso no lo hace ' +
            'cualquiera.',
          en:
            'That is what I said: an intern? But he stays late and ' +
            'asks how we actually work. Not everyone does that.',
        },
        options: [
          {
            label: {
              es: '¿Y tu que opinas?',
              en: 'And what is your take?',
            },
            next: 'rum-2',
          },
          {
            label: { es: '¿Le has hablado?', en: 'Have you talked?' },
            next: 'rum-7',
          },
        ],
      },
      'rum-6': {
        text: {
          es:
            'Que una sola copia valga para las tres sedes. Y que ' +
            'buscar un equipo no sea una expedicion arqueologica.',
          en:
            'That a single copy counts for all three sites. And that ' +
            'finding equipment stops being an archaeological dig.',
        },
        options: [
          {
            label: {
              es: '¿Algo mas de la lista?',
              en: 'Anything else on the list?',
            },
            next: 'rum-8',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'rum-7': {
        text: {
          es:
            'Me pidio una planilla de ejemplo. Le di la mas fea que ' +
            'tenia, para que supiera donde se estaba metiendo.',
          en:
            'He asked me for a sample form. I gave him the ugliest ' +
            'one I had, so he would know what he was getting into.',
        },
        options: [
          {
            label: { es: '¿Y que dijo?', en: 'And what did he say?' },
            next: 'rum-9',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'rum-8': {
        text: {
          es:
            'Que no se caiga cuando se va la luz. Aqui la luz... ' +
            'digamos que conocemos el tema de cerca.',
          en:
            'That it does not die when the power goes out. Here, ' +
            'power... let us say we know the subject closely.',
        },
        options: [
          {
            label: {
              es: '¿Se va la luz aqui?',
              en: 'The power goes out here?',
            },
            next: 'rum-10',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'rum-9': {
        text: {
          es:
            'La miro un buen rato y anoto algo en su cuaderno. Ni se ' +
            'asusto. Eso me dio esperanza, o lastima. Aun no decido.',
          en:
            'He stared at it for a while and wrote something in his ' +
            'notebook. Not even scared. That gave me hope, or pity. ' +
            'Still deciding.',
        },
        options: [
          {
            label: {
              es: 'Dale esperanza, mejor',
              en: 'Go with hope, better',
            },
            next: 'rum-11',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'rum-10': {
        text: {
          es:
            'La ironia no se nos escapa, tranquilo. Por eso lo digo: ' +
            'si ese sistema aguanta sin conexion, le hago un altar.',
          en:
            'The irony is not lost on us, do not worry. That is why I ' +
            'say: if that system holds up offline, I will build it a ' +
            'shrine.',
        },
        options: [
          {
            label: { es: 'Ojala funcione', en: 'I hope it works' },
            next: 'rum-11',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'rum-11': {
        text: {
          es:
            'Ojala. El dia que escriba un codigo y me diga donde esta ' +
            'el equipo, jubilo este archivador con honores.',
          en:
            'Hopefully. The day I type a code and it tells me where ' +
            'the equipment is, I retire this cabinet with full honors.',
        },
        options: [
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
          {
            label: { es: 'Suerte con eso', en: 'Good luck with that' },
            next: null,
          },
        ],
      },
      'dia-1': {
        text: {
          es:
            'Mi dia: cargar planillas de ese escritorio a aquel, ' +
            'sellar, archivar, y volver a empezar. Gimnasio gratis.',
          en:
            'My day: haul forms from that desk to the other one, ' +
            'stamp, file, start again. Free gym membership.',
        },
        options: [
          {
            label: {
              es: '¿Cuantas planillas cargas?',
              en: 'How many forms do you haul?',
            },
            next: 'dia-2',
          },
          {
            label: {
              es: '¿Y ese archivador?',
              en: 'And that cabinet?',
            },
            next: 'dia-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'dia-2': {
        text: {
          es:
            'Las que ves y las que no ves. Cada equipo nuevo son tres ' +
            'copias, una por sede. Multiplica y llora conmigo.',
          en:
            'The ones you see and the ones you do not. Each new asset ' +
            'means three copies, one per site. Do the math and weep ' +
            'with me.',
        },
        options: [
          {
            label: { es: '¿Y el archivador?', en: 'And the cabinet?' },
            next: 'dia-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'dia-3': {
        text: {
          es:
            'Ese mueble sabe mas de esta empresa que cualquier ' +
            'gerente. Lastima que no hable.',
          en:
            'That cabinet knows more about this company than any ' +
            'manager. A shame it cannot talk.',
        },
        options: [
          {
            label: {
              es: '¿Que guarda adentro?',
              en: 'What is inside it?',
            },
            next: 'dia-4',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'dia-4': {
        text: {
          es:
            'Años de inventario. Transformadores, medidores, ' +
            'cables... cada equipo con su carpeta. En teoria.',
          en:
            'Years of inventory. Transformers, meters, cables... ' +
            'every asset with its own folder. In theory.',
        },
        options: [
          {
            label: { es: '¿En teoria?', en: 'In theory?' },
            next: 'dia-5',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'dia-5': {
        text: {
          es:
            'En la practica las carpetas viajan, se prestan y no ' +
            'vuelven. Como los buenos libros.',
          en:
            'In practice folders travel, get borrowed and never come ' +
            'back. Like good books.',
        },
        options: [
          {
            label: {
              es: '¿Y nadie las reclama?',
              en: 'Does nobody claim them back?',
            },
            next: 'dia-6',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'dia-6': {
        text: {
          es:
            'Yo las reclamo. Por eso me conocen en las tres sedes. No ' +
            'siempre por lo bueno.',
          en:
            'I claim them back. That is why all three sites know me. ' +
            'Not always for the good reasons.',
        },
        options: [
          {
            label: {
              es: 'Eres la heroina de esto',
              en: 'You are the hero here',
            },
            next: 'dia-7',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'dia-7': {
        text: {
          es:
            'Heroina con papel carbon en los dedos. Si el rumor del ' +
            'sistema es cierto, cedo el trono feliz.',
          en:
            'A hero with carbon paper on her fingers. If the system ' +
            'rumor is true, I will hand over the throne gladly.',
        },
        options: [
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
          {
            label: { es: 'Descansa un poco', en: 'Get some rest' },
            next: null,
          },
        ],
      },
    },
  }),
  'oficinista-transcribe': defineDialog({
    name: { es: 'Oficinista que transcribe', en: 'Transcribing clerk' },
    chatter: [
      {
        es: 'Siete... ¿o era un uno?',
        en: 'Seven... or was that a one?',
      },
      {
        es: 'No me hables mientras copio seriales.',
        en: 'No talking while I copy serials.',
      },
      {
        es: 'El papel carbon mancha, pero cumple.',
        en: 'Carbon paper stains, but it delivers.',
      },
      {
        es: 'Asi se ha hecho siempre. Creo.',
        en: 'It has always been done this way. I think.',
      },
      {
        es: 'Sin sello, esto no vale nada.',
        en: 'Without the stamp, this is worth nothing.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Un momento... listo. Si me hablas a mitad de un serial, ' +
            'el error queda a tu nombre. ¿Que necesitas?',
          en:
            'One moment... done. If you talk to me mid-serial, the ' +
            'mistake goes under your name. What do you need?',
        },
        options: [
          {
            label: {
              es: '¿Que estas transcribiendo?',
              en: 'What are you transcribing?',
            },
            next: 'err-1',
          },
          {
            label: {
              es: 'Hay mas temas, ¿no?',
              en: 'There is more, right?',
            },
            next: 'hub2',
          },
          {
            label: {
              es: 'Nada, perdona. Sigue',
              en: 'Nothing, sorry. Carry on',
            },
            next: null,
          },
        ],
      },
      hub2: {
        text: {
          es:
            'Temas sobran. Este escritorio es un pais entero. ¿Que te ' +
            'llama la atencion?',
          en:
            'Plenty of topics. This desk is a whole country. What ' +
            'catches your eye?',
        },
        options: [
          {
            label: {
              es: '¿Que es ese papel azulado?',
              en: 'What is that bluish paper?',
            },
            next: 'car-1',
          },
          {
            label: { es: '¿Y ese sello?', en: 'And that stamp?' },
            next: 'sel-1',
          },
          {
            label: { es: '¿Algo mas?', en: 'Anything else?' },
            next: 'hub3',
          },
        ],
      },
      hub3: {
        text: {
          es:
            '¿Todavia aqui? Bueno. Queda una pregunta que todos hacen ' +
            'tarde o temprano.',
          en:
            'Still here? Fine. There is one question everyone asks ' +
            'sooner or later.',
        },
        options: [
          {
            label: {
              es: '¿Por que lo hacen asi?',
              en: 'Why do you do it this way?',
            },
            next: 'asi-1',
          },
          {
            label: {
              es: 'Volvamos al principio',
              en: 'Back to the beginning',
            },
            next: 'hub',
          },
          {
            label: { es: 'Me voy ya', en: 'I will go now' },
            next: 'bye',
          },
        ],
      },
      bye: {
        text: {
          es:
            'Camina despacio entre las pilas. Si tumbas una, aqui ' +
            'nadie te conoce.',
          en:
            'Walk slowly between the stacks. If you knock one over, ' +
            'nobody here knows you.',
        },
        options: [
          {
            label: { es: 'Hasta luego', en: 'See you' },
            next: null,
          },
        ],
      },
      'err-1': {
        text: {
          es:
            'Paso las planillas de campo a limpio. A mano. Cada ' +
            'numero se escribe dos veces: donde nace y donde muere.',
          en:
            'I copy the field forms into clean ones. By hand. Every ' +
            'number gets written twice: where it is born and where it ' +
            'dies.',
        },
        options: [
          {
            label: {
              es: '¿Y si te equivocas?',
              en: 'What if you make a mistake?',
            },
            next: 'err-2',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'err-2': {
        text: {
          es:
            'Pasa. Un siete apurado parece un uno. Y ese equipo ' +
            'cambia de serial para siempre, sin enterarse.',
          en:
            'It happens. A rushed seven looks like a one. And that ' +
            'asset changes serial forever, without ever knowing.',
        },
        options: [
          {
            label: { es: '¿Para siempre?', en: 'Forever?' },
            next: 'err-3',
          },
          {
            label: { es: '¿Nadie revisa?', en: 'Does nobody check?' },
            next: 'err-4',
          },
        ],
      },
      'err-3': {
        text: {
          es:
            'Hasta que alguien lo busca por el serial bueno y no ' +
            'aparece. Ese dia el error, claro, es mio.',
          en:
            'Until someone searches by the right serial and nothing ' +
            'shows up. That day the mistake, of course, is mine.',
        },
        options: [
          {
            label: {
              es: '¿Y nadie revisa?',
              en: 'And does nobody check?',
            },
            next: 'err-4',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'err-4': {
        text: {
          es:
            'Reviso yo, contra mi propia letra. El zorro cuidando el ' +
            'gallinero. Pero con lentes, que impone respeto.',
          en:
            'I check it myself, against my own handwriting. The fox ' +
            'guarding the henhouse. But with glasses, which commands ' +
            'respect.',
        },
        options: [
          {
            label: {
              es: '¿No hay otra forma?',
              en: 'Is there no other way?',
            },
            next: 'err-5',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'err-5': {
        text: {
          es:
            'Dicen que un pasante arma un sistema donde escribes una ' +
            'vez y queda. Si es verdad, firmo donde sea.',
          en:
            'They say an intern is building a system where you type ' +
            'once and it stays. If that is true, I will sign anywhere.',
        },
        options: [
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
          {
            label: { es: 'Que sea pronto', en: 'May it come soon' },
            next: null,
          },
        ],
      },
      'car-1': {
        text: {
          es:
            'Papel carbon. Original y copia en un solo trazo. Magia ' +
            'de oficina... hasta que la tinta se corre.',
          en:
            'Carbon paper. Original and copy in a single stroke. ' +
            'Office magic... until the ink smears.',
        },
        options: [
          {
            label: {
              es: '¿Se corre seguido?',
              en: 'Does it smear often?',
            },
            next: 'car-2',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'car-2': {
        text: {
          es:
            'La copia sale gris y borrosa. ¿Y adivina cual viaja a la ' +
            'otra sede? La borrosa, siempre.',
          en:
            'The copy comes out gray and blurry. And guess which one ' +
            'travels to the other site? The blurry one, always.',
        },
        options: [
          {
            label: {
              es: '¿Y alla la leen bien?',
              en: 'Can they read it there?',
            },
            next: 'car-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'car-3': {
        text: {
          es:
            'Alla la vuelven a transcribir. Otro siete que parece ' +
            'uno. Asi nacen dos inventarios distintos del mismo ' +
            'equipo.',
          en:
            'Over there they transcribe it again. Another seven that ' +
            'looks like a one. That is how one asset ends up with two ' +
            'inventories.',
        },
        options: [
          {
            label: {
              es: 'Con razon nada coincide',
              en: 'No wonder nothing matches',
            },
            next: 'car-4',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'car-4': {
        text: {
          es:
            'Exacto. No es que la gente sea descuidada. Es que el ' +
            'metodo multiplica el error el solito.',
          en:
            'Exactly. It is not that people are careless. It is that ' +
            'the method multiplies the error all by itself.',
        },
        options: [
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
          {
            label: {
              es: 'Entendido, gracias',
              en: 'Understood, thanks',
            },
            next: null,
          },
        ],
      },
      'sel-1': {
        text: {
          es:
            'El sello hace oficial la planilla. Sin sello no vale. ' +
            'Con sello vale, aunque este mal copiada.',
          en:
            'The stamp makes the form official. No stamp, no value. ' +
            'With a stamp it counts, even if it was copied wrong.',
        },
        options: [
          {
            label: {
              es: '¿Aunque tenga errores?',
              en: 'Even with mistakes in it?',
            },
            next: 'sel-2',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'sel-2': {
        text: {
          es:
            'El sello valida el papel, no el contenido. Filosofia ' +
            'pura de oficina. Medita eso un rato.',
          en:
            'The stamp validates the paper, not the content. Pure ' +
            'office philosophy. Meditate on that for a while.',
        },
        options: [
          {
            label: { es: '¿Y quien sella?', en: 'And who stamps?' },
            next: 'sel-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'sel-3': {
        text: {
          es:
            'El jefe. Y el jefe confia en mi letra. Todo el ' +
            'inventario descansa sobre estos lentes. No lo digas muy ' +
            'fuerte.',
          en:
            'The boss. And the boss trusts my handwriting. The whole ' +
            'inventory rests on these glasses. Do not say it too loud.',
        },
        options: [
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
          {
            label: {
              es: 'Tu secreto esta a salvo',
              en: 'Your secret is safe',
            },
            next: null,
          },
        ],
      },
      'asi-1': {
        text: {
          es:
            'Porque asi se ha hecho siempre. Lo dije yo tambien, con ' +
            'orgullo, durante años.',
          en:
            'Because it has always been done this way. I used to say ' +
            'it too, with pride, for years.',
        },
        options: [
          {
            label: {
              es: '¿Ya no lo dices?',
              en: 'You do not say it anymore?',
            },
            next: 'asi-2',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'asi-2': {
        text: {
          es:
            '"Siempre" es la costumbre con años de servicio. El dia ' +
            'que vi tres copias distintas del mismo equipo, dude.',
          en:
            '"Always" is just habit with seniority. The day I saw ' +
            'three different copies of the same asset, I had doubts.',
        },
        options: [
          {
            label: {
              es: '¿Y ahora que piensas?',
              en: 'And what do you think now?',
            },
            next: 'asi-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'asi-3': {
        text: {
          es:
            'Que si el rumor del sistema es cierto, sere el primero ' +
            'en aprender. Con estos lentes y todo.',
          en:
            'That if the system rumor is true, I will be the first to ' +
            'learn. Glasses and all.',
        },
        options: [
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
          {
            label: { es: 'Asi se habla', en: 'That is the spirit' },
            next: null,
          },
        ],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
