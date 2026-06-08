# 01 - Patron canonico

> [<- README](./README.md) | [02-naming-rules ->](./02-naming-rules.md)

## Definicion formal

```text
[{component}.]{product}.{env}.{domain}
```

| Label | Obligatorio | Valores |
|-------|-------------|---------|
| `{domain}` | Si | `the-full-stack.com` |
| `{env}` | Solo si NO es prod | `dev` |
| `{product}` | Si (excepto excepciones) | slug kebab-case |
| `{component}` | Opcional | slug kebab-case |

Prod NO lleva label de env. Eso significa que prod tiene 1 label menos
que dev. Es la unica asimetria del patron y es intencional para
mantener URLs de prod cortas (marketing / SEO).

## Lectura right-to-left

Leer de derecha a izquierda da el nivel de detalle creciente:

```text
api.faststruct.dev.the-full-stack.com
                  └────────────────── dominio
              └────────────────────── environment (no prod)
   └─────────────────────────────────── producto
└──────────────────────────────────── componente
```

## Casos posibles por nivel

### Producto sin componente (1 sub-label + opcional env)

Cuando el producto expone una sola cosa (landing + app monolitica):

```text
prod    faststruct.the-full-stack.com
dev     faststruct.dev.the-full-stack.com
```

### Producto con componentes (2 sub-labels + opcional env)

Cuando el producto separa frontend / backend / admin en hostnames distintos:

```text
prod    app.faststruct.the-full-stack.com
        api.faststruct.the-full-stack.com
        admin.faststruct.the-full-stack.com
dev     app.faststruct.dev.the-full-stack.com
        api.faststruct.dev.the-full-stack.com
```

### Servicio de infra (product = servicio)

Para servicios cross-cutting (status, mail, monitor), el nombre del
servicio actua como `{product}`:

```text
prod    status.the-full-stack.com
        mail.the-full-stack.com
        monitor.the-full-stack.com
dev     status.dev.the-full-stack.com
```

No suelen tener componentes (`{component}` se omite). Si en algun
momento el servicio crece y se parte (ej. `monitor` con UI + API), se
introduce componente normal: `ui.monitor.the-full-stack.com`.

## Ejemplo completo de un producto

Producto hipotetico `faststruct` con landing + app + api + admin + docs,
en los 2 environments:

| Env | URL |
|-----|-----|
| prod | `faststruct.the-full-stack.com` (landing) |
| prod | `app.faststruct.the-full-stack.com` |
| prod | `api.faststruct.the-full-stack.com` |
| prod | `admin.faststruct.the-full-stack.com` |
| prod | `docs.faststruct.the-full-stack.com` |
| dev | `faststruct.dev.the-full-stack.com` |
| dev | `app.faststruct.dev.the-full-stack.com` |
| dev | `api.faststruct.dev.the-full-stack.com` |
| dev | `admin.faststruct.dev.the-full-stack.com` |

## Por que este orden y no otro

Se considero `{env}.{product}.{domain}` (dev primero). Se descarto porque:

1. Wildcards por env son mas valiosos: `*.dev.the-full-stack.com` cubre
   todos los products en dev con un cert wildcard de 1 nivel (cubre
   Universal SSL de Cloudflare).
2. CI/CD pipelines comparten env entre products (`deploy-all-dev`,
   `smoke-test-dev`), mas que pipelines compartidos por product.
3. Listados DNS agrupan por env (todos los `.dev.` juntos), facil de
   auditar que esta vivo en cada ambiente.

## Notas de implementacion

- Component como sub-label (no como sufijo `-component`) permite usar
  un cert wildcard `*.faststruct.the-full-stack.com` que cubra todos los
  components en prod. Detalles en [05-wildcards-and-certs.md](./05-wildcards-and-certs.md).
- DNS TTL recomendado: 300s para dev (rotacion frecuente), 3600s
  para prod (estable).
- Proxied vs DNS-only en Cloudflare: proxied para todo lo HTTP
  (productos, components), DNS-only para records de verificacion
  (DKIM, SPF, DMARC, atproto, etc.).
