**01**

# Por qué el agente pierde el hilo

[← Índice](README.md)

---

### Qué es compactar

Cuando el contexto se llena, el agente **compacta**: reemplaza la conversación por un resumen hecho por un modelo y descarta las salidas de herramientas (archivos leídos, logs, diffs). Es lo que permite sesiones de horas, pero tiene un costo.

### Los seis problemas

| # | Problema | Qué pasa | Dónde se resuelve |
| :-- | :-- | :-- | :-- |
| 1 | **Compactación tardía** | Compactar cerca del límite da un resumen peor: el modelo resume una conversación enorme con poco margen, y los últimos turnos trabajan saturados | [Cap. 02](02-compactar-antes.md) |
| 2 | **Lo que se pierde al compactar** | El resumen omite o deforma decisiones, el paso actual y las trampas ya encontradas: el agente repite errores o vuelve atrás | [Cap. 03](03-handoff-en-disco.md) a [05](05-configurar-cada-agente.md) |
| 3 | **Caché vencida** | Tras una pausa mayor que el TTL, el siguiente mensaje reenvía todo el historial sin descuento | [Caps. 06](06-cache-de-prompt.md) y [07](07-pausa-larga.md) |
| 4 | **El resumen sobra** | Con el estado en disco, la llamada que resume es lenta y casi todo lo que produce ya está escrito | [Caps. 08](08-compactar-sin-resumen.md) y [09](09-receta-del-plugin.md) |
| 5 | **El agente corta el trabajo** | Cierra el turno tras compactar, pregunta lo que puede decidir o se queda esperando | [Cap. 11](11-uso-diario.md) |
| 6 | **Varias sesiones a la vez** | Se pisan el estado o saturan recursos compartidos | [Cap. 11](11-uso-diario.md) |

### Por qué el resumen no basta

- **Es una paráfrasis.** Lo escribe otro llamado al modelo, que decide qué conservar. Una decisión con su motivo se convierte en "se decidió X"; el motivo desaparece y vuelve a discutirse.
- **No obliga a nada.** Pedirle al resumen que "relea `PROGRESS.md`" sirve de poco: la orden queda como texto y el modelo puede ignorarla. Lo que devuelve la información al contexto es un **hook**.
- **Afecta también a las reglas.** Con la compactación remota de Codex, `AGENTS.md` y las reglas pasan por el modelo que resume. **[comunidad]** ([CompressAgent](https://codex.danielvaughan.com/2026/08/28/control-under-compression-agent-control-context-reliability-codex-cli-compaction-agents-md/))

### Valores de fábrica

| Agente | Cuándo compactaba |
| :-- | :-- |
| Claude Code con ventana de 1M | Cerca de 967K tokens, ≈97 % **[doc + prueba]** |
| Codex con ventana de 272k | Con el límite del modelo; la compactación al cerrar el turno, apagada **[doc]** |
| OpenCode | Con el `buffer` por defecto **[doc]** |
| Antigravity | Sin valor documentado **[bin]** |

El "83 %" que circula en blogs para Claude Code corresponde a la ventana antigua de 200K.

### La idea que sostiene la guía

> **Lo que está en disco sobrevive a la compactación; la conversación no.**

El agente mantiene unos pocos archivos breves con el estado del trabajo. Después de compactar (o al iniciar, reanudar o volver de una pausa), un hook los inyecta en el contexto. El agente sigue desde datos que escribió él mismo, no desde un resumen hecho por otro modelo.

### Qué vas a montar

1. Un umbral de compactación versionado por agente ([cap. 02](02-compactar-antes.md)).
2. La carpeta del handoff y sus líneas de estado ([cap. 03](03-handoff-en-disco.md)).
3. Un script común que responde a los hooks de los cuatro agentes ([caps. 04](04-script-comun.md) y [05](05-configurar-cada-agente.md)).
4. La detección de pausas largas ([caps. 06](06-cache-de-prompt.md) y [07](07-pausa-larga.md)).
5. Opcional, en Claude Code: un plugin que compacta sin resumen ([caps. 08](08-compactar-sin-resumen.md) y [09](09-receta-del-plugin.md)).
6. Pruebas que demuestran que el modelo recibe el handoff ([cap. 10](10-probar-el-handoff.md)).

### En mi caso

El sistema no salió de una vez. La primera versión fue una carpeta de handoff por rama, y cada uno de los seis problemas apareció como un fallo concreto: dos sesiones en la misma rama se pisaban el estado, el handoff de un worktree no llegaba a la sesión del checkout principal, y el agente, con el handoff bien inyectado, igual cerraba el turno ante un aviso de presupuesto. El diseño llegó a su cuarta versión ([cap. 03](03-handoff-en-disco.md)), y el plugin de compactación pasó por siete ([cap. 08](08-compactar-sin-resumen.md)). Esta guía es la versión final, con los fallos que la explican.

`compactación` `contexto` `handoff` `problema`
