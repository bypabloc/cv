# 03 — Direccion de arte: manga-ink de trazo marcado

> Como se materializa la decision 5 del usuario: "anime/ilustrada japonesa,
> estilo comic de trazos como dibujo a mano, personajes detallados sin
> realismo". Sabor elegido: MANGA-INK (contornos negros gruesos, colores
> planos de alto contraste, texturas con trazo irregular).

## Los 4 ingredientes (de la guia, adaptados a ink)

1. **Cel shading**: `MeshToonMaterial` + gradient map de 3 escalones de
   ALTO contraste (sombra dura tipo tinta, no pastel).
2. **Contornos**: inverted hull (malla duplicada, escala ~1.04, material
   `MeshBasicMaterial` negro `side: BackSide`) en personajes y props clave.
   Los muros NO llevan hull (estamos dentro de la caja): sus lineas de
   tinta van DIBUJADAS en la textura canvas.
3. **Texturas "a mano"**: canvas procedural con trazos irregulares
   (lineas wobbly, hatching en esquinas, zocalo de trazo grueso) — cero
   archivos, cero red, determinista (LCG ya existente).
4. **Composicion 2D**: overlay DOM de screentone (puntitos) + vineta +
   grano de papel — CSS puro, cero post-processing WebGL.

## engine/toon.ts — API

```ts
makeToonGradient(stops: string[]): CanvasTexture
  // canvas Nx1 px, NearestFilter (escalones duros)

toonMat(color: ColorRepresentation, opts?: {
  map?: Texture; emissive?: ColorRepresentation; emissiveIntensity?: number
}): MeshToonMaterial
  // POOL global cacheado por key (color+map+emissive). userData.shared=true
  // -> disposeDeep NUNCA los libera. Compartir material = menos draw-call
  // state changes y shaders compilados 1 sola vez.

addOutline(mesh: Mesh, thickness = 1.04): Mesh
outlineGroup(root: Object3D, thickness?): void
  // inverted hull: reusa la MISMA geometry (scale del mesh clonado),
  // material negro BackSide COMPARTIDO. Marcar hull.userData.outline=true.

makeCanvasTexture(size, draw): CanvasTexture   // port de textures.ts
inkWallTexture(theme): CanvasTexture           // ver receta abajo
inkFloorTexture(theme): CanvasTexture
label(text, opts?: { size?; color?; ink? }): Mesh
  // plane con canvas transparente: strokeText negro grueso (lineWidth ~8)
  // + fillText color -> lettering manga. Reemplaza a troika <Text>.
screenPanel(opts: { lines; title?; theme; width; height }): Mesh
  // port del ScreenPanel: marco de viñeta manga (borde de tinta irregular,
  // esquinas con hatching) + texto monospace. MeshBasicMaterial (emisivo
  // plano, no depende de luz).
disposeDeep(root: Object3D): void
  // geometry.dispose + material.dispose + texturas, SALVO userData.shared
```

## Receta de las texturas ink (canvas 512, deterministas)

- `inkWallTexture`: base plana del theme → 2-3 lineas horizontales wobbly
  (trazo a mano: segmentos con jitter Y ±2px, lineWidth 3-5, alpha 0.5) →
  hatching diagonal corto en las 2 esquinas superiores (6-10 trazos) →
  zocalo inferior: banda de trazo grueso irregular → screentone sutil
  (puntos cada 8 px, alpha 0.05). AO fake del actual se conserva pero mas
  sutil (el look plano manda).
- `inkFloorTexture`: base plana → tablones/baldosas con lineas wobbly de
  tinta (no rectas perfectas) → algunos trazos de "desgaste" sueltos.
- `windowTexture` (corpoelec): se conserva la silueta de torres pero con
  lineWidth mayor y cielo en 2 bandas planas (sin gradiente suave).

## engine/themes.ts

```ts
interface RoomTheme {
  wall: string; floor: string; ink: string      // colores planos
  accent: string; lightColor: string
  fog: string; sky: string                      // por sala (guia §3)
  gradient: [string, string, string]            // escalones del toon
  screenBg: string; screenFg: string
}
export const THEMES: Record<RoomId | 'corridor' | 'past', RoomTheme>
```

Paletas (evolucion de `palettes.ts`, subiendo contraste y saturacion):

| Zona | Identidad manga-ink |
|------|---------------------|
| aula | papel calido + madera clara, tinta sepia-negra, acento verde pizarra `#7fb069` |
| corpoelec | grises industriales frios + acento naranja `#e2572b` + amarillo seguridad `#f2b705`; hatching mas denso (rubro duro) |
| cima | azul Destacame `#0052cc` sobre casi-negro, tinta azul-negra, brillos planos cian |
| corridor | neutro oscuro desaturado, año pintado en el piso con `label()` |
| past | sepia (el filtro CSS actual se conserva) + trazos mas sucios |

`scene.background` y `scene.fog` se actualizan al cambiar de zona con el
theme correspondiente (lerp de color en ~400 ms para no "saltar").

## Overlays DOM (composicion 2D)

- **Screentone**: div fijo con `background-image: radial-gradient(circle,
  rgba(0,0,0,0.35) 1px, transparent 1px); background-size: 4px 4px;
  opacity: 0.06; mix-blend-mode: multiply` — SIEMPRE activo (firma manga).
- **Vineta**: se conserva la actual (radial-gradient CSS).
- **Pasado**: se conservan sepia filter + grano + glitch actuales (CSS).
- **Fade**: div negro-tinta `#0b0b10` con transition de opacity 300-400 ms,
  controlado por world/hud (esclusa, teleport, portal, rebuild).

## Anti-patrones de estilo (NO hacer)

| Anti-patron | Por que |
|-------------|---------|
| MeshStandardMaterial "porque ya estaba" | Rompe el look plano y paga PBR |
| OutlinePass / post-processing de bordes | Caro; inverted hull + texturas cubren el look en desktop Y movil |
| Gradientes suaves en canvas (createLinearGradient grandes) | Mata el look de tinta; usar bandas planas |
| Hull en muros interiores | Se ve del reves; las lineas de muro van en la textura |
| Texturas > 512 sin comentario justificando | Presupuesto (AC-10) |
