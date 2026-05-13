---
name: server-architecture
description: >
  Complete reference for Django 6 server architecture (config, settings, apps,
  models, providers, workflows, tasks, storage). ALWAYS invoke when user needs
  server structure or model fields before implementing features. Triggers:
  "server", "arquitectura", "modelos", "apps", "django apps", "contexto del
  server", "que apps hay", "model relationships", "fields", "modulos del
  proyecto". More keywords: .claude/docs/skills/server-architecture.md
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: "seccion: overview | config | all"
metadata:
  version: "1.0"
---

# Server Architecture - Referencia Completa

## Navegacion por argumento

El usuario puede invocar `/server-architecture <seccion>` para cargar contexto especifico.

### Si el argumento es "overview" o no hay argumento:

LEE el indice general:
- [.claude/docs/server-architecture/README.md](.claude/docs/server-architecture/README.md)

Presenta el resumen del server, las apps, conteo de modelos, y relaciones entre apps.

### Si el argumento es "config" o "common" o "settings" o "enums":

LEE la configuracion y modelos base:
- [.claude/docs/server-architecture/01-config-common.md](.claude/docs/server-architecture/01-config-common.md)

Cubre: settings (base/dev/prod/test), URLs, WSGI/ASGI, UUIDv7Model, TimestampedModel, enums, seed_db command.

### Si el argumento es "all":

LEE TODOS los archivos en orden:
1. [.claude/docs/server-architecture/README.md](.claude/docs/server-architecture/README.md)
2. [.claude/docs/server-architecture/01-config-common.md](.claude/docs/server-architecture/01-config-common.md)

## Respuesta

Despues de leer los docs relevantes, responde la pregunta del usuario con informacion precisa basada en la documentacion.
Si necesitas verificar el estado actual del codigo (campos exactos, nuevos archivos), usa Glob/Grep/Read directamente en `server/`.
