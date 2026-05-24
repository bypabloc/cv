# 06 — Paralelizacion con git worktrees

[← Commits](05-commits.md) | [Siguiente: Verificacion E2E →](07-verificacion-e2e.md)

## Base secuencial

Estos commits NO se pueden paralelizar — todo el resto del trabajo
depende de ellos:

| Commit | Razon |
|---|---|
| C1 | Crea la spec misma; sin esto no hay roadmap. |
| C2 | Crea la migration Alembic. Los modelos ORM de C3 deben matchear el schema final. |
| C3 | Cambia los modelos ORM. Sin esto los services no compilan. |
| C4 | Helper `ensure_session_and_visit`. C6 y C7 lo importan. |
| C5 | Helper `niche_from_origin`. C7 lo importa. (Se puede mergear paralelo con C4 — archivos disjuntos — pero ambos son rapidos asi que en secuencia es fine.) |

Total base secuencial: **5 commits**.

## Fases paralelizables

Tras la base, C6 y C7 son worktree-safe:

| Fase | Archivos (disjuntos) | Worktree | Owner sugerido |
|---|---|---|---|
| **F-tracking** | `services/tracking_pixel/**` + sus tests | `wt-tracking/` | Dev A |
| **F-contact** | `services/contact_form/**` + sus tests + `shared/http/niche.py` (este ultimo en C5, ya base) | `wt-contact/` | Dev B |

Ambas ramas:
- Parten del SHA del C5 (base secuencial mergeada).
- No tocan archivos en comun (`tracking_pixel/` vs `contact_form/`
  son carpetas hermanas).
- Cada una corre su propia bateria de tests (`serverless tests
  --type=unit --lambda=<lambda>` + integration).
- Al terminar, se hace `git merge wt-tracking` y luego `git merge
  wt-contact` (o al reves) en la rama principal `feature/sessions-normalize`.

## Lo que NO se paraleliza

- C2 + C3 (migration + modelos): un solo dev, secuencial. Cambios
  estrechamente acoplados.
- C4 (helper): unico, comparte `shared/db/repository.py` con futuros
  cambios.
- C8 (verificacion E2E + cleanup): siempre el ultimo, requiere todo lo
  anterior mergeado en la rama.

## Comandos para lanzar worktrees

```bash
# Estando en feature/sessions-normalize (con C1..C5 commiteados):
git worktree add wt-tracking feature/sessions-normalize-tracking
git worktree add wt-contact  feature/sessions-normalize-contact

# Dev A trabaja en wt-tracking/, Dev B en wt-contact/.
# Cada uno hace su commit (C6 o C7) en su rama hija.

# Al terminar:
cd ../portfolio  # vuelve al worktree principal
git merge feature/sessions-normalize-tracking
git merge feature/sessions-normalize-contact
git worktree remove wt-tracking
git worktree remove wt-contact

# Continuar con C8 desde la rama principal.
```

## Regla de tabla de colisiones

Antes de aceptar el merge en la rama principal, verificar:

- ¿Algun archivo aparece en ambos worktrees? -> conflicto seguro,
  re-planificar.
- ¿Algun archivo de `shared/` aparece en algun worktree? -> ese
  worktree NO puede paralelizar con otros que dependan del mismo
  shared (defensa contra Interface Stability rota). En este plan,
  shared/ esta tocado solo en C3, C4 y C5 (base secuencial) — NUNCA
  en F-tracking ni F-contact.

## Anti-patron

- Lanzar F-tracking antes de C4 commiteado (rompe Interface Stability:
  el helper aun no existe).
- Hacer F-tracking edits a `shared/db/repository.py` o
  `shared/db/models/` (debe quedar congelado tras C3/C4).
- Hacer F-contact edits a `shared/http/niche.py` (debe quedar
  congelado tras C5).

## Decision para esta corrida

Trabajaremos **lineal** (sin worktrees). El alcance es chico
(~6 commits efectivos tras la base), 1 dev, y el ahorro de paralelizar
es marginal vs. el costo de gestionar 2 worktrees + 2 PR-internos.

Si en una corrida futura el plan crece (mas Lambdas afectados), se
puede activar el modelo de paralelizacion de arriba.

[← Commits](05-commits.md) | [Siguiente: Verificacion E2E →](07-verificacion-e2e.md)
