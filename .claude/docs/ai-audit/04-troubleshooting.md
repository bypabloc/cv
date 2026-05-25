# 04 - Troubleshooting

> Sintomas comunes durante un run de `ai_audit` y como diagnosticar.

[< 03 Arquitectura](03-arquitectura.md) | [README >](README.md)

## "playwright: command not found" en el primer run

**Sintoma**: el primer run falla con `Executable doesn't exist at .../chromium-XXXXX/chrome-linux/chrome`.

**Diagnostico**: chromium no fue instalado por Playwright todavia.

**Fix**:

```bash
cd devtools && uv run playwright install chromium
```

El script idealmente lo invoca automatico en el primer run, pero si
falla por permisos / disco, ejecutarlo a mano.

## Mas del 50% de los targets reportan BLOCKED

**Sintoma**: el reporte final dice
`>= 50% targets BLOCKED, exit code 1`.

**Diagnostico posible**:

1. La IP esta saturada de captchas porque corriste varios runs
   seguidos. -> esperar 1-2h, reintentar.
2. VPN/proxy interfiere. -> deshabilitar VPN y reintentar.
3. La tool cambio el frontend y dispara captcha a TODO trafico
   headless. -> actualizar `tools/<X>.py` (selectores nuevos).

**Como confirmar**: abrir
`tmp/ai-audit/<ts>/runs/<target>_<tool>_error.png` (Playwright
guarda screenshot al fallar). Si se ve un Cloudflare challenge, es
diagnostico 1 o 2. Si se ve UI rota / vacia, es diagnostico 3.

## Un tool reporta PARTIAL en todos los targets

**Sintoma**: Ahrefs o Semrush devuelven `PARTIAL` para los 6 niches.

**Diagnostico**: storageState expiro o no es valido.

**Fix**:

```bash
# Validar primero
python devtools/run.py ai_audit setup --tool=ahrefs --check-only
# Si dice EXPIRED, regenerar:
python devtools/run.py ai_audit setup --tool=ahrefs
```

## ERROR en isitagentready solamente

**Sintoma**: las otras 3 tools OK, isitagentready siempre ERROR.

**Diagnostico**: el DOM de la tool cambio. Es esperable cada pocos
meses (es un producto nuevo, abril 2026).

**Como diagnosticar**:

1. Abrir `tmp/ai-audit/<ts>/runs/<target>_isitagentready.log`. Buscar
   "ParseError" o "selector not found".
2. Abrir `tmp/ai-audit/<ts>/runs/<target>_isitagentready_error.png`
   para ver el estado del DOM al momento del fallo.
3. Inspeccionar el sitio en browser: `https://isitagentready.com`,
   correr un audit manual, comparar selectores.
4. Actualizar `devtools/ai_audit/tools/isitagentready.py` (los
   selectores estan en una constante `SELECTORS` al tope).
5. Actualizar el fixture HTML en
   `devtools/tests/unit/src/ai_audit/fixtures/isitagentready/` con un
   capture nuevo.
6. Re-correr tests + script.

## "Playwright: Error: page.goto: net::ERR_TIMED_OUT"

**Sintoma**: timeout de 30s en el `page.goto()` inicial.

**Diagnostico**:

- Si pasa solo en algunos targets: la URL especifica esta caida.
  Verificar `curl -I <target>`.
- Si pasa en todos los targets de un tool: la tool esta caida.
  Verificar abriendo la URL del audit en browser.
- Si pasa en todos los targets de todas las tools: tu conexion. El
  retry con backoff suele resolverlo.

## El script no arranca: `ModuleNotFoundError: No module named 'playwright'`

**Sintoma**: error de import al iniciar.

**Diagnostico**: `uv sync` no se ejecuto despues de agregar
playwright a `devtools/pyproject.toml`.

**Fix**:

```bash
cd devtools && uv sync --frozen
```

`devtools/run.py` lo hace automatico cuando el lockfile cambia, pero
en algunos casos (ej. checkout de rama nueva) puede no triggerear.

## El reporte sale en `tmp/ai-audit/` pero esta vacio

**Sintoma**: `report.md` solo tiene encabezado, sin tabla.

**Diagnostico**: el run termino exit 2 (config invalida) antes de
escribir el snapshot.

**Fix**: leer stdout del run anterior. Mensajes tipicos:

- `No targets resolved for env=prod niches=...` -> los flags
  filtraron a 0 niches. Revisar `--niches` / `--targets`.
- `No tools enabled` -> `--tools=` con valor invalido. Revisar
  spelling.
- `playwright install required` -> ver primera seccion.

## El run consume mucha RAM (Chromium > 2GB)

**Sintoma**: el dev box se ralentiza durante el run.

**Diagnostico**: normal — chromium pesa. Para 6 niches x 4 tools
secuencial usa ~1.5GB peak.

**Mitigacion**: cerrar otras apps. Si es persistente, partir el run
en 2 con `--niches=`:

```bash
python devtools/run.py ai_audit --niches=hub,fintech,generic
python devtools/run.py ai_audit --niches=architect,leader,vibe
```

## Bug del script (no de las tools)

Si el script crashea con stacktrace Python (no Playwright):

1. Capturar stacktrace completo.
2. Verificar que estas en la rama mergeada de
   `feature/ai-audit-devtools` (los commits con el codigo real).
3. `python -m compileall -q devtools/ai_audit` para confirmar que el
   codigo compila.
4. Si la causa raiz no es obvia: abrir issue + adjuntar stacktrace +
   estado de `tmp/ai-audit/<ts>/`.

[< 03 Arquitectura](03-arquitectura.md) | [README >](README.md)
