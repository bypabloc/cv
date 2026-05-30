# Plan: bypass de Turnstile firmado (Ed25519)

> Reemplaza el bypass de Cloudflare Turnstile basado en un **secreto fijo
> compartido** (`X-Turnstile-Bypass-Secret`) por un **token efímero firmado
> con Ed25519** (`X-Turnstile-Bypass-Token`). El runner E2E / dev firma con
> la clave PRIVADA (local); el Lambda verifica con la clave PÚBLICA (SSM).
> Solo dev/stage; prod nunca acepta bypass. Corte limpio (sin el secreto
> viejo).

## Cuándo leer cada archivo

| Archivo | Cuándo leer |
|---------|-------------|
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Contexto, solución, criterios de aceptación (AC), flujo antes/después, tests |
| [02-fase-shared-crypto.md](02-fase-shared-crypto.md) | Fase 1: subpaquete `shared.crypto` (Ed25519 + token) |
| [03-fase-verifier-transport.md](03-fase-verifier-transport.md) | Fase 2: orquestador captcha-o-bypass + rename de header/`_meta` |
| [04-fase-services-cleanup.md](04-fase-services-cleanup.md) | Fase 3: wiring `contact_form` + `auth`, limpieza `tracking_pixel`/`cv` |
| [05-fase-devtools.md](05-fase-devtools.md) | Fase 4: keygen Ed25519 + firmante en `api_e2e` + helper on-demand |
| [06-fase-secrets-docs.md](06-fase-secrets-docs.md) | Fase 5: SSM clave pública, catálogo, borrado del secreto viejo, rules |
| [07-descomposicion.md](07-descomposicion.md) | Sección 8: tareas atómicas + paralelización |
| [08-commits.md](08-commits.md) | Sección 9: secuencia de commits |
| [09-worktrees.md](09-worktrees.md) | Sección 10: base secuencial + olas worktree-safe |
| [10-verificacion-e2e.md](10-verificacion-e2e.md) | Sección 11: batería de verificación final (gate del PR) |

## Decisiones no-reabribles (confirmadas con el usuario)

1. **Esquema cripto**: Ed25519 asimétrico. Firma = clave PRIVADA (runner E2E
   / dev-cli local). Verifica = clave PÚBLICA (Lambda, SSM). Un leak del
   env/SSM del Lambda NO permite forjar (solo tiene la pública).
2. **TTL del token**: 300 s. Stateless (sin store de nonce — solo expiración).
3. **Claves por entorno**: un par Ed25519 por env (dev y stage). Aislamiento.
4. **Entornos que aceptan bypass**: SOLO dev y stage. Prod NUNCA (defensa en
   profundidad, igual que hoy `_BYPASS_ALLOWED_STAGES`).
5. **Firmante**: solo E2E + dev local (la privada vive en `dev-cli`,
   local-only). Sin GitHub Secret por ahora (CI no corre `api_e2e`).
6. **Migración**: corte limpio. Se elimina el secreto fijo, su SSM param y el
   código de comparación. No hay clientes externos que romper.
7. **Formato del token**: compacto `b64url(payload).b64url(firma)` (sin
   `pyjwt`; `cryptography` puro). Payload `{v, iat, exp, jti, stage}`.
8. **Stage-binding**: el payload incluye `stage`; el Lambda exige que coincida
   con su `STAGE`.
9. **Transporte**: header `X-Turnstile-Bypass-Secret` → `X-Turnstile-Bypass-Token`;
   `_meta.bypass_secret` → `_meta.bypass_token`.
10. **Aislamiento de deps**: el código Ed25519 vive en un subpaquete nuevo
    `shared.crypto` (con `cryptography`), importado SOLO por `contact_form`
    y `auth`. `shared.http.turnstile` queda httpx-puro → `tracking_pixel`/`cv`
    NO vendorizan `cryptography`.
11. **Frontend intacto**: las 6 apps siguen usando Turnstile real. El bypass
    es exclusivamente herramienta de testing/dev. El frontend no firma nada.
12. **Scope de endpoints**: `contact_form` (POST /contact) y `auth`
    (`register.start`, `login.start`). `tracking_pixel`/`cv` no validan
    Turnstile → se limpia su campo `bypass_secret` muerto.

## Reglas críticas (siempre activas en este plan)

- El token firmado SOLO se evalúa si `cf_response` viene vacío Y `STAGE in
  {dev, local}` (mismas 2 guardas que el bypass actual).
- NUNCA loguear el token, la firma, ni la clave privada. Loguear solo `jti`,
  `stage`, y el resultado (`bypassed`/`invalid`).
- La clave privada NUNCA llega al contexto, ni a stdout, ni a SSM, ni a git
  (vive en `docker/env/dev-cli/.{dev,stage}`, gitignored). Ver
  [.claude/rules/env-files.md](../../../.claude/rules/env-files.md).
- La verificación de firma usa `cryptography` con import **lazy** dentro del
  path de bypass → prod nunca lo carga.
- `serverless lint-deps` debe seguir verde: imports shared-only via portador
  `shared.crypto.*`, sin barrels.

## Estado por fase

| Fase | Archivo | Estado |
|------|---------|--------|
| 1. shared.crypto | 02 | pending |
| 2. verifier + transporte | 03 | pending |
| 3. services + cleanup | 04 | pending |
| 4. devtools | 05 | pending |
| 5. secrets + docs | 06 | pending |
| 6. verificación E2E | 10 | pending |

## Escala

**Large** (11+ archivos): subpaquete shared nuevo, 2 Lambdas, devtools
(keygen + firmante + helper), SSM, limpieza de 2 Lambdas más, rules.
