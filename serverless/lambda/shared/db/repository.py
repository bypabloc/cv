"""@module shared.db.repository — acceso a datos del schema PostgreSQL.

Concentra las operaciones de lectura/escritura ORM del portfolio:

- `list_tables`               — listado de tablas con estimado de filas.
- `insert_contact`            — escritura del form de contacto (Neon).
- `insert_tracking`           — escritura de evento de tracking (Neon).
- `ensure_session_and_visit`  — UPSERT atomico de session + visit
                                (helper del plan sessions-normalize).

Las Lambdas HTTP (`contact_form`, `tracking_pixel`) escriben directo a
Neon en la misma invocacion (spec `direct-neon-writes`). El `core/` de
un Lambda NO importa `sqlalchemy` directo, solo consume estas funciones
(`from shared.db.repository import ...`).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session as OrmSession

from .models import Contact, SessionVisit, TrackingEvent
from .models import Session as SessionRow
from .session import get_engine


class RepositoryError(Exception):
    """Error de acceso a datos del schema PostgreSQL.

    El caller (un service del Lambda) lo captura y lo traduce a la
    respuesta normalizada del estandar lambda-controller.
    """

    def __init__(
        self,
        message: str,
        *,
        code: int = 5000,
        error_code: str = 'DB_QUERY_FAILED',
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.error_code = error_code


# La query de listado de tablas: estimado de filas via las estadisticas
# del planner (`pg_stat_user_tables`), sin contar fila por fila.
_TABLES_QUERY = (
    "SELECT schemaname || '.' || relname AS table_name, "
    'n_live_tup AS estimated_rows '
    'FROM pg_stat_user_tables '
    'ORDER BY n_live_tup DESC'
)


def list_tables() -> dict[str, Any]:
    """Lista las tablas de la DB con un estimado de filas por tabla.

    Consulta `pg_stat_user_tables` (estadisticas del planner):
    `n_live_tup` es un estimado, NO un `COUNT(*)` exacto — barato y
    suficiente para una vista operativa.

    Returns
    -------
    dict[str, Any]
        `{'tables': [{'name': str, 'rows': int}, ...]}`, ordenado por
        `rows` descendente. Lista vacia si la DB no tiene tablas de
        usuario.

    Raises
    ------
    RepositoryError
        Si la query falla (DB inaccesible, schema sin migrar, etc.) con
        `code=5000` y `error_code='DB_QUERY_FAILED'`.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(text(_TABLES_QUERY)).all()
    except Exception as exc:
        raise RepositoryError(
            f'No se pudo listar las tablas: {exc}',
        ) from exc

    tables = [
        {'name': row.table_name, 'rows': int(row.estimated_rows)}
        for row in rows
    ]
    return {'tables': tables}


def insert_contact(session: OrmSession, payload: dict[str, Any]) -> None:
    """Inserta una fila en `contacts` desde el payload del transformer.

    `session_id` enlaza el contacto con `sessions` (FK NOT NULL). Spec
    sessions-normalize: ip/country/user_agent ya no se persisten aqui
    (viven en sessions/session_visits via FK).
    """
    session.add(Contact(**payload))


def insert_tracking(session: OrmSession, payload: dict[str, Any]) -> None:
    """Inserta una fila en `tracking_events` desde el payload.

    `event_props` es un dict plano: SQLAlchemy lo adapta a JSONB sin
    envoltura manual. Spec sessions-normalize: el payload debe incluir
    `session_id` Y `visit_id` (ambas FKs NOT NULL).
    """
    session.add(TrackingEvent(**payload))


# Las 6 claves del visit-trigger (decision 9 del plan). Cambio en
# cualquiera respecto al ultimo visit del session -> nuevo visit.
_VISIT_KEYS: tuple[str, ...] = (
    'ip',
    'utm_source',
    'utm_medium',
    'utm_campaign',
    'utm_content',
    'utm_term',
)


