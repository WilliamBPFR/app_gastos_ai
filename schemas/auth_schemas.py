from pydantic import BaseModel
from typing import Optional, List

class LoginRequest(BaseModel):
    email: str
    password: str
    rememberMe: Optional[bool] = False

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str