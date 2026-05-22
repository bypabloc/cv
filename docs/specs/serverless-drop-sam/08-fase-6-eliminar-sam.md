# 08 — Fase 6: eliminar SAM y CloudFormation del repo

> [Anterior: 07](07-fase-5-integracion-cli.md) | [README](README.md) | [Siguiente: 09](09-fase-7-docs.md)

Limpieza final: borrar todo lo que sostenia SAM y CloudFormation, y
destruir los stacks ya desplegados en AWS. Depende de Fase 5 (el CLI
nuevo ya funciona y reemplaza al viejo).

## Objetivo

1. Eliminar `sam_generate.py` del repo.
2. Borrar cualquier `template.yaml` efimero residual y limpiar los
   `.gitignore` / comentarios que mencionan SAM.
3. Destruir en AWS los stacks CloudFormation actuales
   (`portfolio-infra-*`, `portfolio-<lambda>-*`) en dev / stage / prod.
4. Reaprovisionar con el CLI nuevo.

> Estado verificado del repo (2026-05-21): NO hay `template.yaml`
> commiteados en `serverless/lambda/services/*/`. El `template.yaml` es
> efimero (gitignored) y solo aparece tras correr `sam-generate`
> localmente. Esta fase los borra si quedaron residuales en el working
> tree, pero no hay nada que des-commitear.

## Archivos afectados

### Eliminar

- `devtools/serverless/sam_generate.py` — su logica ya esta en
  `provisioner.py`.
- `serverless/lambda/services/*/template.yaml` — SOLO si quedaron
  residuales en el working tree (efimeros, gitignored). `rg` confirma que
  ninguno esta versionado.
- Cualquier `serverless/.aws-sam/` o `serverless/lambda/services/*/.aws-sam/`
  residual (directorio de build de SAM).

### Modificar

- `serverless/lambda/services/*/.gitignore` (los 4 services:
  `contact_form`, `tracking_pixel`, `stream_processor`, `db`) — quitar
  las entradas `template.yaml` / `.aws-sam/` (ya no se generan).
  Mantener `build/` y agregar `build.zip`.
- `serverless/.gitignore` — quitar entradas `.aws-sam/`, `samconfig.toml`
  si existen.
- `serverless/lambda/services/*/manifest.yaml` — actualizar el comentario
  de cabecera de los 4 (el archivo ya se renombro de `lambda.yaml` a
  `manifest.yaml` en la Fase 2): ya NO se genera SAM; devtools
  provisiona directo.
