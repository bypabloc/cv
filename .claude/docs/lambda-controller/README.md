# Lambda Controller Architecture

> Patron de arquitectura para AWS Lambdas en Python: un Lambda atiende
> muchas operaciones via `operation + action`, cada una resuelta a un
> controller polimorfico con validacion Pydantic y ciclo de vida
> `preload -> validate -> execute`.

Esta documentacion describe el formato. El scaffold reproducible vive en
[.claude/templates/lambda-controller/](../../templates/lambda-controller/).
La rule operativa es [.claude/rules/lambda-controller.md](../../rules/lambda-controller.md).

## Tabla de contenidos

| Documento | Cuando leer |
| --------- | ----------- |
| [01-architecture.md](01-architecture.md) | Entender el patron: capas, flujo, por que existe |
| [02-handler-and-routing.md](02-handler-and-routing.md) | Como `handler.py` enruta `operation + action` a un controller |
| [03-controllers-and-models.md](03-controllers-and-models.md) | Como escribir un controller y su modelo de validacion |
| [04-testing.md](04-testing.md) | Como verificar y testear un Lambda de este tipo |
| [05-create-and-refactor.md](05-create-and-refactor.md) | Receta para crear uno nuevo o refactorizar un Lambda monolitico |
| [06-devtools-operations.md](06-devtools-operations.md) | Operar el Lambda con devtools: manifest.yaml, `run`, `deploy`, `destroy`, `status`, `tests` |

## Reglas criticas

- SIEMPRE el entrypoint se llama `handler.py`, vive en `core/` y la
  funcion es `lambda_handler` (Handler AWS: `core.handler.lambda_handler`).
- SIEMPRE el evento trae `operation`, `action` y `data` (objeto).
- SIEMPRE el nombre de la clase controller es `action.capitalize()`.
- SIEMPRE el controller hereda de `BaseController` e implementa `execute()`.
- SIEMPRE `execute()` y las fases devuelven `{is_valid, data, code}`.
- SIEMPRE la logica de negocio vive en `core/services/`.
- SIEMPRE registrar la operacion en `settings/operations.py` (`OPERATIONS`).
- SIEMPRE los tests siguen el estandar de `04-testing.md`: un archivo
  por escenario en `tests/{unit,integration}/`.
- SIEMPRE el lambda trae un `manifest.yaml` (manifiesto de config);
  devtools lo lee directamente para provisionar el Lambda con AWS CLI.
- SIEMPRE el lambda se opera con el script `serverless` de devtools:
  `run --stage=<env>` (ejecutar), `deploy` (desplegar), `destroy`
  (eliminar), `status` (estado) y `tests --type=<unit|integration|coverage>`
  (testear).
- NUNCA poner logica de negocio en `handler.py` ni en los controllers —
  el handler enruta, el controller orquesta.
- NUNCA registrar controllers a mano — se descubren por convencion de
  nombres (`controllers.<controller>.<action>.<Action>`).
- NUNCA commitear `build/`, `build.zip` ni el archivo de estado de
  devtools (`serverless/lambda/.state/`) — son efimeros / locales.

## Navegacion

- Scaffold: [.claude/templates/lambda-controller/](../../templates/lambda-controller/)
- Rule: [.claude/rules/lambda-controller.md](../../rules/lambda-controller.md)
- Skill: `lambda-controller` (invocable con `/lambda-controller`)
- Referencia AWS Lambda Python (runtime, Powertools, IAM, costos):
  [.claude/docs/aws-lambda/](../aws-lambda/) o skill `aws-lambda-python`
