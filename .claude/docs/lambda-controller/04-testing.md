# 04 - Testing

> Anterior: [03 - Controllers y models](03-controllers-and-models.md) | Siguiente: [05 - Crear y refactorizar](05-create-and-refactor.md)

Estandar de testing tomado del lambda real `santander_offer_handler`
(legolambda). Dos niveles separados: **unit** (aislado) e
**integration** (E2E con recursos reales).

## Estructura

```text
tests/
├── conftest.py              # mocks unit + env vars + sys.path (core/)
├── unit/
│   ├── _helpers.py          # builders compartidos (prefijo _)
│   └── test_<unidad>_<escenario>.py
└── integration/
    ├── conftest.py          # SIN mocks; fixtures + cleanup autouse
    ├── _fixtures/           # builders de integracion (prefijo _)
    │   └── <recurso>.py
    └── test_<escenario>_e2e.py
```

`pytest.ini` en la raiz del lambda fija el `rootdir`, lo que permite
que los tests importen `from tests.unit._helpers import ...` y
`from tests.integration._fixtures.<x> import ...`.

## Regla 1: un archivo por escenario

Cada caso de prueba es **su propio archivo** `test_*.py` con UNA
funcion `test_*` dentro. El nombre del archivo es el escenario:

```text
test_handler_routes_check_to_controller.py
test_handler_rejects_unknown_operation.py
test_create_model_rejects_negative_amount.py
test_create_service_raises_on_downstream_failure.py
```

Patron del nombre: `test_<unidad>_<escenario>`. Esto hace que el
`pytest -q` lea como una lista de comportamientos y que un fallo apunte
directo al archivo del caso.

## Regla 2: el docstring del modulo describe el escenario

El docstring del archivo describe el comportamiento bajo prueba
(estilo Given/When/Then). La funcion `test_*` lleva un docstring corto
o ninguno; el cuerpo sigue Arrange-Act-Assert.

```python
"""
handler.lambda_handler: un evento valido de example/check se enruta al
controller Check y devuelve is_valid True con el resultado del service.

:Authors:
    - <Autor>

:Created:
    - YYYY-MM-DD
"""

from handler import lambda_handler
from tests.unit._helpers import build_event


def test_handler_routes_check_to_controller():
    """
    Given un evento valido example/check,
    When se invoca lambda_handler,
    Then devuelve is_valid True con el status del recurso.
    """
    event = build_event(operation='example', action='check',
                         data={'resource_id': 'R-1'})

    result = lambda_handler(event, {})

    assert result == {
        'is_valid': True,
        'data': {'resource_id': 'R-1', 'status': 'ok'},
    }
```

## Regla 3: builders compartidos con prefijo `_`

Los builders compartidos NO son archivos de test. Llevan prefijo `_`
para que pytest no los recolecte:

- `tests/unit/_helpers.py` - builders de eventos/datos para unit.
- `tests/integration/_fixtures/<recurso>.py` - builders y helpers de
  recursos reales (payloads, datos en BD, objetos S3, ...).

```python
# tests/unit/_helpers.py
def build_event(*, operation='example', action='create', data=None):
    """Construye un evento Lambda valido operation+action."""
    if data is None:
        data = {'resource_id': 'R-1', 'amount': 100}
    return {'operation': operation, 'action': action, 'data': data}
```

## conftest.py raiz: aislar los tests unitarios

`tests/conftest.py` se ejecuta antes de cualquier import del lambda y:

1. Mockea las librerias propietarias del runtime que no estan en pip
   (ej. `bifrost`), SOLO cuando la corrida es de unit.
2. Setea las env vars minimas que `AppConfig` necesita.
3. Agrega `core/` al `sys.path`.

```python
def _is_integration_run() -> bool:
    return any('integration' in arg for arg in sys.argv[1:])

if not _is_integration_run():
    for mod_name in ['bifrost', 'bifrost.logger']:
        sys.modules.setdefault(mod_name, MagicMock())

os.environ.setdefault('ENVIRONMENT', 'dev')
os.environ.setdefault('ARN_EXAMPLE', 'arn:aws:lambda:...:dummy')

CORE_ROOT = Path(__file__).resolve().parent.parent / 'core'
sys.path.insert(0, str(CORE_ROOT))
```

## conftest.py de integration: recursos reales + cleanup

`tests/integration/conftest.py` es distinto: NO mockea nada, usa los
recursos reales, y provee fixtures con cleanup `autouse` para garantizar
estado limpio aunque un test previo haya fallado.

```python
@pytest.fixture(autouse=True)
def cleanup_resources():
    """Cleanup antes y despues de cada test de integracion."""
    # ... cleanup pre-test (estado limpio garantizado) ...
    yield
    # ... cleanup post-test ...
```

Los tests de integracion requieren credenciales AWS y acceso de red;
NO corren en el CI por defecto (lentos y con dependencias externas).

## Que mockear vs que no

| | Unit | Integration |
|--|------|-------------|
| Librerias propietarias del runtime | mockear | reales |
| Lambdas downstream (`invoker_dispatch`) | mockear (`patch`) | reales |
| APIs HTTP externas | mockear | reales (o sandbox) |
| `models/`, `controllers/`, `services/` propios | NO mockear | NO mockear |

En unit, `unittest.mock.patch` reemplaza el punto de E/S:

```python
from services import example_service

def test_create_service_raises_on_downstream_failure():
    with patch.object(example_service, 'invoker_dispatch',
                       return_value=None):
        with pytest.raises(ServiceError) as exc:
            create_resource(resource_id='R-1', amount=100, arn='arn:x')
    assert exc.value.code == 5003
```

## Que testear por capa

| Capa | Que verificar en unit |
|------|----------------------|
| `models/` | un payload invalido lanza `ValidationError`; uno valido pasa |
| `services/` | logica de negocio; `ServiceError` ante fallo de E/S |
| `controllers/` | traduce service/`ServiceError` a `{is_valid, code}` |
| `handler.py` | enruta `operation+action`; rechaza eventos malformados |

Integration verifica el flujo completo: invocar `lambda_handler` con un
evento real y comprobar el efecto end-to-end.

## Asserts EXACTOS

Verificar el valor exacto, nunca rangos:

```python
assert result['code'] == 1001          # SI
assert result['code'] > 1000           # NO
assert result == {'is_valid': True, 'data': {...}}   # SI: dict completo
```

## Comandos

```bash
pip install -r requirements-dev.txt

pytest tests/unit                                   # rapido, sin red
pytest tests/integration                            # requiere AWS / red
pytest tests/unit --cov=core --cov-report=term-missing
pytest tests/unit/test_handler_rejects_missing_data.py   # un solo caso
```

---

[README](README.md) | Anterior: [03](03-controllers-and-models.md) | Siguiente: [05](05-create-and-refactor.md)
