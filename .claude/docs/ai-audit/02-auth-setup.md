# 02 - Auth setup (Ahrefs + Semrush)

> Como crear cuentas free y guardar Playwright storageState para las
> 2 tools que requieren login. Las otras 2 (isitagentready,
> aibotchecker) son anonimas.

[< 01 Tools](01-tools-evaluadas.md) | [03 Arquitectura >](03-arquitectura.md)

## Donde vive el storageState

```text
docker/env/dev-cli/ai-audit/
├── ahrefs.json
└── semrush.json
```

- Categoria `dev-cli`: LOCAL-ONLY, NUNCA sincronizada a remoto. Es la
  misma categoria que las AWS IAM keys del dev. Ver
  [secrets-strategy.md](../../rules/secrets-strategy.md).
- Gitignored: `docker/env/dev-cli/` esta en `.gitignore`.
- Cada archivo contiene cookies + localStorage de la sesion. Es
  equivalente a una credencial — NO compartir.

## Setup por primera vez

### Ahrefs

1. Crear cuenta gratis en https://ahrefs.com/webmaster-tools (Ahrefs
   Webmaster Tools — version free de Ahrefs).
2. Verificar el dominio `the-full-stack.com` (TXT en Cloudflare DNS o
   etiqueta meta — Ahrefs guia paso a paso).
3. Correr el comando setup:

   ```bash
   python devtools/run.py ai_audit setup --tool=ahrefs
   ```

4. Se abre browser Playwright NO-headless. Loguearse manualmente.
5. Cuando el script detecta que estas logueado, guarda
   `docker/env/dev-cli/ai-audit/ahrefs.json` y cierra el browser.
6. Verificar: `ls -la docker/env/dev-cli/ai-audit/ahrefs.json` debe
   existir con perms 600.

### Semrush

1. Crear cuenta gratis en https://www.semrush.com/signup/ (cuenta
   free, no requiere tarjeta).
2. Setup:

   ```bash
   python devtools/run.py ai_audit setup --tool=semrush
   ```

3. Idem Ahrefs: browser interactivo, login manual, storageState
   guardado.

## Cuando expira el storageState

| Tool | Expiracion observada | Sintoma |
|------|----------------------|---------|
| Ahrefs | ~30 dias | Run reporta `PARTIAL` o `ERROR` con "login required" en el log |
| Semrush | ~14 dias | Run reporta `PARTIAL` o redirige a /login |

Cuando expira: re-correr `setup --tool=<X>`. El comando sobrescribe
el `.json` con la sesion nueva.

## Como verificar el storageState

```bash
# Estructura del archivo (NO el contenido, son cookies)
jq 'keys' docker/env/dev-cli/ai-audit/ahrefs.json
# Debe imprimir: ["cookies", "origins"]

# Numero de cookies guardadas
jq '.cookies | length' docker/env/dev-cli/ai-audit/ahrefs.json
# >0 indica sesion guardada

# Validar que sigue siendo valida sin abrir browser
python devtools/run.py ai_audit setup --tool=ahrefs --check-only
# Imprime VALID o EXPIRED
```

## Seguridad

- El storageState es una credencial. Trato igual que una AWS IAM key
  personal.
- NUNCA commitear al repo (gitignored en `.gitignore` raiz +
  `docker/env/dev-cli/.gitignore`).
- NUNCA compartir el archivo por chat ni copiarlo a otra maquina sin
  cifrar.
- Si se compromete: rotacion = cambiar password de la cuenta + correr
  `setup` de nuevo.
- Si la maquina se reemplaza: re-correr `setup` desde cero en la
  nueva.

## Que pasa si no hay storageState

- Sin `ahrefs.json`: el run reporta `SKIPPED` para todos los targets
  de Ahrefs. El reporte final lo lista.
- Sin `semrush.json`: idem para Semrush.
- isitagentready + aibotchecker siguen corriendo normal (no requieren
  auth).
- Si queres correr SOLO las 2 publicas: `--tools=isitagentready,aibotchecker`.

## Flag para deshabilitar tools especificas

```bash
# Por ej. en una maquina sin cuentas Ahrefs/Semrush configuradas:
python devtools/run.py ai_audit --tools=isitagentready,aibotchecker
```

El comando no falla si faltan storageStates de los tools NO incluidos
en `--tools=`.

[< 01 Tools](01-tools-evaluadas.md) | [03 Arquitectura >](03-arquitectura.md)
