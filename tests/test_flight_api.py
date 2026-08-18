import pytest
import requests

from flight_api import FlightApiResponseError, JsonObject, _fetch_pages, _session


def test_public_data_session_uses_provider_accepted_user_agent() -> None:
    assert _session.headers["User-Agent"] == "Mozilla/5.0 (compatible; PBB-Maintenance/1.0)"


class _FakeResponse:
    def __init__(self, data: JsonObject, status_code: int = 200) -> None:
        self._data = data
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"HTTP {self.status_code}")

    def json(self) -> JsonObject:
        return self._data


def test_provider_error_is_not_reported_as_zero_results(monkeypatch: pytest.MonkeyPatch) -> None:
    error_response = _FakeResponse(
        {
            "OpenAPI_ServiceResponse": {
                "cmmMsgHeader": {
                    "returnReasonCode": "30",
                    "returnAuthMsg": "SERVICE_KEY_IS_NOT_REGISTERED_ERROR",
                    "errMsg": "SERVICE ERROR",
                }
            }
        },
        status_code=403,
    )
    monkeypatch.setattr(_session, "get", lambda *args, **kwargs: error_response)

    with pytest.raises(FlightApiResponseError) as caught:
        _fetch_pages("getFltArrivalsDeOdp", "20260818")

    assert caught.value.code == "30"
    assert "SERVICE_KEY_IS_NOT_REGISTERED_ERROR" in str(caught.value)


def test_request_retries_once_when_first_attempt_times_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    successful_response = _FakeResponse(
        {
            "response": {
                "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
                "body": {"totalCount": 0, "items": []},
            }
        }
    )
    call_count = 0

    def get_with_first_attempt_timeout(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise requests.exceptions.ReadTimeout()
        return successful_response

    monkeypatch.setattr(_session, "get", get_with_first_attempt_timeout)

    # When
    result = _fetch_pages("getFltArrivalsDeOdp", "20260818")

    # Then
    assert result == []
    assert call_count == 2
