/**
 * @module dialogs/corpoelec-pasado (engine)
 * @description Arboles de dialogo de la sala 1 pasado: CORPOELEC (2013)
 *   antes de que llegue el pasante. Oficina de planillas en papel: 38
 *   carpetas, busquedas de 20+ minutos, copias duplicadas y desincronizadas
 *   entre las sedes de Yaracuy, Carabobo y Lara, y el rumor de que viene un
 *   pasante de la universidad a digitalizarlo todo. 3 NPCs frustrados
 *   (canon, informe 08): Dubraska Piña cargando planillas (esperanza),
 *   Wilmer Colina hurgando carpetas por un radio sin registro, y el
 *   oficinista que transcribe seriales (escepticismo comico). Dubraska y
 *   Wilmer reaparecen en el presente: el arco antes/despues del sistema.
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const CORPOELEC_PASADO_DIALOGS = {
  dubraska: defineDialog({
    name: { es: 'Dubraska Piña', en: 'Dubraska Piña' },
    chatter: [
      {
        es: 'Estas pilas no se cargan solas.',
        en: 'These stacks do not carry themselves.',
      },
      {
        es: 'Carpeta 7 de 38... no, la 12. ¿O la 30?',
        en: 'Folder 7 of 38... no, 12. Or was it 30?',
      },
      {
        es: 'Dicen que llega un pasante de la universidad.',
        en: 'They say a university intern is coming.',
      },
      {
        es: '¿Buscas algo? Agarra cafe primero.',
        en: 'Looking for something? Get coffee first.',
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
            'las planillas del inventario entre escritorios... y entre ' +
            'estados. ¿Que quieres saber?',
          en:
            'Watch the stacks, they have their own balance. I carry ' +
            'the inventory forms between desks... and between states. ' +
            'What do you want to know?',
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
              es: 'Oi un rumor sobre un pasante',
              en: 'I heard a rumor about an intern',
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
          es:
            'Queda mi dia a dia... y esa mirada tuya, que me tiene ' +
            'intrigada. ¿Que sera?',
          en:
            'There is my day-to-day left... and that look of yours, ' +
            'which intrigues me. Which will it be?',
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
              es: '¿Que tiene mi mirada?',
              en: 'What about my look?',
            },
            next: 'fut-1',
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
            'El mismo inventario vive en tres planillas: una en ' +
            'Yaracuy, otra en Carabobo, otra en Lara. Y ninguna dice ' +
            'lo mismo.',
          en:
            'The same inventory lives in three forms: one in Yaracuy, ' +
            'one in Carabobo, one in Lara. And no two of them match.',
        },
        options: [
          {
            label: {
              es: '¿Como llegaron a eso?',
              en: 'How did it get like this?',
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
            'Cada sede llena su planilla y manda la copia por valija. ' +
            'Semanas de viaje. Cuando llega, alla ya cambio todo.',
          en:
            'Each site fills its own form and ships the copy by ' +
            'courier bag. Weeks on the road. By the time it arrives, ' +
            'everything already changed over there.',
        },
        options: [
          {
            label: {
              es: '¿No hay conexion entre sedes?',
              en: 'No connection between sites?',
            },
            next: 'cop-3',
          },
          {
            label: {
              es: '¿Y cual copia vale?',
              en: 'So which copy counts?',
            },
            next: 'cop-4',
          },
        ],
      },
      'cop-3': {
        text: {
          es:
            '¿Conexion? Aqui la linea se cae mas seguido que la luz. ' +
            'Y entre estados, ni hablar: los datos viajan en papel y ' +
            'en autobus.',
          en:
            'Connection? The line here drops more often than the ' +
            'power. Between states, forget it: data travels by paper ' +
            'and by bus.',
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
            'Llamadas, un viaje entre estados si la cosa es seria, y ' +
            'al final... fe. Mucha fe.',
          en:
            'Phone calls, a trip between states if it is serious, and ' +
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
            'Una sola fuente para las tres sedes... eso pido yo cada ' +
            'noche. Dicen que el pasante que viene quiere justo eso: ' +
            'digitalizarlo todo.',
          en:
            'A single source for all three sites... that is my ' +
            'nightly wish. They say the intern who is coming wants ' +
            'exactly that: to digitize everything.',
        },
        options: [
          {
            label: {
              es: 'Cuentame de ese pasante',
              en: 'Tell me about that intern',
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
            '¿Ves ese archivador? Treinta y ocho carpetas. Encontrar ' +
            'un equipo ahi toma veinte minutos largos. Y eso con ' +
            'suerte.',
          en:
            'See that cabinet? Thirty-eight folders. Finding one ' +
            'piece of equipment in there takes a long twenty minutes. ' +
            'And that is with luck.',
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
            'Vuelvo a empezar: carpeta uno de treinta y ocho, carpeta ' +
            'dos... El otro dia perdi una mañana ENTERA buscando un ' +
            'aislador.',
          en:
            'I start over: folder one of thirty-eight, folder two... ' +
            'The other day I lost an ENTIRE morning looking for one ' +
            'insulator.',
        },
        options: [
          {
            label: {
              es: '¿Una mañana entera?',
              en: 'An entire morning?',
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
            'Entera. Aparecio en la carpeta treinta y uno, archivado ' +
            'bajo "varios". El cafe se me enfrio tres veces ' +
            'esperandome.',
          en:
            'Entire. It turned up in folder thirty-one, filed under ' +
            '"misc". My coffee went cold three times waiting for me.',
        },
        options: [
          {
            label: {
              es: '¿Y si es urgente?',
              en: 'What if it is urgent?',
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
            'Si es urgente suena el telefono, viene el jefe, y media ' +
            'oficina termina de rodillas revisando gavetas. Un ' +
            'clasico de la casa.',
          en:
            'If it is urgent the phone rings, the boss shows up, and ' +
            'half the office ends up on their knees going through ' +
            'drawers. A house classic.',
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
            'Yo sueño con escribir el nombre del equipo y que ' +
            'aparezca solo. Dicen que el pasante que viene promete ' +
            'algo asi. Mientras tanto, sigo cargando.',
          en:
            'I dream of typing the equipment name and having it just ' +
            'show up. They say the incoming intern promises something ' +
            'like that. Meanwhile, I keep hauling.',
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
            'El rumor dice que llega un pasante de la universidad que ' +
            'quiere digitalizar todo el inventario. Nadie lo conoce ' +
            'todavia: llega en unas semanas.',
          en:
            'The rumor says a university intern is coming, and he ' +
            'wants to digitize the whole inventory. Nobody knows him ' +
            'yet: he arrives in a few weeks.',
        },
        options: [
          {
            label: {
              es: '¿Y tu que esperas?',
              en: 'And what do you expect?',
            },
            next: 'rum-2',
          },
          {
            label: {
              es: '¿Un pasante? ¿En serio?',
              en: 'An intern? Seriously?',
            },
            next: 'rum-4',
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
            'Yo espero todo. Que una sola copia valga para las tres ' +
            'sedes. Que buscar un equipo deje de ser una expedicion ' +
            'arqueologica.',
          en:
            'I expect everything. That a single copy counts for all ' +
            'three sites. That finding equipment stops being an ' +
            'archaeological dig.',
        },
        options: [
          {
            label: {
              es: '¿No es demasiada fe?',
              en: 'Is that not too much faith?',
            },
            next: 'rum-3',
          },
          {
            label: {
              es: '¿Que mas le pedirias?',
              en: 'What else would you ask for?',
            },
            next: 'rum-5',
          },
        ],
      },
      'rum-3': {
        text: {
          es:
            'Puede ser. Pero alguien tiene que creer primero para que ' +
            'las cosas pasen. Yo ya me ofreci: cuando llegue, le voy ' +
            'a contar como trabajamos de verdad.',
          en:
            'Maybe. But somebody has to believe first so that things ' +
            'happen. I already volunteered: when he arrives, I will ' +
            'tell him how we actually work.',
        },
        options: [
          {
            label: {
              es: '¿Y si el sistema falla?',
              en: 'What if the system fails?',
            },
            next: 'rum-6',
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
            'Eso dicen todos: ¿un pasante contra treinta y ocho ' +
            'carpetas? Yo digo otra cosa: el que no ha cargado este ' +
            'papel no sabe la falta que hace.',
          en:
            'That is what everyone says: an intern against ' +
            'thirty-eight folders? I say something else: whoever has ' +
            'not hauled this paper does not know how badly we need it.',
        },
        options: [
          {
            label: {
              es: '¿Y tu que esperas de el?',
              en: 'What do you expect from him?',
            },
            next: 'rum-2',
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
            'Que aguante sin conexion. Aqui la linea y la luz se van ' +
            'cuando quieren. Si ese sistema respira sin internet, le ' +
            'hago un altar.',
          en:
            'That it holds up offline. The line and the power here ' +
            'leave whenever they please. If that system can breathe ' +
            'without internet, I will build it a shrine.',
        },
        options: [
          {
            label: {
              es: '¿Se va la luz aqui?',
              en: 'The power goes out here?',
            },
            next: 'rum-7',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'rum-6': {
        text: {
          es:
            'Si falla, seguimos como siempre: cargando. Pero si ' +
            'funciona, jubilo este archivador con honores y desfile.',
          en:
            'If it fails, we go on as always: hauling. But if it ' +
            'works, I retire this cabinet with full honors and a ' +
            'parade.',
        },
        options: [
          {
            label: { es: 'Ojala funcione', en: 'I hope it works' },
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
            'En la empresa electrica, si. La ironia no se nos escapa, ' +
            'tranquilo. Por eso lo digo: lo que llegue tiene que ' +
            'funcionar aunque todo lo demas se caiga.',
          en:
            'At the power company, yes. The irony is not lost on us, ' +
            'do not worry. That is why I say it: whatever arrives ' +
            'must keep working even when everything else goes down.',
        },
        options: [
          {
            label: { es: 'Ojala funcione', en: 'I hope it works' },
            next: 'rum-8',
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
            'Ojala. El dia que escriba un codigo y la respuesta ' +
            'llegue antes de que se enfrie el cafe, lloro de la ' +
            'felicidad.',
          en:
            'Hopefully. The day I type a code and the answer arrives ' +
            'before my coffee cools down, I will cry of joy.',
        },
        options: [
          {
            label: {
              es: '¿Viste esa pantalla rara?',
              en: 'Did you see that odd screen?',
            },
            next: 'rum-9',
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
            '¿La que aparecio junto a la grieta? Dice "0.2 s" donde ' +
            'mi vida entera dice "20 minutos". Los demas juran que es ' +
            'un error de tipeo. Yo digo que es una promesa.',
          en:
            'The one that showed up next to the crack? It says ' +
            '"0.2 s" where my whole life says "20 minutes". The ' +
            'others swear it is a typo. I say it is a promise.',
        },
        options: [
          {
            label: {
              es: 'Yo apostaria a la promesa',
              en: 'I would bet on the promise',
            },
            next: 'rum-10',
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
            '¿Verdad que si? Guardo esa apuesta en la carpeta buena. ' +
            'Si algun dia se cumple, te debo un cafe caliente.',
          en:
            'Right? I am filing that bet in the good folder. If it ' +
            'ever comes true, I owe you a hot coffee.',
        },
        options: [
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
          {
            label: { es: 'Trato hecho', en: 'Deal' },
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
            'Cada equipo nuevo son tres copias, una por sede. Y cada ' +
            'correccion, otras tres. Multiplica y llora conmigo.',
          en:
            'Each new asset means three copies, one per site. And ' +
            'each correction, three more. Do the math and weep with ' +
            'me.',
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
            'Treinta y ocho carpetas de historia pura. Ese mueble ' +
            'sabe mas de esta empresa que cualquier gerente. Lastima ' +
            'que no hable.',
          en:
            'Thirty-eight folders of pure history. That cabinet knows ' +
            'more about this company than any manager. A shame it ' +
            'cannot talk.',
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
            'Yo las reclamo. Por eso me conocen en los tres estados, ' +
            'y no siempre por lo bueno. Si el pasante del rumor ' +
            'arregla esto, cedo el trono feliz.',
          en:
            'I claim them back. That is why all three states know me, ' +
            'not always for the good reasons. If the rumored intern ' +
            'fixes this, I will hand over the throne gladly.',
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
      'fut-1': {
        text: {
          es:
            'Baja la voz un momento... Tu no eres de por aqui, ' +
            '¿cierto? Miras esta oficina como quien mira una foto ' +
            'vieja. Y hueles a... futuro.',
          en:
            'Lower your voice for a moment... You are not from around ' +
            'here, right? You look at this office like someone ' +
            'looking at an old photo. And you smell of... future.',
        },
        options: [
          {
            label: {
              es: '¿Como lo supiste?',
              en: 'How did you know?',
            },
            next: 'fut-2',
          },
          {
            label: {
              es: 'Vengo de mas adelante, si',
              en: 'I come from later on, yes',
            },
            next: 'fut-3',
          },
          {
            label: { es: 'Mejor volvamos', en: 'Let us go back' },
            next: 'hub',
          },
        ],
      },
      'fut-2': {
        text: {
          es:
            'Intuicion de archivadora. Me paso el dia fechando ' +
            'papeles: aprendi a fechar personas de un vistazo. Y tu, ' +
            'querido, no eres de este año.',
          en:
            'Filing clerk intuition. I spend my days dating papers: I ' +
            'learned to date people at a glance. And you, dear, are ' +
            'not from this year.',
        },
        options: [
          { label: { es: 'Touche', en: 'Touche' }, next: 'fut-3' },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'fut-3': {
        text: {
          es:
            'Entonces dime una sola cosa, sin detalles: el rumor del ' +
            'pasante que viene a digitalizar todo... ¿termina bien?',
          en:
            'Then tell me just one thing, no details: the rumor about ' +
            'the intern coming to digitize everything... does it end ' +
            'well?',
        },
        options: [
          {
            label: {
              es: 'Termina bien. Muy bien',
              en: 'It ends well. Very well',
            },
            next: 'fut-4',
          },
          {
            label: {
              es: 'No doy spoilers',
              en: 'I do not give spoilers',
            },
            next: 'fut-5',
          },
        ],
      },
      'fut-4': {
        text: {
          es:
            'Con eso me alcanza. Mañana cargo estas pilas con otro ' +
            'animo. Y cuando ese muchacho llegue, le voy a contar ' +
            'TODO: donde duele y por que.',
          en:
            'That is all I need. Tomorrow I will haul these stacks in ' +
            'a better mood. And when that kid arrives, I will tell ' +
            'him EVERYTHING: where it hurts and why.',
        },
        options: [
          {
            label: {
              es: 'Perfecto. Hasta pronto',
              en: 'Perfect. See you soon',
            },
            next: null,
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'fut-5': {
        text: {
          es:
            'Ja, justo. Los archivos tampoco adelantan el final: hay ' +
            'que llegar hasta la ultima carpeta. Esperare, que ' +
            'paciencia me sobra.',
          en:
            'Ha, fair. Files do not skip to the ending either: you ' +
            'must reach the last folder. I will wait, patience I have ' +
            'plenty.',
        },
        options: [
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
          {
            label: { es: 'Suerte esperando', en: 'Good luck waiting' },
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
        es: 'Asi se ha hecho siempre. Y asi seguira.',
        en: 'It has always been done this way. And it will stay.',
      },
      {
        es: '¿Un pasante digitalizando esto? Ja.',
        en: 'An intern digitizing all this? Ha.',
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
            label: {
              es: 'Oi que llega un pasante',
              en: 'I heard an intern is coming',
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
          es:
            '¿Todavia aqui? Bueno. Queda el sello, que es sagrado... ' +
            'y una cosa tuya que no me cierra.',
          en:
            'Still here? Fine. There is the stamp left, which is ' +
            'sacred... and one thing about you that does not add up.',
        },
        options: [
          {
            label: { es: '¿Y ese sello?', en: 'And that stamp?' },
            next: 'sel-1',
          },
          {
            label: {
              es: '¿Que no te cierra de mi?',
              en: 'What does not add up about me?',
            },
            next: 'fut-1',
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
            'Paso las planillas de campo a limpio. A mano. El mismo ' +
            'registro se escribe tres veces: en el campo, aqui, y en ' +
            'la sede que recibe la copia.',
          en:
            'I copy the field forms into clean ones. By hand. The ' +
            'same record gets written three times: in the field, ' +
            'here, and at the site that receives the copy.',
        },
        options: [
          {
            label: {
              es: '¿Tres veces el mismo dato?',
              en: 'The same data three times?',
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
            'Tres, minimo. Y cada mano nueva es una oportunidad nueva ' +
            'de error: un siete apurado parece un uno.',
          en:
            'Three, at least. And every new hand is a new chance for ' +
            'error: a rushed seven looks like a one.',
        },
        options: [
          {
            label: {
              es: '¿Y si eso pasa?',
              en: 'And if that happens?',
            },
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
            'Ese equipo cambia de serial para siempre, sin enterarse. ' +
            'Hasta que alguien lo busca por el serial bueno y no ' +
            'aparece. Ese dia el error, claro, es mio.',
          en:
            'That asset changes serial forever, without ever knowing. ' +
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
            'Dicen que el pasante que viene quiere que cada dato se ' +
            'escriba UNA sola vez. Una. Cuando termine de reirme, le ' +
            'explico donde esta parado.',
          en:
            'They say the incoming intern wants every piece of data ' +
            'written down ONCE. Once. When I am done laughing, I will ' +
            'explain to him where he is standing.',
        },
        options: [
          {
            label: {
              es: 'Cuentame de ese pasante',
              en: 'Tell me about that intern',
            },
            next: 'rum-1',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
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
            'uno. Asi el mismo equipo termina con dos vidas, una por ' +
            'sede, y ninguna se entera de la otra.',
          en:
            'Over there they transcribe it again. Another seven that ' +
            'looks like a one. That is how the same asset ends up ' +
            'with two lives, one per site, neither aware of the other.',
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
            'metodo multiplica el error el solito. Y el metodo soy ' +
            'yo, asi que un respeto.',
          en:
            'Exactly. It is not that people are careless. It is that ' +
            'the method multiplies the error all by itself. And I am ' +
            'the method, so show some respect.',
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
            'inventario de tres estados descansa sobre estos lentes. ' +
            'No lo digas muy fuerte.',
          en:
            'The boss. And the boss trusts my handwriting. The whole ' +
            'three-state inventory rests on these glasses. Do not say ' +
            'it too loud.',
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
      'rum-1': {
        text: {
          es:
            'Ah, el famoso pasante de la universidad que viene a ' +
            '"digitalizar todo". Todavia no pisa la oficina y ya lo ' +
            'citan mas que al jefe.',
          en:
            'Ah, the famous university intern who is coming to ' +
            '"digitize everything". He has not set foot in the office ' +
            'yet and he is already quoted more than the boss.',
        },
        options: [
          {
            label: {
              es: '¿No le crees?',
              en: 'You do not believe it?',
            },
            next: 'rum-2',
          },
          {
            label: {
              es: '¿Que dicen que hara?',
              en: 'What do they say he will do?',
            },
            next: 'rum-3',
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
            'He visto pasar tres grandes ideas por esta oficina. Las ' +
            'tres terminaron dentro del archivador, bien selladas. La ' +
            'computadora sera la cuarta.',
          en:
            'I have seen three big ideas come through this office. ' +
            'All three ended up inside the cabinet, properly stamped. ' +
            'The computer will be the fourth.',
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
      'rum-3': {
        text: {
          es:
            'Que escribiras el nombre del equipo y aparecera al ' +
            'instante. Al instante. Yo tardo veinte minutos con ' +
            'veinte años de practica. Saca la cuenta de cuanto le ' +
            'creo.',
          en:
            'That you will type the equipment name and it will show ' +
            'up instantly. Instantly. I take twenty minutes with ' +
            'twenty years of practice. Do the math on how much I ' +
            'believe it.',
        },
        options: [
          {
            label: { es: '¿Y si es verdad?', en: 'What if it is true?' },
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
            'Si es verdad, me como una planilla. Con sello. ...Esta ' +
            'bien: si es verdad, aprendo. Pero que no me toque el ' +
            'sello, que sin el no soy nadie.',
          en:
            'If it is true, I will eat a form. Stamp included. ' +
            '...Fine: if it is true, I will learn. But hands off my ' +
            'stamp, without it I am nobody.',
        },
        options: [
          {
            label: {
              es: '¿Y esa pantalla rara de alla?',
              en: 'And that odd screen over there?',
            },
            next: 'rum-5',
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
            '¿La que dice "0.2 s"? Error de tipeo, claramente. Le ' +
            'faltan los veinte minutos adelante. ...¿Y tu por que ' +
            'sonries asi?',
          en:
            'The one that says "0.2 s"? A typo, clearly. It is ' +
            'missing the twenty minutes in front. ...And why are you ' +
            'smiling like that?',
        },
        options: [
          {
            label: {
              es: 'Por nada. Volvamos',
              en: 'No reason. Back to topics',
            },
            next: 'hub',
          },
          {
            label: { es: 'El tiempo dira', en: 'Time will tell' },
            next: null,
          },
        ],
      },
      'fut-1': {
        text: {
          es:
            'A ver... Tu no eres de por aqui. Miras mi papel carbon ' +
            'como quien mira una pieza de museo. Y hueles a... ' +
            'futuro.',
          en:
            'Let me see... You are not from around here. You look at ' +
            'my carbon paper like someone eyeing a museum piece. And ' +
            'you smell of... future.',
        },
        options: [
          {
            label: { es: '¿Tan obvio soy?', en: 'Am I that obvious?' },
            next: 'fut-2',
          },
          {
            label: { es: 'Mejor volvamos', en: 'Let us go back' },
            next: 'hub',
          },
        ],
      },
      'fut-2': {
        text: {
          es:
            'Veinte años comparando letras. Detectar lo que no encaja ' +
            'es mi oficio, y tu no encajas en este año. Tranquilo: ' +
            'sin sello, no es oficial.',
          en:
            'Twenty years comparing handwriting. Spotting what does ' +
            'not fit is my trade, and you do not fit in this year. ' +
            'Relax: without a stamp, it is not official.',
        },
        options: [
          {
            label: {
              es: 'Entonces un consejo: aprende',
              en: 'Then one piece of advice: learn',
            },
            next: 'fut-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'fut-3': {
        text: {
          es:
            '¿Aprender? ¿Lo del pasante? Ja... ja. ¿En serio? Bueno. ' +
            'Si el futuro en persona me lo pide, le dejo una esquina ' +
            'del escritorio a la computadora. Pequeña.',
          en:
            'Learn? The intern thing? Ha... ha. Seriously? Fine. If ' +
            'the future in person asks me to, I will clear a corner ' +
            'of the desk for the computer. A small one.',
        },
        options: [
          {
            label: { es: 'Sabia decision', en: 'Wise decision' },
            next: null,
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
    },
  }),

  wilmer: defineDialog({
    name: { es: 'Wilmer Colina', en: 'Wilmer Colina' },
    chatter: [
      {
        es: 'Carpeta veinte... esto ANTES estaba aqui.',
        en: 'Folder twenty... this USED to be here.',
      },
      {
        es: '¿Alguien vio el radio RAD-014? Nadie. Como siempre.',
        en: 'Anyone seen radio RAD-014? Nobody. As usual.',
      },
      {
        es: 'Treinta años y el papel todavia me gana.',
        en: 'Thirty years in and paper still beats me.',
      },
      {
        es: 'En mi cabeza esta todo. El problema es sacarlo.',
        en: 'It is all in my head. Getting it out is the problem.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Espera, que ando buscando un equipo... hoja por hoja, ' +
            'como todos los dias. Soy Wilmer, el del almacen. Treinta ' +
            'años cuidando repuestos que el papel pierde. ¿Que quieres?',
          en:
            'Hold on, I am looking for a unit... page by page, like ' +
            'every day. I am Wilmer, the warehouse keeper. Thirty ' +
            'years minding spares that paper keeps losing. What do ' +
            'you want?',
        },
        options: [
          {
            label: {
              es: '¿Que buscas ahora?',
              en: 'What are you looking for now?',
            },
            next: 'radio-1',
          },
          {
            label: {
              es: '¿Siempre es asi de lento?',
              en: 'Is it always this slow?',
            },
            next: 'carpetas-1',
          },
          {
            label: {
              es: 'Dicen que viene un pasante',
              en: 'They say an intern is coming',
            },
            next: 'rumor-1',
          },
          {
            label: { es: 'Nada, siga buscando', en: 'Nothing, keep looking' },
            next: null,
          },
        ],
      },
      'radio-1': {
        text: {
          es:
            'Un radio. Una cuadrilla se lo llevo hace semanas y no hay ' +
            'papel que diga quien, ni cuando, ni si volvio. Si aparece ' +
            'dañado, tampoco quedara registro. El equipo muere en ' +
            'silencio y la culpa cae... adivina: en el almacenista.',
          en:
            'A radio. A crew took it weeks ago and there is no paper ' +
            'saying who, or when, or whether it came back. If it turns ' +
            'up broken, there will be no record of that either. The ' +
            'unit dies in silence and the blame lands... guess where: ' +
            'on the warehouse keeper.',
        },
        options: [
          {
            label: {
              es: '¿Y como lo va a encontrar?',
              en: 'How will you find it?',
            },
            next: 'radio-2',
          },
          {
            label: {
              es: '¿Eso pasa seguido?',
              en: 'Does that happen often?',
            },
            next: 'radio-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'radio-2': {
        text: {
          es:
            'Preguntando cuadrilla por cuadrilla, con el walkie en la ' +
            'mano y la paciencia en el suelo. Lo que yo pido es poco: ' +
            'saber QUIEN lo tomo y A QUIEN se le daño. Un cuaderno que ' +
            'no mienta. ¿Tan dificil es?',
          en:
            'Asking crew by crew, walkie in hand and patience on the ' +
            'floor. What I ask is simple: to know WHO took it and on ' +
            'WHOSE watch it broke. A ledger that does not lie. Is that ' +
            'so much?',
        },
        options: [
          {
            label: {
              es: 'Alguien deberia construir eso',
              en: 'Somebody should build that',
            },
            next: 'rumor-1',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'radio-3': {
        text: {
          es:
            'Cada semana. Radios, telefonos, hasta una laptop de las ' +
            'gruesas. Salen del almacen con una firma ilegible y ' +
            'vuelven cuando quieren... o no vuelven. Y las planillas, ' +
            'tan tranquilas, diciendo que todo esta "operativo".',
          en:
            'Every week. Radios, phones, even one of the thick ' +
            'laptops. They leave the warehouse under an unreadable ' +
            'signature and come back whenever they please... or not at ' +
            'all. And the forms sit there calmly claiming everything ' +
            'is "operational".',
        },
        options: [
          {
            label: {
              es: '¿Y nadie arregla eso?',
              en: 'And nobody fixes that?',
            },
            next: 'radio-2',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'carpetas-1': {
        text: {
          es:
            'Lento es poco. Buscar un equipo en estas carpetas me toma ' +
            'minutos largos, y a veces ni aparece: se traspapelo, esta ' +
            'en otra sede o nunca existio. Treinta y ocho carpetas y ' +
            'ni una se pone de acuerdo con la otra.',
          en:
            'Slow is generous. Finding a unit in these folders takes ' +
            'me long minutes, and sometimes it never shows up: ' +
            'misfiled, at another site, or it never existed. ' +
            'Thirty-eight folders and not one agrees with another.',
        },
        options: [
          {
            label: {
              es: '¿Y su memoria no basta?',
              en: 'Is your memory not enough?',
            },
            next: 'carpetas-2',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'carpetas-2': {
        text: {
          es:
            'Mi cabeza sabe donde esta casi todo... pero yo no estoy ' +
            'en tres estados a la vez, ni pienso vivir para siempre. ' +
            'El dia que yo falte, este almacen queda ciego. Eso no se ' +
            'lo digo a nadie, asi que guardamelo.',
          en:
            'My head knows where almost everything is... but I am not ' +
            'in three states at once, and I do not plan to live ' +
            'forever. The day I am gone, this warehouse goes blind. I ' +
            'tell that to nobody, so keep it for me.',
        },
        options: [
          {
            label: {
              es: 'Su cabeza necesita respaldo',
              en: 'Your head needs a backup',
            },
            next: 'rumor-1',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'rumor-1': {
        text: {
          es:
            'Si, ya oi el cuento: un pasante de la universidad que ' +
            'viene a "digitalizarlo todo". Aqui ya vinieron a ' +
            'modernizarnos antes, sin preguntar nada, y todo termino ' +
            'en un cajon. ¿Por que este seria distinto?',
          en:
            'Yes, I heard the tale: a university intern coming to ' +
            '"digitize everything". People came to modernize us ' +
            'before, without asking a thing, and it all ended in a ' +
            'drawer. Why would this one be any different?',
        },
        options: [
          {
            label: {
              es: '¿Y si este si pregunta?',
              en: 'What if this one does ask?',
            },
            next: 'rumor-2',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'rumor-2': {
        text: {
          es:
            'Si ese muchacho pisa MI almacen, pregunta como trabajo y ' +
            'mete al sistema lo del radio — quien lo tomo, a quien se ' +
            'le daño —, entonces me tiene de su lado. Yo dicto y el ' +
            'anota. Pero pantallas, lo que se dice tocar pantallas... ' +
            'eso jamas.',
          en:
            'If that kid walks into MY warehouse, asks how I work and ' +
            'puts the radio thing into his system — who took it, on ' +
            'whose watch it broke — then he has me on his side. I ' +
            'dictate, he writes. But screens, as in actually touching ' +
            'screens... never.',
        },
        options: [
          {
            label: {
              es: 'Algo me dice que cedera',
              en: 'Something tells me you will cave',
            },
            next: 'rumor-3',
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
      'rumor-3': {
        text: {
          es:
            'Ja. El dia que YO busque un repuesto en una computadora, ' +
            'te autorizo a recordarmelo. ...¿Por que sonries asi? No ' +
            'me gusta esa sonrisa. Anda, vete, que la carpeta ' +
            'veintiuno no se revisa sola.',
          en:
            'Ha. The day I look up a spare on a computer, you have my ' +
            'permission to remind me. ...Why are you smiling like ' +
            'that? I do not like that smile. Go on now, folder ' +
            'twenty-one will not search itself.',
        },
        options: [
          {
            label: {
              es: 'Trato hecho. Hasta luego',
              en: 'Deal. See you around',
            },
            next: null,
          },
          {
            label: { es: 'Volvamos', en: 'Back to topics' },
            next: 'hub',
          },
        ],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
