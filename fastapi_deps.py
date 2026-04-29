import secrets

from fastapi import Header, HTTPException, Request, status
from config import config

from fastapi.security import OAuth2PasswordBearer

from services.encrypt_service import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def verify_internal_token(
    x_internal_token: str | None = Header(
        default=None,
        alias="X-Internal-Token",
    )
) -> bool:
    if not x_internal_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing internal token",
        )

    if not secrets.compare_digest(
        x_internal_token,
        config.INTERNAL_API_TOKEN,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal token",
        )

    return True 

def get_current_user_id(request: Request) -> int:
    try:
        token = request.cookies.get("access_token")
        # print(f"Verifying token:{token}")
        payload = decode_token(token)
        # print(f"Decoded payload: {payload}")
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        return int(user_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )