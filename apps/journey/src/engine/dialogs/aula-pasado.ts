/**
 * @module dialogs/aula-pasado (engine)
 * @description Arboles de dialogo del "antes" del aula (sepia, Venezuela
 *   pre-universitaria): tres versiones del mismo Pablo joven, partido en
 *   tres por la grieta temporal — el karateka del tatami, el gamer frente
 *   al GTA San Andreas y el tecnico de aires que ahorra para la
 *   universidad. Los tres hablan en primera persona y se reconocen.
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const AULA_PASADO_DIALOGS = {
  'pablo-karateka': defineDialog({
    name: { es: 'Pablo karateka', en: 'Karateka Pablo' },
    chatter: [
      {
        es: '¡Mil golpes al dia, ni uno menos!',
        en: 'A thousand strikes a day, not one less!',
      },
      {
        es: 'Ichi, ni, san... ¿por donde iba?',
        en: 'Ichi, ni, san... where was I?',
      },
      {
        es: 'Algun dia voy a construir mis propios juegos.',
        en: 'Someday I will build my own games.',
      },
      {
        es: 'El makiwara no miente.',
        en: 'The makiwara does not lie.',
      },
      { es: 'Osu.', en: 'Osu.' },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            '¡Osu! Perdona el salto, es la costumbre del dojo. ' +
            'Bienvenido a mi rincon: tatami, una PC que ruge y un ' +
            'aire a medio armar. Y si: los tres de aqui somos el ' +
            'mismo Pablo. Despues de ver esa grieta, ser tres ya ' +
            'no me parece tan raro. ¿De que quieres hablar?',
          en:
            'Osu! Sorry about the jump, dojo habit. Welcome to my ' +
            'corner: a tatami, a roaring PC and a half-assembled ' +
            'AC unit. And yes: the three of us here are the same ' +
            'Pablo. After seeing that crack, being three does not ' +
            'feel that strange anymore. What do you want to talk ' +
            'about?',
        },
        options: [
          {
            label: { es: 'Cuentame del karate', en: 'Tell me about karate' },
            next: 'k1',
          },
          {
            label: { es: 'Hay mas temas, ¿no?', en: 'There is more, right?' },
            next: 'hub2',
          },
          { label: { es: 'Hasta luego', en: 'See you later' }, next: null },
        ],
      },
      hub2: {
        text: {
          es:
            'Claro que hay mas. Mi vida es un combo: golpes, pixeles ' +
            'y tuberias de cobre. ¿Por donde seguimos?',
          en:
            'Of course there is more. My life is a combo: strikes, ' +
            'pixels and copper pipes. Where to next?',
        },
        options: [
          {
            label: { es: 'Los videojuegos', en: 'The video games' },
            next: 'g1',
          },
          {
            label: { es: 'El trabajo de aires', en: 'The AC job' },
            next: 'a1',
          },
          { label: { es: 'Otra cosa', en: 'Something else' }, next: 'hub3' },
        ],
      },
      hub3: {
        text: {
          es:
            'Tambien esta lo que sueño de noche... y una pregunta ' +
            'rara que me ronda desde que llegaste.',
          en:
            'There is also what I dream about at night... and a ' +
            'strange question circling my head since you arrived.',
        },
        options: [
          {
            label: {
              es: 'Tu sueño de estudiar',
              en: 'Your dream of studying',
            },
            next: 'u1',
          },
          {
            label: {
              es: '¿Que pregunta rara?',
              en: 'What strange question?',
            },
            next: 'f1',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      k1: {
        text: {
          es:
            'Karate-Do. Entreno kihon en este tatami todos los dias, ' +
            'y el makiwara de alla ya conoce mis nudillos mejor que ' +
            'yo.',
          en:
            'Karate-Do. I train kihon on this tatami every day, and ' +
            'that makiwara over there knows my knuckles better than ' +
            'me.',
        },
        options: [
          {
            label: { es: '¿Que es el kihon?', en: 'What is kihon?' },
            next: 'k2',
          },
          {
            label: {
              es: '¿Y ese poste con cuerda?',
              en: 'What about that roped post?',
            },
            next: 'k7',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      k2: {
        text: {
          es:
            'Kihon es la base: el mismo golpe, la misma postura, una ' +
            'y otra vez. Nada de trucos. Pura fundacion.',
          en:
            'Kihon is the basics: the same strike, the same stance, ' +
            'over and over. No tricks. Pure foundation.',
        },
        options: [
          {
            label: { es: '¿Cuantas veces repites?', en: 'How many times?' },
            next: 'k3',
          },
          {
            label: { es: '¿No te aburre?', en: 'Does it not bore you?' },
            next: 'k4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      k3: {
        text: {
          es:
            'Mil veces si hace falta. Las cuento bajito: ichi, ni, ' +
            'san... Cuando pierdo la cuenta, empiezo de nuevo.',
          en:
            'A thousand times if needed. I count them quietly: ichi, ' +
            'ni, san... When I lose count, I start over.',
        },
        options: [
          {
            label: { es: '¿Para que tantas?', en: 'Why so many?' },
            next: 'k5',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      k4: {
        text: {
          es:
            'Al principio si. Despues entiendes que el aburrimiento ' +
            'es la puerta: del otro lado el golpe sale solo, sin ' +
            'pensar.',
          en:
            'At first, yes. Then you learn that boredom is the door: ' +
            'on the other side the strike comes out on its own.',
        },
        options: [
          {
            label: { es: '¿Y el talento que?', en: 'What about talent?' },
            next: 'k5',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      k5: {
        text: {
          es:
            'Repetir un golpe mil veces me ha marcado mas que ' +
            'cualquier manual. La constancia le gana al talento ' +
            'cuando el talento se cansa.',
          en:
            'Repeating one strike a thousand times has shaped me ' +
            'more than any manual. Consistency beats talent when ' +
            'talent gets tired.',
        },
        options: [
          {
            label: {
              es: 'Suena a filosofia',
              en: 'Sounds like philosophy',
            },
            next: 'k6',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      k6: {
        text: {
          es:
            'Sera porque lo es. La disciplina no se queda en el ' +
            'tatami: se viene conmigo al trabajo, a la PC, a todo.',
          en:
            'Maybe because it is. Discipline does not stay on the ' +
            'tatami: it follows me to work, to the PC, to everything.',
        },
        options: [
          { label: { es: 'Sigue', en: 'Go on' }, next: 'k12' },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      k7: {
        text: {
          es:
            'Es un makiwara: un poste para golpear. Le pego todos ' +
            'los dias, con respeto. El respeto no quita que duela.',
          en:
            'That is a makiwara: a striking post. I hit it every ' +
            'day, with respect. Respect does not make it hurt less.',
        },
        options: [
          {
            label: { es: '¿No te lastimas?', en: 'Do you not get hurt?' },
            next: 'k8',
          },
          {
            label: {
              es: '¿Que enseña un poste?',
              en: 'What can a post teach?',
            },
            next: 'k9',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      k8: {
        text: {
          es:
            'Los nudillos protestan la primera semana. Despues se ' +
            'endurecen. El cuerpo aprende antes que la cabeza.',
          en:
            'The knuckles complain for the first week. Then they ' +
            'harden. The body learns before the mind does.',
        },
        options: [
          {
            label: { es: '¿Y sigues igual?', en: 'And you keep going?' },
            next: 'k10',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      k9: {
        text: {
          es:
            'El makiwara no miente. Si el golpe salio torcido, el ' +
            'brazo lo siente al instante. Es el juez mas honesto ' +
            'que conozco.',
          en:
            'The makiwara does not lie. If the strike came out ' +
            'crooked, the arm feels it instantly. The most honest ' +
            'judge I know.',
        },
        options: [
          {
            label: {
              es: '¿Y que haces con eso?',
              en: 'What do you do with that?',
            },
            next: 'k10',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      k10: {
        text: {
          es:
            'Cada golpe corrige al anterior. Golpe, error, ajuste, ' +
            'golpe. Un ciclo chiquito que repito hasta que sale ' +
            'limpio.',
          en:
            'Each strike corrects the last one. Strike, error, ' +
            'adjust, strike. A tiny loop I repeat until it comes ' +
            'out clean.',
        },
        options: [
          { label: { es: 'Buen metodo', en: 'Good method' }, next: 'k11' },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      k11: {
        text: {
          es:
            'Es EL metodo. Mil repeticiones honestas valen mas que ' +
            'cualquier manual. Lo digo yo y lo confirma mi makiwara.',
          en:
            'It is THE method. A thousand honest repetitions are ' +
            'worth more than any manual. I say it and my makiwara ' +
            'confirms it.',
        },
        options: [
          { label: { es: 'Sigue', en: 'Go on' }, next: 'k12' },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      k12: {
        text: {
          es:
            'Un dia esta disciplina va a empujar algo mas grande ' +
            'que un golpe. Todavia no se que, pero ya la estoy ' +
            'entrenando.',
          en:
            'One day this discipline will push something bigger ' +
            'than a strike. I do not know what yet, but I am ' +
            'already training it.',
        },
        options: [
          {
            label: { es: '¿Y la PC que?', en: 'What about the PC?' },
            next: 'g1',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      g1: {
        text: {
          es:
            'Esa PC vieja es mi otro dojo. ¿Y el que esta jugando ' +
            'ahi? Tambien soy yo: mi lado gamer. La grieta nos ' +
            'partio en tres y a el le toco la silla.',
          en:
            'That old PC is my other dojo. And the one playing ' +
            'there? Also me: my gamer side. The crack split us in ' +
            'three and he got the chair.',
        },
        options: [
          {
            label: {
              es: '¿Que estas jugando?',
              en: 'What are you playing?',
            },
            next: 'g2',
          },
          {
            label: {
              es: '¿Que otra cosa haces?',
              en: 'What else do you do?',
            },
            next: 'g5',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      g2: {
        text: {
          es:
            'GTA San Andreas. Un estado entero dentro de una caja ' +
            'beige. Cada vez que carga me parece un milagro.',
          en:
            'GTA San Andreas. A whole state inside a beige box. ' +
            'Every time it loads it feels like a miracle to me.',
        },
        options: [
          {
            label: { es: '¿Quien juega mejor?', en: 'Who plays better?' },
            next: 'g3',
          },
          {
            label: {
              es: '¿Corre bien aqui?',
              en: 'Does it run well here?',
            },
            next: 'g4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      g3: {
        text: {
          es:
            'Mi yo gamer, sin discusion. Este yo se distrae: a ' +
            'mitad de mision me quedo mirando como se mueve la ' +
            'ciudad, y pierdo.',
          en:
            'My gamer self, no contest. This me gets distracted: ' +
            'mid-mission I just stare at how the city moves, and ' +
            'I lose.',
        },
        options: [
          {
            label: { es: '¿Mirando que?', en: 'Staring at what?' },
            next: 'g5',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      g4: {
        text: {
          es:
            'Se arrastra un poco, pero corre. Cuando bajan los ' +
            'frames pienso: algo ahi adentro trabaja demasiado. ' +
            '¿Que sera?',
          en:
            'It crawls a bit, but it runs. When the frames drop I ' +
            'think: something in there is working too hard. What ' +
            'could it be?',
        },
        options: [
          {
            label: { es: 'Buena pregunta', en: 'Good question' },
            next: 'g5',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      g5: {
        text: {
          es:
            'Antes mi pregunta era "¿como se gana?". Un dia cambio ' +
            'sola: "¿como se HACE esto?". Y ya no pude volver atras.',
          en:
            'My question used to be "how do you win?". One day it ' +
            'changed by itself: "how is this MADE?". No way back ' +
            'since.',
        },
        options: [
          {
            label: {
              es: '¿Como se te ocurrio?',
              en: 'How did it hit you?',
            },
            next: 'g6',
          },
          {
            label: {
              es: '¿Y que haces al respecto?',
              en: 'And what do you do about it?',
            },
            next: 'g7',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      g6: {
        text: {
          es:
            'Fue con los creditos. Los deje correr completos y vi ' +
            'cientos de nombres. Personas reales hicieron ese ' +
            'mundo. Personas como yo.',
          en:
            'It was the credits. I let them roll to the end and saw ' +
            'hundreds of names. Real people built that world. ' +
            'People like me.',
        },
        options: [
          { label: { es: '¿Y despues?', en: 'And then?' }, next: 'g7' },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      g7: {
        text: {
          es:
            'Husmeo. Abro las carpetas del juego y miro los ' +
            'archivos: texturas, sonidos, cosas con nombres raros. ' +
            'Mi lado gamer se desespera.',
          en:
            'I snoop. I open the game folders and look at the ' +
            'files: textures, sounds, things with weird names. My ' +
            'gamer side despairs.',
        },
        options: [
          {
            label: {
              es: '¿Entiendes algo?',
              en: 'Do you understand any of it?',
            },
            next: 'g8',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      g8: {
        text: {
          es:
            'Casi nada, y eso es lo mejor. Cada archivo es una ' +
            'pista de como esta armado el sistema por dentro. Un ' +
            'mapa a medio revelar.',
          en:
            'Almost nothing, and that is the best part. Every file ' +
            'is a clue to how the system is built inside. A ' +
            'half-revealed map.',
        },
        options: [
          {
            label: {
              es: '¿A donde lleva el mapa?',
              en: 'Where does the map lead?',
            },
            next: 'g9',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      g9: {
        text: {
          es:
            'A una idea fija: quiero aprender a construir esto. No ' +
            'solo jugar mundos ajenos. Hacer los mios.',
          en:
            'To one fixed idea: I want to learn to build this. Not ' +
            'just play worlds made by others. Make my own.',
        },
        options: [
          {
            label: { es: 'Eso es una semilla', en: 'That is a seed' },
            next: 'g10',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      g10: {
        text: {
          es:
            'Una semilla, si. Por eso ahorro y por eso estudio de ' +
            'noche. La universidad es el agua que le falta.',
          en:
            'A seed, yes. That is why I save and why I study at ' +
            'night. University is the water it still needs.',
        },
        options: [
          {
            label: {
              es: 'Cuentame de ese plan',
              en: 'Tell me about that plan',
            },
            next: 'u1',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      a1: {
        text: {
          es:
            'De dia soy tecnico de aires acondicionados. Ese rincon ' +
            'de herramientas es mi oficina... bueno, mi oficina son ' +
            'los techos.',
          en:
            'By day I am an air conditioning technician. That ' +
            'corner of tools is my office... well, my office is ' +
            'the rooftops.',
        },
        options: [
          {
            label: {
              es: '¿Que haces exactamente?',
              en: 'What exactly do you do?',
            },
            next: 'a2',
          },
          {
            label: { es: '¿Por que ese trabajo?', en: 'Why that job?' },
            next: 'a6',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      a2: {
        text: {
          es:
            'Diagnosticar, desarmar, reparar. Llega un equipo que ' +
            'no enfria y hay que descubrir por que, sin que nadie ' +
            'te lo diga.',
          en:
            'Diagnose, take apart, repair. A unit arrives that ' +
            'will not cool and you must find out why, with nobody ' +
            'telling you.',
        },
        options: [
          {
            label: {
              es: '¿Como lo descubres?',
              en: 'How do you find out?',
            },
            next: 'a3',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      a3: {
        text: {
          es:
            'Por los sintomas. Escuchas el ruido, mides, descartas ' +
            'una causa, pruebas otra. Paso a paso hasta acorralar ' +
            'la falla.',
          en:
            'Through the symptoms. You listen to the noise, ' +
            'measure, rule out one cause, try the next. Step by ' +
            'step until the fault is cornered.',
        },
        options: [
          {
            label: {
              es: 'Eso es debugging',
              en: 'That is debugging',
            },
            next: 'a4',
          },
          {
            label: { es: '¿Te gusta hacerlo?', en: 'Do you enjoy it?' },
            next: 'a5',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      a4: {
        text: {
          es:
            '¿Debu... que? Suena a palabra del futuro. Pero si asi ' +
            'se llama perseguir fallas con paciencia, entonces si: ' +
            'eso hago todo el dia.',
          en:
            'De-bug... what? Sounds like a word from the future. ' +
            'But if that is the name for chasing faults with ' +
            'patience, then yes: I do that all day.',
        },
        options: [
          {
            label: { es: 'Algo asi, si', en: 'Something like that' },
            next: 'a5',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      a5: {
        text: {
          es:
            'Me encanta el momento exacto en que el equipo arranca ' +
            'y sale aire frio. Es como ganar un combate sin tirar ' +
            'un solo golpe.',
          en:
            'I love the exact moment the unit starts up and cold ' +
            'air comes out. Like winning a match without throwing ' +
            'a single strike.',
        },
        options: [
          {
            label: { es: 'Y ademas te pagan', en: 'And they pay you' },
            next: 'a7',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      a6: {
        text: {
          es:
            'Para pagarme la universidad. Aqui el calor no perdona, ' +
            'asi que trabajo nunca falta. Cada equipo reparado es ' +
            'un ladrillo mas.',
          en:
            'To pay for university. The heat here shows no mercy, ' +
            'so there is never a shortage of work. Every repaired ' +
            'unit is one more brick.',
        },
        options: [
          { label: { es: '¿Es duro?', en: 'Is it hard?' }, next: 'a7' },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      a7: {
        text: {
          es:
            'Duro es: techos hirviendo al mediodia, equipos ' +
            'pesados. Pero es trabajo honesto y tiene su ciencia, ' +
            'aunque no lo parezca.',
          en:
            'Hard it is: boiling rooftops at noon, heavy units. ' +
            'But it is honest work and it has its science, even ' +
            'if it does not look like it.',
        },
        options: [
          {
            label: { es: '¿Quien te enseño?', en: 'Who taught you?' },
            next: 'a8',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      a8: {
        text: {
          es:
            'Un maestro veterano me enseño el oficio; hoy anda en ' +
            'otro techo. ¿Y el que esta arrodillado con el aire? ' +
            'Tambien soy yo: mi lado tecnico.',
          en:
            'A veteran master taught me the trade; he is on some ' +
            'other rooftop today. And the one kneeling by the AC ' +
            'unit? Also me: my technician side.',
        },
        options: [
          {
            label: {
              es: '¿Que aprendiste de el?',
              en: 'What did you learn from him?',
            },
            next: 'a9',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      a9: {
        text: {
          es:
            'Que todo es un sistema: el frio viaja, se pierde, ' +
            'vuelve. Si entiendes el todo, la pieza rota se delata ' +
            'sola.',
          en:
            'That everything is a system: the cold travels, leaks, ' +
            'returns. If you understand the whole, the broken part ' +
            'gives itself away.',
        },
        options: [
          {
            label: {
              es: 'Aplica a muchas cosas',
              en: 'That applies to a lot',
            },
            next: 'a10',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      a10: {
        text: {
          es:
            'Eso mismo pienso yo. Siento que reparar aires me ' +
            'entrena para algo mas grande. Todavia no se ponerle ' +
            'nombre.',
          en:
            'That is exactly what I think. Fixing AC units feels ' +
            'like training for something bigger. I just cannot ' +
            'name it yet.',
        },
        options: [
          {
            label: {
              es: 'Cuentame de ese algo',
              en: 'Tell me about that something',
            },
            next: 'u1',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      u1: {
        text: {
          es:
            'Quiero estudiar computacion. Ingenieria. Aprender de ' +
            'verdad como se construyen los sistemas que me quitan ' +
            'el sueño.',
          en:
            'I want to study computing. Engineering. To truly ' +
            'learn how the systems that keep me up at night are ' +
            'built.',
        },
        options: [
          {
            label: { es: '¿Por que computacion?', en: 'Why computing?' },
            next: 'u2',
          },
          {
            label: {
              es: '¿Como lo vas a pagar?',
              en: 'How will you pay for it?',
            },
            next: 'u3',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      u2: {
        text: {
          es:
            'Los juegos me hicieron la pregunta y las maquinas me ' +
            'dieron pistas. La universidad tiene las respuestas ' +
            'que me faltan.',
          en:
            'Games asked me the question and machines gave me ' +
            'clues. University holds the answers I am still ' +
            'missing.',
        },
        options: [
          {
            label: {
              es: '¿Y mientras tanto?',
              en: 'And in the meantime?',
            },
            next: 'u4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      u3: {
        text: {
          es:
            'Con los aires. Cada reparacion suma. No es rapido, ' +
            'pero tampoco tengo apuro: tengo constancia, que rinde ' +
            'mas.',
          en:
            'With the AC units. Every repair adds up. It is not ' +
            'fast, but I am in no hurry: I have consistency, which ' +
            'pays more.',
        },
        options: [
          {
            label: {
              es: '¿Y mientras ahorras?',
              en: 'And while you save?',
            },
            next: 'u4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      u4: {
        text: {
          es:
            'Aplico el kihon al estudio: un poco cada dia, sin ' +
            'fallar ni uno. Los libros que consigo, apuntes, lo ' +
            'que caiga.',
          en:
            'I apply kihon to studying: a little every day, never ' +
            'missing one. The books I can get, notes, whatever ' +
            'comes my way.',
        },
        options: [
          {
            label: {
              es: '¿Y si no lo logras?',
              en: 'What if you fail?',
            },
            next: 'u5',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      u5: {
        text: {
          es:
            'En el dojo dicen: caer siete veces, levantarse ocho. ' +
            'Si un camino se cierra, golpeo mil veces hasta abrir ' +
            'otro.',
          en:
            'In the dojo they say: fall seven times, rise eight. ' +
            'If one path closes, I strike a thousand times to ' +
            'open another.',
        },
        options: [
          {
            label: {
              es: '¿Que imaginas al final?',
              en: 'What do you picture?',
            },
            next: 'u6',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      u6: {
        text: {
          es:
            'Me imagino construyendo programas que use gente de ' +
            'verdad. Sistemas que funcionen tan bien que nadie ' +
            'note el esfuerzo.',
          en:
            'I picture myself building programs real people use. ' +
            'Systems that work so well nobody notices the effort ' +
            'behind them.',
        },
        options: [
          {
            label: {
              es: 'Brindo por eso',
              en: 'I will toast to that',
            },
            next: 'u7',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      u7: {
        text: {
          es:
            'Gracias. Un golpe a la vez, un ahorro a la vez, un ' +
            'apunte a la vez. Asi se llega. Bueno... eso espero.',
          en:
            'Thank you. One strike at a time, one saving at a ' +
            'time, one note at a time. That is how you get there. ' +
            'I hope.',
        },
        options: [
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
          {
            label: {
              es: 'Lo vas a lograr. Adios',
              en: 'You will make it. Bye',
            },
            next: null,
          },
        ],
      },
      f1: {
        text: {
          es:
            'Baja la voz un momento... Tu no eres de por aqui, ' +
            '¿cierto? Hay una grieta rara ahi afuera y tu hueles ' +
            'a... despues.',
          en:
            'Lower your voice for a moment... You are not from ' +
            'around here, right? There is a strange crack out ' +
            'there and you smell of... later.',
        },
        options: [
          {
            label: {
              es: '¿Como lo supiste?',
              en: 'How did you know?',
            },
            next: 'f2',
          },
          {
            label: {
              es: 'Vengo de mas adelante, si',
              en: 'I come from later on, yes',
            },
            next: 'f3',
          },
          {
            label: { es: 'Mejor volvamos', en: 'Let us go back' },
            next: 'hub',
          },
        ],
      },
      f2: {
        text: {
          es:
            'Intuicion de karateka. Miras este lugar como quien ' +
            'mira una foto vieja: con cariño y con ventaja. Nadie ' +
            'mira asi su presente. Y oye: al que la grieta partio ' +
            'en tres, nada le parece raro ya.',
          en:
            'Karateka intuition. You look at this place like ' +
            'someone looking at an old photo: with fondness and an ' +
            'advantage. Nobody sees their present like that. And ' +
            'hey: nothing looks strange anymore to someone the ' +
            'crack split in three.',
        },
        options: [
          { label: { es: 'Touche', en: 'Touche' }, next: 'f3' },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      f3: {
        text: {
          es:
            'Entonces dime solo una cosa, sin detalles: ¿como le ' +
            'va al Pablo de alla? Al de tu lado de la grieta.',
          en:
            'Then tell me just one thing, no details: how is the ' +
            'Pablo over there doing? The one on your side of the ' +
            'crack.',
        },
        options: [
          {
            label: {
              es: 'Le va bien. Construye cosas',
              en: 'He is doing well. He builds',
            },
            next: 'f4',
          },
          {
            label: {
              es: 'Descubrelo tu mismo',
              en: 'Find out yourself',
            },
            next: 'f5',
          },
        ],
      },
      f4: {
        text: {
          es:
            '¿Construye...? Ja. Entonces las mil repeticiones ' +
            'sirven. No me cuentes mas: no quiero spoilers de mi ' +
            'propia vida.',
          en:
            'He builds things...? Ha. Then the thousand ' +
            'repetitions work. Tell me no more: no spoilers of my ' +
            'own life, please.',
        },
        options: [
          { label: { es: 'Trato hecho', en: 'Deal' }, next: 'f6' },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      f5: {
        text: {
          es:
            'Ja, touche. Tienes razon: si me lo cuentas, deja de ' +
            'ser mio. Prefiero ganarme ese futuro golpe a golpe.',
          en:
            'Ha, touche. You are right: if you tell me, it stops ' +
            'being mine. I would rather earn that future strike ' +
            'by strike.',
        },
        options: [
          {
            label: {
              es: 'Asi se habla',
              en: 'That is the spirit',
            },
            next: 'f6',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      f6: {
        text: {
          es:
            'Cuando vuelvas a cruzar la grieta, saludalo de mi ' +
            'parte. Dile que aqui seguimos entrenando para no ' +
            'dejarlo mal.',
          en:
            'When you cross the crack again, say hello to him for ' +
            'me. Tell him we keep training here so we do not let ' +
            'him down.',
        },
        options: [
          {
            label: {
              es: 'Se lo dire. Volvamos',
              en: 'I will tell him. Back',
            },
            next: 'hub',
          },
          {
            label: {
              es: 'Se lo dire. Hasta pronto',
              en: 'I will. See you soon',
            },
            next: null,
          },
        ],
      },
    },
  }),
  'pablo-gamer': defineDialog({
    name: { es: 'Pablo gamer', en: 'Gamer Pablo' },
    chatter: [
      {
        es: 'CJ, sigue el punto rojo... ¡el rojo!',
        en: 'CJ, follow the red dot... the red one!',
      },
      {
        es: 'Esta mision es trampa, lo juro.',
        en: 'This mission is rigged, I swear.',
      },
      {
        es: 'Estos creditos no se saltan. Jamas.',
        en: 'You never skip these credits. Never.',
      },
      {
        es: 'Una partida mas y estudio. Bueno, dos.',
        en: 'One more game and I study. Okay, two.',
      },
      {
        es: 'El del tatami tambien soy yo. Largo de contar.',
        en: 'The one on the tatami is also me. Long story.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Espera, espera... dejame guardar la partida. Listo. ' +
            'Hola. Si, yo tambien soy Pablo: el mismo que salta en ' +
            'el tatami y el que pelea con ese aire. La grieta nos ' +
            'repartio los hobbies. ¿Que quieres saber?',
          en:
            'Wait, wait... let me save the game. Done. Hi. Yes, I ' +
            'am also Pablo: the same one jumping on the tatami and ' +
            'the one fighting that AC unit. The crack split our ' +
            'hobbies. What do you want to know?',
        },
        options: [
          {
            label: {
              es: '¿Que estas jugando?',
              en: 'What are you playing?',
            },
            next: 'j1',
          },
          {
            label: {
              es: 'Eso de ser tres, explica',
              en: 'Explain the three of you',
            },
            next: 's1',
          },
          {
            label: {
              es: 'Sigue jugando, perdon',
              en: 'Keep playing, sorry',
            },
            next: null,
          },
        ],
      },
      j1: {
        text: {
          es:
            'GTA San Andreas, en esta PC vieja que ruge como un ' +
            'avion. Un estado entero dentro de una caja beige. ' +
            'Cada vez que carga me parece un milagro.',
          en:
            'GTA San Andreas, on this old PC that roars like a ' +
            'plane. A whole state inside a beige box. Every time ' +
            'it loads it feels like a miracle.',
        },
        options: [
          {
            label: { es: '¿Corre bien?', en: 'Does it run well?' },
            next: 'j2',
          },
          {
            label: { es: '¿Y juegas bien?', en: 'And do you play well?' },
            next: 'j3',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      j2: {
        text: {
          es:
            'Se arrastra en las persecuciones, pero corre. Cuando ' +
            'bajan los frames pienso: algo ahi adentro trabaja ' +
            'demasiado. ¿Que sera?',
          en:
            'It crawls during chases, but it runs. When the frames ' +
            'drop I think: something in there is working too hard. ' +
            'What could it be?',
        },
        options: [
          {
            label: {
              es: '¿Y eso te intriga?',
              en: 'Does that intrigue you?',
            },
            next: 'j4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      j3: {
        text: {
          es:
            'Mejor que el karateka, que se distrae con el ' +
            'atardecer del juego. Aunque... el karateka soy yo. ' +
            'Digamos que gano y pierdo a la vez.',
          en:
            'Better than the karateka, who gets distracted by the ' +
            'in-game sunset. Although... the karateka is me. Let ' +
            'us say I win and lose at the same time.',
        },
        options: [
          {
            label: {
              es: '¿Que te distrae tanto?',
              en: 'What distracts you so much?',
            },
            next: 'j4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      j4: {
        text: {
          es:
            'Un dia deje correr los creditos COMPLETOS y vi pasar ' +
            'cientos de nombres. Personas reales hicieron este ' +
            'mundo. Personas como yo.',
          en:
            'One day I let the credits roll ALL the way and saw ' +
            'hundreds of names go by. Real people built this ' +
            'world. People like me.',
        },
        options: [
          {
            label: {
              es: '¿Y eso que te hizo?',
              en: 'What did that do to you?',
            },
            next: 'j5',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      j5: {
        text: {
          es:
            'Me cambio la pregunta. Antes era "¿como se gana?". ' +
            'Desde esa noche es "¿como se HACE esto?". Y ya no ' +
            'pude volver atras.',
          en:
            'It changed my question. It used to be "how do you ' +
            'win?". Since that night it is "how is this MADE?". ' +
            'No way back since.',
        },
        options: [
          {
            label: {
              es: '¿Y que haces al respecto?',
              en: 'And what do you do about it?',
            },
            next: 'j6',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      j6: {
        text: {
          es:
            'Husmeo. Abro las carpetas de instalacion y miro los ' +
            'archivos: texturas, sonidos, cosas con nombres raros. ' +
            'Un mapa a medio revelar.',
          en:
            'I snoop. I open the install folders and look at the ' +
            'files: textures, sounds, things with weird names. A ' +
            'half-revealed map.',
        },
        options: [
          {
            label: {
              es: '¿Entiendes algo?',
              en: 'Do you understand any of it?',
            },
            next: 'j7',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      j7: {
        text: {
          es:
            'Casi nada, y eso es lo mejor: cada archivo es una ' +
            'pista de como esta armado el sistema por dentro. Una ' +
            'parte de mi grita "¡asi no se juega!". Yo contesto: ' +
            '"yo juego otro juego".',
          en:
            'Almost nothing, and that is the best part: every ' +
            'file is a clue to how the system is built inside. ' +
            'Part of me yells "that is not how you play!". I ' +
            'answer: "I am playing another game".',
        },
        options: [
          {
            label: {
              es: '¿A donde lleva ese juego?',
              en: 'Where does that game lead?',
            },
            next: 'j8',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      j8: {
        text: {
          es:
            'A una idea fija: quiero construir mis propios mundos. ' +
            'No solo jugar los que hicieron otros. Que algun dia ' +
            'alguien lea MI nombre en unos creditos.',
          en:
            'To one fixed idea: I want to build my own worlds. ' +
            'Not just play the ones others made. Someday somebody ' +
            'will read MY name in some credits.',
        },
        options: [
          {
            label: {
              es: '¿Y como piensas lograrlo?',
              en: 'How will you get there?',
            },
            next: 'u1',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      u1: {
        text: {
          es:
            'La universidad es el plan. Computacion. Ahi debe ' +
            'estar escrito como se hacen estos mundos... o al ' +
            'menos por donde se empieza.',
          en:
            'University is the plan. Computing. That is where it ' +
            'must say how these worlds are made... or at least ' +
            'where to start.',
        },
        options: [
          {
            label: {
              es: '¿Y mientras tanto?',
              en: 'And in the meantime?',
            },
            next: 'u2',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      u2: {
        text: {
          es:
            'Trabajo en equipo conmigo mismo: el tecnico ahorra ' +
            'reparando aires, el karateka pone la disciplina y yo ' +
            'pongo la pregunta. No es mal reparto.',
          en:
            'Teamwork with myself: the technician saves money ' +
            'fixing AC units, the karateka brings discipline and ' +
            'I bring the question. Not a bad split.',
        },
        options: [
          {
            label: {
              es: '¿Y cual manda?',
              en: 'Which one is in charge?',
            },
            next: 'u3',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      u3: {
        text: {
          es:
            'La pregunta manda. "¿Como se HACE esto?" nos levanta ' +
            'a los tres cada mañana. Bueno, al karateka lo ' +
            'levanta el kihon, pero es casi lo mismo.',
          en:
            'The question is in charge. "How is this MADE?" gets ' +
            'the three of us up every morning. Well, kihon gets ' +
            'the karateka up, but that is almost the same.',
        },
        options: [
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
          {
            label: {
              es: 'Suerte con esos mundos. Adios',
              en: 'Good luck with those worlds. Bye',
            },
            next: null,
          },
        ],
      },
      s1: {
        text: {
          es:
            'Facil: la grieta temporal nos partio en tres. El que ' +
            'entrena, el que repara y yo. Mismo Pablo, tres ' +
            'turnos. Ese de alla tambien soy yo.',
          en:
            'Easy: the time crack split us in three. The one ' +
            'training, the one repairing and me. Same Pablo, ' +
            'three shifts. That one over there is also me.',
        },
        options: [
          {
            label: {
              es: '¿Y no te parece raro?',
              en: 'Does it not feel strange?',
            },
            next: 's2',
          },
          {
            label: {
              es: '¿Quien es el original?',
              en: 'Which one is the original?',
            },
            next: 's3',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      s2: {
        text: {
          es:
            '¿Raro? Hay una grieta brillante flotando en medio ' +
            'del aula. Comparado con eso, ser tres es hasta ' +
            'comodo: nunca pierdo mi turno en la PC.',
          en:
            'Strange? There is a glowing crack floating in the ' +
            'middle of the classroom. Next to that, being three ' +
            'is even handy: I never lose my turn at the PC.',
        },
        options: [
          {
            label: {
              es: '¿Y se llevan bien?',
              en: 'Do you get along?',
            },
            next: 's4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      s3: {
        text: {
          es:
            'Los tres. Ninguno es copia: yo pongo la curiosidad, ' +
            'el karateka la constancia y el tecnico la paciencia. ' +
            'Juntos somos el Pablo completo.',
          en:
            'All three. None of us is a copy: I bring curiosity, ' +
            'the karateka brings consistency and the technician ' +
            'brings patience. Together we are the full Pablo.',
        },
        options: [
          {
            label: {
              es: '¿Y se llevan bien?',
              en: 'Do you get along?',
            },
            next: 's4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      s4: {
        text: {
          es:
            'Casi siempre. Discutimos por la silla: yo digo que ' +
            'husmear archivos es investigar, y otro yo dice que ' +
            'es perder la mision. Los dos tenemos razon.',
          en:
            'Almost always. We argue over the chair: I say that ' +
            'snooping files is research, and another me says it ' +
            'is losing the mission. We are both right.',
        },
        options: [
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
          {
            label: {
              es: 'Que gane el mejor Pablo. Adios',
              en: 'May the best Pablo win. Bye',
            },
            next: null,
          },
        ],
      },
    },
  }),
  'pablo-tecnico': defineDialog({
    name: {
      es: 'Pablo tecnico de aires acondicionados',
      en: 'AC technician Pablo',
    },
    chatter: [
      {
        es: 'Este compresor suena a viernes cansado.',
        en: 'This compressor sounds like a tired Friday.',
      },
      {
        es: 'Con este calor, el aire frio es salud.',
        en: 'In this heat, cold air is health.',
      },
      {
        es: 'Como decia mi maestro: primero se escucha.',
        en: 'As my mentor used to say: first you listen.',
      },
      {
        es: 'Un equipo mas, un ladrillo mas.',
        en: 'One more unit, one more brick.',
      },
      {
        es: 'El del tatami tambien soy yo. Si, ya se.',
        en: 'The one on the tatami is also me. Yes, I know.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Pasame esa llave... ah, no, perdona: tu eres visita. ' +
            'Si, tambien soy Pablo. El turno que paga las cuentas. ' +
            'Estoy con esta unidad que no quiere enfriar. ¿Que se ' +
            'te ofrece?',
          en:
            'Hand me that wrench... ah, no, sorry: you are a ' +
            'guest. Yes, I am also Pablo. The shift that pays the ' +
            'bills. I am busy with this unit that refuses to ' +
            'cool. What can I do for you?',
        },
        options: [
          {
            label: {
              es: '¿Que le pasa al equipo?',
              en: 'What is wrong with the unit?',
            },
            next: 't1',
          },
          {
            label: {
              es: '¿Por que este trabajo?',
              en: 'Why this job?',
            },
            next: 'w1',
          },
          {
            label: {
              es: 'Eso de ser tres, explica',
              en: 'Explain the three of you',
            },
            next: 's1',
          },
          {
            label: {
              es: 'Te dejo trabajar',
              en: 'I will let you work',
            },
            next: null,
          },
        ],
      },
      t1: {
        text: {
          es:
            'El compresor no arranca. Podria ser el capacitor, el ' +
            'relay, el cableado... Mi rutina es una sola: ' +
            'diagnosticar, desarmar, reparar.',
          en:
            'The compressor will not start. Could be the ' +
            'capacitor, the relay, the wiring... My routine is ' +
            'one and the same: diagnose, take apart, repair.',
        },
        options: [
          {
            label: {
              es: '¿Como diagnosticas?',
              en: 'How do you diagnose?',
            },
            next: 't2',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      t2: {
        text: {
          es:
            'Escucho la maquina. Cada falla tiene su sonido, su ' +
            'olor, su temperatura. Mido, descarto una causa, ' +
            'pruebo la siguiente. Paso a paso.',
          en:
            'I listen to the machine. Every fault has its sound, ' +
            'its smell, its temperature. I measure, rule out one ' +
            'cause, try the next. Step by step.',
        },
        options: [
          {
            label: { es: '¿En que orden?', en: 'In what order?' },
            next: 't3',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      t3: {
        text: {
          es:
            'De la causa mas simple a la mas cara. Nunca al ' +
            'reves, que el bolsillo llora. El que cambia piezas ' +
            'al azar no es tecnico: es lotero.',
          en:
            'From the simplest cause to the most expensive one. ' +
            'Never backwards, or the wallet cries. Whoever swaps ' +
            'parts at random is no technician: a lottery player.',
        },
        options: [
          {
            label: { es: 'Eso es debugging', en: 'That is debugging' },
            next: 't4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      t4: {
        text: {
          es:
            '¿Debu... que? Suena a palabra del futuro. Pero si ' +
            'asi se llama perseguir fallas con paciencia, ' +
            'entonces sin saberlo ya estoy debuggeando.',
          en:
            'De-bug... what? Sounds like a word from the future. ' +
            'But if that is the name for chasing faults with ' +
            'patience, then I am already debugging without ' +
            'knowing it.',
        },
        options: [
          {
            label: {
              es: '¿Y disfrutas el oficio?',
              en: 'Do you enjoy the trade?',
            },
            next: 't5',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      t5: {
        text: {
          es:
            'El momento exacto en que el equipo arranca y sale ' +
            'aire frio no se compara con nada. Mi lado karateka ' +
            'dice que es como ganar sin tirar un golpe.',
          en:
            'The exact moment the unit starts and cold air comes ' +
            'out compares to nothing. My karateka side says it is ' +
            'like winning without throwing a single strike.',
        },
        options: [
          {
            label: {
              es: '¿Y por que lo haces?',
              en: 'Why do you do it?',
            },
            next: 'w1',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      w1: {
        text: {
          es:
            'Para pagarme la universidad. Aqui el calor no ' +
            'perdona, asi que trabajo nunca falta. Cada equipo ' +
            'reparado es un ladrillo mas del plan.',
          en:
            'To pay my own way through university. The heat here ' +
            'shows no mercy, so there is never a shortage of ' +
            'work. Every repaired unit is one more brick.',
        },
        options: [
          { label: { es: '¿Es duro?', en: 'Is it hard?' }, next: 'w2' },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      w2: {
        text: {
          es:
            'Techos hirviendo al mediodia, escaleras, equipos que ' +
            'pesan como un piano chico. Duro es. Pero es trabajo ' +
            'honesto y tiene su ciencia.',
          en:
            'Boiling rooftops at noon, ladders, units as heavy as ' +
            'a small piano. Hard it is. But it is honest work and ' +
            'it has its science.',
        },
        options: [
          {
            label: { es: '¿Quien te enseño?', en: 'Who taught you?' },
            next: 'w3',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      w3: {
        text: {
          es:
            'Un maestro veterano del oficio. Hoy anda en otro ' +
            'techo de la ciudad, pero lo llevo en la cabeza: ' +
            '"primero se escucha, despues se abre", decia.',
          en:
            'A veteran master of the trade. He is on some other ' +
            'rooftop today, but I carry him in my head: "first ' +
            'you listen, then you open it", he would say.',
        },
        options: [
          {
            label: {
              es: '¿Que mas te enseño?',
              en: 'What else did he teach you?',
            },
            next: 'w4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      w4: {
        text: {
          es:
            'Que todo es un sistema: el frio viaja, se pierde, ' +
            'vuelve. Si entiendes el todo, la pieza rota se ' +
            'delata sola. El veia el mapa, no solo el tornillo.',
          en:
            'That everything is a system: the cold travels, ' +
            'leaks, returns. If you understand the whole, the ' +
            'broken part gives itself away. He saw the map, not ' +
            'just the screw.',
        },
        options: [
          {
            label: {
              es: 'Eso aplica a mas cosas',
              en: 'That applies to more things',
            },
            next: 'w5',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      w5: {
        text: {
          es:
            'Eso sospecho. Siento que cada falla acorralada aqui ' +
            'me entrena para las maquinas que vienen. La falla ' +
            'cambia de traje, no de alma.',
          en:
            'So I suspect. Every fault cornered up here feels ' +
            'like training for the machines to come. Faults ' +
            'change suits, not souls.',
        },
        options: [
          {
            label: {
              es: '¿Que maquinas vienen?',
              en: 'Which machines are coming?',
            },
            next: 'u1',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      u1: {
        text: {
          es:
            'Las computadoras. Quiero estudiar computacion en la ' +
            'universidad. Estos ahorros son el pasaje: no es ' +
            'rapido, pero cada reparacion suma.',
          en:
            'Computers. I want to study computing at university. ' +
            'These savings are the ticket: it is not fast, but ' +
            'every repair adds up.',
        },
        options: [
          {
            label: {
              es: '¿Y si no alcanza?',
              en: 'What if it is not enough?',
            },
            next: 'u2',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      u2: {
        text: {
          es:
            'Alcanzara. Tengo la constancia del karateka, la ' +
            'curiosidad del gamer y estas manos. Tres contra un ' +
            'problema: me gusta esa proporcion.',
          en:
            'It will be enough. I have the karateka consistency, ' +
            'the gamer curiosity and these hands. Three against ' +
            'one problem: I like those odds.',
        },
        options: [
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
          {
            label: {
              es: 'Vas a llegar. Hasta luego',
              en: 'You will make it. Goodbye',
            },
            next: null,
          },
        ],
      },
      s1: {
        text: {
          es:
            'La grieta nos partio en tres. El que salta en el ' +
            'tatami y el de la PC tambien soy yo. Mismo Pablo: ' +
            'uno entrena, otro pregunta, yo cargo el compresor.',
          en:
            'The crack split us in three. The one jumping on the ' +
            'tatami and the one at the PC are also me. Same ' +
            'Pablo: one trains, one asks, I carry the compressor.',
        },
        options: [
          {
            label: {
              es: '¿No te incomoda?',
              en: 'Does it not bother you?',
            },
            next: 's2',
          },
          {
            label: { es: '¿Se llevan bien?', en: 'Do you get along?' },
            next: 's3',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      s2: {
        text: {
          es:
            'Al principio si. Despues hice lo que hago con toda ' +
            'falla rara: observar, descartar, aceptar el ' +
            'diagnostico. Diagnostico: somos tres. Se trabaja ' +
            'igual.',
          en:
            'At first, yes. Then I did what I do with any odd ' +
            'fault: observe, rule out, accept the diagnosis. ' +
            'Diagnosis: we are three. Work goes on the same.',
        },
        options: [
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
          {
            label: {
              es: 'Buen diagnostico. Adios',
              en: 'Good diagnosis. Bye',
            },
            next: null,
          },
        ],
      },
      s3: {
        text: {
          es:
            'Como buenos colegas. El karateka madruga, el gamer ' +
            'trasnocha y yo sudo el turno del medio. Entre los ' +
            'tres, el dia rinde triple.',
          en:
            'Like good coworkers. The karateka wakes up early, ' +
            'the gamer stays up late and I sweat the middle ' +
            'shift. Between the three, the day yields triple.',
        },
        options: [
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
          {
            label: {
              es: 'Buen equipo. Hasta luego',
              en: 'Good team. Goodbye',
            },
            next: null,
          },
        ],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
