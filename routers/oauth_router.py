import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session

from db import get_db
from db_models import Users
from services.gmail_service import (
    list_recent_messages
)
from services.oauth_service import (
    # build_google_auth_url,
    consume_state,
    # exchange_code_for_tokens,
    get_google_email,
    save_user_connection,
)

from services.google_api_service import build_google_auth_url, exchange_code_for_tokens

router = APIRouter(prefix="/oauth/google", tags=["oauth"])

@router.get("/start")
def oauth_start(user_id: str = Query(...), db: Session = Depends(get_db)):
    db_user = db.query(Users).filter(Users.id == user_id).first()
    if not db_user:
        return HTMLResponse("<h1>Usuario no encontrado</h1>", status_code=404)
    
    url = build_google_auth_url(user_id)
    return RedirectResponse(url)

@router.get("/callback", response_class=HTMLResponse)
async def oauth_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    try:

        if error:
            return HTMLResponse(f"<h1>Autorización cancelada</h1><p>{error}</p>", status_code=400)

        if not code or not state:
            return HTMLResponse("<h1>Solicitud inválida</h1>", status_code=400)

        state_data = consume_state(state)
        if not state_data:
            return HTMLResponse("<h1>State inválido o expirado</h1>", status_code=400)
        
        code_verifier = state_data.get("code_verifier")
        if not code_verifier:
            return HTMLResponse("<h1>State inválido: falta code_verifier</h1>", status_code=400)
        
        print("Intercambiando código por tokens")
        tokens = await exchange_code_for_tokens(code, state, code_verifier)

        refresh_token = tokens.get("refresh_token")
        access_token = tokens.get("access_token")
        scope = tokens.get("scope")
        token_type = tokens.get("token_type")

        if not refresh_token:
            return HTMLResponse(
                "<h1>No se recibió refresh token</h1><p>Intenta reconectar de nuevo.</p>",
                status_code=400,
            )
        print("Buscando email de Google")
        google_email = await get_google_email(access_token)

        print(f"Guardando conexión para user_id={state_data['user_id']} con email={google_email}")

        save_user_connection(
            db=db,
            user_id=state_data["user_id"],
            google_email=google_email,
            refresh_token=refresh_token,
            scope=scope,
            token_type=token_type,
        )

        return HTMLResponse(
            "<h1>Cuenta conectada correctamente</h1><p>Ya puedes volver a Telegram.</p>",
            status_code=200,
        )
    except Exception as e:
        print(f"Error en callback: {e}")
        return HTMLResponse(
            "<h1>Error durante la conexión</h1><p>Intenta reconectar de nuevo.</p>",
            status_code=500,
        )