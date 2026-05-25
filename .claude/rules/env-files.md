# No leer archivos .env (CRÍTICO)

> Claude y los subagentes NUNCA leen, importan ni vuelcan el contenido de un
> archivo de entorno del repo. Si se necesita una key, se extrae SOLO esa key
> con bash y se pasa inline al comando — nunca el archivo completo.
>
> **Esta rule complementa [secrets-strategy.md](secrets-strategy.md)**: la
> umbrella define las 3 categorias (`client`, `server`, `dev-cli`) y el
> comando hermetico de sync; esta rule es la politica de NO leer el `.env`
> desde dentro de Claude/subagentes (aplica a las 3 categorias).

## Activacion

Aplica SIEMPRE a Claude y a cualquier subagente cuando se trabaje con:

- Cualquier `docker/env/{client,server,dev-cli}/.{local,dev,test,stage,prod}`
- Cualquier `.env`, `.env.local`, `.env.*` en cualquier ubicacion del repo
- Cualquier archivo cuyo proposito sea almacenar variables de entorno o
  secretos en formato `KEY=value`

Esta rule restringe el comportamiento del **agente** (Read tool, `cat`,
`source`, `head`, `tail`, etc.). NO regula el codigo del proyecto: el codigo
TypeScript/Python puede cargar `.env` como parte de su runtime normal.

## Regla raiz

**El contenido de un `.env` (y cualquier valor real de secreto) NUNCA debe
quedar en el contexto de Claude.** Ni en la ventana de conversacion, ni en el
output de un tool, ni en un mensaje al usuario, ni en un archivo temporal. Si
un valor de secreto aparece en el contexto, la rule fue violada — sin importar
como llego ahi.

Todas las reglas de abajo son consecuencias de esta. El patron de extraer una
key con bash funciona porque el valor viaja del archivo al proceso hijo SIN
pasar por stdout: nunca entra al contexto.

## Reglas criticas (SIEMPRE / NUNCA)

- **NUNCA** usar el Read tool sobre un archivo `.env` del repo.
- **NUNCA** volcar el archivo completo con `cat`, `batcat`, `head`, `tail`,
  `less`, `source`, ni redirigir su contenido a stdout.
- **NUNCA** imprimir un valor real de secreto en stdout — ni con `echo`, ni
  `printf`, ni `grep` sin pipe a un consumidor. Si el valor llega a stdout,
  llega al contexto de Claude (lo prohibido por la regla raiz).
- **NUNCA** copiar el contenido de un `.env` al contexto de la conversacion,
  a un archivo temporal, ni a un mensaje al usuario.
- **SIEMPRE** que se necesite una key, extraer SOLO esa key con bash usando
  un patron anclado (`grep -m1 '^KEY='`) y pasarla inline al comando, de modo
  que el valor pase directo al proceso y NUNCA aparezca en el contexto.
- **SIEMPRE** que la key vaya a una variable, mantenerla en el scope del
  comando (`KEY=... comando`), nunca exportarla a la sesion.

## Excepcion: archivos `.example` versionados

Los archivos `*.example` (ej. `docker/env/server/.example`) SI se pueden
leer: estan versionados en git y contienen solo placeholders, sin valores
reales. Sirven de plantilla — leerlos es seguro y a veces necesario para
saber que keys existen.

## Excepcion: devtools en flujo de deploy automatizado

`devtools/serverless/secrets_sync.py` lee `docker/env/server/.{stage}`
durante `serverless deploy --stage=<env>` para sincronizar a SSM. Es la
unica excepcion a la regla "NUNCA leer un .env":

- El valor pasa del archivo a un dict Python local a SSM, NUNCA a Claude.
- Tests automaticos (`test_secrets_sync.py`) verifican que el valor no
  aparece en stdout/stderr/subprocess args con un canary.
- El subprocess `aws ssm put-parameter` recibe el valor via tempfile
  (`--value file:///tmp/portfolio-ssm-X.tmp` con perms 0600), no como
  argumento (que seria visible en `ps aux`).

