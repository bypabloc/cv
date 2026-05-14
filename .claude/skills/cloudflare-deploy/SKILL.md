---
name: cloudflare-deploy
description: >
  Cloudflare Pages deployment reference for this Astro 6 portfolio
  monorepo. Covers REST API setup with API tokens (NOT wrangler — wrangler
  cannot create git-connected projects), permission minimums, DNS records
  including CNAME flattening on apex, custom domains with the random
  subdomain suffix gotcha, the monorepo pnpm build config (root_dir=""
  + destination_dir=apps/<app>/dist + pnpm --filter <pkg>...), comparison
  with Vercel and Netlify (commercial use, bandwidth, pricing 2026), and
  the future Workers Static Assets migration path. ALWAYS invoke this
  skill BEFORE answering ANY question about deploying to Cloudflare,
  Cloudflare Pages, custom domains setup, API token permissions for
  Cloudflare, monorepo build commands on Cloudflare, or migrating from
  Vercel/Netlify to Cloudflare. NEVER answer Cloudflare questions from
  training data alone — this project has consolidated 2026 knowledge that
  includes gotchas (HTTP 403 from subdomain suffix, env_vars shape change,
  wrangler limitation) that override generic advice.
  Use when the user says "cloudflare", "cloudflare pages", "cf pages",
  "wrangler", "pages.dev", "api token cloudflare", "custom domain
  cloudflare", "deploy a cloudflare", "deployar a cloudflare",
  "configurar cloudflare", "como deployar este proyecto", "como desplegar
  este proyecto", "donde hostear", "donde hostear el portfolio",
  "subir el sitio", "publicar el sitio", "publicar el portfolio",
  "deployar el portfolio", "cf token", "_headers", "cloudflare dns",
  "route 53 cloudflare", "migrar dns", "nameservers cloudflare",
  "vercel a cloudflare", "netlify a cloudflare", "comparar hosting",
  "que hosting uso", "where to host astro", "free hosting astro",
  "monorepo cloudflare", "pnpm cloudflare", "astro cloudflare",
  "cannot find cwd", "ERR_PNPM_NO_PKG_MANIFEST", "build falla en
  cloudflare", "cloudflare build error", "cloudflare 403", "cloudflare
  http 403", "cloudflare 522", "cert pending", "ssl pending cloudflare",
  "workers static assets", "migrar a workers", "cloudflare workers".
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash(curl:*), Bash(dig:*), Bash(nslookup:*), Bash(pnpm:*), Bash(git:*)
argument-hint: "tema: setup | dns | api-token | gotchas | comparacion | workers | troubleshoot"
metadata:
  version: "1.0"
---

# Cloudflare Pages deployment — knowledge reference

> Conocimiento consolidado sobre el setup de Cloudflare Pages para
> este portfolio (6 proyectos Pages git-connected, 6 subdominios bajo
> `the-full-stack.com`). Toda decision, gotcha y procedimiento esta
> documentado en `.claude/docs/cloudflare/`.

## Pre-requisito OBLIGATORIO

Antes de responder cualquier pregunta sobre Cloudflare, leer la doc
relevante de `.claude/docs/cloudflare/`:

| Tema de la pregunta | Archivo a leer |
|---------------------|----------------|
| Setup general / arquitectura | [01-architecture.md](../../docs/cloudflare/01-architecture.md) |
| API token, permisos, rotacion | [02-api-token.md](../../docs/cloudflare/02-api-token.md) |
| Crear proyectos Pages via REST API | [03-pages-api-setup.md](../../docs/cloudflare/03-pages-api-setup.md) |
| Build command para monorepo pnpm | [04-monorepo-build-config.md](../../docs/cloudflare/04-monorepo-build-config.md) |
| DNS, CNAME apex, custom domains | [05-dns-and-custom-domains.md](../../docs/cloudflare/05-dns-and-custom-domains.md) |
| Errores y troubleshooting | [06-gotchas.md](../../docs/cloudflare/06-gotchas.md) |
| Script Python idempotente | [07-script-idempotente.md](../../docs/cloudflare/07-script-idempotente.md) |
| Comparacion vs Vercel/Netlify | [08-vercel-netlify-vs-cloudflare.md](../../docs/cloudflare/08-vercel-netlify-vs-cloudflare.md) |
| Workers Static Assets (futuro) | [09-workers-static-assets-future.md](../../docs/cloudflare/09-workers-static-assets-future.md) |

Si la pregunta toca multiples temas, leer todos los relevantes y luego
sintetizar.

## Reglas criticas (siempre activas)

