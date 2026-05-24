# 05 — Fase 4: Cleanup docs obsoletas

## Objetivo

Actualizar la documentacion del repo para que refleje la realidad
post-plan: el deploy de las apps NO es git-native, va por GitHub
Actions + wrangler, y las env vars del build se inyectan desde
GitHub Environment Variables (sincronizadas desde `docker/env/client/`
con el nuevo script).

## Archivos

### Modificar

- [`cloudflare/pages-config.md`](../../../cloudflare/pages-config.md)
  - Reescribir la seccion "Deploy git-native": ahora deploy es via
    `deploy-apps.yml`, NO via build de Cloudflare desde el repo. Los
    18 Pages projects siguen existiendo pero con `production_branch`
    "desconectado" del flujo de build (solo aceptan deploys via API).
  - Reescribir la seccion "Variables de entorno por proyecto":
    las vars ya NO viven en el dashboard de Cloudflare; viven en
    GitHub Environments (`dev`, `stage`, `prod`) pobladas por
    `python devtools/run.py github_sync --env=<env>`.
  - Agregar tabla canonica branch -> stage -> GH env -> Cloudflare
    project sufijo, con link a la rule de CI/CD.
  - Verificar: revision visual + el hub sigue funcionando contra esa
    doc.

- [`.claude/rules/ci-cd-pipeline.md`](../../../.claude/rules/ci-cd-pipeline.md)
  - Agregar seccion "Build env vars del deploy de apps":
    - tabla `branch -> environment -> vars` (la misma del README de
      la spec, reducida).
    - regla "SIEMPRE el build de `deploy-apps.yml` declara
      `environment: <stage>` para leer GH Variables; sin eso, las
      vars caen al default prod".
    - referencia a `devtools/github_sync/README.md`.
  - Verificar: `claude --permission-mode bypassPermissions ... -p
    "que vars de build necesita el deploy de apps"` invoca esta rule.

### Crear

- [`.claude/rules/client-env-sync.md`](../../../.claude/rules/) — rule
  nueva, corta (~80 lineas), enfocada en el flujo de sync:
  - Activacion: cuando se rota `PUBLIC_TURNSTILE_SITEKEY`, se agrega
    una `PUBLIC_*` nueva, o se onboardea un env nuevo.
  - Reglas duras: NUNCA editar GH Variables a mano (usar el script).
    SIEMPRE actualizar `docker/env/client/.{env}` primero y sync
    despues. NUNCA poner PUBLIC_* como GH Secret.
  - Comandos canonicos (`github_sync --env=dev --dry-run`, luego
    `--env=dev`).
  - Anti-patrones: hardcodear en el workflow, mezclar PUBLIC_* con
    secretos verdaderos.
  - Verificar: claude -p con un prompt que matchee la rule.

### Quitar (opcional)

- [`apps/generic/public/_headers`](../../../apps/generic/public/_headers)
  y los 5 equivalentes:
  - Hoy tienen los 3 hostnames de API en `connect-src`. Esta sobre-
    permisivo pero no roto. Mantenerlo asi por simplicidad (esta fuera
    del scope de este plan), pero anotar TODO en el README de la spec
    para considerar splittearlos por env en un plan futuro.

## Verificacion incremental (al final de la Fase 4)

```bash
# La nueva rule esta indexada en CLAUDE.md
grep -n "client-env-sync" CLAUDE.md
# Si no, agregar la entrada en la tabla del "Arbol de conocimiento"

# pages-config.md no menciona "git-native" como flujo activo
grep -nE "git-native" cloudflare/pages-config.md
# (debe estar marcado historico o ausente)

# Validacion claude -p de la nueva rule
claude --permission-mode bypassPermissions \
  --disallowedTools "WebSearch" "WebFetch" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --output-format json \
  -p "como rotar el sitekey de Turnstile en GitHub Environments"
# num_turns > 1 esperado (invoca client-env-sync rule)
```
