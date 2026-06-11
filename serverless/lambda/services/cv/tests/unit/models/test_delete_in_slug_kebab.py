"""DeleteIn rechaza slug no-kebab-case.

Given slug 'Not A Slug',
When se valida con DeleteIn,
Then ValidationError en slug."""

import pytest
from pydantic import ValidationError


def test_delete_in_slug_kebab():
    from models.content_simple import DeleteIn

    with pytest.raises(ValidationError) as exc:
        DeleteIn.model_validate({'slug': 'Not A Slug'})
    assert any(
        e['loc'][:1] == ('slug',) for e in exc.value.errors()
    ), f"esperaba error en slug pero fue: {exc.value.errors()}"
