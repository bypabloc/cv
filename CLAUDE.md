# portfolio

> Monorepo de 6 sitios Astro (pnpm workspaces) para el portfolio multi-niche
> de Pablo Contreras (bypabloc). Output estático desplegado en Cloudflare Pages.
> Stack local orquestado por Docker + nginx + devtools (Python 3.14 + uv).

## Sitios

| App | URL producción | Subdominio local (puerto 9970) | Posicionamiento |
| --- | --- | --- | --- |
| `apps/generic` | `the-full-stack.com` | `localhost` (apex) | Full Stack Senior — todas las skills |
| `apps/hub` | `hub.portfolio.the-full-stack.com` | `hub.localhost` | Selector multi-niche con cards |
| `apps/fintech` | `fintech.portfolio.the-full-stack.com` | `fintech.localhost` | Senior Full Stack Fintech LATAM |
| `apps/architect` | `architect.portfolio.the-full-stack.com` | `architect.localhost` | Frontend Architect + Microservicios |
| `apps/leader` | `leader.portfolio.the-full-stack.com` | `leader.localhost` | Tech Lead / Engineering Manager |
| `apps/vibe` | `vibe.portfolio.the-full-stack.com` | `vibe.localhost` | Vibe Coding / Claude Code / Dev tools |
| — | — | `services.localhost` | Indice estático de servicios locales |

> Prod: el apex `the-full-stack.com` (+ `www`) es generic; los 5 niches
> cuelgan del product `portfolio`. dev/stage usan
> `{niche}.portfolio.{env}.the-full-stack.com`. Ver
> [.claude/docs/subdomain-standard/](.claude/docs/subdomain-standard/).

## Packages

| Package | Responsabilidad |
|---------|-----------------|
| `packages/content` | Zod schemas + datos del CV (singleton). Filters + sort por nicho |
| `packages/ui` | Design system, componentes Astro, theme toggle, animaciones |
| `packages/seo` | JSON-LD Person, llms.txt, sitemap, robots.txt builders |
| `packages/cv-pdf` | Render CV a HTML (ATS-friendly) + PDF opcional (Puppeteer) |
| `packages/app-shared` | SitePageLayout + CvSections + AboutSection compartidos |

## Stack

- Astro 6.x (output: 'static') + TypeScript 6 strict
- Biome v2 (lint + format unificado)
- Vitest + happy-dom (unit tests, coverage v8)
- Playwright (E2E, container aislado con chromium + webkit)
- Tailwind v4 (via `@tailwindcss/vite`)
- pnpm **11.0.9** (via corepack)
- Node **24** (Alpine en Docker)
- Python **3.14** + uv (devtools)

NUNCA mezclar `npm` o `yarn` — solo `pnpm`.

## Comandos pnpm (host, sin Docker)

```bash
pnpm install              # instalar deps (allowBuilds: esbuild + sharp)
pnpm run dev              # dev server en paralelo (todas las apps)
pnpm run build            # build de todas las apps
pnpm run preview          # preview del build estático
pnpm run lint             # Biome check
pnpm run lint:fix         # Biome con auto-fix
pnpm run typecheck        # tsc + astro check (recursive)
pnpm run test             # Vitest recursivo en packages
pnpm run test:coverage    # Vitest --coverage en packages
pnpm run clean            # limpia dist, .astro, node_modules/.vite, coverage
```

Filtrar por workspace: `pnpm --filter @portfolio/<app> run <script>`.

## Comandos Docker (proyecto: `portfolio`)

Stack: 6 apps Astro + nginx reverse proxy + container `feature` (Playwright,
on-demand). Container names: `portfolio-<servicio>-<env>`.

### Quick start

```bash
pnpm run docker:up         # nginx + 6 apps (modo dev con HMR)
pnpm run docker:ps         # listar containers
pnpm run docker:logs       # tail -f de todos los servicios
pnpm run docker:down       # bajar stack (preserva volúmenes)

pnpm run feature:up        # container Playwright (profile feature)
pnpm run feature:run       # ejecutar specs E2E
```

