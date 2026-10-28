import httpx
import pytest

from app.services.elexon_client import (
    ElexonClient,
    ElexonConnectionError,
    ElexonError,
    ElexonHTTPError,
    ElexonRateLimitError,
    ElexonResponseError,
    ElexonTimeoutError,
)


def make_transport(handler):
    return httpx.MockTransport(handler)


def test_stream_returns_rows(monkeypatch):
    rows = [
        {
            "dataset": "WINDFOR",
            "publishTime": "2026-01-01T02:30:00Z",
            "startTime": "2026-01-01T00:00:00Z",
            "generation": 19960,
        },
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/datasets/WINDFOR/stream"
        assert request.url.params["publishDateTimeFrom"] == "2026-01-01T00:00Z"
        assert request.url.params["publishDateTimeTo"] == "2026-01-02T00:00Z"
        return httpx.Response(200, json=rows)

    with ElexonClient("http://127.0.0.1:9999", transport=make_transport(handler)) as client:
        result = client.get_dataset_stream(
            "WINDFOR",
            {"publishDateTimeFrom": "2026-01-01T00:00Z", "publishDateTimeTo": "2026-01-02T00:00Z"},
        )
    assert result == rows


def test_dataset_unwraps_envelope():
    payload = {"data": [{"dataset": "FUELHH", "generation": 13756}]}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/datasets/FUELHH"
        return httpx.Response(200, json=payload)

    with ElexonClient("http://127.0.0.1:9999", transport=make_transport(handler)) as client:
        result = client.get_dataset("FUELHH", {"settlementDateFrom": "2026-01-01"})
    assert result == payload["data"]


def test_server_error_raises_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    with ElexonClient("http://127.0.0.1:9999", transport=make_transport(handler)) as client:
        with pytest.raises(ElexonHTTPError) as exc_info:
            client.get_dataset_stream("WINDFOR", {})
    assert exc_info.value.status_code == 500
    assert exc_info.value.url == "http://127.0.0.1:9999/datasets/WINDFOR/stream"
    assert "Internal Server Error" in exc_info.value.body


def test_rate_limit_raises_rate_limit_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "60"}, text="Too Many Requests")

    with ElexonClient("http://127.0.0.1:9999", transport=make_transport(handler)) as client:
        with pytest.raises(ElexonRateLimitError) as exc_info:
            client.get_dataset_stream("WINDFOR", {})
    assert exc_info.value.retry_after == 60.0


def test_timeout_raises_timeout_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out", request=request)

    with ElexonClient("http://127.0.0.1:9999", transport=make_transport(handler)) as client:
        with pytest.raises(ElexonTimeoutError):
            client.get_dataset_stream("WINDFOR", {})


def test_connection_error_raises_connection_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with ElexonClient("http://127.0.0.1:9999", transport=make_transport(handler)) as client:
        with pytest.raises(ElexonConnectionError):
            client.get_dataset_stream("WINDFOR", {})


def test_invalid_json_raises_response_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, content=b"{not json", headers={"content-type": "application/json"}
        )

    with ElexonClient("http://127.0.0.1:9999", transport=make_transport(handler)) as client:
        with pytest.raises(ElexonResponseError):
            client.get_dataset_stream("WINDFOR", {})


def test_stream_non_list_raises_response_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"error": "bad"})

    with ElexonClient("http://127.0.0.1:9999", transport=make_transport(handler)) as client:
        with pytest.raises(ElexonResponseError):
            client.get_dataset_stream("WINDFOR", {})


def test_stream_row_not_object_raises_response_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[1, 2, 3])

    with ElexonClient("http://127.0.0.1:9999", transport=make_transport(handler)) as client:
        with pytest.raises(ElexonResponseError):
            client.get_dataset_stream("WINDFOR", {})


def test_invalid_dataset_code_raises_value_error():
    with ElexonClient("http://127.0.0.1:9999") as client:
        with pytest.raises(ValueError):
            client.get_dataset_stream("bad code", {})


def test_all_exceptions_inherit_from_elexon_error():
    assert issubclass(ElexonConnectionError, ElexonError)
    assert issubclass(ElexonTimeoutError, ElexonError)
    assert issubclass(ElexonHTTPError, ElexonError)
    assert issubclass(ElexonRateLimitError, ElexonError)
    assert issubclass(ElexonResponseError, ElexonError)
