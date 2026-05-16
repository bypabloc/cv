# 04 - Excepcion del portfolio personal

> [<- 03-environments](./03-environments.md) | [05-wildcards-and-certs ->](./05-wildcards-and-certs.md)

## Que es excepcion (y que no)

El portfolio personal usa `the-full-stack.com` como dominio raiz. La
**unica excepcion permanente** del estandar es el apex:

| Hostname                 | Que es                                       | Excepcion                       |
|--------------------------|----------------------------------------------|---------------------------------|
| `the-full-stack.com`     | Apex — portfolio generic (full stack senior) | SI — apex no lleva `{product}`  |
| `www.the-full-stack.com` | Alias del apex                               | SI — alias del apex             |

Todo lo demas del portfolio **sigue el estandar** con `product = portfolio`.
Los 5 niches no son una excepcion: cuelgan de `portfolio` como components.

## Niches bajo el estandar (product = portfolio)

Los niches del portfolio son components del product `portfolio`, en los
3 ambientes:

```text
prod    hub.portfolio.the-full-stack.com
        fintech.portfolio.the-full-stack.com
        architect.portfolio.the-full-stack.com
        leader.portfolio.the-full-stack.com
        vibe.portfolio.the-full-stack.com

stage   hub.portfolio.stage.the-full-stack.com
        fintech.portfolio.stage.the-full-stack.com
        ...

dev     hub.portfolio.dev.the-full-stack.com
        fintech.portfolio.dev.the-full-stack.com
        ...
```

El apex `the-full-stack.com` ES el niche `generic` en prod. En dev/stage
el apex del ambiente es `portfolio.dev.the-full-stack.com` /
`portfolio.stage.the-full-stack.com` (no hay apex desnudo en no-prod).

`portfolio.the-full-stack.com` existe (consistencia de patron) y hace
redirect 301 al apex `the-full-stack.com` — el apex es la URL canonica
de generic. El redirect se implementa con una Cloudflare Redirect Rule
a nivel de zona (`http.host eq "portfolio.the-full-stack.com"`), NO con
un `_redirects` de Pages: el proyecto `generic` sirve tanto el apex como
`portfolio.*`, asi que un `_redirects` por path redirigiria tambien el
apex. La Redirect Rule discrimina por hostname.

## Apex / www

`the-full-stack.com` y `www.the-full-stack.com` apuntan al sitio
portfolio generic. El apex NO esta disponible para `{product}` propio:
es la cara del portfolio.

Si en algun momento se quiere un sitio "raiz" del dominio que no sea el
portfolio, opciones:

1. Rediseñar el portfolio como hub/landing y mover el niche generic a
   un subdomain coherente con el estandar.
2. Mantener el portfolio en el apex y poner el nuevo sitio en un
   subdomain coherente con el estandar.

## Backend del portfolio

El backend serverless del portfolio (form de contacto, tracking pixel)
sigue el estandar como component `api` del product `portfolio`:

```text
prod    api.portfolio.the-full-stack.com
stage   api.portfolio.stage.the-full-stack.com
dev     api.portfolio.dev.the-full-stack.com
```

Ver [06-migration-backend-api.md](./06-migration-backend-api.md).

## Nombres reservados

Los niches como words (`hub`, `fintech`, `architect`, `leader`, `vibe`,
`generic`) y `portfolio` estan reservados como component/product names
(ver [02-naming-rules.md](./02-naming-rules.md)) para evitar colisiones.

### Que pasa si quiero un product que choca con un nicho

Ejemplo: quiero lanzar un product comercial llamado `fintech`. Ya no
hay colision con `fintech.the-full-stack.com` (ese hostname es del
portfolio), porque el niche del portfolio vive en
`fintech.portfolio.the-full-stack.com`. Un product nuevo `fintech`
usaria `fintech.the-full-stack.com` (prod) bajo el estandar.

Aun asi, conviene nombres distintivos para products comerciales para no
confundir con los niches del portfolio.

## Resumen visual

```text
EXCEPCION (solo apex):
  the-full-stack.com               ← portfolio generic (canonico)
  www.the-full-stack.com           ← alias apex

ESTANDAR — portfolio (product = portfolio):
  portfolio.the-full-stack.com         ← 301 -> apex
  hub.portfolio.the-full-stack.com     ← niche hub
  fintech.portfolio.the-full-stack.com ← niche fintech
  architect.portfolio.the-full-stack.com
  leader.portfolio.the-full-stack.com
  vibe.portfolio.the-full-stack.com
  api.portfolio.the-full-stack.com     ← backend prod

ESTANDAR — otros products/servicios:
  faststruct.the-full-stack.com    ← product faststruct prod
  status.the-full-stack.com        ← servicio infra prod
  faststruct.dev.the-full-stack.com ← product faststruct dev
  ...
```
