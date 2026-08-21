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
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")
    assert read_session_token(tampered) is None


def test_session_token_rejects_garbage() -> None:
    assert read_session_token("not-a-real-token") is None


def test_totp_roundtrip() -> None:
    import pyotp

    secret = generate_totp_secret()
    assert verify_totp(secret, pyotp.TOTP(secret).now())
    assert not verify_totp(secret, "000000")
