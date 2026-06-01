"""
client.py
---------
Low-level Binance Futures Testnet API wrapper.
Handles authentication (HMAC SHA-256 signing), request execution,
and HTTP/API error handling. No business logic lives here.
"""

import hashlib
import hmac
import logging
import time
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)

TESTNET_BASE_URL = "https://testnet.binancefuture.com"


class BinanceClientError(Exception):
    """
    Raised when the Binance API returns an error response,
    or when a network-level failure occurs.
    """

    def __init__(self, message: str, code: int = None, raw: dict = None):
        super().__init__(message)
        self.code = code
        self.raw = raw or {}

    def __str__(self):
        if self.code:
            return f"[Code {self.code}] {super().__str__()}"
        return super().__str__()


class BinanceClient:
    """
    Authenticated Binance Futures Testnet REST client.

    Responsibilities:
      - Sign requests with HMAC SHA-256
      - Send HTTP requests with retry-friendly timeout
      - Parse and raise errors from API responses
      - Log every request and response to the log file
    """

    def __init__(self, api_key: str, api_secret: str):
        if not api_key:
            raise ValueError("BINANCE_API_KEY is missing or empty.")
        if not api_secret:
            raise ValueError("BINANCE_API_SECRET is missing or empty.")

        self.api_key = api_key
        self.api_secret = api_secret

        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": self.api_key,
            "Accept": "application/json",
        })

        logger.info("BinanceClient initialized (Testnet)")

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _sign(self, params: Dict) -> Dict:
        """
        Attach a timestamp and HMAC-SHA256 signature to the params dict.
        The signature covers all other params including timestamp.
        """
        params["timestamp"] = int(time.time() * 1000)
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _safe_params(self, params: Dict) -> Dict:
        """Return params dict without the signature (safe to log)."""
        return {k: v for k, v in params.items() if k != "signature"}

    def _request(
        self, method: str, endpoint: str, params: Dict
    ) -> Dict[str, Any]:
        """
        Sign and execute an HTTP request to the testnet.

        Args:
            method:   HTTP verb, e.g. 'POST', 'GET'
            endpoint: API path, e.g. '/fapi/v1/order'
            params:   Query parameters (will be signed in-place)

        Returns:
            Parsed JSON response as a dict.

        Raises:
            BinanceClientError: on API errors or network failures.
        """
        signed_params = self._sign(params)
        url = f"{TESTNET_BASE_URL}{endpoint}"

        logger.info(
            f"→ Request  | {method.upper()} {endpoint} "
            f"| Params: {self._safe_params(signed_params)}"
        )

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=signed_params,
                timeout=15,
            )
            data = response.json()

        except requests.exceptions.ConnectionError as exc:
            msg = "Cannot reach Binance Testnet. Check your internet connection."
            logger.error(f"Network error: {exc}")
            raise BinanceClientError(msg) from exc

        except requests.exceptions.Timeout as exc:
            msg = "Request timed out (15 s). Please try again."
            logger.error(f"Timeout: {exc}")
            raise BinanceClientError(msg) from exc

        except requests.exceptions.RequestException as exc:
            msg = f"Unexpected network error: {exc}"
            logger.error(msg)
            raise BinanceClientError(msg) from exc

        except ValueError as exc:
            msg = "Received non-JSON response from server."
            logger.error(f"{msg} Raw: {response.text[:300]}")
            raise BinanceClientError(msg) from exc

        # Handle Binance API-level errors (HTTP 4xx/5xx with JSON body)
        if not response.ok:
            code = data.get("code", response.status_code)
            api_msg = data.get("msg", "Unknown API error")
            logger.error(
                f"← API Error | HTTP {response.status_code} "
                f"| Code: {code} | Message: {api_msg}"
            )
            raise BinanceClientError(api_msg, code=code, raw=data)

        logger.info(f"← Response | {data}")
        return data

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def place_order(self, **kwargs) -> Dict[str, Any]:
        """
        Place a futures order on the testnet.

        All kwargs are forwarded as query parameters to POST /fapi/v1/order.
        Expected keys: symbol, side, type, quantity, and optionally price,
        timeInForce.
        """
        return self._request("POST", "/fapi/v1/order", kwargs)
