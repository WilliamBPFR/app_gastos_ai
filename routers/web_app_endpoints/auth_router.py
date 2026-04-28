from fastapi import APIRouter, File, HTTPException, Query, UploadFile, Depends, Response, Cookie
from sqlalchemy.orm import Session

from services.encrypt_service import create_access_token, create_refresh_token, verify_password, decode_token
from db.db import get_db
from db.db_models import Users, UserPasswords
from schemas.auth_schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["app/auth"])

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
        access_token = create_access_token(user.user_id)

        if login_request.rememberMe:
            refresh_token = create_refresh_token(user.user_id)

            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=False,       # False en local si no usas HTTPS
                samesite="none",    # "none" si frontend y backend están en dominios distintos
                max_age=7 * 24 * 60 * 60,
                path="/auth/refresh",
            )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer"
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
        if user_id is None:
            raise HTTPException(status_code=400, detail="Invalid token payload")
        
        new_access_token = create_access_token(user_id)
        new_refresh_token = create_refresh_token(user_id)

        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=False,       # False en local si no usas HTTPS
            samesite="none",    # "none" si frontend y backend están en dominios distintos
            max_age=7 * 24 * 60 * 60,
            path="/auth/refresh",
        )

        return TokenResponse(
            access_token=new_access_token,
            token_type="bearer"
        )
    
    except Exception as e:
        print(f"Error in refresh_token: {e}")
        raise HTTPException(status_code=e.status_code if hasattr(e, 'status_code') else 500, detail=str(e) if hasattr(e, 'detail') else "Internal Server Error")

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key="refresh_token",
        path="/auth/refresh",
        secure=False,       # False en local si no usas HTTPS
        samesite="none"    # "none" si frontend y backend están en dominios distintos
    )

    return {
        "message": "Logged out successfully"
    }