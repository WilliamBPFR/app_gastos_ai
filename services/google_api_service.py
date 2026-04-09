import json
import secrets
from google_auth_oauthlib.flow import Flow

from config import config
from redis_client import redis_client
from fastapi.concurrency import run_in_threadpool

STATE_PREFIX = "oauth_state:"
GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"

def _client_config() -> dict:
    return {
        "web": {
            "client_id": config.GOOGLE_CLIENT_ID,
            "client_secret": config.GOOGLE_CLIENT_SECRET,
            "auth_uri": GOOGLE_AUTH_URI,
            "token_uri": GOOGLE_TOKEN_URI,
            "redirect_uris": [config.GOOGLE_REDIRECT_URI],
        }
    }

def build_google_auth_url(user_id: str) -> str:
    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(96)
    
    redis_client.setex(
        f"{STATE_PREFIX}{state}",
        config.STATE_TTL_SECONDS,
        json.dumps({
            "user_id": user_id,
            "code_verifier": code_verifier,
        }),
    )

    flow = Flow.from_client_config(
        _client_config(),
        scopes=config.GOOGLE_OAUTH_SCOPE.split(" "),
        state=state,
        code_verifier=code_verifier,
    )
    flow.redirect_uri = config.GOOGLE_REDIRECT_URI

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="false",
        prompt="consent",
        code_challenge_method="S256",
    )
    return auth_url

async def exchange_code_for_tokens(code: str, state: str, code_verifier: str) -> dict:
    flow = Flow.from_client_config(
        client_config=_client_config(),
        scopes=config.GOOGLE_OAUTH_SCOPE.split(" "),
        state=state,
        code_verifier=code_verifier,
    )
    flow.redirect_uri = config.GOOGLE_REDIRECT_URI

    # fetch_token es síncrono; en async lo mandamos a threadpool
    await run_in_threadpool(flow.fetch_token, code=code)

    creds = flow.credentials
    return {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "scope": " ".join(creds.scopes or []),
        "token_type": "Bearer",
        "expiry": creds.expiry.isoformat() if creds.expiry else None,
    }