# 08 — Paralelizacion con git worktrees

[<- 07 Commits](07-commits.md) | [Siguiente: verificacion E2E ->](09-verificacion-e2e.md)

## 10. Paralelizacion

### Base secuencial

Los commits 1 y 2 son base: TODOS los worktrees los necesitan.

- Commit 1 — la carpeta del plan.
- Commit 2 — `http_dispatch.py` + `__init__.py` de `shared.lambda_kit`. Es la
  interfaz que consumen los handlers migrados (fase B) y el handler de `cv`
  (fase C). Nadie puede paralelizar antes de que `http_handler` exista y este
  verde.

Tras el commit 2 se puede abrir paralelizacion.

### Tabla de fases worktree-safe

| Worktree | Commits | Archivos (disjuntos) | Colisiones |
|----------|---------|----------------------|------------|
| `wt-handlers` | 3, 4, 5 | `contact_form/`, `tracking_pixel/`, componentes Astro form/tracking | ninguna |
| `wt-cv-repo` | 6 | `shared/db/cv_repository.py` + sus tests | ninguna |

`wt-handlers` y `wt-cv-repo` son disjuntos: el primero toca los Lambdas
existentes + frontend, el segundo solo `shared/db/`. Se ejecutan en paralelo.

Tras mergear el commit 6 (cv_repository), el scaffold de `cv` (commit 7) es
secuencial. Despues:

| Worktree | Commits | Archivos (disjuntos) | Colisiones |
|----------|---------|----------------------|------------|
| `wt-cv-model` | 8 | `cv/core/models/cv.py` + tests | ninguna |
| `wt-cv-service` | 9 | `cv/core/services/cv_service.py` + tests | ninguna |
| `wt-cv-handler` | 10 | `cv/core/handler.py`, `cv/events/*` | ninguna |

Los tres tocan archivos distintos dentro de `cv/core/` — disjuntos. Tras
mergearlos, el commit 11 (controllers) es secuencial porque cada controller
importa el `cv_service` y el `CvQueryModel` ya estabilizados.

### Lo que NO se paraleliza

- Commit 2 — base, todos dependen.
- Commit 7 — scaffold de `cv` (crea `manifest.yaml`, `pyproject.toml`,
  `settings/`): config central del Lambda.
- Commit 11 — controllers: dependen de la interfaz estable de service + model.
- Commit 14 — los 6 `build-public-assets.mjs`: aunque son archivos distintos,
  comparten el cliente `cv-api-client.ts` (commit 13) y conviene un solo
  cambio coherente.
- Commit 15 — verificacion E2E + limpieza: SIEMPRE secuencial, ultimo.

### Como lanzar cada worktree

```bash
# tras commitear la base (commits 1-2) en feature/cv-data-service
git worktree add ../portfolio-wt-handlers feature/cv-data-service
git worktree add ../portfolio-wt-cv-repo  feature/cv-data-service
# cada worktree implementa sus commits, corre su verificacion incremental,
# y se mergea de vuelta a feature/cv-data-service en el orden de la seccion 9
```

Limite: 5-7 agentes concurrentes. Aqui el maximo real es 3 (`wt-cv-model`,
`wt-cv-service`, `wt-cv-handler`) — por debajo del limite.

Continua en [09-verificacion-e2e.md](09-verificacion-e2e.md).
