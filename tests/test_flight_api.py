from flight_api import _session


def test_public_data_session_uses_provider_accepted_user_agent() -> None:
    assert _session.headers["User-Agent"] == "Mozilla/5.0 (compatible; PBB-Maintenance/1.0)"
