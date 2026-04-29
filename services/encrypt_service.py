from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash
import jwt
from jwt import InvalidTokenError
from typing import Any
from uuid import uuid4

from config import config
from db.redis_client import redis_client

password_hash = PasswordHash.recommended()

REVOKED_SESSION_PREFIX = "revoked_session:"


def create_session_id() -> str:
    return uuid4().hex


def _session_key(session_id: str) -> str:
    return f"{REVOKED_SESSION_PREFIX}{session_id}"


def revoke_session(session_id: str) -> None:
    redis_client.setex(
        _session_key(session_id),
        config.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        "1",
    )


def _is_session_revoked(session_id: str | None) -> bool:
    if not session_id:
        return False

    return bool(redis_client.get(_session_key(session_id)))

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def create_access_token(
    subject: str,
    session_id: str | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(subject),
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "session_id": session_id or create_session_id(),
    }

    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(
        payload,
        config.JWT_SECRET_KEY,
        algorithm=config.JWT_ALGORITHM,
    )


def create_refresh_token(
    subject: str,
    session_id: str | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=config.REFRESH_TOKEN_EXPIRE_DAYS
    )

    payload = {
        "sub": str(subject),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "session_id": session_id or create_session_id(),
    }

    return jwt.encode(
        payload,
        config.JWT_SECRET_KEY,
        algorithm=config.JWT_ALGORITHM,
    )


def decode_token(
    token: str,
    verify_exp: bool = True,
) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET_KEY,
            algorithms=[config.JWT_ALGORITHM],
            options={"verify_exp": verify_exp},
        )

        if _is_session_revoked(payload.get("session_id")):
            raise ValueError("Invalid or expired token")

        return payload

    except InvalidTokenError as e:
        print(f"Invalid token: {e}")
        raise ValueError("Invalid or expired token")