# 11 — Verificación E2E iterativa

[← README](README.md)

## Parte A — refactor de tests

- `rg -l "stage"` en `tests/` y `packages/*/tests/` → cero referencias al
  entorno (solo genéricos).
- Ajustar `packages/seo/tests/unit/{build-sitemap,build-headers}.test.ts`.

## Parte B — batería local (GATE del push/PR; bucle "no parar hasta verde")

- `actionlint .github/workflows/*.yml`
- `pnpm exec biome check .` · `pnpm exec tsc --noEmit` · `pnpm exec astro check`
- `pnpm exec vitest run --coverage` (≥80% per-file en tocados)
- `pnpm run build`
- `python devtools/run.py <scripts> --help` sin stage; `--env=stage` y
  `--stage=stage` rechazados
- `grep -rin` global del entorno stage = cero (salvo genéricos documentados)
- **Solo con todo verde: `git push` + PR + merge a dev.**

## Parte C — despliegue real + DESTRUCCIÓN de infra (post-merge, por bloque)

### C.1 — dev/prod siguen sanos (tras merge a dev)

- Workflows `deploy-backend`/`deploy-apps` del merge a dev: jobs verdes.
- `curl` 200 + marcador a URLs de dev (api.portfolio.dev + 7 apps).

### C.2 — Destruir AWS (`tfs-dev`, us-east-1), por bloque

1. `serverless destroy --stage=stage --yes --aws-profile=tfs-dev`.
2. GAP1: `aws dynamodb delete-table` `portfolio-{contacts,tracking}-stage`.
3. GAP2: `aws ssm delete-parameters` de `/portfolio/stage/*`.
4. GAP3: delete LogGroups huérfanos `portfolio-{aggregator,dashboard-api}-stage`.
5. GAP4: `aws iam delete-role-policy`+`delete-role` `portfolio-deploy-stage`.
6. GAP5: cert ACM `50c750aa-...` es el WILDCARD `*.the-full-stack.com`
   COMPARTIDO por dev y prod → **NO borrar** (rompería dev/prod). Solo borrar
   un cert exclusivo de `api.portfolio.stage` si existe uno distinto.
7. GAP6: `aws sqs list-queues` → borrar colas stage reales si existen.
8. GAP7: `rm` `serverless/lambda/.state/*-stage.json` (gitignored).

### C.3 — Destruir Cloudflare (REST API), por bloque

1. 7 Pages: `DELETE /pages/projects/{niche,admin}-stage`.
2. 9 DNS CNAME `the-full-stack.com`: 7 Pages + 2 API GW.
3. Widget Turnstile `0x4AAAAAADQjTq8AtQXbm3Oq`.

### C.4 — Destruir Neon

- `delete_branch` `stage` (`br-royal-truth-akbys4af`) en proyecto `cv`.

### C.5 — Borrar rama stage + GH Environment (ÚLTIMO)

- `gh pr list --base stage` → cerrar/re-targetear a dev.
- `git push origin --delete stage` + `git branch -D stage`.
- GH Environment `stage`; ruleset rama stage; confirmar guard en main.

### C.6 — Verificación final (bucle "no parar")

- `dig`/`curl` `*.stage.the-full-stack.com` → NXDOMAIN.
- AWS/Cloudflare/Neon: cero recursos stage.
- `curl` 200 a dev y prod (re-confirmar).
