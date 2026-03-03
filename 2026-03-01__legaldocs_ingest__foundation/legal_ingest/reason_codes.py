"""Canonical reason codes for source fetch outcomes.

Every not-OK status in source_status.json must use one of these codes.
"""


class ReasonCode:
    """Machine-readable reason codes for fetch outcomes."""

    # Success
    OK = "OK"

    # EUR-Lex WAF
    EURLEX_WAF_CHALLENGE = "EURLEX_WAF_CHALLENGE"

    # SAOS
    SAOS_MAINTENANCE = "SAOS_MAINTENANCE"

    # Network / transport
    EXTERNAL_TIMEOUT = "EXTERNAL_TIMEOUT"
    EXTERNAL_MALFORMED_HEADERS = "EXTERNAL_MALFORMED_HEADERS"
    EXTERNAL_DISCONNECT = "EXTERNAL_DISCONNECT"
    EXTERNAL_SSL_ERROR = "EXTERNAL_SSL_ERROR"

    # Content
    RESTRICTED_LOW_CHARS = "RESTRICTED_LOW_CHARS"
    ACCESS_DENIED_PAGE = "ACCESS_DENIED_PAGE"

    # Pipeline
    NOT_PROCESSED = "NOT_PROCESSED"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"

    @classmethod
    def classify_error(cls, error_msg: str) -> str:
        """Classify an error message into a reason code."""
        msg = error_msg.lower()
        if "eurlex_waf_challenge" in msg:
            return cls.EURLEX_WAF_CHALLENGE
        if "saos maintenance" in msg or "przerwa techniczna" in msg:
            return cls.SAOS_MAINTENANCE
        if "timed out" in msg or "timeout" in msg:
            return cls.EXTERNAL_TIMEOUT
        if "illegal header" in msg or "malformed" in msg:
            return cls.EXTERNAL_MALFORMED_HEADERS
        if "disconnected" in msg:
            return cls.EXTERNAL_DISCONNECT
        if "ssl" in msg:
            return cls.EXTERNAL_SSL_ERROR
        if "access denied" in msg or "403" in msg:
            return cls.ACCESS_DENIED_PAGE
        return cls.UNKNOWN_ERROR
