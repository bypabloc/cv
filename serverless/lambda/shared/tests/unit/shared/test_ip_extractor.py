"""Unit tests para shared.ip_extractor."""

from __future__ import annotations

import pytest

from shared.ip_extractor import extract_country, extract_ip

pytestmark = pytest.mark.unit


class TestExtractIP:
    """extract_ip - prioridad CF > XFF > requestContext."""

    def test_when_cf_connecting_ip_present_then_returns_it(self) -> None:
        """
        Given header CF-Connecting-IP="1.2.3.4",
        When extract_ip(event),
        Then retorna "1.2.3.4".
        """
        event = {'headers': {'CF-Connecting-IP': '1.2.3.4'}}

        assert extract_ip(event) == '1.2.3.4'

    def test_when_cf_overrides_xff_and_sourceip_then_cf_wins(self) -> None:
        """
        Given headers con CF + XFF + sourceIp,
        When extract_ip,
        Then CF-Connecting-IP gana.
        """
        event = {
            'headers': {
                'CF-Connecting-IP': '1.2.3.4',
                'X-Forwarded-For': '5.6.7.8',
            },
            'requestContext': {'identity': {'sourceIp': '9.10.11.12'}},
        }

        assert extract_ip(event) == '1.2.3.4'

    def test_when_only_true_client_ip_then_returns_it(self) -> None:
        """
        Given header True-Client-IP (CF Enterprise),
        When extract_ip,
        Then retorna ese valor.
        """
        event = {'headers': {'True-Client-IP': '1.2.3.4'}}

        assert extract_ip(event) == '1.2.3.4'

    def test_when_only_xff_then_returns_first_hop(self) -> None:
        """
        Given X-Forwarded-For="a, b, c",
        When extract_ip,
        Then retorna "a" (first hop = cliente real).
        """
        event = {'headers': {'X-Forwarded-For': '1.2.3.4, 5.6.7.8, 9.10.11.12'}}

        assert extract_ip(event) == '1.2.3.4'

    def test_when_only_sourceip_then_returns_it(self) -> None:
        """
        Given solo requestContext.identity.sourceIp,
        When extract_ip,
        Then retorna ese valor.
        """
        event = {'requestContext': {'identity': {'sourceIp': '1.2.3.4'}}}

        assert extract_ip(event) == '1.2.3.4'

    def test_when_no_headers_nor_context_then_returns_empty(self) -> None:
        """
        Given event sin headers ni context,
        When extract_ip,
        Then retorna empty string.
        """
        assert extract_ip({}) == ''

    def test_when_lowercase_header_name_then_still_matches(self) -> None:
        """
        Given header con name lowercase (cf-connecting-ip),
        When extract_ip,
        Then matching es case-insensitive.
        """
        event = {'headers': {'cf-connecting-ip': '1.2.3.4'}}

        assert extract_ip(event) == '1.2.3.4'


class TestExtractCountry:
    """extract_country - lookup CF-IPCountry."""

    def test_when_cf_country_present_then_returns_upper(self) -> None:
        """
        Given header CF-IPCountry="CL",
        When extract_country,
        Then retorna "CL".
        """
        assert extract_country({'headers': {'CF-IPCountry': 'CL'}}) == 'CL'

    def test_when_lowercase_then_normalizes_to_upper(self) -> None:
        """
        Given header CF-IPCountry="cl",
        When extract_country,
        Then retorna "CL".
        """
        assert extract_country({'headers': {'CF-IPCountry': 'cl'}}) == 'CL'

    def test_when_no_header_then_returns_none(self) -> None:
        """Given sin CF-IPCountry, When extract_country, Then None."""
        assert extract_country({}) is None

    def test_when_invalid_length_then_returns_none(self) -> None:
        """Given header con longitud != 2, When extract_country, Then None."""
        assert extract_country({'headers': {'CF-IPCountry': 'CHL'}}) is None
        assert extract_country({'headers': {'CF-IPCountry': 'C'}}) is None
