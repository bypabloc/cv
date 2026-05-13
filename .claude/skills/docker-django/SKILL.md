---
name: docker-django
description: >
  Docker docs for containerizing Django + PostgreSQL. ALWAYS invoke for Docker
  reference in Django projects. Triggers: "docker", "dockerfile", "docker
  compose", "containerizar", "docker django", "docker postgres", "multi-stage
  build", "docker volume", "como dockerizar", "compose.yml", "docker
  production". More keywords: .claude/docs/skills/docker-django.md
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: "tema: dockerfile | compose | todo"
metadata:
  version: "2.0"
---

# Docker para Django - Documentacion de Referencia

Lee la documentacion de Docker para Django desde `.claude/docs/docker-django/` y presenta la informacion relevante al usuario.

## Instrucciones

1. Determina que necesita el usuario segun su pregunta o el argumento proporcionado
2. Lee los archivos correspondientes de la documentacion

### Mapeo de temas a archivos

| Argumento / Tema | Archivo a leer |
|-----------------|----------------|
| `dockerfile`, `image`, `build`, `multi-stage`, `uv`, `pip`, `non-root`, `entrypoint`, `dockerignore`, `layers`, `base` | `.claude/docs/docker-django/01-dockerfile.md` |
| `compose`, `services`, `volumes`, `network`, `health`, `secrets`, `migraciones`, `dev`, `prod`, `comandos`, `pgdata` | `.claude/docs/docker-django/02-docker-compose.md` |
| `todo`, `completo`, `all` | Todos los archivos |

3. Si no hay argumento, lee el README: `.claude/docs/docker-django/README.md` y presenta el indice
4. Responde en espanol con terminos tecnicos en ingles
5. Si el usuario pregunta algo especifico, busca en los archivos con Grep antes de leer todo

## Ejecucion

1. Lee `.claude/docs/docker-django/README.md` para obtener el indice
2. Segun el tema solicitado, lee el archivo correspondiente
3. Presenta la informacion de forma concisa y directa
4. Si el usuario necesita codigo, prioriza los ejemplos de codigo del archivo relevante
