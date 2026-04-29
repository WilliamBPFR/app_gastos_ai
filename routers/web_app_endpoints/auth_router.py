from fastapi import APIRouter, File, HTTPException, Query, UploadFile, Depends, Response, Cookie
from sqlalchemy.orm import Session

from services.encrypt_service import (
    create_access_token,
    create_refresh_token,
    create_session_id,
    decode_token,
    revoke_session,
    verify_password,
)
from db.db import get_db
from db.db_models import Users, UserPasswords
from schemas.auth_schemas import LoginRequest, TokenResponse
from config import config
from fastapi_deps import get_current_user_id

router = APIRouter(prefix="/auth", tags=["app/auth"])
ACCESS_COOKIE_PATH = "/"
REFRESH_COOKIE_PATH = "/auth/refresh"

@router.post("/login", response_model=TokenResponse)
async def login(
    response: Response,
    login_request: LoginRequest,
    db: Session = Depends(get_db),
):
    try:
        # Get user by email
        print(f"Attempting login for email: {login_request.email}")
        user = db.query(Users).filter_by(user_email=login_request.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify password
        if not verify_password(login_request.password, user.user_passwords.hash_password):
            raise HTTPException(status_code=400, detail="Invalid credentials")
        
        # Create access and refresh tokens
        session_id = create_session_id()
        access_token = create_access_token(str(user.user_id), session_id=session_id)

        if login_request.rememberMe:
            refresh_token = create_refresh_token(str(user.user_id), session_id=session_id)

            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=config.PRODUCTION_MODE,       # False en local si no usas HTTPS
                samesite="lax",    # "none" si frontend y backend están en dominios distintos
                max_age=7 * 24 * 60 * 60,
                path=REFRESH_COOKIE_PATH,
            )

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=config.PRODUCTION_MODE,       # False en local si no usas HTTPS
            samesite="lax",    # "none" si frontend y backend están en dominios distintos
            max_age=15 * 60,   # 15 minutes
            path=ACCESS_COOKIE_PATH,
        )

        return TokenResponse(
            login_success=True,
        )
    except Exception as e:
        print(f"Error in login: {e}")
        raise HTTPException(status_code=e.status_code if hasattr(e, 'status_code') else 500, detail=str(e) if hasattr(e, 'detail') else "Internal Server Error")
    

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
    db: Session = Depends(get_db)
):
    
    if not refresh_token:
        raise HTTPException(
            status_code=400,
            detail="Missing refresh token",
    )
    
    try:
        # Verify refresh token and get user ID
        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")
        
        user_id = payload.get("sub")
        session_id = payload.get("session_id")
        if user_id is None:
            raise HTTPException(status_code=400, detail="Invalid token payload")
        
        new_access_token = create_access_token(str(user_id), session_id=session_id)
        new_refresh_token = create_refresh_token(str(user_id), session_id=session_id)

        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=config.PRODUCTION_MODE,       # False en local si no usas HTTPS
            samesite="lax",    # "none" si frontend y backend están en dominios distintos
            max_age=7 * 24 * 60 * 60,
            path=REFRESH_COOKIE_PATH,
        )

        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=config.PRODUCTION_MODE,       # False en local si no usas HTTPS
            samesite="lax",    # "none" si frontend y backend están en dominios distintos
            max_age=15 * 60,   # 15 minutes
            path=ACCESS_COOKIE_PATH,
        )

        return TokenResponse(
            login_success=True,
        )

    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    except Exception as e:
        print(f"Error in refresh_token: {e}")
        raise HTTPException(status_code=e.status_code if hasattr(e, 'status_code') else 500, detail=str(e) if hasattr(e, 'detail') else "Internal Server Error")

@router.post("/logout")
def logout(
    response: Response,
    access_token: str | None = Cookie(default=None, alias="access_token"),
):
    if access_token:
        try:
            payload = decode_token(access_token, verify_exp=False)
            session_id = payload.get("session_id")
            if session_id:
                revoke_session(session_id)
        except ValueError:
            pass

    response.delete_cookie(
        key="refresh_token",
        path=REFRESH_COOKIE_PATH,
        secure=config.PRODUCTION_MODE,       # False en local si no usas HTTPS
        samesite="lax",    # "none" si frontend y backend están en dominios distintos
        httponly=True
    )

    response.delete_cookie(
        key="access_token",
        path=ACCESS_COOKIE_PATH,
        secure=config.PRODUCTION_MODE,       # False en local si no usas HTTPS
        samesite="lax",    # "none" si frontend y backend están en dominios distintos
        httponly=True
    )

    return {
        "message": "Logged out successfully"
    }

@router.get("/verify")
def verify_token(current_user_id: int = Depends(get_current_user_id)):
    return {
        "authenticated": True
    }