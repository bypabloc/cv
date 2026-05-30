"""Cliente HTTP con timing para el harness api_e2e.

`HttpClient` envuelve httpx: arma el shape correcto del request (GET con
query params; POST con `operation`/`action` + campos FLAT en el body),
inyecta una IP rotada + headers, mide el tiempo y devuelve un `Response`
con `(status, body, elapsed)`.
"""

from __future__ import annotations

import json
import time
from typing import Any

from config import IpRotator
import httpx


class Response:
    """Resultado de una llamada HTTP: status, body parseado y elapsed (s)."""

    def __init__(self, status: int, body: Any, elapsed: float) -> None:
        self.status = status
        self.body = body
        self.elapsed = elapsed


class HttpClient:
    """Cliente httpx para el API Gateway del backend (1 IP por request)."""

    def __init__(self, *, base_url: str, timeout: float = 35.0) -> None:
        self._base = base_url.rstrip('/')
        self._client = httpx.Client(timeout=timeout)
        self._ips = IpRotator()

    def close(self) -> None:
        """Cierra el cliente httpx."""
        self._client.close()

    def _headers(
        self,
        *,
        origin: str,
        bypass_secret: str | None,
        bearer: str | None,
    ) -> dict[str, str]:
        headers = {
            'Origin': origin,
            'CF-Connecting-IP': self._ips.next(),
            'CF-IPCountry': 'CL',
            'User-Agent': 'portfolio-api-e2e/1.0',
            'Content-Type': 'application/json',
        }
        if bypass_secret:
            headers['X-Turnstile-Bypass-Secret'] = bypass_secret
        if bearer:
            headers['Authorization'] = f'Bearer {bearer}'
        return headers

    def get(
        self,
        path: str,
        *,
        params: dict[str, str],
        origin: str,
    ) -> Response:
        """GET con query params (operation/action van en params)."""
        headers = self._headers(
            origin=origin,
            bypass_secret=None,
            bearer=None,
        )
        start = time.monotonic()
        resp = self._client.get(
            f'{self._base}{path}',
            params=params,
            headers=headers,
        )
        elapsed = time.monotonic() - start
        return Response(resp.status_code, _parse(resp), elapsed)

    def post(
        self,
        path: str,
        *,
        body: dict[str, Any],
        origin: str,
        bypass_secret: str | None = None,
        bearer: str | None = None,
    ) -> Response:
        """POST con body JSON (operation/action + campos FLAT en el body)."""
        headers = self._headers(
            origin=origin,
            bypass_secret=bypass_secret,
            bearer=bearer,
        )
        start = time.monotonic()
        resp = self._client.post(
            f'{self._base}{path}',
            content=json.dumps(body),
            headers=headers,
        )
        elapsed = time.monotonic() - start
        return Response(resp.status_code, _parse(resp), elapsed)


def _parse(resp: httpx.Response) -> Any:
    """Parsea el body como JSON; si no es JSON devuelve el texto crudo."""
    try:
        return resp.json()
    except (json.JSONDecodeError, ValueError):
        return resp.text
