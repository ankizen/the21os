import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from the21os.audit.service import write_audit_log
from the21os.auth.dependencies import get_current_user
from the21os.auth.schemas import (
    LoginRequest,
    LoginResponse,
    TotpDisableRequest,
    TotpEnableRequest,
    TotpSetupResponse,
    UserResponse,
)
from the21os.auth.security import (
    SESSION_COOKIE_NAME,
    create_session_token,
    generate_totp_secret,
    totp_provisioning_uri,
    verify_password,
    verify_totp,
)
from the21os.config import get_settings
from the21os.db.base import get_db
from the21os.db.models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _to_response(user: User) -> UserResponse:
    return UserResponse(id=str(user.id), email=user.email, totp_enabled=user.totp_enabled)


def _set_session_cookie(response: Response, user_id: str, remember: bool) -> None:
    settings = get_settings()
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_session_token(user_id),
        # "Remember me" off -> a browser-session cookie (no max_age), cleared
        # when the browser closes. The signed token itself is still valid for
        # session_max_age_seconds either way; this only controls how long the
        # browser holds onto it.
        max_age=settings.session_max_age_seconds if remember else None,
        httponly=True,
        secure=settings.is_prod,
        samesite="lax",
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    request_id = str(uuid.uuid4())
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.password_hash):
        await write_audit_log(
            db,
            request_id=request_id,
            actor=body.email,
            source="rest_api",
            action="auth.login",
            success=False,
            decision_reason="invalid credentials",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if user.totp_enabled:
        if body.totp_code is None:
            return LoginResponse(totp_required=True)
        if not verify_totp(user.totp_secret, body.totp_code):
            await write_audit_log(
                db,
                request_id=request_id,
                actor=body.email,
                source="rest_api",
                action="auth.login",
                success=False,
                decision_reason="invalid TOTP code",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication code"
            )

    user.last_login_at = datetime.now(UTC)
    await db.commit()
    _set_session_cookie(response, str(user.id), body.remember)
    await write_audit_log(
        db, request_id=request_id, actor=body.email, source="rest_api", action="auth.login", success=True
    )
    return LoginResponse(user=_to_response(user))


@router.post("/logout")
async def logout(response: Response, user: User = Depends(get_current_user)) -> dict:
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"ok": True}


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> UserResponse:
    return _to_response(user)


@router.post("/totp/setup", response_model=TotpSetupResponse)
async def totp_setup(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> TotpSetupResponse:
    if user.totp_enabled:
        raise HTTPException(status_code=400, detail="TOTP already enabled — disable it first to re-generate")
    secret = generate_totp_secret()
    user.totp_secret = secret
    await db.commit()
    return TotpSetupResponse(secret=secret, provisioning_uri=totp_provisioning_uri(secret, user.email))


@router.post("/totp/enable")
async def totp_enable(
    body: TotpEnableRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> dict:
    if user.totp_secret is None:
        raise HTTPException(status_code=400, detail="Call /totp/setup first")
    if not verify_totp(user.totp_secret, body.code):
        raise HTTPException(status_code=400, detail="Invalid authentication code")
    user.totp_enabled = True
    await db.commit()
    await write_audit_log(
        db,
        request_id=str(uuid.uuid4()),
        actor=user.email,
        source="rest_api",
        action="auth.totp_enable",
        success=True,
    )
    return {"ok": True}


@router.post("/totp/disable")
async def totp_disable(
    body: TotpDisableRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> dict:
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password")
    user.totp_enabled = False
    user.totp_secret = None
    await db.commit()
    await write_audit_log(
        db,
        request_id=str(uuid.uuid4()),
        actor=user.email,
        source="rest_api",
        action="auth.totp_disable",
        success=True,
    )
    return {"ok": True}
