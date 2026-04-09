from fastapi import Header, HTTPException
from config import config

def verify_internal_token(x_internal_token: str = Header(default="")):
    if x_internal_token != config.INTERNAL_API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")