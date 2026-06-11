"""Fixtures y helpers del Lambda `cv_admin` (plan c-cv-management).

Sesion admin sintetica (user activo + whitelist SSM `admin-emails` con
`_wait_ssm_promoted` ANTES del bust de cache + access JWT), helpers de
POST `/cv` (con retry SOLO ante el 404 de consistencia eventual de
la whitelist) y GET `/cv` publico, registro de slugs sinteticos para el
teardown idempotente y el runner generico de la plantilla "full
lifecycle" de las 9 entidades del CV.

Reglas duras que este modulo enforza:
- TODO slug/dato creado lleva el prefijo `e2e-cvadm-`.
- HERMETICO: ningun token/secreto a stdout.
- Asserts EXACTOS (`==`) en el runner del lifecycle.

El prefijo `_` evita que pytest recolecte este modulo como tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
import secrets
import time
from typing import Any
import uuid

from shared.auth_support import create_active_user_with_password
from shared.auth_support import login_with_password
from shared.config import admin_origin
from shared.config import cv_origin
from shared.environment import Environment
from shared.http import HttpClient
from shared.http import Response

from ._flows import _converge_admin_recognized as _converge_users_lambda
from ._flows import _wait_ssm_promoted


# Prefijo de TODO dato sintetico de los tests de cv_admin.
TAG = 'e2e-cvadm'

# Orden canonico de presentacion de los 5 niches (display_order del
# catalogo `tax_niches`; lo seedea `resolve_niches` en cada upsert).
NICHES_DISPLAY_ORDER = ('fintech', 'architect', 'leader', 'vibe', 'generic')

# El access JWT dura 15 min; relogin preventivo pasados 10 min.
_TOKEN_MAX_AGE_SECONDS = 600


def synthetic_slug(prefix: str) -> str:
    """Slug sintetico unico `e2e-cvadm-<prefix>-<rand6>`."""
    return f'{TAG}-{prefix}-{secrets.token_hex(3)}'


def ordered_niches(niches: list[str]) -> list[str]:
    """Proyecta `niches` al orden display_order del catalogo (el del GET)."""
    return [n for n in NICHES_DISPLAY_ORDER if n in niches]


def slugs_of(items: list[dict[str, Any]]) -> list[str]:
    """Lista de slugs de una respuesta GET /cv (en su orden)."""
    return [str(e.get('slug')) for e in items]


def find_one(items: list[dict[str, Any]], slug: str) -> dict[str, Any]:
    """Devuelve LA entidad con `slug` (falla si no esta o esta repetida)."""
    matches = [e for e in items if e.get('slug') == slug]
    assert len(matches) == 1, (
        f'slug {slug!r} aparece {len(matches)} veces en el GET'
    )
    return matches[0]


def _is_admin_denied(response: Response) -> bool:
    """True si la respuesta es el 404 anti-enumeration del guard admin.

    Distingue el `{'error': 'NOT_FOUND', 'code': 'NOT_FOUND'}` (whitelist
    vieja cacheada en un contenedor -> reintentable) del 404 de negocio
    SLUG_NOT_FOUND (`{'error_code': 'SLUG_NOT_FOUND', ...}`).
    """
    return (
        response.status == 404
        and isinstance(response.body, dict)
        and response.body.get('code') == 'NOT_FOUND'
    )


class CvAdminSession:
    """Sesion admin sintetica contra el Lambda cv_admin desplegado.

    Mantiene el access JWT fresco (relogin preventivo), expone los
    helpers POST `/cv` y GET `/cv`, y registra los slugs/vocab
    sinteticos creados para el teardown idempotente del conftest.
    """

    def __init__(
        self,
        *,
        http: HttpClient,
        environment: Environment,
        env_name: str,
        email: str,
        bypass: str,
    ) -> None:
        self.http = http
        self.environment = environment
        self.env_name = env_name
        self.email = email
        self.bypass = bypass
        self.origin = admin_origin(env_name)
        self._cv_origin = cv_origin(env_name)
        self.original_whitelist = ''
        self._access: str | None = None
        self._access_at = 0.0
        self._catalogs: dict[str, Any] | None = None
        # Registro para el teardown: {action_suffix: {slug, ...}}.
        self.created: dict[str, set[str]] = {}
        self.vocab_skills: set[str] = set()
        self.vocab_tech_tags: set[str] = set()

    # --- token ---

    def _relogin(self) -> None:
        access, _refresh = login_with_password(
            self.http,
            self.origin,
            self.email,
            self.bypass,
        )
        if not access:
            msg = 'login del admin sintetico de cv_admin fallo'
            raise RuntimeError(msg)
        self._access = access
        self._access_at = time.monotonic()

    def token(self) -> str:
        """Access JWT vigente (relogin si esta por expirar)."""
        stale = time.monotonic() - self._access_at > _TOKEN_MAX_AGE_SECONDS
        if self._access is None or stale:
            self._relogin()
        return self._access  # type: ignore[return-value]

    # --- HTTP ---

    def post_raw(
        self,
        action: str,
        data: dict[str, Any],
        *,
        operation: str = 'content',
        bearer: str | None = None,
        ip: str | None = None,
    ) -> Response:
        """POST /cv SIN retries (body FLAT: operation/action + data)."""
        body = {'operation': operation, 'action': action, **data}
        return self.http.post(
            '/cv',
            body=body,
            origin=self.origin,
            bearer=bearer,
            ip=ip,
        )

    def post(
        self,
        action: str,
        data: dict[str, Any],
        *,
        operation: str = 'content',
        retries: int = 15,
        delay: float = 4.0,
    ) -> Response:
        """POST /cv autenticado con retry de consistencia eventual.

        Reintenta SOLO ante (a) el 404 NOT_FOUND del guard admin (un
        contenedor con la whitelist vieja cacheada — mismo patron que
        `_flows._admin_call`) y (b) un 401 por token vencido (relogin).
        Cualquier otra respuesta (exito o error de negocio) se devuelve
        tal cual. Las mutaciones son upserts/deletes idempotentes, asi
        que el retry es seguro.
        """
        last: Response | None = None
        for attempt in range(1, retries + 1):
            last = self.post_raw(
                action,
                data,
                operation=operation,
                bearer=self.token(),
            )
            if last.status == 401:
                self._relogin()
            elif not _is_admin_denied(last):
                return last
            if attempt < retries:
                time.sleep(delay)
        return last  # type: ignore[return-value]

    def cv_get(
        self,
        action: str,
        *,
        niche: str | None = None,
        locale: str = 'es',
    ) -> Any:
        """GET /cv publico (sin auth). Devuelve el body parseado."""
        params = {'operation': 'cv', 'action': action, 'locale': locale}
        if niche is not None:
            params['niche'] = niche
        r = self.http.get('/cv', params=params, origin=self._cv_origin)
        if r.status != 200:
            msg = f'GET /cv {action} fallo: HTTP {r.status} {r.body!r}'
            raise RuntimeError(msg)
        return r.body

    def catalogs_data(self) -> dict[str, Any]:
        """Respuesta del action `catalogs` (cacheada por sesion)."""
        if self._catalogs is None:
            r = self.post('catalogs', {})
            if r.status != 200:
                msg = f'catalogs fallo: HTTP {r.status} {r.body!r}'
                raise RuntimeError(msg)
            self._catalogs = r.body
        return self._catalogs

    def existing_names(self, kind: str, count: int) -> list[str]:
        """`count` names REALES del vocabulario (`skills` | `techTags`).

        Excluye los sinteticos (`e2e-cvadm-*`) de corridas previas.
        """
        rows = self.catalogs_data()[kind]
        names = [
            str(r['name']) for r in rows if not str(r['slug']).startswith(TAG)
        ]
        if len(names) < count:
            msg = f'el catalogo {kind} no tiene {count} entradas reales'
            raise RuntimeError(msg)
        return names[:count]

    # --- registro para el teardown ---

    def register(self, action_suffix: str, slug: str) -> None:
        """Registra un slug sintetico para el delete idempotente final."""
        self.created.setdefault(action_suffix, set()).add(slug)

    def register_vocab(self, kind: str, slug: str) -> None:
        """Registra una skill/tech tag NUEVA para limpiarla en Neon."""
        target = self.vocab_skills if kind == 'skill' else self.vocab_tech_tags
        target.add(slug)


def open_admin_session(
    *,
    http: HttpClient,
    environment: Environment,
    env_name: str,
    bypass: str,
) -> CvAdminSession:
    """Crea el user admin sintetico + promueve la whitelist + converge.

    Orden CRITICO (gotcha conocido del modulo admin.*): el
    `_wait_ssm_promoted` corre ANTES del bust de cache, para que el cold
    start del Lambda lea la whitelist YA promovida (put_parameter es
    eventualmente consistente). Despues converge el reconocimiento de
    admin (bust hasta el primer 200, luego confirmacion estable SIN
    bustear) ANTES de devolver la sesion.
    """
    email = (
        f'success+{TAG}-admin-{secrets.token_hex(3)}@simulator.amazonses.com'
    )
    user_id = create_active_user_with_password(
        http,
        environment,
        admin_origin(env_name),
        email,
        bypass,
    )
    if not user_id:
        msg = 'no se pudo crear el user admin sintetico de cv_admin'
        raise RuntimeError(msg)

    session = CvAdminSession(
        http=http,
        environment=environment,
        env_name=env_name,
        email=email,
        bypass=bypass,
    )
    original = environment.read_admin_emails()
    session.original_whitelist = original
    promoted = f'{original},{email}' if original else email
    environment.write_admin_emails(promoted)
    _wait_ssm_promoted(environment, email)
    print('  [INFO] cv_admin: whitelist promovida + cold restart cv_admin...')
    _converge_admin_recognized(session)
    return session


def converge_users_recognized(session: CvAdminSession) -> None:
    """Converge el reconocimiento de admin TAMBIEN en el Lambda `users`.

    El sidebar del admin decide el item adminOnly "Gestion CV" sondeando
    `users.admin.list-users` (`use-is-admin`) — un Lambda DISTINTO de
    cv_admin, con su propia cache de whitelist (TTL 300s repartida entre
    varios contenedores). Sin esta convergencia el probe del browser es
    una loteria: los specs cuyo probe pega un contenedor stale ven 404 y
    el item "Gestion CV" nunca aparece (timeout en goto_cv_overview).
    Reusa el patron 2 fases de `_flows._converge_admin_recognized`.
    """
    _converge_users_lambda(
        session.http,
        session.environment,
        session.origin,
        session.token(),
    )


def _converge_admin_recognized(
    session: CvAdminSession,
    *,
    bust_rounds: int = 6,
    stable_hits: int = 10,
    confirm_rounds: int = 40,
    delay: float = 2.0,
) -> None:
    """Bloquea hasta que `catalogs` de 200 ESTABLE antes de los tests.

    Mismo patron de 2 fases que `_flows._converge_admin_recognized` (el
    Lambda cv_admin cachea la whitelist module-level con TTL 300s y AWS
    reparte entre varios contenedores):

    1. BUST: re-bustear hasta el primer 200 (recicla contenedores viejos).
    2. CONFIRM (sin bustear): exigir `stable_hits` 200 consecutivos. La
       ULTIMA operacion del warm-up NUNCA es un bust.
    """
    for _ in range(bust_rounds):
        resp = session.post_raw(
            'catalogs',
            {},
            bearer=session.token(),
        )
        if resp.status == 200:
            break
        session.environment.bust_lambda_cache('cv')
        time.sleep(delay)

    hits = 0
    for _ in range(confirm_rounds):
        resp = session.post_raw(
            'catalogs',
            {},
            bearer=session.token(),
        )
        if resp.status == 200:
            hits += 1
            if hits >= stable_hits:
                return
        else:
            hits = 0
        time.sleep(delay)


# Secciones GET /cv que listan entidades sinteticas (para la verificacion
# del teardown). publication NO tiene action GET (gap conocido del plan).
_TEARDOWN_GET_ACTIONS = (
    'experiences',
    'projects',
    'certificates',
    'awards',
    'education',
    'languages',
    'references',
    'skills',
)


def close_admin_session(
    session: CvAdminSession,
    *,
    keep_data: bool,
) -> None:
    """Teardown de la sesion: deletes idempotentes + restore + cleanup.

    1. delete-<entidad> por cada slug registrado (200 o 4404 ya-borrado),
       con la whitelist AUN promovida.
    2. Verificacion GET best-effort: ninguna seccion lista `e2e-cvadm-*`.
    3. finally: restaura la whitelist SSM + quita la env var efimera del
       bust + limpia el vocabulario sintetico y el user admin en Neon.
    """
    env = session.environment
    try:
        if not keep_data:
            for suffix, slugs in sorted(session.created.items()):
                for slug in sorted(slugs):
                    session.post(
                        f'delete-{suffix}',
                        {'slug': slug},
                        retries=3,
                        delay=2.0,
                    )
            _warn_leftovers(session)
    finally:
        env.write_admin_emails(session.original_whitelist)
        env.clear_lambda_cache_buster('cv')
        print('  [INFO] cv_admin: whitelist SSM restaurada + buster off')
        if not keep_data:
            env.cleanup_cv_vocab(
                skill_slugs=sorted(session.vocab_skills),
                tech_tag_slugs=sorted(session.vocab_tech_tags),
            )
            env.cleanup_users([session.email])


def _warn_leftovers(session: CvAdminSession) -> None:
    """Imprime un WARN si alguna seccion GET aun lista slugs sinteticos."""
    for action in _TEARDOWN_GET_ACTIONS:
        try:
            leftovers = [
                s for s in slugs_of(session.cv_get(action)) if s.startswith(TAG)
            ]
        except RuntimeError as exc:
            print(f'  [WARN] cv_admin teardown: GET {action} fallo: {exc}')
            continue
        if leftovers:
            print(
                f'  [WARN] cv_admin teardown: {action} aun lista '
                f'sinteticos: {leftovers}'
            )


def minimal_experience_payload(slug: str) -> dict[str, Any]:
    """Payload VALIDO minimo de upsert-experience (para auth/validacion).

    Solo los campos requeridos por `ExperienceIn`; sin niches (no toca el
    catalogo) — sirve para casos donde el request NO debe persistir o
    donde solo importa pasar la fase de validacion Pydantic.
    """
    return {
        'slug': slug,
        'role': {'es': 'Rol sintetico', 'en': 'Synthetic role'},
        'company': 'E2E Cvadm Corp',
        'country': 'Chile',
        'start': '2024-01',
        'seniority': 'senior',
    }


# =========================================================================
# Runner generico de la plantilla "full lifecycle" (doc 11, pasos 1-6)
# =========================================================================


@dataclass
class LifecycleSpec:
    """Especificacion del lifecycle de UNA entidad del CV.

    - `action_suffix`: sufijo de las actions (`experience`,
      `skill-category`, ...).
    - `get_action`: action GET /cv de la seccion (None = sin lectura
      publica, caso publication).
    - `create_expect` / `update_expect`: proyeccion campo -> valor EXACTO
      esperado en el GET tras el paso.
    - `*_expect_sets`: campos lista cuyo ORDEN depende de la collation de
      la DB (skills por nombre): se asserta igualdad de set + largo.
    - `*_expect_key_order`: campos dict cuyo ORDEN de claves es contrato
      (metrics de project): se asserta la lista exacta de keys.
    - `update_absent`: claves que el GET ya NO debe traer tras el update
      (campos vueltos null -> _drop_nones los omite).
    - `update_niche_out`: niche que el update des-asigno (el GET filtrado
      ya no debe listar la entidad).
    """

    action_suffix: str
    get_action: str | None
    slug: str
    create_payload: dict[str, Any]
    update_payload: dict[str, Any]
    niche_in: str
    niche_out: str
    create_expect: dict[str, Any] = field(default_factory=dict)
    update_expect: dict[str, Any] = field(default_factory=dict)
    create_expect_sets: dict[str, set[str]] = field(default_factory=dict)
    update_expect_sets: dict[str, set[str]] = field(default_factory=dict)
    create_expect_key_order: dict[str, list[str]] = field(
        default_factory=dict,
    )
    update_expect_key_order: dict[str, list[str]] = field(
        default_factory=dict,
    )
    update_absent: tuple[str, ...] = ()
    update_niche_out: str | None = None


def _assert_projection(
    entity: dict[str, Any],
    expect: dict[str, Any],
    expect_sets: dict[str, set[str]],
    expect_key_order: dict[str, list[str]],
    *,
    step: str,
) -> None:
    """Asserts EXACTOS campo a campo de una proyeccion del GET."""
    for key, expected in expect.items():
        got = entity.get(key)
        assert got == expected, f'[{step}] {key}: {got!r} != {expected!r}'
    for key, expected_set in expect_sets.items():
        got_list = entity.get(key)
        assert set(got_list) == expected_set, (
            f'[{step}] {key} (set): {got_list!r} != {expected_set!r}'
        )
        assert len(got_list) == len(expected_set), (
            f'[{step}] {key} (largo): {got_list!r}'
        )
    for key, expected_order in expect_key_order.items():
        got_keys = list(entity.get(key, {}).keys())
        assert got_keys == expected_order, (
            f'[{step}] {key} (orden de keys): {got_keys!r} != '
            f'{expected_order!r}'
        )


def run_entity_lifecycle(
    session: CvAdminSession,
    spec: LifecycleSpec,
) -> str:
    """Ejecuta los 6 pasos de la plantilla canonica sobre una entidad.

    1. CREATE (upsert) -> 200 + `{entity, id}` (el data del upsert es la
       referencia `{entity, id}`, NO la entidad completa — los asserts
       campo a campo van sobre el GET publico).
    2. READ publica + cache: el GET ya la lista (invalidacion tag 'cv').
    3. READ por niche: el filtro la incluye/excluye exacto.
    4. UPDATE (re-upsert con mutaciones) -> mismo `id` (upsert real) +
       GET refleja cada mutacion.
    5. DELETE -> `{entity, deleted: true}` + GET ya no la lista en NINGUN
       niche.
    6. DELETE idempotente -> 404 con el error 4404 SLUG_NOT_FOUND exacto.

    Devuelve el `id` creado (lo usa el caso publication para el re-upsert).
    """
    session.register(spec.action_suffix, spec.slug)
    upsert = f'upsert-{spec.action_suffix}'
    delete = f'delete-{spec.action_suffix}'

    # 1. CREATE
    r = session.post(upsert, spec.create_payload)
    assert r.status == 200, f'[create] HTTP {r.status}: {r.body!r}'
    assert sorted(r.body.keys()) == ['entity', 'id'], r.body
    assert r.body['entity'] == spec.slug
    created_id = r.body['id']
    assert str(uuid.UUID(created_id)) == created_id

    if spec.get_action is not None:
        # 2. READ publica (la invalidacion por tag 'cv' ya corrio).
        entity = find_one(session.cv_get(spec.get_action), spec.slug)
        _assert_projection(
            entity,
            spec.create_expect,
            spec.create_expect_sets,
            spec.create_expect_key_order,
            step='create-get',
        )
        # Round-trip de priority por niche (TODAS las entidades lo
        # exponen en el GET; el editor del admin hidrata el picker de
        # este mapa — regresion: las simples no lo serializaban y cada
        # save desde el admin reseteaba la prioridad a 1).
        if 'priority' in spec.create_payload:
            assert entity['priority'] == spec.create_payload['priority'], (
                f'[create-priority] {entity.get("priority")!r} != '
                f'{spec.create_payload["priority"]!r}'
            )
        # 3. READ por niche: n1 la incluye, n2 (no asignado) NO.
        in_n1 = slugs_of(session.cv_get(spec.get_action, niche=spec.niche_in))
        assert in_n1.count(spec.slug) == 1, (
            f'[niche-in] {spec.niche_in}: {in_n1!r}'
        )
        in_n2 = slugs_of(
            session.cv_get(spec.get_action, niche=spec.niche_out),
        )
        assert in_n2.count(spec.slug) == 0, (
            f'[niche-out] {spec.niche_out}: {in_n2!r}'
        )

    # 4. UPDATE (re-upsert): mismo id (upsert real, no fila nueva).
    r2 = session.post(upsert, spec.update_payload)
    assert r2.status == 200, f'[update] HTTP {r2.status}: {r2.body!r}'
    assert r2.body['entity'] == spec.slug
    assert r2.body['id'] == created_id

    if spec.get_action is not None:
        entity = find_one(session.cv_get(spec.get_action), spec.slug)
        _assert_projection(
            entity,
            spec.update_expect,
            spec.update_expect_sets,
            spec.update_expect_key_order,
            step='update-get',
        )
        # Round-trip de priority tambien tras el update (ej. certificate
        # recorta el mapa al quitar un niche).
        if 'priority' in spec.update_payload:
            assert entity['priority'] == spec.update_payload['priority'], (
                f'[update-priority] {entity.get("priority")!r} != '
                f'{spec.update_payload["priority"]!r}'
            )
        for key in spec.update_absent:
            assert key not in entity, (
                f'[update-absent] {key} deberia estar ausente: '
                f'{entity.get(key)!r}'
            )
        if spec.update_niche_out is not None:
            gone = slugs_of(
                session.cv_get(
                    spec.get_action,
                    niche=spec.update_niche_out,
                ),
            )
            assert gone.count(spec.slug) == 0, (
                f'[update-niche-out] {spec.update_niche_out}: {gone!r}'
            )

    # 5. DELETE
    rd = session.post(delete, {'slug': spec.slug})
    assert rd.status == 200, f'[delete] HTTP {rd.status}: {rd.body!r}'
    assert rd.body == {'entity': spec.slug, 'deleted': True}
    if spec.get_action is not None:
        remaining = slugs_of(session.cv_get(spec.get_action))
        assert remaining.count(spec.slug) == 0, f'[post-delete] {remaining!r}'
        in_n1 = slugs_of(session.cv_get(spec.get_action, niche=spec.niche_in))
        assert in_n1.count(spec.slug) == 0, (
            f'[post-delete niche] {spec.niche_in}: {in_n1!r}'
        )

    # 6. DELETE idempotente -> error de negocio EXACTO (4404 -> HTTP 404
    #    + error_code SLUG_NOT_FOUND; el code interno 4404 no viaja en el
    #    body HTTP, el controller lo mapea a status 404).
    entity_key = spec.action_suffix.replace('-', '_')
    rd2 = session.post(delete, {'slug': spec.slug})
    assert rd2.status == 404, f'[delete-idem] HTTP {rd2.status}: {rd2.body!r}'
    assert rd2.body == {
        'error_code': 'SLUG_NOT_FOUND',
        'message': f'{entity_key} con slug {spec.slug!r} no existe',
        'detail': {'entity': entity_key, 'slug': spec.slug},
    }

    return created_id
