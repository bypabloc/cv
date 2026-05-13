# hooks

Orchestrates git hook validations for pre-commit and pre-push.

## Usage

```bash
python devtools/run.py hooks --type=pre-commit
python devtools/run.py hooks --type=pre-push
```

## Behaviour

1. Detect changed files in `server/`, `devtools/`, `dashboard/`, `landing/`.
2. If NO module has relevant changes -> early exit 0 (no Docker, no tests).
3. Otherwise execute the steps registered for the hook type.

The thin shell wrappers in `.git-hooks/pre-commit` and `.git-hooks/pre-push`
simply call this script. All file-detection and step-execution logic lives
here (and in `devtools/shared/` for classification, coverage and purity).

## Steps

See `.git-hooks/config.json` for the full list of steps and their
descriptions. Each step has its own `enabled` flag and can be skipped via
the `SKIP_STEPS` env var, e.g.:

```bash
SKIP_STEPS="coverage,integration" git push
```
