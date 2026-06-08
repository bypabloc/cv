# 05 — Estado local de devtools

> [<- 04-deploy-operacion](04-deploy-operacion.md) | [README](README.md)

Sin CloudFormation, lo que daba el estado declarativo (saber que se
creo, decidir si un recurso esta al dia, borrar en orden) lo reimplementa
devtools de forma minima: un archivo JSON por `(scope, stage)`. Este
capitulo documenta ese archivo de estado.

## 1. Donde vive

```text
serverless/lambda/.state/
├── .gitignore           # ignora *.json
├── infra-dev.json
├── infra-prod.json
├── contact-form-dev.json
├── tracking-pixel-dev.json
├── stream-processor-dev.json
├── db-dev.json
└── ... (un archivo por recurso/lambda x stage)
```

El nombre del archivo es `<scope>-<stage>.json`:

- `scope` — `infra` (el conjunto de recursos compartidos) o el nombre
  de un Lambda (`contact-form`, `tracking-pixel`, `stream-processor`,
  `db`).
- `stage` — `dev` o `prod`.

`devtools/serverless/state.py` lee, escribe y compara estos archivos.

## 2. Es local y gitignored

`serverless/lambda/.state/` esta en `.gitignore` (`*.json`). El estado
es **local de la maquina** que corre los comandos `serverless`, NO se
versiona ni se comparte:

- Es derivado: refleja lo que existe en una cuenta AWS concreta, no es
  la fuente de verdad de la config (esa es `manifest.yaml` +
  `resources/`).
- Cada cuenta / stage tiene su propio estado; versionarlo provocaria
  conflictos y drift entre maquinas.
- Si el archivo se pierde, `serverless status` lo reconstruye
  consultando AWS, o un `deploy` lo regenera tratando los recursos como
  nuevos (los comandos AWS son idempotentes).

## 3. Esquema de un archivo de estado

```jsonc
{
  "scope": "contact-form",        // "infra" | nombre del lambda
  "stage": "dev",                 // dev | prod
  "config_hash": "sha256:...",    // hash de la config renderizada (IAM, env, memory, ...)
  "code_hash": "sha256:...",      // hash del contenido de core/ (solo lambdas)
  "resources": {                  // identificadores de lo creado
    "role_arn": "arn:aws:iam::...:role/portfolio-contact-form-dev",
    "role_name": "portfolio-contact-form-dev",
    "function_arn": "arn:aws:lambda:...:function:portfolio-contact-form-dev",
    "function_name": "portfolio-contact-form-dev",
    "log_group": "/aws/lambda/portfolio-contact-form-dev",
    "api_resource_id": "abc123",
    "api_method": "POST /contact",
    "event_source_uuid": null
  },
  "updated_at": "2026-05-21T10:00:00Z"
}
```

| Campo | Que es |
|-------|--------|
| `scope` | `infra` o el nombre del Lambda |
| `stage` | el entorno del recurso |
| `config_hash` | hash de la config aplicada (rol IAM, env vars, memoria, timeout, wiring del trigger) |
| `code_hash` | hash del contenido de `core/` del Lambda — solo en lambdas, no en `infra` |
| `resources` | identificadores AWS de lo creado (ARNs, nombres, IDs) |
| `updated_at` | timestamp ISO 8601 del ultimo `deploy` |

## 4. El diff de hashes decide la accion del deploy

`config_hash` y `code_hash` son la clave: en cada `deploy`, devtools los
recalcula y los compara con los del archivo de estado.

```text
config_hash y code_hash coinciden con disco  -> noop  (nada que hacer)
solo cambio code_hash                        -> update-function-code
cambio config_hash                           -> update-function-configuration (+ IAM si cambio)
no hay archivo de estado                      -> create  (secuencia completa)
```

Esto hace el `deploy` **idempotente y re-ejecutable**: correrlo dos
veces sin cambios es un no-op; si un `deploy` fallo a mitad, re-correrlo
completa lo que falte. Es el reemplazo minimo del estado declarativo de
CloudFormation.

## 5. Comandos que usan el estado

| Comando | Como usa el estado |
|---------|--------------------|
| `deploy` | Carga el estado previo, calcula el diff de hashes, aplica la accion, y al terminar **guarda** el estado nuevo |
| `status` | Compara el estado local contra los `describe-*` reales de AWS — deteccion de drift |
| `destroy` | Lee el estado para saber que borrar y en que orden inverso; al terminar **borra** los archivos de estado del stage |

```bash
# Ver el estado de un lambda (local vs AWS)
python devtools/run.py serverless status --lambda=contact_form --stage=dev --aws-profile=tfs-dev

# Destruir un lambda y limpiar su estado
python devtools/run.py serverless destroy --lambda=contact_form --stage=dev --yes --aws-profile=tfs-dev

# Destruir todo el backend de un stage (lambdas + infra) y limpiar todos los estados
python devtools/run.py serverless destroy --stage=dev --yes --aws-profile=tfs-dev
```

## 6. Limitaciones (trade-offs asumidos)

- **Sin rollback transaccional.** Si `deploy` falla a mitad, devtools
  deja recursos parciales. Mitigacion: el estado registra que se creo y
  el comando es idempotente — re-ejecutar `deploy` completa lo que falte.
- **Drift no automatico.** Si alguien cambia un recurso a mano en la
  consola AWS, devtools no lo detecta solo. Mitigacion: `serverless
  status` compara estado local vs AWS bajo demanda.
- **Orden de dependencias manual.** Lo que CloudFormation resolvia por
  grafo, devtools lo hace en orden fijo (crear) y orden inverso
  (destruir), documentado en [01-arquitectura-5-stacks.md](01-arquitectura-5-stacks.md).

---

[<- 04-deploy-operacion](04-deploy-operacion.md) | [README](README.md)
