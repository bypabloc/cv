# 04 - Excepcion del portfolio personal

> [<- 03-environments](./03-environments.md) | [05-wildcards-and-certs ->](./05-wildcards-and-certs.md)

## Por que es excepcion

El portfolio personal (`the-full-stack.com`) precede al estandar y es
parte del branding del owner. Migrarlo bajo el patron
`portfolio.the-full-stack.com` o `cv.the-full-stack.com` rompe SEO,
links externos y la narrativa del dominio (que ES el portfolio).

Decision: dejarlo como excepcion permanente. El estandar aplica solo
a productos y servicios NUEVOS bajo el dominio.

## Subdominios reservados por el portfolio

Estos 7 hostnames NO siguen el patron y NO pueden reusarse para otros
productos:

| Hostname | Que es |
|----------|--------|
| `the-full-stack.com` | Apex — portfolio generic (full stack senior) |
| `www.the-full-stack.com` | Alias del apex |
| `hub.the-full-stack.com` | Selector multi-niche con cards |
| `fintech.the-full-stack.com` | Niche fintech LATAM |
| `architect.the-full-stack.com` | Niche frontend architect |
| `leader.the-full-stack.com` | Niche tech lead / engineering manager |
| `vibe.the-full-stack.com` | Niche vibe coding / Claude Code |

Adicionalmente, los nichos como words (`hub`, `fintech`, `architect`,
`leader`, `vibe`, `generic`) estan reservados como product names
(ver [02-naming-rules.md](./02-naming-rules.md)) para evitar
colisiones futuras.

## Como interactua con el estandar

### Apex / www

`the-full-stack.com` y `www.the-full-stack.com` apuntan al sitio
portfolio generic. El apex NO esta disponible para `{product}` propio.

Si en algun momento se quiere un sitio "raiz" del dominio que no sea el
portfolio, opciones:

1. Rediseñar el portfolio como hub/landing y mover el niche generic a
   `generic.the-full-stack.com` (rompe el modelo actual).
2. Mantener el portfolio en el apex y poner el nuevo sitio en un
   subdomain coherente con el estandar.

### Backend del portfolio

El backend serverless del portfolio (form de contacto, tracking pixel)
debe migrarse al estandar como product `portfolio`:

```text
prod    api.portfolio.the-full-stack.com
dev     api.portfolio.dev.the-full-stack.com
```

Ver [06-migration-backend-api.md](./06-migration-backend-api.md) para
el plan concreto.

Notar que `portfolio.the-full-stack.com` (sin component) NO se crea —
el portfolio "es" el dominio, no necesita una landing dedicada bajo
ese slug.

## Que pasa si quiero un product que choca con un nicho

Ejemplo: quiero lanzar un product comercial llamado `fintech`.

NO podes usar `fintech.the-full-stack.com` (ya es el niche fintech del
portfolio). Opciones:

1. Renombrar el product comercialmente.
2. Comprar otro dominio para ese product.
3. Renombrar el niche del portfolio (rompe SEO + branding actual).

La opcion 1 es la recomendada. El portfolio gana en branding y los
products pueden tener nombres distintivos.

## Resumen visual

```text
EXCEPCION (portfolio):
  the-full-stack.com               ← portfolio generic
  www.the-full-stack.com           ← alias apex
  hub.the-full-stack.com           ← niche hub
  fintech.the-full-stack.com       ← niche fintech
  architect.the-full-stack.com     ← niche architect
  leader.the-full-stack.com        ← niche leader
  vibe.the-full-stack.com          ← niche vibe

ESTANDAR (todo lo demas):
  faststruct.the-full-stack.com    ← product faststruct prod
  api.portfolio.the-full-stack.com ← backend portfolio prod
  status.the-full-stack.com        ← servicio infra prod
  faststruct.dev.the-full-stack.com ← product faststruct dev
  ...
```
