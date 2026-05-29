"""Guard de regresion: cv_repository ordena por una columna REAL de Niche.

Given el modelo Niche y el modulo cv_repository,
When se inspecciona la columna usada en los order_by de niches,
Then Niche.display_order existe y Niche NO tiene `position`.

El bug fijado usaba `.order_by(Niche.position)` pero el modelo solo define
`slug` + `display_order` -> AttributeError al construir CADA query del CV.
"""

import pytest

pytestmark = pytest.mark.unit


def test_niche_has_display_order_and_no_position():
    from shared.db.models.taxonomy.catalog import Niche
    from sqlalchemy.orm import InstrumentedAttribute

    # La columna correcta existe y es usable en un order_by.
    assert isinstance(Niche.display_order, InstrumentedAttribute)

    # La columna equivocada (la del bug) NO existe: si alguien revierte el
    # nombre, este assert lo atrapa antes que el AttributeError en runtime.
    assert not hasattr(Niche, 'position')


def test_cv_repository_orders_niches_by_display_order():
    """El codigo de cv_repository referencia display_order, no position."""
    import inspect

    import shared.db.cv_repository as cv_repository

    src = inspect.getsource(cv_repository)
    assert 'Niche.position' not in src
    assert 'Niche.display_order' in src
