# Arquitectura del deploy

> Como esta organizado el deploy del portfolio en Cloudflare Pages.

[← README](./README.md) | [Siguiente: API token →](./02-api-token.md)

## Decision: 6 proyectos Pages separados (no 1 con multi-app)

Cada app del monorepo es un proyecto Pages independiente. Razones:

1. **Pages no soporta multiples root_dir** dentro de un solo proyecto.
   Si quisieras 1 proyecto, todos los `apps/*` se buildearian juntos
   o tendrias que hacer hacky `_routes.json`.
2. **Watch paths funciona por proyecto**: cambios en `apps/hub/` NO
   triggean rebuild de `generic`. Si fuera 1 proyecto, cualquier cambio
   re-buildearia todo.
3. **Custom domains 1:1**: cada app tiene su propio subdominio. Con 1
   proyecto, tendrias que servir todo desde un solo `pages.dev` y hacer
   path-based routing.
4. **Free tier scaling**: 500 builds/mes/proyecto = 3000 builds/mes
   total. Con 1 solo proyecto seria 500 total.

## Topologia

```
the-full-stack.com (zona DNS en Cloudflare)
│
├── @ + www              → CNAME → generic-3ab.pages.dev    [proyecto: generic]
├── hub                  → CNAME → hub-9sd.pages.dev        [proyecto: hub]
├── fintech              → CNAME → fintech-868.pages.dev    [proyecto: fintech]
├── architect            → CNAME → architect-349.pages.dev  [proyecto: architect]
├── leader               → CNAME → leader-av7.pages.dev     [proyecto: leader]
└── vibe                 → CNAME → vibe-c2l.pages.dev       [proyecto: vibe]
```

Todos los CNAMEs estan proxied (proxy naranja activo) — el trafico pasa
por la red de Cloudflare (cache, WAF, SSL termination en el edge).

## Mapeo proyecto -> contenido

| Proyecto | Package pnpm | Root del codigo | Build output |
|----------|--------------|-----------------|--------------|
| `generic` | `@portfolio/generic` | `apps/generic/` | `apps/generic/dist/` |
| `hub` | `@portfolio/hub` | `apps/hub/` | `apps/hub/dist/` |
| `fintech` | `@portfolio/fintech` | `apps/fintech/` | `apps/fintech/dist/` |
| `architect` | `@portfolio/architect` | `apps/architect/` | `apps/architect/dist/` |
| `leader` | `@portfolio/leader` | `apps/leader/` | `apps/leader/dist/` |
| `vibe` | `@portfolio/vibe` | `apps/vibe/` | `apps/vibe/dist/` |

## Registrar vs DNS authority (separados)

- **Registrar**: AWS Route 53 (donde compraste el dominio). Renovacion y
  WHOIS se gestionan en `console.aws.amazon.com/route53/`.
- **DNS authority**: Cloudflare. Los nameservers (`*.ns.cloudflare.com`)
  estan configurados en AWS Route 53 Registrar.
- **Hosting**: Cloudflare Pages (6 proyectos).

Es una configuracion estandar y correcta. **No requiere migrar el
registrar a Cloudflare** — basta con que los nameservers en AWS apunten
a Cloudflare.

## SSL/TLS

- **Universal SSL** de Cloudflare: cert automatico para cada custom
  domain. Tarda 1-10 min en emitirse despues de attach domain.
- CA: Google Trust Services (default actual de CF).
- Renovacion automatica, no requiere accion manual.
- TLS termination en el edge de CF (cliente <-> CF: HTTPS; CF <-> Pages:
  HTTPS interno).

## Headers de seguridad

Cada app emite headers desde `apps/<app>/public/_headers`. Pages copia
ese archivo al output y lo aplica a cada respuesta. Contenido tipico:

```
/*
  Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; ...
```

## CI/CD: git-native, no GitHub Actions para deploy

Pages se dispara por webhook de GitHub al push a `main`. No requiere
secrets en GitHub Actions, no requiere `wrangler` en CI.

El workflow `.github/workflows/ci.yml` corre **paralelo**: lint +
typecheck + unit + build + e2e. Si CI pasa y el PR se mergea a main,
Cloudflare ejecuta su propio build (esta vez para deploy).

Si en el futuro quisieras CI/CD con `wrangler-action` (deploy condicional
por app modificada, approval gates, etc.) podrias migrar a direct upload.
Hoy git-native es mas simple.
