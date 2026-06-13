"""ProjectIn rechaza status fuera del enum.

Given status 'archived',
When se valida con ProjectIn,
Then ValidationError en status."""

import pytest
from pydantic import ValidationError


def test_project_in_status_enum():
    from models.content import ProjectIn

    with pytest.raises(ValidationError) as exc:
        ProjectIn.model_validate({'slug': 'p', 'name': 'P', 'summary': {'es': 's'}, 'status': 'archived', 'projectType': 'web'})
    assert any(
        e['loc'][:1] == ('status',) for e in exc.value.errors()
    ), f"esperaba error en status pero fue: {exc.value.errors()}"
