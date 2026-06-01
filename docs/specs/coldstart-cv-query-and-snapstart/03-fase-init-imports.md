# 03 — Fase INIT / imports (palanca #2, acotar peor caso)

[< Fase query cv](02-fase-query-cv.md) | [Siguiente: Medicion api_e2e >](04-fase-medicion-api-e2e.md)

> SnapStart absorbe el INIT casi siempre (restore ~1.2s). Pero el INIT
> crudo (7-20s) se paga cuando NO restaura (post-deploy, escalado). Esta
> fase lo acota a < 6s. Cubre AC-5. Es la fase de MENOR ROI — hacerla
> SOLO después de la query (fase 02) y solo si la medición lo justifica.

## Por que el INIT crudo es tan alto y variable

A 256 MB el Lambda tiene ~0.16 vCPU. El INIT de `cv` ejecuta en
module-scope (`services/cv/core/handler.py`):

1. 10 imports de modelos SQLAlchemy (`import shared.db.models.cv.*` +
   taxonomy + i18n) — registran mappers.
2. `warm_db()` (`handler.py:57`) -> `create_engine(NullPool)` +
   `configure_mappers()` (compila los ~25 mappers registrados). **CPU-bound.**
3. `build_event_model(OPERATIONS)` (`handler.py:53`) -> crea una clase
   Pydantic dinámica.
4. `Logger()` y `Metrics()` de Powertools se instancian al importar
   `shared.observability.logger`/`metrics` (module-scope).

A 0.16 vCPU, `configure_mappers()` + la compilación de validadores
Pydantic + la inicialización de Powertools se vuelven lentas y variables
(7s a 20s).

## Que NO se toca

- **`warm_db()` se queda.** Es intencional: precalienta el ORM en el INIT
  para que quede en el snapshot de SnapStart. Quitarlo movería el costo a
  la primera request (peor). La regla `lambda-config.md` lo exige.
- **Los imports concretos se quedan.** Ya están bien (no hay barrels, no
  carga fido2/crypto). El subagente confirmó: cv carga solo SQLAlchemy +
  Powertools, no cryptography ni boto3 en INIT.

## Palancas reales (de menor riesgo a mayor)

### Palanca A — precompilar `.pyc` en el zip (bajo riesgo, mejora directa)

Hoy `packaging.py` excluye `*.pyc` del zip. En el INIT, Python compila
cada `.py` a bytecode la primera vez (cv + shared + deps = cientos de
módulos). Precompilar con `compileall` y **incluir** los `.pyc` ahorra
ese paso del INIT.

- Cambio en `devtools/serverless/packaging.py`: tras armar `build/`,
  correr `python -m compileall -q build/` con el intérprete del runtime
  target (3.13) y NO excluir los `.pyc` resultantes del zip.
- Matiz: AWS Lambda Python usa el mismo árbol; los `.pyc` deben ser para
  3.13. Generarlos con `uv run --python 3.13 -m compileall` o el
  intérprete correcto.
- Impacto esperado: 0.5-2s menos de INIT (cientos de módulos sin
  compilar en frío).

### Palanca B — diferir `Metrics()`/`Logger()` de module-scope (riesgo medio)

Powertools instancia el `Logger` y `Metrics` al importar. Evaluar si
construirlos lazy (primera request) reduce el INIT sin romper el snapshot.
Matiz: con SnapStart, lo que está en module-scope queda en el snapshot —
moverlo a la primera request lo SACA del snapshot y lo paga en cada
restore. **Por eso esta palanca es delicada**: solo conviene para el INIT
crudo, pero perjudica el path con restore. Decisión: **NO mover** lo que
ya está en el snapshot; solo confirmar que no se construye dos veces.

### Palanca C — medir el desglose del INIT (prerequisito de B/A)

Antes de tocar nada, instrumentar el INIT con timestamps para saber qué
parte cuesta:

```python
# en handler.py, temporal para medir (luego quitar):
import time as _t
_t0 = _t.perf_counter()
# ... imports de modelos ...
logger.info('init.models', extra={'ms': (_t.perf_counter()-_t0)*1000})
warm_db()
logger.info('init.warm_db', extra={'ms': (_t.perf_counter()-_t0)*1000})
```

Esto NO va al commit final — es para decidir si A/B valen la pena. Si el
INIT crudo lo domina `configure_mappers` (CPU), la única palanca real
sería subir CPU (= memoria), que está vetado. Si lo domina la compilación
de `.pyc`, la palanca A lo arregla sin tocar memoria.

## Decision de la fase

1. Primero **palanca C** (medir el desglose del INIT en dev contra
   `$LATEST`).
2. Si la compilación de bytecode pesa -> **palanca A** (`.pyc` en el zip).
3. **NO** tocar el module-scope que está en el snapshot (palanca B
   descartada por perjudicar el restore).
4. Si tras A el INIT sigue > 6s y lo domina `configure_mappers` a baja
   CPU, documentar que el único fix sería más memoria (vetado) y aceptar
   que SnapStart lo cubre en el 99% de los casos.

## Archivos afectados

### Modificar

- `devtools/serverless/packaging.py` — palanca A: `compileall` del
  `build/` con runtime 3.13 + incluir `.pyc` en el zip (quitar `*.pyc`
  del `_IGNORE` solo para el `build/` final, no para el vendoring de
  fuentes shared).
  - Verificar: `python devtools/run.py serverless deploy --lambda=cv
    --stage=dev` produce un zip con `.pyc` y el Lambda arranca.
  - Verificar: INIT crudo medido baja (CloudWatch `INIT_REPORT`).

## Tests requeridos

- `python devtools/run.py serverless tests --type=unit --module=devtools`
  (si se toca packaging, su test unit debe cubrir el nuevo paso).
- Medición CloudWatch antes/después del INIT crudo (no es un test
  automatizado; va en la sección 11).

## Nota de honestidad

Esta fase puede terminar con **mejora marginal** si `configure_mappers` a
baja CPU domina el INIT (caso en que la única palanca sería memoria,
vetada). Eso está bien: SnapStart ya cubre el 99% de los colds. Esta fase
es "acotar el peor caso", no "el fix principal". El fix principal es la
fase 02 (query).

[< Fase query cv](02-fase-query-cv.md) | [Siguiente: Medicion api_e2e >](04-fase-medicion-api-e2e.md)
