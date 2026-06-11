"""ProjectIn rechaza projectType fuera del enum.

Given projectType 'desktop',
When se valida con ProjectIn,
Then ValidationError en projectType."""

import pytest
from pydantic import ValidationError


def test_project_in_project_type_enum():
    from models.content import ProjectIn

    with pytest.raises(ValidationError) as exc:
        ProjectIn.model_validate({'slug': 'p', 'name': 'P', 'summary': {'es': 's'}, 'status': 'active', 'projectType': 'desktop'})
    assert any(
        e['loc'][:1] == ('projectType',) for e in exc.value.errors()
    ), f"esperaba error en projectType pero fue: {exc.value.errors()}"
