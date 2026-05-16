# Estandar de subdominios — `the-full-stack.com`

> Convencion canonica para nombrar subdominios bajo `the-full-stack.com`,
> cubriendo productos, servicios de infra y multiples environments
> (`dev`, `stage`, `prod`). Aplicable a todo lo que viva en el dominio.
> La unica excepcion permanente es el apex `the-full-stack.com` + `www`.

## Patron canonico

```text
[{component}.]{product}.{env}.{domain}
```

Reglas de presencia:

- `{domain}` — siempre `the-full-stack.com`.
- `{env}` — opcional; presente solo cuando NO es prod. Valores: `dev`, `stage`.
- `{product}` — slug del producto. Obligatorio salvo apex/www del portfolio.
- `{component}` — opcional, identifica componentes dentro del producto.

### Forma reducida por env

```text
prod    [{component}.]{product}.the-full-stack.com
stage   [{component}.]{product}.stage.the-full-stack.com
dev     [{component}.]{product}.dev.the-full-stack.com
```

## Cuando leer cada archivo

| Tema | Archivo | Cuando leer |
|------|---------|-------------|
| Patron canonico + ejemplos | [01-pattern.md](./01-pattern.md) | Entender la forma `[{component}.]{product}.{env}.{domain}` |
| Reglas de naming + reservados | [02-naming-rules.md](./02-naming-rules.md) | Antes de elegir nombre de producto o componente |
| Environments (dev/stage/prod) | [03-environments.md](./03-environments.md) | Definir flujo dev/stage/prod, decision sobre previews por PR |
| Excepcion del portfolio personal | [04-portfolio-exception.md](./04-portfolio-exception.md) | Por que solo el apex es excepcion y los niches usan `{niche}.portfolio.*` |
| Wildcards y certificados | [05-wildcards-and-certs.md](./05-wildcards-and-certs.md) | Planear SSL: por hostname, wildcard 1-nivel, Advanced Cert |
| Migracion backend serverless | [06-migration-backend-api.md](./06-migration-backend-api.md) | Plan concreto para migrar `execute-api.amazonaws.com` |
| Anti-patterns | [07-anti-patterns.md](./07-anti-patterns.md) | Lista de formas prohibidas con razones |

## Reglas criticas

- SIEMPRE prod va SIN label de env (`faststruct.the-full-stack.com`, no
  `prod.faststruct.the-full-stack.com`).
- SIEMPRE `dev` y `stage` van como label intermedio
  (`faststruct.dev.the-full-stack.com`, no `dev-faststruct.the-full-stack.com`).
- NUNCA usar nombres reservados como `{product}` — ver
  [02-naming-rules.md](./02-naming-rules.md) para la lista completa.
- NUNCA inventar un 4to environment (`qa`, `uat`, `preview-N`). Para
  previews por PR usar el default de Cloudflare Pages
  (`<hash>.<project>.pages.dev`) — ver [03-environments.md](./03-environments.md).
- La unica excepcion permanente es el apex `the-full-stack.com` + `www`.
  Los 5 niches del portfolio siguen el estandar como components del
  product `portfolio` (`{niche}.portfolio.the-full-stack.com`). Ver
  [04-portfolio-exception.md](./04-portfolio-exception.md).

## Decision flow rapida

```text
1. Es el apex del portfolio? -> the-full-stack.com (unica excepcion)
2. Es un niche del portfolio? -> {niche}.portfolio.{env}.{domain}
3. Es servicio de infra atomico? -> {service}.{env}.{domain}
4. Es product con un solo frontend? -> {product}.{env}.{domain}
5. Es product con varios components? -> {component}.{product}.{env}.{domain}
6. Es env temporal de PR? -> default pages.dev (no extender el estandar)
```

## Ejemplos rapidos

```text
# Producto faststruct (varios components)
faststruct.the-full-stack.com               (prod, landing)
app.faststruct.the-full-stack.com           (prod, app)
api.faststruct.the-full-stack.com           (prod, api)
api.faststruct.dev.the-full-stack.com       (dev, api)
api.faststruct.stage.the-full-stack.com     (stage, api)

# Portfolio (product = portfolio): apex es excepcion, niches y api siguen el estandar
the-full-stack.com                          (prod, apex = niche generic, excepcion)
fintech.portfolio.the-full-stack.com        (prod, niche fintech)
hub.portfolio.dev.the-full-stack.com        (dev, niche hub)
api.portfolio.the-full-stack.com            (prod, backend)
api.portfolio.stage.the-full-stack.com      (stage, backend)

# Servicio infra status page
status.the-full-stack.com                   (prod)
status.dev.the-full-stack.com               (dev)
```
