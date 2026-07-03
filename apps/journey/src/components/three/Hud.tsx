/**
 * @component Hud
 * @description Overlay DOM sobre el canvas: indicador de sala, prompt de
 *   interaccion, hints de controles, ficha de retos/aprendizajes (DOM real,
 *   accesible) y salida al CV 2D. Todo el texto es HTML — nunca pixeles
 *   dentro del WebGL (regla dura del plan).
 */
import type { CSSProperties } from 'react'
import type { Locale, RoomDef } from '../../lib/rooms'
import { useJourneyStore } from '../../lib/store'

interface HudProps {
  rooms: readonly RoomDef[]
  locale: Locale
  onExit: () => void
}

const HUD_STRINGS = {
  es: {
    exit: 'Ver CV 2D',
    controls: 'WASD / flechas — caminar · mouse — mirar · E — interactuar',
    clickToStart: 'Click para explorar',
    corridorTo: 'Rumbo a',
    roomOf: (n: number, total: number) => `Sala ${n} de ${total}`,
    interactKey: 'E',
    retos: 'Retos',
    aprendizajes: 'Aprendizajes',
    close: 'Cerrar (Esc)',
  },
  en: {
    exit: 'View 2D CV',
    controls: 'WASD / arrows — walk · mouse — look · E — interact',
    clickToStart: 'Click to explore',
    corridorTo: 'Heading to',
    roomOf: (n: number, total: number) => `Room ${n} of ${total}`,
    interactKey: 'E',
    retos: 'Challenges',
    aprendizajes: 'Learnings',
    close: 'Close (Esc)',
  },
} as const

const panelStyle: CSSProperties = {
  background:
    'color-mix(in srgb, var(--color-grey-95, #0a0a0a) 82%, transparent)',
  color: 'var(--color-grey-5, #f7f7f5)',
  border:
    '1px solid color-mix(in srgb, var(--color-grey-5, #f7f7f5) 14%, transparent)',
  borderRadius: 'var(--radius-md, 12px)',
  padding: '0.6rem 0.9rem',
  fontSize: '0.85rem',
  lineHeight: 1.45,
  pointerEvents: 'none',
  backdropFilter: 'blur(6px)',
}

export function Hud({ rooms, locale, onExit }: HudProps) {
  const zone = useJourneyStore((s) => s.zone)
  const activeId = useJourneyStore((s) => s.activeInteractableId)
  const interactables = useJourneyStore((s) => s.interactables)
  const ficha = useJourneyStore((s) => s.ficha)
  const closeFicha = useJourneyStore((s) => s.closeFicha)
  const isLocked = useJourneyStore((s) => s.isLocked)
  const t = HUD_STRINGS[locale]

  const zoneLabel = (() => {
    if (zone.kind === 'room') {
      const room = rooms[zone.index]
      if (!room) {
        return ''
      }
      const texts = room.texts[locale]
      return `${t.roomOf(zone.index + 1, rooms.length)} — ${texts.title} (${texts.period})`
    }
    const target = rooms[zone.index + 1]
    return target ? `${t.corridorTo} ${target.texts[locale].title}` : ''
  })()

  const prompt = activeId ? interactables[activeId]?.label[locale] : null
  const fichaRoom = ficha ? rooms[ficha.roomIndex] : null

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        pointerEvents: 'none',
        fontFamily: 'var(--font-sans, sans-serif)',
        zIndex: 10,
      }}
    >
      {/* indicador de sala */}
      <div style={{ ...panelStyle, position: 'absolute', top: 12, left: 12 }}>
        {zoneLabel}
      </div>

      {/* salida al CV 2D */}
      <button
        type="button"
        onClick={onExit}
        style={{
          ...panelStyle,
          position: 'absolute',
          top: 12,
          right: 12,
          pointerEvents: 'auto',
          cursor: 'pointer',
        }}
      >
        {t.exit}
      </button>

      {/* crosshair */}
      {isLocked && !ficha && (
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            width: 5,
            height: 5,
            marginLeft: -2.5,
            marginTop: -2.5,
            borderRadius: '50%',
            background:
              'color-mix(in srgb, var(--color-grey-5, #f7f7f5) 85%, transparent)',
          }}
        />
      )}

      {/* prompt de interaccion */}
      {isLocked && !ficha && prompt && (
        <div
          style={{
            ...panelStyle,
            position: 'absolute',
            bottom: '22%',
            left: '50%',
            transform: 'translateX(-50%)',
          }}
        >
          <kbd
            style={{
              border: '1px solid currentColor',
              borderRadius: 4,
              padding: '0 0.35em',
              marginRight: '0.5em',
            }}
          >
            {t.interactKey}
          </kbd>
          {prompt}
        </div>
      )}

      {/* click para tomar el control */}
      {!isLocked && !ficha && (
        <div
          style={{
            ...panelStyle,
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            fontSize: '1rem',
            textAlign: 'center',
          }}
        >
          {t.clickToStart}
          <div style={{ fontSize: '0.75rem', opacity: 0.75, marginTop: 4 }}>
            {t.controls}
          </div>
        </div>
      )}

      {/* hints de controles */}
      {isLocked && !ficha && (
        <div
          style={{
            ...panelStyle,
            position: 'absolute',
            bottom: 12,
            left: 12,
            fontSize: '0.72rem',
            opacity: 0.85,
          }}
        >
          {t.controls}
        </div>
      )}

      {/* ficha retos / aprendizajes */}
      {ficha && fichaRoom && (
        <aside
          aria-label={t[ficha.kind]}
          style={{
            ...panelStyle,
            position: 'absolute',
            top: '50%',
            right: 24,
            transform: 'translateY(-50%)',
            width: 'min(420px, calc(100vw - 48px))',
            maxHeight: '76vh',
            overflowY: 'auto',
            pointerEvents: 'auto',
            padding: '1.1rem 1.25rem',
          }}
        >
          <header style={{ marginBottom: '0.6rem' }}>
            <p style={{ margin: 0, opacity: 0.7, fontSize: '0.72rem' }}>
              {fichaRoom.texts[locale].title} · {fichaRoom.texts[locale].period}
            </p>
            <h2 style={{ margin: '0.15rem 0 0', fontSize: '1.05rem' }}>
              {t[ficha.kind]}
            </h2>
          </header>
          <ul style={{ margin: 0, paddingLeft: '1.1rem' }}>
            {fichaRoom.texts[locale][ficha.kind].map((item) => (
              <li key={item} style={{ marginBottom: '0.45rem' }}>
                {item}
              </li>
            ))}
          </ul>
          <button
            type="button"
            onClick={closeFicha}
            style={{
              marginTop: '0.8rem',
              background: 'transparent',
              color: 'inherit',
              border: '1px solid currentColor',
              borderRadius: 6,
              padding: '0.3rem 0.7rem',
              cursor: 'pointer',
            }}
          >
            {t.close}
          </button>
        </aside>
      )}
    </div>
  )
}