### Acceso al stack local

```text
http://localhost:9970            -> apps/generic
http://hub.localhost:9970        -> apps/hub
http://fintech.localhost:9970    -> apps/fintech
http://architect.localhost:9970  -> apps/architect
http://leader.localhost:9970     -> apps/leader
http://vibe.localhost:9970       -> apps/vibe
http://services.localhost:9970   -> indice de servicios
```

| Ambiente | Puerto nginx | Modo Astro |
| --- | --- | --- |
| local | 9970 | dev (HMR via bind mount) |
| dev | 9971 | dev (HMR remoto) |
| test | 9972 | build + preview |
| prod | 9973 | build + preview |

## Comandos devtools (Python CLI)

Entrypoint: `python devtools/run.py <script> [flags...]`. Bootstrap automático
via `uv sync` la primera vez. Ver `python devtools/run.py --help` para
inventario completo.

### Lifecycle Docker

```bash
python devtools/run.py docker up --env=local
python devtools/run.py docker down --env=local
python devtools/run.py docker rebuild --env=local        # down + build --no-cache + up
python devtools/run.py docker restart --env=local
python devtools/run.py docker refresh --env=local        # refresh completo
python devtools/run.py docker ps --env=local
python devtools/run.py docker logs --env=local --follow
python devtools/run.py docker shell --env=local --target=<servicio>
python devtools/run.py docker exec --env=local --target=<servicio> -- <cmd>
```

### Quality (lint/format)

```bash
# Biome en container de la app:
python devtools/run.py docker lint --module=<app> --env=local
python devtools/run.py docker lint-fix --module=<app> --env=local
python devtools/run.py docker format --module=<app> --env=local

# Ruff en host (sin Docker) para devtools/:
python devtools/run.py docker lint --module=devtools --env=local
```

Módulos válidos:

- Frontend: `hub`, `generic`, `fintech`, `architect`, `leader`, `vibe`
- Packages: `pkg-app-shared`, `pkg-content`, `pkg-cv-pdf`, `pkg-seo`, `pkg-ui`
- Python: `devtools`

### Tests

```bash
# Unit + coverage por app/package:
python devtools/run.py test_runner --module=<app> --type=unit
python devtools/run.py test_runner --module=<app> --type=coverage
python devtools/run.py test_runner --module=<app> --type=typecheck

# Para packages: prefijo pkg-
python devtools/run.py test_runner --module=pkg-content --type=unit

# E2E (Playwright contra el stack local):
python devtools/run.py test_runner --module=feature --type=feature --env=local

# Devtools unit tests (host, pytest):
python devtools/run.py test_runner --module=devtools --type=unit
```

### Scan + verify

```bash
python devtools/run.py scan --module=<X> --git-mode=all --only-list
python devtools/run.py verify --all-changed
python devtools/run.py verify --staged --execute --json
```

## Reglas críticas (siempre activas)

- SIEMPRE archivos temporales en `./tmp/` del proyecto, NUNCA `/tmp/` del sistema
- SIEMPRE `rm -f` para eliminar (evita prompts interactivos)
- SIEMPRE tokens del Design System via `var(--color-*)`, NUNCA hex inline
- SIEMPRE fonts self-hosted via `@fontsource/*`, NUNCA Google Fonts CDN
- SIEMPRE TypeScript strict, NUNCA `any` (usar `unknown` con narrow)
- SIEMPRE Conventional Commits en español (subject + body)
- SIEMPRE Node 24 + pnpm 11.0.9 (declarado en `package.json` engines)
- NUNCA atribución de IA en commits, PRs, issues, ni comentarios
- NUNCA `find`, `grep -E/-r/-rn` en Bash (aliases rotos en WSL2): usar
  Glob / Grep / Read / Edit tools
- NUNCA declarar trabajo "listo" sin ejecutar las verificaciones de
  [verify-before-done](.claude/rules/verify-before-done.md)

## Git hooks (pre-commit + pre-push)

Activación automática via `pnpm install` (script `prepare` setea
`core.hooksPath`). Implementados en Python autocontenido (sin dependencia
de devtools/.venv).

