**08**

# Lo que midieron otros

[← Índice](README.md)

---

Estas son pruebas publicadas por terceros, cada una con su fuente. Las cifras son suyas **[publicado]**.

### El benchmark más completo: Bicameral AI

[Bicameral AI](https://github.com/Bicameral-AI/claude-code-mode-benchmark) publicó prompts, datos y verificador: seis tareas, cuatro modelos, dos corridas por combinación, 96 corridas en 2.1.326 y otras 96 en 2.1.325, todas a esfuerzo `medium`.

| Ahorro en tokens procesados (2.1.326) | Opus 5.5 | Sonnet 5.5 | Haiku 5.5 | Fable 5.2 |
| :-- | --: | --: | --: | --: |
| Agregar 120 registros vía MCP | 77 % | 67 % | 62 % | 71 % |
| Leer y clasificar 120 registros vía MCP | 68 % | 49 % | 40 % | 61 % |
| Buscar y modificar archivos locales | 37 % | 54 % | **−9 %** | 15 % |
| Responder una pregunta sobre un archivo | 29 % | 30 % | 29 % | 29 % |

- En la agregación MCP, el contexto añadido cayó 84–94 % y las 16 corridas respondieron bien.
- En las tareas de archivos, el contexto añadido **creció** con Code Mode en 14 de 16 comparaciones.
- El −9 % de Haiku vino sobre todo de una corrida que buscó en el directorio equivocado.
- Sus propias advertencias: los datos eran sintéticos y con patrones que favorecían el filtrado, y recomiendan no citar un porcentaje único.

### Pruebas sobre repositorios reales

| Prueba | Sin → con Code Mode | Qué se observó |
| :-- | :-- | :-- |
| [wmedia](https://wmedia.es/es/tips/claude-code-code-mode-activar): agregar pedidos de 40 JSON, Opus 5.5 | 150.364 → 94.659 tokens de entrada (caché incluida); **15 → 37 s** | Misma respuesta y cuatro requests en ambos casos; en modo normal Claude ya usaba un script de Python |
| [Flavio Copes](https://flaviocopes.com/claude-code-code-mode/): enlaces rotos y verificaciones en un proyecto Astro | Enlaces 35 → 15 s; verificaciones 17 → 14 s | El modo normal ya paralelizaba los comandos independientes |
| [Issue #111033](https://github.com/anthropics/claude-code/issues/111033): enlaces rotos en 432 Markdown, Opus 5.5 en WSL2 | **40 → 96 s**; US$0,58 → US$0,62 | Mismo resultado; Claude pasó de un escaneo en Python a 742 lecturas |
| [Issue #111178](https://github.com/anthropics/claude-code/issues/111178): editar 100 archivos y 10 preguntas web | Edición 17,6 → 48,7 s, US$0,341 → US$0,285; web 34,0 → 27,7 s, US$0,498 → US$0,303 | Tres corridas por modo; delegar en un subagente orquestador no ganó nada |
| [bestagent.dev](https://bestagent.dev/claude-code-code-mode-cost-tested-2026/): implementar una opción de CLI con pruebas, Opus 5.5 | 10–13 → 6–8 requests; 71–97 → 57–63 s; US$0,43–0,47 → US$0,34–0,36 | Pruebas verdes en todas; editar 20 archivos costó y tardó lo mismo |
| [claude-code-lab](https://www.claude-code-lab.com/blog/claude-code-code-mode): 72 corridas, 3 modelos | Costo estimado más bajo en las 12 condiciones (~41–44 %) | El mejor caso, 40 consultas MCP con Opus; enlaces rotos 12–32 % más lentos |

### Lo que dicen juntas

1. El ahorro fijo (~13 mil tokens por sesión) es consistente en todas.
2. El ahorro grande aparece con muchas llamadas MCP agregables.
3. En archivos locales, poco o nada, y a veces más lento.
4. Los filtros pueden esconder datos.
5. Nadie midió el efecto en los límites del plan.

`benchmarks` `comunidad` `comparación`
