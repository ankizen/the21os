"""Secret redaction for anything headed into the audit log or logs — see
master prompt SS20: never log access tokens, app secrets, service-account
keys, passwords, or session cookies."""

import re

_SECRET_KEY_PATTERN = re.compile(
    r"(token|secret|password|passwd|api_key|apikey|authorization|cookie|totp|private_key)",
    re.IGNORECASE,
)
REDACTED = "***REDACTED***"


def redact(value: object) -> object:
    """Recursively redact dict values whose key looks secret-shaped."""
    if isinstance(value, dict):
        return {k: (REDACTED if _SECRET_KEY_PATTERN.search(str(k)) else redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value
