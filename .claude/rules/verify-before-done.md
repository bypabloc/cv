# Verify Before Done (CRITICO)

> NUNCA declarar que algo esta listo sin verificar que funciona. Cada cambio debe probarse antes de reportar exito.

## Regla principal

Despues de CUALQUIER cambio de codigo, SIEMPRE ejecutar las verificaciones correspondientes ANTES de decirle al usuario que el trabajo esta completo. Declarar exito sin verificar es un desperdicio del tiempo del usuario.

## Verificaciones obligatorias por tipo de cambio

### Componentes / paginas Astro (`src/pages/`, `src/components/`, `src/layouts/`)

| Cambio | Verificacion minima |
|--------|---------------------|
| Componente nuevo / modificado | `pnpm exec biome check .` + `pnpm exec astro check` |
| Layout / pagina nueva | Lo anterior + `pnpm run build` (verifica que renderiza al SSG) |
| Estilos en componente | Verificar tokens del DS (no hex inline) y `prefers-reduced-motion` si tiene animacion |

### Utilities / lib (`src/lib/`)

| Cambio | Verificacion minima |
|--------|---------------------|
| Funcion nueva / modificada | Test mirror en `tests/unit/lib/<archivo>.test.ts` + `pnpm exec vitest run` |
| Type / interface | `pnpm exec tsc --noEmit` |
| Cambio que afecta consumers | Buscar usos con Grep y verificar que tipan correcto |

### Content collections (`src/content/`)

| Cambio | Verificacion minima |
|--------|---------------------|
| Schema (config.ts) modificado | `pnpm run build` (Astro valida entries contra schema) |
| Entry nueva | `pnpm run build` + verificar render visual en `pnpm run dev` |

### Config (`astro.config.*`, `biome.json`, `tsconfig.json`, `vitest.config.*`)

| Cambio | Verificacion minima |
|--------|---------------------|
| `astro.config.ts` | `pnpm run build` exitoso |
| `biome.json` | `pnpm exec biome check .` (verificar que reglas nuevas no rompen el repo) |
| `tsconfig.json` | `pnpm exec tsc --noEmit` |
| `vitest.config.ts` | `pnpm exec vitest run` |

### Cualquier `.ts` / `.tsx` / `.astro`

Siempre, como gate minimo:

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
hook + verificacion local explicita.

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

Errores comunes que esta verificacion detecta:
- Subdominios con HTTP 502 (nginx upstream caido)
- Astro dist sin `index.html` (build silenciosamente roto)
- View transitions o theme toggle con bug visual
- Mapping de subdominios mal alineado entre `astro.config.ts` y nginx

### Configuracion `.claude/`

| Cambio | Verificacion minima |
|--------|---------------------|
| `settings.json` | `python3 -m json.tool .claude/settings.json > /dev/null` |
| Hook bash | `bash -n .claude/hooks/<modificado>.sh` |
| Skill/agent/rule | Validar segun `claude-config-testing.md` (claude -p en bypassPermissions) |

## Flujo obligatorio

```text
1. Implementar cambio (con TDD si es logica nueva — ver tdd-workflow)
2. Ejecutar verificacion(es) correspondiente(s)
3. Si falla → corregir → volver a paso 2
4. Si pasa → AHORA reportar al usuario que esta listo
```

## Reglas estrictas

- NUNCA decir "listo", "done", "implementado", "creado" sin haber ejecutado la verificacion
- NUNCA asumir que un cambio funciona solo porque el codigo "se ve correcto"
- Si hay tests existentes para el archivo afectado, ejecutarlos
- Si se crean archivos nuevos, verificar que importan correctamente
- Si se modifica `astro.config.ts`, verificar que el build sigue funcionando
- Reportar al usuario tanto el resultado de la verificacion como el del cambio

## Errores comunes que esta regla previene

- TypeScript errors no detectados (imports rotos, props mal tipadas, generics mal usados)
- Astro components con frontmatter invalido
- Tests rotos por cambios en la interfaz
- `astro check` warnings que no se ven en el editor
- Tokens del DS que dejaron de existir y rompen estilos
- Imports faltantes en archivos nuevos
- Hex colors inline cuando hay token equivalente

## Cuando NO aplica

- Cambios exclusivamente en documentacion (`.md`)
- Cambios en configuracion de Claude (`.claude/`) que no son `settings.json` ni hooks ejecutables
- El usuario explicitamente dice que no quiere verificacion
