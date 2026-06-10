"""@module cv_write — helpers genericos de escritura del dominio CV.

Capa UNICA de escritura a las tablas `cv_*` + `i18n_translations` +
`tax_niche_priorities` + catalogos (`tax_niches`, `cv_skills`,
`tax_tech_tags`). La consumen el seed/restore de la Lambda `db` y la
operation `content` del Lambda `cv_admin` — cero duplicacion.

Idempotencia: `INSERT ... ON CONFLICT ... DO UPDATE` sobre la clave
natural (slug / clave compuesta). Las uniones y los hijos ordenados usan
semantica de REEMPLAZO (delete + insert) para que una lista que se
achico deje la DB consistente, limpiando tambien las traducciones
polimorficas de los hijos eliminados (no tienen FK CASCADE).
"""

from __future__ import annotations

from datetime import date
from typing import Any

from shared.db.models.i18n.translation import Translation
from shared.db.models.taxonomy.catalog import Niche
from shared.db.models.taxonomy.priority import NichePriority
from shared.db.sa import Session, delete
from shared.db.sa import pg_insert as insert
from shared.db.seed_helpers import _parse_ym, _to_slug

# Los 5 niches del portfolio, en orden canonico de presentacion.
NICHES = ['fintech', 'architect', 'leader', 'vibe', 'generic']


def coerce_date(raw: Any) -> date | None:
    """Normaliza fechas de YAML (date nativo) o API (str) a `date`.

    pyyaml resuelve `2024-01-15` como `datetime.date`; la API manda
    strings `YYYY-MM[-DD]` o `YYYY`. Ambas formas convergen aca.
    """
    if raw is None or isinstance(raw, date):
        return raw
    return _parse_ym(str(raw))


def upsert_returning_id(
    session: Session,
    model: type,
    natural_key: str,
    values: dict[str, Any],
) -> str:
    """Inserta una fila y devuelve su `id`. Idempotente sobre `natural_key`.

    `INSERT ... ON CONFLICT (<natural_key>) DO UPDATE SET <field> =
    EXCLUDED.<field>` para TODOS los campos provistos (excepto el propio
    natural_key). Asi un re-upsert propaga los valores nuevos.
    """
    excluded = insert(model).excluded
    update_set = {
        col: getattr(excluded, col) for col in values if col != natural_key
    }
    if not update_set:
        update_set = {natural_key: getattr(excluded, natural_key)}
    stmt = (
        insert(model)
        .values(**values)
        .on_conflict_do_update(
            index_elements=[natural_key],
            set_=update_set,
        )
        .returning(model.id)
    )
    return session.execute(stmt).scalar_one()


def set_translation(
    session: Session,
    entity_type: str,
    entity_id: str,
    field: str,
    bilang: dict[str, str] | None,
) -> None:
    """Inserta (o actualiza) las filas es/en de un campo bilingue."""
    if not bilang:
        return
    for locale in ('es', 'en'):
        value = bilang.get(locale)
        if value is None:
            continue
        stmt = (
            insert(Translation)
            .values(
                entity_type=entity_type,
                entity_id=entity_id,
                field=field,
                locale=locale,
                value=value,
            )
            .on_conflict_do_update(
                index_elements=[
                    'entity_type',
                    'entity_id',
                    'field',
                    'locale',
                ],
                set_={'value': value},
            )
        )
        session.execute(stmt)


def delete_translations(
    session: Session,
    entity_type: str,
    entity_ids: list[str],
) -> None:
    """Borra TODAS las traducciones de las entidades dadas.

    `i18n_translations` es polimorfica (sin FK a la entidad): al eliminar
    una entidad o reemplazar sus hijos hay que limpiar las filas i18n
    explicitamente o quedan huerfanas.
    """
    if not entity_ids:
        return
    session.execute(
        delete(Translation).where(
            Translation.entity_type == entity_type,
            Translation.entity_id.in_(entity_ids),
        )
    )


def set_niche_priorities(
    session: Session,
    entity_type: str,
    entity_id: str,
    priority: dict[str, int] | None,
    niche_ids: dict[str, str],
) -> None:
    """Reescribe las filas de priority por niche de una entidad."""
    session.execute(
        delete(NichePriority).where(
            NichePriority.entity_type == entity_type,
            NichePriority.entity_id == entity_id,
        )
    )
    if not priority:
        return
    for niche_slug, value in priority.items():
        niche_id = niche_ids.get(niche_slug)
        if niche_id is None:
            continue
        session.execute(
            insert(NichePriority).values(
                entity_type=entity_type,
                entity_id=entity_id,
                niche_id=niche_id,
                priority=value,
            )
        )


def link_niches(
    session: Session,
    union_model: type,
    entity_col: str,
    entity_id: str,
    niche_slugs: list[str] | None,
    niche_ids: dict[str, str],
) -> None:
    """Reescribe las filas de la union `<entidad>_niches`."""
    entity_col_attr = getattr(union_model, entity_col)
    session.execute(delete(union_model).where(entity_col_attr == entity_id))
    for niche_slug in niche_slugs or []:
        niche_id = niche_ids.get(niche_slug)
        if niche_id is None:
            continue
        session.execute(
            insert(union_model).values(
                **{entity_col: entity_id, 'niche_id': niche_id}
            )
        )


def resolve_niches(session: Session) -> dict[str, str]:
    """Upsert de los 5 niches del catalogo. Devuelve `{slug: id}`."""
    out: dict[str, str] = {}
    for slug in NICHES:
        nid = upsert_returning_id(
            session,
            Niche,
            'slug',
            {'slug': slug, 'display_order': NICHES.index(slug)},
        )
        out[slug] = nid
    return out


def ensure_named_vocab(
    session: Session,
    model: type,
    names: set[str],
) -> dict[str, str]:
    """Upsert de un vocabulario con clave natural `slug` (cv_skills /
    tax_tech_tags). El `slug` se deriva del `name` via `_to_slug`; el
    `name` se persiste como display canonico. Devuelve `{name: id}`.
    """
    out: dict[str, str] = {}
    for name in sorted(names):
        slug = _to_slug(name)
        nid = upsert_returning_id(
            session, model, 'slug', {'slug': slug, 'name': name}
        )
        out[name] = nid
    return out


# Paso entre prioridades consecutivas al reordenar: deja huecos para
# insertar entidades nuevas sin re-numerar todo.
_REORDER_STEP = 10


def reorder_niche_priorities(
    session: Session,
    entity_type: str,
    niche_id: str,
    ordered_ids: list[str],
) -> None:
    """Reescribe las prioridades de un niche segun el orden dado.

    `ordered_ids[0]` queda con la prioridad mas alta (orden descendente
    en el render). Solo toca las filas del `(entity_type, niche_id)`
    dado; otras entidades/niches no se ven afectadas.
    """
    session.execute(
        delete(NichePriority).where(
            NichePriority.entity_type == entity_type,
            NichePriority.niche_id == niche_id,
            NichePriority.entity_id.in_(ordered_ids),
        )
    )
    total = len(ordered_ids)
    for index, entity_id in enumerate(ordered_ids):
        session.execute(
            insert(NichePriority).values(
                entity_type=entity_type,
                entity_id=entity_id,
                niche_id=niche_id,
                priority=(total - index) * _REORDER_STEP,
            )
        )
