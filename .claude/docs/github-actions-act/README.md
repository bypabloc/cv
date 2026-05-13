# GitHub Actions + act - Testing CI Local

> Referencia para el workflow CI de GitHub Actions del proyecto y la herramienta `act` para ejecutarlo localmente.

## Que es act

[act](https://github.com/nektos/act) (v0.2.84+, 69k+ stars) ejecuta workflows de GitHub Actions localmente usando contenedores Docker. Lee `.github/workflows/*.yml`, resuelve dependencias entre jobs, y ejecuta cada job en un contenedor Docker que simula el runner de GitHub.

Variable especial: `act` inyecta `ACT=true` como variable de entorno, permitiendo saltar steps que no aplican localmente con `if: ${{ !env.ACT }}`.

## Contexto del proyecto

- **Workflow**: `.github/workflows/ci.yml` (1 job: `quality-gates`)
- **Trigger**: PRs a `main`, `master`, `dev`
- **Quality gates**: Conformance (Ruff) + Coverage (80%) + Unit tests + Integration tests
- **El CI reutiliza el hook pre-push**: `python3 .git-hooks/pre-push` (zero duplicacion)
- **Requiere Docker**: El workflow ejecuta `python devtools/run.py docker up --env=test`

## Tabla de referencia

| Tema | Archivo | Cuando leer |
|------|---------|-------------|
| act CLI | [01-act-reference.md](01-act-reference.md) | Instalacion, comandos, flags, configuracion, limitaciones de act |
| CI workflow | [02-ci-workflow.md](02-ci-workflow.md) | Workflow del proyecto, estructura, como modificar/probar con act |

## Configuracion del proyecto

- `.actrc` — Flags por defecto para act (self-hosted, env vars, secrets)
- `.secrets` — Secretos para act (no committear, en `.gitignore`)
- `.github/workflows/ci.yml` — Workflow de GitHub Actions

## Comando rapido

```bash
# Instalar act
brew install act

# Validar sintaxis del workflow (sin ejecutar)
act -n

# Ejecutar CI completo localmente (self-hosted)
act pull_request

# Ejecutar solo el job quality-gates
act -j quality-gates

# Listar workflows
act -l
```
