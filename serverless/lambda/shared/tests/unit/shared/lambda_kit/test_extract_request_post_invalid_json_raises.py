"""shared.lambda_kit.http_dispatch.extract_request — POST body invalido.

Given un evento POST con un body que no es JSON valido,
When se procesa con extract_request,
Then levanta ValidationError con code='INVALID_JSON'.
"""

from __future__ import annotations

import pytest
from shared.core.exceptions import ValidationError
from shared.lambda_kit import extract_request

pytestmark = pytest.mark.unit


def test_extract_request_post_invalid_json_raises() -> None:
    # Arrange
    event = {'httpMethod': 'POST', 'body': '{not valid json'}

    # Act
    with pytest.raises(ValidationError) as exc_info:
        extract_request(event)

    # Assert
    assert exc_info.value.code == 'INVALID_JSON'


def test_extract_request_post_non_dict_body_raises() -> None:
    """Given POST con body JSON pero array (no dict), Then INVALID_JSON."""
    # Arrange
    event = {'httpMethod': 'POST', 'body': '[1, 2, 3]'}

    # Act
    with pytest.raises(ValidationError) as exc_info:
        extract_request(event)

    # Assert
    assert exc_info.value.code == 'INVALID_JSON'
