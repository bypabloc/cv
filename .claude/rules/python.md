---
description: "Estandares de desarrollo Python 3.14: estilo, estructura de archivos, services/selectors, testing y complejidad"
globs: "**/*.py"
---

# Python Development Standards

## Estilo

- Python 3.14 estricto (target-version `py314` en Ruff). Excepciones de bootstrap (`devtools/run.py`, `.git-hooks/*.py`) pinneadas a `py313` via `per-file-target-version` para preservar sintaxis con parentesis en `except`.
- Ruff como linter y formatter. Cada modulo lleva su propio `ruff.toml` autocontenido: `server/ruff.toml` (Django + Python 3.14) y `devtools/ruff.toml` (CLI + bootstrap py313). Sin base compartida: cada archivo declara reglas, ignores y formatter completos. Ruff los autodetecta cuando el cwd es la raiz del modulo.
- line-length 80, indent 4, line-ending lf, single quotes (`flake8-quotes` + formatter), trailing commas habilitadas (no auto-agregadas — ver nota abajo).
- Type hints requeridos en todas las funciones publicas (`ANN`).
- NO usar `from __future__ import annotations` (PEP 649: Python 3.14 tiene lazy annotations nativo).
- Usar union syntax moderna: `str | None` en vez de `Optional[str]`.
- Type parameter syntax (PEP 695): `def first[T](items: list[T]) -> T:`.

### Conflictos formatter vs linter (ignorados intencionalmente)

Estas reglas estan en `ignore` del base porque chocan con el comportamiento del formatter:

- `E501` (line too long): el formatter ya gestiona el corte de lineas
- `E203` (whitespace before `:`): el formatter ya respeta PEP 8
- `COM812` (missing trailing comma): conflicto con formatter — ver nota abajo
- `COM819` (prohibited trailing comma): companion de COM812
- `ISC001` (implicit string concat single-line): el formatter prefiere doble
- `Q001` (multiline-quotes): el formatter prefiere comillas dobles en multilinea

### Comillas: convencion semantica

- **Single quotes (`'...'`)** para strings tecnicos: keys de dicts, valores de codigo, identificadores, paths, choices.
- **Double quotes (`"..."`)** aceptables solo para texto legible por humanos: mensajes de error de usuario, mensajes de log, contenido para UI.
- **Triple double quotes (`"""..."""`)** para docstrings y strings multilinea.

```python
# Correcto: distincion semantica clara
record['status'] = 'pending'
config = {'host': 'localhost', 'port': 9979}
logger.error("No se pudo conectar al provider, reintentando")
raise ValueError("El monto debe ser positivo")

# Incorrecto: comilla doble en string tecnico
record["status"] = "pending"
```

Ver `"..."` en el codigo deberia indicar "este string lo veria un humano".

### Trailing commas (motivacion: minimizar git diff)

La regla NO es estetica. Al agregar un item nuevo, solo aparece **una** linea
modificada en el diff (la nueva), no dos (la nueva mas la coma agregada en la
anterior).

`COM812` esta en `ignore` (conflicto con formatter), pero el formatter respeta
trailing commas existentes y `skip-magic-trailing-comma = false` permite que
una trailing comma fuerce el wrap a multilinea. Resultado: las trailing commas
se preservan al formatear, y el dev las agrega manualmente al escribir.

```python
# Correcto: agregar 'd' modifica solo 1 linea en el diff
my_dict = {
    'a': 1,
    'b': 2,
    'c': 3,
}

# Incorrecto: agregar 'd' modifica 2 lineas
my_dict = {
    'a': 1,
    'b': 2,
    'c': 3
}
```

### Tipado como auto-documentacion

Los desarrolladores leen mas codigo del que escriben. La firma tipada de una
funcion es la primera fuente de informacion para entender que hace, sin tener
que leer el body o el docstring.

```python
# Mal: hay que leer el cuerpo para saber que retorna
def fib(n):
    a, b = 0, 1
    while a < n:
        yield a
        a, b = b, a + b

# Bien: la firma sola dice "iterador de int sobre n int"
def fib(n: int) -> Iterator[int]:
    a, b = 0, 1
    while a < n:
        yield a
        a, b = b, a + b
```

Ruff `ANN` rules hacen enforce de annotations en funciones publicas.

## Estructura de archivos (OBLIGATORIO)

- Un archivo por clase/funcion principal, agrupados en carpetas por tipo
- Archivos NO deben superar 300-500 lineas como maximo
- Usar `__init__.py` para re-exportar los nombres publicos del modulo
- `__init__.py` solo contiene imports y re-exports, NUNCA logica

### Patron correcto (un archivo por entidad)