- `devtools/serverless/lifecycle.py` — `cmd_init` verifica `sam` en el
  PATH ([flags.py:34](../../../devtools/serverless/flags.py#L34) menciona
  "verifica sam + aws CLI"). Quitar la verificacion de `sam`.
- `devtools/serverless/flags.py` — el comentario de `init` (linea ~34)
  dice "verifica sam + aws CLI"; actualizar a "verifica aws CLI + uv".

### Verificar eliminacion completa

```bash
rg -l "aws-sam-cli|sam build|sam deploy|sam local|sam_generate|Transform: AWS::Serverless|samconfig" \
   devtools/ serverless/ --hidden
# Resultado esperado: 0 archivos (salvo docs/specs/ que documentan la migracion)
```

## Destruccion de la infra viva (AWS)

La infra actual son stacks CloudFormation. Decision tomada: recrear desde
cero, la data es descartable. Procedimiento por stage:

```bash
export AWS_PROFILE=tfs-dev
REGION=us-east-1

# 1. Listar los stacks del portfolio
aws cloudformation list-stacks --region $REGION \
  --query "StackSummaries[?starts_with(StackName,'portfolio-') && StackStatus!='DELETE_COMPLETE'].StackName"

# 2. Borrar los stacks de los Lambdas PRIMERO (importan de la infra)
for L in contact-form tracking-pixel stream-processor db; do
  aws cloudformation delete-stack --stack-name portfolio-$L-dev --region $REGION
  aws cloudformation wait stack-delete-complete --stack-name portfolio-$L-dev --region $REGION
done

# 3. Borrar el stack de infra DESPUES
aws cloudformation delete-stack --stack-name portfolio-infra-dev --region $REGION
aws cloudformation wait stack-delete-complete --stack-name portfolio-infra-dev --region $REGION

# 4. Repetir para stage y prod
```

> Orden: lambdas antes que infra. Si la infra todavia exportaba valores
> con `Export` y un lambda los importaba, CloudFormation bloquea el
> borrado de la infra. Con el esquema SSM actual ya no hay `Export`,
> pero el orden lambdas-primero es la regla segura.

### Recursos huerfanos a revisar tras borrar los stacks

CloudFormation borra lo que creo, pero conviene confirmar que no quedo
nada que choque con el reaprovisionamiento:

```bash
aws dynamodb list-tables --region $REGION \
  --query "TableNames[?starts_with(@,'portfolio-')]"
aws lambda list-functions --region $REGION \
  --query "Functions[?starts_with(FunctionName,'portfolio-')].FunctionName"
aws apigateway get-rest-apis --region $REGION \
  --query "items[?starts_with(name,'portfolio-')].name"
aws iam list-roles --query "Roles[?starts_with(RoleName,'portfolio-')].RoleName"
```

Si algo quedo huerfano, borrarlo a mano antes de reaprovisionar.

## Reaprovisionamiento con el CLI nuevo

```bash
export AWS_PROFILE=tfs-dev
for STAGE in dev stage prod; do
  python devtools/run.py serverless provision-infra --stage=$STAGE --aws-profile=tfs-dev
  for L in contact-form tracking-pixel stream-processor db; do
    python devtools/run.py serverless deploy --lambda=$L --stage=$STAGE --aws-profile=tfs-dev
  done
  python devtools/run.py serverless status --stage=$STAGE --aws-profile=tfs-dev
done
```

## Criterios de aceptacion

- **AC-6.1**: When se busca `sam_generate` en `devtools/`, Then no hay
  resultados.
- **AC-6.2**: When se busca `Transform: AWS::Serverless` en `serverless/`,
  Then no hay resultados.
- **AC-6.3**: When `git ls-files serverless/ | rg 'template\.yaml'`,
  Then no hay ningun `template.yaml` versionado (confirma que no quedo
  ninguno trackeado tras la migracion).
- **AC-6.4**: Given los stacks CloudFormation borrados, When
  `provision-infra` + `deploy` x4 en dev, Then los 4 Lambdas responden a
  una invocacion de prueba.
- **AC-6.5**: Given `cmd_init`, When se ejecuta sin SAM CLI instalado,
  Then NO falla ni advierte sobre SAM.
- **AC-6.6**: When se desinstala SAM CLI del sistema, Then ningun
  comando `serverless` falla por falta de `sam`.

## Verificacion incremental con comandos devtools

Esta fase borra SAM del repo. La verificacion clave: con SAM CLI
**desinstalado del sistema**, toda la grilla de comandos debe seguir
funcionando.

```bash
# Desinstalar SAM CLI del sistema (o sacarlo del PATH temporalmente),
# luego re-correr la grilla:
which sam || echo "sam no esta en el PATH — correcto"
python devtools/run.py serverless init             # ya no verifica sam
python devtools/run.py serverless help
python devtools/run.py serverless tests --type=unit
python devtools/run.py serverless deploy --lambda=contact-form --stage=dev --dry-run
python devtools/run.py serverless provision-infra --stage=dev --dry-run
python devtools/run.py serverless run --lambda=contact-form --stage=local \
  --event=events/create.json --runtime-mode=direct
```

Ningun comando debe fallar por falta de `sam`. Este es el chequeo que
demuestra que la dependencia de SAM esta realmente eliminada — no basta
con borrar `sam_generate.py`.

## Verificacion (Definition of Done de la fase)

```bash
rg -l "sam|Transform: AWS::Serverless" devtools/ serverless/ --hidden \
   --glob '!docs/**'                              # 0 resultados
devtools/.venv/bin/python -m pytest devtools/tests/unit/src/serverless/ -v
python devtools/run.py serverless init            # sin SAM, sin error
# grilla completa con SAM desinstalado (ver bloque incremental arriba)
python devtools/run.py serverless help
python devtools/run.py serverless tests --type=unit
# E2E: reaprovisionar dev y verificar (ver arriba)
```

- [ ] AC-6.1..AC-6.6 cubiertos
- [ ] `sam_generate.py` y los `template.yaml` eliminados
- [ ] `.gitignore` limpios
- [ ] Toda la grilla de comandos funciona con SAM desinstalado
- [ ] Stacks CloudFormation destruidos en dev/stage/prod
- [ ] Infra reaprovisionada con el CLI nuevo en los 3 stages
- [ ] Suite de tests verde

---

[Anterior: 07](07-fase-5-integracion-cli.md) | [README](README.md) | [Siguiente: 09](09-fase-7-docs.md)
