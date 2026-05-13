# weak_assertion

> Detector AST de asserts vagos en archivos de test Python (política
> `.claude/rules/ai-testing-independence.md`).

## Patrones detectados

| Patron | Ejemplo rechazado | Fix sugerido |
|--------|-------------------|--------------|
| Comparación vaga | `assert x > 0` / `assert x < 100` | `assert x == 42` |
| Check de None | `assert result is not None` | `assert result == {'status': 'ok'}` |
| Verificación de tipo | `assert isinstance(x, dict)` | `assert x == {'a': 1}` (typecheck estático se encarga) |
| len comparado | `assert len(items) > 0` | `assert items == [item_a, item_b]` |
| Truthy check | `assert flag` | `assert flag is True` o `assert flag == 'ok'` |

## Bypass

- **Inline**: `# noqa: WEAK-ASSERT` en la misma linea, con razón en comentario
- **Por archivo**: `# weak-assert: skip-file` en cualquier linea del archivo
- **Step entero**: `SKIP_STEPS="weak_assertion" git commit ...`

## Uso CLI

```bash
# Lista explicita
python devtools/run.py weak_assertion --files=server/tests/unit/sample.py,server/tests/feature/orders.py

# Toma archivos staged (pre-commit)
python devtools/run.py weak_assertion --git-mode=staged

# Toma archivos no mergeados (pre-push)
python devtools/run.py weak_assertion --git-mode=unmerged

# Modo silencioso (solo conteo)
python devtools/run.py weak_assertion --git-mode=staged --quiet
```

## Exit codes

- `0` - sin findings (o sin archivos relevantes)
- `1` - al menos un weak assertion detectado

## Integración con git hooks

El step `weak_assertion` del orquestador (`.git-hooks/_common.py`) invoca
este script en pre-commit. Para activar:

1. Editar `.git-hooks/config.json`:
   ```json
   "weak_assertion": {
     "name": "Weak assertion detector",
     "enabled": true,
     "description": "Rechaza asserts vagos en archivos de test staged."
   }
   ```
2. Agregar el handler en `.git-hooks/_common.py` (ver `tmp/git-hooks-patch/`).

## Lista lógica

La lógica AST vive en `devtools/shared/weak_assertion.py` para que sea
testeable y reutilizable. Este script (`devtools/weak_assertion/`) es solo
el wrapper CLI + integración git-mode.
