# PostgreSQL 18 - Referencia Tecnica

> Motor de base de datos relacional con Asynchronous I/O, virtual generated columns, uuidv7() y OAuth 2.0 nativo.

## Contenido

| Tema | Archivo | Cuando leer |
|------|---------|-------------|
| Features y configuracion | [01-api-reference.md](01-api-reference.md) | AIO, uuidv7, virtual columns, skip scan, RETURNING OLD/NEW, config |

## Reglas criticas

- SIEMPRE usar psycopg v3 (`psycopg[binary]`) como driver para proyectos nuevos
- SIEMPRE verificar ruta `PGDATA` en Docker (cambio breaking en PostgreSQL 18)
- SIEMPRE usar `uuidv7()` en lugar de `uuid_generate_v4()` para PKs (ordenables temporalmente)
- SIEMPRE usar `scram-sha-256` para autenticacion (md5 deprecado)
- NUNCA usar `PGDATA=/var/lib/postgresql/data` sin subpath en Docker (conflicto con mount)
- PREFERIR virtual generated columns sobre triggers para campos calculados

## Navegacion

Contexto padre: [CLAUDE.md](../../../CLAUDE.md)
