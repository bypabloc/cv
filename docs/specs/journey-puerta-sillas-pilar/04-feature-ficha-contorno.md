# Feature C — Contorno de tinta de los cuadros (`wallArt`) alineado al marco

> AC-10. Ver contexto general en
> [01-contexto-y-decision.md](01-contexto-y-decision.md).

## Diseño

`wallArt` (props.ts:1137-1192) arma el marco de TODOS los cuadros de la
sala en un solo mesh fusionado:

```ts
// ANTES (props.ts:1146-1163)
marcoGroup.add(
  mergedBoxes(
    opts.frames.map((frame) => {
      const [w, h] = frame.size ?? [1.1, 0.8]
      const rotY = frame.rotationY ?? 0
      return {
        w: w + 0.1, h: h + 0.1, d: 0.05,
        x: frame.position[0] - Math.sin(rotY) * 0.035,
        y: frame.position[1],
        z: frame.position[2] - Math.cos(rotY) * 0.035,
        rotY,
      }
    }),
    toonMat(trim),
  ),
)
```

El comentario de `outlinedMergedBoxes` (`toon.ts:690-693`) ya documenta
exactamente este bug: el contorno genérico de la sala (`outlineGroup`,
`toon.ts:279-300`) clona el mesh y lo escala `1.03` alrededor de su
origen LOCAL (`addOutline`, `toon.ts:267-273`). Como las posiciones de
cada marco están horneadas en la geometría con coordenadas absolutas de
sala (ej. `z ≈ 13.12` para un cuadro en el fondo), escalar por `1.03`
alrededor de `(0,0,0)` desplaza ese vértice `~0.03 × 13.12 ≈ 0.39 m` en Z
— la "sombra"/borde que se sale del marco en la imagen reportada.

### Fix

Reemplazar `mergedBoxes` por `outlinedMergedBoxes` (mismo helper que ya
usan `officeLayout`/escritorios/sillas, que SÍ calcula el contorno
correcto: un segundo merge con cada caja inflada en absoluto, en vez de
escalar el conjunto ya fusionado):

```ts
// DESPUES
marcoGroup.add(
  outlinedMergedBoxes(
    opts.frames.map((frame) => {
      const [w, h] = frame.size ?? [1.1, 0.8]
      const rotY = frame.rotationY ?? 0
      return {
        w: w + 0.1, h: h + 0.1, d: 0.05,
        x: frame.position[0] - Math.sin(rotY) * 0.035,
        y: frame.position[1],
        z: frame.position[2] - Math.cos(rotY) * 0.035,
        rotY,
      }
    }),
    toonMat(trim),
  ),
)
```

`outlinedMergedBoxes` ya devuelve un `Group` (no un `Mesh`) y ya marca su
mesh de relleno con `userData.noOutline = true`, así que el pase
genérico `outlineGroup` de la sala lo salta automáticamente (sin doble
contorno) — mismo patrón que usan `officeLayout`/`chair`/`desk` hoy.
`marcoGroup.add(...)` acepta un `Group` igual que aceptaba el `Mesh`
anterior (ambos son `Object3D`), así que no hace falta tocar el resto de
`wallArt` ni sus llamadores.

### Costo

`outlinedMergedBoxes` cuesta 2 draw calls totales para TODOS los marcos
de la sala fusionados (relleno + contorno), igual que hoy el `mergedBoxes`
solo costaba 1 — se suma exactamente 1 draw call por sala (el contorno
correcto). Las salas con `wallArt` tienen holgura de sobra en su
presupuesto de <100 draw calls (medido en el cierre C15 del plan
`journey-salas-estandar`: 92-99 draw calls con margen).

## Verificación de la feature

- Typecheck (`astro check`).
- Smoke visual: revisar al menos 2 salas con `wallArt` (ej. `aula`,
  `cofasa`) desde varios ángulos y confirmar que el contorno de tinta de
  cada cuadro queda pegado a su marco, sin ninguna franja/sombra
  desplazada.
- Medir draw calls antes/después con `window.__journeyDebug.info.render.calls`
  (patrón `journey-rooms.md`) para confirmar que sigue <100 por sala.
