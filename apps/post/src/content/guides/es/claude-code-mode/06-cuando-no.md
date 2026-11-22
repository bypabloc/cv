**06**

# Cuándo no ahorra (y es más lento)

[← Índice](README.md)

---

### Archivos locales que la shell ya resolvía

Si en modo normal Claude ya escribía un `rg` o un script de Python que recorría los archivos en un solo proceso, Code Mode no tiene viajes que ahorrar. Peor: a veces el script cambia de estrategia y hace **una lectura por archivo**. Con cientos de archivos, cada lectura pasa por los permisos y los hooks, y la tarea tarda de 1,4 a 2,8 veces más **[publicado]**.

| Tarea | Qué pasa |
| :-- | :-- |
| Buscar enlaces rotos en cientos de Markdown | El modo normal usa un script de una pasada; Code Mode puede terminar con cientos de `Read` |
| Edición masiva por regla en 100 archivos | Algo más barato, bastante más lento |
| Responder una pregunta sobre un archivo | Solo el ahorro fijo de las herramientas |

### Bloques que imprimen los datos crudos

Si el script devuelve todo lo que leyó, el contexto crece igual o más que en modo normal. En las pruebas publicadas, en tareas con archivos el contexto **añadido durante el trabajo** creció con Code Mode en 14 de 16 comparaciones, aunque el total de tokens bajara por el ahorro fijo **[publicado]**.

### Filtros que esconden datos

El filtro es la gracia del modo y también su riesgo: si el script descarta algo por error, **el modelo no se entera**. En las pruebas publicadas hubo un filtro por palabra clave que dejó afuera 4 de 9 tickets y una respuesta que decía haber leído todos cuando había omitido dos **[publicado]**.

Cómo protegerte:

- Pide conteos por paso (cuántos leyó, cuántos filtró, cuántos quedaron).
- Pide la lista de lo que falló o se descartó.
- Para leer y juzgar texto libre, no confíes en un "leí todos".

### Modelos pequeños

Con Haiku 5.5 los resultados fueron más irregulares: una corrida buscó en la carpeta equivocada y 344 de 349 comandos fallaron, aunque la tarea "pasó" **[publicado]**. Con un modelo pequeño conviene revisar el resultado con más cuidado.

### En mi caso

Lo vi en las auditorías de archivos de mis repos: cuando la tarea era revisar muchos Markdown o aplicar un cambio mecánico, el modo normal ya lo resolvía con un script de una pasada y Code Mode no lo mejoró; en algunas corridas tardó más. Para ese tipo de tareas, hoy prefiero pedirle explícitamente "hazlo con un solo comando de shell" o abrir una sesión sin el modo.

`cuándo-no` `rendimiento` `riesgos`
