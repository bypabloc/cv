"""Registro de passkey WebAuthn end-to-end contra el admin desplegado.

Ejercita el fix del bug "Cannot read properties of undefined (reading
'replace')" (PR #262): el backend (`webauthn.register-options`) devuelve las
options ENVUELTAS en `publicKey`; el componente `WebAuthnRegisterButton` debe
pasar `data.options.publicKey` (el contenido PLANO) a
`startRegistration({optionsJSON})`. Si pasara el wrapper, @simplewebauthn
leeria `optionsJSON.challenge` = undefined y reventaria con el TypeError ANTES
de abrir el ceremony.

El ceremony se completa con un Virtual Authenticator de CDP (sin hardware ni
dialogo del SO). Corre contra el deploy dev real
(`admin.portfolio.dev.the-full-stack.com`), donde el RP ID
`portfolio.dev.the-full-stack.com` SI es un sufijo registrable del dominio de
la pagina (en localhost daria SecurityError, que es la limitacion conocida del
test manual). La prueba es doble:

1. Front: aparece el toast "Passkey registrado" (el ceremony arranco, parseo
   las options y el register-verify del backend acepto la credential).
2. Backend: queda 1 fila en `auth_webauthn_credentials` para el user (el
   ceremony se completo server-side, no solo el toast).
"""

from __future__ import annotations

from shared.browser import add_virtual_authenticator
from shared.browser import screenshot
from shared.environment import Environment


def test_register_passkey_completes_ceremony_and_persists_credential(
    logged_in_page: tuple,
    auth,
    environment: Environment,
) -> None:
    """
    Given un user active autenticado en el shell del admin desplegado, con un
        Virtual Authenticator (CDP) instalado en su contexto,
    When navega a Settings > Seguridad y hace click en "Agregar passkey"
        (dispara navigator.credentials.create con las options del backend),
    Then el ceremony se completa: aparece el toast "Passkey registrado" y queda
        exactamente 1 credential WebAuthn activo en Neon para el user — sin el
        TypeError ".replace" (que reventaria el ceremony antes de empezar).
    """
    # Arrange: page autenticada en el shell + user_id real, sin passkeys aun.
    page, _email, user_id = logged_in_page
    assert environment.count_webauthn_credentials(user_id) == 0
    # Captura los errores de consola del browser (diagnostico del ceremony).
    console_errors: list[str] = []
    page.on(
        'console',
        lambda msg: console_errors.append(f'{msg.type}: {msg.text}')
        if msg.type in ('error', 'warning')
        else None,
    )
    # Virtual Authenticator: responde el ceremony sin hardware ni dialogo.
    add_virtual_authenticator(page)
    # Navega a la tab Seguridad (client-side, preserva la sesion).
    page.locator('nav').get_by_role('link', name='Configuracion').click()
    page.get_by_role('link', name='Seguridad').click()
    page.wait_for_url('**/settings/security**', timeout=15_000)
    page.get_by_role('button', name='Agregar passkey').wait_for(
        state='visible', timeout=15_000,
    )

    # Diagnostico: captura el body del register-verify (el response del
    #   ceremony) para inspeccionar que produce el Virtual Authenticator.
    verify_bodies: list[str] = []

    def _capture_verify(request: object) -> None:
        post = getattr(request, 'post_data', None)
        if post and 'register-verify' in post:
            verify_bodies.append(post)

    page.on('request', _capture_verify)

    # Act: dispara el register ceremony (el Virtual Authenticator lo resuelve).
    page.get_by_role('button', name='Agregar passkey').click()

    # Assert (front): toast de exito — el ceremony arranco (sin .replace) y el
    #   register-verify del backend acepto la credential.
    try:
        page.wait_for_selector('text=Passkey registrado', timeout=30_000)
    except Exception:  # noqa: BLE001 -- diagnostico antes de re-fallar
        screenshot(page, 'results/webauthn-register-fail.png', full_page=True)
        toasts = page.locator('[data-sonner-toast]').all_inner_texts()
        creds = environment.count_webauthn_credentials(user_id)
        verify_payload = verify_bodies[-1] if verify_bodies else '(ninguno)'
        raise AssertionError(
            'toast "Passkey registrado" no aparecio. '
            f'toasts visibles={toasts!r} '
            f'console={console_errors[-8:]!r} '
            f'creds_en_neon={creds} url={page.url}\n'
            f'register-verify body={verify_payload[:1200]}',
        ) from None

    # Assert (backend): el credential quedo persistido en Neon (ceremony
    #   completo server-side, no solo el toast).
    assert environment.count_webauthn_credentials(user_id) == 1