### Pre-commit (liviano, <10s)

- `conformance` — Biome lint + format check sobre archivos staged
- `frontend_purity` — prohibe `.js/.jsx/.mjs/.cjs` salvo configs en raíz

### Pre-push (estricto)

- `conformance` — Biome check sobre cambios vs base branch
- `frontend_purity`
- `typecheck` — astro check (per-app) + tsc --noEmit recursivo
- `unit_tests` — Vitest --coverage en packages modificados (>=80% per-file)
- `build` — pnpm build estático de todas las apps

Skip por env: `SKIP_STEPS="build,unit_tests" git push ...`. Config en
[.git-hooks/config.json](.git-hooks/config.json).

## CI (GitHub Actions)

Dos jobs en [.github/workflows/ci.yml](.github/workflows/ci.yml):

1. `quality-gates` (sin Docker): lint + typecheck + unit + build estático
2. `e2e-tests` (con Docker): levanta stack test + corre Playwright

Trigger: PRs a `main`/`master`/`dev`. Limpieza automática de atribución
de IA en PRs via [.github/workflows/clean-pr-attribution.yml](.github/workflows/clean-pr-attribution.yml).

## Estructura del repo

```text
.
├── apps/
│   └── {generic,hub,fintech,architect,leader,vibe}/  # 6 sitios Astro
├── packages/
│   └── {app-shared,content,cv-pdf,seo,ui}/            # 5 workspaces compartidos
├── tests/feature/        # Playwright E2E (config + fixtures + helpers + specs)
├── docker/
│   ├── docker-compose/   # {local,dev,test,prod}.yml
│   ├── dockerfiles/      # por ambiente x app
│   ├── nginx/            # configs + error-pages + services-page
│   ├── env/              # .example + variantes
│   └── scripts/          # entrypoints sh
├── devtools/             # Python 3.14 + uv (CLI orquestador)
├── .git-hooks/           # pre-commit, pre-push, prepare-commit-msg
├── .github/workflows/    # ci.yml, deploy.yml, clean-pr-attribution.yml
├── .claude/              # rules, skills, agents, hooks de Claude Code
├── docs/                 # documentación del proyecto
└── project.yml           # name: portfolio (single source of truth)
```

## Arbol de conocimiento

Antes de trabajar, identifica que contexto necesitas:

