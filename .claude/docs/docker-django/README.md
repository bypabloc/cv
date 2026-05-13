# Docker para Django + PostgreSQL - Referencia Tecnica

> Containerizacion de aplicaciones Django 6 con PostgreSQL 18 usando Docker Compose, multi-stage builds y uv.

## Contenido

| Tema | Archivo | Cuando leer |
|------|---------|-------------|
| Dockerfile y build | [01-dockerfile.md](01-dockerfile.md) | Multi-stage build, uv, non-root, health checks, .dockerignore |
| Docker Compose | [02-docker-compose.md](02-docker-compose.md) | compose.yml, PostgreSQL 18 PGDATA, volumes, secrets, migraciones |

## Reglas criticas

- SIEMPRE usar `python:3.12-slim-bookworm` como imagen base (~41MB)
- SIEMPRE usar multi-stage builds (builder + runtime)
- SIEMPRE ejecutar como non-root user en produccion
- SIEMPRE incluir health checks en `compose.yml`
- NUNCA incluir `.env` en la imagen Docker (usar Docker secrets o env vars)
- NUNCA usar el campo `version:` en `compose.yml` (deprecado)
- PREFERIR `uv` sobre `pip` para instalacion de dependencias (10-15x mas rapido)
- SIEMPRE usar `.dockerignore` para excluir `.env`, `.git`, `tmp/`, `__pycache__`

## Navegacion

Contexto padre: [CLAUDE.md](../../../CLAUDE.md)
