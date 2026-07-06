/**
 * @module dialogs/destacame-pasado (engine)
 * @description Arboles de dialogo del pasado de Destacame: el drama de
 *   deudas ANTES de la plataforma (sepia + coral de mora, informe 13).
 *   3 NPCs (decision del usuario: los 3): Don Hernan Poblete (deudor
 *   agobiado por tres deudas vencidas y la sucursal), Marta Sepulveda
 *   (deudora triste con el score por el suelo y solo cartas de
 *   cobranza) y Nicolas Vera (el operador que arma cada campaña a mano
 *   en planillas y tarda horas).
 */
import { defineDialog, type NpcDialog } from '../dialog'

export const DESTACAME_PASADO_DIALOGS = {
  hernan: defineDialog({
    name: { es: 'Don Hernan Poblete', en: 'Don Hernan Poblete' },
    chatter: [
      {
        es: 'Tres deudas... ¿y por cual empiezo?',
        en: 'Three debts... which one do I even start with?',
      },
      {
        es: 'Otra fila, otra mañana perdida.',
        en: 'Another queue, another lost morning.',
      },
      {
        es: 'Nadie me dice si hay descuento. Nadie.',
        en: 'Nobody tells me if there is a discount. Nobody.',
      },
      {
        es: 'La angustia de la morosidad no se la doy a nadie.',
        en: 'I would not wish the anguish of arrears on anyone.',
      },
      {
        es: 'El banco abre a las nueve. Yo entro a trabajar a las ocho.',
        en: 'The bank opens at nine. My shift starts at eight.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Hernan Poblete, para servirte... aunque servir no puedo ' +
            'mucho: tengo tres deudas vencidas y no se por donde ' +
            'empezar. ¿Que quieres saber de este calvario?',
          en:
            'Hernan Poblete, at your service... though I cannot serve ' +
            'much: I have three overdue debts and no idea where to ' +
            'start. What do you want to know about this ordeal?',
        },
        options: [
          {
            label: {
              es: '¿Como se paga una deuda hoy?',
              en: 'How do you pay a debt today?',
            },
            next: 'fila-1',
          },
          {
            label: {
              es: '¿Nadie lo ayuda a negociar?',
              en: 'Does nobody help you negotiate?',
            },
            next: 'negociar-1',
          },
          {
            label: { es: 'Animo, don Hernan', en: 'Hang in there' },
            next: null,
          },
        ],
      },
      'fila-1': {
        text: {
          es:
            'Yendo al banco. Fila para el numerito, fila para la ' +
            'caja, y al final un ejecutivo que te mira la mora y te ' +
            'dice "vuelva mañana con el comprobante". Un dia entero ' +
            'por CADA deuda — y tengo tres, en dos bancos distintos.',
          en:
            'By going to the bank. Queue for the ticket, queue for ' +
            'the teller, and at the end an officer looks at your ' +
            'arrears and says "come back tomorrow with the receipt". ' +
            'A full day for EACH debt — and I have three, across two ' +
            'different banks.',
        },
        options: [
          {
            label: {
              es: '¿Y pagar por internet?',
              en: 'What about paying online?',
            },
            next: 'fila-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'fila-2': {
        text: {
          es:
            '¿Deuda vencida por internet? No existe. La pagina del ' +
            'banco sirve para la cuenta al dia; en mora te manda a la ' +
            'sucursal. Como si la verguenza de deber fuera poca, hay ' +
            'que ir a contarla en persona.',
          en:
            'Overdue debt online? Does not exist. The bank’s site ' +
            'works for accounts in good standing; in arrears it sends ' +
            'you to the branch. As if the shame of owing were not ' +
            'enough, you must go tell it in person.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          { label: { es: 'Que injusto', en: 'So unfair' }, next: null },
        ],
      },
      'negociar-1': {
        text: {
          es:
            'Nadie. Dicen que a veces hay condonaciones, descuentos ' +
            'por pago... pero nadie te lo ofrece de frente. Si no ' +
            'sabes preguntar la palabra exacta, pagas completo. Y yo ' +
            'de bancos se lo justo.',
          en:
            'Nobody. They say there are sometimes write-offs, ' +
            'discounts for paying... but nobody offers it to your ' +
            'face. If you do not know the exact word to ask, you pay ' +
            'in full. And I know just enough about banks to get by.',
        },
        options: [
          {
            label: {
              es: '¿Que necesitaria usted?',
              en: 'What would you need?',
            },
            next: 'negociar-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'negociar-2': {
        text: {
          es:
            'Algo que me muestre TODAS mis deudas juntas, me diga ' +
            'cuanto piden de verdad por cerrarlas, y me deje pagar ' +
            'desde la casa. Sin fila, sin verguenza, sin letra chica. ' +
            '¿Existe eso en tu epoca?',
          en:
            'Something that shows me ALL my debts together, tells me ' +
            'what they truly ask to close them, and lets me pay from ' +
            'home. No queue, no shame, no fine print. Does that exist ' +
            'in your time?',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: {
              es: 'Cruce la grieta y vea',
              en: 'Cross the rift and see',
            },
            next: null,
          },
        ],
      },
    },
  }),

  marta: defineDialog({
    name: { es: 'Marta Sepulveda', en: 'Marta Sepulveda' },
    chatter: [
      {
        es: 'Otra carta de cobranza. La quinta del mes.',
        en: 'Another collection letter. Fifth this month.',
      },
      {
        es: 'El telefono suena y ya se quien es.',
        en: 'The phone rings and I already know who it is.',
      },
      {
        es: 'Mi score esta por el suelo y nadie me explica por que.',
        en: 'My score is through the floor and nobody explains why.',
      },
      {
        es: 'Me da verguenza hasta preguntar.',
        en: 'I am ashamed even to ask.',
      },
      {
        es: 'Dicen que soy "riesgo". Yo solo tuve un mal año.',
        en: 'They say I am "risk". I just had one bad year.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Marta. Disculpa el desorden de papeles... son cartas de ' +
            'cobranza, todas mias. Mi score esta por el suelo y ' +
            'siento que nadie me da una oportunidad. ¿Que quieres ' +
            'saber?',
          en:
            'Marta. Excuse the mess of papers... they are collection ' +
            'letters, all mine. My score is through the floor and it ' +
            'feels like nobody gives me a chance. What do you want to ' +
            'know?',
        },
        options: [
          {
            label: {
              es: '¿Que es eso del score?',
              en: 'What is this score thing?',
            },
            next: 'score-1',
          },
          {
            label: {
              es: '¿Como ve su situacion?',
              en: 'How do you see your situation?',
            },
            next: 'situacion-1',
          },
          {
            label: { es: 'Animo, Marta', en: 'Hang in there, Marta' },
            next: null,
          },
        ],
      },
      'score-1': {
        text: {
          es:
            'Un numero que deciden sobre mi y que yo no puedo ver. ' +
            'El banco lo mira y dice no. La tienda lo mira y dice no. ' +
            '¿Cuanto es? ¿Como se sube? Misterio. Solo se que el mio ' +
            'esta malo, porque todos me cierran la puerta.',
          en:
            'A number they decide about me that I cannot even see. ' +
            'The bank looks at it and says no. The store looks at it ' +
            'and says no. What is it? How do you raise it? A mystery. ' +
            'I only know mine is bad, because every door closes.',
        },
        options: [
          {
            label: {
              es: '¿Y si pudiera verlo gratis?',
              en: 'What if you could see it for free?',
            },
            next: 'score-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'score-2': {
        text: {
          es:
            '¿Verlo yo misma, saber que lo baja y que lo sube? Eso ' +
            'cambiaria todo. Una ya no estaria a ciegas: sabria que ' +
            'deuda atacar primero, que habito cuidar. Pero eso hoy no ' +
            'existe — o no para gente como yo.',
          en:
            'See it myself, know what drags it down and what lifts ' +
            'it? That would change everything. I would no longer be ' +
            'blind: I would know which debt to attack first, which ' +
            'habit to mind. But that does not exist today — not for ' +
            'people like me.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          { label: { es: 'Ya existira', en: 'It will exist' }, next: null },
        ],
      },
      'situacion-1': {
        text: {
          es:
            'Un circulo vicioso. No hay una app donde vea mi ' +
            'situacion clara: solo cartas que asustan y llamadas que ' +
            'humillan. Para negociar hay que ir a rogar a la ' +
            'sucursal... y a mi me da verguenza pedir ayuda.',
          en:
            'A vicious circle. There is no app where I can see my ' +
            'situation clearly: only scary letters and humiliating ' +
            'calls. To negotiate you must go beg at the branch... and ' +
            'I am ashamed to ask for help.',
        },
        options: [
          {
            label: {
              es: '¿Que le diria a la Marta del futuro?',
              en: 'What would you tell future Marta?',
            },
            next: 'situacion-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'situacion-2': {
        text: {
          es:
            'Que no se rinda. Que algun dia alguien va a construir ' +
            'algo que trate al deudor como persona: mostrar la deuda ' +
            'clara, ofrecer el descuento de frente, dejar pagar ' +
            'tranquila desde la casa. El dia que exista, yo soy la ' +
            'primera en la fila... bueno, ya sin fila.',
          en:
            'Do not give up. Someday someone will build something ' +
            'that treats a debtor like a person: show the debt ' +
            'clearly, offer the discount up front, let you pay in ' +
            'peace from home. The day it exists, I am first in ' +
            'line... well, no line anymore.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          { label: { es: 'Ya llega', en: 'It is coming' }, next: null },
        ],
      },
    },
  }),

  nicolas: defineDialog({
    name: { es: 'Nicolas Vera', en: 'Nicolas Vera' },
    chatter: [
      {
        es: 'Fila 8.412... fila 8.413... no me hablen.',
        en: 'Row 8,412... row 8,413... do not talk to me.',
      },
      {
        es: 'El cafe se enfrio hace dos horas.',
        en: 'The coffee went cold two hours ago.',
      },
      {
        es: 'Si esta planilla se corrompe, me voy a mi casa.',
        en: 'If this spreadsheet corrupts, I am going home.',
      },
      {
        es: 'Copiar, pegar, filtrar, rezar.',
        en: 'Copy, paste, filter, pray.',
      },
      {
        es: 'Son las siete y sigo armando la campaña de ayer.',
        en: 'It is seven pm and I am still building yesterday’s batch.',
      },
    ],
    start: 'hub',
    nodes: {
      hub: {
        text: {
          es:
            'Nicolas, operador de campañas... o mas bien albañil de ' +
            'planillas. Cada campaña la armo A MANO y me toma horas. ' +
            '¿Que quieres saber, rapido, que voy atrasado?',
          en:
            'Nicolas, campaign operator... more like spreadsheet ' +
            'bricklayer. I build every campaign BY HAND and it takes ' +
            'me hours. What do you want to know — quickly, I am ' +
            'behind?',
        },
        options: [
          {
            label: {
              es: '¿Como se arma una campaña?',
              en: 'How is a campaign built?',
            },
            next: 'manual-1',
          },
          {
            label: {
              es: '¿Que es lo que mas duele?',
              en: 'What hurts the most?',
            },
            next: 'dolor-1',
          },
          {
            label: { es: 'Te dejo trabajar', en: 'I will let you work' },
            next: null,
          },
        ],
      },
      'manual-1': {
        text: {
          es:
            'Exporto la base, filtro a mano quien califica, cruzo ' +
            'con otra planilla los descuentos, pego los correos en ' +
            'la herramienta de envio... y reviso fila por fila, ' +
            'porque un error aca es una oferta equivocada a un ' +
            'cliente real. HORAS. Cada. Vez.',
          en:
            'I export the base, hand-filter who qualifies, cross the ' +
            'discounts against another sheet, paste the emails into ' +
            'the sending tool... and review row by row, because one ' +
            'mistake here is a wrong offer to a real customer. ' +
            'HOURS. Every. Time.',
        },
        options: [
          {
            label: {
              es: '¿Y si algo sale mal?',
              en: 'And if something goes wrong?',
            },
            next: 'manual-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'manual-2': {
        text: {
          es:
            'Sale mal seguido. Un filtro corrido, un copy-paste de ' +
            'mas, y la campaña llega a quien no era. Entonces hay ' +
            'que deshacer, disculparse y volver a empezar — de ' +
            'nuevo a mano. Un solo pais y ya no doy abasto; ni ' +
            'pensar en dos.',
          en:
            'It goes wrong often. One shifted filter, one extra ' +
            'copy-paste, and the campaign reaches the wrong people. ' +
            'Then you undo, apologise and start over — by hand ' +
            'again. One country and I cannot keep up; imagine two.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          { label: { es: 'Aguante', en: 'Hold on' }, next: null },
        ],
      },
      'dolor-1': {
        text: {
          es:
            'Que todo esta aislado. La base por un lado, los ' +
            'descuentos por otro, el envio por otro — cero ' +
            'herramienta que lo junte. Yo SOY la integracion, con ' +
            'mis deditos. Y la integracion termina tardisimo todos ' +
            'los dias.',
          en:
            'That everything is siloed. The base on one side, the ' +
            'discounts on another, the sending tool on a third — no ' +
            'tool joins them. I AM the integration, with my own ' +
            'fingers. And the integration finishes terribly late ' +
            'every day.',
        },
        options: [
          {
            label: {
              es: '¿Que pediria usted?',
              en: 'What would you ask for?',
            },
            next: 'dolor-2',
          },
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
        ],
      },
      'dolor-2': {
        text: {
          es:
            'Un admin donde configure la campaña — segmento, oferta, ' +
            'canal — aprete un boton y salga sola, validada. Que las ' +
            'horas se vuelvan minutos. Dicen que alguien va a ' +
            'construir eso algun dia. Ese dia yo me tomo el cafe ' +
            'CALIENTE.',
          en:
            'An admin where I configure the campaign — segment, ' +
            'offer, channel — press one button and it goes out on ' +
            'its own, validated. Hours turned into minutes. They say ' +
            'someone will build that one day. That day I drink my ' +
            'coffee HOT.',
        },
        options: [
          { label: { es: 'Volvamos', en: 'Back to topics' }, next: 'hub' },
          {
            label: {
              es: 'Alguien lo construyo',
              en: 'Someone built it',
            },
            next: null,
          },
        ],
      },
    },
  }),
} satisfies Record<string, NpcDialog>
