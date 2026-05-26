# 02 — Fase 0: Diagnostico del bug SPA fallback en `/.well-known/api-catalog`

> **Anterior**: [01-contexto-y-decision.md](01-contexto-y-decision.md) · **Siguiente**: [03-fase-1a-fix-api-catalog.md](03-fase-1a-fix-api-catalog.md)
>
> **Objetivo**: Reproducir el bug observado el 2026-05-25T23:47 y dejar
> evidencia en el plan para que el fix de Fase 1A se valide contra la
> evidencia previa.

## Sintoma

```bash
$ curl -sI -X GET https://the-full-stack.com/.well-known/api-catalog
HTTP/2 200
content-type: application/json         # OK (viene del _headers del prebuild)
content-length: 83433                  # BUG: deberia ser ~245 bytes
etag: "8fcde9f06b7d965271cbcab1cc69c48a"

$ curl -s https://the-full-stack.com/.well-known/api-catalog | head -c 50
<!DOCTYPE html><html lang="es"> <head><meta charset="UTF-8">  # BUG: es index.html
```

El archivo correcto (245 bytes JSON) SI existe en el dist:

```bash
$ cat apps/generic/dist/.well-known/api-catalog
{
  "linkset": [
    {
      "anchor": "https://the-full-stack.com",
      "service-desc": [
        {
          "href": "https://api.portfolio.the-full-stack.com/openapi.json",
          "type": "application/json"
        }
      ]
    }
  ]
}
```

Pero Cloudflare Pages devuelve el `index.html` del SPA fallback con el
header `Content-Type: application/json` (porque el `_headers` aplica el
override por path independientemente del body real).

## Causa raiz

**Cloudflare Pages aplica el SPA fallback (sirve `/index.html`) para
rutas que no terminan en una extension reconocida** (`.html`, `.json`,
`.txt`, `.xml`, etc.). El archivo `api-catalog` (sin extension) cae en
este comportamiento aunque el archivo exista en el bucket de assets.

Comportamiento documentado en `_redirects` de Cloudflare Pages (regla
implicita: `/* /index.html 200` si no se encuentra match exacto). La
diferencia con un fallback negativo (HTTP 404) es que Pages aplica el
fallback al index.html por defecto en sitios sin `_redirects` explicito
para esa ruta.

## Tareas de Fase 0

### Tarea 0.1 — Reproducir localmente con `wrangler pages dev`

```bash
# 1. Build de generic
pnpm --filter @portfolio/generic run build

# 2. Servir el dist con wrangler (free local CLI)
npx wrangler pages dev apps/generic/dist --port 8788

# 3. En otra terminal: reproducir el bug
curl -s http://localhost:8788/.well-known/api-catalog | head -c 100
# ESPERADO: <!DOCTYPE html>...  (bug reproducido)

curl -s http://localhost:8788/.well-known/api-catalog.json | head -c 100
# ESPERADO: 404 (archivo no existe con .json)
```

**Verifica**: el bug se reproduce en local sin necesidad de deployar.
Si NO se reproduce, investigar diferencias entre wrangler local y Pages
prod.

### Tarea 0.2 — Confirmar que el archivo se sube al deploy

```bash
# Verificar que el deploy a dev incluye el archivo
curl -sI https://generic.portfolio.dev.the-full-stack.com/.well-known/api-catalog
# Si content-length > 1000 -> bug confirmado en dev
# Si content-length ~245 -> bug NO aplica en dev (raro)
```

### Tarea 0.3 — Probar workarounds rapidos (descartar)

| Workaround | Resultado esperado | Conclusion |
|-----------|--------------------|-----------|
| Renombrar a `.json` | Sirve OK (sin SPA fallback) | **Si funciona** → Fase 1A |
| Crear `_redirects` con `200` explicito a path sin extension | Cloudflare probablemente ignora | A descartar |
| Crear `_routes.json` con exclude para `.well-known/*` | Aplica solo a Functions, no a static | A descartar |

### Tarea 0.4 — Documentar evidencia en commit

El commit de Fase 0 NO modifica codigo, solo agrega este archivo del
plan y documenta el resultado de las pruebas en un bloque al final:

````markdown
## Evidencia de reproduccion (rellenar tras Tarea 0.1)

- Fecha reproduccion: <YYYY-MM-DD HH:MM>
- Wrangler version: `npx wrangler --version` → `X.Y.Z`
- Comando: `curl -s http://localhost:8788/.well-known/api-catalog | head -c 50`
- Output observado: `<!DOCTYPE html><html lang="es"...`
- Confirmacion: bug reproducido en local con wrangler pages dev v<X.Y.Z>
````

## Verificacion (incremental de Fase 0)

```bash
# El commit de Fase 0 debe pasar lint (es solo markdown)
pnpm exec biome check docs/specs/ai-audit-level-3-4/02-fase-0-diagnostico.md
```

## Archivos afectados

### Crear

- `docs/specs/ai-audit-level-3-4/02-fase-0-diagnostico.md` — este archivo
  - Verificar: `wc -l` < 300

### Modificar

Ninguno en esta fase.

## Done

- [ ] Bug reproducido localmente con `wrangler pages dev`
- [ ] Confirmado que el archivo existe en el dist pero Cloudflare sirve
  `index.html` con `content-length` >> 245 bytes
- [ ] Evidencia agregada al final de este archivo
- [ ] Commit `docs(specs): fase 0 - diagnostico bug SPA fallback en api-catalog`
