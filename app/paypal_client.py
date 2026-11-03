import time
import uuid

import httpx

from .config import settings

BASE_URL = "https://api-m.sandbox.paypal.com"  # sandbox only, on purpose


class PayPalError(Exception):
    def __init__(self, status_code: int, body: str):
        super().__init__(f"PayPal returned {status_code}: {body}")
        self.status_code = status_code
        self.body = body


class PayPalClient:
    def __init__(self) -> None:
        self._http = httpx.Client(base_url=BASE_URL, timeout=30)
        self._token: str | None = None
        self._expires_at = 0.0

    def _get_token(self, force: bool = False) -> str:
        if not force and self._token and time.monotonic() < self._expires_at - 60:
            return self._token
        response = self._http.post(
            "/v1/oauth2/token",
            auth=(settings.paypal_client_id, settings.paypal_client_secret),
            data={"grant_type": "client_credentials"},
        )
        if response.status_code >= 400:
            raise PayPalError(response.status_code, response.text)
        body = response.json()
        self._token = body["access_token"]
        self._expires_at = time.monotonic() + body["expires_in"]
        return self._token

    def request(self, method: str, path: str, *, json: dict | None = None,
                request_id: str | None = None) -> dict:
        for attempt in (1, 2):
            headers = {"Authorization": f"Bearer {self._get_token(force=attempt == 2)}"}
            if method.upper() != "GET":
                headers["PayPal-Request-Id"] = request_id or str(uuid.uuid4())
            response = self._http.request(method, path, headers=headers, json=json)
            if response.status_code == 401 and attempt == 1:
                continue  # token may have expired: fetch a fresh one and retry once
            break
        if response.status_code >= 400:
            raise PayPalError(response.status_code, response.text)
        return response.json() if response.content else {}