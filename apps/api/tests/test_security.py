from the21secrets.auth.security import (
    create_session_token,
    generate_totp_secret,
    hash_password,
    read_session_token,
    verify_password,
    verify_totp,
)


def test_password_hash_roundtrip() -> None:
    h = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", h)
    assert not verify_password("wrong password", h)


def test_password_hash_is_not_plaintext() -> None:
    assert hash_password("hunter2") != "hunter2"


def test_session_token_roundtrip() -> None:
    token = create_session_token("user-123")
    assert read_session_token(token) == "user-123"


def test_session_token_rejects_tampering() -> None:
    token = create_session_token("user-123")
    # Flip a character in the interior of the payload segment, not the very
    # last character of the token: base64url's final char(s) can have bits
    # that don't affect the decoded bytes, so an edge flip can spuriously
    # leave the signature valid. An interior flip always changes a full byte.
    i = 5
    tampered = token[:i] + ("a" if token[i] != "a" else "b") + token[i + 1 :]
    assert read_session_token(tampered) is None


def test_session_token_rejects_garbage() -> None:
    assert read_session_token("not-a-real-token") is None


def test_totp_roundtrip() -> None:
    import pyotp

    secret = generate_totp_secret()
    assert verify_totp(secret, pyotp.TOTP(secret).now())
    assert not verify_totp(secret, "000000")
