# mutation_testing

> Wrapper sobre `mutmut` con thresholds por criticidad. Política:
> `.claude/rules/ai-testing-independence.md`.

## Concepto

Coverage 80% no demuestra que los tests maten bugs reales. Mutation testing
muta el codigo (flip operadores, cambia constantes, remueve statements) y
verifica que los tests fallen. Si la mutacion **sobrevive**, el test es debil.

## Thresholds

| Categoria | Threshold | Paths default |
|-----------|-----------|---------------|
| **critical** | 85% | `apps/payments/services`, `apps/auth/services`, `common/security` |
| **standard** | 70% | `apps/orders/services`, `apps/orders/selectors` |
| **experimental** | 30% | (vacío; subir progresivo) |

Config en [`config.py`](./config.py). Agregar nuevos módulos ahí.

## Uso

```bash
# Paths explicitos
python devtools/run.py mutation_testing --paths=apps/payments,apps/auth

# Todos los paths de una categoria
python devtools/run.py mutation_testing --category=critical

# Todas las categorias
python devtools/run.py mutation_testing --all

# Plan sin ejecutar
python devtools/run.py mutation_testing --all --dry-run
```

## Pre-requisitos

- `mutmut` instalado en el venv del server (agregado a
  `server/pyproject.toml [dependency-groups.dev]`). Aplicar con:
  `python devtools/run.py upgrade_deps` o `uv sync` en server/
- Container `server` corriendo (verificado por el script):
  `python devtools/run.py docker up --env=local`
- Tests del server pasando (mutmut requiere baseline limpio)

## Exit codes

- `0` — todos los paths >= threshold
- `1` — al menos un path < threshold (o mutmut fallo en algun path)
- `2` — error interno (config inválido, container no disponible)

## Integración con git hooks

El step `mutation_testing` del orquestador (`.git-hooks/_common.py`) puede
correr en pre-push. **Default OFF** porque mutation testing es lento (5-15
min en suite mediana). Activar via `.git-hooks/config.json` cuando la suite
del módulo crítico este estable. Ver `tmp/git-hooks-patch/README.md`.

## Limitaciones / TODO

- mutmut 3.x cambio el formato de output. El parser actual (`_parse_mutmut_score`)
  busca lineas `killed: N` y `survived: N`. Si la version cambia, ajustar
  el parser
- No hay incremental mode todavia: cada `--paths` corre full mutation;
  evaluar usar `mutmut run --since=<commit>` cuando sea estable
- No reporta survivors por linea — para eso correr `mutmut show <id>` manual
- Frontend (TS) no esta cubierto. Stryker es el equivalente para JS/TS pero
  se evalua adopcion en Q3 2026
