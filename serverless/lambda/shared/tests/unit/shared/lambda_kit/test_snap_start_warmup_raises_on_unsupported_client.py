"""
Given un client no soportado en la lista,
When register_warmup(['sqs', 'nonexistent-service']) corre,
Then raise ValueError ANTES de instanciar cualquier cliente (fail-fast).
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_register_warmup_raises_on_unsupported_client() -> None:
    """Typo en manifest aborta el INIT con error claro y sin instanciar boto3."""
    # Act + Assert
    from shared.lambda_kit.snap_start_warmup import register_warmup

    with pytest.raises(ValueError, match=r'no soportados.*nonexistent-service'):
        register_warmup(['sqs', 'nonexistent-service'])
