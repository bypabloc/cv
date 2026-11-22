**04**

# De dónde sale el ahorro

[← Índice](README.md)

---

### Fuente 1: menos definiciones de herramientas (fijo)

En vez de una docena de herramientas con descripciones largas, el modelo recibe `REPL` y `Poll`. En `/context`, las "System tools" bajan de unos 25k a unos 11k tokens, y todas las sesiones arrancan unos **13 mil tokens más pequeñas**, incluso para una pregunta trivial **[publicado]**. Ese ahorro se paga en cada request de la sesión.

### Fuente 2: los resultados intermedios no vuelven al modelo (variable)

Cuando el script procesa la salida de las herramientas y devuelve solo un resumen, todo lo intermedio (registros, archivos leídos, logs) nunca entra al contexto. Este es el ahorro grande, pero solo aparece cuando la tarea **se puede reducir**: un total, un conteo, una lista corta. Si el script imprime los datos crudos, el ahorro desaparece.

### Fuente 3: menos viajes al modelo (a veces)

Encadenar pasos en un bloque puede ahorrar requests. Pero no siempre: con el modo encendido hay requests extra de `Poll`, y en algunas pruebas el número de requests incluso subió mientras el costo bajaba, porque cada request era más barato.

### El mito del 37 %

El "37 % menos de tokens" que circuló en los primeros días no es de Code Mode: viene de una evaluación de *Programmatic Tool Calling* en la API de Anthropic, de 2025. Otros números virales (77 %, 98,7 %) vienen de una sola tarea favorable o de otros contextos. Un porcentaje sin la tarea que lo produjo no dice nada **[criterio]**.

### Tokens no es lo mismo que costo ni que cuota

- Las lecturas de caché cuentan como tokens procesados pero cuestan una fracción.
- Las pruebas públicas midieron tokens o costo estimado a precio de API. **Nadie publicó cuánto se estira la cuota de 5 horas o la semanal** de una suscripción.
- El tiempo es otra métrica: un modo más barato puede tardar más.

### En mi caso

En mis sesiones con el modo, cada request leyó mucho menos contexto de caché que en mis sesiones normales del mismo período ([cap. 07](07-mis-mediciones.md)). Parte de eso es la Fuente 1 y parte es la Fuente 2, pero no las puedo separar sin un A/B: por eso el capítulo 11 explica cómo medirlo tarea por tarea.

`ahorro` `tokens` `contexto` `mitos`
