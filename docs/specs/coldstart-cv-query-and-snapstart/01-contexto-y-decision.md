# 01 — Contexto, solucion y criterios de aceptacion

[< README](README.md) | [Siguiente: Fase query cv >](02-fase-query-cv.md)

## 1. Contexto / Problema

El reporte de tiempos del backend muestra:

```text
cv   cv.get (success)   cold 13.918   warm 7.365
auth register.start     cold 11.298
users profile.get       cold  8.512   warm 1.836
contact contact.create  cold  9.777   warm 0.532
```

El usuario pidió reducir el cold "por estructura de archivos/carpetas e
importaciones de `shared`, NO por memoria/config".

### Hallazgos de exploración (datos duros, no suposiciones)

Tras medir en AWS (CloudWatch + `aws lambda`/`apigateway`, cuenta
`637423614564`, `us-east-1`):

1. **El cold de 13.9s no es el cold típico.** El API Gateway de `cv`
   (dev/stage/prod) integra el alias `:live` (SnapStart), cuyo
   `RESTORE_REPORT Restore Duration` es **~963-1262 ms**. El 13.9s es el
   `INIT_REPORT Init Duration` crudo, que solo se paga cuando SnapStart
   **no** restaura (ventana post-deploy + escalado). `api_e2e` no fuerza
   cold ni distingue ambos paths, así que capturó un INIT crudo.

2. **El warm de 7.3s ES real y constante.** `get_full_cv`
   (`serverless/lambda/shared/db/cv_repository.py`) ensambla 9 secciones,
   **cada una abre su propio `db_session()`**, ~45-55 SELECT a Neon en
   **serie**. No hay N+1, pero sí 9 aperturas/cierres de conexión y
   serialización secuencial. `Max Memory Used: 162 MB` de 256 MB: no es
   memoria, es I/O serial + wake de Neon scale-to-zero.

3. **El INIT crudo (7-20s, varianza salvaje) escala con CPU.** A 256 MB
   (~0.16 vCPU) el trabajo de INIT —imports de SQLAlchemy + `warm_db()`
   (`configure_mappers` + `create_engine`) + instanciar `Logger()` y
   `Metrics()` de Powertools en module-scope— se vuelve CPU-starved. La
   varianza (7s a 20s) es típica de eso. SnapStart lo absorbe casi
   siempre, pero conviene acotarlo.

4. **El vendoring del zip está correcto.** `packaging.py` usa
   `uv pip install --python-platform aarch64-manylinux2014
   --only-binary=:all:`, poda `boto3`/`botocore` (el runtime los provee),
   excluye `.venv`/`__pycache__`, y `shared_resolver.py` resuelve el
   cierre transitivo por AST. CodeSize: cv 14.1 MB, auth/users/contact
   18.6-18.8 MB. No hay bug; solo una mejora menor opcional (strip de
   `.dist-info`), de impacto despreciable en cold.

## 2. Solucion propuesta

Atacar las dos palancas reales, en este orden de ROI, sin tocar memoria:

### Decisiones clave

