# 07 — Paralelizacion con git worktrees (seccion 10)

[< Commits](06-commits.md) | [Siguiente: Verificacion E2E >](08-verificacion-e2e.md)

> Qué se puede paralelizar con worktrees/subagentes y qué no. Respeta el
> CAP de orquestación del repo: <=4 agentes concurrentes, 1 workflow a la
> vez (ver `.claude/rules/orchestration.md`).

## Base secuencial (NO paralelizable)

- **C1** (carpeta del plan) — primero, todos parten de aquí.
- **C2** (extraer `_*_on_session`) y **C3** (una sola sesión) — tocan el
  MISMO archivo (`cv_repository.py`) en secuencia lógica: C3 depende de
  C2. NO paralelizables entre sí.

## Fases worktree-safe (archivos disjuntos)

Tras C3, estas fases tocan archivos distintos y pueden ir en paralelo en
worktrees separados (olas de <=4):

| Fase | Archivos | Worktree-safe con |
|---|---|---|
| C4 (consolidar SELECT) | `cv_repository.py` | NO con C2/C3 (mismo archivo) |
| C5 (api_e2e desglose) | `devtools/api_e2e/*` | SÍ — disjunto de cv_repository |
| C6 (.pyc en zip) | `devtools/serverless/packaging.py` | SÍ — disjunto |
| C7 (strip dist-info) | `devtools/serverless/packaging.py` | NO con C6 (mismo archivo) |

Ola posible tras C3: **C5 + C6 en paralelo** (archivos disjuntos:
`api_e2e/` vs `packaging.py`). C4 va en la rama principal (mismo archivo
que C2/C3). C7 va después de C6 (mismo archivo).

## Que NO se paraleliza

- La medición/deploy a dev (C6, sección 11) — un solo entorno dev, los
  deploys de `cv` se serializan (el provisioner usa estado local +
  publish-version; deploys concurrentes del mismo Lambda corromperían el
  estado).
- La sección 11 (verificación E2E final) — siempre secuencial, al final.

## Eleccion de primitiva

- C2/C3/C4: **inline** (mismo archivo, secuencia lógica, requiere juicio).
- C5/C6: candidatos a **subagente** o worktree si se ejecutan en paralelo,
  pero son cambios chicos — probablemente inline es más simple.
- La verificación (correr pytest/deploy/api_e2e) es **determinista**: va
  en **Bash**, NUNCA 1 agente LLM por suite (regla de orquestación).

`isolation: 'worktree'` SOLO si se decide ejecutar C5+C6 con agentes
concurrentes que muten archivos. Para este plan, dado el tamaño, la
ejecución **secuencial inline** es lo razonable. Worktrees son
overkill aquí.

[< Commits](06-commits.md) | [Siguiente: Verificacion E2E >](08-verificacion-e2e.md)
