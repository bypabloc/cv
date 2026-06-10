"""Engine del lifecycle UI de las entidades SIMPLES del CV (doc 12).

Las 6 entidades planas (education, certificate, award, language,
endorsement, publication) comparten el `SimpleEntityForm` parametrizado
del admin: este engine recorre los 10 pasos del flujo canonico
(crear -> guardar -> reload -> hidratacion exacta -> mutar -> verificar
UI + API espejo -> eliminar con confirmacion -> reload ausente) con la
lista de campos declarada por cada spec.

Los valores de create se eligen ROUND-TRIP-SAFE: el form hidrata desde el
GET /cv publico, asi que un valor cuya serializacion difiere del input
(ej. education start '2018-03' -> GET '2018') romperia la hidratacion.
Cada spec usa el formato que el GET preserva (educacion: YYYY; award:
YYYY-MM; certificate: YYYY-MM-DD).

El prefijo `_` evita que pytest recolecte este modulo como tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from api._cv_admin_flows import CvAdminSession
from api._cv_admin_flows import find_one

from ._cv_ui import ACTION_TIMEOUT
from ._cv_ui import bilang_values
from ._cv_ui import card
from ._cv_ui import cards_count
from ._cv_ui import close_dialog
from ._cv_ui import delete_entity
from ._cv_ui import dom_slugs
from ._cv_ui import field_value
from ._cv_ui import fill_bilang
from ._cv_ui import fill_field
from ._cv_ui import goto_cv_overview
from ._cv_ui import niche_checked
from ._cv_ui import niche_priority_value
from ._cv_ui import open_edit_entity
from ._cv_ui import open_new_entity
from ._cv_ui import open_section
from ._cv_ui import reload_section
from ._cv_ui import save_entity
from ._cv_ui import set_niche


_UNSET = object()


@dataclass
class SimpleField:
    """Un campo del form de una entidad simple + sus expectativas.

    - `kind`: 'text' (Input, incluye dates) | 'bilang' (par es/en).
    - `create`: valor inicial (str, o tuple (es, en) para bilang).
    - `update`: valor mutado en el paso 7 (None = sin mutacion).
    - `get_create` / `get_update`: valor esperado en el GET publico si
      difiere del default (text -> el string; bilang -> {'es','en'}).
    """

    name: str
    kind: str
    create: Any
    update: Any | None = None
    get_create: Any = _UNSET
    get_update: Any = _UNSET


def _fill(page: Any, spec: SimpleField, value: Any) -> None:
    if spec.kind == 'bilang':
        fill_bilang(page, spec.name, value[0], value[1])
    else:
        fill_field(page, f'cv-field-{spec.name}', value)


def _assert_form(page: Any, spec: SimpleField, value: Any, step: str) -> None:
    if spec.kind == 'bilang':
        got = bilang_values(page, spec.name)
        assert got == (value[0], value[1]), (
            f'[{step}] {spec.name}: {got!r} != {value!r}'
        )
    else:
        got = field_value(page, f'cv-field-{spec.name}')
        assert got == value, f'[{step}] {spec.name}: {got!r} != {value!r}'


def _expected_get(spec: SimpleField) -> Any:
    """Valor esperado en el GET publico tras el update (o el create)."""
    if spec.update is not None and spec.get_update is not _UNSET:
        return spec.get_update
    if spec.update is None and spec.get_create is not _UNSET:
        return spec.get_create
    final = spec.update if spec.update is not None else spec.create
    if spec.kind == 'bilang':
        return {'es': final[0], 'en': final[1]}
    return final


def run_simple_section_flow(
    cvp: Any,
    session: CvAdminSession,
    *,
    section: str,
    action_suffix: str,
    get_action: str | None,
    slug: str,
    fields: list[SimpleField],
    niche: str = 'generic',
    priority: int = 2,
) -> None:
    """Recorre los 10 pasos del lifecycle UI de una entidad simple.

    `cvp` es el `CvAdminPage` del conftest (page autenticada como el admin
    de cv_admin + captura de errores de consola). Registra el slug en la
    sesion API para el teardown idempotente ANTES de tocar la UI.
    """
    page = cvp.page
    session.register(action_suffix, slug)
    upsert_action = f'upsert-{action_suffix}'
    delete_action = f'delete-{action_suffix}'

    # 1. Navegar a la seccion + conteo inicial.
    goto_cv_overview(page)
    open_section(page, section)
    initial = cards_count(page)

    # 2. Alta: el dialog abre con el form vacio.
    open_new_entity(page)
    assert field_value(page, 'cv-field-slug') == ''

    # 3. Llenar TODOS los campos + niches/prioridad.
    fill_field(page, 'cv-field-slug', slug)
    for spec in fields:
        _fill(page, spec, spec.create)
    set_niche(page, niche, priority=priority)

    # 4. Guardar: 200 + toast + dialog cierra + card visible.
    save_entity(page, action=upsert_action)
    card(page, slug).wait_for(state='visible', timeout=ACTION_TIMEOUT)

    # 5. Reload: la card persiste (conteo == inicial + 1).
    reload_section(page)
    assert cards_count(page) == initial + 1
    assert dom_slugs(page).count(slug) == 1

    # 6. Reabrir editar: HIDRATACION EXACTA campo a campo.
    open_edit_entity(page, slug)
    assert field_value(page, 'cv-field-slug') == slug
    assert page.locator('[data-testid=cv-field-slug]').is_disabled() is True
    for spec in fields:
        _assert_form(page, spec, spec.create, 'hydrate-create')
    assert niche_checked(page, niche) is True
    assert niche_priority_value(page, niche) == str(priority)

    # 7. Mutar (los campos con `update`) y guardar.
    for spec in fields:
        if spec.update is not None:
            _fill(page, spec, spec.update)
    save_entity(page, action=upsert_action)

    # 8a. Verificar UI: reabrir -> mutaciones exactas.
    open_edit_entity(page, slug)
    for spec in fields:
        final = spec.update if spec.update is not None else spec.create
        _assert_form(page, spec, final, 'hydrate-update')
    close_dialog(page)

    # 8b. Espejo API: el GET publico refleja el estado final.
    if get_action is not None:
        entity = find_one(session.cv_get(get_action), slug)
        for spec in fields:
            expected = _expected_get(spec)
            got = entity.get(spec.name)
            assert got == expected, (
                f'[get-mirror] {spec.name}: {got!r} != {expected!r}'
            )
        assert entity.get('niches') == [niche]

    # 9. Eliminar con confirmacion + reload ausente.
    delete_entity(page, slug, action=delete_action)
    reload_section(page)
    assert cards_count(page) == initial
    assert dom_slugs(page).count(slug) == 0

    # 10. Cero errores de consola en todo el flujo.
    assert cvp.console_errors == []
