from typing import Any

import httpx


class ElexonError(Exception):
    """Base class for all Elexon client errors."""


class ElexonConnectionError(ElexonError):
    """A network connection to Elexon could not be established."""


class ElexonTimeoutError(ElexonError):
    """The Elexon request timed out."""


class ElexonHTTPError(ElexonError):
    """Elexon returned an unsuccessful HTTP status code."""

    def __init__(self, message: str, status_code: int, url: str, body: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.url = url
        self.body = body


class ElexonRateLimitError(ElexonError):
    """Elexon rate-limited the request (HTTP 429)."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class ElexonResponseError(ElexonError):
    """Elexon returned a response that could not be parsed as expected."""


class ElexonClient:
    """Thin synchronous client over the Elexon BMRS API v1.

    The client does not retry failed requests. Callers decide how to handle
    each exception type (for example, backing off on ``ElexonRateLimitError``).
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._transport = transport
        self._client: httpx.Client | None = None

    def __enter__(self) -> "ElexonClient":
        self._client = httpx.Client(timeout=self.timeout, transport=self._transport)
        return self

    def __exit__(self, *_: object) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            raise RuntimeError("ElexonClient must be used as a context manager")
        return self._client

    @staticmethod
    def _validate_dataset_code(dataset: str) -> None:
        if not dataset or not all(c.isalnum() or c == "_" for c in dataset):
            raise ValueError(f"invalid Elexon dataset code: {dataset!r}")

    @staticmethod
    def _first_text(text: str) -> str:
        return text.strip().splitlines()[0].strip() if text.strip() else ""

    def _handle_http_error(self, exc: httpx.HTTPStatusError) -> None:
        body = self._first_text(exc.response.text)
        status = exc.response.status_code
        if status == 429:
            retry_after: float | None = None
            raw = exc.response.headers.get("Retry-After")
            if raw:
                try:
                    retry_after = float(raw)
                except ValueError:
                    retry_after = None
            raise ElexonRateLimitError(
                f"Elexon rate-limited request to {exc.request.url} (HTTP {status})",
                retry_after,
            ) from exc
        raise ElexonHTTPError(
            f"Elexon request failed for {exc.request.url} (HTTP {status}): {body}",
            status,
            str(exc.request.url),
            body,
        ) from exc

    def _parse_dataset_response(
        self, payload: Any, envelope_expected: bool
    ) -> list[dict[str, Any]]:
        if not isinstance(payload, list) and not isinstance(payload, dict):
            raise ElexonResponseError(
                f"Elexon response must be a JSON object or array, got {type(payload).__name__}"
            )

        if envelope_expected:
            if not isinstance(payload, dict):
                raise ElexonResponseError(
                    "Elexon dataset endpoint must return a JSON object, "
                    f"got {type(payload).__name__}"
                )
            data = payload.get("data")
            if data is None:
                raise ElexonResponseError("Elexon dataset response is missing the 'data' field")
            if not isinstance(data, list):
                raise ElexonResponseError(
                    f"Elexon dataset 'data' field must be an array, got {type(data).__name__}"
                )
        else:
            data = payload

        rows: list[dict[str, Any]] = []
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                raise ElexonResponseError(
                    f"Elexon dataset row {index} must be an object, got {type(item).__name__}"
                )
            rows.append(item)
        return rows

    def get_dataset(
        self, dataset: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Fetch a standard dataset endpoint returning ``{"data": [...]}``."""
        self._validate_dataset_code(dataset)
        url = f"{self.base_url}/datasets/{dataset}"
        try:
            response = self.client.get(url, params=params)
        except httpx.ConnectError as exc:
            raise ElexonConnectionError(f"could not connect to Elexon at {url}") from exc
        except httpx.TimeoutException as exc:
            raise ElexonTimeoutError(f"timed out connecting to Elexon at {url}") from exc
        except httpx.RequestError as exc:
            raise ElexonConnectionError(f"request to Elexon failed: {exc}") from exc

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc)
            raise  # unreachable

        try:
            payload = response.json()
        except ValueError as exc:
            raise ElexonResponseError(f"Elexon response for {url} was not valid JSON") from exc

        return self._parse_dataset_response(payload, envelope_expected=True)

    def get_dataset_stream(
        self, dataset: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Fetch an optimised stream endpoint returning a bare JSON array."""
        self._validate_dataset_code(dataset)
        url = f"{self.base_url}/datasets/{dataset}/stream"
        try:
            response = self.client.get(url, params=params)
        except httpx.ConnectError as exc:
            raise ElexonConnectionError(f"could not connect to Elexon at {url}") from exc
        except httpx.TimeoutException as exc:
            raise ElexonTimeoutError(f"timed out connecting to Elexon at {url}") from exc
        except httpx.RequestError as exc:
            raise ElexonConnectionError(f"request to Elexon failed: {exc}") from exc

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc)
            raise  # unreachable

        try:
            payload = response.json()
        except ValueError as exc:
            raise ElexonResponseError(
                f"Elexon stream response for {url} was not valid JSON"
            ) from exc

        return self._parse_dataset_response(payload, envelope_expected=False)
