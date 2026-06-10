# Plan: d-cv-consolidation

> Consolidar el lambda `cv_admin` dentro del lambda `cv` (la API `/cv-admin`
> deja de existir), check de permisos declarativo por controller en
> `shared/lambda_kit`, action admin `content.get-all` (todo el CV en 1
> request / 1 sesion Neon), optimizacion del `get` publico (1 sesion),
> y mejoras del admin: tab activo en `/cv/*`, textareas, sweep UI con
> playwright. Plan Large. Carpeta EFIMERA: se elimina al mergear.

## Indice

| Doc | Contenido | Cuando leer |
|-----|-----------|-------------|
| [01-backend.md](01-backend.md) | Fase Authorize en lambda_kit, fusion cv_admin->cv, get-all, sesion compartida | Antes de tocar serverless/ |
| [02-frontend.md](02-frontend.md) | /cv-admin->/cv, get-all en overview, tab activo, textareas, sweep UI | Antes de tocar admin/ o packages/ui |
| [03-commits-verificacion.md](03-commits-verificacion.md) | Secciones 9-11: commits, paralelizacion, verificacion E2E + Parte C | Al implementar y cerrar |

## 1. Contexto / Problema

1. El overview `/cv/` del admin dispara ~10 requests al GET `/cv` (una por
   seccion) en cada mount (`staleTime: 0`); cada action abre su propia
   sesion Neon. `get_full_cv` publico hace fan-out de 9 funciones, cada una
   con su `db_session()` propia (~55 queries por miss).
2. Existe una segunda API `/cv-admin` (lambda `cv_admin`) para la escritura
   del CV. Decision del dueno: NO debe existir; toda la logica del CV se
   centra en el lambda `cv`. Los permisos por action van al kit compartido.
3. El tab activo en `/cv/<seccion>/` no se resalta: `trailingSlash: true`
   hace que `usePathname()` devuelva `/cv/profile/` y `cv-shell.tsx` compara
   `===` contra `/cv/profile` (el sidebar usa `startsWith` y no sufre esto).
4. Los textareas se ven mal: el `Textarea` shadcn del admin es `min-h-16`
   (64px) sin auto-grow ni `resize`; el del form publico (ContactFormReact)
   tiene `rows=6 + resize: vertical + min-height: 120px` como referencia.

## 2. Solucion (decisiones — no reabrir)

- **D-1** Mover las operations `content` + `publish` TAL CUAL al lambda
  `cv` (solo cambia la URL); `cv_admin` se destruye en dev post-merge y la
  carpeta se elimina en commit de seguimiento (el `destroy` exige el
  manifest vivo). Prod: al promover a main (cv_admin nunca se desplego en prod).
- **D-2** Permiso declarativo: `required_permission: str | None = None` en
  `BaseController` + `set_permission_checker()` (inyeccion en cold start,
  espejo de `set_app_config`; el kit NO importa shared.auth). Fase
  Authorize al inicio de `run()` leyendo `_meta` del event crudo; el
  rechazo es `raise ApplicationError` (401/403/404 anti-enumeration).
- **D-3** `content.get-all` (admin-only): devuelve las 10 secciones en el
  MISMO shape que las lecturas publicas por seccion + `publications`
  (sin lectura publica hoy). 1 request, 1 sesion Neon. Cacheada con
  `tags=['cv']` (coherente: todo write invalida el tag).
- **D-4** `get_full_cv` publico: las funciones de seccion de
  `shared/db/cv_repository.py` aceptan `session` opcional (back-compat) y
  `get_full_cv` abre UNA sesion compartida.
- **D-5** CORS por operation en `http_handler`: `cv` -> `public` (`*`),
  `content`/`publish` -> `echo` (whitelist con el origin del admin).
- **D-6** Rate-limit: endpoints `'/cv#content'`, `'/cv#publish.dispatch'`,
  `'/cv#publish.status'` (re-seed en dev y prod; las rows `'/cv-admin#*'`
  quedan huerfanas y se borran con `delete-item` manual).
- **D-7** Overview del admin consume `content.get-all` (1 request); las
  paginas por seccion conservan su lectura por seccion (1 request + niche).
- **D-8** Mejoras UI: aplicar e iterar directo con playwright (decidido por
  el dueno), capturas como evidencia.

## 3. Criterios de aceptacion

- **AC-1** When el admin abre `/cv/`, Then se hace UNA sola llamada de
  datos (`POST /cv {operation:'content', action:'get-all'}`) y las cards
  muestran conteos reales (incl. publications, sin guion).
- **AC-2** When un caller sin JWT valido invoca `content.*`/`publish.*` en
  `/cv`, Then 401; non-admin -> 404 (anti-enumeration); admin -> 200.
- **AC-3** When se invoca `GET /cv?operation=cv&action=get`, Then la
  respuesta es identica a la actual y se ejecuta en UNA sesion Neon.
- **AC-4** When `https://api.../cv-admin` se invoca tras el cierre, Then ya
  no existe (la ruta del API GW se elimina con el destroy).
- **AC-5** Given `/cv/profile/` abierto, Then el tab "Perfil" aparece
  resaltado (idem las 11 tabs, con y sin trailing slash).
- **AC-6** Los textareas del admin crecen con el contenido (min-height
  >=120px, resize vertical) y el del form de contacto mantiene su UX.
- **AC-7** El flujo Publicar (dispatch + status) funciona igual via `/cv`.
- **AC-8** Bateria completa verde (unit shared+cv+devtools+admin, build,
  E2E api+admin contra dev) y Parte C con curls reales.

## 4-5. Diagramas

N/A — flujo identico con URL consolidada; sin cambios de schema DB.

## 6-7. Tests y archivos

Detalle por fase en [01-backend.md](01-backend.md) y
[02-frontend.md](02-frontend.md).

## 8. Descomposicion / paralelizacion

Backend (serverless/ + devtools/) y frontend (admin/ + packages/ui) tocan
arboles disjuntos -> 1 agente frontend en paralelo con el backend inline,
tras fijar el contrato de `get-all` (D-3). E2E y docs al final (secuencial).
