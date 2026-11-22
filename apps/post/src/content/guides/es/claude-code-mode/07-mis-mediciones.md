**07**

# Mis mediciones

[← Índice](README.md)

---

### De dónde salen

Claude Code guarda cada sesión en un transcript JSONL con los mensajes, el uso de tokens de cada request y, en Code Mode, el código de cada bloque. Medí los transcripts de mis últimas sesiones con el modo encendido y los comparé con mis sesiones normales con Opus 5.5 del mismo período (del 12 al 22 de noviembre de 2026).

| Muestra | Valor **[medido]** |
| :-- | :-- |
| Sesiones con Code Mode | 10 (klinikae 5, content-studio 2, portfolio 1, monorepo de plugins 1, otra 1) |
| Modelos | Opus 5.5 en 8, Haiku 5.5 en 2 |
| Versión | 2.1.330 |
| Bloques de código | 873 |
| Sesiones normales de referencia (Opus 5.5) | 43 |

### Cómo escribe Claude los bloques

| Métrica | Valor **[medido]** |
| :-- | :-- |
| Líneas por bloque (mediana) | 5 |
| Líneas por bloque (percentil 90) | 27 |
| Comandos de shell por bloque (promedio) | 1,5 |
| Bloques con 3 o más comandos de shell | 17 % |
| Bloques sin ningún comando de shell (solo archivos o MCP) | 19 % |
| Bloques que paralelizan con `Promise.all` | 11 % |

Claude no escribe programas largos: agrupa dos o tres pasos y devuelve lo esencial. La paralelización explícita es la excepción, no la regla.

### Por request, frente a mis sesiones normales

| Por request (Opus 5.5) | Sin Code Mode (43 sesiones) | Con Code Mode (8 sesiones) |
| :-- | --: | --: |
| Contexto leído de caché | ~283 mil tokens | ~68 mil tokens |
| Contexto escrito en caché | ~3,3 mil tokens | ~0,9 mil tokens |
| Tokens de salida | ~830 | ~220 |
| Costo estimado (a precio de API) | ~US$0,114 | ~US$0,024 |
| Tiempo de API | ~11,5 s | ~2,4 s |

**Cómo leer esta tabla.** No es un A/B: son tareas distintas. Las sesiones con Code Mode tienen muchos requests cortos de `Poll` que bajan el promedio, y las sesiones normales incluyen corridas autónomas muy largas con contextos enormes. La tabla muestra el patrón (cada request de Code Mode carga mucho menos contexto), no un porcentaje de ahorro.

### Mis comparaciones por tarea

Además de los transcripts, repetí tareas de mis proyectos con el modo encendido y apagado. Los resultados fueron muy parecidos a los de las pruebas publicadas del [capítulo 08](08-lo-que-midieron-otros.md):

- **Con muchas llamadas y un resultado pequeño** (consultas repetidas a un MCP, ciclos de editar y probar), el ahorro fue claro en tokens y en costo.
- **En trabajo con archivos locales** que ya resolvía un script de shell, el ahorro fue pequeño o nulo, y algunas corridas tardaron más.
- **En una pregunta sobre un archivo**, solo se notó el ahorro fijo de las herramientas.

### En mi caso

La cifra que más me sirvió no fue un porcentaje sino la forma de los bloques: si una tarea mía termina en bloques de una o dos líneas que solo leen archivos, no gano nada; si termina en un bloque que llama varias herramientas y devuelve un objeto pequeño, sí. El capítulo 11 trae el script que usé para contar todo esto, para que lo corras sobre tus transcripts.

`mediciones` `transcripts` `datos-reales`
