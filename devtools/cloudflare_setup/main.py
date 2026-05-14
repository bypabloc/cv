"""
Cloudflare Pages setup orchestrator for the portfolio monorepo.

Idempotent script: each phase checks current state before mutating, so it
can be re-run safely after partial failures.

Phases:
  - projects: create or update the 6 Pages projects
  - domains:  attach the apex + 5 subdomains to their projects
  - dns:      create CNAME records pointing each domain to its pages.dev URL
  - status:   print latest deployment status per project
  - all:      run projects -> domains -> dns -> status in order

Credentials are read from environment variables (loaded by run.py from
``tmp/cloudflare-creds.env`` when present):
  - CLOUDFLARE_API_TOKEN
  - ACCOUNT_ID
"""

from __future__ import annotations

import logging
import os
import sys
import time

from devtools.cloudflare_setup.api import CloudflareClient
from devtools.cloudflare_setup.api import CloudflareError
from devtools.cloudflare_setup.config import APEX_DOMAIN
from devtools.cloudflare_setup.config import APPS
from devtools.cloudflare_setup.config import AppConfig
from devtools.cloudflare_setup.payloads import build_create_project_payload
from devtools.cloudflare_setup.payloads import build_patch_project_payload


logger = logging.getLogger(__name__)


# ---- helpers --------------------------------------------------------------


def _ok(message: str) -> None:
    print(f'[OK]   {message}')


def _info(message: str) -> None:
    print(f'[INFO] {message}')


def _fail(message: str) -> None:
    print(f'[FAIL] {message}', file=sys.stderr)


def _load_credentials() -> tuple[str, str]:
    token = os.environ.get('CLOUDFLARE_API_TOKEN', '').strip()
    account_id = os.environ.get('ACCOUNT_ID', '').strip()
    if not token or not account_id:
        msg = (
            'Missing CLOUDFLARE_API_TOKEN or ACCOUNT_ID. '
            'Export them or fill tmp/cloudflare-creds.env.'
        )
        raise SystemExit(msg)
    return token, account_id


# ---- phases --------------------------------------------------------------


def phase_projects(client: CloudflareClient) -> None:
    """Create or update the 6 Pages projects."""
    for app in APPS:
        existing = client.get_project(app.project_name)
        if existing is None:
            payload = build_create_project_payload(app)
            client.create_project(payload)
            _ok(f'created project {app.project_name} (root_dir={app.root_dir})')
        else:
            patch = build_patch_project_payload(app)
            client.patch_project(app.project_name, patch)
            _ok(f'patched  project {app.project_name} (already existed)')


def phase_domains(client: CloudflareClient) -> None:
    """Attach each app's custom domain to its Pages project."""
    for app in APPS:
        existing_names = {
            d['name'] for d in client.list_domains(app.project_name)
        }
        if app.custom_domain in existing_names:
            _ok(
                f'domain {app.custom_domain} already attached to {app.project_name}'
            )
            continue
        client.attach_domain(app.project_name, app.custom_domain)
        _ok(f'attached {app.custom_domain} -> project {app.project_name}')


