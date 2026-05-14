"""Tests para contact_form.notification (SES + template render)."""

from __future__ import annotations

import pytest

from contact_form.notification import _render_mustache_lite, send_owner_email

pytestmark = pytest.mark.unit


class TestRenderMustacheLite:
    """_render_mustache_lite - mini-mustache."""

    def test_when_simple_vars_then_substitutes(self) -> None:
        """Given {{var}}, When render, Then substituye."""
        result = _render_mustache_lite('hola {{name}}', {'name': 'Pablo'})
        assert result == 'hola Pablo'

    def test_when_var_missing_then_empty_string(self) -> None:
        """Given var no en context, When render, Then empty."""
        result = _render_mustache_lite('hola {{name}}', {})
        assert result == 'hola '

    def test_when_truthy_block_then_includes(self) -> None:
        """Given {{#var}}block{{/var}} con var truthy, When render, Then incluye."""
        result = _render_mustache_lite(
            'a {{#optional}}OPCIONAL: {{optional}}{{/optional}} b',
            {'optional': 'value'},
        )
        assert 'OPCIONAL: value' in result

    def test_when_falsy_block_then_omits(self) -> None:
        """Given block con var falsy/empty, When render, Then omite."""
        result = _render_mustache_lite(
            'a {{#optional}}OPCIONAL{{/optional}} b',
            {'optional': None},
        )
        assert 'OPCIONAL' not in result

    def test_when_complex_template_then_renders(self) -> None:
        """Given template realista, When render, Then todo OK."""
        tpl = 'Nombre: {{name}}\n{{#company}}Empresa: {{company}}\n{{/company}}Mensaje: {{message}}'
        context = {
            'name': 'Pablo',
            'company': 'Acme',
            'message': 'hola',
        }
        result = _render_mustache_lite(tpl, context)
        assert 'Nombre: Pablo' in result
        assert 'Empresa: Acme' in result
        assert 'Mensaje: hola' in result


class TestSendOwnerEmail:
    """send_owner_email - SES integration."""

    def test_when_called_then_calls_ses_send_email(
        self, contact_form_aws: None
    ) -> None:
        """
        Given contact data + AWS mocked,
        When send_owner_email,
        Then SES recibe la llamada send_email (no excepcion).

        Nota: moto sesv2 puede no devolver MessageId en la respuesta;
        validamos que NO lanza excepcion.
        """
        # No raise -> success path
        result = send_owner_email({
            'contact_id': 'abc-123',
            'created_at': '2026-05-14T15:00:00Z',
            'name': 'Pablo',
            'email': 'p@example.com',
            'message': 'Hola mundo',
            'niche': 'generic',
            'ip': '1.2.3.4',
        })

        # message_id puede ser string vacio si moto no lo retorna
        assert isinstance(result, str)
