---
name: python-devtools
description: >
  Python environment reference for this Astro portfolio. The ONLY Python in
  the repo lives in devtools/ (CLI orchestrator, Python 3.14 + uv venv) and
  .git-hooks/ (self-contained quality gates). Covers the CRITICAL gotcha that
  devtools code runs under devtools/.venv/bin/python (3.14.x), NOT the shell
  python3 (3.12.x in WSL2) — verifying with the wrong interpreter produces
  false SyntaxError reports. Covers PEP 758 (Python 3.14 allows except with
  multiple exception types without parentheses when there is no `as` clause),
  the py313 pin for bootstrap files (devtools/run.py + .git-hooks/**) via
  ruff.toml per-file-target-version, devtools package structure (main.py +
  flags.py + README.md per script, max 300 lines/file), canonical commands
  (python devtools/run.py <script>, test_runner, py_compile with the venv),
  Ruff config, and PEP 649 lazy annotations / PEP 695 type params.
  ALWAYS invoke this skill BEFORE answering ANY question about Python in this
  project, running or verifying devtools code, Python syntax errors in
  devtools/, the Python interpreter or venv to use, or git hook Python.
  NEVER answer Python-in-this-project questions from training data alone —
  the project pins Python 3.14 (PEP 758 syntax is valid) and the shell
  python3 is an older version that will misreport valid code as broken.
  Use when the user says "python", "python 3.14", "python 3.13", "devtools",
  "venv", "uv", "interprete python", "que python uso", "python interpreter",
  "syntaxerror", "syntax error python", "except sin parentesis", "except
  parentheses", "pep 758", "pep 649", "pep 695", "ruff", "py_compile",
  "compilar python", "correr devtools", "run devtools", "test devtools",
  "git hook python", "py313", "py314", "python del proyecto", "verificar
  python", "validar python".
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash
---

# Python en este portfolio (devtools + git hooks)

> Referencia del entorno Python del proyecto. Verificado 2026-05-16.
> NO responder preguntas de Python de este proyecto desde training data:
> el proyecto pinnea Python 3.14 y el `python3` del shell es mas viejo.

## Cuando invocar

- Usuario pregunta sobre Python en este proyecto (devtools, git hooks)
- Usuario reporta un `SyntaxError` en codigo de `devtools/`
- Usuario pregunta que interprete / venv usar, como correr o verificar devtools
- Usuario menciona PEP 758 / 649 / 695, Ruff, `py_compile`, uv
- Antes de editar/verificar cualquier `.py` en `devtools/` o `.git-hooks/`

## Cuando NO invocar

- Pregunta sobre Python en AWS Lambda → skill `aws-lambda-python`
- Pregunta sobre PostgreSQL/psycopg → skill `postgresql-18` / `neon`
- Pregunta de Python generico sin relacion con este repo

## Version de Python: 3.14 exclusivo (con UNA excepcion externa)

El proyecto usa **Python 3.14 y solo 3.14**. Codigo nuevo se escribe siempre
para 3.14.

| Arbol | Version | Por que |
|-------|---------|---------|
| `devtools/` (codigo del CLI) | **3.14** | Target del proyecto. Corre en `devtools/.venv` (uv) |
| `serverless/` (Lambdas AWS) | **3.13** | NO es decision del proyecto: AWS aun no ofrece runtime Lambda 3.14. Excepcion externa de la plataforma. Migrar a 3.14 apenas AWS lo permita |
| `devtools/run.py` + `.git-hooks/**` | compatibles con 3.13 | Corren en el `python3` del shell ANTES del re-exec al `.venv` 3.14. No es una version "soportada": es compatibilidad de bootstrap |

## Regla critica: el interprete correcto (SIEMPRE / NUNCA)

El codigo de `devtools/` corre con el Python del **venv del modulo**, NO con
el `python3` del shell. Verificar con el interprete equivocado produce
errores falsos.

| Que | Interprete | Version |
|-----|-----------|---------|
| `python3` del shell (WSL2) | sistema | 3.12.x |
| `devtools/.venv/bin/python` | venv del modulo (uv) | **3.14.x** |
| `devtools/run.py` (antes del re-exec) | sistema | 3.12/3.13 |
| `.git-hooks/*.py` | Python del shell que invoca el hook | 3.12/3.13 |
| Lambdas `serverless/` (runtime AWS) | runtime AWS | **3.13** (limite de AWS) |

- **SIEMPRE** verificar codigo de `devtools/` con `devtools/.venv/bin/python`.
- **NUNCA** usar `python3` pelado para compilar/correr/testear devtools.
- **NUNCA** reportar un `SyntaxError` en `devtools/` sin antes confirmarlo
  con `devtools/.venv/bin/python`.

### Comandos canonicos

```bash
# Compilar / chequear sintaxis de un archivo de devtools
devtools/.venv/bin/python -m py_compile devtools/<ruta>.py

# Correr un script de devtools (run.py se re-exec al .venv 3.14)
python devtools/run.py <script> [flags]

# Tests de devtools
python devtools/run.py test_runner --module=devtools --type=unit
```

## PEP 758: except sin parentesis (Python 3.14)

Python 3.14 permite `except` con multiples excepciones **sin parentesis**
cuando no hay clausula `as`:

```python
# Valido en Python 3.14 (PEP 758) — se usa en devtools/
except EOFError, KeyboardInterrupt:
    ...

# Sigue siendo valido; OBLIGATORIO si hay `as`
except (EOFError, KeyboardInterrupt) as exc:
    ...
```

Compilar ese codigo con `python3` 3.12 lanza
`SyntaxError: multiple exception types must be parenthesized`. **No es un
bug** — es una feature de 3.14 verificada con el interprete equivocado.

### Excepcion: archivos de bootstrap pinneados a py313

`devtools/run.py` y `.git-hooks/**/*.py` corren ANTES del re-exec al venv
3.14, en el Python del shell. Su `ruff.toml` los pinnea a `py313` via
`per-file-target-version`. En esos archivos NO usar sintaxis 3.14
(PEP 758 incluido) — deben correr en 3.12/3.13.

## Otras features de Python 3.14 en uso

- **PEP 649** (lazy annotations nativo): NO usar
  `from __future__ import annotations`.
- **PEP 695** (type parameter syntax): `def first[T](items: list[T]) -> T:`.
- Union moderna: `str | None`, nunca `Optional[str]`.

## Estructura de devtools (resumen)

- Entry point unico: `devtools/run.py` (plugin loader, re-exec a .venv 3.14).
- Cada script es un paquete: `main.py` (logica) + `flags.py` (validacion) +
  `README.md`. Modulos max ~300 lineas — partir por dominio al crecer.
- Ruff propio: `devtools/ruff.toml` autocontenido (sin `extend`).
- Deps: `devtools/pyproject.toml` + `devtools/uv.lock` (gestionado por uv).
- Bootstrap automatico: `run.py` corre `uv sync --frozen --project devtools`
  la primera vez (o si cambia el lockfile).

Detalle completo: regla `.claude/rules/python.md` y `.claude/rules/devtools.md`.

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| `python3 -m py_compile devtools/x.py` | Usa 3.12 del shell, falla con sintaxis 3.14 | `devtools/.venv/bin/python -m py_compile ...` |
| Reportar `SyntaxError` sin verificar interprete | Falso positivo si el codigo usa PEP 758 | Confirmar con `.venv/bin/python` antes |
| "Arreglar" `except A, B:` agregando parentesis en devtools/ | El codigo ya era valido en 3.14 | Dejarlo; solo agregar parentesis si hay `as` |
| Sintaxis 3.14 (PEP 758) en `devtools/run.py` o `.git-hooks/` | Esos archivos corren en py313 | Mantenerlos compatibles con 3.13 |
| `from __future__ import annotations` | PEP 649 lo hace innecesario en 3.14 | Eliminar el import |

## Validacion

Skill validada (2026-05-16) contra:

- Python real del proyecto: `devtools/.venv` → cpython 3.14.2
- `python3` del shell WSL2: 3.12.3
- PEP 758 (peps.python.org/pep-0758) — aceptado e incluido en Python 3.14
- Reglas `.claude/rules/python.md` y `.claude/rules/devtools.md`

## Soporte de idioma

- Frontmatter: ingles (matching logic)
- Cuerpo de la skill: espanol, terminos tecnicos en ingles
- Respuestas: espanol
