"""Tests for restricted-content char threshold logic (default + per-source override)."""
from legal_ingest.config import SourceConfig


def test_default_min_chars_override_is_none():
    """SourceConfig.min_chars_override defaults to None (use global 500)."""
    src = SourceConfig(
        source_id="test",
        url="https://example.com",
        fetch_strategy="direct",
        doc_type_hint="STATUTE",
        jurisdiction="PL",
        language="pl",
    )
    assert src.min_chars_override is None


def test_min_chars_override_accepted():
    """SourceConfig accepts an explicit min_chars_override value."""
    src = SourceConfig(
        source_id="test",
        url="https://example.com",
        fetch_strategy="direct",
        doc_type_hint="STATUTE_REF",
        jurisdiction="PL",
        language="pl",
        min_chars_override=200,
    )
    assert src.min_chars_override == 200


def test_threshold_logic_default():
    """Without override, threshold should be the global default (500)."""
    src = SourceConfig(
        source_id="test",
        url="https://example.com",
        fetch_strategy="direct",
        doc_type_hint="STATUTE",
        jurisdiction="PL",
        language="pl",
    )
    min_chars = src.min_chars_override if src.min_chars_override is not None else 500
    assert min_chars == 500


def test_threshold_logic_override():
    """With override=200, threshold should be 200."""
    src = SourceConfig(
        source_id="test_lex",
        url="https://example.com",
        fetch_strategy="direct",
        doc_type_hint="STATUTE_REF",
        jurisdiction="PL",
        language="pl",
        min_chars_override=200,
    )
    min_chars = src.min_chars_override if src.min_chars_override is not None else 500
    assert min_chars == 200


def test_threshold_logic_override_zero():
    """Override=0 disables the restricted check entirely."""
    src = SourceConfig(
        source_id="test_zero",
        url="https://example.com",
        fetch_strategy="direct",
        doc_type_hint="GUIDANCE",
        jurisdiction="EU",
        language="en",
        min_chars_override=0,
    )
    min_chars = src.min_chars_override if src.min_chars_override is not None else 500
    assert min_chars == 0
    # With min_chars=0, total_chars can never be < 0 → never RESTRICTED
    total_chars = 10
    assert not (total_chars < min_chars)
