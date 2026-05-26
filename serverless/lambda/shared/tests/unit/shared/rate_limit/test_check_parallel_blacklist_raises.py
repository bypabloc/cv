"""
Given get_ip_rule retorna blacklist Y las otras 3 lookups exito,
When check_or_raise corre,
Then raise IPBlacklistedError ignorando los otros 3 resultados.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from shared.rate_limit.exceptions import IPBlacklistedError

pytestmark = pytest.mark.unit


def test_check_or_raise_parallel_blacklist_raises_ignoring_others() -> None:
    """IP blacklisteada raise IPBlacklistedError aunque las otras 3 lookups
    devuelvan exito (paralelizacion no rompe short-circuit logico)."""
    # Arrange
    blacklist_rule = {
        'kind': 'ip_blacklist',
        'reason': 'spam',
        'expires_at': 9999999999,
    }

    with patch.multiple(
        'shared.rate_limit.check',
        get_ip_rule=lambda _ip: blacklist_rule,
        get_country_rule=lambda _country: None,
        get_endpoint_rule=lambda _endpoint: {
            'limit': 100,
            'window_seconds': 60,
        },
        get_effective_count=lambda **_kw: 0.0,
        increment_bucket=lambda **_: {'turnstile_tokens': 0},
    ):
        from shared.rate_limit.check import check_or_raise

        # Act + Assert
        with pytest.raises(IPBlacklistedError) as exc:
            check_or_raise(
                ip='1.2.3.4', endpoint='/contact', country='CL'
            )

    assert exc.value.code == 'IP_BLACKLISTED'
    assert exc.value.extra.get('ip') == '1.2.3.4'
