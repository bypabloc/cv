"""CertificateIn exige url.

Given un certificado sin url,
When se valida con CertificateIn,
Then ValidationError en url."""

import pytest
from pydantic import ValidationError


def test_certificate_in_url_required():
    from models.content_simple import CertificateIn

    with pytest.raises(ValidationError) as exc:
        CertificateIn.model_validate({'slug': 'c', 'title': 'T', 'issuer': 'I', 'date': '2023-04-20'})
    assert any(
        e['loc'][:1] == ('url',) for e in exc.value.errors()
    ), f"esperaba error en url pero fue: {exc.value.errors()}"
