# 09 - Paralelizacion con git worktrees

> Que fases del plan se pueden ejecutar en worktrees concurrentes
> sin colision de archivos, y cuales son secuenciales.

[< 08 Commits](08-commits.md) | [10 Verificacion E2E >](10-verificacion-e2e.md)

## Base secuencial (NO worktree-safe)

Los siguientes commits tocan archivos transversales y deben hacerse
en orden, en la rama principal del plan:

| Commit | Por que es secuencial |
|--------|----------------------|
| C1 (docs permanentes) | Crea `.claude/*` que el resto puede referenciar |
| C2 (scaffold) | Toca `devtools/pyproject.toml` + `uv.lock` + `.gitignore` (centrales) + crea contratos en `tools/base.py` |
| C3 (auth) | Toca `main.py` para wire del subcomando setup |
| C9 (orquestador) | Toca `main.py` para wire del comando default + `scraper.py` que importa todos los tools |
| C10 (cleanup) | Toca `git rm -r docs/specs/` (estado final del repo) |

## Fases worktree-safe (paralelizables)

### Tabla de paralelizacion: los 4 scrapers (C4-C7)

| Worktree | Archivos exclusivos | Tests exclusivos | Fixture exclusivo |
|----------|---------------------|------------------|-------------------|
| W4 isitagentready | `devtools/ai_audit/tools/isitagentready.py` | `devtools/tests/unit/src/ai_audit/tools/test_isitagentready.py` | `fixtures/isitagentready/` |
| W5 aibotchecker | `devtools/ai_audit/tools/aibotchecker.py` | `tests/.../test_aibotchecker.py` | `fixtures/aibotchecker/` |
| W6 ahrefs | `devtools/ai_audit/tools/ahrefs.py` | `tests/.../test_ahrefs.py` | `fixtures/ahrefs/` |
| W7 semrush | `devtools/ai_audit/tools/semrush.py` | `tests/.../test_semrush.py` | `fixtures/semrush/` |

Los 4 cumplen los 3 checks de paralelizabilidad:

- **File Exclusivity**: cada uno solo crea archivos en su carpeta.
- **Interface Stability**: dependen solo de `tools/base.py` ya
  commiteado en C2.
- **Bounded Scope**: parsear DOM de UNA tool + tests. No tocan ni
  `main.py`, ni `scraper.py`, ni `report.py`, ni `auth.py`.

Excepcion: el archivo `devtools/ai_audit/tools/__init__.py` (el
registry) debe actualizarse al final, cuando los 4 worktrees
mergean. Una de dos estrategias:

- **Strategy A (recomendada)**: el ultimo de los 4 commits que
  mergea agrega su entrada al registry. Conflicto sencillo de
  resolver.
- **Strategy B**: dejar el registry stub en C2 con las 4 entradas ya
  declaradas (apuntando a clases que aun no existen — falla typecheck
  hasta que cada worktree mergea su tool). Mas complejo.

Elegir Strategy A.

### Lo que NO se paraleliza

- C8 (report.py) y C9 (scraper.py) podrian solaparse pero ambos
  necesitan los 4 tools listos (C4-C7) para sus tests de
  integracion. Mejor secuencial:
  `C2 -> C3 -> [C4||C5||C6||C7] -> C8 -> C9 -> C10`.
- Documentos del plan (`docs/specs/ai-audit-tool/*`) ya estan
  escritos en C1 y NO se vuelven a tocar (la spec es read-only durante
  ejecucion; cualquier nueva decision se anota y se materializa al
  cerrar el plan).

## Como lanzar un worktree

Para un worktree por tool (asumiendo `feature/ai-audit-devtools` ya
existe en main):

```bash
# Desde la raiz del repo
git worktree add ../portfolio-ai-audit-tool-X feature/ai-audit-devtools
cd ../portfolio-ai-audit-tool-X

# Trabajar:
# - Crear devtools/ai_audit/tools/<X>.py
# - Crear fixture + test
# - Verify local
git add devtools/ai_audit/tools/<X>.py devtools/tests/unit/src/ai_audit/tools/test_<X>.py \
        devtools/tests/unit/src/ai_audit/fixtures/<X>/
git commit -m "feat(devtools): ai_audit tool <X> (parser + fixture + tests)"
git push origin feature/ai-audit-devtools

# Cleanup
cd ..
git worktree remove portfolio-ai-audit-tool-X
```

Limite recomendado: 4 worktrees concurrentes (las 4 tools). Mas no
agrega valor porque las otras fases dependen de estas.

## Anti-patterns

- Lanzar worktrees ANTES de mergear C2 (scaffold). Sin `tools/base.py`
  no hay contrato comun = conflict on import.
- Tocar `main.py` desde un worktree de tool. Es archivo central, se
  edita solo en C3 y C9.
- Modificar `pyproject.toml` desde varios worktrees a la vez (uv.lock
  conflict garantizado).
- Capturar el fixture HTML desde un worktree sin commitear el
  `sample.html` — el siguiente worktree no podra reproducir el test.

[< 08 Commits](08-commits.md) | [10 Verificacion E2E >](10-verificacion-e2e.md)
