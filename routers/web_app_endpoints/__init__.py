from fastapi import APIRouter
from . import forgot_password_router, auth_router, user_router

web_app_router = APIRouter(prefix="/app")
web_app_router.include_router(forgot_password_router.router)
web_app_router.include_router(auth_router.router)
web_app_router.include_router(user_router.router)