Claude y los subagentes NO ejecutan `serverless deploy` directamente:
solo el dev humano lo hace. Si Claude necesita revisar el estado del
sync, usa `serverless secrets-status --stage=<env>` (muestra hash
truncado a 4 chars, nunca el valor).

## Patron obligatorio: extraer una key

Para descubrir QUE keys existen sin ver valores, leer el `.example`. Para
USAR un valor real, extraer solo esa key:

```bash
# Extraer UNA key y usarla inline en el MISMO comando.
# grep -m1 '^KEY=' -> ancla a inicio de linea, corta en la 1a coincidencia.
# cut -d= -f2-     -> toma todo tras el primer '=' (soporta '=' en el valor).
DB_URL="$(grep -m1 '^DB_URL=' docker/env/server/.local | cut -d= -f2-)" \
  python serverless/scripts/migrate.py status
```

O pasandola directo como argumento, sin variable intermedia:

```bash
python devtools/run.py serverless db-migrate --stage=local \
  --db-url="$(grep -m1 '^DB_URL=' docker/env/server/.local | cut -d= -f2-)"
```

### Por que este patron es seguro

1. `grep -m1 '^KEY='` trae UNA sola linea (la de esa key), nunca el archivo
   entero. El `^` evita matchear keys que contengan el nombre como substring.
2. `cut -d= -f2-` extrae el valor sin volcar el resto del archivo.
3. El valor viaja por el pipe directo al proceso hijo (variable inline o
   argumento) y NUNCA se imprime en stdout — por lo tanto nunca entra al
   contexto de Claude (la regla raiz).
4. El valor vive solo en el scope del comando; no se exporta a la sesion ni
   se persiste en disco.
5. Si el valor lleva espacios o comillas, envolverlo en `"..."` como arriba.

> El comando NO debe terminar imprimiendo el valor. `grep ... | cut ...` a
> secas (sin consumidor) vuelca el valor a stdout y por ende al contexto —
> eso viola la regla raiz. Siempre debe haber un comando que CONSUMA la key
> (la variable inline `KEY=... comando`, o `--flag="$(...)"`).

> Nota WSL2: `grep` esta aliasado a `rg`. El patron `grep -m1 '^KEY=' file`
> funciona igual en `rg` (`-m1` = `--max-count=1`). Evitar `grep -E/-r/-rn`
> (ver `general.md`). Si hay duda, usar `rg -m1 '^KEY=' file | cut -d= -f2-`.

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| `Read docker/env/server/.local` | Vuelca todos los secretos al contexto | `grep -m1 '^KEY='` de la key puntual |
| `cat docker/env/server/.local` | Idem — expone el archivo entero | Idem |
| `source docker/env/server/.local` | Carga TODAS las keys a la sesion | Variable inline solo para el comando |
| `export DB_URL=...` en la sesion | La key persiste fuera del comando | `DB_URL=... comando` (scope acotado) |
| Copiar el `.env` a `./tmp/` para "trabajarlo" | El secreto queda en disco sin control | Extraer la key cuando se necesite |
| Pegar el contenido del `.env` en un mensaje | El secreto entra al historial | Nunca; referirse a la key por nombre |

## Verificacion

Antes de cerrar una tarea que toco env vars, confirmar que en el transcript
NO aparece:

- Ninguna llamada al Read tool sobre un `.env` (los `.example` son OK).
- Ningun `cat`/`source`/`head`/`tail` sobre un `.env`.
- Ningun valor real de secreto impreso en stdout o en un mensaje.

## Referencias cruzadas

- `security.md` — credenciales y secretos (`.env` no committeado, `PUBLIC_*`)
- `neon-management.md` — `DB_URL` es categoria `server`; resolver desde SSM
  en runtime, el `.env` solo lleva placeholders
- `general.md` — aliases rotos en WSL2 (`grep`, `find`)
