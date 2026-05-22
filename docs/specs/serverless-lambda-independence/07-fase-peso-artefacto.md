# 07 — Fase 6: Control de peso del artefacto

[< 06 Validador dedup](06-fase-validacion-dedup.md) | [Siguiente: 08 Descomposicion >](08-descomposicion.md)

## Objetivo

El packaging mide el peso del artefacto y:

- **WARNING** al acercarse al limite (vendoring, tests, build).
- **ERROR** que aborta el `build`/`deploy` si supera un hard limit de
  AWS Lambda.

## 4. Diagrama de flujo

```text
package_lambda(lambda)            vendored_shared(lambda) / tests
  -> arma build/                    -> vendoriza core/shared/
  -> mide:                          -> mide el peso vendorizado
       descomprimido = du(build/)
       zip = size(build.zip)
  -> {zip > 50MB o desc > 250MB}? --SI--> PackagingError (ABORTA)
  -> {zip > 40MB o desc > 200MB}? --SI--> [WARN] ambas cifras
  -> sigue
```

## 5. Diagrama ER

N/A.

## Limites de AWS Lambda (fuente del control)

Investigado 2026-05-22, `docs/progress/explore_aws_lambda_size_limits.md`:

| Limite | Valor | Aplica a |
|--------|-------|----------|
| `.zip` subida directa | 50 MB comprimido | el `build.zip` |
| Paquete descomprimido (codigo + deps + layers) | 250 MB | el `build/` |
| Imagen OCI | 10 GB | N/A (el backend usa `.zip`) |

Los tres son **hard limits no ajustables**. Umbrales del plan:

| Cifra | WARNING (80%) | ERROR (hard limit) |
|-------|---------------|--------------------|
| zip comprimido | > 40 MB | > 50 MB |
| build descomprimido | > 200 MB | > 250 MB |

El backend usa `.zip` con subida directa (`aws lambda
update-function-code --zip-file`), asi que el limite de 50 MB
comprimido SI aplica (no se usa S3). Si en el futuro un Lambda necesita
mas, la salida es S3 o imagen OCI — fuera del scope de este plan, pero
el mensaje de error lo menciona.

## Que mide y donde

- **`build/` descomprimido**: `du -sb` del directorio que arma
  `package_lambda` (deps + `core/` + `core/shared/`). Mapea al limite de
  250 MB.
- **`build.zip` comprimido**: `Path.stat().st_size` del zip que arma
  `zip_build_dir`. Mapea al limite de 50 MB.
- El WARNING reporta AMBAS cifras siempre (Decision D-6) y marca cual
  esta mas cerca de su limite.

Puntos de medicion:

| Comando | Que mide | Accion |
|---------|----------|--------|
| `deploy` / `build` | zip + descomprimido | WARN al 80%, ERROR al pasar |
| `tests` (vendoriza `core/shared/`) | descomprimido del vendor | WARN informativo (no aborta tests) |
| `run --stage=local` (RIE arma build) | zip + descomprimido | WARN al 80% |

`tests` y `run` solo ADVIERTEN — no abortan (no estan deployando). Solo
`deploy`/`build` ERROR-an: ahi el artefacto va a AWS.

## Configuracion de los umbrales

Decision: los umbrales son los **hard limits de AWS** (no configurables
por Lambda). Viven como constantes en el modulo nuevo de devtools:

```python
AWS_ZIP_LIMIT_MB = 50            # hard limit subida directa
AWS_UNZIPPED_LIMIT_MB = 250      # hard limit descomprimido
WARN_RATIO = 0.80                # warning al 80% del limite
```

No hay `max_zip_size` por `manifest.yaml`: los limites son de AWS, no
del Lambda. Si un Lambda los supera, el problema es el Lambda, no el
umbral.

## 6. Tests requeridos

### 6.A TDD flows

- `WHEN el build.zip mide 45MB THEN se imprime [WARN] (>80% de 50MB) [AC-10]`
- `WHEN el build descomprimido mide 260MB THEN package_lambda lanza
  PackagingError [AC-9]`
- `WHEN el build.zip mide 30MB y desc 100MB THEN no hay warning ni error`
- `WHEN hay warning THEN el mensaje incluye AMBAS cifras (zip + desc) [AC-10]`

### 6.B Unit tests (devtools, pytest)

- `devtools/tests/serverless/test_artifact_size_*.py` — un archivo por
  escenario. Mockear `du`/`stat` para simular tamanos. Asserts EXACTOS
  sobre el mensaje y el exit/excepcion.

### 6.C Typecheck

- `mypy` del modulo nuevo.

## 7. Archivos afectados

### Crear

- `devtools/serverless/artifact_size.py` — mide `build/` y `build.zip`,
  compara contra los limites, produce warning/error.
  - Verificar: `serverless tests --type=unit --module=devtools` (tests
    de artifact_size) verde.
- `devtools/tests/serverless/test_artifact_size_*.py`

### Modificar

- `devtools/serverless/packaging.py` — `package_lambda` mide el `build/`
  descomprimido tras armarlo; `zip_build_dir` mide el zip. Encadena el
  check de `artifact_size`: WARN o `PackagingError` segun el caso.
  - Verificar: build de un Lambda imprime ambas cifras.
- `devtools/serverless/vendoring.py` — `vendor_shared_selective` mide el
  vendor y emite WARN informativo.
- `devtools/serverless/lambda_controller.py` — el comando `tests`
  reporta el peso del vendor tras vendorizar.

## Definition of Done de la fase

- [ ] `build`/`deploy` falla si el zip > 50 MB o el descomprimido >
      250 MB (AC-9).
- [ ] `build`/`deploy`/`tests` imprime `[WARN]` con ambas cifras al
      80% del limite (AC-10).
- [ ] Los 4 Lambdas actuales pasan sin warning (estan muy por debajo).
- [ ] Tests unit del modulo verdes, coverage >= 80%.

[< 06 Validador dedup](06-fase-validacion-dedup.md) | [Siguiente: 08 Descomposicion >](08-descomposicion.md)
