from pydantic import BaseModel
from typing import Optional, List

class LoginRequest(BaseModel):
    email: str
    password: str
    rememberMe: Optional[bool] = False

class TokenResponse(BaseModel):
    login_success: bool

class RefreshTokenRequest(BaseModel):
    refresh_token: str