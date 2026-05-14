from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AccountTypeBase(BaseModel):
    account_type_id: int
    account_type_name: Optional[str] = None

class AccountBase(BaseModel):
    account_id: Optional[int] = None
    account_name: str
    account_description: str
    creation_date: Optional[datetime] = None
    active: Optional[bool] = True
    account_type: AccountTypeBase

class AccountGetAllResponseModel(BaseModel):
    total_accounts: int
    pagination_use: int
    accounts: List[AccountBase]
    
class AccountCreateModel(BaseModel):
    account_name: str
    account_description: Optional[str] = None
    active: Optional[bool] = True