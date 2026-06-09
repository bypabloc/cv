---
name: subdomain-standard
description: >
  Subdomain naming standard for the-full-stack.com — canonical pattern
  [{component}.]{product}.{env}.{domain} with prod implicit (no env
  label) and dev as the only middle label. Covers naming rules (kebab-case,
  ASCII lowercase, reserved names: www/api/app/admin/mail/status/dev/stage/
  prod/test/localhost/infra/internal/private/vpn/tunnel + portfolio niches
  hub/fintech/architect/leader/vibe/generic), environment conventions
  (dev/prod only — qa/uat/beta/stage/preview prohibited, use dev or
  pages.dev), portfolio personal exception (ONLY the apex the-full-stack.com
  + www is a permanent exception; the 5 niches follow the standard as
  components of product portfolio: {niche}.portfolio.the-full-stack.com),
  wildcard SSL
  strategies (1-level limit, Universal SSL covers *.the-full-stack.com,
  Pages auto-cert per hostname, ACM cert for API Gateway, Advanced
  Certificate for 2-level wildcards), migration plan for the current
  backend serverless (from execute-api.us-east-1.amazonaws.com to
  api.portfolio.the-full-stack.com / api.portfolio.dev.the-full-stack.com)
  and anti-patterns (env as flat suffix dev-faststruct, slug composition
  faststruct-api, qa/uat/beta envs, uppercase, underscores in hostnames).
  ALWAYS invoke this skill BEFORE answering ANY question about subdomain
  naming, hostname structure, environment URL patterns, new product
  hostname, where to put a new service, how to name dev/stage URL,
  reserved hostnames, wildcard SSL planning, or migrating the API Gateway
  custom domain for this portfolio. NEVER answer subdomain naming
  questions from training data alone — this project has a consolidated
  standard with specific reserved words and a portfolio exception that
  overrides generic advice.
  Use when the user says "subdomain standard", "estandar subdominios",
  "convencion subdominios", "naming subdominios", "nombrar subdominio",
  "como nombrar subdominio", "como llamo el subdominio", "patron
  subdominios", "subdomain pattern", "subdomain naming convention",
  "subdomain structure", "new product subdomain", "agregar subdominio",
  "nuevo subdominio", "como crear subdominio nuevo", "donde pongo este
  servicio", "que url uso para", "como llamo la api", "como llamo el
  admin", "subdominio dev", "subdominio stage", "subdominio prod",
  "subdominio environment", "url por ambiente", "dev stage prod url",
  "url dev stage prod", "wildcard ssl", "wildcard cert", "cert wildcard",
  "wildcard *.the-full-stack.com", "ssl multi nivel", "ssl multinivel",
  "advanced cert cloudflare", "acm cert api gateway", "cert para api
  gateway", "custom domain api gateway", "migrar execute-api",
  "ejecute-api a custom domain", "api gateway custom domain", "the
  full stack subdomain", "reserved hostnames", "reservados", "nombres
  reservados", "prohibidos", "que no usar como subdominio", "antipattern
  subdominio", "anti pattern subdomain", "como migrar al estandar",
  "migracion subdomain", "qa subdomain", "uat subdomain", "preview
  subdomain", "beta subdomain", "release candidate url".
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash(curl:*), Bash(dig:*), Bash(nslookup:*)
argument-hint: "tema: pattern | naming | environments | portfolio | wildcards | migration | anti-patterns"
metadata:
  version: "1.0"
---

# Subdomain naming standard — knowledge reference

> Conocimiento consolidado sobre la convencion de subdominios bajo
> `the-full-stack.com`. Toda decision, regla, reserva y plan de
> migracion esta documentado en `.claude/docs/subdomain-standard/`.

## Pre-requisito OBLIGATORIO

Antes de responder cualquier pregunta sobre subdominios, leer la doc
relevante:

