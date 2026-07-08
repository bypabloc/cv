# Créditos de assets 3D (CC0)

> Ver `docs/specs/journey-spiderverse-style/03-sourcing-assets.md` para el
> detalle completo de sourcing. Ninguna licencia exige atribución — esta
> tabla es buena práctica, no obligación legal.

| Archivo | Pack | Autor | Licencia | Fuente |
| --- | --- | --- | --- | --- |
| `characters/base.glb` | Ultimate Modular Men Pack — "Hoodie Character" | Quaternius | CC0 1.0 Universal | [quaternius.com](https://quaternius.com/packs/ultimatemodularcharacters.html) / [poly.pizza](https://poly.pizza/bundle/Ultimate-Modular-Men-Pack-ZiH8muWqwQ) |
| `furniture/desk.glb` | Furniture Kit — "desk" | Kenney | CC0 (Kenney license) | [kenney.nl](https://kenney.nl/assets/furniture-kit) |
| `furniture/chairDesk.glb` | Furniture Kit — "chairDesk" | Kenney | CC0 (Kenney license) | [kenney.nl](https://kenney.nl/assets/furniture-kit) |

Comprimidos con `@gltf-transform/cli` (Draco, `--method edgebreaker`) antes
de vendorizar. Sin KTX2 (los materiales de ambos packs son colores planos,
sin texturas de imagen). Los materiales se convierten a `MeshToonMaterial`
en runtime (`character.ts` / `rooms/furniture.ts`).

Pendiente de completar cuando se migren las salas restantes (T4b-T4c):
mobiliario de oficina de destacame y el pack de `futuro`.
