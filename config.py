import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")
    GOOGLE_OAUTH_SCOPE = os.getenv(
        "GOOGLE_OAUTH_SCOPE",
        "https://www.googleapis.com/auth/gmail.readonly"
    )

    DATABASE_URL = os.getenv("DATABASE_URL", "")
    REDIS_URL = os.getenv("REDIS_URL", "")
    TOKEN_ENCRYPTION_KEY = os.getenv("TOKEN_ENCRYPTION_KEY", "")
    INTERNAL_API_TOKEN = os.getenv("INTERNAL_API_TOKEN", "")
    APP_BASE_URL = os.getenv("APP_BASE_URL", "")
    RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
    STATE_TTL_SECONDS = int(os.getenv("STATE_TTL_SECONDS", "600"))
    S3_ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL", "").strip()
    S3_ACCESS_KEY_ID: str = os.getenv("S3_ACCESS_KEY_ID", "").strip()
    S3_ACCESS_KEY_SECRET: str = os.getenv("S3_ACCESS_KEY_SECRET", "").strip()
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "").strip()
    S3_REGION: str = os.getenv("S3_REGION", "us-east-1").strip()
    S3_USE_SSL: bool = bool(os.getenv("S3_USE_SSL") == "true")
    JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM=os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    PRODUCTION_MODE=bool(os.getenv("PRODUCTION_MODE") == "true")

config = Config()