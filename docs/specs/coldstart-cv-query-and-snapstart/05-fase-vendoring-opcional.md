# 05 — Fase vendoring (opcional, impacto despreciable en cold)

[< Medicion](04-fase-medicion-api-e2e.md) | [Siguiente: Commits >](06-commits.md)

> El usuario pidió mejorar el cold "por estructura de carpetas/archivos e
> imports de shared y por el vendoring del zip". El vendoring se auditó y
> está CORRECTO. Esta fase documenta la única mejora menor posible y por
> qué el resto NO mueve la aguja. Es OPCIONAL.

## El vendoring ya es correcto (no hay bug)

`devtools/serverless/packaging.py` (auditado contra el código):

- `uv pip install --target build/ --python-version 3.13
  --python-platform aarch64-manylinux2014 --only-binary=:all:` — wheels
  arm64 correctos para el runtime AWS, nunca build desde source
  (`packaging.py:200-212`).
- Poda `boto3` + `botocore` porque el runtime los provee
  (`packaging.py:234-259`) — ahorra ~100 MB. Correcto.
- Excluye `.venv`, `__pycache__`, `*.pyc`, `.pytest_cache`, `*.egg-info`
  del vendoring de fuentes shared (`packaging.py:50-62`).
- `shared_resolver.py` resuelve el cierre transitivo por AST +
  `internal-deps` — un Lambda que no usa `shared.db` no arrastra
  SQLAlchemy. Correcto.

CodeSize medido: cv 14.1 MB, auth/users/contact 18.6-18.8 MB. Todos muy
por debajo del límite (50 MB zip / 250 MB descomprimido). **El tamaño del
zip no es el cuello de botella del cold** — el cold lo domina el INIT
(CPU) y la query (I/O), no la descarga del zip (que ocurre una vez y
queda cacheada en el host).

## Por que reestructurar imports/carpetas NO baja el cold

El usuario suponía que reordenar imports de `shared` bajaría el cold. Los
hechos:

1. SnapStart **ya** snapshotea el INIT con todos los imports ejecutados.
   El restore (~1.2s) NO re-ejecuta imports. Reordenarlos no cambia el
   restore.
2. Los imports concretos ya están bien (sin barrels, `cv` no carga
   cryptography/fido2/boto3 en INIT — confirmado por AST scan).
3. El INIT crudo (cuando no hay restore) lo domina `configure_mappers`
   (CPU) y la compilación de bytecode, NO el grafo de imports en sí.

Por eso la reestructuración de imports tiene ROI ~nulo y NO está en el
plan principal. La fase 03 (`.pyc` precompilados) es lo único del lado
"estructura/empaquetado" que mueve la aguja del INIT, y es marginal.

## Unica mejora menor del zip (opcional)

`uv pip install --target` deja los `.dist-info/` de cada dep en el zip.
Son metadatos no necesarios en runtime. Podarlos reduce el tamaño del
zip ~5-10%. **Impacto en cold: despreciable** (el zip ya está cacheado en
el host tras el primer pull). Solo vale por higiene/tamaño.

- Cambio en `packaging.py`: tras `uv pip install` + `_prune_runtime_provided`,
  borrar `build/*.dist-info/` (excepto los que alguna lib lea en runtime —
  raro; verificar que ninguna dep use `importlib.metadata` en runtime;
  Powertools y Pydantic NO lo necesitan para funcionar).
- Riesgo: alguna dep que use `importlib.metadata.version(...)` en runtime
  fallaría. Mitigación: probar el deploy + invocar en dev antes de
  generalizar.

## Decision

**Diferir esta fase.** No mueve la aguja del cold. Si se quiere por
higiene, hacerla al final, aislada, con verificación de que ningún Lambda
rompe por `.dist-info` faltante. NO bloquea el plan.

## Archivos afectados (si se decide hacer)

### Modificar

- `devtools/serverless/packaging.py` — paso opcional de strip de
  `.dist-info` tras la poda de runtime-provided.
  - Verificar: deploy + invoke de cada Lambda en dev sin error.

[< Medicion](04-fase-medicion-api-e2e.md) | [Siguiente: Commits >](06-commits.md)
