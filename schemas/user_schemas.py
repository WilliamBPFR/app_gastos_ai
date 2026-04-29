from pydantic import BaseModel
from typing import Optional, List

class MeUserResponse(BaseModel):
    id: int
    username: str
    email: str
    name_initials: Optional[str] = None