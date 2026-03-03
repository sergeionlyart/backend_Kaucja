"""Tests for SAOS maintenance page detection and SaosMaintenanceError."""
from legal_ingest.fetch import (
    is_saos_maintenance,
    SaosMaintenanceError,
    SAOS_MAINTENANCE_SIGNATURES,
)


# Real maintenance page excerpt from SAOS (1230 bytes, captured during downtime)
MAINTENANCE_HTML = (
    b'<!DOCTYPE html>\n<html>\n\n<head>\n'
    b'    <title>Przerwa techniczna</title>\n'
    b'    <meta charset="UTF-8" />\n'
    b'</head>\n\n<body style="font-family: Arial;">\n'
    b'<div>System SAOS jest chwilowo niedostepny</div>\n'
    b'</body>\n</html>'
)

REAL_JUDGMENT_HTML = b"<html><body>" + b"x" * 10000 + b"</body></html>"


def test_is_saos_maintenance_detects_real_page():
    """Real maintenance page should be detected."""
    assert is_saos_maintenance(MAINTENANCE_HTML) is True


def test_is_saos_maintenance_rejects_real_content():
    """Large real content should not be flagged as maintenance."""
    assert is_saos_maintenance(REAL_JUDGMENT_HTML) is False


def test_is_saos_maintenance_rejects_empty():
    """Empty bytes should not be maintenance."""
    assert is_saos_maintenance(b"") is False


def test_is_saos_maintenance_size_guard():
    """Content > 5000 bytes is never maintenance even if it contains the keyword."""
    big_content = b"Przerwa techniczna " + b"x" * 10000
    assert is_saos_maintenance(big_content) is False


def test_saos_maintenance_error_message():
    """SaosMaintenanceError contains source_id and bytes info."""
    err = SaosMaintenanceError(source_id="s12_saos_171957", bytes_len=1230)
    assert "s12_saos_171957" in str(err)
    assert "1230" in str(err)
    assert "Przerwa techniczna" in str(err)
    assert err.source_id == "s12_saos_171957"
    assert err.bytes_len == 1230


def test_maintenance_signatures_are_bytes():
    """All signatures must be bytes for comparison with raw content."""
    for sig in SAOS_MAINTENANCE_SIGNATURES:
        assert isinstance(sig, bytes)
