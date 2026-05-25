# 09 — Idempotencia ORM (`ON CONFLICT DO NOTHING`)

> Soporte de idempotencia en `shared/db/repository.py` para que los workers
> puedan re-procesar el mismo mensaje SQS sin generar duplicados. Cambios
> minimos al ORM: nuevas helpers `insert_contact_idempotent` y
> `insert_tracking_idempotent` que usan `pg_insert(...).on_conflict_do_nothing()`.

[< 08](08-refactor-tracking-pixel-encoder.md) | [Siguiente: 10 — Commits >](10-commits.md)

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `shared/db/repository.py` | + `insert_contact_idempotent`; + `insert_tracking_idempotent`. Los viejos `insert_contact` y `insert_tracking` se mantienen para sync-mode |
| `shared/db/tests/test_repository_idempotent.py` | NUEVO archivo |

## Cambios en `repository.py`

```python
# ... mantener todo lo actual ...

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session as OrmSession

from .models import Contact, TrackingEvent


def insert_contact_idempotent(
    session: OrmSession, payload: dict[str, Any],
) -> bool:
    """INSERT en contacts con ON CONFLICT (id) DO NOTHING.

    Returns
    -------
    bool
        True si la fila se inserto; False si ya existia (rowcount == 0).
        El caller usa este bool para decidir si manda email (worker).
    """
    stmt = pg_insert(Contact).values(**payload).on_conflict_do_nothing(
        index_elements=['id'],
    )
    result = session.execute(stmt)
    return (result.rowcount or 0) > 0


def insert_tracking_idempotent(
    session: OrmSession, payload: dict[str, Any],
) -> bool:
    """INSERT en tracking_events con ON CONFLICT (PK compuesta) DO NOTHING.

    La PK fisica es (created_at, visit_id, page_id). Para que la
    idempotencia funcione:
      - `created_at` y `page_id` los pre-genera el ENCODER (Lambda HTTP).
      - `visit_id` lo resuelve `ensure_session_and_visit` (UPSERT
        idempotente). En el segundo intento del mismo mensaje, los
        UTM keys + IP coinciden -> reusa el mismo visit_id.

    Returns
    -------
    bool
        True si inserto; False si ya existia.
    """
    stmt = pg_insert(TrackingEvent).values(**payload).on_conflict_do_nothing(
        index_elements=['created_at', 'visit_id', 'page_id'],
    )
    result = session.execute(stmt)
    return (result.rowcount or 0) > 0
```

## Tests nuevos

### `tests/test_repository_idempotent.py`

