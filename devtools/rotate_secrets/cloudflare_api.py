"""Thin Cloudflare Turnstile API client.

Scope minimo:
  - list widgets
  - get widget (incluye secret)
  - create widget
  - rotate widget secret

Synchronous httpx client (3-6 calls por ejecucion).
"""

from __future__ import annotations

from typing import Any

import httpx


CF_API = 'https://api.cloudflare.com/client/v4'


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


class TurnstileClient:
    """Synchronous Cloudflare Turnstile API client."""

    def __init__(self, *, api_token: str, account_id: str) -> None:
        self.account_id = account_id
        self._http = httpx.Client(
            base_url=CF_API,
            headers={
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json',
            },
            timeout=30.0,
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> TurnstileClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> Any:
        response = self._http.request(method, path, json=json)
        try:
            envelope = response.json()
        except ValueError as exc:
            raise CloudflareError(
                f'{method} {path} -> non-JSON (HTTP {response.status_code})',
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

    def list_widgets(self) -> list[dict[str, Any]]:
        path = f'/accounts/{self.account_id}/challenges/widgets?per_page=50'
        return self._request('GET', path) or []

    def get_widget(self, sitekey: str) -> dict[str, Any]:
        path = f'/accounts/{self.account_id}/challenges/widgets/{sitekey}'
        return self._request('GET', path)

    def create_widget(
        self,
        *,
        name: str,
        domains: list[str],
        mode: str = 'managed',
    ) -> dict[str, Any]:
        path = f'/accounts/{self.account_id}/challenges/widgets'
        body = {
            'name': name,
            'domains': domains,
            'mode': mode,
            'bot_fight_mode': False,
            'region': 'world',
            'clearance_level': 'no_clearance',
            'offlabel': False,
        }
        return self._request('POST', path, json=body)

    def rotate_secret(self, sitekey: str) -> dict[str, Any]:
        path = (
            f'/accounts/{self.account_id}/challenges/widgets/'
            f'{sitekey}/rotate_secret'
        )
        return self._request(
            'POST',
            path,
            json={'invalidate_immediately': True},
        )
