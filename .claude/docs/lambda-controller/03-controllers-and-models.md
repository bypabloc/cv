# 03 - Controllers, services y models

> Anterior: [02 - Handler y routing](02-handler-and-routing.md) | Siguiente: [04 - Testing](04-testing.md)

## Las tres capas de una operacion

Una operacion completa se reparte en tres archivos:

| Archivo | Capa | Rol |
|---------|------|-----|
| `models/<operation>.py` | Modelo | Valida la estructura del payload (Pydantic) |
| `controllers/<operation>/<action>.py` | Controller | Orquesta: valida -> service -> normaliza |
| `services/<operation>_service.py` | Service | Logica de negocio pura |

## El modelo: validacion de estructura

Un modelo Pydantic por accion valida el campo `data` del evento. Solo
valida **estructura y formato**, no logica de negocio.

```python
from pydantic import BaseModel
from pydantic import field_validator


class PaymentsCreateModel(BaseModel):
    """Valida el payload de payments/create."""

    transaction_id: str
    amount: int

    model_config = {'extra': 'forbid'}  # rechaza campos no declarados

    @field_validator('amount')
    @classmethod
    def amount_must_be_positive(cls, value: int) -> int:
        """El monto debe ser estrictamente positivo."""
        if value <= 0:
            raise ValueError('amount debe ser mayor a 0')
        return value
```

`model_config`:

- `extra='forbid'` - rechaza campos no declarados (estricto, recomendado).
- `extra='allow'` - los acepta y preserva (passthrough hacia downstream).

## El controller: orquestador delgado

El controller hereda de `BaseController` y define tres cosas:

```python
from models.payments import PaymentsCreateModel
from services.payments_service import ServiceError, create_payment
from utils.base_controller import BaseController


class Create(BaseController):
    """Controller para la accion 'create' de la operacion 'payments'."""

    event_model = PaymentsCreateModel   # modelo de la fase validate
    arn_config_key = 'arn_payments'     # ARN downstream para la fase preload

    def execute(self) -> dict:
        """Orquesta payments/create: delega al service, normaliza salida."""
        data = self.validated_data      # instancia de PaymentsCreateModel
        try:
            result = create_payment(
                transaction_id=data.transaction_id,
                amount=data.amount,
                arn=self.arn,
            )
        except ServiceError as exc:
            return {
                'is_valid': False,
                'data': {'error_code': exc.error_code,
                         'message': exc.message},
                'code': exc.code,
            }
        return {'is_valid': True, 'data': result, 'code': 0}
```

Reglas del controller:

- El **nombre del archivo** es la forma snake_case de `action`
  (`create` -> `create.py`, `verify-magic-link` ->
  `verify_magic_link.py`).
- El **nombre de la clase** es la forma PascalCase de `action`
  (`create` -> `Create`, `verify-magic-link` -> `VerifyMagicLink`).
- `event_model` - modelo Pydantic; lo usa la fase `validate`.
- `arn_config_key` - campo de `AppConfig` con el ARN downstream; lo usa
  la fase `preload`. Dejar `''` si no invoca otro Lambda.
- `execute()` NO tiene logica de negocio: extrae datos validados, llama
  al service, traduce el resultado/error a `{is_valid, data, code}`.
- `self.validated_data` es la instancia del modelo, ya validada.
- `self.arn` ya esta resuelto por `preload()` cuando llega a `execute()`.

## El service: logica de negocio

El service concentra la logica de negocio. NO conoce el formato del
evento Lambda ni de la respuesta — recibe datos simples y devuelve
datos simples, o lanza `ServiceError`.

```python
class ServiceError(Exception):
    """Error de negocio. El controller lo traduce a {is_valid: False}."""

    def __init__(self, message: str, *, code: int,
                 error_code: str = 'SERVICE_ERROR') -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.error_code = error_code


def create_payment(*, transaction_id: str, amount: int,
                    arn: str) -> dict:
    """Crea un pago invocando el Lambda downstream."""
    response = invoker_dispatch(arn=arn, data={...})
    if not response:
        raise ServiceError('Error invocando downstream',
                            code=5003, error_code='LAMBDA_INVOKE_ERROR')
    return response
```

Por que separar service de controller:

- El service es **testeable en aislamiento** sin construir un evento
  Lambda completo.
- La logica de negocio se puede **reusar** entre acciones o lambdas.
- El controller queda trivial: si crece, la logica esta mal ubicada.

## Que va en cada capa

| Decision | Capa |
|----------|------|
| "el campo X es obligatorio / debe ser int" | `models/` (Pydantic) |
| "el monto debe ser > 0" (formato) | `models/` (field_validator) |
| "si el cliente esta moroso, rechazar" (negocio) | `services/` |
| "invocar el Lambda de pagos" | `services/` (via `utils/invoker`) |
| "traducir el resultado del service a la respuesta" | `controllers/` |
| "elegir que controller corre" | `handler.py` + `import_controller` |

## Agregar una accion a una operacion existente

Para agregar `payments/cancel`:

1. `controllers/payments/cancel.py` con la clase `Cancel(BaseController)`.
2. `PaymentsCancelModel` en `models/payments.py`.
3. La logica `cancel_payment(...)` en `services/payments_service.py`.

No hay que tocar `handler.py` ni `OPERATIONS` (la operacion ya existe).

## Agregar una operacion nueva

Para agregar la operacion `refunds`:

1. `controllers/refunds/` con sus acciones (`create.py`, ...).
2. `services/refunds_service.py`.
3. `models/refunds.py` con los modelos por accion.
4. Entrada en `OPERATIONS` (`settings/operations.py`):
   `'refunds': {'controller': 'refunds', 'arn_key': 'arn_refunds'}`.
5. Si invoca un Lambda, el campo `arn_refunds` en `AppConfig`.

## Manejo de errores: codigos por rango

El service lanza `ServiceError` con un `code` del rango apropiado; el
controller lo propaga; el handler lo colapsa al codigo de salida.

| Situacion | code | Rango |
|-----------|------|-------|
| Payload mal formado | `ValidationError` -> 1000 | validacion |
| ARN downstream sin configurar | 2001 | configuracion |
| Regla de negocio incumplida | 4000-4999 | negocio |
| Downstream falla / timeout | 5000-5999 | API externa |
| Bug inesperado | 6000 | sistema |

---

[README](README.md) | Anterior: [02](02-handler-and-routing.md) | Siguiente: [04](04-testing.md)
