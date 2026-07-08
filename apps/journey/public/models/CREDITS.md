# Créditos de assets 3D (CC0)

> Ver `docs/specs/journey-spiderverse-style/03-sourcing-assets.md` para el
> detalle completo de sourcing. Ninguna licencia exige atribución — esta
> tabla es buena práctica, no obligación legal.

| Archivo | Pack | Autor | Licencia | Fuente |
| --- | --- | --- | --- | --- |
| `characters/base.glb` | Ultimate Modular Men Pack — "Hoodie Character" | Quaternius | CC0 1.0 Universal | [quaternius.com](https://quaternius.com/packs/ultimatemodularcharacters.html) / [poly.pizza](https://poly.pizza/bundle/Ultimate-Modular-Men-Pack-ZiH8muWqwQ) |
| `characters/male-casual.glb` | Ultimate Modular Men Pack | Quaternius | CC0 1.0 Universal | [poly.pizza](https://poly.pizza/bundle/Ultimate-Modular-Men-Pack-ZiH8muWqwQ) |
| `characters/male-suit.glb` | Ultimate Modular Men Pack | Quaternius | CC0 1.0 Universal | [poly.pizza](https://poly.pizza/bundle/Ultimate-Modular-Men-Pack-ZiH8muWqwQ) |
| `characters/male-worker.glb` | Ultimate Modular Men Pack | Quaternius | CC0 1.0 Universal | [poly.pizza](https://poly.pizza/bundle/Ultimate-Modular-Men-Pack-ZiH8muWqwQ) |
| `characters/female-casual.glb` | Ultimate Modular Women Pack | Quaternius | CC0 1.0 Universal | [poly.pizza](https://poly.pizza/bundle/Ultimate-Modular-Women-Pack-aCBDXDdTNN) |
| `characters/female-office.glb` | Ultimate Modular Women Pack | Quaternius | CC0 1.0 Universal | [poly.pizza](https://poly.pizza/bundle/Ultimate-Modular-Women-Pack-aCBDXDdTNN) |
| `characters/female-worker.glb` | Ultimate Modular Women Pack | Quaternius | CC0 1.0 Universal | [poly.pizza](https://poly.pizza/bundle/Ultimate-Modular-Women-Pack-aCBDXDdTNN) |
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
- Los 6 cuerpos de NPC (3 masculinos + 3 femeninos: casual / oficina-traje /
  obrero) se **curaron a mano** de los packs Ultimate Modular Men/Women — que
  incluyen tambien personajes disfrazados (bruja, rey, punk); esos se
  descartaron por no encajar en oficinas/universidad. Todos comparten el
  esqueleto y los clips `CharacterArmature|*`, asi que el mapping de poses de
  `character.ts` funciona sin cambios. Se reparten ~50/50 hombre/mujer entre
  los NPCs del recorrido.

## Look visual (2026-07-07)

El post-procesado tipo cómic (halftone Ben-Day + aberración cromática) y los
contornos de tinta inverted-hull se **eliminaron** (pedido del dueño): el
render es 3D toon limpio, directo, con MSAA nativo. `postfx.ts` ya no existe;
`toon.ts::outlineGroup` es no-op.
