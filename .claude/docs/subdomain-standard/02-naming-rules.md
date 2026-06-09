# 02 - Reglas de naming + reservados

> [<- 01-pattern](./01-pattern.md) | [03-environments ->](./03-environments.md)

## Reglas para `{product}`

1. **kebab-case obligatorio** si son 2+ palabras: `practical-exercises`,
   `join-files`. Sin camelCase, sin snake_case.
2. **Single-word preferido** cuando sea natural y reconocible:
   `faststruct` mejor que `fast-struct`. Solo aplica si la palabra
   completa es la marca real del producto.
3. **ASCII lowercase**. Sin acentos (`á`), sin diacriticos (`ñ`), sin
   caracteres especiales. Compatible con RFC 1035 + RFC 1123.
4. **Longitud**: minimo 3, maximo 30 caracteres.
5. **Sin guion al inicio o final** (`-foo`, `foo-`). Sin doble guion
   (`foo--bar`).
6. **Inmutable una vez lanzado**: una vez que un product tiene trafico,
   renombrar requiere redirects + SEO migration. Pensar antes.

## Reglas para `{component}`

1. kebab-case + ASCII lowercase (idem).
2. Nombres bien conocidos (preferidos, no obligatorios):
   - `app` — SPA / web app principal
   - `api` — backend HTTP / GraphQL / REST
   - `admin` — panel admin separado
   - `docs` — documentacion publica
   - `cdn` — assets estaticos
   - `auth` — IdP / SSO si aplica
   - `ws` — WebSocket si separado
   - `webhook` — receptores de webhooks
3. Si el producto tiene un solo "thing" publico, **omitir component**.
   La landing del producto vive en el slug del producto solo
   (`faststruct.the-full-stack.com`).

## Reglas para `{env}`

Solo 2 valores formales:

| Env | Label | Que es |
|-----|-------|--------|
| prod | (vacio) | Production estable, publica |
| dev | `dev` | Branch dev / trunk, expuesto publicamente con auth si aplica |

Para previews por PR, ver [03-environments.md](./03-environments.md) —
NO se extiende el patron con `preview`, `pr-123`, etc.

## Reservados — PROHIBIDOS como `{product}`

Estos nombres NO pueden usarse como nombre de un product propio porque
ya tienen significado en el patron o en convenciones de internet:

### Componentes reservados

```text
www, api, app, admin, mail, status, auth, cdn, assets, static
```

Razon: son nombres de `{component}` esperados. Si los usas como product,
generan colisiones (`www.www.the-full-stack.com`? `api.api.the-full-stack.com`?).

### Environments reservados

```text
dev, stage, staging, prod, production, test, qa, uat, local, localhost
```

Razon: son labels de `{env}` o variantes. Confundirian la lectura del
patron.

### Infra reservada

```text
infra, internal, private, vpn, tunnel
```

Razon: convencion para servicios cross-cutting. Si necesitas un product
con uno de estos nombres, elegir un nombre mas especifico.

### Portfolio nichos reservados

```text
hub, fintech, architect, leader, vibe, generic, admin
```

Razon: son los 5 nichos del portfolio personal + el sitio generic + el
panel admin (`admin.portfolio.{env}.the-full-stack.com`). `admin` ya esta
reservado como component bien conocido (ver "Componentes reservados"
arriba); aqui se confirma su uso como component del product `portfolio`.
Ver [04-portfolio-exception.md](./04-portfolio-exception.md).

## Reservados — PERMITIDOS como `{component}`

Los nombres bien conocidos (`api`, `app`, `admin`, etc.) son
**reservados como product** pero **permitidos como component**.
Ejemplos:

- ✅ `api.faststruct.the-full-stack.com` — `api` es component de
  `faststruct` (product). Valido.
- ❌ `api.the-full-stack.com` (directo, sin product padre) — sin
  product, `api` queda como product. PROHIBIDO.

## Validacion practica (regex)

Para un product:

```regex
^[a-z](?:[a-z0-9]|-(?=[a-z0-9])){1,28}[a-z0-9]$
```

- Empieza y termina con [a-z0-9]
- Solo letras minusculas, digitos, guiones
- Sin guion doble
- Longitud total entre 3 y 30

Para un component: mismo regex.

Para una URL completa (sin protocolo):

```regex
^(?:[a-z][a-z0-9-]*\.)?[a-z][a-z0-9-]*(?:\.dev)?\.the-full-stack\.com$
```

## Casos limite

### Producto con 1 palabra que tambien es reservado

Ejemplo: si tu producto se llama `Status` (nombre comercial). NO podes
usar `status.the-full-stack.com` como product propio porque colisiona
con el servicio de infra reservado.

Soluciones:
1. Renombrar el product comercialmente (`statusly`, `statuspulse`).
2. Usar un nombre interno distinto del comercial (`spulse.the-full-stack.com`
   con redirect/canonical desde el dominio publico real).
3. Comprar dominio propio para ese product.

### Producto con marca multi-palabra unica

Ejemplo: `Visual Studio Marketplace`. NO usar `vsm` (siglas dificiles).
NO usar `visual-studio-marketplace` (excesivo, 32 chars). Solucion: usar
el slug corto que ya usás en otros lados (`vs-marketplace`,
`vscodemkt`, etc.) y documentarlo.
