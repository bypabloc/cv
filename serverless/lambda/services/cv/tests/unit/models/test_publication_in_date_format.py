"""PublicationIn rechaza date con formato invalido.

Given date '15-01-2026' (orden invertido),
When se valida con PublicationIn,
Then ValidationError en date."""

import pytest
from pydantic import ValidationError


def test_publication_in_date_format():
    from models.content_simple import PublicationIn

    with pytest.raises(ValidationError) as exc:
        PublicationIn.model_validate({'slug': 'p', 'title': 'T', 'platform': 'X', 'url': 'https://x', 'date': '15-01-2026', 'summary': {'es': 's'}})
    assert any(
        e['loc'][:1] == ('date',) for e in exc.value.errors()
    ), f"esperaba error en date pero fue: {exc.value.errors()}"