- **Decisión 1 (palanca #1): consolidar la query de `cv` a UN solo
  `db_session()` para las 9 secciones** — hoy abre/cierra 9 conexiones a
  Neon en serie. Reutilizar una sola sesión elimina 8 round-trips de
  apertura + el wake repetido del pooler. Es el cambio de menor riesgo
  con mayor impacto en los 7.3s. Las funciones públicas siguen cacheadas
  individualmente (`@cached`), pero `get_full_cv` (el caso `cv.get`, el
  más lento) pasa a usar una variante interna que comparte sesión.

- **Decisión 2 (palanca #1, profundización): consolidar las secciones
  más caras a menos round-trips con carga en bulk dentro de la misma
  sesión** — `list_experiences` (~9 queries) y `list_projects` (~8) son
  las que dominan. Agrupar sus sub-consultas (traducciones, prioridades,
  niches, bullets/stack) en menos SELECT con `IN (...)` ya parcialmente
  hecho; falta unirlas bajo una sola sesión y, donde aplique, usar
  `selectinload`/`joinedload` para evitar las consultas separadas de
  hidratación.

- **Decisión 3 (palanca #2): bajar el INIT crudo difiriendo trabajo que
  no necesita estar en module-scope** — `warm_db()` se mantiene (es
  intencional para SnapStart), pero `Logger()`/`Metrics()` de Powertools
  y la construcción del `EventModel` se revisan para que el INIT haga lo
  mínimo. Objetivo: INIT crudo < 6s (peor caso acotado).

- **Decisión 4 (medición correcta): instrumentar `api_e2e` para reportar
  cold REAL (restore) separado del INIT crudo** — hoy mezcla ambos. Sin
  esto no se puede verificar la mejora ni distinguir regresiones.

- **Decisión 5 (alcance): trabajar y verificar SOLO en dev.** dev tiene
  el código actual de la rama; stage/prod corren código viejo y NO son
  comparables ni se tocan en este plan. Toda medición antes/después es
  sobre dev.

## 3. Criterios de aceptación (AC)

- **AC-1**: Given `cv.get` (CV completo) sin cache, When se invoca contra
  dev, Then `get_full_cv` usa **un solo `db_session()`** para las 9
  secciones (verificable: una sola apertura de conexión en el log de
  queries o por test que cuenta `db_session()` invocaciones).
- **AC-2**: Given `cv.get` warm sin cache, When se mide con `api_e2e`,
  Then el tiempo de respuesta baja de 7.3s a **< 2.0s** en dev.
- **AC-3**: Given las funciones públicas de `cv_repository`, When se
  invocan individualmente (`cv.experiences`, `cv.projects`, etc.), Then
  siguen devolviendo **exactamente el mismo dict** que hoy (sin regresión
  de contrato — tests existentes verdes).
- **AC-4**: Given un cache HIT de `cv.get`, When se invoca, Then NO toca
  Neon y responde < 0.1s (sin cambio respecto a hoy).
- **AC-5**: Given el INIT crudo de `cv` (sin SnapStart restore), When se
  mide en `$LATEST`, Then baja a **< 6s** (acotar el peor caso).
- **AC-6**: Given `api_e2e`, When corre contra dev, Then reporta el cold
  REAL (con `Restore Duration` si SnapStart restauró) **separado** del
  INIT crudo, no un único número ambiguo.
- **AC-7**: Given el deploy de `cv` en dev, When termina, Then el API
  Gateway sigue integrando `:live` y `SnapStart.OptimizationStatus=On`
  (sin regresión de SnapStart).
- **AC-8**: Given los cambios en `shared.db`, When se corre
  `serverless lint-deps --lambda=cv` y los tests, Then pasan (dedup D-3 +
  imports concretos + coverage >= 80% per-file).
- **AC-9**: Given el redeploy EN DEV de los Lambdas que importan
  `shared.db` (cv, auth, users, contact_form, tracking_writer), When se
  verifican contra dev, Then ninguno regresiona (las queries de
  auth/users/contact siguen ok). stage/prod quedan fuera de scope: corren
  código viejo y no son comparables.

## 4. Diagrama de flujo (antes y despues)

### Antes (`get_full_cv`)

```text
cv.get
  -> get_full_cv()
       -> get_profile()        -> db_session() [abre/cierra]  ~0.8s
       -> list_experiences()   -> db_session() [abre/cierra]  ~1.3s (9 queries)
       -> list_projects()      -> db_session() [abre/cierra]  ~1.4s (8 queries)
       -> list_certificates()  -> db_session() [abre/cierra]  ~0.8s
       -> list_awards()        -> db_session() [abre/cierra]  ~0.9s
       -> list_education()     -> db_session() [abre/cierra]  ~0.7s
       -> list_languages()     -> db_session() [abre/cierra]  ~0.7s
       -> list_references()    -> db_session() [abre/cierra]  ~0.7s
       -> list_skill_cats()    -> db_session() [abre/cierra]  ~1.0s
  TOTAL ~7.3s (9 conexiones, serial)
```

### Despues (`get_full_cv` con sesion compartida)

```text
cv.get
  -> get_full_cv()
       -> with db_session() as s:          [UNA conexion]
            _profile(s) ; _experiences(s) ; _projects(s) ; ...
       (mismas queries, una sola conexion, sin 8 wakes de pooler)
  TOTAL objetivo < 2.0s
```

## 5. Diagrama ER

N/A — no hay cambios de schema. Solo cambia cómo se consulta el schema
existente.

[< README](README.md) | [Siguiente: Fase query cv >](02-fase-query-cv.md)
