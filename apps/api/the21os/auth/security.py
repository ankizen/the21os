import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from the21os.config import get_settings

_hasher = PasswordHasher()

SESSION_COOKIE_NAME = "the21os_session"
_SESSION_SALT = "the21os-session"


def hash_password(raw: str) -> str:
    return _hasher.hash(raw)


def verify_password(raw: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, raw)
    except VerifyMismatchError:
        return False


def create_session_token(user_id: str) -> str:
    serializer = URLSafeTimedSerializer(get_settings().session_secret, salt=_SESSION_SALT)
    return serializer.dumps({"uid": user_id})


def read_session_token(token: str) -> str | None:
    """Returns the user id if the token is valid and unexpired, else None."""
    settings = get_settings()
    serializer = URLSafeTimedSerializer(settings.session_secret, salt=_SESSION_SALT)
    try:
        data = serializer.loads(token, max_age=settings.session_max_age_seconds)
    except (BadSignature, SignatureExpired):
        return None
    return data.get("uid")


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def totp_provisioning_uri(secret: str, email: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name="The21OS — AI Ads")


def verify_totp(secret: str, code: str) -> bool:
    return pyotp.totp.TOTP(secret).verify(code, valid_window=1)
