"""
Given que se generan 1000 codes con CSPRNG,
When se cuentan los unicos,
Then >= 995 son unicos (colision esperada < 5 por la prob 1-in-30^8).
"""

import pytest
from shared.auth import generate_code

pytestmark = pytest.mark.unit


def test_codes_generate_high_uniqueness():
    # Arrange
    iterations = 1000

    # Act
    codes = [generate_code() for _ in range(iterations)]
    unique = set(codes)

    # Assert
    # 30^8 = 6.56e11. Prob de colision en 1000 muestras es ~7.6e-7.
    # Limite defensivo: >=995 unicos (permite hasta 5 colisiones).
    assert len(unique) >= 995