| Tema | Archivo | Cuando leer |
|------|---------|-------------|
| Reglas generales | [.claude/rules/general.md](.claude/rules/general.md) | Indice de reglas + estructura del repo |
| Astro + Biome + TS | [.claude/rules/astro-landing.md](.claude/rules/astro-landing.md) | Antes de crear componente / página / utility |
| Design System | [.claude/rules/design-system.md](.claude/rules/design-system.md) | Tokens CSS, dark/light, tipografia, fonts |
| YAML data loading | [.claude/rules/yaml-data-loading.md](.claude/rules/yaml-data-loading.md) | Antes de agregar/modificar entry del CV o tocar plugin yaml |
| Docstrings | [.claude/rules/docstring-standard.md](.claude/rules/docstring-standard.md) | Antes de documentar cualquier unidad de codigo |
| Python 3.14 + Ruff | [.claude/rules/python.md](.claude/rules/python.md) | Antes de tocar `.py` en `devtools/` o `.git-hooks/` |
| Devtools (CLI) | [.claude/rules/devtools.md](.claude/rules/devtools.md) | Antes de agregar/modificar scripts en `devtools/` |
| Verify-before-done | [.claude/rules/verify-before-done.md](.claude/rules/verify-before-done.md) | Antes de reportar trabajo completado |
| Git workflow | [.claude/rules/git-workflow.md](.claude/rules/git-workflow.md) | Antes de commit / push / PR |
| Git hooks | [.claude/rules/git-hooks.md](.claude/rules/git-hooks.md) | Quality gates pre-commit / pre-push |
| Security | [.claude/rules/security.md](.claude/rules/security.md) | Secrets, CSP, headers, supply chain |
| Plan format | [.claude/rules/plan-format.md](.claude/rules/plan-format.md) | En plan mode o al planificar features |
| Harness protocol | [.claude/rules/harness-protocol.md](.claude/rules/harness-protocol.md) | Subagentes, feature_list, current/history |
| Markdown docs | [.claude/rules/markdown-docs.md](.claude/rules/markdown-docs.md) | Editar archivos de `docs/` |
| Skills (frontmatter) | [.claude/rules/skills.md](.claude/rules/skills.md) | Crear / modificar skills |
| Testing config Claude | [.claude/rules/claude-config-testing.md](.claude/rules/claude-config-testing.md) | Antes de commitear cambios en `.claude/*` |
| Docker stack | [docker/README.md](docker/README.md) | Levantar local, mapping subdominios, env files |
| Tests E2E | [tests/feature/README.md](tests/feature/README.md) | Escribir specs Playwright |
| CV (contenido) | [.claude/docs/cv/README.md](.claude/docs/cv/README.md) | Datos del CV (perfil, experiencia, proyectos) |
| Estrategia portfolio 2026 | invocar skill `astro-portfolio` | Decisiones de SEO/GEO/ATS/AI literacy/diseño |
| Deploy Cloudflare Pages | [.claude/docs/cloudflare/README.md](.claude/docs/cloudflare/README.md) o skill `cloudflare-deploy` | Deploy, custom domains, DNS, gotchas, troubleshoot del setup actual |
| Estandar subdominios | [.claude/docs/subdomain-standard/README.md](.claude/docs/subdomain-standard/README.md) o skill `subdomain-standard` | Patron `[{component}.]{product}.{env}.{domain}` para products, components y envs (dev/stage/prod) bajo the-full-stack.com. Reservados, wildcards SSL, plan de migracion del backend |
| AWS Lambda Python 3.13 | [.claude/docs/aws-lambda/README.md](.claude/docs/aws-lambda/README.md) o skill `aws-lambda-python` | Backend serverless: runtime, Powertools v3, cold start, SAM deploy, IAM, costs |
| AWS API Gateway | [.claude/docs/aws-api-gateway/README.md](.claude/docs/aws-api-gateway/README.md) o skill `aws-api-gateway` | REST vs HTTP, throttling per-IP via WAF, CORS, request validation, deploy |
| AWS DynamoDB | [.claude/docs/aws-dynamodb/README.md](.claude/docs/aws-dynamodb/README.md) o skill `aws-dynamodb` | On-demand, TTL, boto3, single-table, GSI, pricing 2026 |
| AWS SES | [.claude/docs/aws-ses/README.md](.claude/docs/aws-ses/README.md) o skill `aws-ses` | Email transaccional v2: DKIM/SPF/DMARC, sandbox→prod, bounces, costos |
| Cloudflare Turnstile | [.claude/docs/cloudflare-turnstile/README.md](.claude/docs/cloudflare-turnstile/README.md) o skill `cloudflare-turnstile` | CAPTCHA alternativa: Managed mode, frontend Astro, validation backend |
| Neon PostgreSQL | [.claude/docs/neon/README.md](.claude/docs/neon/README.md) o skill `neon` | Serverless PG 18, scale-to-zero, branching git-style, psycopg3 en Lambda, vs RDS/Supabase |
| Gestion de Neon (operativa) | [.claude/rules/neon-management.md](.claude/rules/neon-management.md) | Como gestionar Neon: connection string en SSM, runner de migrations versionado, branches, rollback, comandos `serverless db-*`, seguridad |
| PostgreSQL 18 Analytics | [.claude/docs/postgresql-18-analytics/README.md](.claude/docs/postgresql-18-analytics/README.md) | Schema de las 4 tablas del backend, window functions, partitioning, JSONB, queries dashboard. Complementa skill `postgresql-18` |
| DynamoDB Cache patterns | [.claude/docs/dynamodb-cache/README.md](.claude/docs/dynamodb-cache/README.md) o skill `dynamodb-cache` | Cache TTL + lock distribuido + SWR + tag invalidation. Modulo en `serverless/src/common/cache/` |
| Serverless rate-limit (sin WAF) | [.claude/docs/serverless-rate-limit/README.md](.claude/docs/serverless-rate-limit/README.md) o skill `serverless-rate-limit` | Rate-limit per-IP con DynamoDB (alternativa $0 a AWS WAF). Sliding window weighted, auto-blacklist bot detection, IP white/blacklist, country rules. Modulo en `serverless/src/common/rate_limit/` |
| Backend serverless | [serverless/ARCHITECTURE.md](serverless/ARCHITECTURE.md) + [INTEGRATION.md](serverless/INTEGRATION.md) | Estructura + diagramas ASCII + propuesta hibrida DynamoDB+Neon+Cache. Costo $0/mes (todo free tier perpetuo, sin WAF, sin CloudWatch Alarms) |
| Specs serverless | [serverless/specs/README.md](serverless/specs/README.md) | Plan de implementacion atomico en 16 specs (SPEC-000 a SPEC-015): setup, SAM base, common, cache, rate-limit, 5 Lambdas, Neon, frontend, dashboard, runbook. Cada spec con AC BDD + dependencias + verify commands + DoD |
| Devtools serverless CLI | [devtools/serverless/README.md](devtools/serverless/README.md) | `python devtools/run.py serverless <command>` — build, deploy, invoke, logs, db-migrate, db-branch, rate-limit, cache, smoke |

