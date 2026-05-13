# upgrade_deps

> Bumpea las dependencias de los manifestos del proyecto a la ultima version
> estable disponible en PyPI / npm registry.

## Uso

```bash
# Preview (no escribe archivos)
python devtools/run.py upgrade_deps --dry-run

# Aplica los upgrades
python devtools/run.py upgrade_deps
```

## Manifestos cubiertos

| Manifest | Registry |
| --- | --- |
| `server/pyproject.toml` | PyPI |
| `devtools/pyproject.toml` | PyPI |
| `dashboard/package.json` | npm |
| `landing/package.json` | npm |

## Comportamiento

1. Parsea cada manifest:
   - **PEP 621/735** (pyproject.toml): lee `[project.dependencies]` y
     `[dependency-groups.<grupo>]`, extrae specs pinned `name[extras]<op>version`.
     Soporta `==`, `>=`, `<=`, `>`, `<`, `!=`, `~=`, `===`. Skip de markers de
     entorno (`; python_version<X`).
   - **package.json**: lee `dependencies`, `devDependencies` y
     `pnpm.overrides`. Saltea protocolos no-registry (`workspace:`,
     `file:`, `link:`, `git+`, `http(s):`, `npm:`, `github:`).

2. Consulta concurrentemente cada paquete:
   - **PyPI**: `https://pypi.org/pypi/<pkg>/json` (descarta yanked).
   - **npm**: `https://registry.npmjs.org/<pkg>` (incluye scoped).

3. Filtra **pre-releases** (alpha/beta/rc/dev) y elige la version estable
   mas alta. Si solo hay pre-releases, se omite el paquete.

4. Compara con la version actual:
   - `upgrade`: latest > actual, se reescribe el manifest.
   - `ok`: ya estas en latest.
   - `skip`: solo hay pre-releases disponibles.
   - `error`: no se pudo consultar (404, timeout).

5. **Preserva el prefijo original** al escribir:
   - `astro: "^6.1.0"` -> `astro: "^6.2.1"` (mantiene `^`)
   - `Django==6.0.4` -> `Django==6.0.5` (mantiene `==`)
   - `ruff>=0.15.12` -> `ruff>=0.15.13` (mantiene `>=`)
   - `typescript: "~6.0.2"` -> `typescript: "~6.0.3"` (mantiene `~`)

## Concurrencia

Hasta 10 requests simultaneos por registry. PyPI y npm tienen rate limits
generosos para manifestos pequenos (<100 paquetes), no deberia haber
problemas.

## Lo que NO hace

- **NO instala** las nuevas versiones (`uv sync` / `pnpm install`).
- **NO regenera lockfiles** (`uv.lock`, `pnpm-lock.yaml`).
- **NO rebuildea** containers Docker.
- **NO ejecuta tests** post-upgrade.

Despues de correr el script, vos decides:

```bash
# Reinstalar deps en containers
python devtools/run.py docker rebuild --service=server
python devtools/run.py docker rebuild --service=dashboard
python devtools/run.py docker rebuild --service=landing

# Correr tests para verificar
python devtools/run.py test_runner
```

## Tests

Tests unitarios en `devtools/tests/unit/src/upgrade_deps/`:

```bash
devtools/.venv/bin/python -m pytest devtools/tests/unit/src/upgrade_deps/ -c devtools/tests/pytest.ini
```
