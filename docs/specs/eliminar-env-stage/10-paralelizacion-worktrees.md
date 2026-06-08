# 10 — Paralelización con git worktrees

[← README](README.md)

## Base secuencial (commitear ANTES de paralelizar)

Commits 1-3: plan + CI/CD (`.github/workflows/*`) + config central de envs
(`devtools/serverless/{secrets_catalog,provisioner,state}.py`). Definen el flujo
y la validación de envs de la que todo depende. NO se paralelizan.

## Olas worktree-safe (archivos disjuntos)

- **Ola 1 (≤4):** devtools por-script (commits 4-6), serverless resources +
  manifests (commits 7-8), seo (commit 9). Archivos 100% disjuntos.
- **Ola 2 (≤4):** docs/rules/skills (commits 11-12). `.md` disjuntos.

## NO se paraleliza

- Commits 2-3 (CI/CD + config central).
- Commit 10 (`git rm` docker — depende de 4-9 limpios).
- Commit 13 (sección 11) y toda la **Parte C** (destrucción de infra, por
  bloque).

Cap duro: **≤4 agentes simultáneos**, **1 workflow a la vez**
(`.claude/rules/orchestration.md`). `isolation: 'worktree'` solo si se
paraleliza con agentes que mutan archivos. Esta ejecución se hace inline
(secuencial) por simplicidad y por el bajo riesgo de colisión.
