# Eliminar el entorno `stage`

> Plan **Large**: elimina por completo el entorno de despliegue `stage` del
> portfolio (código + config + CI/CD + docs + infra cloud). El flujo de
> promoción pasa de `dev -> stage -> main` a `dev -> main` directo. Resultado:
> modelo de **2 entornos** (`dev` + `prod`).

## Contexto

`stage` era el escalón intermedio del flujo de promoción. El usuario decidió
eliminarlo: no aporta y mantiene infra duplicada (7 Pages projects, 9 Lambdas,
~16 recursos AWS, 1 branch Neon, 1 widget Turnstile). `main` sigue siendo prod;
no se renombran ramas.

Decisiones tomadas:

1. Flujo resultante `dev -> main` directo.
2. Se EJECUTA la destrucción de la infra cloud de stage (AWS + Cloudflare +
   Neon) con confirmación por bloque.
3. Se elimina TODO lo de stage, incluido el widget Turnstile y el cert ACM del
   API GW de stage.

## Índice (cuándo leer)

| Archivo | Cuándo leer |
|---------|-------------|
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Contexto, solución, criterios de aceptación (AC), inventario real de la infra |
| [09-commits.md](09-commits.md) | Listado de los 13 commits incrementales |
| [10-paralelizacion-worktrees.md](10-paralelizacion-worktrees.md) | Qué fases son worktree-safe y el orden |
| [11-verificacion-e2e.md](11-verificacion-e2e.md) | Verificación E2E + destrucción de infra (Parte C) |

## Reglas críticas

- Implementar SIEMPRE en `feature/eliminar-env-stage` (desde dev). NUNCA sobre
  dev/stage/main.
- **NO renombrar** el job "Branch Flow Guard" (es required check en main por
  nombre); solo reescribir su lógica (PR a main viene de `dev`).
- En CI, `${{ outputs.stage }}` (env actual: dev/prod) y `${stage}` placeholder
  en serverless **se quedan**; solo se quita el `case stage)` literal de rama.
- Limpiar código ANTES de destruir infra; destruir infra ANTES de borrar la rama
  stage + GH Environment.
- Push + PR SOLO con la batería de la sección 11 (Parte A+B) en verde.

## Estado por fase

| Fase | Commit(s) | Estado |
|------|-----------|--------|
| Plan | 1 | en curso |
| CI/CD (base) | 2 | pendiente |
| devtools/serverless central (base) | 3 | pendiente |
| devtools CLI por-script | 4-6 | pendiente |
| serverless infra-as-code | 7-8 | pendiente |
| frontend seo | 9 | pendiente |
| git rm docker stage-only | 10 | pendiente |
| docs/rules/skills | 11-12 | pendiente |
| verificación + destrucción infra | 13 + Parte C | pendiente |

## Ciclo de vida

Esta carpeta es efímera: el commit 13 la elimina con `git rm -r`.
