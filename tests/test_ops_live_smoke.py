from app.ops.live_smoke import _AttemptTracker, _is_transient


class MockError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


def test_attempt_tracker_initializes_and_increments():
    tracker = _AttemptTracker()
    assert tracker.count == 0
    tracker.count += 1
    assert tracker.count == 1


def test_is_transient_identifies_llm_api_errors():
    error_429 = MockError("Rate Limit", 429)
    assert _is_transient(error_429) is True

    error_503 = MockError("Service Unavailable", 503)
    assert _is_transient(error_503) is True

    error_400 = MockError("Bad Request", 400)
    assert _is_transient(error_400) is False


def test_is_transient_identifies_network_exceptions():
    assert _is_transient(RuntimeError("Connection refused")) is True
    assert _is_transient(TimeoutError("Operation Timeout")) is True
    assert _is_transient(ValueError("Bad Logic")) is False
