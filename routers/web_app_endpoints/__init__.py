from fastapi import APIRouter
web_app_router = APIRouter(prefix="/app")

from . import forgot_password
web_app_router.include_router(forgot_password.router)
