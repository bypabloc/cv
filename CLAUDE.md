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

Stack: 6 apps Astro + nginx reverse proxy + container `e2e` (E2E unificado
Python 3.14 + playwright-python, on-demand contra dev/stage desplegado).
Container names: `portfolio-<servicio>-<env>`.

### Quick start

```bash
pnpm run docker:up         # nginx + 6 apps (modo dev con HMR)
pnpm run docker:ps         # listar containers
pnpm run docker:logs       # tail -f de todos los servicios
pnpm run docker:down       # bajar stack (preserva volúmenes)

python devtools/run.py e2e --module=app --env=dev   # E2E app (sin auth)
python devtools/run.py e2e --env=dev --aws-profile=tfs-dev  # los 3 modulos
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

# E2E unificado (Python, contra dev/stage desplegado):
python devtools/run.py e2e --module=<api|admin|app> --env=dev --aws-profile=tfs-dev

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
├── tests/                # E2E Python (shared + api + admin + app) — comando `e2e`
├── docker/
│   ├── docker-compose/   # {local,dev,test,prod}.yml
│   ├── dockerfiles/      # por ambiente x app
│   ├── nginx/            # configs + error-pages + services-page
│   ├── env/{client,server,dev-cli}/  # env vars por categoria de sensibilidad
│   └── scripts/          # entrypoints sh
├── devtools/             # Python 3.14 + uv (CLI orquestador)
├── serverless/
│   └── lambda/           # backend serverless Python (Lambdas AWS)
│       ├── resources/    # un yaml por recurso compartido (provisionado por devtools)
│       ├── services/     # los 8 Lambdas (auth, contact_form, cv, db,
│       │                 #   send_email, tracking_pixel, tracking_writer, users)
│       └── shared/       # libreria comun (subpaquetes por dominio)
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
| TypeScript 6 (politica raiz) | [.claude/rules/typescript.md](.claude/rules/typescript.md) o skill `typescript-6` | Antes de tocar cualquier `.ts`/`.tsx`/`tsconfig.json`. **Solo TypeScript** en codigo de aplicacion (JavaScript nativo prohibido). **`any` PROHIBIDO** sin excepciones — usar `unknown` con narrow, `satisfies` o Zod `z.infer`. Strict + `noUncheckedIndexedAccess` + `verbatimModuleSyntax`. tsconfig canonicos para Astro 6 / Next 16 / packages. Codemod `ts5to6` para migracion 5.x→6.0 |
| Design System | [.claude/rules/design-system.md](.claude/rules/design-system.md) | Tokens CSS, dark/light, tipografia, fonts |
| YAML data loading | [.claude/rules/yaml-data-loading.md](.claude/rules/yaml-data-loading.md) | Antes de agregar/modificar entry del CV o tocar plugin yaml |
| Docstrings | [.claude/rules/docstring-standard.md](.claude/rules/docstring-standard.md) | Antes de documentar cualquier unidad de codigo |
| Python 3.14 + Ruff | [.claude/rules/python.md](.claude/rules/python.md) o skill `python-devtools` | Antes de tocar `.py` en `devtools/`, `.git-hooks/` o `serverless/`. La skill `python-devtools` tiene el detalle: interprete correcto (`.venv` 3.14 vs `python3` del shell), politica de versiones, PEP 758, estructura |
| Devtools (CLI) | [.claude/rules/devtools.md](.claude/rules/devtools.md) | Antes de agregar/modificar scripts en `devtools/` |
| Verify-before-done | [.claude/rules/verify-before-done.md](.claude/rules/verify-before-done.md) | Antes de reportar trabajo completado |
| Git workflow | [.claude/rules/git-workflow.md](.claude/rules/git-workflow.md) | Antes de commit / push / PR |
| Git hooks | [.claude/rules/git-hooks.md](.claude/rules/git-hooks.md) | Quality gates pre-commit / pre-push |
| Security | [.claude/rules/security.md](.claude/rules/security.md) | Secrets, CSP, headers, supply chain |
| Archivos .env | [.claude/rules/env-files.md](.claude/rules/env-files.md) | NUNCA leer/importar `.env` (incl. `docker/env/**`): extraer solo la key con bash e inyectarla inline al comando |
| Secrets (umbrella) | [.claude/rules/secrets-strategy.md](.claude/rules/secrets-strategy.md) o skill `secrets-management` | Politica unificada de las 3 categorias (`client` -> GH Variables, `server` -> SSM, `dev-cli` -> local). Comando: `python devtools/run.py sync_secrets --env=<X> [--category=...]`. Matriz de decisiones (donde va una key nueva), pre-requisitos por categoria, anti-patrones |
| Client env sync | [.claude/rules/client-env-sync.md](.claude/rules/client-env-sync.md) | Detalle del flujo client (rule hija de secrets-strategy): catalogo, rotacion de Turnstile sitekey, comando `sync_secrets --category=client` |
| Plan format | [.claude/rules/plan-format.md](.claude/rules/plan-format.md) + [.claude/docs/plan-format-large/README.md](.claude/docs/plan-format-large/README.md) | En plan mode o al planificar features. Todo plan vive en `docs/specs/<nombre>/` y trae 4 secciones de ejecucion obligatorias: descomposicion, commits, paralelizacion con worktrees y verificacion E2E iterativa |
| Harness protocol | [.claude/rules/harness-protocol.md](.claude/rules/harness-protocol.md) | Subagentes, feature_list, current/history |
| Orquestacion (workflow/subagents/agents/worktree) | [.claude/rules/orchestration.md](.claude/rules/orchestration.md) o skill `orchestration` | Antes de ejecutar un workflow, diseñar un fan-out, o decidir inline vs subagente vs workflow vs worktree (incl. al crear un plan). CAPS de concurrencia para NO pegar el rate-limit "Server is temporarily limiting requests": **1 workflow a la vez**, **<=4 agentes concurrentes** por workflow en Opus 4.8 (14 -> 429 medido), batching en olas. Politica de modelos: **Opus 4.8 por defecto**, Sonnet 4.6 solo para fan-outs mecanicos de alta concurrencia. Regla de oro: NO 1 agente LLM por tarea deterministica (pytest/lint/build -> Bash) |
| Sesiones en paralelo (multi-ventana + worktrees) | [.claude/rules/parallel-sessions.md](.claude/rules/parallel-sessions.md) | Antes de abrir MAS de una sesion de Claude Code a la vez sobre el mismo repo, o de usar `--worktree`/`EnterWorktree`/`.worktreeinclude`. Modelo de las 3 capas (ventanas VS Code / worktrees / subagentes): multi-tab NO aisla archivos, solo los **worktrees** lo hacen (`claude --worktree <x>` -> `.claude/worktrees/<x>/`). Aislamiento de recursos del monorepo: cada worktree corre su `pnpm install` (store compartido), un `docker:up` por worktree (`COMPOSE_PROJECT_NAME` o env distinto — los puertos/containers `portfolio-<svc>-local`+9970 son fijos), `.worktreeinclude` copia los `.env` gitignored. La cuota es **de cuenta** (rolling 5h + cap semanal): abrir N ventanas NO la multiplica -> max **2-3 sesiones activas a la vez**. Gestion: `claude agents` (Agent View, NO "FleetView") |
| Markdown docs | [.claude/rules/markdown-docs.md](.claude/rules/markdown-docs.md) | Editar archivos de `docs/` |
| Skills (frontmatter) | [.claude/rules/skills.md](.claude/rules/skills.md) | Crear / modificar skills |
| Testing config Claude | [.claude/rules/claude-config-testing.md](.claude/rules/claude-config-testing.md) | Antes de commitear cambios en `.claude/*` |
| Docker stack | [docker/README.md](docker/README.md) | Levantar local, mapping subdominios, env files |
| Tests E2E | [.claude/rules/e2e-testing.md](.claude/rules/e2e-testing.md) o skill `e2e-testing` | Comando `e2e` (Python unico) contra dev/stage; escribir tests en `tests/{api,admin,app}` |
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
| Gestion de Neon (operativa) | [.claude/rules/neon-management.md](.claude/rules/neon-management.md) | Como gestionar Neon: connection string en SSM, migrations Alembic versionadas, branches (via `neonctl`), rollback, operacion de la Lambda `db` con `serverless run --lambda=db --event=events/<X>.json`, seguridad |
| Secrets serverless | [.claude/rules/serverless-secrets.md](.claude/rules/serverless-secrets.md) | Inventario SSM (`/portfolio/*`), KMS key, IAM scopes por Lambda, rotacion de Turnstile/Neon/emails, estado de AWS SES (production access, DKIM/SPF/DMARC) |
| PostgreSQL 18 Analytics | [.claude/docs/postgresql-18-analytics/README.md](.claude/docs/postgresql-18-analytics/README.md) | Schema de las 4 tablas del backend, window functions, partitioning, JSONB, queries dashboard. Complementa skill `postgresql-18` |
| DynamoDB Cache patterns | [.claude/docs/dynamodb-cache/README.md](.claude/docs/dynamodb-cache/README.md) o skill `dynamodb-cache` | Cache TTL + lock distribuido + SWR + tag invalidation. Modulo en `serverless/lambda/shared/cache/` |
| Serverless rate-limit (sin WAF) | [.claude/docs/serverless-rate-limit/README.md](.claude/docs/serverless-rate-limit/README.md) o skill `serverless-rate-limit` | Rate-limit per-IP con DynamoDB (alternativa $0 a AWS WAF). Sliding window weighted, auto-blacklist bot detection, IP white/blacklist, country rules. Modulo en `serverless/lambda/shared/rate_limit/` |
| Backend serverless | [.claude/docs/serverless-backend/README.md](.claude/docs/serverless-backend/README.md) | Recursos gestionados por devtools con AWS CLI directo y estado local (sin SAM ni CloudFormation): recursos compartidos (tablas DynamoDB + API GW, publican identificadores a SSM) + 8 Lambdas Python `lambda-controller` (async via invoke Lambda->Lambda, sin SQS). Flujos ASCII de cada Lambda, schema de tablas DynamoDB + Neon, archivo de estado local. Costo $0/mes (free tier perpetuo, sin WAF, sin CloudWatch Alarms) |
| Devtools serverless CLI | [.claude/docs/serverless-backend/04-deploy-operacion.md](.claude/docs/serverless-backend/04-deploy-operacion.md) | `python devtools/run.py serverless <command>` — opera el backend: `provision-infra`/`list-resources` (los recursos compartidos, provisionados con AWS CLI) y, con `--lambda=<nombre>` o `--path=<dir>`, los Lambdas `lambda-controller` (`run --stage=<env>`, `deploy`, `destroy`, `status`, `tests --type=<unit\|integration\|coverage>`). La DB se opera con `run --lambda=db --event=events/<X>.json`. Mas rate-limit, setup-ssm, metrics |
| Schema PostgreSQL unificado | [docs/diagrams/db-er.mmd](docs/diagrams/db-er.mmd) | Schema relacional unico de Neon en `serverless/lambda/shared/db/`: 35 tablas (CV + datos del visitante) modeladas en SQLAlchemy 2.x, gestionadas por un solo Alembic. La Lambda `db` corre las migraciones. Los Lambdas `contact_form` y `tracking_writer` usan el ORM para la replica analitica a Neon. El seed del CV (YAML -> DB) lo corre la Lambda `db` con el command `seed` |
| Formato de Lambdas Python | [.claude/rules/lambda-controller.md](.claude/rules/lambda-controller.md) + [.claude/docs/lambda-controller/](.claude/docs/lambda-controller/) o skill `lambda-controller` | Patron `operation + action` -> controller (orquestador) + service (logica de negocio), validacion Pydantic, ciclo `preload->validate->execute`, testing unit + integration. Scaffold en `.claude/templates/lambda-controller/`. Cada lambda trae un `manifest.yaml` (manifiesto) que devtools lee directamente para provisionar el Lambda con AWS CLI, y un `pyproject.toml` (PEP 621, deps gestionadas con uv) en vez de `requirements*.txt`. El deploy arma el zip con uv, vendoriza selectivamente los subpaquetes de `serverless/lambda/shared/` que el lambda usa y registra el resultado en un archivo de estado local. Operacion: `serverless run --stage=<env> --lambda=<nombre>` y `serverless tests --type=<tipo> --lambda=<nombre>`. Aplica a los Lambdas Python del backend, NO al frontend Astro |
| Shared-only imports en Lambdas | [.claude/rules/lambda-shared-imports.md](.claude/rules/lambda-shared-imports.md) + [.claude/docs/lambda-shared-imports/](.claude/docs/lambda-shared-imports/) o skill `lambda-shared-imports` | Los `services/*/core/**/*.py` del backend NO importan directamente paquetes externos (pydantic, sqlalchemy, boto3, aws-lambda-powertools, ...): toda dep viaja por `shared.<subpaquete>` que es el portador unico de cada paquete y lo re-exporta. `serverless lint-deps` valida los 2 checks (dedup D-3 + imports prohibidos) con AST scan. Catalogo de portadores + procedimientos para agregar paquete nuevo y migrar service existente. Cero exenciones en `core/`; tests/ exento |
| Config de Lambdas (memoria/timeout) | [.claude/rules/lambda-config.md](.claude/rules/lambda-config.md) | Antes de crear/editar un `manifest.yaml` o diagnosticar un 502/timeout de cold start. `memory`/`timeout` = MINIMO medido y justificado en el comentario del manifest; NUNCA subir memoria para enmascarar imports lentos: cortar imports con carga lazy (PEP 562 en el `__init__` de subpaquetes shared con deps pesadas como fido2). memoria == CPU; el timeout cubre el cold SIN SnapStart restore. Minimos medidos: auth/users/cv 512, contact_form 384, tracking_pixel 256 |
| CI/CD pipeline | [.claude/rules/ci-cd-pipeline.md](.claude/rules/ci-cd-pipeline.md) + [.claude/docs/ci-cd-pipeline/](.claude/docs/ci-cd-pipeline/) o skill `ci-cd-pipeline` | Workflows GitHub Actions del backend serverless y las apps Astro. AWS auth via OIDC (cero secrets), state de devtools en S3, concurrency queue por env. `ci.yml` (lint+build, ~45s); `deploy-backend.yml` (migrate-db -> detect-changes -> deploy-lambdas matrix); `deploy-apps.yml` (matrix 6 niches a Cloudflare Pages multi-env). Mapeo branch -> stage -> IAM role + Pages projects + URLs canonicas |

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
| `orchestration` | Como usar workflow / subagents / agents / worktree y cuando; CAPS de concurrencia (1 workflow a la vez, <=4 agentes) para evitar el rate-limit; politica de modelos (Opus 4.8 default, Sonnet 4.6 acotado); eleccion de primitiva al crear un plan |
| `python-devtools` | Entorno Python del proyecto (`devtools/` + `.git-hooks/`): interprete correcto (`.venv` 3.14 vs `python3` 3.12 del shell), PEP 758, estructura de paquetes, comandos. Invocar ANTES de tocar/verificar cualquier `.py` |
| `research` | Deep research de tecnologías y librerías (skill con web habilitada) |
| `rotate-secrets` | Devtools script `rotate_secrets` para rotar/configurar credenciales de servicios externos (hoy: Cloudflare Turnstile) y escribir `docker/env/{server,client}/.{env}`. Subcommand-style: cada servicio exige sus credenciales como flags explicitas. Paso 1 de la rotacion antes de `serverless setup-ssm` |
| `spec-workflow` | Descomponer features en specs + tareas atómicas |
| `tdd-workflow` | TDD obligatorio (Red-Green-Refactor) antes de implementar |

### Backend AWS serverless (form contacto + tracking pixel)

Skills consolidadas para el backend del portfolio: 8 Lambdas Python 3.13
(auth, contact_form, cv, db, send_email, tracking_pixel, tracking_writer,
users) detras de API Gateway REST + rate-limit per-IP con DynamoDB (sin
WAF), persistencia en DynamoDB On-Demand, replica analitica en Neon
PostgreSQL (escritura inline de contact_form + tracking_writer async via
invoke, sin SQS), email transaccional centralizado en `send_email`
(invocado async), anti-bot con Cloudflare Turnstile. devtools provisiona
cada recurso compartido y cada Lambda con AWS CLI directo, manteniendo el
estado en archivos locales (sin SAM ni CloudFormation). Costo: $0/mes
(todo free tier perpetuo).

| Skill | Uso |
|-------|-----|
| `aws-lambda-python` | Lambda Python 3.13 (managed runtime, Powertools v3, SnapStart, arm64, SAM deploy, IAM least privilege, observability, costs) |
| `aws-api-gateway` | REST API + WAF rate-based per-IP, usage plans, request validators, CORS multi-subdomain, ACM custom domain, defense in depth 5 capas |
| `aws-dynamodb` | 2 tablas (contacts + tracking), On-Demand, TTL 60d, boto3 Decimal/ConditionExpression, IAM scoped, pricing 2026 |
| `aws-ses` | Email transaccional v2 desde Lambda (DKIM/SPF/DMARC en Cloudflare DNS, sandbox→prod approval, bounce/complaint, MJML HTML, free tier 62k/mes) |
| `cloudflare-turnstile` | CAPTCHA alternativa privacy-preserving: 1 sitekey para 6 subdominios, Managed mode form + Invisible tracking, idempotency_key, CSP directives |
| `neon` | Neon serverless PostgreSQL: scale-to-zero, branching git-style, integracion con AWS Lambda Python via psycopg3, free tier 0.5GB + 191.9h compute/mes, vs RDS/Supabase/PlanetScale |
| `postgresql-18` | PostgreSQL 18 (AIO, UUIDv7, virtual generated columns, skip scan, `RETURNING OLD/NEW`, psycopg3) — referencia del motor que usa Neon |
| `dynamodb-cache` | Sistema de cache con DynamoDB TTL: `@cached(ttl)` decorator, lock distribuido (cache stampede prevention), stale-while-revalidate, tag invalidation. Vive en `serverless/lambda/shared/cache/` y se usa desde todas las Lambdas |
| `serverless-rate-limit` | Rate-limiting per-IP self-managed con DynamoDB (alternativa $0/mes a AWS WAF Web ACL que cuesta $7/mes). Sliding window weighted, atomic counters, auto-blacklist bot detection (3+ tokens Turnstile validos en 60s -> blacklist 24h), IP whitelist/blacklist, country rules. Vive en `serverless/lambda/shared/rate_limit/` + 2 tablas DynamoDB |
| `lambda-controller` | Formato para crear/refactorizar Lambdas Python con el patron `operation + action` -> controller (orquestador) + service (logica de negocio), validacion Pydantic, ciclo `preload->validate->execute`, testing unit + integration. Scaffold reproducible en `.claude/templates/lambda-controller/`, docs en `.claude/docs/lambda-controller/`. Pensado para los Lambdas Python del backend serverless |
| `lambda-shared-imports` | Catalogo de portadores shared para los paquetes externos del backend (pydantic, sqlalchemy, boto3, aws-lambda-powertools, ...): que `shared.<subpaquete>` aporta cada paquete y como se importa desde el `core/` del service. Procedimientos para agregar paquete externo nuevo y migrar service con import prohibido. Implementacion del enforcement en `devtools/serverless/import_validator.py` (AST scan integrado en `serverless lint-deps`) |
| `ci-cd-pipeline` | Pipeline CI/CD del portfolio: workflows de deploy del backend serverless (lambdas + migrations) y las apps Astro (Cloudflare Pages multi-env). AWS auth via OIDC, devtools state en S3, concurrency queue por env. Troubleshooting de errores comunes |
| `secrets-management` | Politica unificada de las 3 categorias de secretos del portfolio (`client` -> GH Variables, `server` -> AWS SSM SecureString + KMS, `dev-cli` -> LOCAL-ONLY). Comando hermetico unificado `python devtools/run.py sync_secrets --env=<X> --category=...`. Decision: donde va una key nueva. Rotacion de Turnstile sitekey + secret, Neon URL, etc. Anti-patrones (gh/aws CLI a mano, PUBLIC_* como Secret, sync de dev-cli) |

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
  `diagrams/`, `claude/` — cambia raramente, audiencia: reviewers
- **Harness interno**: `progress/`, `specs/`, `<area>/feature_list.json`,
  `CHECKPOINTS.md` — cambia constantemente, audiencia: el orquestador.
  `docs/specs/<plan>/` es efimero: se elimina al mergear el plan a `dev`

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
- Branches `main`, `master`, `dev`, `stage` están protegidas: el hook
  `protect-branch.sh` bloquea `git push` directo.
- Subdominios `*.localhost` resuelven a 127.0.0.1 por RFC 6761 (no requiere
  editar `/etc/hosts` en el host). Dentro de containers Docker con
  `network_mode: host` tampoco (los containers `feature` y similares
  inyectan las entradas en su `/etc/hosts` desde el entrypoint).
- pnpm 11 requiere `allowBuilds` explicito para `esbuild` + `sharp`
  (ya configurado en `pnpm-workspace.yaml`).
- `compose_exec` siempre invoca con `--user 1000:1000` en apps Astro para
  no crear archivos root-owned en `.vite/` y `.astro/` del bind mount.
- GitGuardian: `.gitguardian.yaml` (raiz, `secret.ignored_paths`) lo respeta
  SOLO `ggshield`; el check del PR (GitHub App) corre server-side y NO lee
  ese archivo — usa la config del dashboard. Ante un falso positivo
  confirmado en un fixture de test: excluir el path en el dashboard o
  mergear con `gh pr merge --admin`. Detalle:
  [.claude/rules/secrets-strategy.md](.claude/rules/secrets-strategy.md)
  (seccion GitGuardian).