```
server/apps/<app_name>/
├── models/
│   ├── __init__.py          # from .appointment import Appointment; from .appointment_event import AppointmentEvent
│   ├── appointment.py       # class Appointment + AppointmentQuerySet + AppointmentManager
│   └── appointment_event.py # class AppointmentEvent
├── services/
│   ├── __init__.py          # re-exports
│   ├── creation.py          # def create_appointment(*, business, consumer, service, staff, ...)
│   └── update.py            # def cancel_appointment(*, appointment, actor, reason, ...)
├── selectors/
│   ├── __init__.py          # re-exports
│   ├── appointment_queries.py  # def get_business_appointments(*, business, ...) -> QuerySet
│   └── slot_queries.py         # def get_available_slots(*, business, service, staff, date, ...)
├── admin/
│   ├── __init__.py          # re-exports
│   ├── appointment.py       # @admin.register(Appointment) class AppointmentAdmin
│   └── appointment_event.py # @admin.register(AppointmentEvent) class AppointmentEventAdmin
├── serializers/
│   ├── __init__.py
│   ├── input.py             # Serializers de validacion (Serializer puro, no ModelSerializer)
│   └── output.py            # Serializers de respuesta (ModelSerializer read-only)
├── enums/
│   ├── __init__.py
│   ├── status.py            # class AppointmentStatus(models.TextChoices)
│   └── payment_status.py    # class PaymentStatus(models.TextChoices)
├── tasks/
│   ├── __init__.py
│   └── reminders.py         # @shared_task def send_appointment_reminder(appointment_id)
├── exceptions.py            # Custom exceptions de la app
├── constants.py             # Constantes de la app (UPPER_SNAKE_CASE)
├── urls.py
└── apps.py
```

### Patron incorrecto (archivos monoliticos)

```
server/apps/<app_name>/
├── models.py       # Todos los modelos en un solo archivo
├── admin.py        # Todos los admins en un solo archivo
├── services.py     # Toda la logica en un solo archivo
├── enums.py        # Todos los enums en un solo archivo
└── apps.py
```

### Reglas de division

- Si un archivo supera 300 lineas, dividirlo inmediatamente
- Cada modelo Django en su propio archivo dentro de `models/`
- Cada admin class en su propio archivo dentro de `admin/`
- Cada enum en su propio archivo dentro de `enums/`
- Services, selectors, serializers, views, tasks: un archivo por dominio logico

## Services y Selectors (patron obligatorio)

### Services (operaciones de escritura)

- Funciones, NO clases (a menos que se necesite estado complejo)
- SIEMPRE usar `*` para forzar keyword-only arguments
- Un service function = una operacion de negocio
- Usar `@transaction.atomic` para operaciones multi-modelo
- Retornar la instancia creada/actualizada
- Lanzar excepciones custom para violaciones de reglas de negocio

```python
from django.db import transaction

def create_appointment(
    *,
    business: Business,
    consumer: User,
    service: Service,
    staff: StaffMember,
    start: datetime,
) -> Appointment:
    appointment = Appointment(
        business=business,
        consumer=consumer,
        service=service,
        staff=staff,
        start=start,
        end=start + timedelta(minutes=service.duration_minutes),
    )
    appointment.full_clean()
    appointment.save()
    return appointment
```

### Selectors (operaciones de lectura)

- Retornar `QuerySet` (permite encadenamiento) o tipos primitivos
- NUNCA realizar escrituras
- Aplicar `select_related`/`prefetch_related` aqui, no en views

```python
from django.db.models import QuerySet

def get_business_appointments(
    *,
    business: Business,
    active_only: bool = True,
) -> QuerySet[Appointment]:
    qs = Appointment.objects.filter(business=business)
    if active_only:
        qs = qs.exclude(status=AppointmentStatus.CANCELLED)
    return qs.select_related('consumer', 'service', 'staff')
```

## Excepciones custom (patron obligatorio)

```python
# common/exceptions.py
class ApplicationError(Exception):
    def __init__(self, message: str = '', extra: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.extra = extra or {}

# apps/<app>/exceptions.py
from common.exceptions import ApplicationError

class BookingConflictError(ApplicationError): ...
class SlotTakenError(ApplicationError): ...
class BusinessNotActiveError(ApplicationError): ...
class AppointmentNotCancellableError(ApplicationError): ...
```

- NUNCA usar `except:` o `except Exception:` sin re-raise
- Usar `raise ... from e` para preservar cadena de excepciones
- Manejar en la capa view/API, no dentro de services

## Logging

- NUNCA f-strings en llamadas a logging (rompe lazy evaluation)
- Usar logging estructurado con contexto

```python
# Correcto
logger.info('Record created', extra={'record_id': str(record.id)})
logger.warning('Attempt %d failed: %s', attempt, error)

# Incorrecto
logger.info(f'Record created: {record.id}')
```

## Estructura de scripts

- Incluir `if __name__ == "__main__":` en scripts ejecutables
- Usar `logging` module, nunca `print()` para info de ejecucion

## APIs externas

- Retry con backoff exponencial para llamadas a APIs
- Timeout explicito en todas las requests (default: 30s)
- Validar respuestas antes de procesar
- Nunca hardcodear API keys — usar `.env` con `python-dotenv`

## Testing

