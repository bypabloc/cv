# 01 — Contexto, decisión y AC

[← README](README.md)

## 1. Problema

El portfolio opera 3 ambientes (`dev`, `stage`, `prod`) con promoción
`dev -> stage -> main`. El escalón `stage` ya no aporta y mantiene infra
duplicada que cuesta dinero y complejidad. Se elimina por completo.

## 2. Solución

Rama `feature/eliminar-env-stage` (desde dev) que limpia código/config/CI/docs y
borra los archivos stage-only en commits atómicos → PR → merge a dev. Después
del merge, destruir la infra cloud de stage con confirmación por bloque. Al
final, borrar la rama `stage` y el GH Environment.

### Decisiones clave

- **D1**: limpiar código ANTES de destruir infra (coherencia en todo momento).
- **D2**: destruir infra DESPUÉS del merge, ANTES de borrar la rama stage.
- **D3**: NO renombrar el job "Branch Flow Guard" (required check por nombre).
- **D4**: `${{ outputs.stage }}` (env actual) y `${stage}` placeholder se quedan;
  solo se quita el `case stage)` literal de rama.
- **D5**: `host.includes('.stage.')` en `build-sitemap.ts` se conserva (detector
  genérico no-prod); solo se ajusta el comentario y 2 tests.

## 3. Criterios de Aceptación

- **AC-1**: PR base `main` head `dev` → Branch Flow Guard pasa; no existe head
  `stage`.
- **AC-2**: comando devtools con `--env=stage`/`--stage=stage` → rechazado.
- **AC-3**: `grep -rin "stage"` (entorno) en `serverless/`, `devtools/`,
  `.github/`, `.claude/`, `docker/` → cero (solo `${stage}`/`outputs.stage`).
- **AC-4**: merge a dev → deploy-backend/deploy-apps verdes desplegando solo dev;
  cases `dev`/`prod` intactos.
- **AC-5**: suite unit → ningún test referencia widget/host/manifest stage;
  coverage ≥80% per-file en tocados.
- **AC-6**: `pnpm run build` → exitoso sin `.stage.` en outputs.
- **AC-7 (Parte C)**: `*.stage.the-full-stack.com` → NXDOMAIN; dev y prod → 200.
- **AC-8 (Parte C)**: cero recursos stage en AWS/Cloudflare/Neon/git/GH.

## Inventario real de infra (a destruir en Parte C)

- **AWS** (637423614564, us-east-1, `tfs-dev`): 9 Lambdas `*-stage`, 8 tablas
  DDB `*-stage`, S3 `portfolio-email-templates-stage`, REST API
  `portfolio-api-stage` (`5k8os58pn5`), custom domain
  `api.portfolio.stage.the-full-stack.com`, cert ACM
  `50c750aa-abbf-4b88-885b-17e4d243b439`, 30 SSM `/portfolio/stage/*` (8 SQS
  legacy), 12 LogGroups (2 huérfanos: `portfolio-aggregator-stage`,
  `portfolio-dashboard-api-stage`), IAM role `portfolio-deploy-stage`.
  - GAP: `portfolio-contacts-stage`, `portfolio-tracking-stage` NO en
    `infra-stage.json` → `serverless destroy` NO las borra (delete manual).
- **Cloudflare**: 7 Pages `*-stage`, 9 DNS CNAME `*.stage` (7 Pages +
  `api.portfolio.stage` + `_acm-validations`), widget Turnstile
  `0x4AAAAAADQjTq8AtQXbm3Oq`.
- **Neon**: proyecto `cv` (`late-paper-11192344`), branch `stage`
  (`br-royal-truth-akbys4af`, hijo de dev).
- **GitHub**: rama `stage`, GH Environment `stage`, ruleset rama stage.

## Riesgos

1. Branch Flow Guard required en main esperando `stage` (ALTO) → reescribir
   lógica, no renombrar job.
2. PRs abiertos contra stage (MEDIO) → `gh pr list --base stage` antes de borrar
   la rama.
3. Cert ACM en uso (MEDIO) → borrar DESPUÉS del destroy y de los DNS.
4. Gitignored vs tracked (BAJO): `.stage` env y `.state/*-stage.json` no son
   tracked → solo `rm` de disco, no `git rm`.
