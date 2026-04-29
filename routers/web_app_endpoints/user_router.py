from fastapi import APIRouter, File, HTTPException, Query, UploadFile, Depends, Response, Cookie
from sqlalchemy.orm import Session
from fastapi_deps import get_current_user_id

from db.db import get_db
from db.db_models import Users
from schemas.user_schemas import MeUserResponse

router = APIRouter(prefix="/user", tags=["app/user"])

@router.get("/me", response_model=MeUserResponse)
async def get_current_user(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        print(f"Fetching user with ID: {current_user_id}")
        user = db.query(Users).filter(Users.user_id == current_user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user_name_initials = ''.join([name[0].upper() for name in user.user_name.split() if name]) # Example: "John Doe" -> "JD"
        return MeUserResponse(
            id=user.user_id,
            username=user.user_name,
            email=user.user_email,
            name_initials=user_name_initials
        )
    except Exception as e:
        raise HTTPException(status_code=e.status_code if hasattr(e, 'status_code') else 500, detail=str(e) if hasattr(e, 'detail') else "Internal Server Error")