def phase_dns(client: CloudflareClient, zone_id: str) -> None:
    """
    Create or update CNAME records pointing each custom domain at the project's
    real ``pages.dev`` subdomain.

    Critical gotcha: Cloudflare appends a random suffix to the pages.dev
    subdomain when ``<project_name>.pages.dev`` is already taken at the global
    level (e.g. ``generic.pages.dev`` belongs to someone else, our project gets
    ``generic-3ab.pages.dev``). Pointing a CNAME at the unsuffixed URL returns
    HTTP 403 because the request lands on a stranger's project. We resolve the
    real subdomain from the project's API payload before touching DNS.

    Apex is handled with CNAME flattening (Cloudflare's automatic apex CNAME
    support). Cloudflare DNS treats a CNAME at the apex transparently as A/AAAA
    at the edge — works only inside Cloudflare DNS.
    """
    for app in APPS:
        project = client.get_project(app.project_name)
        if project is None:
            _fail(
                f'project {app.project_name} does not exist; run phase=projects first'
            )
            continue
        target = project.get('subdomain') or f'{app.project_name}.pages.dev'

        existing = client.list_dns_records(zone_id, name=app.custom_domain)
        if existing:
            record = existing[0]
            if (
                record.get('content') == target
                and record.get('type') == 'CNAME'
            ):
                _ok(
                    f'DNS for {app.custom_domain} already correct '
                    f'(CNAME -> {target})'
                )
                continue
            # PUT replaces the record in place (idempotent update).
            client._request(  # noqa: SLF001 - intentional access to thin helper
                'PUT',
                f'/zones/{zone_id}/dns_records/{record["id"]}',
                json={
                    'type': 'CNAME',
                    'name': app.custom_domain,
                    'content': target,
                    'proxied': True,
                    'ttl': 1,
                },
            )
            _ok(
                f'DNS CNAME {app.custom_domain} updated: '
                f'{record.get("content")} -> {target}'
            )
            continue
        client.create_dns_record(
            zone_id,
            record_type='CNAME',
            name=app.custom_domain,
            content=target,
            proxied=True,
        )
        _ok(f'DNS CNAME {app.custom_domain} -> {target}')


def phase_status(client: CloudflareClient) -> None:
    """Print the latest deployment status for each project."""
    for app in APPS:
        deployments = client.list_deployments(app.project_name, per_page=1)
        if not deployments:
            _info(f'{app.project_name:10} no deployments yet')
            continue
        latest = deployments[0]
        stage = latest.get('latest_stage') or {}
        url = latest.get('url') or '-'
        print(
            f'[INFO] {app.project_name:10} '
            f'stage={stage.get("name", "?"):10} '
            f'status={stage.get("status", "?"):10} '
            f'url={url}'
        )


def phase_trigger(client: CloudflareClient) -> None:
    """Trigger a fresh deploy for each project (does NOT push to GitHub)."""
    for app in APPS:
        try:
            result = client.trigger_deployment(app.project_name)
            _ok(
                f'triggered deploy for {app.project_name} (id={result.get("id", "?")[:8]})'
            )
        except CloudflareError as exc:
            _fail(f'{app.project_name}: {exc}')


# ---- entrypoint -----------------------------------------------------------


def main(flags: dict) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
    )

    token, account_id = _load_credentials()
    phase: str = flags.get('phase', 'all')

    with CloudflareClient(api_token=token, account_id=account_id) as client:
        # zone_id is only needed for the dns phase; resolve lazily.
        zone_id: str | None = None
        if phase in {'dns', 'all'}:
            zone_id = client.get_zone_id(APEX_DOMAIN)
            if not zone_id:
                _fail(f'zone {APEX_DOMAIN} not found in this account')
                return 2
            _info(f'zone {APEX_DOMAIN} -> {zone_id}')

        try:
            if phase in {'projects', 'all'}:
                phase_projects(client)
            if phase in {'domains', 'all'}:
                phase_domains(client)
            if phase in {'dns', 'all'}:
                assert zone_id is not None  # noqa: S101 - tipo enviado por la rama
                phase_dns(client, zone_id)
            if phase == 'trigger':
                phase_trigger(client)
            if phase in {'status', 'all'}:
                # Give Cloudflare a moment to register the first builds.
                if phase == 'all':
                    _info('waiting 5s for first deployments to register...')
                    time.sleep(5)
                phase_status(client)
        except CloudflareError as exc:
            _fail(str(exc))
            return 1

    return 0


def _validate_flags(argv: list[str]) -> dict:
    """Parse positional + --phase=<X>. Tiny on purpose."""
    flags: dict = {'phase': 'all'}
    for arg in argv:
        if arg.startswith('--phase='):
            flags['phase'] = arg.split('=', 1)[1]
        elif arg in {'projects', 'domains', 'dns', 'status', 'trigger', 'all'}:
            flags['phase'] = arg
    valid = {'projects', 'domains', 'dns', 'status', 'trigger', 'all'}
    if flags['phase'] not in valid:
        raise SystemExit(
            f'phase must be one of {sorted(valid)}, got {flags["phase"]!r}'
        )
    return flags


if __name__ == '__main__':
    sys.exit(main(_validate_flags(sys.argv[1:])))
