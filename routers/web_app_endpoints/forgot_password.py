from pathlib import Path
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, Depends
from sqlalchemy.orm import Session

from services.html_template_service import reset_password_code_html
from services.resend_service import send_email_with_resend
from db.db import get_db
from db.db_models import Users, UserResetPassword, UserPasswords
from schemas.fotgot_password_schemas import VerifyResetCodePetitionModel, ChangePasswordPetitionModel
from services.encrypt_service import hash_password

router = APIRouter(prefix="/forgot-password", tags=["app/forgot-password"])

@router.post("/create-petition")
async def create_petition(
    email: str = Query(..., description="The email of the user requesting a password reset"),
    db: Session = Depends(get_db)
):
    try:
        # Get user by email
        user = db.query(Users).filter_by(user_email=email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create Reset Code
        reset_code = f"{secrets.randbelow(1_000_000):06d}"

        # Save reset code to database with expiration time of 10 minutes
        user_reset_password = UserResetPassword(
            user_id=user.user_id,
            verify_code=reset_code,
            valid_expiration_date=datetime.now(timezone.utc) + timedelta(minutes=10)
        )
        db.add(user_reset_password)
        db.commit()

        # Create password reset email content
        email_content = reset_password_code_html.format(
            user_name=user.user_name,
            reset_code=reset_code,
            expiry_minutes=10
        )
        send_email_with_resend(
            receiver_email=user.user_email,
            subject="Password Reset Request - Registro de Gastos Automatico",
            html_content=email_content
        )
        return {"message": "Password reset code sent to email successfully"}
    except Exception as e:
        print(f"Error in create_petition: {e}")
        raise HTTPException(status_code=e.status_code if hasattr(e, 'status_code') else 500, detail=str(e) if hasattr(e, 'detail') else "Internal Server Error")

@router.post("/verify-reset-code")
async def verify_reset_code(
    petition: VerifyResetCodePetitionModel,
    db: Session = Depends(get_db)
):
    try:
        # Get user by email
        user = db.query(Users).filter_by(user_email=petition.user_email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get the latest reset code for the user
        user_reset_password = db.query(UserResetPassword).filter_by(user_id=user.user_id).order_by(UserResetPassword.creation_date.desc()).first()
        if not user_reset_password:
            raise HTTPException(status_code=404, detail="No reset code found for this user")
        
        # Check if the reset code is valid
        if user_reset_password.verify_code != petition.reset_code:
            raise HTTPException(status_code=400, detail="Invalid reset code")
        
        # Check if the reset code is expired
        if user_reset_password.valid_expiration_date < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Reset code has expired")
        
        # Check if the reset code is not used
        if user_reset_password.code_used:
            raise HTTPException(status_code=400, detail="Reset code has already been used")
        
        # Mark the reset code as used  
        user_reset_password.code_used = True
        db.commit()

        return {"message": "Reset code is valid"}
    except Exception as e:
        print(f"Error in verify_reset_code: {e}")
        raise HTTPException(status_code=e.status_code if hasattr(e, 'status_code') else 500, detail=str(e) if hasattr(e, 'detail') else "Internal Server Error")

@router.post("/confirm-password-reset")
async def change_password(
    petition: ChangePasswordPetitionModel,
    db: Session = Depends(get_db)
):
    try:
        # Get user by email
        user = db.query(Users).filter_by(user_email=petition.user_email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify if User have a UserPasswords record, if not create one
        user_passwords = db.query(UserPasswords).filter_by(user_id=user.user_id).first()
        if not user_passwords:
            user_passwords = UserPasswords(user_id=user.user_id, hash_password=hash_password(petition.new_password))
            user.account_activated = True
            db.add(user_passwords)
        else:
            user_passwords.hash_password = hash_password(petition.new_password)
            user_passwords.update_date = datetime.now(timezone.utc)
        user.user_last_interaction = datetime.now(timezone.utc)
        db.commit()
        return {"message": "Password changed successfully"}
    except Exception as e:
        print(f"Error in change_password: {e}")
        raise HTTPException(status_code=e.status_code if hasattr(e, 'status_code') else 500, detail=str(e) if hasattr(e, 'detail') else "Internal Server Error")

@router.post('/resend-reset-code')
async def resend_reset_code(
    email: str = Query(..., description="The email of the user requesting to resend the password reset code"),
    db: Session = Depends(get_db)
):
    try:
        # Get user by email
        user = db.query(Users).filter_by(user_email=email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify if there is an active reset code for the user
        user_reset_password = db.query(UserResetPassword).filter_by(user_id=user.user_id, code_used=False).order_by(UserResetPassword.creation_date.desc()).first()
        if user_reset_password and user_reset_password.valid_expiration_date > datetime.now(timezone.utc):
            user_reset_password.verify_code = f"{secrets.randbelow(1_000_000):06d}"
            user_reset_password.valid_expiration_date = datetime.now(timezone.utc) + timedelta(minutes=10)
        else:
            # Create new reset code
            reset_code = f"{secrets.randbelow(1_000_000):06d}"

            # Save reset code to database with expiration time of 10 minutes
            user_reset_password = UserResetPassword(
                user_id=user.user_id,
                verify_code=reset_code,
                valid_expiration_date=datetime.now(timezone.utc) + timedelta(minutes=10)
            )
            db.add(user_reset_password)
        db.commit()

        # Create password reset email content
        email_content = reset_password_code_html.format(
            user_name=user.user_name,
            reset_code=user_reset_password.verify_code,
            expiry_minutes=10
        )
        send_email_with_resend(
            receiver_email=user.user_email,
            subject="Password Reset Request - Registro de Gastos Automatico",
            html_content=email_content
        )
        return {"message": "Password reset code resent to email successfully"}
    except Exception as e:
        print(f"Error in resend_reset_code: {e}")
        raise HTTPException(status_code=e.status_code if hasattr(e, 'status_code') else 500, detail=str(e) if hasattr(e, 'detail') else "Internal Server Error")
        