"""
Given una lista vacia,
When register_warmup([]) corre,
Then no-op silencioso (no llama boto3, no loguea, no falla).
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_register_warmup_empty_list_is_noop() -> None:
    """Lista vacia no instancia ningun cliente boto3."""
    # Act + Assert
    from shared.lambda_kit.snap_start_warmup import register_warmup

    with patch(
        'shared.lambda_kit.snap_start_warmup._build_client'
    ) as mock_build:
        register_warmup([])
        mock_build.assert_not_called()
