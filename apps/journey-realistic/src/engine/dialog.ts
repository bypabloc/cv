/**
 * @module dialog (engine)
 * @description Sistema de dialogo con NPCs: arboles bilingues data-driven
 *   (nodos + opciones que se reencuentran), burbuja manga de "habla suelta"
 *   para el NPC cercano con prompt activo y helper `npcTalk` que convierte
 *   un NpcHandle en un interactable conversable (pausa la patrulla, saluda,
 *   mira al jugador y abre el panel DOM del HUD). Los arboles viven en
 *   `dialogs/<escena>.ts`; `defineDialog` los valida en DEV (referencias +
 *   alcanzabilidad) sin costo en prod.
 */
import type { Locale } from '../lib/rooms'
import type { NpcHandle } from './character'
import type { Interactable } from './state'

export type DialogLine = Record<Locale, string>

export interface DialogOption {
  label: DialogLine
  /** Id del nodo siguiente; null cierra la conversacion. */
  next: string | null
}

export interface DialogNode {
  text: DialogLine
  /** 1-4 opciones (4 solo en hubs); alguna rama termina con next null. */
  options: readonly DialogOption[]
}

export interface NpcDialog {
  /** Nombre visible del NPC (cabecera del panel + prompt "Hablar con"). */
  name: DialogLine
  /** Lineas de burbuja: se muestra 1 al azar al acercarse al NPC. */
  chatter: readonly DialogLine[]
  start: string
  nodes: Readonly<Record<string, DialogNode>>
}

export type OpenDialog = (npc: NpcDialog, onClose?: () => void) => void

/** BFS desde start: nodos alcanzables + referencias rotas (issues). */
function walkReachable(dialog: NpcDialog, issues: string[]): Set<string> {
  const reachable = new Set<string>()
  const queue = [dialog.start]
  while (queue.length > 0) {
    const id = queue.pop()
    if (id === undefined || reachable.has(id)) {
      continue
    }
    reachable.add(id)
    const node = dialog.nodes[id]
    if (!node) {
      issues.push(`opcion apunta a un nodo inexistente: "${id}"`)
      continue
    }
    for (const option of node.options) {
      if (option.next !== null) {
        queue.push(option.next)
      }
    }
  }
  return reachable
}

/**
 * @function defineDialog
 * @description Identidad con validacion DEV-only del grafo: start existe,
 *   toda opcion apunta a un nodo real, ningun nodo queda inalcanzable y
 *   ningun nodo se queda sin opciones (callejon sin salida).
 */
export function defineDialog(dialog: NpcDialog): NpcDialog {
  if (!import.meta.env.DEV) {
    return dialog
  }
  const issues: string[] = []
  const reachable = walkReachable(dialog, issues)
  for (const [id, node] of Object.entries(dialog.nodes)) {
    if (node.options.length === 0) {
      issues.push(`nodo sin opciones (callejon): "${id}"`)
    }
    if (!reachable.has(id)) {
      issues.push(`nodo inalcanzable desde "${dialog.start}": "${id}"`)
    }
  }
  if (issues.length > 0) {
    console.error(`[journey] dialogo "${dialog.name.es}" invalido:`, issues)
  }
  return dialog
}

export interface NpcTalkOpts {
  id: string
  npc: NpcHandle
  dialog: NpcDialog
  openDialog: OpenDialog
  radius?: number
  /** Gesto previo a abrir el panel (ej. el salto del karateka). */
  onGreet?(): void
}

export interface NpcTalk {
  interactable: Interactable
  /** Sincroniza el interactable con la posicion del NPC (caminantes). */
  update(): void
}

/**
 * @function npcTalk
 * @description Interactable conversable de un NPC: prompt "Hablar con X",
 *   burbuja de chatter anclada a su cabeza y, con E, pausa + saludo/mirada
 *   al jugador + panel de dialogo (endTalk al cerrar).
 */
export function npcTalk(opts: NpcTalkOpts): NpcTalk {
  const { npc, dialog } = opts
  const interactable: Interactable = {
    id: opts.id,
    x: npc.group.position.x,
    z: npc.group.position.z,
    radius: opts.radius ?? 2.1,
    label: {
      es: `Hablar con ${dialog.name.es}`,
      en: `Talk to ${dialog.name.en}`,
    },
    bubble: {
      lines: dialog.chatter,
      anchor: () => ({
        x: npc.group.position.x,
        y: npc.group.position.y + 1.85,
        z: npc.group.position.z,
      }),
    },
    onActivate: (player) => {
      opts.onGreet?.()
      npc.talk(player)
      opts.openDialog(dialog, () => npc.endTalk())
    },
  }
  return {
    interactable,
    update: () => {
      interactable.x = npc.group.position.x
      interactable.z = npc.group.position.z
    },
  }
}
