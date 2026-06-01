# 06 — Commits (seccion 9)

[< Vendoring opcional](05-fase-vendoring-opcional.md) | [Siguiente: Worktrees >](07-paralelizacion-worktrees.md)

> Commits incrementales, cada uno deja el repo verde (lint + typecheck +
> tests del scope). Conventional Commits en español, sin atribución de IA.
> Cada commit ejecuta su verificación ANTES de commitear.

## Secuencia

### C1 — `docs(specs): plan cold-start cv query + snapstart`

- Agrega `docs/specs/coldstart-cv-query-and-snapstart/` (este plan).
- Verificar: `pnpm exec biome check docs/` no aplica (md); revisar links.

### C2 — `refactor(cv): extrae variantes _*_on_session en cv_repository`

- Paso A de la fase 02: cada función pública de sección delega en una
  variante interna `_*_on_session(session, ...)`. Comportamiento idéntico.
- Cubre la base de AC-1/AC-3.
- Verificar: `python devtools/run.py serverless tests --type=unit --shared`
- Verificar: `python devtools/run.py serverless lint-deps --shared`

### C3 — `perf(cv): get_full_cv usa una sola db_session para las 9 secciones`

- Paso B: `_full_cv_on_session` + `get_full_cv` con una sola sesión.
- Test nuevo `test_cv_full_uses_single_session.py` (AC-1).
- Cubre AC-1, AC-2 (parcial), AC-3, AC-4.
- Verificar: `python devtools/run.py serverless tests --type=coverage --lambda=cv` >= 80%
- Verificar: tests de `cv_service` existentes verdes (sin regresión).

### C4 — `perf(cv): consolida SELECT de experiences/projects` (CONDICIONAL)

- Paso C: solo si tras C3 la medición no baja de 2.0s. `selectinload`/
  menos SELECT en las 2 secciones más caras.
- Cubre AC-2 (cierre).
- Verificar: tests verdes + medición `api_e2e` < 2.0s.

### C5 — `feat(api_e2e): desglosa cold real (restore) vs INIT crudo`

- Fase 04: correlación CloudWatch en `api_e2e`, columnas restore/init.
- Cubre AC-6.
- Verificar: `python devtools/run.py serverless tests --type=unit --module=devtools`
- Verificar: `python devtools/run.py api_e2e --env=dev` muestra el desglose.

### C6 — `perf(serverless): precompila .pyc en el zip de deploy` (CONDICIONAL)

- Fase 03 palanca A: `compileall` del `build/` + incluir `.pyc`.
- Solo si la medición del INIT (palanca C de fase 03) muestra que la
  compilación de bytecode pesa.
- Cubre AC-5.
- Verificar: deploy dev + INIT crudo medido baja (CloudWatch).

### C7 — `chore(serverless): strip .dist-info del zip` (OPCIONAL, diferible)

- Fase 05. Solo higiene. Diferible o se omite.
- Verificar: deploy + invoke de cada Lambda en dev sin error.

### C8 — `test(cv): verificacion E2E cold/warm antes-despues + limpieza plan`

- Sección 11: bateria completa, medición antes/después documentada.
- Incluye `git rm -r docs/specs/coldstart-cv-query-and-snapstart/` (la
  carpeta del plan es efímera; se elimina al cerrar).
- Verificar: TODA la batería de la sección 11 en verde.

## Regla por commit

Cada commit deja verde: `serverless lint-deps` + `serverless tests` del
scope tocado. C6/C7 además requieren un deploy a dev exitoso. El push +
PR ocurren SOLO tras C8 con la sección 11 completa en verde.

## PR

Un solo PR `feature/serverless-coldstart-refactor -> dev` (la rama ya
existe). Body con: Problema (cold ambiguo + query 7.3s), Solución (query
1 sesión + medición correcta + .pyc), Cómo probar (la batería de la
sección 11), TODO (stage/prod siguen en SAM; consolidación agresiva de
SELECT si se difirió C4).

> Nota: la rama `feature/serverless-coldstart-refactor` ya tiene 5 commits
> previos (refactor SQS->invoke). Estos commits se suman; el PR puede ser
> el mismo si aún no se mergeó, o uno nuevo desde `dev` si ya se cerró.
> Verificar el estado de la rama antes de C1.

[< Vendoring opcional](05-fase-vendoring-opcional.md) | [Siguiente: Worktrees >](07-paralelizacion-worktrees.md)
