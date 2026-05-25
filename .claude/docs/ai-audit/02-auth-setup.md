# 02 - Auth setup (PSI_API_KEY)

> El stack actual solo tiene UN setup de auth: la API key gratis de
> Google PageSpeed Insights. Las otras 2 tools (isitagentready,
> validators) son anonimas. Las viejas tools que requerian login
> (Ahrefs/Semrush) fueron descartadas — ver
> [01-tools-evaluadas.md](01-tools-evaluadas.md).

[< 01 Tools](01-tools-evaluadas.md) | [03 Arquitectura >](03-arquitectura.md)

## Donde vive la API key

```text
docker/env/dev-cli/
├── .local      <- PSI_API_KEY=<tu_key>
├── .dev
├── .stage
└── .prod
```

- Categoria `dev-cli`: LOCAL-ONLY, NUNCA sincronizada a remoto. Es la
  misma categoria que las AWS IAM keys del dev. Ver
  [secrets-strategy.md](../../rules/secrets-strategy.md).
- Gitignored: `docker/env/dev-cli/` esta en `.gitignore`.
- El tool resuelve la key en runtime via `grep -m1 '^PSI_API_KEY='`
  del archivo del env activo. NUNCA carga el `.env` completo. Cumple
  [env-files.md](../../rules/env-files.md).

## Setup por primera vez

1. Ir a https://console.cloud.google.com/apis/credentials
2. Crear/usar un proyecto Google Cloud (no requiere tarjeta).
3. En "APIs & Services > Library", buscar "PageSpeed Insights API" y
   habilitarla en tu proyecto.
4. Volver a "Credentials" -> "Create Credentials" -> "API key". Copiar
   la key.
5. (Opcional pero recomendado) Restringir la key:
   - "Application restrictions": None (porque la usa devtools desde la
     laptop, no un sitio web).
   - "API restrictions": "Restrict key" -> seleccionar SOLO "PageSpeed
     Insights API". Defensa en profundidad por si la key leakea.
6. Pegar en el `.env` del env donde la quieras usar:
   ```text
   # docker/env/dev-cli/.local
   PSI_API_KEY=<paste-here>
   ```
   - Sin comillas
   - Sin espacios alrededor del `=`
   - Una sola linea
7. Verificar que el tool la encuentra:
   ```bash
   PSI_ENV=local python -c "
   from ai_audit.tools.lighthouse_psi import LighthousePsi
   k = LighthousePsi().get_api_key()
   print('key encontrada:' if k else 'NO encontrada', len(k or '') if k else '')
   "
   ```
   (Imprime `key encontrada: 39` o similar. NUNCA imprime el valor.)
8. Correr el audit completo:
   ```bash
   python devtools/run.py ai_audit --env=prod
   ```

## ¿Una key por env?

No es obligatorio. La misma key sirve para auditar prod/stage/dev (la
restriccion es por API, no por origen de la request). Sugerido:

- Pegar la key en `.local`, `.dev`, `.stage`, `.prod` (4 copias). El
  `PSI_ENV` que setea `main.py` solo determina cual archivo leer.
- Alternativa minimalista: pegar solo en `.prod` y siempre correr con
  `--env=prod` (que es lo recomendado de todos modos por la rule).

## Free tier de Google PSI

| Limite | Valor |
|--------|-------|
| Requests/dia | 25 000 |
| Requests/100s | 100 |
| Costo | $0 (sin tarjeta, sin trial) |
| Renovacion | Diaria, automatica |

Suficiente para correr el audit hasta ~600 veces al dia (18 audits por
run × 25k / 18 = ~1388 runs/dia). Sin riesgo de costo accidental.

## Sintomas de problemas

| Sintoma | Causa probable | Fix |
|---------|----------------|-----|
| `lighthouse_psi` reporta SKIPPED | `.env` no existe o no contiene `PSI_API_KEY=` | Crear el archivo + agregar la key |
| ERROR `http 403: PSI_API_KEY invalido o sin quota` | Key revocada o quota diaria agotada | Verificar en Google Cloud Console |
| ERROR `http 429: rate-limited por PSI` | >100 req/100s | Esperar 100s y reintentar; el retry exp backoff del scraper lo gestiona |
| ERROR `api error: API key not valid` | La API "PageSpeed Insights" no esta habilitada en el proyecto | Habilitarla en el proyecto donde se creo la key |

## Rotacion

Si la key leakea (commit accidental, screenshot, etc.):

1. Revocar la key vieja en Google Cloud Console.
2. Crear nueva key (mismos pasos del setup).
3. Pegar la nueva en los `.env` afectados.
4. Si por accidente quedo en git history: `git filter-repo` + force
   push (coordinar con todos los devs porque rescribe history).

[< 01 Tools](01-tools-evaluadas.md) | [03 Arquitectura >](03-arquitectura.md)