```python
"""Tests de idempotencia de insert_contact_idempotent + insert_tracking_idempotent."""

import pytest
from datetime import UTC, datetime
from uuid import uuid4

from shared.db.repository import (
    ensure_session_and_visit,
    insert_contact_idempotent,
    insert_tracking_idempotent,
)
from shared.db.session import db_session


@pytest.fixture
def clean_neon(neon_test):
    """Limpia las 3 tablas afectadas. neon_test es la fixture standard del proyecto."""
    with db_session() as session:
        session.execute(text("TRUNCATE vis_sessions, vis_session_visits, "
                             "vis_tracking_events, contacts CASCADE"))


def test_insert_contact_idempotent_returns_true_on_first_insert(clean_neon):
    """
    Given una tabla contacts vacia,
    When insert_contact_idempotent corre con un id nuevo,
    Then retorna True (rowcount == 1) y la fila esta en la DB.
    """
    payload = _contact_payload(contact_id='01900000-...')
    with db_session() as session:
        ensure_session_and_visit(session, session_id='s1', ip='1.1.1.1',
                                 country=None, user_agent=None, browser=None,
                                 browser_version=None, os_name=None,
                                 device_type=None, utm_source=None,
                                 utm_medium=None, utm_campaign=None,
                                 utm_content=None, utm_term=None,
                                 referrer=None, landing_page_path=None,
                                 niche=None, bump_event_count=False)
        result = insert_contact_idempotent(session, payload)
    assert result is True


def test_insert_contact_idempotent_returns_false_on_second_insert_same_id(clean_neon):
    """
    Given una fila ya existe con id X,
    When insert_contact_idempotent corre con el MISMO id,
    Then retorna False (rowcount == 0) y NO se inserta una segunda fila.
    """
    payload = _contact_payload(contact_id='01900000-...')
    with db_session() as session:
        ensure_session_and_visit(session, session_id='s1', ip='1.1.1.1', ...)
        first = insert_contact_idempotent(session, payload)
        second = insert_contact_idempotent(session, payload)
    assert first is True
    assert second is False
    # Verifica que hay exactamente 1 fila
    with db_session() as session:
        count = session.execute(
            text('SELECT COUNT(*) FROM contacts WHERE id = :id'),
            {'id': payload['id']},
        ).scalar()
    assert count == 1


def test_insert_tracking_idempotent_dedup_by_created_at_visit_id_page_id(clean_neon):
    """
    Given un tracking_event ya insertado con (created_at=T, visit_id=V, page_id=P),
    When insert_tracking_idempotent corre con el MISMO (T, V, P),
    Then retorna False y la tabla sigue con 1 fila.
    """
    created_at = datetime.now(UTC)
    page_id = '01900000-...'

    with db_session() as session:
        session_id, visit_id = ensure_session_and_visit(
            session, session_id='s1', ip='1.1.1.1', ...
        )
        payload = {
            'session_id': session_id,
            'visit_id': visit_id,
            'page_id': page_id,
            'created_at': created_at,
            'event_id': str(uuid4()),
            'event_type_id': '...',
            'page_path': '/',
            'viewport_width': 1920,
            'viewport_height': 1080,
        }
        first = insert_tracking_idempotent(session, payload)
        second = insert_tracking_idempotent(session, payload)

    assert first is True
    assert second is False


def test_insert_tracking_idempotent_inserts_new_when_page_id_differs(clean_neon):
    """
    Given un tracking_event ya insertado con page_id=P1,
    When insert_tracking_idempotent corre con page_id=P2 (mismo created_at, visit_id),
    Then retorna True (es un evento diferente).
    """
    ...


def _contact_payload(contact_id: str) -> dict:
    return {
        'id': contact_id,
        'created_at': datetime.now(UTC),
        'name': 'Test',
        'email': 'test@example.com',
        'message': 'Lorem ipsum dolor sit amet.',
        'session_id': 's1',
    }
```

## Reglas duras

- **SIEMPRE** los helpers viejos (`insert_contact`, `insert_tracking`) se
  mantienen para no romper el sync mode mientras dure el feature flag.
- **SIEMPRE** la PK de `contacts` es `id` (UUIDv7 UNICO).
- **SIEMPRE** la PK de `tracking_events` es compuesta
  `(created_at, visit_id, page_id)`.
- **SIEMPRE** el caller de los helpers idempotentes interpreta el `bool`
  de retorno: `True` = insertado nuevo (manda email, etc); `False` = ya
  existia (no-op).
- **NUNCA** confundir los UPSERT de `sessions` y `session_visits` con la
  idempotencia del INSERT. `ensure_session_and_visit` ya es idempotente
  por diseno; los helpers nuevos cubren los INSERTS finales.
- **NUNCA** poner `on_conflict_do_update` (eso sobreescribiria datos). Es
  DO NOTHING — los duplicados se ignoran.

## AC cubiertos

- AC-10 (contact idempotencia)
- AC-14 (tracking idempotencia)

## Verificacion incremental

```bash
cd serverless/lambda/shared/db
.venv/bin/pytest tests/test_repository_idempotent.py -v
```

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| `on_conflict_do_update` | Sobreescribe datos, idempotencia rota | DO NOTHING |
| Idempotencia via `SELECT antes de INSERT` | TOCTOU race (2 workers en paralelo crean duplicados) | ON CONFLICT atomico |
| Mantener solo los helpers idempotentes (borrar los viejos) | Rompe el sync mode = bloquea rollback | Coexisten hasta que el flag se elimine |
| Logear el row entero (puede tener email) | PII en logs | Solo loguear `id`, `persisted: bool` |
| Cambiar el shape de la PK de tracking_events para "facilitar" | Migracion costosa de prod | La PK actual (created_at, visit_id, page_id) basta |

---

[< 08](08-refactor-tracking-pixel-encoder.md) | [Siguiente: 10 — Commits >](10-commits.md)
