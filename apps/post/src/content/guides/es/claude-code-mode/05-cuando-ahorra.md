**05**

# Cuándo ahorra

[← Índice](README.md)

---

### La regla

> **Importa más cuántas llamadas a herramientas hace Claude, y si su resultado se puede reducir, que cuántos archivos hay.**

### Las tareas donde conviene

| Tarea | Por qué ahorra |
| :-- | :-- |
| Muchas llamadas a un servidor MCP (consultar registros, issues, filas) y devolver un total | Un script de shell no puede llamar herramientas MCP; con Code Mode, las respuestas se procesan dentro del bloque y al modelo le llega solo el resultado |
| Leer muchas respuestas y clasificarlas | Mismo motivo, con más cuidado: el filtro puede dejar datos afuera ([cap. 06](06-cuando-no.md)) |
| Investigación con varias búsquedas web | Las páginas se resumen dentro del script |
| Implementar algo y correr las pruebas | Editar, compilar y probar en un bloque ahorra viajes de ida y vuelta |
| Varios comandos independientes (build, typecheck, lint) | Corren a la vez y vuelve un resumen |
| Comandos largos | Pueden correr en segundo plano mientras Claude sigue con otra cosa |

### Qué tienen en común

- **Muchas llamadas relacionadas** que en modo normal serían muchos turnos.
- **Un resultado pequeño** al final: un conteo, un total, un sí o no, las últimas líneas de un log.
- **Herramientas que la shell no alcanza** (MCP, web) o pasos que dependen del anterior.

### Cómo ayudarlo

- Pídele explícitamente que devuelva un resumen: "dime cuántos fallan y cuáles, no la salida completa".
- Pide conteos por paso y la lista de lo que falló, para que un filtro no esconda errores.
- En tareas MCP grandes, pídele que trabaje en lotes y devuelva totales parciales.

### En mi caso

En mis comparaciones, las tareas donde el ahorro fue claro tenían esta forma: varias consultas seguidas a un servidor MCP que terminaban en un número o una lista corta, y los ciclos de "editar, compilar, probar" en los que antes Claude hacía un viaje por cada paso. Coincide con lo que muestran las pruebas publicadas del [cap. 08](08-lo-que-midieron-otros.md).

`cuándo-usar` `mcp` `ahorro`
