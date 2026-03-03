"""Tests for EUR-Lex WAF challenge detection and EurlexWafChallengeError."""
from legal_ingest.fetch import (
    is_eurlex_waf_challenge,
    EurlexWafChallengeError,
    EURLEX_DOMAINS,
)


def test_eurlex_waf_zero_bytes():
    """EUR-Lex returning HTTP 200 with 0 bytes is WAF challenge."""
    assert is_eurlex_waf_challenge(
        "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62011CJ0415",
        200,
        b"",
    ) is True


def test_eurlex_waf_not_eurlex_domain():
    """Non-EUR-Lex domain should not be detected as WAF."""
    assert is_eurlex_waf_challenge(
        "https://example.com/page",
        200,
        b"",
    ) is False


def test_eurlex_waf_normal_content():
    """EUR-Lex with normal content should not be WAF."""
    assert is_eurlex_waf_challenge(
        "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62011CJ0415",
        200,
        b"<html><body>" + b"x" * 10000 + b"</body></html>",
    ) is False


def test_eurlex_waf_403_status():
    """EUR-Lex returning HTTP 403 with 0 bytes is WAF."""
    assert is_eurlex_waf_challenge(
        "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=test",
        403,
        b"",
    ) is True


def test_eurlex_waf_202_status():
    """EUR-Lex returning HTTP 202 with 0 bytes is WAF."""
    assert is_eurlex_waf_challenge(
        "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=test",
        202,
        b"",
    ) is True


def test_eurlex_waf_captcha_page():
    """EUR-Lex returning small captcha page is WAF."""
    assert is_eurlex_waf_challenge(
        "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=test",
        200,
        b"<html><body>AWSWAF captcha required</body></html>",
    ) is True


def test_eurlex_waf_error_attributes():
    """EurlexWafChallengeError stores URL, status code, and content length."""
    err = EurlexWafChallengeError(
        url="https://eur-lex.europa.eu/test",
        status_code=200,
        content_len=0,
    )
    assert "EURLEX_WAF_CHALLENGE" in str(err)
    assert err.url == "https://eur-lex.europa.eu/test"
    assert err.status_code == 200
    assert err.content_len == 0


def test_eurlex_domains_constant():
    """Sanity check that EURLEX_DOMAINS is not empty."""
    assert len(EURLEX_DOMAINS) > 0
    assert "eur-lex.europa.eu" in EURLEX_DOMAINS
