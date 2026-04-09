from cryptography.fernet import Fernet
from config import config

fernet = Fernet(config.TOKEN_ENCRYPTION_KEY.encode())

def encrypt_text(value: str) -> str:
    return fernet.encrypt(value.encode()).decode()

def decrypt_text(value: str) -> str:
    return fernet.decrypt(value.encode()).decode()