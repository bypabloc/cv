"""Flujos cv (read), contact_form y tracking_pixel.

Casos de exito + error de los 3 Lambdas HTTP que NO requieren JWT. cv es
read-only (GET, sin mutacion). contact_form y tracking_pixel mutan (crean
un contact / tracking event) pero el cleanup borra lo creado.
"""

from __future__ import annotations

from api_e2e.config import NICHE
from api_e2e.config import TRACKING_EVENT_TYPE_ID
from api_e2e.config import apex_origin
from api_e2e.config import cv_origin
from api_e2e.config import synthetic_email
from api_e2e.runner import Runner
from api_e2e.runner import make_body
from api_e2e.support import HttpClient


_CV_ACTIONS = (
    'get',
    'profile',
    'experiences',
    'projects',
    'certificates',
    'awards',
    'education',
    'languages',
    'references',
    'skills',
)


def run_cv(runner: Runner, http: HttpClient, env: str) -> None:
    """cv: las 10 actions read (2xx) + 2 errores (action/operation)."""
    origin = cv_origin(env)
    for action in _CV_ACTIONS:
        params = {'operation': 'cv', 'action': action, 'locale': 'es'}
        if action != 'profile':
            params['niche'] = NICHE
        runner.case(
            lambda_name='cv',
            name=f'cv.{action} (success)',
            method='GET',
            call=lambda p=params: http.get('/cv', params=p, origin=origin),
            expected='2xx',
        )
    runner.case(
        lambda_name='cv',
        name='cv.nope (error: action invalida)',
        method='GET',
        call=lambda: http.get(
            '/cv',
            params={'operation': 'cv', 'action': 'nope', 'locale': 'es'},
            origin=origin,
        ),
        expected='4xx',
    )
    runner.case(
        lambda_name='cv',
        name='cv (error: sin operation)',
        method='GET',
        call=lambda: http.get(
            '/cv',
            params={'action': 'get'},
            origin=origin,
        ),
        expected='4xx',
    )


def run_contact(
    runner: Runner,
    http: HttpClient,
    env: str,
    run_id: str,
    bypass: str | None,
    created_emails: list[str],
) -> None:
    """contact_form: create exitoso (202 via bypass) + errores de payload."""
    origin = apex_origin(env)
    if bypass:
        email = synthetic_email(run_id, 'contact')
        created_emails.append(email)
        runner.case(
            lambda_name='contact_form',
            name='contact.create (success)',
            method='POST',
            call=lambda: http.post(
                '/contact',
                body=make_body(
                    'contact',
                    'create',
                    name='API E2E',
                    email=email,
                    message='Mensaje de prueba E2E del harness api_e2e.',
                    cf_token='',
                ),
                origin=origin,
                bypass_token=bypass,
            ),
            expected='2xx',
            samples=2,
            note='via bypass Turnstile',
        )
    else:
        print('  [SKIP] contact.create (success): bypass no disponible')

    runner.case(
        lambda_name='contact_form',
        name='contact.create (error: sin message)',
        method='POST',
        call=lambda: http.post(
            '/contact',
            body=make_body(
                'contact',
                'create',
                name='API E2E',
                email='success+e2e@simulator.amazonses.com',
                cf_token='',
            ),
            origin=origin,
            bypass_token=bypass,
        ),
        expected='4xx',
    )
    runner.case(
        lambda_name='contact_form',
        name='contact.create (error: email invalido)',
        method='POST',
        call=lambda: http.post(
            '/contact',
            body=make_body(
                'contact',
                'create',
                name='API E2E',
                email='no-es-un-email',
                message='mensaje suficientemente largo para pasar',
                cf_token='',
            ),
            origin=origin,
            bypass_token=bypass,
        ),
        expected='4xx',
    )


def run_tracking(
    runner: Runner,
    http: HttpClient,
    env: str,
    run_id: str,
    created_sessions: list[str],
) -> None:
    """tracking_pixel: track exitoso (202) + errores de payload."""
    origin = apex_origin(env)
    session_id = f'sess-{run_id}-track-000000000000'
    created_sessions.append(session_id)

    def _track_body(**over: object) -> dict:
        base: dict[str, object] = {
            'session_id': session_id,
            'event_id': 'a1b2c3d4e5f60718293a4b5c6d7e8f90',
            'event_type_id': TRACKING_EVENT_TYPE_ID,
            'page_url': 'https://the-full-stack.com/projects',
            'page_title': 'Projects',
            'page_path': '/projects',
            'utm_source': 'e2e',
            'utm_medium': 'api',
            'utm_campaign': 'verify',
            'utm_content': 'run',
            'viewport_width': 1920,
            'viewport_height': 1080,
            'niche': NICHE,
        }
        base.update(over)
        return make_body('tracking', 'track', **base)

    runner.case(
        lambda_name='tracking_pixel',
        name='tracking.track (success)',
        method='POST',
        call=lambda: http.post('/track', body=_track_body(), origin=origin),
        expected='2xx',
        samples=3,
    )
    runner.case(
        lambda_name='tracking_pixel',
        name='tracking.track (error: sin event_type_id)',
        method='POST',
        call=lambda: http.post(
            '/track',
            body=make_body(
                'tracking',
                'track',
                session_id=session_id,
                event_id='a1b2c3d4e5f60718293a4b5c6d7e8f90',
                page_url='https://the-full-stack.com/p',
                page_title='P',
                page_path='/p',
                utm_source='e2e',
                utm_medium='api',
                utm_campaign='verify',
                utm_content='run',
                viewport_width=1920,
                viewport_height=1080,
                niche=NICHE,
            ),
            origin=origin,
        ),
        expected='4xx',
    )
    runner.case(
        lambda_name='tracking_pixel',
        name='tracking.track (error: viewport invalido)',
        method='POST',
        call=lambda: http.post(
            '/track',
            body=_track_body(viewport_width=999999),
            origin=origin,
        ),
        expected='4xx',
    )
