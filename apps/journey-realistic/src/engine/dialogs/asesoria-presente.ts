/**
 * @module dialogs/asesoria-presente (engine)
 * @description Arboles de dialogo de la sala 5 presente: Asesoria /
 *   PROSALUD (nov-dic 2015). El primer trabajo COBRADO de Pablo como
 *   consultor: rescato en ~1 semana una tesis bloqueada por meses,
 *   desarrollo e implanto EL SOLO la solucion web local (PHP + MySQL en
 *   XAMPP) para PROSALUD y enseño al equipo a exponer/defender. 5 NPCs
 *   con los 2 enfoques del canon (informe 17): Jhonny Parra y Oriana
 *   Castillo (tesistas), Coromoto Linares (farmacia) y Maigualida Torres
 *   (admision) como personal del instituto, y la Dra. Xiomara Graterol
 *   (directora que encargo y pago la solucion). Eje doble: el RESCATE
 *   (meses -> 1 semana) y la MENTORIA PAGADA (no solo programo: les
 *   enseño a defender). La sala NUNCA menciona una segunda tesis.
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const ASESORIA_PRESENTE_DIALOGS = {
  jhonny: defineDialog({
    name: { es: 'Jhonny Parra', en: 'Jhonny Parra' },
    chatter: [
      {
        es: 'Cuatro meses trancados. Pablo lo destranco en una semana.',
        en: 'Four months stuck. Pablo unstuck it in one week.',
      },
      {
        es: 'Ahora el codigo lo explico yo. Linea por linea.',
        en: 'Now I explain the code myself. Line by line.',
      },
      {
        es: 'El diagnostico fue una tarde. UNA tarde.',
        en: 'The diagnosis took one afternoon. ONE afternoon.',
      },
      {
        es: 'Include, consulta, tabla. Ya no le tengo miedo al PHP.',
        en: 'Include, query, table. PHP does not scare me anymore.',
      },
      {
        es: 'La defensa es en diciembre. Y por fin dormimos.',
        en: 'The defence is in December. And we finally sleep.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Jhonny, tesista. Esta tesis estuvo VARADA cuatro meses hasta ' +
            'que llego Pablo en noviembre. Hoy el sistema corre en todo el ' +
            'instituto y yo lo entiendo linea por linea. ¿Que quieres saber?',
          en:
            'Jhonny, thesis student. This thesis was STUCK for four months ' +
            'until Pablo arrived in November. Today the system runs across ' +
            'the whole institute and I understand it line by line. What do ' +
            'you want to know?',
        },
        options: [
          {
            label: {
              es: '¿Que tenia trancada la tesis?',
              en: 'What had the thesis stuck?',
            },
            next: 'bloqueo-1',
          },
          {
            label: {
              es: '¿Que hizo Pablo al llegar?',
              en: 'What did Pablo do on arrival?',
            },
            next: 'diag-1',
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
            'Queda lo mejor: como nos enseño a DEFENDER lo que ahora es ' +
            'nuestro, o mi resumen de todo el rescate.',
          en:
            'The best part remains: how he taught us to DEFEND what is now ' +
            'ours, or my summary of the whole rescue.',
        },
        options: [
          {
            label: {
              es: '¿Como los preparo?',
              en: 'How did he prepare you?',
            },
            next: 'mentoria-1',
          },
          {
            label: { es: 'Dame tu resumen', en: 'Give me your summary' },
            next: 'resumen-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Habla con Oriana: ella presenta el modulo de farmacia y lo ' +
            'cuenta mejor que yo. Y si quieres ver el drama completo, la ' +
            'grieta del muro te lleva a los meses del bloqueo.',
          en:
            'Talk to Oriana: she presents the pharmacy module and tells it ' +
            'better than I do. And if you want the full drama, the rift on ' +
            'the wall takes you to the stuck months.',
        },
        options: [{ label: { es: 'Hasta luego', en: 'See you' }, next: null }],
      },

      'bloqueo-1': {
        text: {
          es:
            'Heredamos codigo de intentos anteriores: paginas PHP que se ' +
            'llamaban entre si sin orden, consultas repetidas y una base ' +
            'de datos que nadie del equipo sabia explicar. Cada arreglo ' +
            'rompia otra cosa. Cuatro meses asi.',
          en:
            'We inherited code from earlier attempts: PHP pages calling ' +
            'each other with no order, duplicated queries and a database ' +
            'nobody on the team could explain. Every fix broke something ' +
            'else. Four months of that.',
        },
        options: [
          {
            label: {
              es: '¿Y como se sentia eso?',
              en: 'And how did that feel?',
            },
            next: 'bloqueo-2',
          },
          {
            label: {
              es: '¿Quien los desatasco?',
              en: 'Who got you unstuck?',
            },
            next: 'diag-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'bloqueo-2': {
        text: {
          es:
            'Como un examen que no termina nunca. La fecha de defensa ' +
            'rodeada en rojo, el calendario tachandose solo, y yo sin ' +
            'poder explicar ni el login. Hasta que la doctora Graterol ' +
            'dijo: "esto se resuelve con un profesional". Y lo contrato.',
          en:
            'Like an exam that never ends. The defence date circled in ' +
            'red, the calendar crossing itself out, and me unable to ' +
            'explain even the login. Until doctor Graterol said: "this ' +
            'takes a professional". And she hired him.',
        },
        options: [
          {
            label: {
              es: '¿Y que hizo Pablo?',
              en: 'And what did Pablo do?',
            },
            next: 'diag-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'diag-1': {
        text: {
          es:
            'Llego un lunes y no escribio codigo: LEYO. Se sento con lo ' +
            'heredado una tarde entera y salio con la lista exacta de ' +
            'puntos de falla: donde se caia, que sobraba, que faltaba. ' +
            'Cuatro meses de misterio resueltos en una tarde de lectura.',
          en:
            'He arrived on a Monday and wrote no code: he READ. He sat ' +
            'with the inherited mess for a whole afternoon and came out ' +
            'with the exact list of failure points: where it crashed, what ' +
            'was redundant, what was missing. Four months of mystery ' +
            'solved in one afternoon of reading.',
        },
        options: [
          {
            label: {
              es: '¿Y despues del diagnostico?',
              en: 'And after the diagnosis?',
            },
            next: 'diag-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'diag-2': {
        text: {
          es:
            'El cronograma que ves en la pared: siete dias. Diagnostico, ' +
            'arquitectura nueva, desarrollo, implantacion en el instituto ' +
            'y ensayo de la defensa. Lo desarrollo EL SOLO — nosotros ' +
            'mirabamos, preguntabamos y aprendiamos. Y se cumplio dia por ' +
            'dia.',
          en:
            'The timeline you see on the wall: seven days. Diagnosis, new ' +
            'architecture, development, deployment at the institute and ' +
            'defence rehearsal. He built it ALONE — we watched, asked and ' +
            'learned. And it was met day by day.',
        },
        options: [
          {
            label: {
              es: '¿Aprendian mientras el programaba?',
              en: 'You learned while he coded?',
            },
            next: 'mentoria-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'mentoria-1': {
        text: {
          es:
            'Esa fue la diferencia: Pablo no nos regalo la tesis, nos la ' +
            'EXPLICO. Cada tabla de la base, cada include, cada decision: ' +
            '"esto va aqui por esto". Al final el codigo era suyo de ' +
            'autor... pero nuestro de entendimiento.',
          en:
            'That was the difference: Pablo did not gift us the thesis, ' +
            'he EXPLAINED it to us. Every table, every include, every ' +
            'decision: "this goes here because of this". In the end the ' +
            'code was his by authorship... but ours by understanding.',
        },
        options: [
          {
            label: {
              es: '¿Y la defensa como va?',
              en: 'And how is the defence going?',
            },
            next: 'defensa-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'defensa-1': {
        text: {
          es:
            'Ensayada con proyector y todo — ahi esta la pantalla. Pablo ' +
            'nos hacia las preguntas dificiles del jurado hasta que las ' +
            'respuestas salian solas. Hoy me preguntas por cualquier ' +
            'consulta SQL del sistema y te la explico sin mirar.',
          en:
            'Rehearsed with the projector and all — the screen is right ' +
            'there. Pablo drilled us with the jury’s hard questions until ' +
            'the answers came out on their own. Ask me about any SQL query ' +
            'in the system today and I will explain it without looking.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
      'resumen-1': {
        text: {
          es:
            'Mi resumen: cuatro meses varados, una tarde de diagnostico, ' +
            'una semana de trabajo y una tesis que ahora podemos defender ' +
            'con la frente en alto. Eso hizo Pablo en 2015. Y le PAGARON ' +
            'por hacerlo, como debe ser.',
          en:
            'My summary: four months stuck, one afternoon of diagnosis, ' +
            'one week of work and a thesis we can now defend with our ' +
            'heads high. That is what Pablo did in 2015. And he got PAID ' +
            'for it, as it should be.',
        },
        options: [
          {
            label: {
              es: 'Bien dicho. Volvamos',
              en: 'Well said. Back to topics',
            },
            next: 'hub',
          },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
    },
  }),

  oriana: defineDialog({
    name: { es: 'Oriana Castillo', en: 'Oriana Castillo' },
    chatter: [
      {
        es: 'Lamina cuatro: arquitectura. Me la se hasta dormida.',
        en: 'Slide four: architecture. I know it in my sleep.',
      },
      {
        es: 'Le pagaron por programar Y por enseñarnos. Valio todo.',
        en: 'He got paid to code AND to teach us. Worth every bit.',
      },
      {
        es: 'Ensayamos con el proyector hasta que salio solo.',
        en: 'We rehearsed with the projector until it flowed.',
      },
      {
        es: 'Yo presento farmacia. Y ya no me tiembla la voz.',
        en: 'I present pharmacy. And my voice no longer shakes.',
      },
      {
        es: 'Preguntame lo que quieras del sistema. Atrevete.',
        en: 'Ask me anything about the system. I dare you.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Oriana, tesista. En noviembre yo no podia ni abrir el codigo ' +
            'sin angustia; en diciembre defiendo el modulo de farmacia ' +
            'ante el jurado. En el medio: Pablo. ¿Que quieres saber?',
          en:
            'Oriana, thesis student. In November I could not even open ' +
            'the code without anguish; in December I defend the pharmacy ' +
            'module before the jury. In between: Pablo. What do you want ' +
            'to know?',
        },
        options: [
          {
            label: {
              es: '¿Como fue el trato con Pablo?',
              en: 'What was the deal with Pablo?',
            },
            next: 'pago-1',
          },
          {
            label: {
              es: '¿Como ensayaron la defensa?',
              en: 'How did you rehearse the defence?',
            },
            next: 'ensayo-1',
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
            '¿Te cuento del sistema en si — la web local que corre en ' +
            'todo el instituto — o de mi modulo de farmacia?',
          en:
            'Shall I tell you about the system itself — the local web app ' +
            'running across the institute — or about my pharmacy module?',
        },
        options: [
          {
            label: { es: 'Del sistema', en: 'About the system' },
            next: 'sistema-1',
          },
          {
            label: { es: 'De tu modulo', en: 'About your module' },
            next: 'farmacia-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Si pasas por el proyector, dale al ensayo: veras las laminas ' +
            'que tanto sudamos. Y el showcase junto a la puerta tiene el ' +
            'sistema vivo, con su navegador de 2015 y todo.',
          en:
            'If you pass the projector, try the rehearsal: you will see ' +
            'the slides we sweated over. And the showcase by the door has ' +
            'the live system, 2015 browser chrome and all.',
        },
        options: [{ label: { es: 'Hasta luego', en: 'See you' }, next: null }],
      },

      'pago-1': {
        text: {
          es:
            'La doctora Graterol lo contrato con dos encargos: DESARROLLAR ' +
            'la solucion — el solo, porque nosotros ya habiamos demostrado ' +
            'que no salia — y ENSEÑARNOS a exponerla y defenderla. Le ' +
            'pagaron por las dos cosas. Su primer trabajo de consultor.',
          en:
            'Doctor Graterol hired him with two mandates: to BUILD the ' +
            'solution — alone, because we had already proven it would not ' +
            'happen — and to TEACH us to present and defend it. He was ' +
            'paid for both. His first consulting job.',
        },
        options: [
          {
            label: { es: '¿Y valio la pena?', en: 'And was it worth it?' },
            next: 'pago-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'pago-2': {
        text: {
          es:
            'Toda. Un profesional que en una semana entrega lo que no ' +
            'salio en meses, y que ademas te deja SABIENDO — eso no es un ' +
            'gasto, es la mejor inversion que hizo este instituto en 2015. ' +
            'Hasta el sobre del pago quedo en la mesa como recuerdo.',
          en:
            'Completely. A professional who delivers in one week what did ' +
            'not happen in months, and leaves you KNOWING on top — that ' +
            'is not an expense, it is the best investment this institute ' +
            'made in 2015. Even the payment envelope stayed on the table ' +
            'as a keepsake.',
        },
        options: [
          {
            label: {
              es: '¿Que aprendiste tu?',
              en: 'What did you learn?',
            },
            next: 'ensayo-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'ensayo-1': {
        text: {
          es:
            'Como un entrenamiento: proyector encendido, laminas en orden ' +
            '— titulo, problema, arquitectura, demo, conclusiones — y ' +
            'Pablo de jurado malvado. Nos cortaba, nos repreguntaba, nos ' +
            'hacia empezar de nuevo. Ronda tras ronda hasta que salio ' +
            'redondo.',
          en:
            'Like training camp: projector on, slides in order — title, ' +
            'problem, architecture, demo, conclusions — and Pablo playing ' +
            'the evil jury. He cut us off, asked follow-ups, made us start ' +
            'over. Round after round until it came out clean.',
        },
        options: [
          {
            label: {
              es: '¿Y funciono el metodo?',
              en: 'And did the method work?',
            },
            next: 'ensayo-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'ensayo-2': {
        text: {
          es:
            'En el primer ensayo me temblaba la voz y me salte dos ' +
            'laminas. En el ultimo, respondi la pregunta trampa de las ' +
            'claves foraneas sin pestañear. Pablo dijo "lista". Y tenia ' +
            'razon: ahora la que se sabe farmacia soy yo.',
          en:
            'In the first rehearsal my voice shook and I skipped two ' +
            'slides. In the last one I answered the foreign-key trick ' +
            'question without blinking. Pablo said "ready". And he was ' +
            'right: now I am the one who owns pharmacy.',
        },
        options: [
          {
            label: {
              es: 'Cuentame tu modulo',
              en: 'Tell me about your module',
            },
            next: 'farmacia-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'farmacia-1': {
        text: {
          es:
            'Farmacia e inventario: entradas, salidas y la alerta de ' +
            'minimos que pidio la señora Coromoto. Cada despacho descuenta ' +
            'stock y si un insumo toca su minimo, la fila se pone roja ' +
            'ANTES de que falte. En papel eso era imposible.',
          en:
            'Pharmacy and inventory: stock in, stock out and the minimum ' +
            'alert Mrs Coromoto asked for. Every dispatch decrements stock ' +
            'and if an item hits its minimum, the row turns red BEFORE it ' +
            'runs out. On paper that was impossible.',
        },
        options: [
          {
            label: {
              es: '¿Y el resto del sistema?',
              en: 'And the rest of the system?',
            },
            next: 'sistema-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'sistema-1': {
        text: {
          es:
            'Web local: PHP y MySQL sobre XAMPP, servidos desde esa torre ' +
            'con etiqueta que ves alla. Cada PC del instituto entra por el ' +
            'navegador a la misma direccion de red — sin instalar nada en ' +
            'los puestos. Citas, farmacia y afiliados en un solo sistema.',
          en:
            'A local web app: PHP and MySQL on XAMPP, served from that ' +
            'labelled tower over there. Every institute PC reaches the ' +
            'same network address through the browser — nothing installed ' +
            'per seat. Appointments, pharmacy and members in one system.',
        },
        options: [
          {
            label: {
              es: '¿Por que web y no escritorio?',
              en: 'Why web and not desktop?',
            },
            next: 'sistema-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'sistema-2': {
        text: {
          es:
            'Pablo lo decidio en el diagnostico: muchos puestos, un solo ' +
            'servidor, cero instalaciones. Con el navegador que ya tenia ' +
            'cada PC bastaba. En 2015 y con los equipos del instituto, la ' +
            'web local era la respuesta honesta — y la tesis lo defiende ' +
            'asi.',
          en:
            'Pablo decided it during the diagnosis: many seats, one ' +
            'server, zero installs. The browser each PC already had was ' +
            'enough. In 2015, with the institute’s hardware, a local web ' +
            'app was the honest answer — and the thesis defends it that ' +
            'way.',
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

  coromoto: defineDialog({
    name: { es: 'Coromoto Linares', en: 'Coromoto Linares' },
    chatter: [
      {
        es: 'Stock al dia. Sin tachones. Todavia no me lo creo.',
        en: 'Stock up to date. No scribbles. I still cannot believe it.',
      },
      {
        es: 'La alerta roja me avisa ANTES. Antes, señores.',
        en: 'The red alert warns me BEFORE. Before, people.',
      },
      {
        es: 'Yo se la pedi a Pablo. Dos dias tardo.',
        en: 'I asked Pablo for it. It took him two days.',
      },
      {
        es: 'El cuaderno lo guarde de recuerdo. De escarmiento.',
        en: 'I kept the notebook as a keepsake. As a warning.',
      },
      {
        es: 'Despacho, descargo, y el numero baja solo.',
        en: 'I dispatch, I log it, and the number drops on its own.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Coromoto, encargada de la farmacia del instituto. Durante ' +
            'años mi inventario fue un cuaderno con mas tachones que ' +
            'letras. Desde diciembre es una pantalla que no se equivoca. ' +
            '¿Que quieres saber?',
          en:
            'Coromoto, in charge of the institute pharmacy. For years my ' +
            'inventory was a notebook with more scribbles than words. ' +
            'Since December it is a screen that does not get it wrong. ' +
            'What do you want to know?',
        },
        options: [
          {
            label: {
              es: '¿Como era con el cuaderno?',
              en: 'How was it with the notebook?',
            },
            next: 'cuaderno-1',
          },
          {
            label: {
              es: '¿Que es la alerta de minimos?',
              en: 'What is the minimum alert?',
            },
            next: 'alerta-1',
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
            'Puedo contarte como es despachar hoy, o darte mi opinion del ' +
            'muchacho que armo todo esto.',
          en:
            'I can tell you what dispatching looks like today, or give ' +
            'you my take on the young man who built all this.',
        },
        options: [
          {
            label: { es: '¿Como es hoy?', en: 'What is it like today?' },
            next: 'hoy-1',
          },
          {
            label: { es: 'Tu opinion de Pablo', en: 'Your take on Pablo' },
            next: 'resumen-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Si cruzas la grieta esa vas a ver mi cuaderno como era: ' +
            'tachon sobre tachon. Miralo y despues me cuentas si la ' +
            'pantalla no es una bendicion.',
          en:
            'If you cross that rift you will see my notebook as it was: ' +
            'scribble over scribble. Look at it and then tell me the ' +
            'screen is not a blessing.',
        },
        options: [{ label: { es: 'Hasta luego', en: 'See you' }, next: null }],
      },

      'cuaderno-1': {
        text: {
          es:
            'Cada caja que entraba o salia, una linea a lapiz. Se ' +
            'despachaba rapido y se anotaba "despues". El despues no ' +
            'llegaba, y el cuaderno mentia. Yo hacia inventario contando ' +
            'cajas los viernes por la tarde.',
          en:
            'Every box in or out, one pencil line. Dispatch fast, log it ' +
            '"later". Later never came, and the notebook lied. I did ' +
            'inventory by counting boxes on Friday afternoons.',
        },
        options: [
          {
            label: {
              es: '¿Y cuando fallaba?',
              en: 'And when it failed?',
            },
            next: 'cuaderno-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'cuaderno-2': {
        text: {
          es:
            'Me enteraba de que no habia acetaminofen cuando la señora ya ' +
            'estaba en la ventanilla con el record en la mano. "No hay, ' +
            'mi amor, vuelva la semana que viene". Esa frase me dolia mas ' +
            'a mi que a ella.',
          en:
            'I found out we were out of paracetamol when the lady was ' +
            'already at the window holding her slip. "None left, dear, ' +
            'come back next week". That sentence hurt me more than her.',
        },
        options: [
          {
            label: {
              es: '¿Y como se arreglo?',
              en: 'And how did it get fixed?',
            },
            next: 'alerta-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'alerta-1': {
        text: {
          es:
            'Cuando Pablo vino a levantar el modulo de farmacia, yo le ' +
            'pedi UNA cosa: "avisame ANTES de que se acabe". Le puso un ' +
            'minimo a cada insumo, y cuando el stock lo toca, la fila se ' +
            'pone roja en la pantalla. Dos dias tardo en tenerlo listo.',
          en:
            'When Pablo came to survey the pharmacy module I asked him ' +
            'for ONE thing: "warn me BEFORE it runs out". He gave every ' +
            'item a minimum, and when stock hits it, the row turns red on ' +
            'screen. It took him two days to have it ready.',
        },
        options: [
          {
            label: {
              es: '¿Y funciona de verdad?',
              en: 'Does it really work?',
            },
            next: 'alerta-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'alerta-2': {
        text: {
          es:
            'La semana pasada el ibuprofeno toco minimo un martes; el ' +
            'pedido salio el miercoles y la señora del viernes se llevo ' +
            'su medicina sin enterarse de nada. ESO es el sistema: los ' +
            'problemas se resuelven antes de llegar a la ventanilla.',
          en:
            'Last week ibuprofen hit its minimum on a Tuesday; the order ' +
            'went out Wednesday and Friday’s lady took her medicine ' +
            'none the wiser. THAT is the system: problems get solved ' +
            'before they reach the window.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
      'hoy-1': {
        text: {
          es:
            'Hoy despacho con la pantalla al lado: busco el insumo, ' +
            'marco la salida y el numero baja solo. Entrego mas rapido, ' +
            'me equivoco menos y los viernes por la tarde... los viernes ' +
            'por la tarde ya no cuento cajas.',
          en:
            'Today I dispatch with the screen beside me: find the item, ' +
            'log the withdrawal and the number drops on its own. I hand ' +
            'out faster, err less, and on Friday afternoons... on Friday ' +
            'afternoons I no longer count boxes.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy contenta', en: 'I leave happy' },
            next: 'bye',
          },
        ],
      },
      'resumen-1': {
        text: {
          es:
            'Ese muchacho vino por una tesis y termino arreglandonos el ' +
            'instituto. Escucho a la gente de a pie — a mi, a Maigualida ' +
            '— y lo que pedimos aparecio en la pantalla. Ojala todos los ' +
            'que hacen sistemas fueran asi.',
          en:
            'That young man came for a thesis and ended up fixing the ' +
            'institute for us. He listened to the ground staff — to me, ' +
            'to Maigualida — and what we asked for appeared on screen. I ' +
            'wish everyone who builds systems were like that.',
        },
        options: [
          {
            label: {
              es: 'Bonito. Volvamos',
              en: 'Nice. Back to topics',
            },
            next: 'hub',
          },
          {
            label: { es: 'Me voy. Gracias', en: 'I will go. Thanks' },
            next: 'bye',
          },
        ],
      },
    },
  }),

  maigualida: defineDialog({
    name: { es: 'Maigualida Torres', en: 'Maigualida Torres' },
    chatter: [
      {
        es: 'Turno cero cuarenta y dos. Y nadie pelea.',
        en: 'Ticket zero forty-two. And nobody fights.',
      },
      {
        es: 'Cedula, enter, afiliado. Se acabaron las carpetas.',
        en: 'ID, enter, member. No more folders.',
      },
      {
        es: 'Los papelitos a mano quedaron en el pasado. Literal.',
        en: 'The hand-numbered slips stayed in the past. Literally.',
      },
      {
        es: 'El display canta el turno mejor que yo.',
        en: 'The display calls the ticket better than I do.',
      },
      {
        es: 'La cola avanza. AVANZA.',
        en: 'The queue moves. It MOVES.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Maigualida, admision y citas. Yo era la que repartia ' +
            'papelitos numerados a mano y aguantaba las peleas de la ' +
            'cola. Ahora el display canta el turno y yo atiendo. ¿Que ' +
            'quieres saber?',
          en:
            'Maigualida, admissions and appointments. I was the one ' +
            'handing out hand-numbered slips and refereeing queue fights. ' +
            'Now the display calls the ticket and I do my job. What do ' +
            'you want to know?',
        },
        options: [
          {
            label: {
              es: '¿Como era con los papelitos?',
              en: 'How was it with the slips?',
            },
            next: 'papelitos-1',
          },
          {
            label: {
              es: '¿Como funciona hoy la cola?',
              en: 'How does the queue work today?',
            },
            next: 'display-1',
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
            'Falta lo mio: el buscador de afiliados. Y si te interesa la ' +
            'cocina, la torre del servidor esta ahi mismo.',
          en:
            'My favourite is missing: the member search. And if you like ' +
            'the plumbing, the server tower is right there.',
        },
        options: [
          {
            label: { es: 'El buscador', en: 'The search' },
            next: 'buscador-1',
          },
          {
            label: { es: 'La torre esa', en: 'That tower' },
            next: 'red-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Toma un turno en el mostrador antes de irte, aunque sea de ' +
            'mentira: el display sube solo y es un gustazo. Al muchacho ' +
            'del sistema, donde este, que le vaya bonito.',
          en:
            'Take a ticket at the counter before you go, even just for ' +
            'fun: the display climbs on its own and it is a delight. ' +
            'Wherever the system kid is, may life treat him well.',
        },
        options: [{ label: { es: 'Hasta luego', en: 'See you' }, next: null }],
      },

      'papelitos-1': {
        text: {
          es:
            'Un pincho con papelitos numerados a lapiz. Yo los cortaba en ' +
            'la mañana, la gente los perdia al mediodia y a las diez ya ' +
            'habia dos señores con el mismo cuarenta y uno, cada uno ' +
            'jurando que el suyo era el bueno.',
          en:
            'A spike of pencil-numbered slips. I cut them in the morning, ' +
            'people lost them by noon, and by ten there were two men ' +
            'holding the same forty-one, each swearing his was the real ' +
            'one.',
        },
        options: [
          {
            label: {
              es: '¿Y como terminaba eso?',
              en: 'And how did that end?',
            },
            next: 'papelitos-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'papelitos-2': {
        text: {
          es:
            'Con la mañana perdida y conmigo de arbitro. Sin papelito no ' +
            'habia turno, y sin turno la señora volvia otro dia — con lo ' +
            'que cuesta venir desde el municipio. Esas peleas no eran por ' +
            'mala gente: eran por un sistema malo.',
          en:
            'With the morning lost and me as referee. No slip meant no ' +
            'turn, and no turn meant coming back another day — and ' +
            'getting here from the far municipios is not cheap. Those ' +
            'fights were not bad people: they were a bad system.',
        },
        options: [
          {
            label: { es: '¿Y ahora?', en: 'And now?' },
            next: 'display-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'display-1': {
        text: {
          es:
            'Ahora el sistema asigna el turno y el display lo canta: ' +
            'numero, servicio y a que ventanilla. Nadie discute con una ' +
            'pantalla. La cola de la mañana que antes duraba hasta el ' +
            'almuerzo hoy se despacha en un par de horas.',
          en:
            'Now the system assigns the ticket and the display calls it: ' +
            'number, service and window. Nobody argues with a screen. The ' +
            'morning queue that used to last until lunch clears in a ' +
            'couple of hours today.',
        },
        options: [
          {
            label: {
              es: '¿Y el buscador de afiliados?',
              en: 'And the member search?',
            },
            next: 'buscador-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'buscador-1': {
        text: {
          es:
            'Escribo la cedula y sale el afiliado al instante: datos, ' +
            'municipio, si tiene cita. Antes eso era buscar una carpeta ' +
            'manila en el archivador — y rezar que estuviera donde debia. ' +
            'De minutos a un enter, igualito que me contaron del IPASME.',
          en:
            'I type the ID and the member appears instantly: details, ' +
            'municipio, whether they have an appointment. That used to be ' +
            'hunting a manila folder in the cabinet — and praying it was ' +
            'where it should be. From minutes to one enter key, just like ' +
            'they say happened at IPASME.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
      'red-1': {
        text: {
          es:
            'La torre con la etiqueta "SERVIDOR LOCAL": ahi vive el ' +
            'sistema, dicen que en algo llamado XAMPP. Yo de eso no se — ' +
            'lo que se es que mi PC, la de farmacia y la de la doctora ' +
            'entran todas por el navegador a la misma direccion. Magia de ' +
            'red local, dijo Pablo.',
          en:
            'The tower labelled "LOCAL SERVER": the system lives there, ' +
            'on something called XAMPP they say. Not my department — what ' +
            'I know is that my PC, the pharmacy one and the doctor’s ' +
            'all reach the same address through the browser. Local ' +
            'network magic, Pablo said.',
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

  xiomara: defineDialog({
    name: { es: 'Dra. Xiomara Graterol', en: 'Dr. Xiomara Graterol' },
    chatter: [
      {
        es: 'Yo no pago promesas: pago sistemas funcionando.',
        en: 'I do not pay for promises: I pay for working systems.',
      },
      {
        es: 'Dos exigencias: implantado, y que ELLOS lo mantengan.',
        en: 'Two demands: deployed, and THEY must maintain it.',
      },
      {
        es: 'La carta de aceptacion la firme con gusto.',
        en: 'I signed the acceptance letter gladly.',
      },
      {
        es: 'El instituto respira distinto desde diciembre.',
        en: 'The institute breathes differently since December.',
      },
      {
        es: 'Ese muchacho cobro justo. Y rindio el doble.',
        en: 'That young man charged fairly. And delivered double.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Xiomara Graterol, coordino este instituto. Yo contrate a ' +
            'Pablo en noviembre de 2015 — y fue de las mejores decisiones ' +
            'administrativas que he firmado. ¿Que desea saber?',
          en:
            'Xiomara Graterol, I run this institute. I hired Pablo in ' +
            'November 2015 — one of the best administrative decisions I ' +
            'have ever signed. What would you like to know?',
        },
        options: [
          {
            label: {
              es: '¿Por que lo contrato?',
              en: 'Why did you hire him?',
            },
            next: 'encargo-1',
          },
          {
            label: {
              es: '¿Que le exigio?',
              en: 'What did you demand?',
            },
            next: 'exigencia-1',
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
            'Puedo contarle de la carta que firme para la universidad, o ' +
            'de lo que cambio en el instituto con el sistema.',
          en:
            'I can tell you about the letter I signed for the university, ' +
            'or about what changed in the institute with the system.',
        },
        options: [
          {
            label: { es: 'La carta', en: 'The letter' },
            next: 'carta-1',
          },
          {
            label: { es: 'Lo que cambio', en: 'What changed' },
            next: 'instituto-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      bye: {
        text: {
          es:
            'Cuidese. Y si el recorrido sigue, fijese en lo que ese ' +
            'muchacho construyo despues: quien rescata una tesis en una ' +
            'semana no se queda quieto mucho tiempo.',
          en:
            'Take care. And if the journey continues, watch what that ' +
            'young man built afterwards: whoever rescues a thesis in one ' +
            'week does not sit still for long.',
        },
        options: [{ label: { es: 'Hasta luego', en: 'See you' }, next: null }],
      },

      'encargo-1': {
        text: {
          es:
            'Porque el problema era doble. La tesis de los muchachos ' +
            'llevaba meses varada... y esa tesis era NUESTRO sistema: las ' +
            'citas, la farmacia, los afiliados. Cada mes que la tesis no ' +
            'avanzaba, el instituto seguia en papelitos y cuadernos.',
          en:
            'Because the problem was double. The students’ thesis had ' +
            'been stuck for months... and that thesis was OUR system: ' +
            'appointments, pharmacy, members. Every month the thesis did ' +
            'not move, the institute stayed on slips and notebooks.',
        },
        options: [
          {
            label: {
              es: '¿Y como fue el trato?',
              en: 'And what was the deal?',
            },
            next: 'encargo-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'encargo-2': {
        text: {
          es:
            'Un contrato claro y pagado: desarrollar el la solucion ' +
            'completa — solo, sin comites — y capacitar a los tesistas ' +
            'para exponerla y sostenerla. Noviembre y diciembre de 2015. ' +
            'Presupuesto justo, resultado el doble de lo esperado.',
          en:
            'A clear, paid contract: he would build the complete solution ' +
            '— alone, no committees — and coach the students to present ' +
            'and sustain it. November and December 2015. A fair budget, ' +
            'double the expected result.',
        },
        options: [
          {
            label: {
              es: '¿Que le exigio usted?',
              en: 'What did you demand?',
            },
            next: 'exigencia-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'exigencia-1': {
        text: {
          es:
            'Primera exigencia: IMPLANTADO. Yo no queria un CD en un ' +
            'cajon ni un demo bonito: queria el sistema corriendo en la ' +
            'admision, en la farmacia y en las citas, con mi personal ' +
            'usandolo. Pablo lo dejo servido en la red del instituto.',
          en:
            'First demand: DEPLOYED. I did not want a CD in a drawer or a ' +
            'pretty demo: I wanted the system running at admissions, the ' +
            'pharmacy and appointments, with my staff using it. Pablo ' +
            'left it serving on the institute network.',
        },
        options: [
          {
            label: {
              es: '¿Y la segunda exigencia?',
              en: 'And the second demand?',
            },
            next: 'exigencia-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'exigencia-2': {
        text: {
          es:
            'Que los tesistas quedaran en capacidad de MANTENERLO. Un ' +
            'sistema que solo entiende su autor es una deuda, no un ' +
            'activo. Por eso el contrato incluia la mentoria: cuando ' +
            'Pablo se fuera, el conocimiento tenia que quedarse aqui.',
          en:
            'That the students be able to MAINTAIN it. A system only its ' +
            'author understands is a liability, not an asset. That is why ' +
            'the contract included mentoring: when Pablo left, the ' +
            'knowledge had to stay here.',
        },
        options: [
          {
            label: {
              es: '¿Y se cumplio?',
              en: 'And was it met?',
            },
            next: 'carta-1',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'carta-1': {
        text: {
          es:
            'Se cumplio con creces. Vi a los muchachos ensayar la defensa ' +
            'hasta responder sin titubear, y al sistema despachar la cola ' +
            'de una mañana completa sin un papelito. Firme la carta de ' +
            'aceptacion para la universidad ese mismo dia.',
          en:
            'Met and exceeded. I watched the students rehearse the ' +
            'defence until they answered without hesitation, and the ' +
            'system clear a full morning queue without a single slip. I ' +
            'signed the university acceptance letter that very day.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: { es: 'Me voy con eso', en: 'I will leave with that' },
            next: 'bye',
          },
        ],
      },
      'instituto-1': {
        text: {
          es:
            'Menos colas, menos peleas, menos "vuelva mañana". La ' +
            'farmacia pide ANTES de quedarse sin nada y admision atiende ' +
            'en vez de arbitrar. PROSALUD rige la salud primaria de todo ' +
            'el estado: cada minuto que se ahorra aqui es un paciente ' +
            'mejor atendido alla afuera.',
          en:
            'Shorter queues, fewer fights, fewer "come back tomorrow". ' +
            'The pharmacy reorders BEFORE running dry and admissions ' +
            'serves instead of refereeing. PROSALUD steers the state’s ' +
            'primary healthcare: every minute saved here is a patient ' +
            'better served out there.',
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
