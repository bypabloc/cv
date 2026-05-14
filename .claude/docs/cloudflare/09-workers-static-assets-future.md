# Workers Static Assets (futuro)

> Cuando migrar de Cloudflare Pages a Workers Static Assets. Hoy: NO.
> En el futuro (Q4 2026+): tal vez si agregamos SSR o serverless.

[← Comparacion proveedores](./08-vercel-netlify-vs-cloudflare.md) | [README](./README.md)

## Que es Workers Static Assets

Cloudflare introduce **Workers Static Assets** en 2024-2025 como el
"sucesor" de Pages. Es un Worker que sirve assets estaticos + tiene
acceso opcional a `fetch()` para SSR/serverless logic.

Roadmap publico de Cloudflare (blog 2025-2026): "Pages and Workers are
converging into one experience". Pages NO desaparece, pero **todas las
inversiones nuevas van a Workers**.

## Estado en 2026

| Capacidad | Pages | Workers Static Assets |
|-----------|-------|----------------------|
| Static hosting | ✓ | ✓ |
| Git integration auto | ✓ | ✓ (mas reciente) |
| `_headers` / `_redirects` | ✓ | ✓ (pero recomienda Worker code) |
| SSR / fetch handler | Limitado (Functions) | Nativo |
| Durable Objects | No | ✓ |
| Cron Triggers | No | ✓ |
| KV / R2 / D1 | Via Functions | Nativo |
| WAF / Page Rules | Idem | Idem |
| Madurez | Production-grade desde 2021 | Stable, evolucionando |
| Wrangler support | Parcial | Full |
| Pricing | Free tier generoso | Free tier diferente (10M req/mes) |

## Por que NO migrar HOY

1. **Pages funciona perfecto** para este caso (Astro static + 6 apps +
   custom domains)
2. **No necesitamos SSR**, serverless, Cron, ni Durable Objects
3. **Wrangler.toml requerido** en Workers — mas complejidad inicial
4. **No hay deadline**: Cloudflare confirmo que Pages seguira soportado
   "indefinidamente"
5. **Free tier ligeramente distinto**: Workers cuenta requests, no
   bandwidth. Para este trafico no importa, pero hay que pensarlo.

## Cuando SI migrar

Migrar a Workers Static Assets cuando se cumpla alguna de estas:

### 1. Necesitamos SSR

Ejemplos:
- Form de contacto con backend en el mismo dominio
- API de busqueda full-text sobre el CV
- Endpoint de webhook para Notion/Calendly
- A/B testing server-side

Hoy todo eso esta resuelto con servicios externos (Formspree, Algolia,
n8n.cloud, etc.).

### 2. Necesitamos schedule jobs

Ejemplos:
- Refrescar datos del CV desde una fuente externa cada dia
- Notificacion automatica al recibir un visit pico
- Health-check de los 6 sitios + alertas

Esto se podria resolver con Cron Triggers de Workers (1 a la vez en
free tier). Hoy no es necesario.

### 3. Necesitamos KV/R2/D1 con baja latencia

Ejemplos:
- Cache de respuestas LLM (si el CV agrega chatbot)
- Storage de uploads (avatars dinamicos, etc.)
- DB chica para tracking de visitas custom

Si llega ese caso, Workers Static Assets > Pages porque el binding es
nativo (en Pages hay que ir via Functions con mas overhead).

## Como migrar (cuando llegue el momento)

Migration estimada en <1 dia para 6 apps. Pasos:

1. **Crear `wrangler.toml`** por cada app:
   ```toml
   name = "generic"
   compatibility_date = "2026-05-13"
   main = "src/worker.ts"   # opcional, si hay SSR

   [assets]
   directory = "./dist"
   not_found_handling = "404-page"
   ```

2. **Actualizar el script Python** para usar la nueva API de Workers
   (similar a Pages pero distinto endpoint).

3. **Reemplazar CNAMEs DNS** apuntando a `<worker>.workers.dev` en vez
   de `<project>.pages.dev`.

4. **Probar uno (`generic`)** antes de migrar los 5 restantes.

5. **Borrar proyectos Pages viejos** una vez verificada la migracion.

## Cambios en el script de setup

`devtools/cloudflare_setup/` esta diseñado para Pages. Cuando migremos:

- `payloads.py` necesita nuevo `build_create_worker_payload(app)`
- `api.py` agrega endpoints `/accounts/{id}/workers/scripts/<name>`
- `config.py` agrega `compatibility_date` por app
- `main.py` cambia las llamadas

Es backwards-compatible: podemos correr ambos sets (Pages + Workers) en
paralelo durante la migracion para test.

## Recursos

- [Blog: Pages and Workers are converging](https://blog.cloudflare.com/pages-and-workers-are-converging-into-one-experience/) (2025)
- [Migration guide: Pages → Workers Static Assets](https://developers.cloudflare.com/workers/static-assets/migration-guides/migrate-from-pages/) (2025-2026)
- [Workers Static Assets docs](https://developers.cloudflare.com/workers/static-assets/) (2026)

## Conclusion

**Q3 2026**: Quedarse en Pages, monitorear bandwidth + builds usados.

**Q4 2026 o cuando lleguen estas condiciones**:
- Necesitas SSR, Cron, Durable Objects, o bindings nativos KV/R2/D1
- Cloudflare deprecate algo critico de Pages
- Tarea de portfolio donde valga la pena experimentar con Workers

Hasta entonces: Pages es production-grade y zero-friction.
