**03**

# Cómo se ve un bloque de código

[← Índice](README.md)

---

### Las piezas que usa Claude

Dentro de un bloque, Claude tiene un conjunto de funciones para llegar a las herramientas **[doc]**:

| Pieza | Para qué |
| :-- | :-- |
| `` $`comando` `` | Corre un comando de shell; `.text()`, `.lines()` o `.json()` leen la salida, `.nothrow()` no lanza error con un exit distinto de 0 |
| `file(ruta).text()` | Lee un archivo |
| `edit(ruta, viejo, nuevo)` / `write(ruta, texto)` | Edita o escribe, con el diff visible en la conversación |
| `Promise.all([...])` | Corre varias llamadas a la vez |
| Herramientas MCP | Se llaman como funciones; sus respuestas se procesan dentro del script |

### Lo que vuelve al modelo

Solo la última expresión del bloque (o lo que se registre explícitamente). Un patrón típico:

```js
const [log, tests] = await Promise.all([
  $`git log --oneline -20`.text(),
  $`pnpm test`.nothrow(),
])
;({ commits: log.trim().split('\n').length, testsOk: tests.exitCode === 0, tail: tests.stdout.slice(-2000) })
```

El modelo recibe un conteo, un booleano y las últimas líneas de las pruebas, no el log completo ni toda la salida.

### Bloques en segundo plano

Un bloque que tarda puede seguir corriendo mientras Claude hace otra cosa o te responde; `Poll` recoge el resultado cuando termina. Los límites **[doc]**:

- Si Claude espera al bloque, se corta a los **10 minutos**.
- En segundo plano puede correr hasta **2 horas**, pero solo si la sesión **empezó** en auto mode o `bypassPermissions`.
- `Esc` detiene un bloque en curso; los de segundo plano se ven y se detienen en `/tasks`.

### El resultado se corta

Lo que devuelve un bloque se recorta a unos 30 mil caracteres (el inicio y el final), y la parte del medio no se guarda en ningún lado. El truco es guardar el resultado en una variable y pedir solo trozos, o recortar antes de devolver.

### En mi caso

En mis sesiones, un bloque típico corre uno o dos comandos y devuelve un objeto con lo esencial; solo uno de cada diez usa `Promise.all` para paralelizar ([cap. 07](07-mis-mediciones.md)). Los bloques largos son la excepción: solo uno de cada diez pasa de 27 líneas.

`code-mode` `javascript` `anatomía`
