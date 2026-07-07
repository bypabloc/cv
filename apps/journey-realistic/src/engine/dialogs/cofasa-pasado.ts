/**
 * @module dialogs/cofasa-pasado (engine)
 * @description Arboles de dialogo de la sala 3 pasado: Cofasa (2017)
 *   antes del sistema. El registro manual de paradas: la supervisora con
 *   libreta y reloj, planillas que no cuadran, la torre de luces en rojo
 *   fijo y una llenadora detenida sin que nadie sepa por que. 3 NPCs
 *   frustrados (canon, informe 10): Nelida Guerra cronometrando a mano,
 *   Rafael Escalona mirando la maquina parada y Carmen Yepez con las
 *   planillas que ni cuadran entre si. Los tres reaparecen en el
 *   presente usando el sistema: el arco antes/despues.
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const COFASA_PASADO_DIALOGS = {
  nelida: defineDialog({
    name: { es: 'Nelida Guerra', en: 'Nelida Guerra' },
    chatter: [
      {
        es: 'Otra parada... y yo aqui con la libreta y el reloj.',
        en: 'Another stoppage... and me here with the notebook and the watch.',
      },
      {
        es: '¿Que hora es? Anota: diez y cuarenta y dos.',
        en: 'What time is it? Write it down: ten forty-two.',
      },
      {
        es: 'Tres horas me va a costar cuadrar esto al final del turno.',
        en: 'Balancing this will cost me three hours at end of shift.',
      },
      {
        es: 'El lapiz ya no raya. EL LAPIZ.',
        en: 'The pencil stopped writing. THE PENCIL.',
      },
      {
        es: '¿Causa? Ponle... "se paro". ¿Que mas pongo?',
        en: 'Cause? Put down... "it stopped". What else can I write?',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Soy la supervisora del turno y este es mi "sistema": una ' +
            'libreta, un lapiz y el reloj de pulsera. Cada parada de ' +
            'maquina, una fila a mano. Pregunta rapido, que la linea no ' +
            'espera.',
          en:
            'I am the shift supervisor and this is my "system": a ' +
            'notebook, a pencil and my wristwatch. Every machine ' +
            'stoppage, one handwritten row. Ask quickly, the line does ' +
            'not wait.',
        },
        options: [
          {
            label: {
              es: '¿Como anotas una parada?',
              en: 'How do you log a stoppage?',
            },
            next: 'anota-1',
          },
          {
            label: {
              es: '¿Que pasa al final del turno?',
              en: 'What happens at end of shift?',
            },
            next: 'cuadre-1',
          },
          {
            label: {
              es: '¿Y si pudieras pedir algo?',
              en: 'If you could ask for anything?',
            },
            next: 'deseo-1',
          },
          {
            label: { es: 'Te dejo trabajar', en: 'I will let you work' },
            next: null,
          },
        ],
      },
      'anota-1': {
        text: {
          es:
            'La maquina se para: miro el reloj y anoto la hora. ' +
            'Arranca: otra vez el reloj. ¿La causa? La que alcance a ' +
            'ver desde donde este parada yo. Si estoy en la otra punta ' +
            'de la planta, esa parada queda... como quede.',
          en:
            'The machine stops: I check the watch and write the time. ' +
            'It restarts: the watch again. The cause? Whatever I manage ' +
            'to see from wherever I am standing. If I am at the far end ' +
            'of the plant, that stoppage gets logged... however it ' +
            'gets logged.',
        },
        options: [
          {
            label: {
              es: '¿Y las planillas manchadas?',
              en: 'And the stained sheets?',
            },
            next: 'anota-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'anota-2': {
        text: {
          es:
            'Mira esa pila: filas tachadas, numeros que no se ' +
            'entienden, cafe derramado del apuro. Eso no es descuido — ' +
            'es que anoto CORRIENDO, entre la linea y el telefono. ' +
            'Despues alguien tiene que descifrar mi letra. Ese alguien ' +
            'tambien soy yo.',
          en:
            'Look at that pile: crossed-out rows, unreadable numbers, ' +
            'coffee spilled in the rush. That is not carelessness — I ' +
            'write things down RUNNING, between the line and the phone. ' +
            'Later somebody has to decipher my handwriting. That ' +
            'somebody is also me.',
        },
        options: [
          {
            label: {
              es: '¿Que pasa al final del turno?',
              en: 'What happens at end of shift?',
            },
            next: 'cuadre-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'cuadre-1': {
        text: {
          es:
            'El cuadre: pasar la libreta a la planilla, sumar los ' +
            'tiempos con la calculadora y rezar para que de lo mismo ' +
            'que ayer no dio. Horas DESPUES de mi jornada. Y manana, la ' +
            'jefa me va a preguntar cuanto paramos — y ni yo me creo ' +
            'mis totales.',
          en:
            'The balancing: copy the notebook into the sheet, add the ' +
            'times on the calculator and pray it matches what it did ' +
            'not match yesterday. Hours AFTER my workday. And tomorrow ' +
            'the boss will ask how long we were down — and even I do ' +
            'not trust my own totals.',
        },
        options: [
          {
            label: {
              es: '¿Y si pudieras pedir algo?',
              en: 'If you could ask for anything?',
            },
            next: 'deseo-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'deseo-1': {
        text: {
          es:
            'Algo que anote SOLO. Que yo diga "se paro la llenadora, ' +
            'atasco" y la hora se ponga sola, y el total se sume solo. ' +
            'Dicen que trajeron a un muchacho de sistemas que anda ' +
            'preguntando por la planta... Ojala pregunte por aqui.',
          en:
            'Something that writes ITSELF. I say "the filler stopped, ' +
            'jam" and the time stamps itself, and the totals add ' +
            'themselves. They say a systems kid arrived and is asking ' +
            'around the plant... I hope he asks around here.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Ojala. Suerte', en: 'Hopefully. Good luck' },
            next: null,
          },
        ],
      },
    },
  }),

  rafael: defineDialog({
    name: { es: 'Rafael Escalona', en: 'Rafael Escalona' },
    chatter: [
      {
        es: '¡Se paro otra vez! ¡SE PARO OTRA VEZ!',
        en: 'It stopped again! IT STOPPED AGAIN!',
      },
      {
        es: '¿Por que se para? Ni idea. Nadie la tiene.',
        en: 'Why does it stop? No idea. Nobody has one.',
      },
      {
        es: 'Aviso gritando, como siempre. A ver quien anota.',
        en: 'I shout it out, as always. Let us see who writes it down.',
      },
      {
        es: 'La torre lleva en rojo toda la mañana.',
        en: 'The tower has been red all morning.',
      },
      {
        es: 'El lote de Miovit va atrasado. Otra vez.',
        en: 'The Miovit batch is behind. Again.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Rafael, operario. Esa de ahi es la llenadora de ampollas — ' +
            'parada, como la ves. ¿Cuanto lleva asi? ¿Quien sabe? ¿Por ' +
            'que se paro? Tampoco. Bienvenido a mi dia.',
          en:
            'Rafael, operator. That one there is the ampoule filler — ' +
            'stopped, as you can see. How long has it been down? Who ' +
            'knows. Why did it stop? No idea either. Welcome to my day.',
        },
        options: [
          {
            label: {
              es: '¿Como avisas cuando se para?',
              en: 'How do you report a stoppage?',
            },
            next: 'aviso-1',
          },
          {
            label: {
              es: '¿Por que se para tanto?',
              en: 'Why does it stop so much?',
            },
            next: 'causas-1',
          },
          {
            label: { es: 'Animo. Sigue asi', en: 'Hang in there' },
            next: null,
          },
        ],
      },
      'aviso-1': {
        text: {
          es:
            'Grito. En serio: grito por encima del ruido de la planta ' +
            '"¡SE PARO LA LLENADORA!" y sigo con lo mio. Si la ' +
            'supervisora anda cerca, lo anota con su reloj. Si no... la ' +
            'parada existe solo en mi memoria. Y mi memoria trabaja ' +
            'turno corrido.',
          en:
            'I shout. Seriously: I shout over the plant noise "THE ' +
            'FILLER STOPPED!" and carry on. If the supervisor is ' +
            'nearby, she logs it with her watch. If not... the stoppage ' +
            'exists only in my memory. And my memory works double ' +
            'shifts.',
        },
        options: [
          {
            label: {
              es: '¿Y nadie revisa despues?',
              en: 'And nobody checks later?',
            },
            next: 'aviso-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'aviso-2': {
        text: {
          es:
            'Revisar QUE. A fin de mes preguntan cuanto paro la linea y ' +
            'cada quien dice un numero distinto: la libreta dice uno, ' +
            'la planilla otro y el jefe de mantenimiento otro. La unica ' +
            'que sabe la verdad es la maquina — y la maquina no habla.',
          en:
            'Check WHAT. At month’s end they ask how long the ' +
            'line was down and everyone gives a different number: the ' +
            'notebook says one thing, the sheet another, maintenance a ' +
            'third. The only one who knows the truth is the machine — ' +
            'and the machine does not talk.',
        },
        options: [
          {
            label: {
              es: '¿Por que se para tanto?',
              en: 'Why does it stop so much?',
            },
            next: 'causas-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'causas-1': {
        text: {
          es:
            'Puede ser mil cosas: atasco, cambio de formato, limpieza, ' +
            'que no llego el material, que se fue la luz... El problema ' +
            'no es que pare — toda linea para. El problema es que NADIE ' +
            'sabe cual causa se come el tiempo. Sin eso, ¿que arreglas ' +
            'primero?',
          en:
            'It can be a thousand things: a jam, a changeover, ' +
            'cleaning, material that never arrived, a power cut... The ' +
            'problem is not that it stops — every line stops. The ' +
            'problem is that NOBODY knows which cause eats the time. ' +
            'Without that, what do you fix first?',
        },
        options: [
          {
            label: {
              es: '¿Y que necesitarias?',
              en: 'And what would you need?',
            },
            next: 'causas-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'causas-2': {
        text: {
          es:
            'Que cada parada quede escrita EN EL MOMENTO, con su causa ' +
            'y su hora, sin que yo tenga que gritar ni Nelida correr ' +
            'con el reloj. Que la planta se cuente a si misma. Suena a ' +
            'ciencia ficcion, ¿verdad? Cruza de vuelta y me cuentas.',
          en:
            'Every stoppage written down IN THE MOMENT, with its cause ' +
            'and time, without me shouting or Nelida running with her ' +
            'watch. A plant that counts itself. Sounds like science ' +
            'fiction, right? Cross back over and tell me.',
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
    name: { es: 'Carmen Yepez', en: 'Carmen Yepez' },
    chatter: [
      {
        es: '¿Cuanto perdimos esta semana? No se. NO SE.',
        en: 'How much did we lose this week? I do not know. I DO NOT KNOW.',
      },
      {
        es: 'Estas planillas no cuadran ni entre ellas.',
        en: 'These sheets do not even match each other.',
      },
      {
        es: 'Me piden productividad y yo tengo papel mojado.',
        en: 'They ask me for productivity and I hold soggy paper.',
      },
      {
        es: 'Una reunion mas adivinando. Una mas.',
        en: 'One more meeting spent guessing. One more.',
      },
      {
        es: 'La calculadora echa humo y el total sigue sin dar.',
        en: 'The calculator is smoking and the total still will not land.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Carmen Yepez, jefa de produccion — o eso dice mi cargo, ' +
            'porque dirigir sin datos es adivinar con uniforme. Mañana ' +
            'tengo reunion de resultados y mire usted mi escritorio: ' +
            'planillas, planillas, planillas.',
          en:
            'Carmen Yepez, head of production — or so my title says, ' +
            'because managing without data is guessing in uniform. I ' +
            'have a results meeting tomorrow and look at my desk: ' +
            'sheets, sheets, sheets.',
        },
        options: [
          {
            label: {
              es: '¿Que le piden en la reunion?',
              en: 'What do they ask in the meeting?',
            },
            next: 'reunion-1',
          },
          {
            label: {
              es: '¿Por que no cuadran las planillas?',
              en: 'Why do the sheets not match?',
            },
            next: 'planillas-1',
          },
          {
            label: { es: 'La dejo trabajar', en: 'I will let you work' },
            next: null,
          },
        ],
      },
      'reunion-1': {
        text: {
          es:
            'Tres preguntas de siempre: cuanto produjimos, cuanto ' +
            'estuvo parada la linea y POR QUE. La primera la respondo. ' +
            'La segunda, mas o menos. La tercera... la tercera nadie en ' +
            'esta planta la ha respondido nunca con numeros.',
          en:
            'The same three questions: how much we produced, how long ' +
            'the line was down and WHY. The first I can answer. The ' +
            'second, roughly. The third... nobody in this plant has ' +
            'ever answered the third with numbers.',
        },
        options: [
          {
            label: {
              es: '¿Y que responde entonces?',
              en: 'So what do you answer?',
            },
            next: 'reunion-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'reunion-2': {
        text: {
          es:
            'Impresiones: "la llenadora falla mucho", "la limpieza nos ' +
            'quita tiempo", "el mes fue duro". Y sobre impresiones se ' +
            'deciden inversiones. Un dia vamos a culpar a la maquina ' +
            'equivocada y va a salir CARO.',
          en:
            'Impressions: "the filler breaks a lot", "cleaning steals ' +
            'our time", "it was a rough month". And investments get ' +
            'decided on impressions. One day we will blame the wrong ' +
            'machine and it will cost us DEARLY.',
        },
        options: [
          {
            label: {
              es: '¿Que necesitaria usted?',
              en: 'What would you need?',
            },
            next: 'futuro-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'planillas-1': {
        text: {
          es:
            'Porque cada una nacio distinto: la libreta de Nelida, la ' +
            'copia que saco el otro turno, lo que mantenimiento ' +
            'recuerda. Sumas la misma semana en dos planillas y dan ' +
            'totales distintos. ¿A cual le creo? A NINGUNA — y esa es ' +
            'la respuesta que no puedo dar mañana.',
          en:
            'Because each one was born differently: Nelida’s ' +
            'notebook, the other shift’s copy, what maintenance ' +
            'remembers. Add up the same week on two sheets and you get ' +
            'different totals. Which one do I trust? NEITHER — and ' +
            'that is the answer I cannot give tomorrow.',
        },
        options: [
          {
            label: {
              es: '¿Que necesitaria usted?',
              en: 'What would you need?',
            },
            next: 'futuro-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'futuro-1': {
        text: {
          es:
            'UNA fuente: que cada parada entre una sola vez, cuando ' +
            'pasa, con causa y hora — y que el reporte salga de ahi, no ' +
            'de mi calculadora. Contrataron a un muchacho de sistemas ' +
            'que anda haciendo preguntas... Le voy a dar UNA ' +
            'oportunidad. Una.',
          en:
            'ONE source: every stoppage entered once, when it happens, ' +
            'with cause and time — and the report drawn from there, not ' +
            'from my calculator. They hired a systems kid who keeps ' +
            'asking questions... I will give him ONE chance. One.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: {
              es: 'La va a aprovechar',
              en: 'He will make it count',
            },
            next: null,
          },
        ],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
