/**
 * @module dialogs/aula-pasado (engine)
 * @description Arboles de dialogo del "antes" del aula (sepia, Venezuela
 *   pre-universitaria): el Pablo joven entrenando kihon en el tatami, su
 *   amigo gamer frente al GTA San Andreas y el tecnico veterano de aires
 *   acondicionados que le enseño el oficio.
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const AULA_PASADO_DIALOGS = {
  'pablo-karate': defineDialog({
    name: { es: 'Pablo joven', en: 'Young Pablo' },
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
            'aire a medio armar. ¿De que quieres hablar?',
          en:
            'Osu! Sorry about the jump, dojo habit. Welcome to my ' +
            'corner: a tatami, a roaring PC and a half-assembled AC ' +
            'unit. What do you want to talk about?',
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
            'Esa PC vieja es mi otro dojo. Paso horas ahi con mi ' +
            'amigo: el juega en serio, yo hago algo mas ademas de ' +
            'jugar.',
          en:
            'That old PC is my other dojo. I spend hours there with ' +
            'my friend: he plays for real, I do something else ' +
            'besides playing.',
        },
        options: [
          {
            label: {
              es: '¿Que estan jugando?',
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
            'El, sin discusion. Yo me distraigo: a mitad de mision ' +
            'me quedo mirando como se mueve la ciudad, y pierdo.',
          en:
            'He does, no contest. I get distracted: mid-mission I ' +
            'just stare at how the city moves, and I lose.',
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
            'Mi amigo se desespera.',
          en:
            'I snoop. I open the game folders and look at the ' +
            'files: textures, sounds, things with weird names. My ' +
            'friend despairs.',
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
            'Un tecnico veterano, ese que esta alla arrodillado. ' +
            'Sabe escuchar maquinas como otros escuchan musica. ' +
            'Aprendo mirandolo.',
          en:
            'A veteran technician, the one kneeling over there. He ' +
            'listens to machines the way others listen to music. I ' +
            'learn by watching him.',
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
            'mira asi su presente.',
          en:
            'Karateka intuition. You look at this place like ' +
            'someone looking at an old photo: with fondness and an ' +
            'advantage. Nobody sees their present like that.',
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
  'amigo-gamer': defineDialog({
    name: { es: 'Amigo gamer', en: 'Gamer friend' },
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
        es: 'Pablo, suelta los archivos y juega.',
        en: 'Pablo, drop the files and play.',
      },
      {
        es: 'Una partida mas y me voy. Bueno, dos.',
        en: 'One more game and I leave. Okay, two.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Espera, espera... dejame guardar la partida. Listo. ' +
            'Hola. Si buscas a Pablo, esta alla saltando. Si ' +
            'buscas al bueno del juego, ese soy yo.',
          en:
            'Wait, wait... let me save the game. Done. Hi. If you ' +
            'want Pablo, he is over there jumping. If you want the ' +
            'good player, that would be me.',
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
              es: 'Hablame de Pablo',
              en: 'Tell me about Pablo',
            },
            next: 'p1',
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
            'GTA San Andreas. Salio este año y desde entonces no ' +
            'dormimos igual. Una ciudad entera para hacer lo que ' +
            'quieras.',
          en:
            'GTA San Andreas. It came out this year and we have ' +
            'not slept the same since. A whole city to do ' +
            'whatever you want.',
        },
        options: [
          {
            label: { es: '¿Tan bueno es?', en: 'Is it that good?' },
            next: 'j2',
          },
          {
            label: {
              es: '¿Juegan por turnos?',
              en: 'Do you take turns?',
            },
            next: 'j3',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      j2: {
        text: {
          es:
            'Es gigante. Tres ciudades, campo, desierto... todo ' +
            'dentro de esta pobre PC que ya venia cansada de los ' +
            'noventa.',
          en:
            'It is huge. Three cities, countryside, desert... all ' +
            'inside this poor PC that was already tired from the ' +
            'nineties.',
        },
        options: [
          {
            label: {
              es: '¿Y corre bien?',
              en: 'And does it run well?',
            },
            next: 'j4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      j3: {
        text: {
          es:
            'Turnos, si. El problema es el turno de Pablo: agarra ' +
            'la bici, pedalea dos cuadras y se queda viendo el ' +
            'atardecer del juego.',
          en:
            "Turns, yes. The problem is Pablo's turn: he grabs " +
            'the bike, pedals two blocks and just stares at the ' +
            'in-game sunset.',
        },
        options: [
          {
            label: {
              es: '¿Mirando el atardecer?',
              en: 'Staring at the sunset?',
            },
            next: 'j5',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      j4: {
        text: {
          es:
            'Se arrastra en las persecuciones, pero corre. Pablo ' +
            'dice que cuando bajan los frames "la maquina esta ' +
            'pensando". Rarisimo.',
          en:
            'It crawls during chases, but it runs. Pablo says that ' +
            'when the frames drop "the machine is thinking". So ' +
            'weird.',
        },
        options: [
          {
            label: { es: '¿Raro por que?', en: 'Weird how?' },
            next: 'j5',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      j5: {
        text: {
          es:
            'No juega como la gente normal. Deja pasar los ' +
            'creditos COMPLETOS. ¿Quien hace eso? Lee los nombres ' +
            'como si fueran un poster.',
          en:
            'He does not play like normal people. He lets the ' +
            'credits roll ALL the way. Who does that? He reads ' +
            'the names like a poster.',
        },
        options: [
          {
            label: {
              es: '¿Los creditos del juego?',
              en: 'The game credits?',
            },
            next: 'j6',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      j6: {
        text: {
          es:
            'Los creditos, si. Dice que ahi esta la gente que ' +
            'HIZO el juego. Y despues abre las carpetas de ' +
            'instalacion a husmear.',
          en:
            'The credits, yes. He says that is where the people ' +
            'who MADE the game are. Then he opens the install ' +
            'folders to snoop.',
        },
        options: [
          {
            label: {
              es: '¿Y que busca ahi?',
              en: 'What is he looking for?',
            },
            next: 'j7',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      j7: {
        text: {
          es:
            'Ni idea. Archivos con nombres raros. Yo le digo "asi ' +
            'no se juega" y el me contesta "yo juego otro juego". ' +
            'Filosofo, el tipo.',
          en:
            'No idea. Files with weird names. I tell him "that is ' +
            'not how you play" and he answers "I am playing ' +
            'another game". A philosopher.',
        },
        options: [
          {
            label: {
              es: '¿Y te molesta?',
              en: 'Does it bother you?',
            },
            next: 'j8',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      j8: {
        text: {
          es:
            'Solo cuando es mi turno y la pantalla esta llena de ' +
            'carpetas. Pero la verdad... pregunta cosas que yo ' +
            'nunca me pregunte.',
          en:
            'Only when it is my turn and the screen is full of ' +
            'folders. But honestly... he asks things I had never ' +
            'asked myself.',
        },
        options: [
          {
            label: {
              es: '¿Como que cosas?',
              en: 'Things like what?',
            },
            next: 'j9',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      j9: {
        text: {
          es:
            '"¿Como sabe el juego donde esta cada carro?" "¿Quien ' +
            'dibujo esta calle?" "¿Como se HACE esto?" Asi todo ' +
            'el dia. TODO el dia.',
          en:
            '"How does the game know where every car is?" "Who ' +
            'drew this street?" "How is this MADE?" All day like ' +
            'that. ALL day.',
        },
        options: [
          {
            label: {
              es: '¿Y tu que respondes?',
              en: 'What do you answer?',
            },
            next: 'j10',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      j10: {
        text: {
          es:
            'Que es magia. Pero el no acepta magia como respuesta. ' +
            'Te apuesto lo que sea a que un dia termina haciendo ' +
            'estas cosas el.',
          en:
            'That it is magic. But he does not accept magic as an ' +
            'answer. I bet you anything one day he ends up making ' +
            'these things.',
        },
        options: [
          {
            label: {
              es: 'Yo no apostaria en contra',
              en: 'I would not bet against it',
            },
            next: 'j11',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      j11: {
        text: {
          es:
            'Nadie deberia. Cuando a Pablo se le mete algo, lo ' +
            'repite hasta que le sale. Lo vi con el karate. Da un ' +
            'poco de miedo.',
          en:
            'Nobody should. When Pablo sets his mind on something, ' +
            'he repeats it until he gets it. I saw it with karate. ' +
            'A bit scary.',
        },
        options: [
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
          {
            label: {
              es: 'Suerte con la mision',
              en: 'Good luck with the mission',
            },
            next: null,
          },
        ],
      },
      p1: {
        text: {
          es:
            'Pablo es intenso, hermano. Karate al amanecer, aires ' +
            'todo el dia y esta PC de noche. No se de donde saca ' +
            'energia.',
          en:
            'Pablo is intense, brother. Karate at dawn, AC units ' +
            'all day and this PC at night. Where does the energy ' +
            'come from?',
        },
        options: [
          {
            label: {
              es: '¿Duerme algo?',
              en: 'Does he sleep at all?',
            },
            next: 'p2',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      p2: {
        text: {
          es:
            'Poco. Dice que ahorra para la universidad y que "la ' +
            'constancia gana". Yo digo que dormir tambien cuenta, ' +
            'pero bueno.',
          en:
            'Not much. He says he is saving for university and ' +
            'that "consistency wins". I say sleep also counts, ' +
            'but oh well.',
        },
        options: [
          {
            label: {
              es: '¿Tu que opinas?',
              en: 'What do you think?',
            },
            next: 'p3',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      p3: {
        text: {
          es:
            'Que esta medio loco... y que lo va a lograr. Esa ' +
            'combinacion exacta. Los que lo logran siempre estan ' +
            'un poco locos, ¿no?',
          en:
            'That he is half crazy... and that he will make it. ' +
            'That exact combo. The ones who make it are always a ' +
            'little crazy, right?',
        },
        options: [
          {
            label: {
              es: '¿Y tu mientras tanto?',
              en: 'And you, meanwhile?',
            },
            next: 'p4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      p4: {
        text: {
          es:
            'Yo cuido lo importante: la partida guardada y que la ' +
            'PC no se muera. Alguien tiene que mantener la ' +
            'infraestructura, ¿no?',
          en:
            'I take care of what matters: the saved game and ' +
            'keeping the PC alive. Somebody has to maintain the ' +
            'infrastructure, right?',
        },
        options: [
          {
            label: {
              es: 'Un heroe silencioso',
              en: 'A silent hero',
            },
            next: 'p5',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      p5: {
        text: {
          es:
            'Exacto. Cuando Pablo haga juegos o lo que sea, que se ' +
            'acuerde de quien le soplaba los trucos. Ese voy a ' +
            'ser yo.',
          en:
            'Exactly. When Pablo makes games or whatever, he ' +
            'better remember who whispered him the cheat codes. ' +
            'That will be me.',
        },
        options: [
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
          {
            label: {
              es: 'Quedo registrado. Adios',
              en: 'Duly noted. Bye',
            },
            next: null,
          },
        ],
      },
    },
  }),
  'tecnico-ac': defineDialog({
    name: { es: 'Tecnico veterano', en: 'Veteran technician' },
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
        es: 'Primero se escucha, despues se abre.',
        en: 'First you listen, then you open it.',
      },
      {
        es: 'Muchacho, ¿y la llave del diez?',
        en: 'Kid, where is the ten wrench?',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Pasame esa llave... ah, no, disculpa. Tu eres visita. ' +
            'Estoy con esta unidad que no quiere enfriar. ¿Que se ' +
            'te ofrece?',
          en:
            'Hand me that wrench... ah, no, my apologies. You are ' +
            'a guest. I am busy with this unit that refuses to ' +
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
              es: 'Hablame del muchacho',
              en: 'Tell me about the kid',
            },
            next: 'm1',
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
            'relay, el cableado... El equipo lo sabe. Mi trabajo ' +
            'es hacerlo confesar.',
          en:
            'The compressor will not start. Could be the ' +
            'capacitor, the relay, the wiring... The unit knows. ' +
            'My job is to make it confess.',
        },
        options: [
          {
            label: {
              es: '¿Y como confiesa?',
              en: 'And how does it confess?',
            },
            next: 't2',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      t2: {
        text: {
          es:
            'Por los sintomas. Cada falla tiene su sonido, su ' +
            'olor, su temperatura. Un clic seco dice una cosa; un ' +
            'zumbido, otra.',
          en:
            'Through the symptoms. Every fault has its sound, its ' +
            'smell, its temperature. A dry click says one thing; ' +
            'a hum, another.',
        },
        options: [
          {
            label: {
              es: '¿Como se aprende eso?',
              en: 'How do you learn that?',
            },
            next: 't3',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      t3: {
        text: {
          es:
            'Con años y con metodo: descartas una causa a la vez, ' +
            'de la mas simple a la mas cara. Nunca al reves, que ' +
            'el bolsillo llora.',
          en:
            'With years and with method: you rule out one cause ' +
            'at a time, from simplest to most expensive. Never ' +
            'backwards, or the wallet cries.',
        },
        options: [
          {
            label: {
              es: '¿Y si cambias al azar?',
              en: 'What if you swap at random?',
            },
            next: 't4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      t4: {
        text: {
          es:
            'El que cambia piezas al azar no es tecnico: es ' +
            'lotero. A veces acierta, si, pero nunca sabe por ' +
            'que. Y lo que no sabes, se repite.',
          en:
            'Whoever swaps parts at random is no technician: he ' +
            'plays the lottery. He may win sometimes, but never ' +
            'knows why. And what you do not know, repeats.',
        },
        options: [
          {
            label: { es: 'Sabias palabras', en: 'Wise words' },
            next: 't5',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      t5: {
        text: {
          es:
            'Es el oficio. Aqui el calor no negocia: un aire ' +
            'dañado no es capricho, es salud, es sueño, es el ' +
            'humor de la casa entera.',
          en:
            'That is the trade. Here the heat does not negotiate: ' +
            'a broken AC is no whim, it is health, sleep, the ' +
            'mood of the whole house.',
        },
        options: [
          {
            label: {
              es: '¿Es duro el trabajo?',
              en: 'Is the job hard?',
            },
            next: 't6',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      t6: {
        text: {
          es:
            'Techos al mediodia, escaleras, equipos que pesan como ' +
            'un piano chico. Duro es. Pero uno baja del techo con ' +
            'la falla resuelta y algo de paz.',
          en:
            'Rooftops at noon, ladders, units as heavy as a small ' +
            'piano. Hard it is. But you climb down with the fault ' +
            'solved and some peace.',
        },
        options: [
          {
            label: {
              es: '¿Cual es el secreto?',
              en: 'What is the secret?',
            },
            next: 't7',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      t7: {
        text: {
          es:
            'Paciencia y oido. La maquina siempre esta diciendo ' +
            'donde le duele. El truco es callarse uno para poder ' +
            'escucharla.',
          en:
            'Patience and a good ear. The machine is always ' +
            'telling you where it hurts. The trick is to quiet ' +
            'down and listen.',
        },
        options: [
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
          {
            label: {
              es: 'Gracias por la leccion',
              en: 'Thanks for the lesson',
            },
            next: null,
          },
        ],
      },
      m1: {
        text: {
          es:
            '¿Pablo? Ese muchacho tiene cabeza para los sistemas. ' +
            'Se lo digo yo, que llevo veinte años viendo pasar ' +
            'aprendices.',
          en:
            'Pablo? That kid has a head for systems. Take it from ' +
            'me: I have watched apprentices come and go for ' +
            'twenty years.',
        },
        options: [
          {
            label: {
              es: '¿Por que lo dices?',
              en: 'Why do you say that?',
            },
            next: 'm2',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      m2: {
        text: {
          es:
            'Porque pregunta el PORQUE de cada pieza, no solo el ' +
            'como. El aprendiz comun quiere terminar; el quiere ' +
            'entender. Es distinto.',
          en:
            'Because he asks the WHY of every part, not just the ' +
            'how. The average apprentice wants to finish; he ' +
            'wants to understand.',
        },
        options: [
          {
            label: {
              es: '¿Entender que, por ejemplo?',
              en: 'Understand what, say?',
            },
            next: 'm3',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      m3: {
        text: {
          es:
            'El sistema completo: de donde viene el frio, por ' +
            'donde se escapa, que pieza empuja a cual. Ve el ' +
            'mapa, no solo el tornillo.',
          en:
            'The whole system: where the cold comes from, where ' +
            'it leaks, which part pushes which. He sees the map, ' +
            'not just the screw.',
        },
        options: [
          {
            label: { es: '¿Y eso es raro?', en: 'Is that rare?' },
            next: 'm4',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      m4: {
        text: {
          es:
            'Rarisimo. A la mayoria hay que enseñarle a mirar ' +
            'asi, y a muchos ni asi. El vino con esa mirada ' +
            'puesta de fabrica.',
          en:
            'Very rare. Most must be taught to look that way, and ' +
            'many never learn. He came with that gaze installed ' +
            'at the factory.',
        },
        options: [
          {
            label: {
              es: '¿Le ves futuro aqui?',
              en: 'A future in the trade?',
            },
            next: 'm5',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      m5: {
        text: {
          es:
            'En los aires no se queda, y esta bien. Esta ' +
            'ahorrando para estudiar. Computacion, dice. Las ' +
            'maquinas del futuro, supongo.',
          en:
            'He will not stay in AC repair, and that is fine. He ' +
            'is saving up to study. Computing, he says. The ' +
            'machines of the future, I suppose.',
        },
        options: [
          {
            label: {
              es: '¿Le habra servido esto?',
              en: 'Will this have helped?',
            },
            next: 'm6',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      m6: {
        text: {
          es:
            'Todo lo que aprendio aqui viaja con el: diagnosticar ' +
            'es diagnosticar, aqui o en una computadora. La falla ' +
            'cambia de traje, no de alma.',
          en:
            'Everything he learned here travels with him: ' +
            'diagnosing is diagnosing, here or inside a computer. ' +
            'Faults change suits, not souls.',
        },
        options: [
          {
            label: {
              es: 'Bonita forma de decirlo',
              en: 'A fine way to put it',
            },
            next: 'm7',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      m7: {
        text: {
          es:
            'Cuando repara algo, sonrie como si hubiera ganado ' +
            'una pelea. Esa alegria no se enseña. Con eso se ' +
            'llega lejos.',
          en:
            'When he fixes something, he smiles as if he had won ' +
            'a fight. That joy cannot be taught. It takes you far.',
        },
        options: [
          {
            label: {
              es: '¿Algun consejo final?',
              en: 'Any last advice?',
            },
            next: 'm8',
          },
          { label: { es: 'Volver', en: 'Back' }, next: 'hub' },
        ],
      },
      m8: {
        text: {
          es:
            'Uno solo: si algun dia el muchacho trabaja contigo, ' +
            'dale problemas dificiles. Con los faciles se aburre.',
          en:
            'Just one: if that kid ever works with you, give him ' +
            'hard problems. The easy ones bore him.',
        },
        options: [
          {
            label: {
              es: 'Lo tendre en cuenta',
              en: 'I will keep it in mind',
            },
            next: 'hub',
          },
          {
            label: { es: 'Anotado. Hasta luego', en: 'Noted. Goodbye' },
            next: null,
          },
        ],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
