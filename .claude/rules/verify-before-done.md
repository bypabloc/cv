# Verify Before Done (CRÍTICO)

> NUNCA declarar que algo esta listo sin verificar que funciona. Cada cambio debe probarse antes de reportar exito.

## Regla principal

Después de CUALQUIER cambio de codigo, SIEMPRE ejecutar las verificaciones correspondientes ANTES de decirle al usuario que el trabajo esta completo. Declarar exito sin verificar es un desperdicio del tiempo del usuario.

## Verificaciones obligatorias por tipo de cambio

### Componentes / páginas Astro (`src/pages/`, `src/components/`, `src/layouts/`)

| Cambio | Verificación mínima |
|--------|---------------------|
| Componente nuevo / modificado | `pnpm exec biome check .` + `pnpm exec astro check` |
| Layout / página nueva | Lo anterior + `pnpm run build` (verifica que renderiza al SSG) |
| Estilos en componente | Verificar tokens del DS (no hex inline) y `prefers-reduced-motion` si tiene animación |

### Utilities / lib (`src/lib/`)

| Cambio | Verificación mínima |
|--------|---------------------|
| Función nueva / modificada | Test mirror en `tests/unit/lib/<archivo>.test.ts` + `pnpm exec vitest run` |
| Type / interface | `pnpm exec tsc --noEmit` |
| Cambio que afecta consumers | Buscar usos con Grep y verificar que tipan correcto |

### Content collections (`src/content/`)

| Cambio | Verificación mínima |
|--------|---------------------|
| Schema (config.ts) modificado | `pnpm run build` (Astro válida entries contra schema) |
| Entry nueva | `pnpm run build` + verificar render visual en `pnpm run dev` |

### Config (`astro.config.*`, `biome.json`, `tsconfig.json`, `vitest.config.*`)

| Cambio | Verificación mínima |
|--------|---------------------|
| `astro.config.ts` | `pnpm run build` exitoso |
| `biome.json` | `pnpm exec biome check .` (verificar que reglas nuevas no rompen el repo) |
| `tsconfig.json` | `pnpm exec tsc --noEmit` |
| `vitest.config.ts` | `pnpm exec vitest run` |

### Cualquier `.ts` / `.tsx` / `.astro`

Siempre, como gate mínimo:

```bash
pnpm exec biome check .
pnpm exec tsc --noEmit
pnpm exec astro check
```

Si hay tests relacionados, agregar:

```bash
pnpm exec vitest run --changed
```

### Feature tests E2E (OBLIGATORIO antes de push)

