# server/ (stub)

> Directorio placeholder requerido por la arquitectura de `devtools/`.
> Este portfolio NO tiene backend Django. `server/manage.py` es solo
> un stub que existe para que `devtools/hooks/main.py` no aborte al
> verificar la presencia del modulo server.

## Por que existe

El orquestador de hooks (`devtools/hooks/main.py`) hereda de
`mvp-template-full-stack`, donde existe un Django server. La logica
de deteccion de archivos (`shared/scan_helper.py`) y de clasificacion
asume que `server/` es un workspace valido.

Para mantener paridad 100% con esa arquitectura sin tener Django:

- `server/manage.py` existe pero solo imprime un mensaje y sale 0
- `server/.gitignore` ignora cualquier artefacto que pudiera crearse
- Los steps `coverage`, `integration` y `conformance` de Python en
  pre-commit/pre-push no encuentran archivos `.py` en `server/` y
  exit-early sin levantar Docker

## Si en el futuro se agrega backend

1. Reemplazar `manage.py` por el real de Django
2. Agregar las apps Django bajo `server/<app>/`
3. Crear `server/ruff.toml` con la config de linting
4. Los hooks empezaran a detectar archivos `.py` automaticamente

Por ahora, este directorio queda intencionalmente vacio.
