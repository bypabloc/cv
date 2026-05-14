"""
Thin httpx-backed client for the Cloudflare REST API v4.

Scope:
  - Pages projects (create / get / delete / list)
  - Pages custom domains (attach)
  - Pages deployments (trigger / get latest)
  - DNS records (create / list)

The client is intentionally narrow — it only covers the endpoints the
setup script needs. Each method returns the parsed `result` field of the
Cloudflare envelope and raises CloudflareError on `success: false`.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx


logger = logging.getLogger(__name__)

API_BASE = 'https://api.cloudflare.com/client/v4'


class CloudflareError(RuntimeError):
    """Raised when the Cloudflare API returns success=false or HTTP >=400."""

    def __init__(
        self,
        message: str,
        *,
        errors: list[dict[str, Any]] | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.errors = errors or []
        self.status_code = status_code


class CloudflareClient:
    """
    Synchronous Cloudflare API client.

    Synchronous on purpose: the setup script does six operations sequentially,
    and rate-limit headroom matters more than the ~1s saved by parallelizing
    six requests.
    """

    def __init__(self, *, api_token: str, account_id: str) -> None:
        self._api_token = api_token
        self.account_id = account_id
        self._http = httpx.Client(
            base_url=API_BASE,
            headers={
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json',
            },
            timeout=30.0,
        )

    # ---- lifecycle -----------------------------------------------------

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> CloudflareClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    # ---- low-level -----------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        allow_404: bool = False,
    ) -> Any:
        """Send a request, unwrap envelope, raise on failure."""
        response = self._http.request(method, path, json=json)
        if allow_404 and response.status_code == httpx.codes.NOT_FOUND:
            return None
        try:
            envelope = response.json()
        except ValueError as exc:
            raise CloudflareError(
                f'{method} {path} -> non-JSON response (HTTP {response.status_code})',
                status_code=response.status_code,
            ) from exc

        if not envelope.get('success', False):
            errors = envelope.get('errors') or []
            raise CloudflareError(
                f'{method} {path} -> {errors}',
                errors=errors,
                status_code=response.status_code,
            )
        return envelope.get('result')

    # ---- Pages projects -------------------------------------------------

    def get_project(self, name: str) -> dict[str, Any] | None:
        """Return the project or None if it does not exist."""
        return self._request(
            'GET',
            f'/accounts/{self.account_id}/pages/projects/{name}',
            allow_404=True,
        )

    def create_project(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a new Pages project. Idempotent guard is on the caller."""
        return self._request(
            'POST',
            f'/accounts/{self.account_id}/pages/projects',
            json=payload,
        )

    def patch_project(
        self, name: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing Pages project (build_config, env_vars, etc.)."""
        return self._request(
            'PATCH',
            f'/accounts/{self.account_id}/pages/projects/{name}',
            json=payload,
        )

    def delete_project(self, name: str) -> None:
        self._request(
            'DELETE', f'/accounts/{self.account_id}/pages/projects/{name}'
        )

    # ---- Pages domains --------------------------------------------------

    def list_domains(self, project_name: str) -> list[dict[str, Any]]:
        return (
            self._request(
                'GET',
                f'/accounts/{self.account_id}/pages/projects/{project_name}/domains',
            )
            or []
        )

    def attach_domain(self, project_name: str, domain: str) -> dict[str, Any]:
        return self._request(
            'POST',
            f'/accounts/{self.account_id}/pages/projects/{project_name}/domains',
            json={'name': domain},
        )

    # ---- Pages deployments ----------------------------------------------

    def list_deployments(
        self,
        project_name: str,
        *,
        per_page: int = 5,
    ) -> list[dict[str, Any]]:
        return (
            self._request(
                'GET',
                f'/accounts/{self.account_id}/pages/projects/{project_name}/deployments?per_page={per_page}',
            )
            or []
        )

    def trigger_deployment(self, project_name: str) -> dict[str, Any]:
        return self._request(
            'POST',
            f'/accounts/{self.account_id}/pages/projects/{project_name}/deployments',
        )

    # ---- DNS records ----------------------------------------------------

    def list_dns_records(
        self,
        zone_id: str,
        *,
        name: str | None = None,
    ) -> list[dict[str, Any]]:
        path = f'/zones/{zone_id}/dns_records'
        if name:
            path += f'?name={name}'
        return self._request('GET', path) or []

    def create_dns_record(
        self,
        zone_id: str,
        *,
        record_type: str,
        name: str,
        content: str,
        proxied: bool = True,
        ttl: int = 1,  # 1 = "auto" when proxied
    ) -> dict[str, Any]:
        return self._request(
            'POST',
            f'/zones/{zone_id}/dns_records',
            json={
                'type': record_type,
                'name': name,
                'content': content,
                'proxied': proxied,
                'ttl': ttl,
            },
        )

    # ---- Zones ---------------------------------------------------------

    def get_zone_id(self, zone_name: str) -> str | None:
        """Resolve a zone name to its zone_id, or None if not found."""
        result = self._request('GET', f'/zones?name={zone_name}')
        if not result:
            return None
        return result[0]['id']
