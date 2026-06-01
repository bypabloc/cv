# 04 — Fase medicion (api_e2e mide cold real vs INIT crudo)

[< INIT/imports](03-fase-init-imports.md) | [Siguiente: Vendoring opcional >](05-fase-vendoring-opcional.md)

> Sin medición correcta no se verifica la mejora ni se distingue una
> regresión. Hoy `api_e2e` mezcla cold real (restore) con INIT crudo en un
> solo número. Cubre AC-6. Es prerequisito de la verificación (sección 11).

## Problema actual

`devtools/api_e2e/support.py:27-34` mide `elapsed` con `time.monotonic()`
client-side alrededor del request HTTP. `reporter.py` toma `cold =
elapsed[0]` (primer hit) y `warm = avg(elapsed[1:])`. No fuerza cold y no
sabe si el primer hit fue un SnapStart restore (~1.2s) o un INIT crudo
(~14s). Por eso el número "cold" es ruidoso e ininterpretable.

## Solucion

`api_e2e` no puede leer el `Restore Duration` desde el cliente HTTP (es un
dato de CloudWatch). Dos opciones:

### Opción 1 (recomendada): correlacionar con CloudWatch tras el run

Tras el run HTTP, `api_e2e` consulta CloudWatch (`filter-log-events`) por
`REPORT`/`RESTORE_REPORT`/`INIT_REPORT` del Lambda en la ventana del run y
reporta, por caso cold:

```
cv  cv.get  cold(http) 1.34s  [Restore 0.96s | Init crudo: -]   warm 0.04s
cv  cv.get  cold(http) 14.4s  [Restore: -    | Init crudo 13.9s] warm 0.04s
```

Así se ve si el cold fue un restore (bueno) o un INIT crudo (el peor
caso). Requiere `logs:FilterLogEvents` en el perfil (ya disponible) y el
nombre de la función por caso.

### Opción 2 (más simple): forzar cold reproducible

Antes de medir, `api_e2e` puede forzar un cold real con
`update-function-configuration` (un env var dummy bump) para invalidar el
container, y así medir el cold del path `:live` de forma reproducible. Es
lo que hoy NO hace. Matiz: tras el bump, SnapStart re-optimiza la versión;
hay que esperar `OptimizationStatus=On` antes de medir, si no se mide el
INIT crudo siempre.

## Decision

Implementar **Opción 1** (correlación CloudWatch) — es no-intrusiva, no
muta la función, y da el desglose que falta. Opción 2 queda documentada
como modo opcional `--force-cold` para mediciones controladas.

## Archivos afectados

### Modificar

- `devtools/api_e2e/reporter.py` — agregar columnas/desglose
  `restore_ms` e `init_crudo_ms` por caso cold.
- `devtools/api_e2e/runner.py` o nuevo
  `devtools/api_e2e/cloudwatch.py` — tras el run, consultar
  `filter-log-events` por función en la ventana temporal del run y
  parsear `Restore Duration` / `Init Duration` de los `REPORT`.
- `devtools/api_e2e/config.py` — mapear cada caso a su nombre de función
  Lambda (`cv -> portfolio-cv-<env>`).
- `devtools/api_e2e/flags.py` — flag opcional `--force-cold` (Opción 2).
  - Verificar: `python devtools/run.py serverless tests --type=unit --module=devtools`
  - Verificar: `python devtools/run.py api_e2e --env=dev` reporta el
    desglose restore vs INIT crudo.

## Tests requeridos

- Unit del parser de `Restore Duration`/`Init Duration` desde una línea
  `REPORT` de ejemplo (assert exacto del valor parseado). BDD-style.
- `python devtools/run.py serverless tests --type=unit --module=devtools` verde.

## Nota

CI no gatea `devtools/` (memoria del proyecto). Verificar SIEMPRE local
con `devtools/.venv/bin/python` (3.14), no el `python3` del shell.

[< INIT/imports](03-fase-init-imports.md) | [Siguiente: Vendoring opcional >](05-fase-vendoring-opcional.md)
