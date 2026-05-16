# 07 - Anti-patterns

> [<- 06-migration-backend-api](./06-migration-backend-api.md) | [README ->](./README.md)

## Lista de formas prohibidas con razon

### Forma del subdomain

| Prohibido | Por que | Correcto |
|-----------|---------|----------|
| `prod.faststruct.the-full-stack.com` | Prod va sin label de env (asimetria intencional) | `faststruct.the-full-stack.com` |
| `dev-faststruct.the-full-stack.com` | Env como sufijo flat rompe el patron `{env}` como label | `faststruct.dev.the-full-stack.com` |
| `faststruct-dev.the-full-stack.com` | Env como sufijo flat invertido | `faststruct.dev.the-full-stack.com` |
| `faststruct-api.the-full-stack.com` | Component como sufijo slug compuesto rompe wildcards | `api.faststruct.the-full-stack.com` |
| `dev.the-full-stack.com` | Falta product, queda env solo | nunca usar — env siempre con product |
| `stage.the-full-stack.com` | Idem dev | nunca usar |
| `Faststruct.the-full-stack.com` | Mayusculas violan RFC 1035 | `faststruct.the-full-stack.com` |
| `faststruct_api.the-full-stack.com` | Underscore prohibido en hostnames | `api.faststruct.the-full-stack.com` |
| `faststruct.com.the-full-stack.com` | Punto extra en slug, parece TLD pegado | usar slug propio |

### Naming de products

| Prohibido | Por que | Correcto |
|-----------|---------|----------|
| `api.the-full-stack.com` | `api` es reservado como product (es component) | usar como component de algo: `api.{product}.the-full-stack.com` |
| `app.the-full-stack.com` | `app` es reservado como product | `app.{product}.the-full-stack.com` |
| `admin.the-full-stack.com` | `admin` es reservado como product | `admin.{product}.the-full-stack.com` |
| `dev.the-full-stack.com` como product propio | `dev` reservado para env | usar otro nombre |
| `prod.the-full-stack.com` como product propio | `prod` reservado para env | usar otro nombre |
| `portfolio.the-full-stack.com` como product propio | reservado: es el product del portfolio (301 al apex) | usar otro nombre |
| `tunnel.the-full-stack.com` como product propio | reservado para infra | si es CF tunnel, scope a env: `vpn.{env}.the-full-stack.com` |
| Product `Status` | colision con servicio infra `status` | renombrar comercialmente |

### Environments

| Prohibido | Por que | Correcto |
|-----------|---------|----------|
| `qa.faststruct.the-full-stack.com` | `qa` no esta en la lista cerrada | usar `stage` |
| `uat.faststruct.the-full-stack.com` | idem | usar `stage` |
| `preview.faststruct.the-full-stack.com` | extender el patron para previews | usar default `<hash>.<project>.pages.dev` |
| `beta.faststruct.the-full-stack.com` | sub-env post-prod no formal | usar feature flags + prod URL |
| `test.faststruct.the-full-stack.com` | tests corren en CI, no necesitan URL | usar CI / local |
| `feature-x.faststruct.the-full-stack.com` | env temporal por feature | usar default pages.dev |
| `release-candidate.faststruct.the-full-stack.com` | sub-env informal | usar `stage` |

### Multiples envs en un slug

| Prohibido | Por que | Correcto |
|-----------|---------|----------|
| `faststruct.dev-stage.the-full-stack.com` | dos envs combinados sin sentido | uno o el otro |
| `faststruct.dev.stage.the-full-stack.com` | 2 labels env, ambigüo | uno solo |

## Anti-patterns por motivo

### Marketing-driven (ceder al impulso de URLs "lindas")

```text
❌ get.faststruct.com  ← punto entry de marketing, separa del estandar
✅ faststruct.the-full-stack.com  ← prod simple cumple ese rol
```

Si necesitas un CTA muy corto, comprar un dominio dedicado (`fstr.io`)
en lugar de inventar un subdomain del estandar.

### "Solo por esta vez"

```text
❌ demo-cliente-acme.the-full-stack.com  ← deploy one-off para un demo
✅ demo.{product}.dev.the-full-stack.com con feature flag
✅ usar URL pages.dev directa
```

Los demos one-off acumulan DNS huerfanos rapido. Limitar al patron o
usar pages.dev efimero.

### Acronimos crypticos como product

```text
❌ vsm.the-full-stack.com (que es vsm?)
✅ vscodemkt.the-full-stack.com (autodescriptivo)
```

Reglas: si un dev nuevo no entiende que es el product por el nombre,
el nombre es malo.

### Sufijos para evitar el patron

```text
❌ api-v2.faststruct.the-full-stack.com  ← versioning en subdomain
✅ api.faststruct.the-full-stack.com con /v2 path-based versioning
✅ api.faststruct-v2.the-full-stack.com solo si v2 es un product propio
```

## Cuando una excepcion es valida

Casos donde se puede romper el estandar conscientemente:

1. **Migracion temporal**: subdomain legacy durante transicion (max 90 dias).
2. **Constraint externo**: proveedor SaaS requiere un CNAME especifico
   (ej. `auto-detect.fly.dev`).
3. **Verificacion de identidad**: CNAMEs `*._domainkey` (DKIM),
   `_dmarc`, `_atproto` etc. no son del trafico HTTP — siguen reglas
   propias del protocolo.

Documentar excepciones en `docs/cv/` o en un `EXCEPTIONS.md` de la zona
para que esten visibles en review.

## Como auditar la zona

Script de auditoria sugerido:

```bash
#!/usr/bin/env bash
# Lista records de Cloudflare + Route 53 y marca los que rompen el estandar.

# 1. Leer todos los hostnames
# 2. Filtrar los que apuntan a hosting (excluir DKIM/SPF/DMARC/atproto)
# 3. Para cada uno, validar contra regex del estandar
# 4. Reportar los que no matchean + razon
```

Regex del estandar (para validacion):

```regex
^(?:[a-z][a-z0-9-]*\.)?[a-z][a-z0-9-]*(?:\.(?:dev|stage))?\.the-full-stack\.com$
```

Reservados a excluir adicionalmente: el conjunto del portfolio (apex, www, hub, fintech, architect, leader, vibe).