| Pregunta del usuario | Leer |
|----------------------|------|
| Que patron uso? Como armo la URL? | `.claude/docs/subdomain-standard/01-pattern.md` |
| Como nombro el product? Que palabras estan reservadas? | `.claude/docs/subdomain-standard/02-naming-rules.md` |
| Como manejo dev/prod? Que pasa con QA/UAT/beta/stage? | `.claude/docs/subdomain-standard/03-environments.md` |
| Por que el portfolio no sigue el patron? Puedo nombrar mi product como un niche? | `.claude/docs/subdomain-standard/04-portfolio-exception.md` |
| Como configuro SSL wildcard? Necesito Advanced Cert? | `.claude/docs/subdomain-standard/05-wildcards-and-certs.md` |
| Como migro el backend de execute-api a custom domain? | `.claude/docs/subdomain-standard/06-migration-backend-api.md` |
| Que NO puedo hacer? Que es anti-pattern? | `.claude/docs/subdomain-standard/07-anti-patterns.md` |

Para preguntas genericas (cualquier mencion del estandar sin tema
especifico), leer primero `README.md` del directorio docs.

## Patron canonico (resumen)

```text
[{component}.]{product}.{env}.{domain}

prod    [{component}.]{product}.the-full-stack.com
dev     [{component}.]{product}.dev.the-full-stack.com
```

## Reglas criticas

- NUNCA prod lleva label de env (`prod.faststruct.the-full-stack.com`
  PROHIBIDO).
- NUNCA env como sufijo flat (`dev-faststruct.the-full-stack.com`
  PROHIBIDO).
- NUNCA usar reservados como product propio: `api`, `app`, `admin`,
  `mail`, `status`, `auth`, `cdn`, `assets`, `static`, `dev`, `stage`,
  `staging`, `prod`, `production`, `test`, `qa`, `uat`, `local`,
  `localhost`, `infra`, `internal`, `private`, `vpn`, `tunnel`, `hub`,
  `fintech`, `architect`, `leader`, `vibe`, `generic`.
- SIEMPRE la unica excepcion permanente es el apex `the-full-stack.com`
  + `www`. Los 5 niches del portfolio siguen el estandar como components
  del product `portfolio` (`{niche}.portfolio.{env}.the-full-stack.com`).
- SIEMPRE solo 2 envs formales: `dev`, prod. Previews por PR
  usan default `<hash>.<project>.pages.dev`.

## Quick decision flow

```text
1. Es el apex del portfolio? -> the-full-stack.com (unica excepcion)
2. Es un niche del portfolio? -> {niche}.portfolio.{env}.{domain}
3. Es servicio de infra atomico? -> {service}.{env}.{domain}
4. Es product con 1 frontend? -> {product}.{env}.{domain}
5. Es product con varios components? -> {component}.{product}.{env}.{domain}
6. Es env temporal de PR? -> default pages.dev (NO extender estandar)
```

## Ejemplos clave

```text
# Producto faststruct
faststruct.the-full-stack.com               (prod, landing)
api.faststruct.the-full-stack.com           (prod, component api)
api.faststruct.dev.the-full-stack.com       (dev, component api)
app.faststruct.dev.the-full-stack.com       (dev, component app)

# Backend portfolio (post-migracion)
api.portfolio.the-full-stack.com            (prod)
api.portfolio.dev.the-full-stack.com        (dev)

# Servicio infra
status.the-full-stack.com                   (prod)
status.dev.the-full-stack.com               (dev)
```

## Validacion regex

```regex
^(?:[a-z][a-z0-9-]*\.)?[a-z][a-z0-9-]*(?:\.dev)?\.the-full-stack\.com$
```

Mas: nombres reservados a rechazar adicionalmente segun
[02-naming-rules.md](../../docs/subdomain-standard/02-naming-rules.md).

## Estado del estandar

- **Adopcion**: 2026-05-15
- **Excepcion permanente**: solo el apex `the-full-stack.com` + `www`.
  Los 5 niches del portfolio siguen el estandar como
  `{niche}.portfolio.the-full-stack.com` (prod) + dev.
- **Migraciones pendientes**: ninguna. El backend ya usa custom domains
  `api.portfolio.{env}.the-full-stack.com` y el frontend prod los
  `{niche}.portfolio.the-full-stack.com`.
