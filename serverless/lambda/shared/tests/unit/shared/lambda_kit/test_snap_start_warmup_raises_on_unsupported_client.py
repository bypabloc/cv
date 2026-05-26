"""
Given un client no soportado en la lista,
When register_warmup(['sqs', 's3']) corre (s3 no esta en _WARMUP_CALLS),
Then raise ValueError ANTES de cualquier call AWS (fail-fast).
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_register_warmup_raises_on_unsupported_client() -> None:
    """Typo en manifest aborta el INIT con error claro y sin llamar a AWS."""
    # Act + Assert
    from shared.lambda_kit.snap_start_warmup import register_warmup

    with pytest.raises(ValueError, match=r'no soportados.*s3'):
        register_warmup(['sqs', 's3'])
