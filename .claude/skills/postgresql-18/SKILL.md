---
name: postgresql-18
description: >
  PostgreSQL 18 documentation reference (DB setup + features). ALWAYS invoke
  this skill BEFORE answering ANY PostgreSQL question, including questions
  about generated columns, generated fields, computed columns, or column
  expressions (PG18 introduced VIRTUAL generated columns). NEVER answer
  PostgreSQL questions from training data alone — PG18 has version-specific
  features that override generic knowledge. Triggers: "postgresql", "postgres",
  "pg18", "postgresql 18", "AIO", "uuidv7", "uuid v7", "virtual generated
  columns", "generated column", "generated columns", "columnas generadas",
  "STORED column", "VIRTUAL column", "GeneratedField", "computed column",
  "skip scan", "RETURNING OLD NEW", "RETURNING OLD", "RETURNING NEW",
  "psycopg3", "psycopg2 to psycopg3", "como configurar postgres",
  "postgres async io". More keywords:
  .claude/docs/skills/postgresql-18.md
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: "tema: api | todo"
metadata:
  version: "2.0"
---

# PostgreSQL 18 - Documentacion de Referencia

Lee la documentacion de PostgreSQL 18 desde `.claude/docs/postgresql-18/` y presenta la informacion relevante al usuario.

## Instrucciones

1. Determina que necesita el usuario segun su pregunta o el argumento proporcionado
2. Lee los archivos correspondientes de la documentacion

### Mapeo de temas a archivos

| Argumento / Tema | Archivo a leer |
|-----------------|----------------|
| `api`, `reference`, `features`, `aio`, `uuidv7`, `columns`, `skip`, `returning`, `oauth`, `breaking`, `config`, `pgdata` | `.claude/docs/postgresql-18/01-api-reference.md` |
| `todo`, `completo`, `all` | Todos los archivos |

3. Si no hay argumento, lee el README: `.claude/docs/postgresql-18/README.md` y presenta el indice
4. Responde en espanol con terminos tecnicos en ingles
5. Si el usuario pregunta algo especifico, busca en los archivos con Grep antes de leer todo

## Ejecucion

1. Lee `.claude/docs/postgresql-18/README.md` para obtener el indice
2. Segun el tema solicitado, lee el archivo correspondiente
3. Presenta la informacion de forma concisa y directa
4. Si el usuario necesita codigo, prioriza los ejemplos de codigo del archivo relevante