## Skills disponibles

Invocables manualmente con `/<nombre>` o automáticamente según keywords del
prompt. Detalles del frontmatter: [.claude/rules/skills.md](.claude/rules/skills.md).

### Activas en el portfolio (frontend Astro)

| Skill | Uso |
|-------|-----|
| `astro-portfolio` | Referencia obligatoria para cualquier decisión de estructura, SEO, GEO, ATS, diseño o stack del portfolio |
| `animations-css` | Animaciones CSS (scroll-driven, view transitions, micro-interactions) — NO usar libs como motion / gsap / aos |
| `cloudflare-deploy` | Deploy a Cloudflare Pages: REST API, custom domains, DNS, gotchas, comparacion vs Vercel/Netlify |
| `codebase-audit` | Auditoria de calidad: dead code, complexity, duplication, tech debt |
| `dependency-upgrade` | Workflows de upgrade con pnpm (audit, outdated, CVE, majors) |
| `fix-hooks` | Reparar errores de pre-commit / pre-push iterativamente |
| `github-actions` | Workflows CI + testing local con `act` (nektos/act) |
| `mermaid` | Crear / modificar diagramas `.mmd` en `docs/diagrams/` |
| `research` | Deep research de tecnologías y librerías (skill con web habilitada) |
| `spec-workflow` | Descomponer features en specs + tareas atómicas |
| `tdd-workflow` | TDD obligatorio (Red-Green-Refactor) antes de implementar |

### Backend AWS serverless (form contacto + tracking pixel)

Skills consolidadas para el backend del portfolio: 3 Lambdas Python 3.13
en us-west-2 (contact-form, tracking-pixel, turnstile-validator) detras
de API Gateway REST + WAF rate-based, persistencia en DynamoDB
On-Demand, notificacion via SES, anti-bot con Cloudflare Turnstile.
Stack IaC: AWS SAM. Costo estimado: ~$7/mes (dominado por WAF Web ACL).

