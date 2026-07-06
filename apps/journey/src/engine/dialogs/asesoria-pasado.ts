/**
 * @module dialogs/asesoria-pasado (engine)
 * @description Arboles de dialogo de la sala 5 pasado: PROSALUD antes del
 *   sistema (2015). Los DOS hilos del caos en el mismo pasado (informe
 *   17): el instituto en papel (papelitos de turno a mano, cuaderno de
 *   farmacia con tachones, archivador de afiliados) y la mesa de tesis
 *   BLOQUEADA (stack trace, pizarra sin plan, la fecha de defensa rodeada
 *   en rojo, meses tachados en el calendario). 3 NPCs frustrados: Jhonny
 *   Parra junto al codigo que no compila, Coromoto Linares con el
 *   cuaderno y Maigualida Torres con los papelitos — los tres reaparecen
 *   en el presente usando (y defendiendo) el sistema.
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const ASESORIA_PASADO_DIALOGS = {
  jhonny: defineDialog({
    name: { es: 'Jhonny Parra', en: 'Jhonny Parra' },
    chatter: [
      {
        es: 'Cuatro meses. CUATRO.',
        en: 'Four months. FOUR.',
      },
      {
        es: 'Esto no compila desde agosto.',
        en: 'This has not compiled since August.',
      },
      {
        es: 'La defensa es en diciembre y no se ni que hay aqui.',
        en: 'The defence is in December and I do not even know what is in here.',
      },
      {
        es: 'Otro error fatal. Otro. OTRO.',
        en: 'Another fatal error. Another. ANOTHER.',
      },
      {
        es: 'Alguien nos hablo de un tal Pablo...',
        en: 'Someone told us about this Pablo guy...',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'No te acerques mucho, que esto contagia mala suerte. Soy ' +
            'Jhonny, tesista... de una tesis que no avanza desde agosto. ' +
            'Y la defensa es el quince de diciembre. ¿Que quieres?',
          en:
            'Do not come too close, this thing spreads bad luck. I am ' +
            'Jhonny, thesis student... of a thesis that has not moved ' +
            'since August. And the defence is December fifteenth. What do ' +
            'you want?',
        },
        options: [
          {
            label: {
              es: '¿Que le pasa al codigo?',
              en: 'What is wrong with the code?',
            },
            next: 'roto-1',
          },
          {
            label: {
              es: '¿Y esa fecha en rojo?',
              en: 'And that date in red?',
            },
            next: 'fecha-1',
          },
          {
            label: {
              es: '¿Quien es "el tal Pablo"?',
              en: 'Who is "this Pablo guy"?',
            },
            next: 'pablo-1',
          },
          {
            label: { es: 'Suerte con eso', en: 'Good luck with that' },
            next: null,
          },
        ],
      },
      'roto-1': {
        text: {
          es:
            'Ni nosotros lo sabemos, y ese es el problema. Paginas que ' +
            'heredamos de intentos anteriores, consultas que se pisan ' +
            'entre si, y este stack trace que no se va con nada. Cada vez ' +
            'que tocamos algo, se rompe otra cosa.',
          en:
            'We do not know either, and that is the problem. Pages ' +
            'inherited from earlier attempts, queries stepping on each ' +
            'other, and this stack trace that will not go away. Every ' +
            'time we touch something, something else breaks.',
        },
        options: [
          {
            label: {
              es: '¿Y la pizarra sin plan?',
              en: 'And the planless whiteboard?',
            },
            next: 'roto-2',
          },
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
        ],
      },
      'roto-2': {
        text: {
          es:
            'Empezamos tres planes distintos y los tachamos todos. Ya ni ' +
            'sabemos que dia toca que. El calendario de al lado dice el ' +
            'resto: agosto tachado, septiembre tachado, octubre tachado. ' +
            'El tiempo se nos fue en pelear con codigo ajeno.',
          en:
            'We started three different plans and crossed them all out. ' +
            'We no longer know which day is for what. The calendar next ' +
            'to it says the rest: August crossed out, September crossed ' +
            'out, October crossed out. Our time went into fighting ' +
            'someone else’s code.',
        },
        options: [
          {
            label: {
              es: '¿Y que van a hacer?',
              en: 'So what will you do?',
            },
            next: 'pablo-1',
          },
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
        ],
      },
      'fecha-1': {
        text: {
          es:
            'DEFENSA: 15 DIC. La rodee en rojo yo mismo, para que doliera ' +
            'todos los dias. Si no llegamos, perdemos el año... y el ' +
            'instituto se queda sin su sistema, que es lo que mas le ' +
            'duele a la doctora Graterol.',
          en:
            'DEFENCE: DEC 15. I circled it in red myself, so it would ' +
            'hurt every single day. If we miss it, we lose the year... ' +
            'and the institute loses its system, which is what pains ' +
            'doctor Graterol the most.',
        },
        options: [
          {
            label: {
              es: '¿Hay algun plan B?',
              en: 'Is there a plan B?',
            },
            next: 'pablo-1',
          },
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
        ],
      },
      'pablo-1': {
        text: {
          es:
            'La doctora dice que conocio a un muchacho que hizo el ' +
            'sistema del IAI y antes el del IPASME. Que cobra por el ' +
            'trabajo, pero que ENTREGA. Lo va a contratar en noviembre: ' +
            'que desarrolle el la solucion y que nos enseñe a ' +
            'defenderla. Yo ya no creo en milagros... pero firmo.',
          en:
            'The doctor says she met a young man who built the IAI ' +
            'system and the IPASME one before that. He charges for the ' +
            'work, but he DELIVERS. She will hire him in November: he ' +
            'builds the solution and teaches us to defend it. I no ' +
            'longer believe in miracles... but sign me up.',
        },
        options: [
          {
            label: {
              es: 'Cruza y ve como termina',
              en: 'Cross over and see how it ends',
            },
            next: 'pablo-2',
          },
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
        ],
      },
      'pablo-2': {
        text: {
          es:
            '¿Como que del otro lado de la grieta esta diciembre y el ' +
            'sistema funcionando? No me digas mas: no quiero spoilers. ' +
            'Aqui todavia es la peor semana de mi vida academica.',
          en:
            'What do you mean December is on the other side of the rift ' +
            'with the system running? Say no more: no spoilers. Here it ' +
            'is still the worst week of my academic life.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
          {
            label: { es: 'Nos vemos alla', en: 'See you over there' },
            next: null,
          },
        ],
      },
    },
  }),

  coromoto: defineDialog({
    name: { es: 'Coromoto Linares', en: 'Coromoto Linares' },
    chatter: [
      {
        es: 'Se acabo el acetaminofen. Y me entere en la ventanilla.',
        en: 'Paracetamol ran out. And I found out at the window.',
      },
      {
        es: 'Este cuaderno tiene mas tachones que letras.',
        en: 'This notebook has more scribbles than words.',
      },
      {
        es: '¿Alguien vio la pagina de octubre? La arranque sin querer.',
        en: 'Anyone seen the October page? I tore it out by accident.',
      },
      {
        es: 'Viernes: contar cajas. Otra vez.',
        en: 'Friday: counting boxes. Again.',
      },
      {
        es: 'Ojala algo me avisara ANTES de quedarme sin nada.',
        en: 'I wish something warned me BEFORE I run out.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Coromoto, farmacia. Mi inventario es este cuaderno, y el ' +
            'cuaderno miente: dice que hay acetaminofen y la caja esta ' +
            'vacia. ¿Que necesitas? Espero que no sea acetaminofen.',
          en:
            'Coromoto, pharmacy. My inventory is this notebook, and the ' +
            'notebook lies: it says there is paracetamol and the box is ' +
            'empty. What do you need? I hope not paracetamol.',
        },
        options: [
          {
            label: {
              es: '¿Por que miente el cuaderno?',
              en: 'Why does the notebook lie?',
            },
            next: 'cuaderno-1',
          },
          {
            label: {
              es: '¿Que paso con el acetaminofen?',
              en: 'What happened with the paracetamol?',
            },
            next: 'stock-1',
          },
          {
            label: { es: 'Nada, disculpe', en: 'Nothing, sorry' },
            next: null,
          },
        ],
      },
      'cuaderno-1': {
        text: {
          es:
            'Porque se escribe DESPUES de despachar, cuando hay cola no ' +
            'se escribe, y cuando se escribe, se tacha. Mira: entrada, ' +
            'tachon, salida, tachon, un numero que ni yo entiendo. El ' +
            'inventario real solo existe contando cajas.',
          en:
            'Because it gets written AFTER dispatching, when there is a ' +
            'queue nothing gets written, and what gets written gets ' +
            'crossed out. Look: stock in, scribble, stock out, scribble, ' +
            'a number even I cannot read. The real inventory only exists ' +
            'by counting boxes.',
        },
        options: [
          {
            label: {
              es: '¿Y eso cuando se arregla?',
              en: 'And when does that get fixed?',
            },
            next: 'deseo-1',
          },
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
        ],
      },
      'stock-1': {
        text: {
          es:
            'Que se acabo un martes y yo me entere el miercoles, con la ' +
            'señora Petra en la ventanilla y su record en la mano. "No ' +
            'hay, mi amor, vuelva la semana que viene". Ella vino desde ' +
            'Aroa. DESDE AROA. Ese dia odie este cuaderno.',
          en:
            'It ran out on a Tuesday and I found out on Wednesday, with ' +
            'Mrs Petra at the window holding her slip. "None left, dear, ' +
            'come back next week". She came from Aroa. FROM AROA. I hated ' +
            'this notebook that day.',
        },
        options: [
          {
            label: {
              es: '¿Que pediria usted?',
              en: 'What would you ask for?',
            },
            next: 'deseo-1',
          },
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
        ],
      },
      'deseo-1': {
        text: {
          es:
            'Dicen que la doctora va a contratar al muchacho de la tesis ' +
            'para que haga un sistema. Si ese muchacho me pregunta, yo le ' +
            'pido UNA sola cosa: que algo se ponga rojo y me grite ANTES ' +
            'de que se acabe. Con eso me cambia la vida.',
          en:
            'They say the doctor will hire the thesis young man to build ' +
            'a system. If that young man asks me, I will request ONE ' +
            'thing: something that turns red and yells at me BEFORE it ' +
            'runs out. That alone changes my life.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
          {
            label: {
              es: 'Se lo van a cumplir',
              en: 'They will grant you that',
            },
            next: null,
          },
        ],
      },
    },
  }),

  maigualida: defineDialog({
    name: { es: 'Maigualida Torres', en: 'Maigualida Torres' },
    chatter: [
      {
        es: 'Numero cuarenta y dos... ¿y el cuarenta y uno?',
        en: 'Number forty-two... and where is forty-one?',
      },
      {
        es: 'Señora, si pierde el papelito pierde el turno.',
        en: 'Ma’am, lose the slip and you lose the turn.',
      },
      {
        es: 'Dos señores con el mismo numero. Otra vez.',
        en: 'Two men with the same number. Again.',
      },
      {
        es: 'La cola llega hasta la puerta. Son las nueve.',
        en: 'The queue reaches the door. It is nine a.m.',
      },
      {
        es: 'Asi no se puede. Asi NO se puede.',
        en: 'This cannot go on. It CANNOT.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Maigualida, admision... y arbitro de la cola. Reparto ' +
            'papelitos numerados a mano desde las siete y a esta hora ya ' +
            'perdi la cuenta de las peleas. ¿Que quieres, mi amor? Rapido ' +
            'que el cuarenta y dos anda perdido.',
          en:
            'Maigualida, admissions... and queue referee. I have been ' +
            'handing out hand-numbered slips since seven and by now I ' +
            'lost count of the fights. What do you need, dear? Quick, ' +
            'number forty-two has gone missing.',
        },
        options: [
          {
            label: {
              es: '¿Como funciona el papelito?',
              en: 'How does the slip work?',
            },
            next: 'papelito-1',
          },
          {
            label: {
              es: '¿Y las carpetas de afiliados?',
              en: 'And the member folders?',
            },
            next: 'carpetas-1',
          },
          {
            label: { es: 'Nada, suerte con la cola', en: 'Nothing, good luck' },
            next: null,
          },
        ],
      },
      'papelito-1': {
        text: {
          es:
            'Corto los papelitos en la mañana y los numero a lapiz. El ' +
            'que llega, agarra el suyo del pincho. Hasta ahi la teoria. ' +
            'La practica: se pierden, se mojan, se repiten... y cuando ' +
            'dos personas juran tener el mismo turno, la que arbitra soy ' +
            'yo.',
          en:
            'I cut the slips in the morning and number them in pencil. ' +
            'Whoever arrives takes theirs from the spike. That is the ' +
            'theory. The practice: they get lost, soaked, duplicated... ' +
            'and when two people swear they hold the same turn, I am the ' +
            'referee.',
        },
        options: [
          {
            label: {
              es: '¿Y eso cuanto cuesta al dia?',
              en: 'And what does that cost per day?',
            },
            next: 'papelito-2',
          },
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
        ],
      },
      'papelito-2': {
        text: {
          es:
            'La mañana entera. La gente viene de los catorce municipios ' +
            'del estado, algunos desde las cinco de la madrugada, y ' +
            'pierden el dia por un papelito. Eso no es un mal dia: es ' +
            'todos los dias. Por eso digo que asi no se puede.',
          en:
            'The whole morning. People come from all fourteen municipios ' +
            'of the state, some setting off at five a.m., and they lose ' +
            'the day over a slip. That is not a bad day: it is every ' +
            'day. That is why I say this cannot go on.',
        },
        options: [
          {
            label: {
              es: '¿Nadie va a arreglarlo?',
              en: 'Will nobody fix it?',
            },
            next: 'esperanza-1',
          },
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
        ],
      },
      'carpetas-1': {
        text: {
          es:
            'Cada afiliado tiene su carpeta manila en el archivador. ' +
            'Buscar una es hojear: apellido, municipio, año... y rezar. ' +
            'Con la cola esperando, cada carpeta que no aparece son diez ' +
            'personas mas de mal humor.',
          en:
            'Every member has a manila folder in the cabinet. Finding ' +
            'one means leafing through: surname, municipio, year... and ' +
            'praying. With the queue waiting, every folder that does not ' +
            'show up is ten more people in a bad mood.',
        },
        options: [
          {
            label: {
              es: '¿Nadie va a arreglarlo?',
              en: 'Will nobody fix it?',
            },
            next: 'esperanza-1',
          },
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
        ],
      },
      'esperanza-1': {
        text: {
          es:
            'La doctora anda diciendo que en noviembre llega un muchacho ' +
            'que hace sistemas — el mismo de la tesis de los estudiantes. ' +
            'Que el display cantara el turno solo y que el afiliado ' +
            'saldra con la cedula. Yo, mientras no lo vea... sigo ' +
            'cortando papelitos.',
          en:
            'The doctor keeps saying a young man who builds systems ' +
            'arrives in November — the same one from the students’ ' +
            'thesis. That a display will call the tickets by itself and ' +
            'members will pop up from their ID. Until I see it... I keep ' +
            'cutting slips.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back' }, next: 'hub' },
          {
            label: {
              es: 'Lo va a ver pronto',
              en: 'You will see it soon',
            },
            next: null,
          },
        ],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
