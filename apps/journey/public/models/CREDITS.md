# Créditos de assets 3D (CC0)

> Ver `docs/specs/journey-spiderverse-style/03-sourcing-assets.md` para el
> detalle completo de sourcing. Ninguna licencia exige atribución — esta
> tabla es buena práctica, no obligación legal.

| Archivo | Pack | Autor | Licencia | Fuente |
| --- | --- | --- | --- | --- |
| `characters/*.glb` (23 cuerpos + `base`) | Mixamo Characters (T-pose) + Mixamo Animations | Adobe Mixamo | Free / uso comercial sin atribución (solo prohíbe redistribuir el asset standalone) | [mixamo.com](https://www.mixamo.com/#/?type=Character) |
| `furniture/desk.glb` | Furniture Kit — "desk" | Kenney | CC0 (Kenney license) | [kenney.nl](https://kenney.nl/assets/furniture-kit) |
| `furniture/chairDesk.glb` | Furniture Kit — "chairDesk" | Kenney | CC0 (Kenney license) | [kenney.nl](https://kenney.nl/assets/furniture-kit) |
| `furniture/space/table.glb` | Space Station Kit — "table" | Kenney | CC0 (Kenney license) | [kenney.nl](https://kenney.nl/assets/space-station-kit) |
| `furniture/space/chair.glb` | Space Station Kit — "chair" | Kenney | CC0 (Kenney license) | [kenney.nl](https://kenney.nl/assets/space-station-kit) |
| `furniture/space/computer.glb` | Space Station Kit — "computer" | Kenney | CC0 (Kenney license) | [kenney.nl](https://kenney.nl/assets/space-station-kit) |

## Notas técnicas

- Comprimidos con `@gltf-transform/cli draco` (Draco `KHR_draco_mesh_compression`)
  antes de vendorizar; decodificados en runtime con `DRACOLoader` (worker
  `blob:` habilitado en la CSP via `allowBlobWorkers`).
- El **Furniture Kit** (`desk`/`chairDesk`) trae colores planos sin textura.
- El **Space Station Kit** (`space/*`) trae una textura atlas `colormap.png`
  (PNG ~7 KB); `gltf-transform draco` la **embebe** en el `.glb` (self-contained,
  sin carpeta `Textures/` externa). Se decodifica nativamente en el browser —
  sin KTX2.
- Los materiales PBR de los packs se convierten a `MeshToonMaterial` en runtime
  (`character.ts` / `rooms/furniture.ts`). El aula tinta su mobiliario a madera
  (color plano); el pack sci-fi **preserva su textura** (`toonMat('#ffffff',
  { map })`) y solo recibe el toon shading.
- **Personajes (Mixamo, 2026-07-08).** 23 cuerpos con CARA PINTADA (textura),
  rig `mixamorig` nativo — las 83 animaciones (tambien de Mixamo) se aplican
  SIN retarget. Elenco casual/oficina (hombres + mujeres, ~50/50) + roles
  tematicos (salud/scrubs, obrero, jefe-traje, ejecutiva, profesora).
  `base` = el cuerpo del jugador Pablo (`david`) + sus facetas del pasado del
  aula. El pipeline vive en `apps/journey/scripts/blender/`:
  `build-character.py` mergea cuerpo + clips en un GLB (normaliza los huesos
  `mixamorig##:Hips` -> `mixamorig_Hips` para que Three.js resuelva los tracks;
  ancla el root motion in-place; deja solo la textura baseColor) y
  `compress-glb.sh` lo comprime (resize 512 + resample + webp + draco).
  El look es cel-shading "Arcane": `CHARACTER_GRADIENT` (bandas de sombra
  duras) + rim light fresnel (`toon.ts::applyRim`) sobre la textura real.

## Look visual (2026-07-07)

El post-procesado tipo cómic (halftone Ben-Day + aberración cromática) y los
contornos de tinta inverted-hull se **eliminaron** (pedido del dueño): el
render es 3D toon limpio, directo, con MSAA nativo. `postfx.ts` ya no existe;
`toon.ts::outlineGroup` es no-op.
