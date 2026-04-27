import json
import secrets
from urllib.parse import urlencode
from fastapi.exceptions import ValidationException
import httpx
from sqlalchemy.orm import Session

from config import config
from db.redis_client import redis_client
from db.db_models import UserGoogleConnections, Users
from utils.crypto_utils import encrypt_text

STATE_PREFIX = "oauth_state:"

def build_google_auth_url(user_id: str) -> str:
    state = secrets.token_urlsafe(32)

    redis_client.setex(
        f"{STATE_PREFIX}{state}",
        config.STATE_TTL_SECONDS,
        json.dumps({"user_id": user_id})
    )

    params = {
        "client_id": config.GOOGLE_CLIENT_ID,
        "redirect_uri": config.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": config.GOOGLE_OAUTH_SCOPE,
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
        "state": state,
    }

    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)

def consume_state(state: str) -> dict | None:
    key = f"{STATE_PREFIX}{state}"
    data = redis_client.get(key)
    if not data:
        return None

    redis_client.delete(key)
    return json.loads(data)

async def exchange_code_for_tokens(code: str) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": config.GOOGLE_CLIENT_ID,
                "client_secret": config.GOOGLE_CLIENT_SECRET,
                "redirect_uri": config.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
    resp.raise_for_status()
    return resp.json()

async def get_google_email(access_token: str) -> str | None:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/profile",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if resp.status_code != 200:
        return None
    return resp.json().get("emailAddress")

def save_user_connection(
    db: Session,
    user_id: str,
    google_email: str | None,
    refresh_token: str,
    scope: str | None,
    token_type: str | None,
):
    encrypted = encrypt_text(refresh_token)

    # Verificar si el correo traido es el mismo en la base de datos
    print(f"Verificando conexión para user_id={user_id} con email={google_email}")
    user_data = (
        db.query(Users)
        .filter(Users.user_id == user_id)
        .first()
    )

    if not user_data:
        print(f"No se encontró el usuario con user_id={user_id}")
        raise ValidationException("Usuario no encontrado")

    if user_data.user_email and user_data.user_email != google_email:
        print(f"El correo del usuario en la base de datos ({user_data.user_email}) no coincide con el correo obtenido de Google ({google_email}) para user_id={user_id}")
        raise ValidationException("El correo del usuario no coincide con el correo de Google")
    
    existing = (
        db.query(UserGoogleConnections)
        .filter(UserGoogleConnections.user_id == user_id)
        .first()
    )

    if existing:
        existing.refresh_token_encrypted = encrypted
        existing.scope = scope
        existing.token_type = token_type
        existing.is_active = True
        user_data.user_email = google_email
    else:
        item = UserGoogleConnections(
            user_id=user_id,
            refresh_token_encrypted=encrypted,
            scope=scope,
            token_type=token_type,
            is_active=True
        )
        db.add(item)

    db.commit()