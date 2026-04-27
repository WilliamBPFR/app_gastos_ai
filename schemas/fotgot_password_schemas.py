from pydantic import BaseModel
from typing import Optional, List

class VerifyResetCodePetitionModel(BaseModel):
    user_email: str
    reset_code: str

class ChangePasswordPetitionModel(BaseModel):
    user_email: str
    new_password: str