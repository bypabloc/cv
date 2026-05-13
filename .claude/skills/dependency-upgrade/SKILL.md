---
name: dependency-upgrade
description: >
  Dependency upgrade workflows for this Astro 6 portfolio (pnpm only). Audit
  CVEs, check outdated packages, plan major upgrades, regenerate lockfile.
  Use when the user says: "upgrade deps", "actualizar dependencias", "pnpm
  audit", "CVE", "outdated", "bump versions", "auditar dependencias", "deps
  check", "subir versiones", "actualizar paquetes".
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash(pnpm:*), Bash(npx:*), WebSearch, WebFetch
argument-hint: "scope: all | audit-only | outdated-only | major <pkg>"
metadata:
  version: "2.0"
---

# Dependency Upgrade

Upgrade y auditoria de dependencias del portfolio Astro 6 (pnpm).

## Archivos de dependencias

| Archivo | Proposito |
|---------|-----------|
| `package.json` | Manifest principal (dependencies + devDependencies) |
| `pnpm-lock.yaml` | Lockfile reproducible (NUNCA editar a mano) |
| `.npmrc` | Config de pnpm (registry, strict-peer-deps, etc.) |

## Workflow

### Paso 1: Audit de seguridad (siempre primero)

```bash
pnpm audit --json
```

Reportar vulnerabilidades con: paquete, severidad, version actual, version fija sugerida, vector de ataque.

Si hay vulnerabilidades criticas/altas, aplicar fix primero:

```bash
pnpm audit --fix
```

### Paso 2: Check outdated

```bash
pnpm outdated --json
```

Identificar paquetes con version mas reciente disponible.

### Paso 3: Clasificar upgrades

| Tipo | Riesgo | Accion |
|------|--------|--------|
| Patch (1.2.3 → 1.2.4) | Bajo | Upgrade directo |
| Minor (1.2.3 → 1.3.0) | Medio | Leer changelog, upgrade |
| Major (1.2.3 → 2.0.0) | Alto | Leer breaking changes, evaluar |
| Security fix | Critico | Upgrade inmediato |

Para dependencias criticas del stack — Astro, TypeScript, Biome, Vitest, Playwright — investigar breaking changes con WebSearch/WebFetch antes de subir major.

### Paso 4: Aplicar upgrades

Patch/minor (low risk):

```bash
pnpm update                          # todos los paquetes a la version permitida por semver
pnpm update <package>                # uno solo
```

Major (high risk):

```bash
pnpm add <package>@latest            # fija a la ultima estable
# o
pnpm add <package>@<version>         # version especifica
```

Despues de cada cambio:

```bash
pnpm install
pnpm exec biome check .
pnpm exec tsc --noEmit
pnpm exec astro check
pnpm exec vitest run
pnpm run build
```

Si falla cualquier paso: revertir (`git checkout HEAD -- package.json pnpm-lock.yaml`) y documentar incompatibilidad.

### Paso 5: Verificacion post-upgrade

- [ ] `pnpm install` sin warnings
- [ ] `pnpm audit` sin vulnerabilidades nuevas
- [ ] Tests Vitest passing
- [ ] Typecheck (`tsc` + `astro check`) limpio
- [ ] Build (`pnpm run build`) exitoso
- [ ] Site funciona en `pnpm run dev` (verificar manual si UI relevante)

## Formato de reporte

```markdown
## Dependency Upgrade Report

### Vulnerabilidades criticas (fix inmediato)
| Paquete | Severidad | Actual | Fija | CVE |
|---------|-----------|--------|------|-----|

### Upgrades aplicados
| Paquete | Anterior | Nueva | Tipo | Tests |
|---------|----------|-------|------|-------|

### Upgrades pendientes (requieren evaluacion)
| Paquete | Anterior | Disponible | Tipo | Razon |
|---------|----------|------------|------|-------|

### Verificacion
- [ ] pnpm audit limpio
- [ ] tsc --noEmit OK
- [ ] astro check OK
- [ ] Vitest passing
- [ ] Build exitoso
```

## Reglas

- SIEMPRE ejecutar `pnpm audit` ANTES de upgrades
- SIEMPRE ejecutar tests + build despues de cada upgrade
- NUNCA hacer upgrade major sin leer breaking changes (Astro, TypeScript, Biome especialmente)
- NUNCA editar `pnpm-lock.yaml` manualmente (regenerar con `pnpm install`)
- NUNCA mezclar npm/yarn en el mismo repo (solo pnpm)
- Upgrades de seguridad tienen prioridad sobre todo
- Si un upgrade rompe tests, revertir y documentar