- Framework: pytest (+ `pytest-bdd` para feature tests del server)
- Coverage minimo: 80% per-file (enforced en pre-push)
- Patron AAA en el cuerpo + **BDD-style en el docstring** (Given/When/Then)
- Un concepto de assertion por test (multiples `assert` ok si validan lo mismo)
- factory-boy sobre fixtures para datos de test
- Nomenclatura metodos: `test_<unit>_<scenario>_<expected>`
- Nomenclatura archivos: SIN prefijo `test_` (path mirroring, descubiertos via hook)
- `pytestmark = pytest.mark.unit` o `pytest.mark.integration` obligatorio por archivo
- `@pytest.mark.parametrize` para multiples escenarios de input
- Server: `cd server && python tests/run.py --type unit|integration`
- Coverage: `python devtools/run.py test_runner --module=server --type=coverage`
- Mutation testing (calidad de tests): `python devtools/run.py mutation_testing --paths=apps/<app>` (ver `ai-testing-independence.md`)

### BDD-style obligatorio en el docstring

Mantener AAA como estructura del cuerpo. El docstring describe el
comportamiento en formato Given/When/Then — facilita lectura sin contexto
IA y traza el test al AC humano.

```python
def test_create_appointment_when_slot_taken_raises_booking_conflict():
    """
    Given un negocio con un profesional que ya tiene cita a las 10:00,
    When un consumer intenta reservar el mismo slot,
    Then lanza BookingConflictError con codigo SLOT_TAKEN.
    """
    # Arrange
    business = BusinessFactory.create()
    staff = StaffMemberFactory.create(business=business)
    service = ServiceFactory.create(business=business, duration_minutes=60)
    start = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
    AppointmentFactory.create(business=business, staff=staff, start=start)

    # Act / Assert
    with pytest.raises(BookingConflictError) as exc:
        create_appointment(
            business=business,
            consumer=UserFactory.create(),
            service=service,
            staff=staff,
            start=start,
        )
    assert exc.value.extra['code'] == 'SLOT_TAKEN'
```

### Asserts EXACTOS, no rangos (enforced en pre-commit)

El hook `weak_assertion` (`.git-hooks/weak_assertion_detector.py`) rechaza
asserts vagos en archivos de test staged. Reglas:

```python
# Rechazado:
assert x > 0
assert result is not None
assert isinstance(result, dict)
assert len(items) >= 1

# Aceptado:
assert x == 42
assert result == {'status': 'ok'}
assert items == [item1, item2]
```

Si necesitas range/type assertions justificadas, usar `# noqa: WEAK-ASSERT`
inline (con razon en comentario).

### Que mockear vs que no

- MOCKEAR: APIs HTTP externas, email, file storage (S3), time/datetime
- NO MOCKEAR: Base de datos, Django ORM, services/selectors propios, request/response Django

### Property-based testing (Hypothesis)

Para algoritmos puros + validaciones criticas (RUT chileno, RUC peruano,
calculos de slots de disponibilidad), preferir `hypothesis` sobre tests
parametrizados manuales. Es agnostico al modelo IA y deriva tests de los
type hints.

```python
from hypothesis import given, strategies as st


@given(duration=st.integers(min_value=15, max_value=240))
def test_slot_end_is_consistent_with_duration(duration: int) -> None:
    """
    Property: el slot end = start + duration_minutes, para cualquier duracion valida.
    Given una cita con duracion arbitraria,
    When calcular el end,
    Then end - start == duration en minutos.
    """
    start = datetime(2026, 6, 1, 9, 0, tzinfo=UTC)
    slot = calculate_slot_end(start=start, duration_minutes=duration)
    assert (slot - start).seconds // 60 == duration
```

### AI-testing independence

Cualquier test (humano o AI-asistido) debe ser mantenible si la IA
desaparece manana. Politica completa, workflow Three Amigos + AI, mutation
testing thresholds (70% standard / 85% critical) y compliance EU AI Act:
ver `ai-testing-independence.md`.

## Complejidad

- Max complejidad ciclomatica por funcion: 10 (enforced via Ruff C90)
- Max argumentos posicionales: 5 (usar dataclasses/TypedDict para mas)
- Max lineas por funcion: ~50 (soft limit)
- No anidar try/except — extraer a funciones separadas

## Dependencias

- Server: `server/pyproject.toml` (PEP 621 `[project.dependencies]` para prod, PEP 735 `[dependency-groups.dev]` para test/lint) + `server/uv.lock`
- Devtools: `devtools/pyproject.toml` (ruff, GitPython, httpx, pytest) + `devtools/uv.lock`
- Pinear versiones exactas en produccion (`==X.Y.Z`); `>=` aceptable para tooling de devtools
- Gestionar via uv: `uv add <pkg>` para agregar, `uv lock --upgrade-package <pkg>` para actualizar uno solo, `uv sync --frozen` para reproducir; `python devtools/run.py upgrade_deps --dry-run` para ver el cuadro completo de upgrades disponibles
- En containers: `uv sync --frozen --no-install-project --no-dev` para prod; sin `--no-dev` para dev/local/test
