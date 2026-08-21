from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: str | None = None
    remember: bool = True


class LoginResponse(BaseModel):
    totp_required: bool = False
    user: "UserResponse | None" = None


class UserResponse(BaseModel):
    id: str
    email: str
    totp_enabled: bool


class TotpSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class TotpEnableRequest(BaseModel):
    code: str


class TotpDisableRequest(BaseModel):
    password: str
