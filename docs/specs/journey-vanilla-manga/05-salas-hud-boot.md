# 05 — Salas, HUD DOM y boot/integracion Astro

> Port del contenido real de las 3 salas (+ pasado) a factories vanilla
> manga-ink, el HUD como DOM puro y el arranque sin React.

## Factories de sala (engine/rooms/*.ts)

Contrato (ver [02-motor-y-carga.md](02-motor-y-carga.md)): cada archivo
exporta `default: RoomFactory`. El `RoomCtx` que reciben:

```ts
interface RoomCtx {
  def: RoomDef                 // datos reales del CV (lib/rooms.ts)
  room: RoomLayout             // caja de la sala (lib/layout.ts)
  theme: RoomTheme             // paleta manga-ink (engine/themes.ts)
  locale: Locale
  state: EngineState           // para registrar interactables
  actions: {                   // puente al HUD/estado (sin imports circulares)
    openFicha(kind): void; openContact(): void
    enterPast(spawn): void
  }
}
```

Se PORTA 1:1 el contenido narrativo actual (nada se pierde), cambiando
materiales a toon + outline y `<Text>` troika por `label()`:

| Sala | Contenido portado | Micro-interaccion |
|------|-------------------|-------------------|
| aula.ts | 4 pupitres con monitores "ping servidor", pizarra cliente-servidor, ficha retos (pizarra) + aprendizajes (cuaderno), portal al pasado, 3 NPCs estudiantes | tablero proyectos BLOQUEADO→LISTO (rojo→verde) |
| corpoelec.ts | transformador + bujes, cajas inventario + label, monitor tabla OFFLINE, ventana torres (canvas ink), casco, guiño YARACUY·CARABOBO·LARA, fichas, portal, 2 NPCs con casco | tablero de control rojo→verde + luz |
| cima.ts | mesa reunion + 6 sillas, paneles observability/vibe-coding, grafo microservicios (canvas), escritorio ultrawide code-base→forks, puerta PROXIMAMENTE, CTA contacto (holograma), fichas, portal, 3 NPCs | orquestacion CL↔MX (pulso entre nodos) |
| past.ts | mini-sala sepia por indice: clutter especifico (papeles, archivador, planillas), cartel ANTES·{año}, portal de salida | — |

Los props compartidos (`desk`, `monitor`, `screenPanel`, `fichaProp`,
`pastPortal`, `paperStack`) viven como helpers en `engine/toon.ts` o un
`engine/rooms/props.ts` si superan ~80 lineas (decidir al implementar;
preferir 1 archivo menos).

Notas de port:

- `FichaProp` pulsante: la animacion de emissive pasa al `update(t)` del
  RoomBuild (el factory registra sus animables en una lista local).
- Los interactables se registran en `state.interactables` al montar y el
  `dispose()` los des-registra (hoy lo hacia useEffect).
- El pasillo NO es factory: su shell + puerta + año son parte de world.ts.

## engine/hud.ts — HUD DOM (port del Hud.tsx)

`createHud({ locale, actions })` construye el arbol DOM (un `<style>` con
clases + nodos) dentro del container y expone metodos imperativos:

```ts
interface Hud {
  setZoneLabel(text: string): void
  showPrompt(label: string | null): void          // con kbd E / boton tactil
  openFicha(def: RoomDef, kind: FichaKind): void  // panel DOM accesible
  openContact(): void; openTeleport(): void; closeAll(): void
  fade(on: boolean): Promise<void>                // esclusa/teleport/portal
  setPastMode(on: boolean): void                  // sepia+grano CSS
  setCameraMode(mode): void; setAudio(on): void; setTour(on): void
  showLoader(on: boolean): void                   // "Cargando el mundo 3D…"
  mountTouchControls(): { joystick; actionBtn }   // solo pointer coarse
  dispose(): void
}
```

- Se portan TODOS los `HUD_STRINGS` es/en actuales + los overlays
  (vineta, screentone nuevo, grano/glitch del pasado, fade).
- Panel de contacto: mismos links (email/LinkedIn/GitHub de
  `@portfolio/content` profile).
- Menu teletransporte: mismas entradas "Sala N de 3 — titulo (periodo)";
  al elegir: fade + world.teleport(index).
- Botones top-right: audio ON/OFF, camara (3a/POV), Ver CV 2D. Bottom:
  mapa (M), tour (solo reduced o `?tour`), hints de controles por modo.
- Estetica: mismos tokens DS (`var(--color-*)`) + borde estilo viñeta
  (border 2px tinta + esquina irregular via clip-path sutil) para que el
  HUD acompañe el manga-ink sin perder legibilidad.
- Accesibilidad: paneles `aria-label`, botones `<button>`, Escape cierra
  (igual que hoy).

## lib/boot.ts + paginas Astro

`boot.ts` es el entry LIVIANO (sin three, sin engine):

```ts
export async function initJourney(): Promise<void> {
  const root = document.getElementById('journey-root')
  const locale = root?.dataset.locale === 'en' ? 'en' : 'es'
  const tier = detectTier()            // port del probe de Journey3D.tsx
  if (tier === 'static') return       // fallback 2D queda visible (AC-2)
  // overlay fijo + loader con el TEXTO EXACTO del contrato E2E
  // "Cargando el mundo 3D…" / "Loading the 3D world…"
  const { startJourney } = await import('../engine/app')   // chunk 3D
  // ocultar #cv-fallback, overflow hidden, montar; onExit -> dispose total
  // + boton "Explorar en 3D" para re-entrar (recrea el engine)
}
```

Paginas (`index.astro` + `en/index.astro`): se reemplaza la isla React por

```html
<div id="journey-root" data-locale="es"></div>
<script>
  import { initJourney } from '../lib/boot'
  initJourney()
</script>
```

(Astro bundlea el `<script>` como modulo; el `import('../engine/app')`
dentro de boot crea el chunk 3D separado — AC-12. En `en/` cambia el path
relativo y `data-locale`.)

## Audio

`components/three/ambient-audio.ts` se MUEVE a `engine/audio.ts` sin
cambios de logica (ya es vanilla WebAudio, opt-in). El zone manager llama
`ambientAudio.setRoom(roomId)` al cambiar de sala si `audioOn`.

## astro.config.ts y deps

- Quitar `react()` de integrations y el bloque `optimizeDeps.include` de
  react (el resto del config queda igual: yaml, tailwind, sitemap, env).
- `package.json` de journey — remover: `@astrojs/react`, `react`,
  `react-dom`, `@react-three/fiber`, `@react-three/drei`,
  `troika-three-text`, `zustand`, `@types/react`, `@types/react-dom`,
  `vitest`, `@vitest/coverage-v8`, `happy-dom` y los scripts
  `test`/`test:coverage`. Mantener: `three`, `@types/three`, astro,
  sitemap, tailwind, packages workspace, js-yaml/@modyfi (config),
  `vite-node` (scripts pre/postbuild), typescript.
- Borrar: `src/components/` completo, `src/lib/store.ts`,
  `src/types/troika-three-text.d.ts`, `tests/`, `vitest.config.ts`,
  `public/fonts/space-grotesk-latin-400-normal.woff` (era solo de troika;
  verificar con `rg` que nadie mas lo referencia antes de borrar).
