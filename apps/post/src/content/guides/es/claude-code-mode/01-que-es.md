**01**

# Qué es Code Mode y qué cambia

[← Índice](README.md)

---

### El modo normal: un viaje por herramienta

Sin Code Mode, Claude pide una herramienta, espera el resultado, lo lee y recién entonces decide la siguiente: lee un archivo, ejecuta un comando, lee la salida, edita, vuelve a ejecutar. Cada paso es un viaje al modelo, y cada resultado completo se queda en la ventana de contexto para el resto de la sesión.

### Con Code Mode: un script que encadena herramientas

Con el modo encendido, Claude escribe un bloque de JavaScript que hace las llamadas por él y Claude Code lo ejecuta dentro de la sesión **[doc]**:

```js
const hits = await $`rg -l "maxAttempts: 3" src`.text()
for (const f of hits.trim().split('\n')) await edit(f, 'maxAttempts: 3', 'maxAttempts: 5')
const t = await $`npm test`.nothrow()
;({ edited: hits.trim().split('\n').length, tests: t.exitCode })
```

Un solo bloque busca, edita en varios archivos y corre las pruebas. **La última expresión es lo único que vuelve al modelo**: en el ejemplo, dos números, no la lista de archivos ni la salida de las pruebas.

### Qué ve el modelo

En vez de una docena de herramientas, el modelo recibe dos **[doc]**:

| Herramienta | Para qué |
| :-- | :-- |
| `REPL` | Ejecuta un bloque de JavaScript con acceso a la shell, a los archivos, a la web y a los servidores MCP |
| `Poll` | Recoge el resultado de un bloque que sigue corriendo en segundo plano |

Dentro del bloque, las herramientas de siempre (Bash, Read, Edit, MCP) siguen existiendo: se llaman desde el código y pasan por tus permisos y hooks con su nombre normal ([cap. 09](09-permisos-y-hooks.md)).

### Qué promete y qué no

La documentación no da cifras de ahorro. Dice que conviene probarlo en tres casos: un cambio que se repite en muchos archivos, una búsqueda cuyos resultados hay que filtrar antes de leerlos y varios comandos independientes que pueden correr a la vez **[doc]**. Es experimental, viene apagado y puede cambiar o desaparecer en cualquier versión.

Un detalle importante: **el modelo decide** cuándo escribir un script. Con el modo encendido, una pregunta simple se sigue respondiendo con una sola lectura.

### En mi caso

Lo que más me sorprendió al principio fue lo corto de los bloques. Esperaba scripts largos que hicieran todo; en mis sesiones, la mitad de los bloques tiene 5 líneas o menos ([cap. 07](07-mis-mediciones.md)). Claude usa el script para agrupar dos o tres pasos y devolver solo lo necesario, no para escribir un programa.

`code-mode` `claude-code` `conceptos`