1. **NUNCA** recomendar `npx wrangler deploy` para crear proyectos
   git-connected — wrangler v4 NO soporta esa operacion (issue
   [cloudflare/workers-sdk#10972](https://github.com/cloudflare/workers-sdk/issues/10972)).
   Para git-connected, usar REST API directamente.

2. **NUNCA** asumir que `<project_name>.pages.dev` es el subdomain real.
   CF agrega sufijo aleatorio si el nombre esta tomado globalmente.
   Leer el campo `subdomain` del payload del proyecto.

3. **SIEMPRE** usar `root_dir: ""` (vacio) en monorepo pnpm. Combinarlo
   con `destination_dir: "apps/<app>/dist"`. `root_dir = apps/<app>`
   rompe con bug "Cannot find cwd".

4. **SIEMPRE** usar shape `env_vars` (no `environment_variables`) con
   valores `{"type": "plain_text", "value": "..."}` — el shape viejo
   responde 200 pero deja null.

5. **NUNCA** dar al API token mas permisos de los necesarios:
   `Pages:Edit` + `DNS:Edit` + `SSL:Read` + `User:Read`. NUNCA
   `Account Admin` ni `API Token Management`.

6. **SIEMPRE** verificar la skill antes de modificarla con
   `claude --permission-mode bypassPermissions -p` (regla
   [.claude/rules/claude-config-testing.md](../../rules/claude-config-testing.md)).

## Workflow tipico de respuesta

1. Identificar el tema del prompt (setup / DNS / token / error / etc.)
2. Leer el(los) archivo(s) relevante(s) de `.claude/docs/cloudflare/`
3. Responder con:
   - Causa raiz (si es un error)
   - Solucion concreta (no genericos)
   - Comando o snippet ejecutable
   - Verificacion: como confirmar que funciona
4. Si la pregunta cae fuera de scope: derivar a otra skill o decir que
   no esta cubierto

## Atajos rapidos para preguntas frecuentes

### "Como deployo este portfolio a Cloudflare?"

Leer [01-architecture.md](../../docs/cloudflare/01-architecture.md) y
[07-script-idempotente.md](../../docs/cloudflare/07-script-idempotente.md).
Resumen:

1. Crear token en https://dash.cloudflare.com/profile/api-tokens con
   permisos minimos (ver `02-api-token.md`).
2. `cp tmp/cloudflare-creds.env.template tmp/cloudflare-creds.env` y
   completar.
3. `set -a; . tmp/cloudflare-creds.env; set +a`
4. `devtools/.venv/bin/python -m devtools.cloudflare_setup.main all`
5. Verificar con `... main status`

### "Cuanto cuesta?"

$0. Free tier de CF Pages: 500 builds/mes × 6 proyectos = 3000 builds,
bandwidth ilimitado, uso comercial permitido. Vercel/Netlify mas caros
o limitados. Detalle en
[08-vercel-netlify-vs-cloudflare.md](../../docs/cloudflare/08-vercel-netlify-vs-cloudflare.md).

### "Por que el sitio responde HTTP 403?"

Leer [06-gotchas.md](../../docs/cloudflare/06-gotchas.md#4) — tres
causas posibles: (a) CNAME apunta al subdomain sin sufijo, (b) cert SSL
aun emitiendose, (c) A record viejo no eliminado.

### "Migrar el dominio desde Route 53?"

Si los nameservers en AWS Route 53 ya apuntan a `*.ns.cloudflare.com`,
no hay nada que migrar — la zona DNS ya esta en CF, solo el registrar
sigue en AWS (correcto). Verificar con `dig +short NS the-full-stack.com`.

### "Deberia usar Workers Static Assets?"

Hoy no — esperar a Q4 2026 o cuando necesites SSR/Cron/Durable Objects.
Pages production-grade y "set and forget". Detalle en
[09-workers-static-assets-future.md](../../docs/cloudflare/09-workers-static-assets-future.md).

### "El build falla con 'Cannot find cwd' / 'No package.json'"

Causa: `root_dir` mal configurado o CF cacheo un commit viejo. Fix en
[06-gotchas.md](../../docs/cloudflare/06-gotchas.md#1).

## Anti-patrones a evitar

- ❌ Responder desde training data generica de Cloudflare sin leer la
  doc del proyecto
- ❌ Recomendar wrangler para crear git-connected projects
- ❌ Sugerir `root_dir: "apps/<app>"` en monorepo pnpm
- ❌ Hardcodear `<project_name>.pages.dev` como CNAME target
- ❌ Pedir al usuario que de "Account Admin" al token "para simplificar"
- ❌ Recomendar Vercel Hobby para portfolio comercial (prohibido por ToS)
- ❌ Olvidar el `_headers` en `apps/<app>/public/` cuando se discute CSP

## Comandos utiles (smoke test rapido)

```bash
# Status de los 6 proyectos
set -a; . tmp/cloudflare-creds.env; set +a
devtools/.venv/bin/python -m devtools.cloudflare_setup.main status

# Verificar nameservers del dominio
dig +short NS the-full-stack.com

# Verificar que un subdominio responde
for sub in "" www. hub. fintech. architect. leader. vibe.; do
  url="https://${sub}the-full-stack.com"
  printf '%-40s %s\n' "$url" "$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$url")"
done

# Bypass cache DNS local
dig @1.1.1.1 hub.the-full-stack.com
```

## Relacion con otras skills/rules

- `astro-portfolio` — strategy general del portfolio (incluye hosting
  como subtema general)
- `github-actions` — el CI workflow paralelo al deploy de CF
- `dependency-upgrade` — antes de un deploy nuevo, validar deps
- [.claude/rules/security.md](../../rules/security.md) — headers de
  seguridad, CSP, secrets
- [.claude/rules/verify-before-done.md](../../rules/verify-before-done.md)
  — smoke test post-deploy obligatorio

## Cuando NO invocar esta skill

- Pregunta sobre Astro framework en si (usar `astro-portfolio` o
  responder directo)
- Pregunta sobre GitHub Actions workflow (usar `github-actions`)
- Pregunta sobre Workers como entorno de runtime para apps no estaticas
  (esta skill solo cubre el subset de Pages + Workers Static Assets)
- Pregunta sobre otros servicios CF (R2, KV, D1, Stream, Images, etc.)
  que no aplican al deploy estatico del portfolio
