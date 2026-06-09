# 03 - Environments (dev / prod)

> [<- 02-naming-rules](./02-naming-rules.md) | [04-portfolio-exception ->](./04-portfolio-exception.md)

## 2 environments formales

| Env | Label en URL | Proposito | Datos | Acceso |
|-----|--------------|-----------|-------|--------|
| **prod** | (vacio) | Production estable, publica | Reales | Publico |
| **dev** | `.dev.` | Trabajo en curso (branch dev / trunk) | Synthetic / mock | Publico con BasicAuth o token |

## Asimetria prod

Prod NO lleva label de env. La regla es:

> Si NO hay label `.dev.` antes de `the-full-stack.com`, es prod.

Razones:
1. URLs de prod limpias para marketing / SEO.
2. Diferencia visual inmediata en logs / monitoring (`*.dev.*`
   salta a la vista).
3. Coherente con SaaS modernos (`linear.app`, no `prod.linear.app`).

## Ejemplos completos

### Producto faststruct con 2 envs

```text
prod    faststruct.the-full-stack.com
        app.faststruct.the-full-stack.com
        api.faststruct.the-full-stack.com

dev     faststruct.dev.the-full-stack.com
        app.faststruct.dev.the-full-stack.com
        api.faststruct.dev.the-full-stack.com
```

### Servicio infra status con 2 envs (dev + prod)

```text
prod    status.the-full-stack.com
dev     status.dev.the-full-stack.com
```

## Previews por PR — NO extender el patron

Cloudflare Pages crea automaticamente preview URLs por commit / PR:

```text
<commit-hash>.<project>.pages.dev
```

Ejemplo: `a1b2c3d.faststruct.pages.dev`.

**NO crear records DNS custom para previews**. NO inventar
`pr-123.faststruct.dev.the-full-stack.com` ni similar. Razones:

1. Los previews son efimeros (segundos de vida util). Crear DNS records
   es overhead innecesario.
2. Cloudflare Pages ya gestiona el certificado SSL automatico.
3. Si se necesita URL "linda" para compartir un preview en PR review,
   usar la `pages.dev` directa.

## Flujo dev -> prod

```text
1. Branch feature -> merge a dev -> deploy automatico a *.dev.*
2. QA + smoke test en dev -> merge dev a main -> deploy a prod (sin label)
```

NO inventar variantes (`pre-prod`, `release-candidate`, `beta`, `stage`,
`qa`, `uat`). Las 2 etiquetas (dev/prod) son la lista cerrada.

## Caso portfolio: los 2 envs del frontend

El portfolio sigue el patron component-based con `product = portfolio`
en los 2 ambientes. La unica excepcion es el apex en prod
(`the-full-stack.com`), que ES el niche `generic`.

| Env | apex (generic) | niches (hub/fintech/architect/leader/vibe) |
|-----|----------------|---------------------------------------------|
| prod | `the-full-stack.com` (+ `www`) | `<niche>.portfolio.the-full-stack.com` |
| dev | `portfolio.dev.the-full-stack.com` | `<niche>.portfolio.dev.the-full-stack.com` |

En prod tambien existe `portfolio.the-full-stack.com`, que hace redirect
301 al apex (consistencia de patron; el apex es la URL canonica de
generic). El backend sigue la misma logica:
`api.portfolio.{env}.the-full-stack.com` (ver
[06-migration-backend-api](./06-migration-backend-api.md)).

El branch dispara el env via la integracion git nativa de Cloudflare
Pages: `dev` -> proyectos `<app>-dev`, `main` -> `<app>`. Cada proyecto
Pages tiene su `BASE_DOMAIN` y `SITE_URL` como build env vars (no hay
workflow de deploy).

## Acceso restringido en no-prod

Recomendado para dev:

| Mecanismo | Cuando usar |
|-----------|-------------|
| HTTP Basic Auth via Cloudflare Worker | Mas simple, sin cambiar la app |
| Cloudflare Access (zero trust) | Si tenes equipo, sso integrado |
| IP allowlist | Si trabajas siempre desde IPs conocidas |
| Robot.txt + noindex | SIEMPRE (evitar indexacion en Google) |

`robots.txt` en dev debe tener:

```text
User-agent: *
Disallow: /
```

Servido condicionalmente segun hostname (detectar `.dev.`).

## Que NO usar

```text
❌ qa.faststruct.the-full-stack.com       — usa dev
❌ uat.faststruct.the-full-stack.com      — usa dev
❌ stage.faststruct.the-full-stack.com    — env eliminado, usa dev
❌ preview.faststruct.the-full-stack.com  — usa default pages.dev
❌ beta.faststruct.the-full-stack.com     — releases en prod con feature flags
❌ test.faststruct.the-full-stack.com     — tests corren en CI, no necesitan URL
❌ feature-x.faststruct.the-full-stack.com — usa flag o branch preview pages.dev
❌ prod.faststruct.the-full-stack.com     — prod va sin label
```

## Variables de entorno asociadas

Sugerencia para mantener consistencia con
`docker/env/client/.{local,dev,prod}` (las vars `BASE_*` son de la
categoria `client`):

```bash
# client/.dev
BASE_DOMAIN=the-full-stack.com
BASE_SCHEME=https
ENV_LABEL=dev          # se inserta entre product y domain
# Resultado: api.faststruct.dev.the-full-stack.com

# client/.prod
BASE_DOMAIN=the-full-stack.com
BASE_SCHEME=https
ENV_LABEL=              # vacio -> prod
# Resultado: api.faststruct.the-full-stack.com
```

Helper TypeScript / Python para construir la URL:

```python
def build_url(component: str | None, product: str, env_label: str, domain: str) -> str:
    parts = []
    if component:
        parts.append(component)
    parts.append(product)
    if env_label:  # vacio -> prod, no agregar
        parts.append(env_label)
    parts.append(domain)
    return '.'.join(parts)
```
