/**
 * @module dialogs/cofasa-presente (engine)
 * @description Arboles de dialogo de la sala 3 presente: Laboratorio
 *   Cofasa (2017-18), farmaceutica venezolana donde Pablo construyo el
 *   sistema web (jQuery + Laravel) de monitoreo de produccion y paradas
 *   de maquina que reemplazo las planillas de papel. 5 NPCs con los 2
 *   enfoques del canon (informe 10): Yorman Rondon y Douglas Materan
 *   (compañeros dev), Nelida Guerra (supervisora de planta) y Rafael
 *   Escalona (operario de la llenadora) como personal del sitio, y
 *   Carmen Yepez (jefa de produccion). Todos anclados a la data real:
 *   red local con login por empleado, BD relacional de eventos/tiempos/
 *   causas, reportes de horas a consulta directa, visibilidad por
 *   primera vez de las causas de parada, casi 2 años en uso productivo.
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const COFASA_PRESENTE_DIALOGS = {
  yorman: defineDialog({
    name: { es: 'Yorman Rondon', en: 'Yorman Rondon' },
    chatter: [
      {
        es: 'jQuery y Laravel, corriendo en la red local. Cero nube.',
        en: 'jQuery and Laravel, running on the local network. Zero cloud.',
      },
      {
        es: 'Cada empleado su usuario y su clave. Asi entra todo el mundo.',
        en: 'Each employee their own user and password. That is how everyone gets in.',
      },
      {
        es: 'El modelo de la base de datos salio de la planta, no de un libro.',
        en: 'The database model came from the plant floor, not from a book.',
      },
      {
        es: 'Pablo primero caminaba la planta. Despues codeaba.',
        en: 'Pablo walked the plant first. Then he coded.',
      },
      {
        es: 'Casi dos años en produccion. Eso no pasa sin mantenimiento.',
        en: 'Almost two years in production. That does not happen without maintenance.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Yorman, desarrollo y soporte TI del laboratorio. Con Pablo ' +
            'levantamos el sistema de monitoreo de produccion: web, en ' +
            'nuestra propia red. ¿Que quieres saber?',
          en:
            'Yorman, development and IT support at the lab. Pablo and I ' +
            'stood up the production monitoring system: web-based, on our ' +
            'own network. What do you want to know?',
        },
        options: [
          {
            label: {
              es: '¿Por que jQuery y Laravel?',
              en: 'Why jQuery and Laravel?',
            },
            next: 'stack-1',
          },
          {
            label: {
              es: '¿Como se modelo la base de datos?',
              en: 'How was the database modelled?',
            },
            next: 'bd-1',
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
            'Claro: puedo contarte como era Pablo levantando ' +
            'requerimientos, o como se sostuvo el sistema casi dos años.',
          en:
            'Sure: I can tell you how Pablo gathered requirements, or how ' +
            'the system held up for almost two years.',
        },
        options: [
          {
            label: {
              es: '¿Como levantaba requerimientos?',
              en: 'How did he gather requirements?',
            },
            next: 'pablo-1',
          },
          {
            label: {
              es: '¿Como se sostuvo tanto tiempo?',
              en: 'How did it last that long?',
            },
            next: 'mant-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Pasa por el showcase junto a la puerta: el dashboard esta ' +
            'vivo ahi, con su azul Cofasa. Y habla con Douglas, que el te ' +
            'cuenta lo que dicen las barras.',
          en:
            'Stop by the showcase next to the door: the dashboard lives ' +
            'there, Cofasa blue and all. And talk to Douglas, he can tell ' +
            'you what the bars say.',
        },
        options: [{ label: { es: 'Hasta luego', en: 'See you' }, next: null }],
      },

      'stack-1': {
        text: {
          es:
            'Porque era 2017 y esto es una planta, no un startup: PHP con ' +
            'Laravel en el servidor, jQuery en el navegador. Lo solido de ' +
            'la epoca, facil de mantener y de explicar. Nada de ' +
            'experimentos con la produccion corriendo al lado.',
          en:
            'Because it was 2017 and this is a plant, not a startup: PHP ' +
            'with Laravel on the server, jQuery in the browser. The solid ' +
            'stack of the era, easy to maintain and to explain. No ' +
            'experiments with production running next door.',
        },
        options: [
          {
            label: {
              es: '¿Y por que en la red local?',
              en: 'And why on the local network?',
            },
            next: 'stack-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'stack-2': {
        text: {
          es:
            'Aqui el internet iba y venia, pero la LAN de la empresa no ' +
            'fallaba. El sistema se desplego en toda la empresa sobre esa ' +
            'red: cada quien entra desde su PC con su usuario y su clave. ' +
            'Si la calle se cae, la planta sigue registrando.',
          en:
            'Internet here came and went, but the company LAN never ' +
            'failed. The system was deployed company-wide on that ' +
            'network: everyone logs in from their PC with their own user ' +
            'and password. If the outside line drops, the plant keeps ' +
            'logging.',
        },
        options: [
          {
            label: {
              es: '¿Un login por empleado?',
              en: 'A login per employee?',
            },
            next: 'stack-3',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'stack-3': {
        text: {
          es:
            'Por empleado, si: el que registra una parada queda en el ' +
            'registro. No es para vigilar a nadie — es que un dato con ' +
            'dueño se discute; un papel anonimo se bota. La gente lo ' +
            'entendio rapido.',
          en:
            'Per employee, yes: whoever logs a stoppage is on the record. ' +
            'Not to police anyone — data with an owner gets discussed; an ' +
            'anonymous slip of paper gets tossed. People got it quickly.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
      'bd-1': {
        text: {
          es:
            'Relacional y sin adornos: eventos de produccion, tiempos de ' +
            'parada y causas. Pablo le dio vueltas al modelo hasta que ' +
            'cada tabla tenia una razon de ser. Decia que si el modelo ' +
            'estaba bien, los reportes salian solos.',
          en:
            'Relational and unadorned: production events, downtime spans ' +
            'and causes. Pablo turned the model over until every table ' +
            'had a reason to exist. He said that with the right model, ' +
            'the reports would write themselves.',
        },
        options: [
          {
            label: {
              es: '¿Y las causas de parada?',
              en: 'And the stoppage causes?',
            },
            next: 'bd-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'bd-2': {
        text: {
          es:
            'El catalogo de causas lo dicto la planta, no nosotros: ' +
            'cambio de formato, limpieza, atasco, falta de material, ' +
            'falla electrica, calibracion... Pablo lo levanto con los ' +
            'operarios y los supervisores. Por eso el selector del ' +
            'formulario habla el idioma de la linea.',
          en:
            'The cause catalogue was dictated by the plant, not by us: ' +
            'changeover, cleaning, jams, missing material, power ' +
            'failure, calibration... Pablo collected it with the ' +
            'operators and supervisors. That is why the form dropdown ' +
            'speaks the language of the line.',
        },
        options: [
          {
            label: {
              es: '¿Y tenia razon con el modelo?',
              en: 'And was he right about the model?',
            },
            next: 'bd-3',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'bd-3': {
        text: {
          es:
            'Toda la razon. Cuando Carmen pidio "paradas por causa del ' +
            'mes", fue una consulta, no un proyecto. Los datos crudos se ' +
            'volvieron indicadores porque el modelo ya sabia que pregunta ' +
            'venia. Eso se decide al diseñar, no al reportar.',
          en:
            'Completely right. When Carmen asked for "downtime by cause ' +
            'this month", it was a query, not a project. Raw data became ' +
            'indicators because the model already knew the question was ' +
            'coming. You decide that at design time, not report time.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
      'pablo-1': {
        text: {
          es:
            'Pablo no empezaba por la pantalla: se ponia bata y cofia y ' +
            'se iba a la linea a ver parar la maquina de verdad. ' +
            'Preguntaba a los operarios, a Nelida, a Carmen. Volvia con ' +
            'el cuaderno lleno y recien ahi abriamos el editor.',
          en:
            'Pablo never started at the screen: he put on the gown and ' +
            'cap and went to the line to watch the machine actually ' +
            'stop. He asked the operators, Nelida, Carmen. He came back ' +
            'with a full notebook and only then did we open the editor.',
        },
        options: [
          {
            label: {
              es: '¿Y eso se noto en el sistema?',
              en: 'And did it show in the system?',
            },
            next: 'pablo-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'pablo-2': {
        text: {
          es:
            'En todo. El formulario de parada tiene el orden en que la ' +
            'supervisora piensa: maquina, hora, causa. Los reportes ' +
            'responden las preguntas que la jefa hace en la reunion. ' +
            'Cuando el software copia el trabajo real, la gente lo ' +
            'adopta sola.',
          en:
            'In everything. The stoppage form follows the order the ' +
            'supervisor thinks in: machine, time, cause. The reports ' +
            'answer the questions the boss asks in the meeting. When ' +
            'software mirrors the real work, people adopt it on their ' +
            'own.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy. Gracias', en: 'I will go. Thanks' },
            next: 'bye',
          },
        ],
      },
      'mant-1': {
        text: {
          es:
            'Casi dos años en uso productivo, y no de milagro: cada vez ' +
            'que la planta pedia un ajuste — una causa nueva, un reporte ' +
            'distinto — Pablo lo escuchaba, lo priorizaba y lo entregaba. ' +
            'Mantener un sistema vivo es la mitad del oficio.',
          en:
            'Almost two years in productive use, and not by miracle: ' +
            'every time the plant asked for a tweak — a new cause, a ' +
            'different report — Pablo listened, prioritised and ' +
            'delivered. Keeping a system alive is half the craft.',
        },
        options: [
          {
            label: {
              es: '¿Que clase de ajustes?',
              en: 'What kind of tweaks?',
            },
            next: 'mant-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'mant-2': {
        text: {
          es:
            'De los que solo aparecen usandolo: que el selector ordene ' +
            'las causas mas frecuentes primero, que el reporte del turno ' +
            'salga listo para imprimir, que un registro se pueda ' +
            'corregir con permiso. Feedback de la planta, directo al ' +
            'codigo.',
          en:
            'The kind you only find by using it: sort the most frequent ' +
            'causes first in the dropdown, make the shift report ' +
            'print-ready, allow corrections with permission. Plant ' +
            'feedback, straight into the code.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
    },
  }),

  douglas: defineDialog({
    name: { es: 'Douglas Materan', en: 'Douglas Materan' },
    chatter: [
      {
        es: 'Cambio de formato y limpieza. Ahi se iba el tiempo.',
        en: 'Changeover and cleaning. That is where the time went.',
      },
      {
        es: 'Un dato crudo no decide nada. Un indicador, si.',
        en: 'Raw data decides nothing. An indicator does.',
      },
      {
        es: 'Las barras por causa no saben mentir.',
        en: 'Bars by cause do not know how to lie.',
      },
      {
        es: 'Reportes de horas... ahora son una consulta.',
        en: 'Reports that took hours... now they are one query.',
      },
      {
        es: 'Carmen entra a la reunion con los numeros frescos.',
        en: 'Carmen walks into the meeting with fresh numbers.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Douglas, desarrollo — la parte analitica. Yo vivia en las ' +
            'vistas de reportes del sistema: convertir paradas ' +
            'registradas en graficos que alguien pueda usar. ¿Que ' +
            'quieres saber?',
          en:
            'Douglas, development — the analytics side. I lived in the ' +
            'reporting views of the system: turning logged stoppages ' +
            'into charts someone can actually use. What do you want to ' +
            'know?',
        },
        options: [
          {
            label: {
              es: '¿Que mostraron las barras?',
              en: 'What did the bars show?',
            },
            next: 'pareto-1',
          },
          {
            label: {
              es: '¿Como eran los reportes antes?',
              en: 'What were reports like before?',
            },
            next: 'reportes-1',
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
            'Queda lo mio favorito: la diferencia entre un dato crudo y ' +
            'un indicador accionable.',
          en:
            'My favourite is left: the difference between raw data and ' +
            'an actionable indicator.',
        },
        options: [
          {
            label: { es: 'Explicamela', en: 'Explain it to me' },
            next: 'ind-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Dale una vuelta al showcase: la segunda demo son las barras ' +
            'por causa. Y mira el cuadro del Pareto en la pared — ese ' +
            'grafico le cambio la agenda a produccion.',
          en:
            'Take a spin through the showcase: the second demo is the ' +
            'bars by cause. And check the Pareto picture on the wall — ' +
            'that chart rewrote the production agenda.',
        },
        options: [{ label: { es: 'Hasta luego', en: 'See you' }, next: null }],
      },

      'pareto-1': {
        text: {
          es:
            'Que el tiempo no se perdia donde todos juraban. Cuando ' +
            'ordenamos las paradas por causa, arriba quedaron el cambio ' +
            'de formato y la limpieza — no las fallas de maquina. Nadie ' +
            'lo habia MEDIDO nunca; solo se sospechaba.',
          en:
            'That the time was not lost where everyone swore it was. ' +
            'When we sorted stoppages by cause, changeover and cleaning ' +
            'came out on top — not machine failures. Nobody had ever ' +
            'MEASURED it; there were only hunches.',
        },
        options: [
          {
            label: {
              es: '¿Y que hicieron con eso?',
              en: 'And what did you do with it?',
            },
            next: 'pareto-2',
          },
          {
            label: {
              es: '¿Que es el cambio de formato?',
              en: 'What is a changeover?',
            },
            next: 'pareto-3',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'pareto-2': {
        text: {
          es:
            'Priorizar, que es lo que los datos permiten: si el grueso ' +
            'del tiempo se va en cambio de formato y limpieza, ahi se ' +
            'ataca primero — planificar los lotes para cambiar menos, ' +
            'preparar la limpieza antes de parar. Decisiones informadas, ' +
            'no corazonadas.',
          en:
            'Prioritise, which is what data is for: if the bulk of the ' +
            'time goes to changeover and cleaning, you attack there ' +
            'first — plan batches to switch less, stage the cleaning ' +
            'before stopping. Informed decisions, not gut feelings.',
        },
        options: [
          {
            label: {
              es: '¿Y la productividad subio?',
              en: 'And did productivity improve?',
            },
            next: 'pareto-4',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'pareto-3': {
        text: {
          es:
            'Pasar la linea de un producto a otro: de un lote de ' +
            'ampollas a otro formato cambian boquillas, etiquetas, ' +
            'documentacion... y en farmacia ademas se limpia y sanitiza ' +
            'TODO. Es parada normal y necesaria — por eso importaba ' +
            'medirla en vez de sufrirla a ciegas.',
          en:
            'Switching the line from one product to another: from one ' +
            'ampoule batch to another format you change nozzles, ' +
            'labels, paperwork... and in pharma you also clean and ' +
            'sanitise EVERYTHING. It is normal, necessary downtime — ' +
            'which is why measuring it beat suffering it blind.',
        },
        options: [
          {
            label: {
              es: '¿Y que hicieron con eso?',
              en: 'And what did you do with it?',
            },
            next: 'pareto-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'pareto-4': {
        text: {
          es:
            'Contribuyo, si — asi lo dice hasta el CV de Pablo, con ' +
            'prudencia: el analisis de los datos ayudo a subir la ' +
            'productividad. Yo lo vi mas simple: por primera vez las ' +
            'reuniones discutian numeros en vez de recuerdos.',
          en:
            'It contributed, yes — even Pablo’s CV puts it ' +
            'carefully: analysing the data helped raise productivity. I ' +
            'saw it more simply: for the first time, meetings argued ' +
            'over numbers instead of memories.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
      'reportes-1': {
        text: {
          es:
            'Un via crucis: juntar las planillas de todos los turnos, ' +
            'descifrar letras, sumar tiempos a calculadora y pelear con ' +
            'totales que no cuadraban. VARIAS horas de consolidacion ' +
            'manual para un solo reporte de productividad.',
          en:
            'A slog: collect every shift’s paper sheets, decipher ' +
            'handwriting, add up times on a calculator and fight totals ' +
            'that never matched. SEVERAL hours of manual consolidation ' +
            'for a single productivity report.',
        },
        options: [
          {
            label: { es: '¿Y con el sistema?', en: 'And with the system?' },
            next: 'reportes-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'reportes-2': {
        text: {
          es:
            'Consulta directa: eliges el rango de fechas y el reporte ' +
            'sale. Las horas de calculadora se volvieron segundos de ' +
            'SQL. La primera vez que Carmen lo vio, pidio el mismo ' +
            'reporte tres veces seguidas solo para creerselo.',
          en:
            'Direct query: pick the date range and the report comes ' +
            'out. Calculator hours became SQL seconds. The first time ' +
            'Carmen saw it, she asked for the same report three times ' +
            'in a row just to believe it.',
        },
        options: [
          {
            label: { es: 'Hay mas temas, ¿no?', en: 'There is more, right?' },
            next: 'hub2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'ind-1': {
        text: {
          es:
            '"Parada de 22 minutos en la llenadora" es un dato crudo. ' +
            '"La limpieza se lleva mas tiempo de linea que los atascos ' +
            'este mes" es un indicador: te dice donde actuar. El sistema ' +
            'registraba lo primero y ENTREGABA lo segundo. Esa ' +
            'transformacion era el producto.',
          en:
            '"22-minute stoppage on the filler" is raw data. "Cleaning ' +
            'eats more line time than jams this month" is an indicator: ' +
            'it tells you where to act. The system recorded the former ' +
            'and DELIVERED the latter. That transformation was the ' +
            'product.',
        },
        options: [
          {
            label: {
              es: '¿Y quien consumia los indicadores?',
              en: 'And who consumed the indicators?',
            },
            next: 'ind-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'ind-2': {
        text: {
          es:
            'Carmen y su gente, cada semana. El dashboard con el ' +
            'semaforo, las barras por causa y la disponibilidad de ' +
            'linea. Habla con ella: te va a decir lo que significa ' +
            'entrar a una reunion con los numeros de TU planta a la ' +
            'vista.',
          en:
            'Carmen and her people, every week. The dashboard with the ' +
            'stack light, the bars by cause and line availability. Talk ' +
            'to her: she will tell you what it means to walk into a ' +
            'meeting with YOUR plant’s numbers in sight.',
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

  nelida: defineDialog({
    name: { es: 'Nelida Guerra', en: 'Nelida Guerra' },
    chatter: [
      {
        es: 'Guarde la libreta de paradas. De recuerdo.',
        en: 'I kept the old downtime notebook. As a souvenir.',
      },
      {
        es: 'Parada nueva: dos toques y quedo registrada.',
        en: 'New stoppage: two clicks and it is logged.',
      },
      {
        es: 'Antes cronometraba con el reloj de pulsera. De verdad.',
        en: 'I used to time stoppages with my wristwatch. Truly.',
      },
      {
        es: 'El reporte del turno sale solo. SOLO.',
        en: 'The shift report comes out on its own. ON ITS OWN.',
      },
      {
        es: 'Le dije a Pablo: yo no se de computadoras. Y mira.',
        en: 'I told Pablo: I know nothing about computers. And look.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Nelida, supervisora de planta. Yo era la de la libreta: ' +
            'cada parada de maquina, una fila escrita a mano con el ' +
            'reloj en la otra mano. Hasta que llego el sistema. ¿Que ' +
            'quieres saber?',
          en:
            'Nelida, plant supervisor. I was the notebook person: every ' +
            'machine stoppage, one handwritten row with a watch in the ' +
            'other hand. Until the system arrived. What do you want to ' +
            'know?',
        },
        options: [
          {
            label: {
              es: '¿Como era con la libreta?',
              en: 'What was the notebook like?',
            },
            next: 'antes-1',
          },
          {
            label: { es: '¿Y como es ahora?', en: 'And how is it now?' },
            next: 'ahora-1',
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
            'Te puedo contar como fue que Pablo me convencio a MI, que ' +
            'no sabia de computadoras.',
          en:
            'I can tell you how Pablo won ME over — the one who knew ' +
            'nothing about computers.',
        },
        options: [
          {
            label: {
              es: '¿Como te convencio?',
              en: 'How did he win you over?',
            },
            next: 'pablo-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Si quieres ver la libreta y el reloj, cruza la grieta esa ' +
            'del muro: alla sigo yo, la de antes, cuadrando planillas. ' +
            'Dale saludos de mi parte.',
          en:
            'If you want to see the notebook and the watch, cross that ' +
            'rift on the wall: the old me is still there, balancing ' +
            'paper sheets. Say hello from me.',
        },
        options: [{ label: { es: 'Hasta luego', en: 'See you' }, next: null }],
      },

      'antes-1': {
        text: {
          es:
            'Turno completo cargando la libreta y el reloj. La maquina ' +
            'se para: anoto la hora. Arranca: anoto la hora. ¿La causa? ' +
            'La que alcanzara a ver, o "se paro" a secas. Una fila por ' +
            'parada, todo el turno, todos los dias.',
          en:
            'A whole shift carrying the notebook and the watch. Machine ' +
            'stops: write down the time. Starts: write down the time. ' +
            'The cause? Whatever I managed to see, or just "it ' +
            'stopped". One row per stoppage, all shift, every day.',
        },
        options: [
          {
            label: {
              es: '¿Y al final del turno?',
              en: 'And at the end of the shift?',
            },
            next: 'antes-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'antes-2': {
        text: {
          es:
            'Ahi empezaba lo peor: cuadrar. Sumar tiempos a mano, pasar ' +
            'la libreta a la planilla, descubrir que un numero no se ' +
            'entendia o que me falto una parada. Horas despues de la ' +
            'jornada, y aun asi los totales no siempre cuadraban.',
          en:
            'That is when the worst began: balancing. Adding times by ' +
            'hand, copying the notebook into the sheet, finding a ' +
            'number I could not read or a stoppage I had missed. Hours ' +
            'after the workday, and the totals still did not always ' +
            'match.',
        },
        options: [
          {
            label: { es: '¿Y como es ahora?', en: 'And how is it now?' },
            next: 'ahora-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'ahora-1': {
        text: {
          es:
            'La maquina se para y yo registro en la pantalla: linea, ' +
            'causa, y la hora la pone el sistema solo. Dos toques. La ' +
            'parada queda guardada donde nadie la pierde y donde todos ' +
            'la pueden consultar.',
          en:
            'The machine stops and I log it on the screen: line, cause, ' +
            'and the system stamps the time itself. Two clicks. The ' +
            'stoppage is stored where nobody loses it and everybody can ' +
            'look it up.',
        },
        options: [
          {
            label: {
              es: '¿Y el cuadre del final?',
              en: 'And the end-of-shift balancing?',
            },
            next: 'ahora-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'ahora-2': {
        text: {
          es:
            'Ya no existe. El reporte del turno sale con una consulta: ' +
            'los tiempos sumados, las causas contadas, todo cuadrado ' +
            'porque lo cuadro la computadora. Yo superviso la LINEA, no ' +
            'una libreta. Para eso me pagan, ¿no?',
          en:
            'It no longer exists. The shift report comes out with one ' +
            'query: times added, causes counted, everything balanced ' +
            'because the computer balanced it. I supervise the LINE, ' +
            'not a notebook. That is what they pay me for, right?',
        },
        options: [
          {
            label: { es: 'Hay mas temas, ¿no?', en: 'There is more, right?' },
            next: 'hub2',
          },
          {
            label: { es: 'Me quedo con eso', en: 'That is enough for me' },
            next: null,
          },
        ],
      },
      'pablo-1': {
        text: {
          es:
            'No me trajo un manual: se paso un turno entero a mi lado, ' +
            'viendo como anotaba cada parada. Despues me mostro el ' +
            'formulario y era MI planilla, pero en pantalla: mismo ' +
            'orden, mismas palabras. No tuve que aprender el sistema — ' +
            'el sistema me aprendio a mi.',
          en:
            'He did not bring me a manual: he spent a whole shift at my ' +
            'side, watching how I logged each stoppage. Then he showed ' +
            'me the form and it was MY sheet, but on a screen: same ' +
            'order, same words. I did not have to learn the system — ' +
            'the system learned me.',
        },
        options: [
          {
            label: {
              es: '¿Y le pediste algo?',
              en: 'Did you ask him for anything?',
            },
            next: 'pablo-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'pablo-2': {
        text: {
          es:
            'Una sola cosa: "mijo, que la hora la ponga la maquina, que ' +
            'yo bastante tengo con la causa". Al dia siguiente la hora ' +
            'salia sola. Ahi dije: este muchacho si escucha. Y le firme ' +
            'la fe que le tengo hasta hoy.',
          en:
            'One thing only: "sweetheart, let the machine stamp the ' +
            'time, the cause is plenty for me". Next day the time ' +
            'stamped itself. Right there I said: this kid actually ' +
            'listens. He has had my faith ever since.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
    },
  }),

  rafael: defineDialog({
    name: { es: 'Rafael Escalona', en: 'Rafael Escalona' },
    chatter: [
      {
        es: 'Si la llenadora se para, ya no grito: aviso y queda registrado.',
        en: 'If the filler stops, I no longer shout: I report it and it is logged.',
      },
      {
        es: 'Miovit: el complejo B que todos llevamos en la sangre.',
        en: 'Miovit: the B-complex all of us carry in our blood.',
      },
      {
        es: 'Cofia, bata, guantes. La sala limpia no perdona.',
        en: 'Cap, gown, gloves. The clean room forgives nothing.',
      },
      {
        es: 'Antes nadie sabia por que se paraba tanto. NADIE.',
        en: 'Before, nobody knew why it stopped so much. NOBODY.',
      },
      {
        es: 'La torre de luces habla por la linea.',
        en: 'The stack light speaks for the line.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Rafael, operario de la linea de inyectables. Esta de aqui ' +
            'es la llenadora de ampollas — ahorita corre Miovit, el ' +
            'producto estrella de la casa. ¿Que quieres saber?',
          en:
            'Rafael, injectables line operator. This one here is the ' +
            'ampoule filler — right now it is running Miovit, the house ' +
            'flagship product. What do you want to know?',
        },
        options: [
          {
            label: {
              es: '¿Que es Miovit?',
              en: 'What is Miovit?',
            },
            next: 'miovit-1',
          },
          {
            label: {
              es: '¿Que pasa cuando se para?',
              en: 'What happens when it stops?',
            },
            next: 'parada-1',
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
            'Puedo contarte de la sala limpia — la cofia no es un ' +
            'capricho — o de la torre de luces.',
          en:
            'I can tell you about the clean room — the cap is not a ' +
            'whim — or about the stack light.',
        },
        options: [
          {
            label: {
              es: '¿Que es la sala limpia?',
              en: 'What is the clean room?',
            },
            next: 'sala-1',
          },
          {
            label: {
              es: 'Cuentame del semaforo',
              en: 'Tell me about the light',
            },
            next: 'andon-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Dale al boton de la torre si quieres ver como se registra ' +
            'una parada — tranquilo, que la de mentira no detiene nada. ' +
            'Y no toques las ampollas, que van esterilizadas.',
          en:
            'Hit the tower button if you want to see how a stoppage ' +
            'gets logged — relax, the pretend one stops nothing. And do ' +
            'not touch the ampoules, they go out sterilised.',
        },
        options: [{ label: { es: 'Hasta luego', en: 'See you' }, next: null }],
      },

      'miovit-1': {
        text: {
          es:
            'El complejo B inyectable de Cofasa — el que "todos los ' +
            'venezolanos llevan en la sangre", como dicen. Se vende en ' +
            'kit: ampollas de vidrio ambar con sus inyectadoras. Esas ' +
            'cajitas azules apiladas alla son lotes listos.',
          en:
            'Cofasa’s injectable B-complex — the one "all ' +
            'Venezuelans carry in their blood", as they say. Sold as a ' +
            'kit: amber glass ampoules with their syringes. Those blue ' +
            'boxes stacked over there are finished batches.',
        },
        options: [
          {
            label: {
              es: '¿Y la maquina que hace?',
              en: 'And what does the machine do?',
            },
            next: 'miovit-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'miovit-2': {
        text: {
          es:
            'Llena y sella las ampollas: la mezcla viene del tanque, la ' +
            'ampolla pasa por la boquilla, se llena, se sella a la ' +
            'llama y sigue a inspeccion y blisteado. Cuando el lote ' +
            'cambia de producto viene el famoso cambio de formato — y ' +
            'la linea se detiene un buen rato.',
          en:
            'It fills and seals the ampoules: the mix comes from the ' +
            'tank, the ampoule passes the nozzle, gets filled, ' +
            'flame-sealed and moves on to inspection and blistering. ' +
            'When the batch switches product comes the famous ' +
            'changeover — and the line stops for a good while.',
        },
        options: [
          {
            label: {
              es: '¿Que pasa cuando se para?',
              en: 'What happens when it stops?',
            },
            next: 'parada-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'parada-1': {
        text: {
          es:
            'Aviso a la supervisora y la parada queda registrada al ' +
            'toque: la maquina, la causa y la hora, con nombre y ' +
            'apellido. Cuando arranca de nuevo, tambien. El tiempo ' +
            'detenido queda medido solo, sin que nadie corra con un ' +
            'reloj.',
          en:
            'I flag the supervisor and the stoppage is logged right ' +
            'away: machine, cause and time, with a name attached. When ' +
            'it starts again, same thing. The downtime measures itself ' +
            'without anyone running around with a watch.',
        },
        options: [
          {
            label: {
              es: '¿Y antes del sistema?',
              en: 'And before the system?',
            },
            next: 'antes-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'antes-1': {
        text: {
          es:
            'Antes la linea se paraba y se paraba, y nadie sabia por ' +
            'que se paraba TANTO. Yo avisaba gritando por encima del ' +
            'ruido y quien sabe si alguien lo anotaba. A fin de mes, ' +
            'puro cuento: cada quien recordaba una planta distinta.',
          en:
            'Before, the line stopped and stopped, and nobody knew why ' +
            'it stopped SO MUCH. I shouted over the noise and who knows ' +
            'if anyone wrote it down. By month’s end, pure ' +
            'folklore: everyone remembered a different plant.',
        },
        options: [
          {
            label: {
              es: '¿Y eso cambio en que?',
              en: 'And what changed?',
            },
            next: 'antes-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'antes-2': {
        text: {
          es:
            'En que ahora la planta se conoce a si misma. Las causas ' +
            'estan contadas y ordenadas — el sistema le dio ojos a lo ' +
            'que antes era ruido. Y de paso: cuando dicen "la llenadora ' +
            'falla mucho", los numeros me defienden. Casi siempre es el ' +
            'cambio de formato, no mi maquina.',
          en:
            'Now the plant knows itself. Causes are counted and ranked ' +
            '— the system gave eyes to what used to be noise. And as a ' +
            'bonus: when they say "the filler breaks a lot", the ' +
            'numbers defend me. It is almost always the changeover, not ' +
            'my machine.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
      'sala-1': {
        text: {
          es:
            'Aqui se fabrican inyectables: lo que va dentro de la ' +
            'ampolla termina dentro de una persona. Por eso bata, ' +
            'cofia, mascarilla y guantes, y por eso la limpieza y la ' +
            'sanitizacion son sagradas — aunque paren la linea. Buenas ' +
            'practicas: asi trabaja un laboratorio serio.',
          en:
            'We make injectables here: what goes inside the ampoule ' +
            'ends up inside a person. Hence gown, cap, mask and gloves, ' +
            'and hence cleaning and sanitisation are sacred — even if ' +
            'they stop the line. Good practices: that is how a serious ' +
            'lab works.',
        },
        options: [
          {
            label: {
              es: '¿La limpieza tambien es parada?',
              en: 'Is cleaning also downtime?',
            },
            next: 'sala-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'sala-2': {
        text: {
          es:
            'Claro, y de las grandes. Pero es parada BUENA: obligatoria ' +
            'y planificable. La gracia del sistema fue separar las ' +
            'paradas que tocan de las que duelen — la limpieza se ' +
            'programa; el atasco se repara. Sin datos, todo era el ' +
            'mismo saco.',
          en:
            'Of course, and a big one. But it is GOOD downtime: ' +
            'mandatory and plannable. The system’s gift was ' +
            'splitting the stoppages you owe from the ones that hurt — ' +
            'cleaning gets scheduled; jams get fixed. Without data, it ' +
            'was all one sack.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy. Gracias', en: 'I will go. Thanks' },
            next: 'bye',
          },
        ],
      },
      'andon-1': {
        text: {
          es:
            'La torre de luces junto a la linea: verde operando, ' +
            'amarillo en preparacion, rojo parada. El dashboard usa los ' +
            'MISMOS colores — la linea y la pantalla hablan un solo ' +
            'idioma. Si ves rojo en la torre, ya hay una parada ' +
            'registrandose.',
          en:
            'The light tower by the line: green running, amber in ' +
            'setup, red stopped. The dashboard uses the SAME colours — ' +
            'the line and the screen speak one language. If the tower ' +
            'shows red, a stoppage is already being logged.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Voy a probarla', en: 'I will go try it' },
            next: 'bye',
          },
        ],
      },
    },
  }),

  carmen: defineDialog({
    name: { es: 'Carmen Yepez', en: 'Carmen Yepez' },
    chatter: [
      {
        es: 'Por primera vez VI los numeros de mi propia planta.',
        en: 'For the first time I SAW my own plant’s numbers.',
      },
      {
        es: 'Decidir con datos. Aqui eso fue una revolucion.',
        en: 'Deciding with data. Around here that was a revolution.',
      },
      {
        es: 'Casi dos años y el sistema nunca nos dejo botados.',
        en: 'Almost two years and the system never left us stranded.',
      },
      {
        es: 'Las planillas sueltas no cuadraban ni entre ellas.',
        en: 'The loose paper sheets did not even match each other.',
      },
      {
        es: 'El muchacho lo sostuvo y lo ajusto hasta el final.',
        en: 'The kid maintained and tuned it to the very end.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Carmen Yepez, jefa de produccion. Yo dirigia esta planta a ' +
            'ciegas: planillas sueltas, totales que no cuadraban y ' +
            'reuniones adivinando. El sistema de Pablo me encendio la ' +
            'luz. ¿Que quiere saber?',
          en:
            'Carmen Yepez, head of production. I used to run this plant ' +
            'blind: loose paper sheets, totals that never matched and ' +
            'meetings full of guessing. Pablo’s system switched the ' +
            'lights on. What would you like to know?',
        },
        options: [
          {
            label: {
              es: '¿Que cambio para usted?',
              en: 'What changed for you?',
            },
            next: 'numeros-1',
          },
          {
            label: {
              es: '¿Como era dirigir a ciegas?',
              en: 'What was running blind like?',
            },
            next: 'antes-1',
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
            'Queda lo que mas valoro del muchacho: no fue solo ' +
            'entregarlo — fue sostenerlo casi dos años.',
          en:
            'What I value most about the kid is left: it was not just ' +
            'shipping it — it was sustaining it for almost two years.',
        },
        options: [
          {
            label: { es: 'Cuenteme eso', en: 'Tell me about that' },
            next: 'sistema-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Mire el cuadro de la disponibilidad antes de irse: esa ' +
            'formula tan simple es la que me dice como va MI planta. Y ' +
            'cuidese, que aqui todo el mundo sale con complejo B.',
          en:
            'Look at the availability picture before you go: that ' +
            'simple formula is what tells me how MY plant is doing. And ' +
            'take care — everyone leaves this place with B-complex.',
        },
        options: [{ label: { es: 'Hasta luego', en: 'See you' }, next: null }],
      },

      'numeros-1': {
        text: {
          es:
            'Que por primera vez tuve los numeros de productividad A LA ' +
            'VISTA: cuanto opero cada linea, cuanto estuvo parada y por ' +
            'que causa. No planillas sueltas — un dashboard. Suena ' +
            'basico; aqui fue un antes y un despues.',
          en:
            'For the first time I had the productivity numbers IN ' +
            'SIGHT: how long each line ran, how long it sat stopped and ' +
            'for what cause. Not loose sheets — a dashboard. Sounds ' +
            'basic; here it was a before-and-after.',
        },
        options: [
          {
            label: {
              es: '¿Y que decisiones tomo?',
              en: 'And what decisions did you make?',
            },
            next: 'numeros-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'numeros-2': {
        text: {
          es:
            'Las que los datos mandaban: el Pareto puso arriba el ' +
            'cambio de formato y la limpieza, asi que reorganizamos ' +
            'lotes y programamos la sanitizacion para cambiar menos ' +
            'veces. El analisis contribuyo a subir la productividad — ' +
            'con datos, no con carisma.',
          en:
            'The ones the data dictated: the Pareto ranked changeover ' +
            'and cleaning on top, so we reorganised batches and ' +
            'scheduled sanitisation to switch fewer times. The analysis ' +
            'contributed to raising productivity — with data, not ' +
            'charisma.',
        },
        options: [
          {
            label: {
              es: '¿Confio en el sistema desde el dia uno?',
              en: 'Did you trust the system from day one?',
            },
            next: 'numeros-3',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'numeros-3': {
        text: {
          es:
            'No, y lo confieso: las primeras semanas pedia el reporte Y ' +
            'las planillas, por si acaso. Hasta que el reporte cuadro ' +
            'tres viernes seguidos y las planillas no cuadraron ' +
            'ninguno. Guarde los papeles y no los volvi a pedir.',
          en:
            'No, I will confess: the first weeks I asked for the report ' +
            'AND the paper sheets, just in case. Until the report ' +
            'balanced three Fridays in a row and the sheets balanced ' +
            'none. I filed the papers away and never asked again.',
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
            '¿Cuanto perdimos esta semana y por que causa? No sabia. ' +
            'Tenia un monton de planillas que ni cuadraban entre si y ' +
            'un reporte que tardaba VARIAS horas de calculadora en ' +
            'armarse. Dirigir asi es adivinar con uniforme.',
          en:
            'How much did we lose this week and to what cause? I did ' +
            'not know. I had a pile of paper sheets that did not even ' +
            'match each other and a report that took SEVERAL calculator ' +
            'hours to assemble. Managing like that is guessing in ' +
            'uniform.',
        },
        options: [
          {
            label: {
              es: '¿Y el sistema lo resolvio?',
              en: 'And the system solved it?',
            },
            next: 'antes-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'antes-2': {
        text: {
          es:
            'Lo resolvio de raiz: la parada se registra cuando ocurre, ' +
            'no cuando alguien la recuerda. El reporte que costaba una ' +
            'tarde ahora es una consulta directa. Y las causas — eso ' +
            'nadie lo habia visto NUNCA — ordenadas de mayor a menor.',
          en:
            'Solved at the root: the stoppage is logged when it ' +
            'happens, not when someone remembers it. The report that ' +
            'cost an afternoon is now a direct query. And the causes — ' +
            'which nobody had EVER seen — ranked top to bottom.',
        },
        options: [
          {
            label: { es: 'Hay mas temas, ¿no?', en: 'There is more, right?' },
            next: 'hub2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'sistema-1': {
        text: {
          es:
            'Cualquiera entrega un sistema; pocos lo sostienen. Este ' +
            'estuvo casi dos años en uso productivo porque el muchacho ' +
            'volvia: escuchaba a Nelida, a Rafael, a mi, y ajustaba. ' +
            'Una causa nueva en el catalogo, un reporte que faltaba... ' +
            'el sistema crecio CON la planta.',
          en:
            'Anyone can ship a system; few sustain one. This ran for ' +
            'almost two years in production because the kid kept coming ' +
            'back: he listened to Nelida, to Rafael, to me, and tuned ' +
            'it. A new cause in the catalogue, a missing report... the ' +
            'system grew WITH the plant.',
        },
        options: [
          {
            label: {
              es: '¿Que le dejo a usted eso?',
              en: 'What did that leave you with?',
            },
            next: 'sistema-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'sistema-2': {
        text: {
          es:
            'Una vara para medir proveedores: el que se sienta con ' +
            'produccion antes de programar, entrega herramientas; el ' +
            'que no, entrega problemas nuevos. Pablo era de los ' +
            'primeros. Me consta que despues siguio creciendo — no me ' +
            'extraña nada.',
          en:
            'A yardstick for measuring vendors: whoever sits with ' +
            'production before coding delivers tools; whoever does not, ' +
            'delivers new problems. Pablo was the first kind. I hear he ' +
            'kept growing afterwards — no surprise at all.',
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
} satisfies Record<string, NpcDialog>
