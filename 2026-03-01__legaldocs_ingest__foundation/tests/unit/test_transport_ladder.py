"""Tests for transport ladder, reason codes, and fetch_browser integration."""

from legal_ingest.reason_codes import ReasonCode
from legal_ingest.fetch import (
    is_eurlex_waf_challenge,
    _make_attempt,
    BROWSER_FALLBACK_ERRORS,
    EurlexWafChallengeError,
)


class TestReasonCodes:
    """Tests for ReasonCode classification."""

    def test_classify_waf(self):
        assert ReasonCode.classify_error("EURLEX_WAF_CHALLENGE: bla") == ReasonCode.EURLEX_WAF_CHALLENGE

    def test_classify_timeout(self):
        assert ReasonCode.classify_error("timed out waiting") == ReasonCode.EXTERNAL_TIMEOUT

    def test_classify_malformed(self):
        assert ReasonCode.classify_error("illegal header line") == ReasonCode.EXTERNAL_MALFORMED_HEADERS

    def test_classify_disconnect(self):
        assert ReasonCode.classify_error("Server disconnected") == ReasonCode.EXTERNAL_DISCONNECT

    def test_classify_ssl(self):
        assert ReasonCode.classify_error("SSL handshake failed") == ReasonCode.EXTERNAL_SSL_ERROR

    def test_classify_unknown(self):
        assert ReasonCode.classify_error("something weird") == ReasonCode.UNKNOWN_ERROR


class TestTransportLadder:
    """Tests for transport ladder logic."""

    def test_make_attempt_structure(self):
        """_make_attempt returns correct dict structure."""
        a = _make_attempt(
            source_id="s25", attempt_no=1, method="direct_httpx",
            status_code=200, nbytes=1000, reason_code="OK",
            duration_ms=150, final_outcome="OK"
        )
        assert a["source_id"] == "s25"
        assert a["attempt_no"] == 1
        assert a["method"] == "direct_httpx"
        assert a["bytes"] == 1000
        assert a["final_outcome"] == "OK"

    def test_browser_fallback_errors_includes_waf(self):
        """EurlexWafChallengeError is in BROWSER_FALLBACK_ERRORS."""
        assert EurlexWafChallengeError in BROWSER_FALLBACK_ERRORS

    def test_waf_detection_triggers_fallback(self):
        """EUR-Lex WAF challenge should trigger browser fallback."""
        assert is_eurlex_waf_challenge(
            "https://eur-lex.europa.eu/test", 200, b""
        ) is True


class TestFallbackPolicy:
    """Tests for when browser fallback should/shouldn't trigger."""

    def test_non_eurlex_domain_no_fallback(self):
        """Non-EUR-Lex domains should not trigger WAF detection."""
        assert is_eurlex_waf_challenge(
            "https://example.com/page", 200, b""
        ) is False

    def test_eurlex_with_content_no_fallback(self):
        """EUR-Lex with real content should not trigger WAF."""
        assert is_eurlex_waf_challenge(
            "https://eur-lex.europa.eu/test", 200, b"x" * 10000
        ) is False

    def test_saos_no_fallback(self):
        """SAOS domains should not trigger EUR-Lex WAF detection."""
        assert is_eurlex_waf_challenge(
            "https://www.saos.org.pl/api/judgments/123", 200, b""
        ) is False
