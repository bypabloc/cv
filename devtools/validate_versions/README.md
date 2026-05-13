# validate_versions

> Read-only check del monorepo: confirma que cada dep declarada esta en la
> ultima version stable disponible **y** que las versiones cross-package
> son coherentes (mismo Astro major, Vite peer correcto, etc).
>
> NO escribe. NO modifica manifests. Para bumpear use
> `python devtools/run.py upgrade_deps`.

## Uso

```bash
# Reporte humano (tabla por workspace + compat)
python devtools/run.py validate_versions

# Reporte JSON (CI / scripting)
python devtools/run.py validate_versions --json

# Modo strict: exit 1 si hay outdated O incompat (pre-merge gate)
python devtools/run.py validate_versions --strict
```

## Que cubre

### 1. Versiones actuales vs latest stable

Por cada dep declarada en TODOS los manifests del monorepo:

- `package.json` raiz
- `apps/<app>/package.json` (6 sites Astro)
- `packages/<pkg>/package.json` (5 workspaces compartidos)
- `devtools/pyproject.toml`
- `server/pyproject.toml` (si existe)

Consulta el registry (npm o PyPI) y compara con la version pinned local.
Filtra pre-releases (alpha/beta/rc/dev/canary/next/etc).

Status posibles:

| Status | Significado |
|--------|-------------|
| `ok` | current == latest stable |
| `outdated` | latest > current (hay upgrade disponible) |
| `unknown` | registry no respondio o sin estables |
| `ahead` | current > latest (canary local, raro) |

### 2. Compatibilidad cross-package

Reglas que `upgrade_deps` NO puede detectar (porque solo mira version
local vs registry, no coherencia entre workspaces):

| Regla | Verifica |
|-------|----------|
| `astro_major_uniform` | Todas las apps declaran astro en la misma major |
| `astrojs_compatible_with_astro` | @astrojs/sitemap >=3.7 y @astrojs/check >=0.9.9 si astro == 6 |
| `vite_peer_consistency` | Si hay astro 6: vite debe ser ^7 (Astro 6 advierte con Vite 8) |
| `vite_node_matches_vitest` | vite-node y vitest comparten major si conviven |
| `tailwind_uniform` | @tailwindcss/* y tailwindcss comparten major |
| `typescript_uniform` | typescript es la misma major en todo el monorepo |

Severidades:

- `error`: rompe builds o peer deps. En `--strict` cuenta como fail.
- `warning`: deprecation / inconsistencia menor. NO causa fail.

## Output

### Humano (default)

```
======================================================================
  validate_versions [read-only]
======================================================================

=== apps/generic/package.json ===
  package                         current       latest        status
  ----------------------------------------------------------------------
  astro                           5.16.5        6.3.2              outdated
  @astrojs/sitemap                3.4.2         3.7.2              outdated
  @tailwindcss/vite               4.0.18        4.3.0              outdated
  ...

======================================================================
  Compatibilidad cross-package: 2 issue(s)
======================================================================

  [ERROR] vite_peer_consistency
    vite@8.0.12 en pkg:content no coincide con Vite 7.x ...
    - pkg:content::vite@8.0.12

  [WARNING] typescript_uniform
    typescript declarado en majors distintas [5, 6] ...

======================================================================
  Resumen
======================================================================
  packages: 145 total | 64 ok | 81 outdated | 0 unknown | 0 ahead
  compat: 1 error(s) | 1 warning(s)
```

### JSON (`--json`)

```json
{
  "packages": [
    {
      "kind": "npm",
      "workspace": "app:generic",
      "manifest": "apps/generic/package.json",
      "name": "astro",
      "section": "dependencies",
      "current": "5.16.5",
      "latest": "6.3.2",
      "status": "outdated"
    },
    ...
  ],
  "compat_issues": [
    {
      "rule": "vite_peer_consistency",
      "severity": "error",
      "message": "...",
      "affected": ["pkg:content::vite@8.0.12"]
    }
  ],
  "summary": {
    "total_packages": 145,
    "ok": 64,
    "outdated": 81,
    "unknown": 0,
    "ahead": 0,
    "compat_errors": 1,
    "compat_warnings": 1
  }
}
```

## Exit codes

| Modo | Outdated | Compat error | Compat warning | Exit |
|------|----------|--------------|----------------|------|
| default | ≥1 | 0 | * | 0 |
| default | * | ≥1 | * | 1 |
| `--strict` | ≥1 | * | * | 1 |
| `--strict` | 0 | ≥1 | * | 1 |
| `--strict` | 0 | 0 | * | 0 |

## Relacion con upgrade_deps

| Script | Read-only | Escribe | Compat cross-package |
|--------|-----------|---------|----------------------|
| `validate_versions` | sí | no | sí |
| `upgrade_deps` | con `--dry-run` | sí (sin flag) | no |

Use validate_versions como **pre-merge gate** o **CI check**. Use
upgrade_deps cuando decida que es momento de bumpear (en su propio PR).

## Reglas adicionales

Para agregar una regla nueva: editar `compat_rules.py`, agregar funcion
``rule_xxx(packages) -> list[CompatIssue]`` y registrarla en `ALL_RULES`.
