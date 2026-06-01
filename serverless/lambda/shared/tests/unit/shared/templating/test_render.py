"""shared.templating.jinja render_html / render_text.

Cubre: sustitucion de vars, autoescape HTML (anti-XSS), texto sin escape, y
StrictUndefined -> TemplateRenderError cuando falta una var.
"""

from __future__ import annotations

import pytest
from shared.templating.jinja import (
    TemplateRenderError,
    render_html,
    render_text,
)

pytestmark = pytest.mark.unit


def test_render_html_substitutes_vars():
    """Given un template con {{ name }}, Then sustituye el valor."""
    result = render_html('<p>Hola {{ name }}</p>', {'name': 'Pablo'})
    assert result == '<p>Hola Pablo</p>'


def test_render_html_escapes_html_in_vars():
    """Given una var con HTML, Then queda escapada (autoescape ON)."""
    result = render_html('<p>{{ name }}</p>', {'name': '<script>x</script>'})
    assert result == '<p>&lt;script&gt;x&lt;/script&gt;</p>'


def test_render_text_does_not_escape():
    """Given render_text con '&', Then NO escapa (texto plano)."""
    result = render_text('Hola {{ name }} & cia', {'name': 'Pablo'})
    assert result == 'Hola Pablo & cia'


def test_render_html_missing_var_raises():
    """Given una var faltante, Then StrictUndefined -> TemplateRenderError."""
    with pytest.raises(TemplateRenderError):
        render_html('<p>{{ missing }}</p>', {})