Antes de `git push`, cuando los cambios tocan apps/* o packages/*, ejecutar
SIEMPRE la suite Playwright. NO esta en CI (es lento), vive en el pre-push
hook + verificación local explicita.

```bash
# 1. Stack arriba
python3 devtools/run.py docker up --env=local

# 2. Feature tests (Playwright contra los 6 subdominios via nginx)
python3 devtools/run.py test_runner --module=feature --type=feature --env=local

# 3. (opcional) bajar stack si terminaste
python3 devtools/run.py docker down --env=local
```

El pre-push hook automatiza estos pasos. Si Docker no esta disponible, el
hook hace skip con [OMITIDO]. NUNCA usar `SKIP_STEPS="feature_tests"` en
push final — solo en intermedios o cuando se prueban hooks en si.

Errores comunes que esta verificación detecta:
- Subdominios con HTTP 502 (nginx upstream caido)
- Astro dist sin `index.html` (build silenciosamente roto)
- View transitions o theme toggle con bug visual
- Mapping de subdominios mal alineado entre `astro.config.ts` y nginx

### Verificación de despliegue REAL (OBLIGATORIO — gate de "listo")

> CRÍTICO: push + merge + "CI verde" NO es "listo". Un site/app/endpoint
> solo está listo cuando su URL real responde 200 con el contenido
> esperado. NUNCA declarar listo un trabajo que despliega o provisiona
> infra sin haber hecho `curl` a la URL final. Esta regla nace de un
> caso real: se mergeó el admin con "CI verde" pero ninguna de sus 3
> URLs (local/dev/custom-domain) servía — el custom domain no resolvía
> en DNS y un job `Verify admin dist` del CI estaba en rojo sin que
> nadie lo mirara.

Aplica SIEMPRE que el trabajo: despliega a Cloudflare Pages / un Lambda /
cualquier hosting, provisiona infra (custom domain, DNS, Pages project,
recurso AWS), o mergea a una rama que dispara un workflow de deploy.

Pasos NO negociables ANTES de declarar listo:

1. **Esperar y MIRAR el resultado del deploy**, no solo dispararlo. Si el
   merge dispara un workflow, revisar su `conclusion` Y el de CADA job:

   ```bash
   gh run list --workflow=deploy-apps.yml --branch=<branch> --limit=1 \
     --json databaseId,conclusion,status
   # Si conclusion != success -> ver los jobs:
   gh run view <id> --json jobs --jq '.jobs[] | {name, conclusion}'
   ```

   Un solo job en `failure` (ej. `Verify <app> dist matches env`) =
   NO listo. Diagnosticar ESE job, no ignorarlo.

2. **`curl` real a CADA URL canónica afectada** (todos los envs tocados):

   ```bash
   # Astro/Next en Cloudflare Pages (custom domain). --resolve saltea el
   # cache DNS de WSL2 (rc=6 'Could not resolve host' es del cache local,
   # NO del estado real -> confirmar con nslookup contra 1.1.1.1).
   curl -fsS -o /dev/null -w "HTTP %{http_code}\n" --max-time 25 \
     https://<subdominio>.portfolio.<env>.the-full-stack.com/
   # rutas clave de la app (no solo el home): /login/, etc.
   ```

   Aceptación: HTTP 200 (o el código correcto del endpoint) + el body
   contiene un marcador esperado (ej. `<title>` correcto). 404/502/000
   = NO listo.

3. **Si hay custom domain nuevo**: confirmar las 3 piezas, NO asumir que
   el deploy las creó:
   - Pages project existe con el nombre correcto (ojo: el naming real es
     `<niche>-<env>`, ej. `admin-dev`, SIN prefijo `portfolio-`).
   - Custom domain attachado al project en status `active` (no `pending`).
   - Registro DNS CNAME existe en la zona (`matches: 0` = falta crearlo
     con `cloudflare_setup dns --env=<X>`). El cert ACM no se emite hasta
     que el DNS resuelve.

4. **DNS recién creado**: verificar propagación contra un resolver público
   antes de concluir que "no sirve":

   ```bash
   nslookup <fqdn> 1.1.1.1   # debe devolver IPs de Cloudflare
   ```

   Propagación + emisión de cert tras crear un CNAME nuevo puede tardar
   minutos: reintentar el curl con backoff, no declarar fallo al primer
   intento.

NUNCA reportar "desplegado / listo / funcionando" basándose en
`gh pr merge` exitoso, "CI passed" o "el deploy se disparó". El estado
real es lo que devuelve el `curl` a la URL final.

### Configuración `.claude/`

| Cambio | Verificación mínima |
|--------|---------------------|
| `settings.json` | `python3 -m json.tool .claude/settings.json > /dev/null` |
| Hook bash | `bash -n .claude/hooks/<modificado>.sh` |
| Skill/agent/rule | Validar según `claude-config-testing.md` (claude -p en bypassPermissions) |

## Flujo obligatorio

```text
1. Implementar cambio (con TDD si es lógica nueva — ver tdd-workflow)
2. Ejecutar verificación(es) correspondiente(s)
3. Si falla → corregir → volver a paso 2
4. Si el cambio DESPLIEGA o provisiona infra:
   a. Esperar y MIRAR el resultado del workflow de deploy (cada job)
   b. curl real a CADA URL canónica afectada -> debe dar 200 + marcador
   c. Si hay custom domain/DNS nuevo, confirmar project + domain + CNAME
5. Si todo pasa → AHORA reportar al usuario que esta listo (con los
   códigos HTTP reales de las URLs como evidencia)
```

## Reglas estrictas

- NUNCA decir "listo", "done", "implementado", "creado", "desplegado" sin
  haber ejecutado la verificación
- NUNCA tratar `gh pr merge` exitoso, "CI passed" o "el deploy se disparó"
  como evidencia de que algo funciona. La evidencia es el `curl` a la URL
  real desplegada (ver "Verificación de despliegue REAL" arriba)
- NUNCA ignorar un job en `failure` dentro de un workflow cuyo
  `conclusion` global es `failure` — diagnosticar ESE job
- NUNCA asumir que un cambio funciona solo porque el codigo "se ve correcto"
- Si hay tests existentes para el archivo afectado, ejecutarlos
- Si se crean archivos nuevos, verificar que importan correctamente
- Si se modifica `astro.config.ts`, verificar que el build sigue funcionando
- Reportar al usuario tanto el resultado de la verificación como el del
  cambio (incluyendo los códigos HTTP de las URLs cuando hubo deploy)

## Errores comunes que esta regla previene

- TypeScript errors no detectados (imports rotos, props mal tipadas, generics mal usados)
- Astro components con frontmatter inválido
- Tests rotos por cambios en la interfaz
- `astro check` warnings que no se ven en el editor
- Tokens del DS que dejaron de existir y rompen estilos
- Imports faltantes en archivos nuevos
- Hex colors inline cuando hay token equivalente
- Custom domain en `pending` por falta de registro DNS (el `.pages.dev`
  sirve pero la URL canónica da `Could not resolve host`)
- Declarar un deploy "listo" con un job `Verify * dist` del CI en rojo
- Pages project con nombre equivocado (asumir prefijo `portfolio-` cuando
  el naming real es `<niche>-<env>`)

## Cuando NO aplica

- Cambios exclusivamente en documentación (`.md`)
- Cambios en configuración de Claude (`.claude/`) que no son `settings.json` ni hooks ejecutables
- El usuario explicitamente dice que no quiere verificación
