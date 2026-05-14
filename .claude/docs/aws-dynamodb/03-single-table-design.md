# Single-Table Design (Patrón Avanzado - NO Aplicable Aqui)

> Referencia sobre el patrón Single-Table Design de Rick Houlihan. NOTA: NO se usa en este portfolio (se mantienen 2 tablas separadas). Leer para arquitectura futura.

## ¿Qué es Single-Table Design?

Patrón de diseño NoSQL donde todos los datos de múltiples entidades se almacenan en **una sola tabla**, usando estrategias de partition keys + sort keys + global secondary indexes (GSI) para modelar relaciones.

**Mantra:** "Lo que se accede junto debe estar junto" (co-locate data that is accessed together).

### Ejemplo Conceptual

En SQL, tendrías:
```sql
users (id, name)
orders (id, user_id, total)  -- FK a users
```

En single-table design:
```
Tabla única "AppData"
- PK=user#123, SK=metadata       → datos del usuario
- PK=user#123, SK=order#001      → primer orden del usuario
- PK=user#123, SK=order#002      → segunda orden del usuario
- PK=order#001, SK=item#item1    → items de la orden
```

**Una query** get(PK=user#123, SK begins_with "order") trae TODAS las órdenes del usuario sin join.

## Ventajas

1. **Queries complejas en 1 call:** No necesitas query A + query B
2. **Costos menores:** 1 tabla = menos índices = menos write amplification
3. **Transacciones más simples:** TransactWriteItems en 1 tabla (vs cross-table)
4. **Performance predecible:** Menos índices = menos overhead

## Desventajas (Críticas)

1. **Complejidad cognitiva:** Schema es críptico (PK=user#123 vs PK=user_metadata#123)
2. **Mantenibilidad:** Cambiar estructura requiere remigrar datos
3. **Query ad-hoc difícil:** Necesitas entender el patrón de claves
4. **Projection complexity:** GSI projection (KEYS_ONLY vs ALL) requiere planning
5. **Index overflow:** Muchos GSI (~5-10) compensan la ventaja single-table

## Cuándo Aplicar Single-Table Design

✅ **Buena idea si:**
- Relaciones complejas entre entidades (usuarios ↔ órdenes ↔ items)
- Patrón de acceso bien definido y estable
- Queries que siempre acceden datos relacionados juntos
- Volumen muy alto (millones de items/mes)
- Equipo experimentado en NoSQL

❌ **MALA idea si:**
- Tablas independientes sin relaciones (como contacts + tracking)
- Schema en evolución constante
- Queries impredecibles o ad-hoc
- Equipo nuevo en DynamoDB
- Volumen bajo

## Por Qué NO en Este Portfolio

Este portfolio tiene **2 tablas completamente desacopladas:**

**contacts:**
- Queries: put_item(contacto), list por fecha, get por ID
- No accede nunca a tracking
- Schema simple y estable

**tracking:**
- Queries: put_item(evento), get_session (todos los eventos de una sesión)
- No accede nunca a contacts
- TTL maneja borrado automático

**Veredicto:** Dos tablas separadas = **90% más simple, sin perder nada en performance**.

Si el portfolio creciera a un sistema de **dashboard donde necesites:**
- "Dame todos los contactos que visitaron la pagina X"
- "Dame los eventos de tracking del contacto Y"

...entonces SÍ, single-table design estaría justificado:
```
PK=contact#123, SK=metadata
PK=contact#123, SK=visit#2026-05-13T14:30
PK=session#xyz, SK=event#001
  con GSI: PK=contact_id (sparse), para buscar por contacto
```

Pero eso NO es el caso hoy. **Aplica YAGNI (You Aren't Gonna Need It).**

## Decision Log

- **2026-05-13:** Investigacion de single-table design completada
- **Recomendacion:** Mantener 2 tablas separadas para portfolio actual
- **Futuro:** Revisar si se integra dashboard en Q3 2026

## Referencias

- [Rick Houlihan - DynamoDB Advanced Design Patterns (re:Invent 2021)](https://www.youtube.com/watch?v=xfxBhvGpoa0)
- [Alex DeBrie - The What, Why, and When of Single-Table Design](https://www.alexdebrie.com/posts/dynamodb-single-table/)
- [madhead - On DynamoDB's Single Table Design](https://madhead.me/posts/std/)
