# 02 — Fase query cv (palanca #1, ROI mayor)

[< Contexto](01-contexto-y-decision.md) | [Siguiente: INIT/imports >](03-fase-init-imports.md)

> El warm de `cv.get` (7.3s) es el costo real y constante. Esta fase lo
> ataca SIN tocar memoria. Cubre AC-1, AC-2, AC-3, AC-4.

## Diagnostico preciso

`serverless/lambda/shared/db/cv_repository.py` (860 líneas):

- `get_full_cv()` llama a las 9 funciones de sección.
- Cada función pública (`get_profile`, `list_experiences`, ...) hace
  `with db_session() as session:` — abre y cierra **su propia** conexión.
- Con `NullPool` (`shared/db/session.py:32`), cada `db_session()` crea una
  conexión nueva a Neon. 9 secciones = 9 conexiones nuevas en serie. Cada
  apertura paga: TLS handshake + auth + el wake del pooler de Neon si
  estuvo idle.
- Las funciones más caras (`list_experiences` ~9 queries, `list_projects`
  ~8) ya hidratan en bulk (`IN (...)`), pero dentro de su propia sesión.

## Estrategia (incremental, sin romper contrato)

### Paso A — separar "lógica de query" de "apertura de sesión"

Para CADA función pública de sección, extraer una variante interna que
**recibe la `Session`** en vez de abrirla:

```python
# antes
def get_profile(*, locale: str) -> dict[str, Any]:
    with db_session() as session:
        return _profile_query(session, locale=locale)  # ya existe la logica

# despues: separar
def _profile_on_session(session: Session, *, locale: str) -> dict[str, Any]:
    ...  # MISMA logica que hoy, pero usa la session pasada

def get_profile(*, locale: str) -> dict[str, Any]:
    with db_session() as session:
        return _profile_on_session(session, locale=locale)
```

Esto NO cambia el comportamiento de las funciones públicas (siguen
abriendo su sesión) — solo extrae la lógica para reusarla. Los tests
existentes de cada función siguen verdes (AC-3).

### Paso B — `get_full_cv` usa UNA sola sesion

```python
def _full_cv_on_session(
    session: Session, *, niche: str | None, locale: str
) -> dict[str, Any]:
    return {
        'profile': _profile_on_session(session, locale=locale),
        'experiences': _experiences_on_session(session, niche=niche, locale=locale),
        'projects': _projects_on_session(session, niche=niche, locale=locale),
        'certificates': _certificates_on_session(session, niche=niche),
        'awards': _awards_on_session(session, niche=niche, locale=locale),
        'education': _education_on_session(session, niche=niche, locale=locale),
        'languages': _languages_on_session(session, niche=niche, locale=locale),
        'references': _references_on_session(session, niche=niche, locale=locale),
        'skillCategories': _skill_categories_on_session(session, niche=niche, locale=locale),
    }


def get_full_cv(*, niche: str | None, locale: str) -> dict[str, Any]:
    with db_session() as session:
        return _full_cv_on_session(session, niche=niche, locale=locale)
```

Resultado: `cv.get` pasa de 9 conexiones a **1**. Mismas queries, mismo
dict de salida. Elimina 8 aperturas de conexión + 8 oportunidades de wake
del pooler. Esperado: la mayor parte de la mejora de 7.3s -> objetivo.

### Paso C (si el objetivo < 2.0s no se alcanza con A+B) — consolidar SELECT

Solo si las mediciones tras A+B no bajan de 2.0s. Para `list_experiences`
y `list_projects`, reemplazar las consultas separadas de hidratación
(traducciones, prioridades, niches, bullets) por `selectinload`/
`joinedload` en una sola query con la relación ORM, o por menos SELECT
agrupados. Es más invasivo: hacerlo después de medir A+B, una sección a
la vez, con su test verde.

## Sobre el cache (`@cached`) — NO se rompe

Las funciones públicas siguen decoradas con `@cached` (ttl 15min, SWR
24h). El cambio es solo cómo abren la sesión cuando hay cache MISS. El
cache HIT (AC-4) no toca esta ruta: responde antes de llamar a la función
envuelta. `functools.wraps` se preserva (las variantes `_*_on_session`
son internas, sin decorar).

## Archivos afectados

### Modificar

- `serverless/lambda/shared/db/cv_repository.py` — extraer 9 variantes
  `_*_on_session(session, ...)`, agregar `_full_cv_on_session`, y que
  `get_full_cv` use una sola sesión. Las 9 públicas delegan en su
  variante interna.
  - Verificar: `python devtools/run.py serverless tests --type=unit --shared`
  - Verificar: el dict de salida de cada función es idéntico (tests
    existentes de `cv_service`/repositorio verdes).

### Crear (tests)

- `serverless/lambda/shared/tests/unit/shared/db/test_cv_full_uses_single_session.py`
  — test que mockea/cuenta las invocaciones de `db_session()` y asegura
  que `get_full_cv` la abre **una sola vez** (AC-1). BDD-style
  Given/When/Then, assert exacto (`== 1`).
  - Verificar: el test pasa y falla si se revierte el cambio.

## Tests requeridos

### 6.A TDD flows

- `WHEN get_full_cv(niche='fintech', locale='es') THEN db_session se abre exactamente 1 vez [AC-1]`
- `WHEN get_full_cv THEN el dict tiene las 9 keys con el mismo contenido que la suma de las 9 funciones [AC-3]`
- `WHEN cache HIT de cv.get THEN no se llama a ninguna _*_on_session [AC-4]`

### 6.B Unit (Vitest no aplica — es Python)

- `python devtools/run.py serverless tests --type=coverage --lambda=cv` >= 80%
- `python devtools/run.py serverless tests --type=unit --shared`

## Riesgos

- **Transacción larga única**: con una sola sesión, las 9 secciones
  comparten transacción. Como todo es read-only (`SELECT`), no hay riesgo
  de lock de escritura. Neon tolera la transacción de lectura.
- **Memoria**: cargar las 9 secciones en una sesión NO sube el pico (los
  dicts ya se materializan igual; `Max Memory 162 MB` deja headroom).

[< Contexto](01-contexto-y-decision.md) | [Siguiente: INIT/imports >](03-fase-init-imports.md)