| Skill | Uso |
|-------|-----|
| `aws-lambda-python` | Lambda Python 3.13 (managed runtime, Powertools v3, SnapStart, arm64, SAM deploy, IAM least privilege, observability, costs) |
| `aws-api-gateway` | REST API + WAF rate-based per-IP, usage plans, request validators, CORS multi-subdomain, ACM custom domain, defense in depth 5 capas |
| `aws-dynamodb` | 2 tablas (contacts + tracking), On-Demand, TTL 60d, boto3 Decimal/ConditionExpression, IAM scoped, pricing 2026 |
| `aws-ses` | Email transaccional v2 desde Lambda (DKIM/SPF/DMARC en Cloudflare DNS, sandbox→prod approval, bounce/complaint, MJML HTML, free tier 62k/mes) |
| `cloudflare-turnstile` | CAPTCHA alternativa privacy-preserving: 1 sitekey para 6 subdominios, Managed mode form + Invisible tracking, idempotency_key, CSP directives |
| `neon` | Neon serverless PostgreSQL: scale-to-zero, branching git-style, integracion con AWS Lambda Python via psycopg3, free tier 0.5GB + 191.9h compute/mes, vs RDS/Supabase/PlanetScale |
| `postgresql-18` | PostgreSQL 18 (AIO, UUIDv7, virtual generated columns, skip scan, `RETURNING OLD/NEW`, psycopg3) — referencia del motor que usa Neon |
| `dynamodb-cache` | Sistema de cache con DynamoDB TTL: `@cached(ttl)` decorator, lock distribuido (cache stampede prevention), stale-while-revalidate, tag invalidation. Vive en `serverless/src/common/cache/` y se usa desde todas las Lambdas |
| `serverless-rate-limit` | Rate-limiting per-IP self-managed con DynamoDB (alternativa $0/mes a AWS WAF Web ACL que cuesta $7/mes). Sliding window weighted, atomic counters, auto-blacklist bot detection (3+ tokens Turnstile validos en 60s -> blacklist 24h), IP whitelist/blacklist, country rules. Vive en `serverless/src/common/rate_limit/` + 2 tablas DynamoDB |

## Convenciones (resumen)

- Componentes Astro: `PascalCase.astro` (ej. `ExperienceCard.astro`)
- Páginas: kebab-case (`user-profile.astro`)
- Utilities: kebab-case (`format-date.ts`)
- Branches: `feature/`, `fix/`, `chore/`, `docs/`, `refactor/`, `test/` con `/` obligatorio
- Tests: mirror de `src/` en `tests/unit/`, BDD-style en `it()` (`Given/When/Then`), asserts EXACTOS
- Coverage mínimo: 80% per-file en archivos modificados
- Comunicación: respuestas técnicas directas, sin validación emocional ni preámbulos

## Documentación (zonas)

`docs/` tiene dos zonas separadas — NO mezclar:

- **Producto** (Knowledge Tree navegable): `cv/`, `guide/`, `design-system/`,
  `diagrams/`, `specs/`, `claude/` — cambia raramente, audiencia: reviewers
- **Harness interno**: `progress/`, `<area>/feature_list.json`,
  `CHECKPOINTS.md` — cambia constantemente, audiencia: el orquestador

Reglas: [.claude/rules/markdown-docs.md](.claude/rules/markdown-docs.md)
y [.claude/rules/harness-protocol.md](.claude/rules/harness-protocol.md).

## Gotchas

- WSL2: `find` esta aliasado a `fd`, `grep -E/-r/-rn` a `rg`. Cada uso
  rompe la ejecución — usar Glob / Grep / Read / Edit tools.
- Hooks en `.claude/hooks/` + `.git-hooks/` son enforcement real; CLAUDE.md
  no enforza por si solo. Ver [.claude/hooks/README.md](.claude/hooks/README.md).
- `attribution.commit` y `attribution.pr` están vacíos en
  [.claude/settings.json](.claude/settings.json) — defensa en profundidad
  contra atribución de IA.
- Branches `main`, `master`, `dev`, `release` están protegidas: el hook
  `protect-branch.sh` bloquea `git push` directo.
- Subdominios `*.localhost` resuelven a 127.0.0.1 por RFC 6761 (no requiere
  editar `/etc/hosts` en el host). Dentro de containers Docker con
  `network_mode: host` tampoco (los containers `feature` y similares
  inyectan las entradas en su `/etc/hosts` desde el entrypoint).
- pnpm 11 requiere `allowBuilds` explicito para `esbuild` + `sharp`
  (ya configurado en `pnpm-workspace.yaml`).
- `compose_exec` siempre invoca con `--user 1000:1000` en apps Astro para
  no crear archivos root-owned en `.vite/` y `.astro/` del bind mount.
