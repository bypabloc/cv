# Build config para monorepo pnpm

> Como configurar el build de cada proyecto Pages cuando el codigo vive
> en un monorepo pnpm con packages compartidos.

[← Pages API setup](./03-pages-api-setup.md) | [README](./README.md) | [Siguiente: DNS →](./05-dns-and-custom-domains.md)

## Decision: root_dir = "" (repo root)

La clave para que funcione un monorepo pnpm en Cloudflare Pages:

| Campo | Valor | Por que |
|-------|-------|---------|
| `root_dir` | `""` (vacio) | pnpm workspaces necesita ver `pnpm-workspace.yaml` en la raiz para resolver `@portfolio/*` |
| `destination_dir` | `apps/<app>/dist` | El output de Astro vive ahi |
| `build_command` | `pnpm install --frozen-lockfile && pnpm --filter @portfolio/<app>... build` | Instala todo + buildea solo lo necesario |

### Por que NO `root_dir = "apps/<app>"`

Si seteas root al directorio de la app:
- pnpm no encuentra `pnpm-workspace.yaml` (esta en la raiz)
- `@portfolio/content`, `@portfolio/ui`, etc. no resuelven
- Cloudflare falla con `Cannot find cwd: /opt/buildhome/repo/apps/<app>`
  (bug del build system v2 con monorepos)

Workaround posible (`cd ../..` en build command) — pero es fragil y
no aporta nada vs `root_dir=""`.

## Build command desglosado

```bash
pnpm install --frozen-lockfile \
  && pnpm --filter @portfolio/generic... build
```

### `pnpm install --frozen-lockfile`

- `--frozen-lockfile`: falla si `pnpm-lock.yaml` no coincide con
  `package.json`. Equivalente a "reproducibilidad estricta", obligatorio
  en CI.
- pnpm respeta `allowBuilds` en `pnpm-workspace.yaml`:
  ```yaml
  allowBuilds:
    esbuild: true   # build script de esbuild aprobado
    sharp: true     # build script de sharp aprobado
  ```
  Sin esto, pnpm 11+ skipea esbuild/sharp y el build falla.

### `pnpm --filter @portfolio/<app>... build`

- `--filter` selecciona un workspace.
- `...` (tres puntos al final) incluye **deps internas del workspace**.
- Ejemplo: `@portfolio/generic` depende de `@portfolio/content`,
  `@portfolio/ui`, `@portfolio/seo`, etc. — todas se buildean en orden
  topologico antes de generic.

Variantes de `--filter`:

| Sintaxis | Que selecciona |
|----------|----------------|
| `--filter @portfolio/generic` | Solo generic |
| `--filter @portfolio/generic...` | generic + sus deps internas (TODAS las que necesite) |
| `--filter ...@portfolio/generic` | Lo que dependa de generic (no aplica aqui) |
| `--filter @portfolio/generic^...` | Solo deps internas de generic (sin generic) |
| `-r` | Todos los packages del workspace (overkill) |

`pnpm -r build` tambien funciona pero buildea TODO el monorepo, incluso
packages que la app no usa. Para 6 apps que comparten subsets distintos
de packages, `--filter <app>...` es mas rapido.

## Env vars de build

```
NODE_VERSION=24
PNPM_VERSION=11.0.9
```

- Default de Cloudflare Pages: Node 20, pnpm 9. Si tu `package.json#engines`
  pide Node 24, hay que setearlo explicito.
- Pages usa `asdf` internamente para instalar versiones de runtime —
  acepta cualquier version reciente de Node y pnpm.
- Otras env vars (custom): se pasan exactamente como cualquier variable
  de entorno al build process. Ej: `BASE_DOMAIN`, `BASE_SCHEME`.

## Prebuild scripts

Si tu `package.json` tiene `"prebuild": "..."`, npm/pnpm lo ejecuta
automaticamente antes de `build`. NO hay que invocarlo explicito en el
build command.

Ejemplo del portfolio:
```json
"scripts": {
  "prebuild": "vite-node --config scripts/vite.config.ts scripts/build-public-assets.mjs",
  "build": "astro build"
}
```

Al correr `pnpm --filter @portfolio/generic... build`, pnpm dispara
primero `prebuild` y luego `build`. Esta cadena se preserva en Pages.

## Path de output: `apps/<app>/dist`

El campo `destination_dir` del build_config es RELATIVO a `root_dir`.
Como `root_dir = ""`:

```
root_dir       = ""                  (repo root = /opt/buildhome/repo)
destination_dir = "apps/generic/dist" (donde Astro emite output)
```

Si `root_dir` fuera `apps/generic`, `destination_dir` seria `dist`.
Pero por el bug mencionado, evitamos esa combinacion.

## Build image version

Pages tiene "build images" con toolchain pre-instalado:
- v1: Node 12, pnpm viejo (deprecated)
- v2: Node 18 default
- v3: Node 20 default (current default)

Especificar Node 24 via env var `NODE_VERSION` funciona en cualquier
build image >= v2.

## Cache de pnpm en Pages

Pages cachea automaticamente `node_modules` entre builds (si lockfile
no cambio). Primer build: 30-60s en `pnpm install`. Builds subsecuentes:
3-5s.

No requiere config — Pages detecta `pnpm-lock.yaml` y cachea.

## Verificacion local del build command

Antes de configurar Pages, validar el comando localmente:

```bash
# Limpiar
rm -rf apps/generic/dist

# Correr exactamente lo que Pages va a correr
pnpm install --frozen-lockfile
pnpm --filter @portfolio/generic... build

# Verificar output
ls apps/generic/dist/index.html
```

Si funciona local, funciona en Pages (modulo diferencias de env vars
que setees explicitas).
