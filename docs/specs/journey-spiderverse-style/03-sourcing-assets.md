# 3. Sourcing de assets CC0

Verificado con licencia confirmada (fetch/search real, sin URLs
inventadas):

| Necesidad | Pack | Licencia | Formato | Nota |
|---|---|---|---|---|
| Mobiliario `aula` | [Kenney "Furniture Kit"](https://kenney.nl/assets/furniture-kit) | CC0, sin atribución | GLTF (via export/poly.pizza) | 140 assets: escritorios, sillas, estantes, sofás |
| Personaje jugador + NPCs (todas las salas) | [Quaternius "Ultimate Modular Men Pack"](https://quaternius.com/packs/ultimatemodularcharacters.html) / "Ultimate Modular Women Pack" | CC0 | GLTF/FBX/OBJ/Blend | 11 (hombres) + 10 (mujeres) personajes modulares, 4 partes intercambiables, 24 animaciones incluidas por pack |
| Vegetación/naturaleza (si hace falta ambientación) | Quaternius (packs "Nature"/"Stylized Nature") | CC0 | GLTF | Confirmado 100% CC0 en todo el catálogo de Quaternius |
| Oficina moderna (`destacame`) | Kenney "Furniture Kit" + Quaternius (complementario) | CC0 | GLTF | Mismo pack base que aula, reutilizado con otra disposición/paleta |
| Props sci-fi (`futuro`) | **Pendiente de confirmar en T4b** | — | — | Candidatos vistos sin licencia CC0 100% verificada aún (ITHappy "Sci-Fi Rooms", itch.io tag sci-fi+low-poly) — ver plan B en 05 |
| Agregador / mirror GLTF | [poly.pizza](https://poly.pizza/) | Variable por modelo (filtrar CC0 explícito por ficha) | GLTF nativo | 10,500+ modelos, mirror de Kenney/Quaternius entre otros catálogos |
| Animación/rig complementario (si el pack de Quaternius no cubre alguna pose) | [Mixamo](https://www.mixamo.com/) (Adobe) | Gratis, uso comercial permitido, sin atribución requerida. Restricción: no redistribuir standalone (se embebe en el proyecto, cumple) | FBX (retarget a la malla propia via auto-rigger) | Confirmado via búsqueda de los términos oficiales de Adobe |

Ninguna licencia exige atribución ni prohíbe uso comercial — compatibles
con un portfolio profesional público. Se documentan igual en
`apps/journey/public/models/CREDITS.md` (AC-8) como buena práctica, no
por obligación legal.

## Estilo visual: geometría CC0 + shader propio, no "packs painterly"

Los packs listados arriba traen geometría/rig/animación de calidad, pero
**colores planos simples** (no vienen "estilo Spider-Verse" de fábrica).
El look final sale de aplicarles el pipeline de postprocesado propio
(halftone + outline + aberración cromática, ver
[02-arquitectura-tecnica.md](02-arquitectura-tecnica.md)) — es la
combinación geometría real + shader la que produce el resultado, no algo
que se descargue ya hecho.

## Referencia técnica del shader

[neftale99/halftone-shader](https://github.com/neftale99/halftone-shader)
— WebGL/GLSL (proyecto Vite), shader de Ben-Day dots inspirado
específicamente en el estilo de Spider-Verse. Punto de partida técnico
para adaptar como `ShaderPass` de Three.js — no es una librería a
instalar, es referencia de implementación.