def ensure_session_and_visit(
    session: OrmSession,
    *,
    session_id: str,
    ip: str | None,
    country: str | None,
    user_agent: str | None,
    browser: str | None,
    browser_version: str | None,
    os_name: str | None,
    device_type: str | None,
    utm_source: str | None,
    utm_medium: str | None,
    utm_campaign: str | None,
    utm_content: str | None,
    utm_term: str | None,
    referrer: str | None,
    landing_page_path: str | None,
    niche: str | None,
    bump_event_count: bool = True,
) -> tuple[str, str]:
    """UPSERT atomico de `sessions` + `session_visits`.

    Helper que ambos Lambdas (`tracking_pixel`, `contact_form`) invocan
    dentro de la misma transaccion del INSERT del event/contact.

    Algoritmo (decisiones 1, 8, 9, 12 del plan sessions-normalize):

    1. UPSERT en `sessions`: INSERT con `ON CONFLICT (session_id) DO
       UPDATE SET last_seen_at = now()`. Los demas campos
       (ua/browser/os/device_type) NO se sobrescriben — snapshot
       inmutable del primer evento.
    2. SELECT del ultimo visit del session por `started_at DESC LIMIT 1
       FOR UPDATE` (evita race conditions entre eventos concurrentes
       del mismo session_id).
    3. Compara las 6 claves `_VISIT_KEYS` (`ip` + 5 `utm_*`) entre el
       payload y el ultimo visit. Si NO existe ultimo visit O alguna
       de las 6 claves difiere -> INSERT nuevo `session_visits` con
       `event_count = 1` (si `bump_event_count`) o `0`. Si todas
       coinciden -> UPDATE `ended_at = now()` y opcionalmente
       `event_count = event_count + 1`. Reusa el `visit_id`.

    Parameters
    ----------
    session : OrmSession
        Sesion SQLAlchemy con la transaccion del Lambda. NO se commitea
        aqui — el caller controla el ciclo.
    session_id : str
        Identidad del visitante (texto, viene del cliente).
    ip, country, user_agent, browser, browser_version, os_name,
    device_type :
        Datos de la session/visit. `os_name` se renombra para no chocar
        con el modulo builtin `os`. Todos pueden ser None.
    utm_source, utm_medium, utm_campaign, utm_content, utm_term :
        Los 5 campos UTM del visit. None si no estan presentes.
    referrer, landing_page_path, niche :
        Metadata del landing de la visit (solo se persiste al crear un
        visit nuevo; UPDATE no las toca).
    bump_event_count : bool, default True
        Si True, el `event_count` del visit (nuevo o reusado) se
        incrementa en 1. El caller debe llamar el helper UNA vez por
        evento/contact a persistir.

    Returns
    -------
    tuple[str, str]
        `(session_id, visit_id)`. El caller usa `visit_id` para el
        INSERT del `tracking_events`/`contacts`.
    """
    # --- Paso 1: UPSERT en sessions --------------------------------
    # `ON CONFLICT DO UPDATE SET last_seen_at=now()` mantiene snapshot
    # inmutable del resto de campos (decision 1).
    sessions_insert = pg_insert(SessionRow).values(
        session_id=session_id,
        user_agent=user_agent,
        browser=browser,
        browser_version=browser_version,
        os=os_name,
        device_type=device_type,
    )
    sessions_upsert = sessions_insert.on_conflict_do_update(
        index_elements=['session_id'],
        set_={'last_seen_at': text('now()')},
    )
    session.execute(sessions_upsert)

    # --- Paso 2: SELECT ultimo visit del session, FOR UPDATE --------
    # host(ip) en vez de ip::text: INET cast a text agrega sufijo de
    # mascara (/32 para IPv4, /128 para IPv6) y la comparacion contra
    # el payload (str plano sin mascara) fallaba SIEMPRE. host() devuelve
    # solo la direccion sin mascara, alineado con el formato del payload.
    last_visit_query = (
        text(
            'SELECT visit_id, host(ip) AS ip, utm_source, utm_medium, '
            'utm_campaign, utm_content, utm_term '
            'FROM session_visits '
            'WHERE session_id = :sid '
            'ORDER BY started_at DESC '
            'LIMIT 1 '
            'FOR UPDATE'
        )
    )
    last_visit = session.execute(
        last_visit_query, {'sid': session_id}
    ).first()

    incoming: dict[str, str | None] = {
        'ip': ip,
        'utm_source': utm_source,
        'utm_medium': utm_medium,
        'utm_campaign': utm_campaign,
        'utm_content': utm_content,
        'utm_term': utm_term,
    }

    bump_delta = 1 if bump_event_count else 0

    if last_visit is None or _visit_keys_differ(last_visit, incoming):
        # --- Paso 3a: INSERT nuevo visit ----------------------------
        new_visit = SessionVisit(
            session_id=session_id,
            ip=ip,
            country=country,
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
            utm_content=utm_content,
            utm_term=utm_term,
            referrer=referrer,
            landing_page_path=landing_page_path,
            niche=niche,
            event_count=bump_delta,
        )
        session.add(new_visit)
        # Flush para obtener el visit_id generado server-side
        # (uuidv7()). NO commitea: solo emite el INSERT al server.
        session.flush()
        return session_id, str(new_visit.visit_id)

    # --- Paso 3b: UPDATE visit existente (ended_at + event_count) --
    visit_id = str(last_visit.visit_id)
    session.execute(
        text(
            'UPDATE session_visits '
            'SET ended_at = now(), '
            '    event_count = event_count + :delta '
            'WHERE visit_id = :vid'
        ),
        {'delta': bump_delta, 'vid': visit_id},
    )
    return session_id, visit_id


def _visit_keys_differ(
    last_visit: Any, incoming: dict[str, str | None]
) -> bool:
    """True si alguna de las 6 claves de _VISIT_KEYS cambio.

    Compara el row del ultimo `session_visits` (devuelto por SELECT)
    con el payload del nuevo evento. La comparacion es case-sensitive y
    None == None (visitante sin utm sigue en el mismo visit).
    """
    for key in _VISIT_KEYS:
        if getattr(last_visit, key) != incoming[key]:
            return True
    return False
